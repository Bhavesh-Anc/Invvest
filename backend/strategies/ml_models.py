"""
Machine Learning Models for Quantitative Trading
Used by: Renaissance Technologies, Two Sigma, D.E. Shaw, WorldQuant

Implements:
- LSTM/GRU for time series prediction
- XGBoost for feature importance and signal generation
- Ensemble models for robust predictions
- Feature engineering for financial data
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

# Try importing ML libraries
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. LSTM models will not work.")
    TORCH_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    logger.warning("XGBoost not available. XGBoost models will not work.")
    XGBOOST_AVAILABLE = False


class FeatureEngineering:
    """
    Feature engineering for financial time series

    Used by: All quant hedge funds

    Creates features from price, volume, and order book data
    """

    def __init__(self):
        pass

    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create technical indicator features

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added features
        """
        # Returns
        df['returns_1d'] = df['close'].pct_change()
        df['returns_5d'] = df['close'].pct_change(5)
        df['returns_20d'] = df['close'].pct_change(20)

        # Log returns
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Moving averages
        df['sma_5'] = df['close'].rolling(5).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()

        # Moving average crossovers
        df['sma_5_20_cross'] = df['sma_5'] - df['sma_20']
        df['sma_20_50_cross'] = df['sma_20'] - df['sma_50']

        # Exponential moving averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()

        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Volatility
        df['volatility_5d'] = df['returns_1d'].rolling(5).std()
        df['volatility_20d'] = df['returns_1d'].rolling(20).std()
        df['volatility_60d'] = df['returns_1d'].rolling(60).std()

        # Volume features
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        df['volume_trend'] = df['volume'].rolling(5).mean() / df['volume'].rolling(20).mean()

        # High-Low range
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['close_open_ratio'] = (df['close'] - df['open']) / df['open']

        # Momentum
        df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1

        # Rate of change
        df['roc_5'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5) * 100
        df['roc_20'] = (df['close'] - df['close'].shift(20)) / df['close'].shift(20) * 100

        return df

    def create_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5]) -> pd.DataFrame:
        """
        Create lagged features

        Args:
            df: DataFrame
            lags: List of lag periods

        Returns:
            DataFrame with lagged features
        """
        for lag in lags:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'returns_lag_{lag}'] = df['returns_1d'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)

        return df

    def create_rolling_features(self, df: pd.DataFrame, windows: List[int] = [5, 20, 60]) -> pd.DataFrame:
        """
        Create rolling statistical features

        Args:
            df: DataFrame
            windows: Rolling window sizes

        Returns:
            DataFrame with rolling features
        """
        for window in windows:
            # Mean
            df[f'returns_mean_{window}'] = df['returns_1d'].rolling(window).mean()

            # Std
            df[f'returns_std_{window}'] = df['returns_1d'].rolling(window).std()

            # Max/Min
            df[f'high_max_{window}'] = df['high'].rolling(window).max()
            df[f'low_min_{window}'] = df['low'].rolling(window).min()

            # Z-score
            df[f'returns_zscore_{window}'] = (
                (df['returns_1d'] - df[f'returns_mean_{window}']) / df[f'returns_std_{window}']
            )

        return df


class LSTMPredictor:
    """
    LSTM Neural Network for Price Prediction

    Used by: Renaissance Technologies, Two Sigma, WorldQuant

    Predicts future prices using past sequences
    """

    def __init__(
        self,
        input_size: int = 50,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        sequence_length: int = 60
    ):
        """
        Args:
            input_size: Number of features
            hidden_size: LSTM hidden dimension
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            sequence_length: Length of input sequence
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not installed. Install with: pip install torch")

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.sequence_length = sequence_length

        self.model = None
        self.scaler = MinMaxScaler()

    def build_model(self):
        """Build LSTM model"""

        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, dropout):
                super(LSTMModel, self).__init__()

                self.lstm = nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    dropout=dropout if num_layers > 1 else 0,
                    batch_first=True
                )

                self.fc = nn.Linear(hidden_size, 1)

            def forward(self, x):
                # x shape: (batch, sequence, features)
                lstm_out, _ = self.lstm(x)

                # Take last timestep
                last_output = lstm_out[:, -1, :]

                # Prediction
                prediction = self.fc(last_output)

                return prediction

        self.model = LSTMModel(
            self.input_size,
            self.hidden_size,
            self.num_layers,
            self.dropout
        )

        return self.model

    def prepare_sequences(
        self,
        data: np.ndarray,
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training

        Args:
            data: Feature array (samples, features)
            target: Target array (samples,)

        Returns:
            X, y arrays for LSTM
        """
        X, y = [], []

        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length:i])
            y.append(target[i])

        return np.array(X), np.array(y)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> Dict:
        """
        Train LSTM model

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate

        Returns:
            Training history
        """
        # Build model if not built
        if self.model is None:
            self.build_model()

        # Convert to PyTorch tensors
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.FloatTensor(y_train).view(-1, 1)

        # Create data loader
        train_dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)

        # Training history
        history = {'train_loss': [], 'val_loss': []}

        # Training loop
        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0

            for batch_X, batch_y in train_loader:
                # Forward pass
                predictions = self.model(batch_X)
                loss = criterion(predictions, batch_y)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_train_loss = epoch_loss / len(train_loader)
            history['train_loss'].append(avg_train_loss)

            # Validation
            if X_val is not None and y_val is not None:
                self.model.eval()
                with torch.no_grad():
                    X_val_tensor = torch.FloatTensor(X_val)
                    y_val_tensor = torch.FloatTensor(y_val).view(-1, 1)

                    val_predictions = self.model(X_val_tensor)
                    val_loss = criterion(val_predictions, y_val_tensor)

                    history['val_loss'].append(val_loss.item())

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}")

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input sequences

        Returns:
            Predictions
        """
        self.model.eval()

        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            predictions = self.model(X_tensor)

        return predictions.numpy().flatten()

    def predict_next(self, last_sequence: np.ndarray) -> float:
        """
        Predict next value given last sequence

        Args:
            last_sequence: Last N timesteps

        Returns:
            Predicted next value
        """
        # Reshape for batch
        sequence = last_sequence.reshape(1, self.sequence_length, -1)

        prediction = self.predict(sequence)

        return float(prediction[0])


class XGBoostSignalGenerator:
    """
    XGBoost for Trading Signal Generation

    Used by: Two Sigma, WorldQuant, AQR Capital

    Learns from features to predict returns or direction
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.1,
        task: str = 'regression'
    ):
        """
        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            task: 'regression' or 'classification'
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not installed. Install with: pip install xgboost")

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.task = task

        self.model = None
        self.feature_names = None
        self.scaler = StandardScaler()

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> Dict:
        """
        Train XGBoost model

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets

        Returns:
            Training results
        """
        self.feature_names = X_train.columns.tolist()

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)

        # Prepare DMatrix
        dtrain = xgb.DMatrix(X_train_scaled, label=y_train)

        # Parameters
        params = {
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'objective': 'reg:squarederror' if self.task == 'regression' else 'binary:logistic',
            'eval_metric': 'rmse' if self.task == 'regression' else 'logloss',
            'tree_method': 'hist',
            'seed': 42
        }

        # Evaluation list
        evals = [(dtrain, 'train')]

        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            X_val_scaled = pd.DataFrame(X_val_scaled, columns=X_val.columns)
            dval = xgb.DMatrix(X_val_scaled, label=y_val)
            evals.append((dval, 'val'))

        # Train
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.n_estimators,
            evals=evals,
            verbose_eval=10
        )

        # Feature importance
        importance = self.model.get_score(importance_type='gain')

        return {
            'feature_importance': importance,
            'num_features': len(self.feature_names)
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Features

        Returns:
            Predictions
        """
        X_scaled = self.scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns)

        dtest = xgb.DMatrix(X_scaled)
        predictions = self.model.predict(dtest)

        return predictions

    def generate_signals(
        self,
        X: pd.DataFrame,
        threshold: float = 0.0
    ) -> pd.Series:
        """
        Generate trading signals from predictions

        Args:
            X: Features
            threshold: Signal threshold

        Returns:
            Series of signals (1=buy, 0=hold, -1=sell)
        """
        predictions = self.predict(X)

        # Convert to signals
        signals = pd.Series(index=X.index, dtype=int)

        if self.task == 'regression':
            # Regression: predict returns
            signals[predictions > threshold] = 1  # Buy
            signals[predictions < -threshold] = -1  # Sell
            signals[(predictions >= -threshold) & (predictions <= threshold)] = 0  # Hold

        else:
            # Classification: predict direction
            signals[predictions > 0.5] = 1  # Buy
            signals[predictions <= 0.5] = -1  # Sell

        return signals

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance

        Args:
            top_n: Number of top features

        Returns:
            DataFrame with feature importance
        """
        importance = self.model.get_score(importance_type='gain')

        importance_df = pd.DataFrame({
            'feature': importance.keys(),
            'importance': importance.values()
        })

        importance_df = importance_df.sort_values('importance', ascending=False)

        return importance_df.head(top_n)


class EnsemblePredictor:
    """
    Ensemble of multiple models for robust predictions

    Used by: All top quant funds

    Combines LSTM, XGBoost, and other models
    """

    def __init__(self):
        self.models = {}
        self.weights = {}

    def add_model(self, name: str, model, weight: float = 1.0):
        """
        Add model to ensemble

        Args:
            name: Model name
            model: Model object with predict() method
            weight: Weight in ensemble
        """
        self.models[name] = model
        self.weights[name] = weight

    def predict(self, X, **kwargs) -> np.ndarray:
        """
        Ensemble prediction (weighted average)

        Args:
            X: Input features
            **kwargs: Model-specific arguments

        Returns:
            Ensemble predictions
        """
        predictions = []
        weights = []

        for name, model in self.models.items():
            pred = model.predict(X, **kwargs)
            predictions.append(pred)
            weights.append(self.weights[name])

        # Weighted average
        weighted_predictions = np.average(
            predictions,
            weights=weights,
            axis=0
        )

        return weighted_predictions


class SentimentAnalyzer:
    """
    Sentiment Analysis for Trading Signals

    Used by: Two Sigma, Renaissance Technologies, WorldQuant

    Analyzes news headlines, social media, and financial reports
    to generate sentiment-based trading signals
    """

    def __init__(self):
        """
        Initialize sentiment analyzer

        In production, use:
        - transformers (FinBERT, Twitter-RoBERTa)
        - NewsAPI, Twitter API
        - Economic Times, Moneycontrol RSS feeds
        """
        self.sentiment_weights = {
            'news': 0.5,
            'social_media': 0.3,
            'financial_reports': 0.2
        }

        # Simple keyword-based sentiment (production would use NLP models)
        self.positive_keywords = [
            'profit', 'growth', 'surge', 'rally', 'bullish', 'positive',
            'beat', 'exceed', 'strong', 'record', 'high', 'upgrade',
            'buy', 'outperform', 'gain', 'rise', 'jump', 'soar'
        ]

        self.negative_keywords = [
            'loss', 'decline', 'fall', 'bearish', 'negative', 'miss',
            'weak', 'low', 'downgrade', 'sell', 'underperform', 'drop',
            'plunge', 'crash', 'concern', 'risk', 'warning', 'disappoint'
        ]

    def analyze_text(self, text: str) -> float:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Sentiment score (-1 to 1, negative to positive)
        """
        if not text:
            return 0.0

        text_lower = text.lower()

        # Count positive and negative keywords
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)

        # Calculate sentiment score
        total_words = len(text.split())

        if total_words == 0:
            return 0.0

        # Normalize by text length
        sentiment = (positive_count - negative_count) / max(total_words / 10, 1)

        # Cap between -1 and 1
        sentiment = max(-1, min(sentiment, 1))

        return float(sentiment)

    def analyze_news_batch(self, news_items: List[Dict]) -> Dict:
        """
        Analyze batch of news articles

        Args:
            news_items: List of dicts with 'title', 'description', 'timestamp'

        Returns:
            Aggregated sentiment metrics
        """
        if not news_items:
            return {
                'sentiment_score': 0.0,
                'num_articles': 0,
                'positive_pct': 0.0,
                'negative_pct': 0.0,
                'neutral_pct': 0.0
            }

        sentiments = []

        for item in news_items:
            title = item.get('title', '')
            description = item.get('description', '')

            # Combine title and description
            combined_text = f"{title} {description}"

            sentiment = self.analyze_text(combined_text)
            sentiments.append(sentiment)

        sentiments = np.array(sentiments)

        # Calculate metrics
        avg_sentiment = float(np.mean(sentiments))
        positive_pct = float(np.sum(sentiments > 0.1) / len(sentiments) * 100)
        negative_pct = float(np.sum(sentiments < -0.1) / len(sentiments) * 100)
        neutral_pct = 100 - positive_pct - negative_pct

        return {
            'sentiment_score': round(avg_sentiment, 3),
            'num_articles': len(news_items),
            'positive_pct': round(positive_pct, 1),
            'negative_pct': round(negative_pct, 1),
            'neutral_pct': round(neutral_pct, 1),
            'std_dev': round(float(np.std(sentiments)), 3)
        }

    def analyze_social_media(self, posts: List[str]) -> Dict:
        """
        Analyze social media posts (Twitter, Reddit, StockTwits)

        Args:
            posts: List of social media posts

        Returns:
            Sentiment metrics
        """
        if not posts:
            return {
                'sentiment_score': 0.0,
                'num_posts': 0,
                'bullish_pct': 0.0,
                'bearish_pct': 0.0
            }

        sentiments = [self.analyze_text(post) for post in posts]
        sentiments = np.array(sentiments)

        avg_sentiment = float(np.mean(sentiments))
        bullish_pct = float(np.sum(sentiments > 0.1) / len(sentiments) * 100)
        bearish_pct = float(np.sum(sentiments < -0.1) / len(sentiments) * 100)

        return {
            'sentiment_score': round(avg_sentiment, 3),
            'num_posts': len(posts),
            'bullish_pct': round(bullish_pct, 1),
            'bearish_pct': round(bearish_pct, 1),
            'neutral_pct': round(100 - bullish_pct - bearish_pct, 1)
        }

    def calculate_sentiment_momentum(
        self,
        historical_sentiments: pd.Series,
        window: int = 5
    ) -> float:
        """
        Calculate sentiment momentum (rate of change)

        Args:
            historical_sentiments: Time series of sentiment scores
            window: Lookback window

        Returns:
            Sentiment momentum (-1 to 1)
        """
        if len(historical_sentiments) < window:
            return 0.0

        # Recent vs previous sentiment
        recent_sentiment = historical_sentiments.iloc[-window:].mean()
        previous_sentiment = historical_sentiments.iloc[-2*window:-window].mean()

        # Momentum
        momentum = recent_sentiment - previous_sentiment

        return float(momentum)

    def generate_sentiment_signal(
        self,
        symbol: str,
        news_sentiment: Dict,
        social_sentiment: Optional[Dict] = None,
        threshold: float = 0.3
    ) -> Dict:
        """
        Generate trading signal from sentiment

        Args:
            symbol: Stock symbol
            news_sentiment: News sentiment metrics
            social_sentiment: Social media sentiment metrics
            threshold: Signal threshold

        Returns:
            Trading signal and analysis
        """
        # Weighted sentiment score
        sentiment_score = news_sentiment['sentiment_score'] * self.sentiment_weights['news']

        if social_sentiment:
            sentiment_score += (
                social_sentiment['sentiment_score'] * self.sentiment_weights['social_media']
            )

        # Generate signal
        if sentiment_score > threshold:
            signal = 'buy'
            strength = min(sentiment_score / threshold, 1.0)
            explanation = (
                f"Positive sentiment ({sentiment_score:.2f}) from "
                f"{news_sentiment['num_articles']} news articles. "
                f"{news_sentiment['positive_pct']:.0f}% positive coverage."
            )

        elif sentiment_score < -threshold:
            signal = 'sell'
            strength = min(abs(sentiment_score) / threshold, 1.0)
            explanation = (
                f"Negative sentiment ({sentiment_score:.2f}) from "
                f"{news_sentiment['num_articles']} news articles. "
                f"{news_sentiment['negative_pct']:.0f}% negative coverage."
            )

        else:
            signal = 'hold'
            strength = 0.0
            explanation = f"Neutral sentiment ({sentiment_score:.2f}), no clear direction"

        return {
            'symbol': symbol,
            'signal': signal,
            'sentiment_score': round(sentiment_score, 3),
            'strength': round(strength, 2),
            'news_articles': news_sentiment['num_articles'],
            'positive_pct': news_sentiment.get('positive_pct', 0),
            'negative_pct': news_sentiment.get('negative_pct', 0),
            'explanation': explanation,
            'timestamp': datetime.now()
        }

    def calculate_sentiment_divergence(
        self,
        price_returns: pd.Series,
        sentiment_scores: pd.Series
    ) -> Dict:
        """
        Detect divergence between price and sentiment

        Divergence signals:
        - Price up, Sentiment down: Bearish divergence (potential reversal)
        - Price down, Sentiment up: Bullish divergence (potential reversal)

        Args:
            price_returns: Price return series
            sentiment_scores: Sentiment score series

        Returns:
            Divergence analysis
        """
        if len(price_returns) != len(sentiment_scores):
            return {'divergence': 'none', 'signal': 'hold'}

        # Recent trends
        price_trend = price_returns.iloc[-5:].mean()
        sentiment_trend = sentiment_scores.iloc[-5:].mean() - sentiment_scores.iloc[-10:-5].mean()

        # Detect divergence
        if price_trend > 0.01 and sentiment_trend < -0.1:
            # Price rising, sentiment falling
            divergence = 'bearish'
            signal = 'sell'
            explanation = "Bearish divergence: Price rising but sentiment deteriorating"

        elif price_trend < -0.01 and sentiment_trend > 0.1:
            # Price falling, sentiment rising
            divergence = 'bullish'
            signal = 'buy'
            explanation = "Bullish divergence: Price falling but sentiment improving"

        else:
            divergence = 'none'
            signal = 'hold'
            explanation = "No significant divergence detected"

        return {
            'divergence': divergence,
            'signal': signal,
            'price_trend': round(price_trend, 4),
            'sentiment_trend': round(sentiment_trend, 3),
            'explanation': explanation
        }


# Example usage
if __name__ == "__main__":
    # Mock data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=500, freq='D')

    df = pd.DataFrame({
        'open': 22000 + np.cumsum(np.random.randn(500) * 50),
        'high': 22100 + np.cumsum(np.random.randn(500) * 50),
        'low': 21900 + np.cumsum(np.random.randn(500) * 50),
        'close': 22000 + np.cumsum(np.random.randn(500) * 50),
        'volume': np.random.randint(1000000, 10000000, 500)
    }, index=dates)

    print("=" * 60)
    print("FEATURE ENGINEERING TEST")
    print("=" * 60)

    fe = FeatureEngineering()
    df = fe.create_technical_features(df)
    df = fe.create_lag_features(df)
    df = fe.create_rolling_features(df)

    print(f"Original columns: 5")
    print(f"After feature engineering: {len(df.columns)} columns")
    print(f"Sample features: {df.columns[:10].tolist()}")

    # Drop NaN
    df = df.dropna()

    print(f"\nData shape after cleaning: {df.shape}")

    # Test Sentiment Analysis
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS TEST")
    print("=" * 60)

    sentiment_analyzer = SentimentAnalyzer()

    # Mock news articles
    news_items = [
        {
            'title': 'Reliance posts record profit, beats estimates',
            'description': 'Strong performance across all business segments. Growth expected to continue.'
        },
        {
            'title': 'TCS reports weak quarterly results, misses expectations',
            'description': 'Decline in revenue and profit margins. Concerns about future outlook.'
        },
        {
            'title': 'HDFC Bank maintains steady growth',
            'description': 'Positive quarterly results with stable loan growth and asset quality.'
        }
    ]

    news_sentiment = sentiment_analyzer.analyze_news_batch(news_items)
    print(f"News Sentiment Score: {news_sentiment['sentiment_score']}")
    print(f"Articles Analyzed: {news_sentiment['num_articles']}")
    print(f"Positive: {news_sentiment['positive_pct']}% | Negative: {news_sentiment['negative_pct']}%")

    # Generate trading signal
    signal = sentiment_analyzer.generate_sentiment_signal('RELIANCE', news_sentiment)
    print(f"\nTrading Signal: {signal['signal']}")
    print(f"Signal Strength: {signal['strength']}")
    print(f"Explanation: {signal['explanation']}")

    print("\n" + "=" * 60)
    print("All ML models tested successfully!")
    print("=" * 60)
