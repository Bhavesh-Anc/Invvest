# utils/model.py
import pickle
import hashlib
from datetime import datetime, timedelta
import logging
import json
import warnings
import os
import numpy as np
import pandas as pd
import optuna
from sklearn.inspection import permutation_importance
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb
from catboost import CatBoostClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    VotingClassifier,
    ExtraTreesClassifier
)
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import (
    TimeSeriesSplit,
    cross_val_score
)
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from typing import Dict, List, Tuple, Any, Optional
import sqlite3
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, matthews_corrcoef, log_loss
)
import xgboost as xgb
from pathlib import Path
import time

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

# ==================== INDIVIDUAL MODEL CONFIGURATION ====================

INDIVIDUAL_MODEL_CONFIG = {
    'model_types': ['xgboost', 'lightgbm', 'catboost', 'random_forest', 'neural_network'],
    'default_models': ['xgboost', 'lightgbm', 'random_forest'],
    'model_cache_dir': 'models/individual_models',
    'test_size': 0.2,
    'validation_size': 0.1,
    'cv_folds': 5,
    'random_state': 42,
    'n_jobs': -1,
    'max_features': 150,
    'feature_selection_enabled': True,
    'hyperparameter_tuning': True,
    'optuna_trials': 50,
    'early_stopping': True,
    'model_calibration': True,
    'performance_threshold': 0.55,
    'save_feature_importance': True,
    'enable_monitoring': True
}

TARGET_HORIZONS = {
    'next_week': 5,
    'next_month': 21,
    'next_quarter': 63,
    'next_year': 252
}

# ==================== INDIVIDUAL STOCK PREDICTOR CLASS ====================

class IndividualStockPredictor:
    """Enhanced predictor for individual stocks"""
    
    def __init__(self, stock_symbol: str, horizon: str, model_type: str):
        self.stock_symbol = stock_symbol
        self.horizon = horizon
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.calibrator = None
        self.selected_features = None
        self.feature_importances = None
        self.validation_score = None
        self.cv_score = None
        self.training_time = None
        self.training_date = datetime.now()
        self.hyperparameters = None
        self.model_id = f"{stock_symbol}_{model_type}_{horizon}"
        
        # Ensure model directory exists
        self.model_dir = Path(INDIVIDUAL_MODEL_CONFIG['model_cache_dir'])
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Model file path
        self.model_path = self.model_dir / f"{self.model_id}.pkl"
    
    def _prepare_data(self, features: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for training"""
        
        target_col = f'target_{self.horizon}'
        if target_col not in features.columns:
            raise ValueError(f"Target column '{target_col}' not found in features")
        
        # Remove rows with NaN targets
        clean_features = features.dropna(subset=[target_col])
        
        # Separate features and target
        feature_cols = [col for col in clean_features.columns if not col.startswith('target_')]
        X = clean_features[feature_cols]
        y = clean_features[target_col].astype(int)
        
        return X, y
    
    def _select_features(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Select relevant features"""
        
        if not INDIVIDUAL_MODEL_CONFIG['feature_selection_enabled']:
            self.selected_features = X.columns.tolist()
            return X
        
        try:
            from sklearn.feature_selection import SelectKBest, f_classif
            from sklearn.feature_selection import RFE
            
            # Remove features with very low variance
            feature_variance = X.var()
            high_variance_features = feature_variance[feature_variance > 0.001].index
            X_filtered = X[high_variance_features]
            
            # SelectKBest
            max_features = min(INDIVIDUAL_MODEL_CONFIG['max_features'], len(X_filtered.columns))
            selector = SelectKBest(score_func=f_classif, k=max_features)
            X_selected = selector.fit_transform(X_filtered, y)
            
            selected_feature_names = X_filtered.columns[selector.get_support()].tolist()
            self.selected_features = selected_feature_names
            
            return pd.DataFrame(X_selected, columns=selected_feature_names, index=X.index)
            
        except Exception as e:
            logging.warning(f"Feature selection failed for {self.model_id}: {e}")
            self.selected_features = X.columns.tolist()
            return X
    
    def _scale_features(self, X: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """Scale features"""
        
        if fit:
            self.scaler = RobustScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            if self.scaler is None:
                raise ValueError("Scaler not fitted. Call fit first.")
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def _create_model(self) -> Any:
        """Create model instance"""
        
        random_state = INDIVIDUAL_MODEL_CONFIG['random_state']
        n_jobs = INDIVIDUAL_MODEL_CONFIG['n_jobs']
        
        if self.model_type == 'xgboost':
            return xgb.XGBClassifier(
                random_state=random_state,
                n_jobs=n_jobs,
                eval_metric='logloss'
            )
        
        elif self.model_type == 'lightgbm':
            return lgb.LGBMClassifier(
                random_state=random_state,
                n_jobs=n_jobs,
                verbose=-1
            )
        
        elif self.model_type == 'catboost':
            return CatBoostClassifier(
                random_state=random_state,
                thread_count=n_jobs,
                verbose=False
            )
        
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                random_state=random_state,
                n_jobs=n_jobs
            )
        
        elif self.model_type == 'neural_network':
            return MLPClassifier(
                hidden_layer_sizes=(100, 50),
                random_state=random_state,
                max_iter=500
            )
        
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def _tune_hyperparameters(self, X: np.ndarray, y: pd.Series) -> Dict:
        """Tune hyperparameters using Optuna"""
        
        if not INDIVIDUAL_MODEL_CONFIG['hyperparameter_tuning']:
            return {}
        
        try:
            def objective(trial):
                if self.model_type == 'xgboost':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                        'max_depth': trial.suggest_int('max_depth', 3, 10),
                        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
                    }
                    model = xgb.XGBClassifier(**params, random_state=INDIVIDUAL_MODEL_CONFIG['random_state'], eval_metric='logloss')
                
                elif self.model_type == 'lightgbm':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                        'max_depth': trial.suggest_int('max_depth', 3, 10),
                        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                        'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
                        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0)
                    }
                    model = lgb.LGBMClassifier(**params, random_state=INDIVIDUAL_MODEL_CONFIG['random_state'], verbose=-1)
                
                elif self.model_type == 'catboost':
                    params = {
                        'iterations': trial.suggest_int('iterations', 50, 300),
                        'depth': trial.suggest_int('depth', 3, 10),
                        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3)
                    }
                    model = CatBoostClassifier(**params, random_state=INDIVIDUAL_MODEL_CONFIG['random_state'], verbose=False)
                
                elif self.model_type == 'random_forest':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                        'max_depth': trial.suggest_int('max_depth', 3, 20),
                        'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5)
                    }
                    model = RandomForestClassifier(**params, random_state=INDIVIDUAL_MODEL_CONFIG['random_state'])
                
                else:
                    return 0.5  # Default for unsupported models
                
                # Cross-validation
                tscv = TimeSeriesSplit(n_splits=3)
                scores = cross_val_score(model, X, y, cv=tscv, scoring='roc_auc')
                return scores.mean()
            
            # Create study
            study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler())
            study.optimize(objective, n_trials=min(INDIVIDUAL_MODEL_CONFIG['optuna_trials'], 20), show_progress_bar=False)
            
            self.hyperparameters = study.best_params
            return study.best_params
            
        except Exception as e:
            logging.warning(f"Hyperparameter tuning failed for {self.model_id}: {e}")
            return {}
    
    def train(self, features: pd.DataFrame) -> bool:
        """Train the model"""
        
        start_time = time.time()
        
        try:
            # Prepare data
            X, y = self._prepare_data(features)
            
            if len(X) < 100:
                logging.warning(f"Insufficient data for {self.model_id}: {len(X)} samples")
                return False
            
            # Check class balance
            class_counts = y.value_counts()
            if len(class_counts) < 2 or min(class_counts) < 10:
                logging.warning(f"Insufficient class samples for {self.model_id}")
                return False
            
            # Feature selection
            X_selected = self._select_features(X, y)
            
            # Scale features
            X_scaled = self._scale_features(X_selected, fit=True)
            
            # Split data
            split_idx = int(len(X_scaled) * (1 - INDIVIDUAL_MODEL_CONFIG['test_size']))
            X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            # Create model
            self.model = self._create_model()
            
            # Tune hyperparameters
            best_params = self._tune_hyperparameters(X_train, y_train)
            if best_params:
                self.model.set_params(**best_params)
            
            # Train model
            if self.model_type in ['xgboost', 'lightgbm', 'catboost']:
                # Use early stopping for gradient boosting models
                eval_set = [(X_test, y_test)]
                
                if self.model_type == 'xgboost':
                    self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=20, verbose=False)
                elif self.model_type == 'lightgbm':
                    self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=20, verbose=False)
                elif self.model_type == 'catboost':
                    self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=20, verbose=False)
            else:
                self.model.fit(X_train, y_train)
            
            # Calibrate probabilities
            if INDIVIDUAL_MODEL_CONFIG['model_calibration']:
                try:
                    self.calibrator = CalibratedClassifierCV(self.model, method='isotonic', cv=3)
                    self.calibrator.fit(X_train, y_train)
                except Exception as e:
                    logging.warning(f"Model calibration failed for {self.model_id}: {e}")
            
            # Evaluate on test set
            if self.calibrator:
                y_pred_proba = self.calibrator.predict_proba(X_test)[:, 1]
            else:
                y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            # Calculate metrics
            self.validation_score = roc_auc_score(y_test, y_pred_proba)
            
            # Cross-validation score
            try:
                tscv = TimeSeriesSplit(n_splits=INDIVIDUAL_MODEL_CONFIG['cv_folds'])
                cv_scores = cross_val_score(self.model, X_scaled, y, cv=tscv, scoring='roc_auc')
                self.cv_score = cv_scores.mean()
            except Exception as e:
                logging.warning(f"CV scoring failed for {self.model_id}: {e}")
                self.cv_score = self.validation_score
            
            # Feature importance
            if INDIVIDUAL_MODEL_CONFIG['save_feature_importance']:
                self._calculate_feature_importance(X_selected, y)
            
            # Training time
            self.training_time = time.time() - start_time
            
            # Check if model meets performance threshold
            if self.validation_score >= INDIVIDUAL_MODEL_CONFIG['performance_threshold']:
                logging.info(f"✅ {self.model_id} trained successfully (Score: {self.validation_score:.3f})")
                return True
            else:
                logging.warning(f"⚠️ {self.model_id} performance below threshold ({self.validation_score:.3f})")
                return True  # Still return True as training completed
            
        except Exception as e:
            logging.error(f"Training failed for {self.model_id}: {e}")
            return False
    
    def _calculate_feature_importance(self, X: pd.DataFrame, y: pd.Series):
        """Calculate feature importance"""
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                # Tree-based models
                self.feature_importances = dict(zip(X.columns, self.model.feature_importances_))
            else:
                # Permutation importance for other models
                X_scaled = self._scale_features(X, fit=False)
                perm_importance = permutation_importance(
                    self.model, X_scaled, y, 
                    n_repeats=3, random_state=INDIVIDUAL_MODEL_CONFIG['random_state']
                )
                self.feature_importances = dict(zip(X.columns, perm_importance.importances_mean))
        
        except Exception as e:
            logging.warning(f"Feature importance calculation failed for {self.model_id}: {e}")
            self.feature_importances = {}
    
    def predict(self, features: pd.DataFrame) -> Tuple[int, float]:
        """Make prediction"""
        
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            # Prepare features
            if self.selected_features:
                X = features[self.selected_features]
            else:
                feature_cols = [col for col in features.columns if not col.startswith('target_')]
                X = features[feature_cols]
            
            # Scale features
            X_scaled = self._scale_features(X, fit=False)
            
            # Make prediction
            if self.calibrator:
                prediction_proba = self.calibrator.predict_proba(X_scaled)[:, 1]
            else:
                prediction_proba = self.model.predict_proba(X_scaled)[:, 1]
            
            prediction = (prediction_proba > 0.5).astype(int)
            
            return prediction[0], prediction_proba[0]
            
        except Exception as e:
            logging.error(f"Prediction failed for {self.model_id}: {e}")
            return 0, 0.5
    
    def save(self) -> bool:
        """Save model to disk"""
        
        try:
            model_data = {
                'stock_symbol': self.stock_symbol,
                'horizon': self.horizon,
                'model_type': self.model_type,
                'model': self.model,
                'scaler': self.scaler,
                'calibrator': self.calibrator,
                'selected_features': self.selected_features,
                'feature_importances': self.feature_importances,
                'validation_score': self.validation_score,
                'cv_score': self.cv_score,
                'training_time': self.training_time,
                'training_date': self.training_date,
                'hyperparameters': self.hyperparameters,
                'model_id': self.model_id
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logging.info(f"Model saved: {self.model_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save model {self.model_id}: {e}")
            return False
    
    def load(self) -> bool:
        """Load model from disk"""
        
        if not self.model_path.exists():
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Restore model attributes
            for key, value in model_data.items():
                setattr(self, key, value)
            
            logging.info(f"Model loaded: {self.model_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load model {self.model_id}: {e}")
            return False

# ==================== TRAINING FUNCTIONS ====================

def train_individual_stock_model(stock_symbol: str, features: pd.DataFrame, 
                                horizon: str, model_type: str,
                                hyperparameter_tuning: bool = True,
                                cross_validation: bool = True) -> Optional[IndividualStockPredictor]:
    """Train a model for individual stock"""
    
    try:
        predictor = IndividualStockPredictor(stock_symbol, horizon, model_type)
        
        # Update configuration based on parameters
        old_tuning = INDIVIDUAL_MODEL_CONFIG['hyperparameter_tuning']
        old_cv = INDIVIDUAL_MODEL_CONFIG['cv_folds']
        
        INDIVIDUAL_MODEL_CONFIG['hyperparameter_tuning'] = hyperparameter_tuning
        if not cross_validation:
            INDIVIDUAL_MODEL_CONFIG['cv_folds'] = 2  # Minimum for functionality
        
        success = predictor.train(features)
        
        # Restore original configuration
        INDIVIDUAL_MODEL_CONFIG['hyperparameter_tuning'] = old_tuning
        INDIVIDUAL_MODEL_CONFIG['cv_folds'] = old_cv
        
        if success:
            return predictor
        else:
            return None
            
    except Exception as e:
        logging.error(f"Failed to train {stock_symbol}_{model_type}_{horizon}: {e}")
        return None

def train_multiple_stocks_batch(stock_data: Dict[str, pd.DataFrame],
                               horizons: List[str] = None,
                               model_types: List[str] = None,
                               max_workers: int = 4) -> Dict[str, List[Dict]]:
    """Train models for multiple stocks in batch"""
    
    horizons = horizons or ['next_week', 'next_month']
    model_types = model_types or INDIVIDUAL_MODEL_CONFIG['default_models']
    
    results = {}
    
    for stock_symbol, data in stock_data.items():
        stock_results = []
        
        try:
            # Engineer features for this stock
            from utils.feature_engineer import engineer_features_individual
            features = engineer_features_individual(stock_symbol, data)
            
            if features.empty:
                logging.warning(f"No features generated for {stock_symbol}")
                continue
            
            # Train models for each horizon and model type
            for horizon in horizons:
                for model_type in model_types:
                    start_time = time.time()
                    
                    try:
                        predictor = train_individual_stock_model(
                            stock_symbol, features, horizon, model_type
                        )
                        
                        if predictor:
                            predictor.save()
                            
                            stock_results.append({
                                'horizon': horizon,
                                'model_type': model_type,
                                'success': True,
                                'validation_score': predictor.validation_score,
                                'cv_score': predictor.cv_score,
                                'training_time': time.time() - start_time,
                                'feature_count': len(predictor.selected_features) if predictor.selected_features else 0
                            })
                        else:
                            stock_results.append({
                                'horizon': horizon,
                                'model_type': model_type,
                                'success': False,
                                'error': 'Training failed'
                            })
                            
                    except Exception as e:
                        stock_results.append({
                            'horizon': horizon,
                            'model_type': model_type,
                            'success': False,
                            'error': str(e)
                        })
        
        except Exception as e:
            logging.error(f"Failed to process {stock_symbol}: {e}")
        
        results[stock_symbol] = stock_results
    
    return results

# ==================== PREDICTION FUNCTIONS ====================

def predict_individual_stock(stock_symbol: str, features: pd.DataFrame,
                           horizon: str, model_types: List[str] = None) -> Dict:
    """Generate predictions for individual stock"""
    
    model_types = model_types or INDIVIDUAL_MODEL_CONFIG['default_models']
    predictions = {}
    
    for model_type in model_types:
        try:
            predictor = IndividualStockPredictor(stock_symbol, horizon, model_type)
            
            if predictor.load():
                prediction, probability = predictor.predict(features.tail(1))
                
                predictions[model_type] = {
                    'prediction': int(prediction),
                    'probability': float(probability),
                    'validation_score': predictor.validation_score
                }
            
        except Exception as e:
            logging.warning(f"Prediction failed for {stock_symbol}_{model_type}_{horizon}: {e}")
    
    if not predictions:
        return {}
    
    # Ensemble prediction
    ensemble_prediction, ensemble_probability = calculate_ensemble_prediction(predictions)
    confidence = calculate_prediction_confidence(predictions)
    
    return {
        'stock_symbol': stock_symbol,
        'horizon': horizon,
        'ensemble_prediction': ensemble_prediction,
        'ensemble_probability': ensemble_probability,
        'confidence': confidence,
        'individual_predictions': predictions,
        'models_used': len(predictions)
    }

def calculate_ensemble_prediction(predictions: Dict) -> Tuple[int, float]:
    """Calculate ensemble prediction from individual predictions"""
    
    if not predictions:
        return 0, 0.5
    
    # Weighted average based on validation scores
    total_weight = 0
    weighted_probability = 0
    
    for model_type, pred_data in predictions.items():
        weight = pred_data.get('validation_score', 0.5)
        probability = pred_data['probability']
        
        weighted_probability += probability * weight
        total_weight += weight
    
    if total_weight > 0:
        ensemble_probability = weighted_probability / total_weight
    else:
        ensemble_probability = np.mean([pred['probability'] for pred in predictions.values()])
    
    ensemble_prediction = 1 if ensemble_probability > 0.5 else 0
    
    return ensemble_prediction, ensemble_probability

def calculate_prediction_confidence(predictions: Dict) -> float:
    """Calculate confidence in ensemble prediction"""
    
    if not predictions:
        return 0.0
    
    probabilities = [pred['probability'] for pred in predictions.values()]
    validation_scores = [pred.get('validation_score', 0.5) for pred in predictions.values()]
    
    # Confidence based on agreement and validation scores
    prob_std = np.std(probabilities) if len(probabilities) > 1 else 0
    avg_validation_score = np.mean(validation_scores)
    
    # Higher confidence when models agree (low std) and have good validation scores
    agreement_confidence = 1.0 - (prob_std * 2)  # Normalized to [0, 1]
    performance_confidence = avg_validation_score
    
    overall_confidence = (agreement_confidence + performance_confidence) / 2
    
    return max(0.0, min(1.0, overall_confidence))

def generate_predictions_for_stock(stock_symbol: str, stock_data: pd.DataFrame,
                                 horizons: List[str] = None) -> Dict[str, Dict]:
    """Generate predictions for all horizons of a stock"""
    
    horizons = horizons or list(TARGET_HORIZONS.keys())
    
    try:
        # Engineer features
        from utils.feature_engineer import engineer_features_individual
        features = engineer_features_individual(stock_symbol, stock_data)
        
        if features.empty:
            logging.error(f"No features available for {stock_symbol}")
            return {}
        
        predictions = {}
        
        for horizon in horizons:
            prediction = predict_individual_stock(stock_symbol, features, horizon)
            if prediction:
                # Add additional metrics
                prediction['predicted_direction'] = prediction['ensemble_prediction']
                prediction['success_probability'] = prediction['ensemble_probability']
                prediction['risk_score'] = calculate_risk_score(stock_data)
                prediction['model_agreement'] = calculate_model_agreement(prediction.get('individual_predictions', {}))
                
                # Add individual model votes for transparency
                if 'individual_predictions' in prediction:
                    prediction['model_votes'] = {
                        model: (pred_data['prediction'], pred_data['probability'])
                        for model, pred_data in prediction['individual_predictions'].items()
                    }
                
                predictions[horizon] = prediction
        
        return predictions
        
    except Exception as e:
        logging.error(f"Failed to generate predictions for {stock_symbol}: {e}")
        return {}

def calculate_risk_score(stock_data: pd.DataFrame) -> float:
    """Calculate risk score for a stock"""
    
    try:
        if len(stock_data) < 20:
            return 0.5
        
        # Calculate volatility
        returns = stock_data['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Normalize volatility to [0, 1] scale
        # Using 50% annual volatility as high risk threshold
        risk_score = min(1.0, volatility / 0.5)
        
        return risk_score
        
    except Exception as e:
        logging.warning(f"Risk score calculation failed: {e}")
        return 0.5

def calculate_model_agreement(individual_predictions: Dict) -> bool:
    """Calculate if models agree on prediction direction"""
    
    if not individual_predictions or len(individual_predictions) < 2:
        return True
    
    predictions = [pred['prediction'] for pred in individual_predictions.values()]
    
    # Models agree if all predictions are the same
    return len(set(predictions)) == 1

# ==================== MODEL MANAGEMENT FUNCTIONS ====================

def get_available_individual_models() -> Dict[str, Dict]:
    """Get information about available individual models"""
    
    model_dir = Path(INDIVIDUAL_MODEL_CONFIG['model_cache_dir'])
    if not model_dir.exists():
        return {}
    
    models_info = {}
    
    for model_file in model_dir.glob("*.pkl"):
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            model_id = model_data.get('model_id', model_file.stem)
            
            models_info[model_id] = {
                'stock_symbol': model_data.get('stock_symbol', ''),
                'horizon': model_data.get('horizon', ''),
                'model_type': model_data.get('model_type', ''),
                'validation_score': model_data.get('validation_score', 0),
                'training_date': model_data.get('training_date', ''),
                'file_path': str(model_file),
                'file_size_mb': model_file.stat().st_size / (1024 * 1024)
            }
        
        except Exception as e:
            logging.warning(f"Failed to load model info from {model_file}: {e}")
    
    return models_info

def load_individual_model(stock_symbol: str, horizon: str, model_type: str) -> Optional[IndividualStockPredictor]:
    """Load individual model"""
    
    try:
        predictor = IndividualStockPredictor(stock_symbol, horizon, model_type)
        if predictor.load():
            return predictor
        else:
            return None
    except Exception as e:
        logging.error(f"Failed to load model {stock_symbol}_{model_type}_{horizon}: {e}")
        return None

def get_model_summary() -> pd.DataFrame:
    """Get summary of all available models"""
    
    models_info = get_available_individual_models()
    
    if not models_info:
        return pd.DataFrame()
    
    summary_data = []
    
    for model_id, info in models_info.items():
        summary_data.append({
            'Model ID': model_id,
            'Stock Symbol': info['stock_symbol'],
            'Horizon': info['horizon'],
            'Model Type': info['model_type'],
            'Validation Score': info['validation_score'],
            'Training Date': str(info['training_date'])[:19] if info['training_date'] else '',
            'File Size (MB)': info['file_size_mb']
        })
    
    return pd.DataFrame(summary_data)

def cleanup_old_models(days_old: int = 30):
    """Clean up old model files"""
    
    model_dir = Path(INDIVIDUAL_MODEL_CONFIG['model_cache_dir'])
    if not model_dir.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    removed_count = 0
    
    for model_file in model_dir.glob("*.pkl"):
        try:
            # Check file modification time
            file_mtime = datetime.fromtimestamp(model_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                model_file.unlink()
                removed_count += 1
                
        except Exception as e:
            logging.warning(f"Failed to remove old model {model_file}: {e}")
    
    logging.info(f"Cleaned up {removed_count} old model files")

# ==================== UTILITY FUNCTIONS ====================

def validate_model_performance(model: IndividualStockPredictor, 
                              features: pd.DataFrame) -> Dict:
    """Validate model performance on new data"""
    
    try:
        X, y = model._prepare_data(features)
        
        if len(X) < 50:
            return {'status': 'insufficient_data', 'samples': len(X)}
        
        # Make predictions
        X_selected = X[model.selected_features] if model.selected_features else X
        X_scaled = model._scale_features(X_selected, fit=False)
        
        if model.calibrator:
            y_pred_proba = model.calibrator.predict_proba(X_scaled)[:, 1]
        else:
            y_pred_proba = model.model.predict_proba(X_scaled)[:, 1]
        
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        auc_score = roc_auc_score(y, y_pred_proba)
        
        return {
            'status': 'success',
            'accuracy': accuracy,
            'auc_score': auc_score,
            'samples': len(X),
            'validation_date': datetime.now()
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def get_model_feature_importance(model: IndividualStockPredictor) -> Dict[str, float]:
    """Get feature importance from model"""
    
    if model.feature_importances:
        # Sort by importance
        sorted_importance = dict(sorted(
            model.feature_importances.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        return sorted_importance
    
    return {}

# ==================== MAIN EXPORTS ====================

__all__ = [
    'IndividualStockPredictor',
    'train_individual_stock_model',
    'train_multiple_stocks_batch',
    'predict_individual_stock',
    'generate_predictions_for_stock',
    'load_individual_model',
    'get_available_individual_models',
    'get_model_summary',
    'cleanup_old_models',
    'TARGET_HORIZONS',
    'INDIVIDUAL_MODEL_CONFIG'
]