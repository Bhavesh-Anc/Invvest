"""
MLOps Model Management System
Model Registry, Versioning, Drift Detection, and Automated Retraining
Production-grade ML pipeline management
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import sqlite3
import json
import pickle
import hashlib
from pathlib import Path
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Model metadata for registry"""
    model_id: str
    model_name: str
    model_type: str
    version: str
    created_at: datetime
    created_by: str
    dataset_version: str
    training_data_hash: str
    feature_names: List[str]
    hyperparameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    status: str  # 'development', 'staging', 'production', 'archived'
    approval_status: str  # 'pending', 'approved', 'rejected'
    description: str
    tags: List[str]


@dataclass
class ModelCard:
    """Comprehensive model documentation (Model Cards for Model Reporting)"""
    model_id: str
    model_name: str
    version: str

    # Model details
    model_type: str
    architecture: str
    training_algorithm: str

    # Intended use
    intended_use: str
    out_of_scope_use: str

    # Training data
    training_data_source: str
    training_data_size: int
    training_data_period: str
    data_preprocessing: str

    # Performance
    performance_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    test_metrics: Dict[str, float]

    # Limitations
    known_limitations: List[str]
    failure_modes: List[str]

    # Ethical considerations
    ethical_considerations: List[str]
    bias_analysis: str

    # Technical specifications
    input_features: List[str]
    output_format: str
    inference_latency_ms: float
    model_size_mb: float

    # Governance
    approval_date: Optional[datetime]
    approved_by: Optional[str]
    review_date: Optional[datetime]
    next_review_date: Optional[datetime]


class ModelRegistry:
    """
    Centralized model registry for version control and governance
    Similar to MLflow Model Registry
    """

    def __init__(self, database_path: str = 'data/model_registry.db'):
        """
        Args:
            database_path: Path to SQLite database for registry
        """
        self.database_path = database_path
        self.ensure_database_directory()
        self.init_database()

    def ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def init_database(self):
        """Initialize registry database"""
        with sqlite3.connect(self.database_path) as conn:
            # Models table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    created_by TEXT NOT NULL,
                    dataset_version TEXT,
                    training_data_hash TEXT,
                    feature_names TEXT,
                    hyperparameters TEXT,
                    performance_metrics TEXT,
                    status TEXT DEFAULT 'development',
                    approval_status TEXT DEFAULT 'pending',
                    description TEXT,
                    tags TEXT,
                    model_path TEXT,
                    UNIQUE(model_name, version)
                )
            """)

            # Model versions history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    performance_metrics TEXT,
                    deployment_date TIMESTAMP,
                    deprecated_date TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES models(model_id)
                )
            """)

            # Model approvals
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    approver TEXT NOT NULL,
                    approval_date TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    comments TEXT,
                    FOREIGN KEY (model_id) REFERENCES models(model_id)
                )
            """)

            # Performance tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    evaluation_date TIMESTAMP NOT NULL,
                    dataset_name TEXT,
                    metrics TEXT NOT NULL,
                    FOREIGN KEY (model_id) REFERENCES models(model_id)
                )
            """)

            conn.commit()

    def register_model(self, metadata: ModelMetadata, model_object: Any,
                      model_path: Optional[str] = None) -> str:
        """
        Register a new model in the registry

        Args:
            metadata: Model metadata
            model_object: Trained model object
            model_path: Path to save model (optional)

        Returns:
            model_id
        """
        # Save model to disk
        if model_path is None:
            model_path = f"models/{metadata.model_name}_v{metadata.version}.pkl"

        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(model_object, f)

        # Store in database
        with sqlite3.connect(self.database_path) as conn:
            conn.execute("""
                INSERT INTO models (
                    model_id, model_name, model_type, version, created_at,
                    created_by, dataset_version, training_data_hash,
                    feature_names, hyperparameters, performance_metrics,
                    status, approval_status, description, tags, model_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.model_id,
                metadata.model_name,
                metadata.model_type,
                metadata.version,
                metadata.created_at,
                metadata.created_by,
                metadata.dataset_version,
                metadata.training_data_hash,
                json.dumps(metadata.feature_names),
                json.dumps(metadata.hyperparameters),
                json.dumps(metadata.performance_metrics),
                metadata.status,
                metadata.approval_status,
                metadata.description,
                json.dumps(metadata.tags),
                model_path
            ))

            # Add version history
            conn.execute("""
                INSERT INTO model_versions (
                    model_id, version, created_at, performance_metrics
                ) VALUES (?, ?, ?, ?)
            """, (
                metadata.model_id,
                metadata.version,
                metadata.created_at,
                json.dumps(metadata.performance_metrics)
            ))

            conn.commit()

        logger.info(f"Registered model: {metadata.model_id}")
        return metadata.model_id

    def load_model(self, model_id: str) -> Tuple[Any, ModelMetadata]:
        """
        Load model from registry

        Args:
            model_id: Model identifier

        Returns:
            (model_object, metadata)
        """
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM models WHERE model_id = ?
            """, (model_id,))

            row = cursor.fetchone()

            if row is None:
                raise ValueError(f"Model {model_id} not found")

            # Parse metadata
            metadata = ModelMetadata(
                model_id=row[0],
                model_name=row[1],
                model_type=row[2],
                version=row[3],
                created_at=datetime.fromisoformat(row[4]),
                created_by=row[5],
                dataset_version=row[6],
                training_data_hash=row[7],
                feature_names=json.loads(row[8]),
                hyperparameters=json.loads(row[9]),
                performance_metrics=json.loads(row[10]),
                status=row[11],
                approval_status=row[12],
                description=row[13],
                tags=json.loads(row[14])
            )

            model_path = row[15]

        # Load model object
        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        return model, metadata

    def approve_model(self, model_id: str, approver: str, comments: str = ""):
        """Approve model for production deployment"""
        with sqlite3.connect(self.database_path) as conn:
            conn.execute("""
                UPDATE models SET approval_status = 'approved'
                WHERE model_id = ?
            """, (model_id,))

            conn.execute("""
                INSERT INTO model_approvals (
                    model_id, approver, approval_date, status, comments
                ) VALUES (?, ?, ?, 'approved', ?)
            """, (model_id, approver, datetime.now(), comments))

            conn.commit()

        logger.info(f"Model {model_id} approved by {approver}")

    def promote_to_production(self, model_id: str):
        """Promote model to production status"""
        with sqlite3.connect(self.database_path) as conn:
            # Check if approved
            cursor = conn.execute("""
                SELECT approval_status FROM models WHERE model_id = ?
            """, (model_id,))

            row = cursor.fetchone()
            if row is None or row[0] != 'approved':
                raise ValueError("Model must be approved before production deployment")

            conn.execute("""
                UPDATE models SET status = 'production'
                WHERE model_id = ?
            """, (model_id,))

            conn.execute("""
                UPDATE model_versions SET deployment_date = ?
                WHERE model_id = ? AND deployment_date IS NULL
            """, (datetime.now(), model_id))

            conn.commit()

        logger.info(f"Model {model_id} promoted to production")

    def get_production_models(self) -> List[ModelMetadata]:
        """Get all models currently in production"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM models WHERE status = 'production'
            """)

            models = []
            for row in cursor.fetchall():
                metadata = ModelMetadata(
                    model_id=row[0],
                    model_name=row[1],
                    model_type=row[2],
                    version=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    created_by=row[5],
                    dataset_version=row[6],
                    training_data_hash=row[7],
                    feature_names=json.loads(row[8]),
                    hyperparameters=json.loads(row[9]),
                    performance_metrics=json.loads(row[10]),
                    status=row[11],
                    approval_status=row[12],
                    description=row[13],
                    tags=json.loads(row[14])
                )
                models.append(metadata)

        return models


class DriftDetector:
    """
    Detect feature drift and concept drift
    Trigger automated retraining when drift is detected
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Args:
            significance_level: P-value threshold for drift detection
        """
        self.significance_level = significance_level
        self.reference_statistics = {}

    def fit_reference(self, X: pd.DataFrame, name: str = 'reference'):
        """
        Fit reference distribution for drift detection

        Args:
            X: Reference data (training data)
            name: Reference dataset name
        """
        self.reference_statistics[name] = {
            'mean': X.mean().to_dict(),
            'std': X.std().to_dict(),
            'min': X.min().to_dict(),
            'max': X.max().to_dict(),
            'quantiles': {
                '25': X.quantile(0.25).to_dict(),
                '50': X.quantile(0.50).to_dict(),
                '75': X.quantile(0.75).to_dict()
            }
        }

        logger.info(f"Fitted reference distribution: {name}")

    def detect_feature_drift(self, X_current: pd.DataFrame,
                            reference_name: str = 'reference',
                            method: str = 'ks') -> Dict[str, Any]:
        """
        Detect feature drift using statistical tests

        Args:
            X_current: Current data
            reference_name: Reference dataset name
            method: 'ks' (Kolmogorov-Smirnov) or 'chi2'

        Returns:
            Drift detection results
        """
        if reference_name not in self.reference_statistics:
            raise ValueError(f"Reference {reference_name} not found")

        ref_stats = self.reference_statistics[reference_name]

        drift_detected = {}
        drift_scores = {}

        for column in X_current.columns:
            if column not in ref_stats['mean']:
                continue

            # Kolmogorov-Smirnov test
            if method == 'ks':
                # Compare distributions
                # Note: We don't have the original data, so we use statistical approximation
                # In production, store reference samples or use more sophisticated methods

                current_mean = X_current[column].mean()
                current_std = X_current[column].std()

                ref_mean = ref_stats['mean'][column]
                ref_std = ref_stats['std'][column]

                # Z-test for mean shift
                z_score = abs(current_mean - ref_mean) / (ref_std / np.sqrt(len(X_current)))
                p_value = 2 * (1 - stats.norm.cdf(z_score))

                drift_detected[column] = p_value < self.significance_level
                drift_scores[column] = {
                    'p_value': p_value,
                    'z_score': z_score,
                    'mean_shift': current_mean - ref_mean,
                    'std_ratio': current_std / ref_std if ref_std > 0 else 0
                }

        # Overall drift assessment
        drift_ratio = sum(drift_detected.values()) / len(drift_detected) if drift_detected else 0

        return {
            'drift_detected': drift_ratio > 0.2,  # More than 20% features drifted
            'drift_ratio': drift_ratio,
            'drifted_features': [k for k, v in drift_detected.items() if v],
            'drift_scores': drift_scores,
            'recommendation': 'RETRAIN' if drift_ratio > 0.2 else 'MONITOR'
        }

    def detect_concept_drift(self, y_true: np.ndarray, y_pred: np.ndarray,
                            reference_performance: Dict[str, float],
                            threshold: float = 0.1) -> Dict[str, Any]:
        """
        Detect concept drift by comparing current vs reference performance

        Args:
            y_true: True labels
            y_pred: Predicted labels
            reference_performance: Reference metrics from training
            threshold: Degradation threshold (e.g., 10% drop)

        Returns:
            Concept drift results
        """
        # Calculate current performance
        current_performance = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }

        # Compare with reference
        performance_degradation = {}
        for metric, current_val in current_performance.items():
            if metric in reference_performance:
                ref_val = reference_performance[metric]
                degradation = (ref_val - current_val) / ref_val if ref_val > 0 else 0
                performance_degradation[metric] = degradation

        # Check if significant degradation
        avg_degradation = np.mean(list(performance_degradation.values()))
        concept_drift_detected = avg_degradation > threshold

        return {
            'concept_drift_detected': concept_drift_detected,
            'current_performance': current_performance,
            'reference_performance': reference_performance,
            'performance_degradation': performance_degradation,
            'avg_degradation': avg_degradation,
            'recommendation': 'RETRAIN_URGENT' if avg_degradation > 0.2 else 'RETRAIN' if concept_drift_detected else 'MONITOR'
        }


class AutomatedRetrainingPipeline:
    """
    Automated model retraining pipeline
    Triggered by drift detection or scheduled intervals
    """

    def __init__(self, model_registry: ModelRegistry,
                 drift_detector: DriftDetector):
        """
        Args:
            model_registry: Model registry instance
            drift_detector: Drift detector instance
        """
        self.model_registry = model_registry
        self.drift_detector = drift_detector
        self.retraining_queue = []

    def schedule_retraining(self, model_id: str, reason: str, priority: str = 'normal'):
        """
        Schedule model for retraining

        Args:
            model_id: Model to retrain
            reason: Reason for retraining (drift, scheduled, manual)
            priority: 'low', 'normal', 'high', 'urgent'
        """
        self.retraining_queue.append({
            'model_id': model_id,
            'scheduled_at': datetime.now(),
            'reason': reason,
            'priority': priority,
            'status': 'queued'
        })

        logger.info(f"Scheduled retraining for {model_id}: {reason} (priority: {priority})")

    def check_drift_and_schedule(self, model_id: str, X_current: pd.DataFrame,
                                 y_true: Optional[np.ndarray] = None,
                                 y_pred: Optional[np.ndarray] = None):
        """
        Check for drift and schedule retraining if needed

        Args:
            model_id: Model ID to check
            X_current: Current feature data
            y_true: True labels (for concept drift)
            y_pred: Predictions (for concept drift)
        """
        # Load model metadata
        _, metadata = self.model_registry.load_model(model_id)

        # Feature drift check
        feature_drift = self.drift_detector.detect_feature_drift(X_current)

        if feature_drift['drift_detected']:
            self.schedule_retraining(
                model_id,
                f"Feature drift detected: {feature_drift['drift_ratio']:.1%} features drifted",
                priority='high' if feature_drift['drift_ratio'] > 0.4 else 'normal'
            )

        # Concept drift check (if labels available)
        if y_true is not None and y_pred is not None:
            concept_drift = self.drift_detector.detect_concept_drift(
                y_true, y_pred, metadata.performance_metrics
            )

            if concept_drift['concept_drift_detected']:
                priority = 'urgent' if concept_drift['recommendation'] == 'RETRAIN_URGENT' else 'high'
                self.schedule_retraining(
                    model_id,
                    f"Concept drift detected: {concept_drift['avg_degradation']:.1%} performance drop",
                    priority=priority
                )

    def get_retraining_queue(self, status: Optional[str] = None) -> List[Dict]:
        """Get retraining queue, optionally filtered by status"""
        if status is None:
            return self.retraining_queue
        return [item for item in self.retraining_queue if item['status'] == status]


if __name__ == "__main__":
    logger.info("MLOps Model Management System - Production Grade")

    # Example usage
    registry = ModelRegistry()

    # Register a model
    metadata = ModelMetadata(
        model_id="stock_predictor_v1.0",
        model_name="stock_predictor",
        model_type="xgboost",
        version="1.0",
        created_at=datetime.now(),
        created_by="quant_team",
        dataset_version="2024Q1",
        training_data_hash="abc123",
        feature_names=["price", "volume", "rsi"],
        hyperparameters={"max_depth": 5, "learning_rate": 0.1},
        performance_metrics={"accuracy": 0.85, "sharpe": 1.5},
        status="development",
        approval_status="pending",
        description="Stock price predictor using XGBoost",
        tags=["stocks", "prediction", "xgboost"]
    )

    # Drift detection example
    drift_detector = DriftDetector()

    # Fit reference
    X_train = pd.DataFrame(np.random.randn(1000, 10), columns=[f'feature_{i}' for i in range(10)])
    drift_detector.fit_reference(X_train)

    # Check drift on new data
    X_current = pd.DataFrame(np.random.randn(100, 10) + 0.5, columns=[f'feature_{i}' for i in range(10)])  # Shifted
    drift_result = drift_detector.detect_feature_drift(X_current)

    print(f"\nDrift Detection Results:")
    print(f"Drift detected: {drift_result['drift_detected']}")
    print(f"Drift ratio: {drift_result['drift_ratio']:.2%}")
    print(f"Drifted features: {drift_result['drifted_features']}")
    print(f"Recommendation: {drift_result['recommendation']}")
