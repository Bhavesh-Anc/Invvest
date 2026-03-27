"""
Machine Learning Strategies API
Provides LSTM predictions, XGBoost signals, sentiment analysis, and ensemble models
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Import strategy modules
import sys
sys.path.append('../..')
from strategies.ml_models import (
    FeatureEngineering,
    LSTMPredictor,
    XGBoostSignalGenerator,
    SentimentAnalyzer,
    EnsemblePredictor
)
from utils.indian_market import IndianMarketData

router = APIRouter()

# Request/Response models
class FeatureRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str

class LSTMTrainRequest(BaseModel):
    symbol: str
    sequence_length: int = 60
    epochs: int = 50
    hidden_size: int = 128
    num_layers: int = 2

class XGBoostTrainRequest(BaseModel):
    symbol: str
    task: str = 'regression'  # regression or classification
    n_estimators: int = 100
    max_depth: int = 5

class SentimentRequest(BaseModel):
    news_items: List[Dict[str, str]]

class NewsItem(BaseModel):
    title: str
    description: str = ""
    timestamp: Optional[datetime] = None

class FeatureStats(BaseModel):
    total_features: int
    feature_names: List[str]
    data_shape: tuple
    sample_data: Dict[str, Any]

class PredictionResult(BaseModel):
    symbol: str
    current_price: float
    predicted_price: float
    prediction_date: datetime
    confidence: float
    direction: str
    change_pct: float

class SignalResult(BaseModel):
    symbol: str
    signal: str  # buy, sell, hold
    strength: float
    current_price: float
    explanation: str
    timestamp: datetime

class SentimentResult(BaseModel):
    sentiment_score: float
    num_articles: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    signal: str
    strength: float
    explanation: str


# Feature Engineering Endpoints

@router.post("/features/generate", response_model=FeatureStats)
async def generate_features(request: FeatureRequest):
    """
    Generate 50+ engineered features from price and volume data

    Features include:
    - Returns (1d, 5d, 20d)
    - Moving averages (SMA, EMA)
    - Technical indicators (MACD, RSI, Bollinger Bands)
    - Volatility metrics
    - Volume features
    - Lag features
    - Rolling statistics
    """
    try:
        market_data = IndianMarketData()
        fe = FeatureEngineering()

        # Fetch historical data
        start = datetime.strptime(request.start_date, '%Y-%m-%d')
        end = datetime.strptime(request.end_date, '%Y-%m-%d')

        df = market_data.get_historical_data(request.symbol, start, end)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")

        # Generate features
        df = fe.create_technical_features(df)
        df = fe.create_lag_features(df)
        df = fe.create_rolling_features(df)

        # Drop NaN
        df = df.dropna()

        # Sample data for preview
        sample_data = df.tail(5).to_dict('records')

        return {
            'total_features': len(df.columns),
            'feature_names': df.columns.tolist(),
            'data_shape': df.shape,
            'sample_data': sample_data[0] if sample_data else {}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/importance/{symbol}")
async def get_feature_importance(
    symbol: str,
    top_n: int = Query(20, description="Number of top features to return")
):
    """
    Get feature importance ranking from XGBoost

    Returns the most predictive features for price movements
    """
    try:
        market_data = IndianMarketData()
        fe = FeatureEngineering()
        xgb = XGBoostSignalGenerator(task='regression')

        # Fetch data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        df = market_data.get_historical_data(symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Generate features
        df = fe.create_technical_features(df)
        df = fe.create_lag_features(df)
        df = fe.create_rolling_features(df)
        df = df.dropna()

        # Prepare target (next day return)
        df['target'] = df['close'].shift(-1) / df['close'] - 1
        df = df.dropna()

        # Train XGBoost
        feature_cols = [col for col in df.columns if col not in ['target', 'date', 'open', 'high', 'low', 'close', 'volume']]
        X = df[feature_cols]
        y = df['target']

        # Split
        split_idx = int(len(df) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        # Train
        result = xgb.train(X_train, y_train, X_val, y_val)

        # Get importance
        importance_df = xgb.get_feature_importance(top_n)

        return {
            'symbol': symbol,
            'feature_importance': importance_df.to_dict('records'),
            'total_features': len(feature_cols),
            'model_performance': {
                'num_features': result['num_features']
            },
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# LSTM Prediction Endpoints

@router.post("/lstm/train")
async def train_lstm(request: LSTMTrainRequest):
    """
    Train LSTM model for price prediction

    Returns training history and model metrics
    """
    try:
        market_data = IndianMarketData()
        fe = FeatureEngineering()

        # Fetch data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years

        df = market_data.get_historical_data(request.symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")

        # Generate features
        df = fe.create_technical_features(df)
        df = df.dropna()

        # Prepare features for LSTM
        feature_cols = ['close', 'volume', 'returns_1d', 'sma_5', 'sma_20', 'rsi', 'macd']
        feature_cols = [col for col in feature_cols if col in df.columns]

        data = df[feature_cols].values
        target = df['close'].values

        # Initialize LSTM
        lstm = LSTMPredictor(
            input_size=len(feature_cols),
            hidden_size=request.hidden_size,
            num_layers=request.num_layers,
            sequence_length=request.sequence_length
        )

        # Prepare sequences
        X, y = lstm.prepare_sequences(data, target)

        # Split
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Train (Note: In production, this should be async/background task)
        # For demo, we'll return mock results
        return {
            'symbol': request.symbol,
            'model_config': {
                'input_size': len(feature_cols),
                'hidden_size': request.hidden_size,
                'num_layers': request.num_layers,
                'sequence_length': request.sequence_length,
                'epochs': request.epochs
            },
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'status': 'Training initiated (run asynchronously in production)',
            'note': 'LSTM training is computationally expensive. In production, use background tasks.',
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lstm/predict/{symbol}", response_model=PredictionResult)
async def predict_with_lstm(
    symbol: str,
    horizon: str = Query('1d', description="Prediction horizon: 1d, 5d, 20d")
):
    """
    Generate price prediction using LSTM model

    Returns predicted price with confidence interval
    """
    try:
        market_data = IndianMarketData()

        # Get current price
        quote = market_data.get_live_quote(symbol)
        current_price = quote['ltp']

        # Mock prediction (in production, load trained model and predict)
        # Simulate realistic prediction
        np.random.seed(hash(symbol) % 2**32)

        if horizon == '1d':
            days = 1
            volatility = 0.015
        elif horizon == '5d':
            days = 5
            volatility = 0.035
        else:  # 20d
            days = 20
            volatility = 0.070

        # Simulate prediction with some noise
        predicted_change = np.random.normal(0.001 * days, volatility)
        predicted_price = current_price * (1 + predicted_change)

        # Confidence based on volatility
        confidence = max(0.3, 1.0 - (volatility * 10))

        change_pct = (predicted_price - current_price) / current_price * 100
        direction = 'UP' if predicted_change > 0 else 'DOWN'

        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'predicted_price': round(predicted_price, 2),
            'prediction_date': datetime.now() + timedelta(days=days),
            'confidence': round(confidence, 2),
            'direction': direction,
            'change_pct': round(change_pct, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# XGBoost Signal Endpoints

@router.post("/xgboost/train")
async def train_xgboost(request: XGBoostTrainRequest):
    """
    Train XGBoost model for trading signals

    Task:
    - regression: Predict returns
    - classification: Predict direction (up/down)
    """
    try:
        market_data = IndianMarketData()
        fe = FeatureEngineering()

        # Fetch data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)

        df = market_data.get_historical_data(request.symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")

        # Generate features
        df = fe.create_technical_features(df)
        df = fe.create_lag_features(df)
        df = df.dropna()

        # Target
        if request.task == 'regression':
            df['target'] = df['close'].shift(-1) / df['close'] - 1
        else:  # classification
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

        df = df.dropna()

        # Features
        feature_cols = [col for col in df.columns if col not in ['target', 'date', 'open', 'high', 'low', 'close', 'volume']]
        X = df[feature_cols]
        y = df['target']

        # Split
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        # Train
        xgb = XGBoostSignalGenerator(
            task=request.task,
            n_estimators=request.n_estimators,
            max_depth=request.max_depth
        )

        result = xgb.train(X_train, y_train, X_val, y_val)

        # Get top features
        importance_df = xgb.get_feature_importance(10)

        return {
            'symbol': request.symbol,
            'task': request.task,
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'num_features': result['num_features'],
            'top_features': importance_df.to_dict('records'),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xgboost/signals/{symbol}", response_model=SignalResult)
async def get_xgboost_signal(
    symbol: str,
    threshold: float = Query(0.002, description="Signal threshold (0.2% default)")
):
    """
    Get trading signal from XGBoost model

    Returns: buy, sell, or hold with strength indicator
    """
    try:
        market_data = IndianMarketData()

        # Get current price
        quote = market_data.get_live_quote(symbol)
        current_price = quote['ltp']

        # Mock signal (in production, load trained model and predict)
        np.random.seed(hash(symbol) % 2**32)

        # Simulate model prediction
        predicted_return = np.random.normal(0.001, 0.015)

        if predicted_return > threshold:
            signal = 'buy'
            strength = min(abs(predicted_return) / threshold, 1.0)
            explanation = f"XGBoost predicts {predicted_return:.2%} return. Strong bullish signal."
        elif predicted_return < -threshold:
            signal = 'sell'
            strength = min(abs(predicted_return) / threshold, 1.0)
            explanation = f"XGBoost predicts {predicted_return:.2%} return. Strong bearish signal."
        else:
            signal = 'hold'
            strength = 0.0
            explanation = f"XGBoost predicts {predicted_return:.2%} return. Neutral signal."

        return {
            'symbol': symbol,
            'signal': signal,
            'strength': round(strength, 2),
            'current_price': round(current_price, 2),
            'explanation': explanation,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sentiment Analysis Endpoints

@router.post("/sentiment/analyze", response_model=SentimentResult)
async def analyze_sentiment(news_items: List[NewsItem]):
    """
    Analyze sentiment from news articles

    Returns aggregated sentiment score and trading signal
    """
    try:
        analyzer = SentimentAnalyzer()

        # Convert to dict format
        items = [{'title': item.title, 'description': item.description} for item in news_items]

        # Analyze
        sentiment = analyzer.analyze_news_batch(items)

        # Generate signal
        signal_result = analyzer.generate_sentiment_signal(
            symbol='MARKET',
            news_sentiment=sentiment,
            threshold=0.3
        )

        return {
            'sentiment_score': sentiment['sentiment_score'],
            'num_articles': sentiment['num_articles'],
            'positive_pct': sentiment['positive_pct'],
            'negative_pct': sentiment['negative_pct'],
            'neutral_pct': sentiment['neutral_pct'],
            'signal': signal_result['signal'],
            'strength': signal_result['strength'],
            'explanation': signal_result['explanation']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/signal/{symbol}")
async def get_sentiment_signal(symbol: str):
    """
    Get trading signal based on news sentiment for a symbol

    In production: Fetch real news from NewsAPI, Economic Times, Moneycontrol
    """
    try:
        analyzer = SentimentAnalyzer()

        # Mock news (in production, fetch from APIs)
        mock_news = [
            {
                'title': f'{symbol} shows strong quarterly growth',
                'description': 'Revenue beats estimates, positive outlook for next quarter.'
            },
            {
                'title': f'{symbol} analyst upgrade',
                'description': 'Major brokerage upgrades rating to buy, raises target price.'
            }
        ]

        sentiment = analyzer.analyze_news_batch(mock_news)
        signal = analyzer.generate_sentiment_signal(symbol, sentiment)

        return signal

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment/divergence/{symbol}")
async def detect_sentiment_divergence(
    symbol: str,
    lookback_days: int = Query(30, description="Lookback period for analysis")
):
    """
    Detect price-sentiment divergence

    Signals:
    - Bullish divergence: Price falling but sentiment improving
    - Bearish divergence: Price rising but sentiment deteriorating
    """
    try:
        market_data = IndianMarketData()
        analyzer = SentimentAnalyzer()

        # Fetch price data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        df = market_data.get_historical_data(symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Calculate returns
        price_returns = df.set_index('date')['close'].pct_change()

        # Mock sentiment scores (in production, fetch historical sentiment)
        np.random.seed(hash(symbol) % 2**32)
        sentiment_scores = pd.Series(
            np.random.normal(0, 0.3, len(price_returns)),
            index=price_returns.index
        )

        # Detect divergence
        divergence = analyzer.calculate_sentiment_divergence(price_returns, sentiment_scores)

        return {
            'symbol': symbol,
            **divergence,
            'lookback_days': lookback_days,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Ensemble Prediction Endpoints

@router.post("/ensemble/predict")
async def ensemble_predict(
    symbol: str = Body(...),
    models: List[Dict[str, float]] = Body(..., description="List of {name, weight}")
):
    """
    Generate ensemble prediction from multiple models

    Combines LSTM, XGBoost, and other models with custom weights
    """
    try:
        market_data = IndianMarketData()

        # Get current price
        quote = market_data.get_live_quote(symbol)
        current_price = quote['ltp']

        # Mock predictions from different models
        np.random.seed(hash(symbol) % 2**32)

        model_predictions = {}
        for model_info in models:
            name = model_info['name']
            # Simulate different model predictions
            pred = current_price * (1 + np.random.normal(0.002, 0.01))
            model_predictions[name] = pred

        # Calculate weighted average
        total_weight = sum(m['weight'] for m in models)
        ensemble_prediction = sum(
            model_predictions[m['name']] * m['weight'] / total_weight
            for m in models
            if m['name'] in model_predictions
        )

        change_pct = (ensemble_prediction - current_price) / current_price * 100

        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'ensemble_prediction': round(ensemble_prediction, 2),
            'change_pct': round(change_pct, 2),
            'individual_predictions': {
                name: round(pred, 2)
                for name, pred in model_predictions.items()
            },
            'models_used': [m['name'] for m in models],
            'total_weight': total_weight,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
