import pandas as pd
import numpy as np
import ta
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional
import warnings
from sklearn.preprocessing import StandardScaler, RobustScaler
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
import hashlib
import pickle
from functools import lru_cache
import json
from pathlib import Path
from datetime import datetime    # ← Add this import!
warnings.filterwarnings('ignore')

# ==================== INDIVIDUAL FEATURE CONFIGURATION ====================
INDIVIDUAL_FEATURE_CONFIG = {
    'lookback_periods': [5, 10, 20, 50, 100],
    'technical_indicators': [
        'sma', 'ema', 'rsi', 'macd', 'bollinger',
        'stochastic', 'atr', 'cci', 'williams_r', 'obv', 'vwap'
    ],
    'price_features': True,
    'volume_features': True,
    'volatility_features': True,
    'momentum_features': True,
    'trend_features': True,
    'pattern_features': True,
    'market_microstructure': True,
    'target_horizons': ['next_week', 'next_month', 'next_quarter', 'next_year'],
    'feature_selection_enabled': True,
    'cache_features': True,
    'cache_duration_hours': 24,
    'cache_dir': 'feature_cache_individual',
    'advanced_features': True,
    'max_features': 200
}

TARGET_HORIZONS = {
    'next_week': 5,
    'next_month': 21,
    'next_quarter': 63,
    'next_year': 252
}

class IndividualFeatureCache:
    """Cache manager for individual stock features"""
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or INDIVIDUAL_FEATURE_CONFIG['cache_dir'])
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _create_cache_key(self, symbol: str, data: pd.DataFrame) -> str:
        try:
            data_signature = {
                'symbol': symbol,
                'shape': data.shape,
                'start_date': str(data.index[0]) if len(data) > 0 else '',
                'end_date': str(data.index[-1]) if len(data) > 0 else '',
                'columns': list(data.columns),
                'last_close': float(data['Close'].iloc[-1]) if len(data) > 0 else 0
            }
            signature_str = json.dumps(data_signature, sort_keys=True, default=str)
            cache_key = hashlib.md5(signature_str.encode()).hexdigest()
            return f"{symbol}_{cache_key}"
        except Exception as e:
            logging.warning(f"Failed to create cache key for {symbol}: {e}")
            return f"{symbol}_{hash(str(data.shape))}"

    def get_cached_features(self, symbol: str, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        if not INDIVIDUAL_FEATURE_CONFIG['cache_features']:
            return None
        try:
            cache_key = self._create_cache_key(symbol, data)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                cache_age = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() / 3600
                if cache_age < INDIVIDUAL_FEATURE_CONFIG['cache_duration_hours']:
                    with open(cache_file, 'rb') as f:
                        cached = pickle.load(f)
                    logging.info(f"📊 Using cached features for {symbol}")
                    return cached['features']
                else:
                    cache_file.unlink()
        except Exception as e:
            logging.warning(f"Failed to load cached features for {symbol}: {e}")
        return None

    def save_features(self, symbol: str, data: pd.DataFrame, features: pd.DataFrame):
        if not INDIVIDUAL_FEATURE_CONFIG['cache_features']:
            return
        try:
            cache_key = self._create_cache_key(symbol, data)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            cache_data = {
                'symbol': symbol,
                'features': features,
                'created_at': datetime.now(),
                'data_shape': data.shape,
                'feature_shape': features.shape
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logging.info(f"💾 Cached features for {symbol}: {features.shape}")
        except Exception as e:
            logging.warning(f"Failed to cache features for {symbol}: {e}")

# ==================== INDIVIDUAL TECHNICAL INDICATORS ====================

class IndividualTechnicalIndicators:
    """Technical indicators optimized for individual stocks"""
    
    @staticmethod
    def calculate_sma(series: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(window=window, min_periods=1).mean()
    
    @staticmethod
    def calculate_ema(series: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(span=window).mean()
        avg_loss = loss.ewm(span=window).mean()
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD Indicator"""
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, window: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        
        return {
            'bb_upper': sma + (std * std_dev),
            'bb_middle': sma,
            'bb_lower': sma - (std * std_dev),
            'bb_width': (std * std_dev * 2) / (sma + 1e-10),
            'bb_position': (series - sma) / (std * std_dev + 1e-10)
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'stoch_k': k_percent.fillna(50),
            'stoch_d': d_percent.fillna(50)
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.ewm(span=window).mean()
        
        return atr.fillna(atr.mean())
    
    @staticmethod
    def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On Balance Volume"""
        price_change = close.diff()
        volume_direction = np.where(price_change > 0, volume,
                                  np.where(price_change < 0, -volume, 0))
        obv = pd.Series(volume_direction, index=close.index).cumsum()
        return obv

# ==================== INDIVIDUAL FEATURE ENGINEERING ====================

def engineer_features_individual(symbol: str, data: pd.DataFrame, config: Dict = None) -> pd.DataFrame:
    """Engineer features for individual stock"""
    
    if data.empty:
        logging.warning(f"Empty data provided for {symbol}")
        return pd.DataFrame()
    
    config = config or INDIVIDUAL_FEATURE_CONFIG
    
    # Check cache first
    cache_manager = IndividualFeatureCache()
    cached_features = cache_manager.get_cached_features(symbol, data)
    if cached_features is not None:
        return cached_features
    
    logging.info(f"🔧 Engineering features for {symbol} ({len(data)} records)")
    
    try:
        features_df = data.copy()
        
        # Basic price features
        if config.get('price_features', True):
            features_df = create_price_features_individual(features_df, config)
        
        # Technical indicators
        if config.get('technical_indicators'):
            features_df = create_technical_features_individual(features_df, config)
        
        # Volume features
        if config.get('volume_features', True):
            features_df = create_volume_features_individual(features_df, config)
        
        # Volatility features
        if config.get('volatility_features', True):
            features_df = create_volatility_features_individual(features_df, config)
        
        # Momentum features
        if config.get('momentum_features', True):
            features_df = create_momentum_features_individual(features_df, config)
        
        # Trend features
        if config.get('trend_features', True):
            features_df = create_trend_features_individual(features_df, config)
        
        # Pattern features
        if config.get('pattern_features', True):
            features_df = create_pattern_features_individual(features_df, config)
        
        # Market microstructure features
        if config.get('market_microstructure', True):
            features_df = create_microstructure_features_individual(features_df, config)
        
        # Target variables
        features_df = create_target_variables_individual(features_df, config)
        
        # Clean features
        features_df = clean_features_individual(features_df)
        
        # Cache features
        cache_manager.save_features(symbol, data, features_df)
        
        logging.info(f"✅ Generated {features_df.shape[1]} features for {symbol}")
        return features_df
        
    except Exception as e:
        logging.error(f"Feature engineering failed for {symbol}: {e}")
        return pd.DataFrame()

def create_price_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create price-based features for individual stock"""
    
    features_df = df.copy()
    
    # Price ratios
    features_df['high_low_ratio'] = df['High'] / (df['Low'] + 1e-10)
    features_df['open_close_ratio'] = df['Open'] / (df['Close'] + 1e-10)
    features_df['close_open_ratio'] = df['Close'] / (df['Open'] + 1e-10)
    
    # Price ranges
    features_df['daily_range'] = (df['High'] - df['Low']) / (df['Close'] + 1e-10)
    features_df['body_range'] = abs(df['Close'] - df['Open']) / (df['Close'] + 1e-10)
    features_df['upper_shadow'] = (df['High'] - np.maximum(df['Open'], df['Close'])) / (df['Close'] + 1e-10)
    features_df['lower_shadow'] = (np.minimum(df['Open'], df['Close']) - df['Low']) / (df['Close'] + 1e-10)
    
    # Price changes
    for period in config['lookback_periods']:
        if period < len(df):
            features_df[f'price_change_{period}'] = (df['Close'] - df['Close'].shift(period)) / (df['Close'].shift(period) + 1e-10)
            features_df[f'high_change_{period}'] = (df['High'] - df['High'].shift(period)) / (df['High'].shift(period) + 1e-10)
            features_df[f'low_change_{period}'] = (df['Low'] - df['Low'].shift(period)) / (df['Low'].shift(period) + 1e-10)
    
    return features_df

def create_technical_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create technical indicator features for individual stock"""
    
    features_df = df.copy()
    indicators = IndividualTechnicalIndicators()
    
    # Simple Moving Averages
    if 'sma' in config['technical_indicators']:
        for period in [5, 10, 20, 50]:
            if period < len(df):
                sma = indicators.calculate_sma(df['Close'], period)
                features_df[f'sma_{period}'] = sma
                features_df[f'price_sma_ratio_{period}'] = df['Close'] / (sma + 1e-10)
                features_df[f'sma_slope_{period}'] = sma.diff(5) / (sma.shift(5) + 1e-10)
    
    # Exponential Moving Averages
    if 'ema' in config['technical_indicators']:
        for period in [5, 10, 20, 50]:
            if period < len(df):
                ema = indicators.calculate_ema(df['Close'], period)
                features_df[f'ema_{period}'] = ema
                features_df[f'price_ema_ratio_{period}'] = df['Close'] / (ema + 1e-10)
    
    # RSI
    if 'rsi' in config['technical_indicators']:
        for period in [9, 14, 21]:
            if period < len(df):
                rsi = indicators.calculate_rsi(df['Close'], period)
                features_df[f'rsi_{period}'] = rsi
                features_df[f'rsi_overbought_{period}'] = (rsi > 70).astype(int)
                features_df[f'rsi_oversold_{period}'] = (rsi < 30).astype(int)
    
    # MACD
    if 'macd' in config['technical_indicators']:
        macd_data = indicators.calculate_macd(df['Close'])
        features_df['macd'] = macd_data['macd']
        features_df['macd_signal'] = macd_data['macd_signal']
        features_df['macd_histogram'] = macd_data['macd_histogram']
        features_df['macd_crossover'] = ((macd_data['macd'] > macd_data['macd_signal']) & 
                                        (macd_data['macd'].shift(1) <= macd_data['macd_signal'].shift(1))).astype(int)
    
    # Bollinger Bands
    if 'bollinger' in config['technical_indicators']:
        bb_data = indicators.calculate_bollinger_bands(df['Close'])
        for key, value in bb_data.items():
            features_df[key] = value
        
        # Additional BB features
        features_df['bb_squeeze'] = (bb_data['bb_width'] < bb_data['bb_width'].rolling(20).mean()).astype(int)
        features_df['bb_breakout_up'] = (df['Close'] > bb_data['bb_upper']).astype(int)
        features_df['bb_breakout_down'] = (df['Close'] < bb_data['bb_lower']).astype(int)
    
    # Stochastic
    if 'stochastic' in config['technical_indicators']:
        stoch_data = indicators.calculate_stochastic(df['High'], df['Low'], df['Close'])
        features_df['stoch_k'] = stoch_data['stoch_k']
        features_df['stoch_d'] = stoch_data['stoch_d']
        features_df['stoch_overbought'] = (stoch_data['stoch_k'] > 80).astype(int)
        features_df['stoch_oversold'] = (stoch_data['stoch_k'] < 20).astype(int)
    
    # ATR
    if 'atr' in config['technical_indicators']:
        atr = indicators.calculate_atr(df['High'], df['Low'], df['Close'])
        features_df['atr'] = atr
        features_df['atr_normalized'] = atr / (df['Close'] + 1e-10)
        features_df['atr_percentile'] = atr.rolling(50).rank(pct=True)
    
    # VWAP
    if 'vwap' in config['technical_indicators']:
        vwap = indicators.calculate_vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        features_df['vwap'] = vwap
        features_df['price_vwap_ratio'] = df['Close'] / (vwap + 1e-10)
    
    # OBV
    if 'obv' in config['technical_indicators']:
        obv = indicators.calculate_obv(df['Close'], df['Volume'])
        features_df['obv'] = obv
        features_df['obv_sma'] = indicators.calculate_sma(obv, 20)
        features_df['obv_ratio'] = obv / (features_df['obv_sma'] + 1e-10)
    
    return features_df

def create_volume_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create volume features for individual stock"""
    
    features_df = df.copy()
    
    # Volume ratios and changes
    for period in [5, 10, 20]:
        if period < len(df):
            vol_sma = df['Volume'].rolling(period).mean()
            features_df[f'volume_sma_{period}'] = vol_sma
            features_df[f'volume_ratio_{period}'] = df['Volume'] / (vol_sma + 1e-10)
            features_df[f'volume_change_{period}'] = df['Volume'].pct_change(period)
    
    # Volume-price relationships
    features_df['volume_price_trend'] = (df['Volume'] * np.where(df['Close'] > df['Close'].shift(1), 1, -1))
    features_df['price_volume_rank'] = df['Close'].rolling(20).rank() * df['Volume'].rolling(20).rank()
    
    # Volume patterns
    features_df['volume_spike'] = (df['Volume'] > df['Volume'].rolling(20).mean() * 2).astype(int)
    features_df['volume_dry_up'] = (df['Volume'] < df['Volume'].rolling(20).mean() * 0.5).astype(int)
    
    return features_df

def create_volatility_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create volatility features for individual stock"""
    
    features_df = df.copy()
    
    # Returns
    returns = df['Close'].pct_change()
    features_df['returns'] = returns
    
    # Rolling volatilities
    for period in [5, 10, 20, 50]:
        if period < len(df):
            vol = returns.rolling(period).std()
            features_df[f'volatility_{period}'] = vol
            features_df[f'volatility_rank_{period}'] = vol.rolling(100).rank(pct=True)
    
    # Volatility patterns
    vol_20 = returns.rolling(20).std()
    vol_50 = returns.rolling(50).std()
    features_df['vol_regime'] = (vol_20 > vol_50).astype(int)
    features_df['vol_expansion'] = (vol_20 > vol_20.shift(5)).astype(int)
    features_df['vol_contraction'] = (vol_20 < vol_20.shift(5)).astype(int)
    
    # Parkinson volatility (high-low estimator)
    parkinson_vol = np.sqrt((np.log(df['High'] / df['Low']) ** 2).rolling(20).mean())
    features_df['parkinson_volatility'] = parkinson_vol
    
    return features_df

def create_momentum_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create momentum features for individual stock"""
    
    features_df = df.copy()
    
    # Rate of Change (ROC)
    for period in [5, 10, 20, 50]:
        if period < len(df):
            roc = (df['Close'] - df['Close'].shift(period)) / (df['Close'].shift(period) + 1e-10)
            features_df[f'roc_{period}'] = roc
            features_df[f'roc_rank_{period}'] = roc.rolling(100).rank(pct=True)
    
    # Momentum oscillators
    for period in [10, 20]:
        if period < len(df):
            momentum = df['Close'] - df['Close'].shift(period)
            features_df[f'momentum_{period}'] = momentum
    
    # Price acceleration
    returns = df['Close'].pct_change()
    features_df['acceleration'] = returns - returns.shift(1)
    features_df['acceleration_sma'] = features_df['acceleration'].rolling(10).mean()
    
    # Momentum divergence
    features_df['price_momentum_div'] = (df['Close'].rolling(20).apply(lambda x: x.iloc[-1] - x.iloc[0]) * 
                                       df['Volume'].rolling(20).apply(lambda x: x.iloc[-1] - x.iloc[0]))
    
    return features_df

def create_trend_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create trend features for individual stock"""
    
    features_df = df.copy()
    
    # Trend direction
    for period in [10, 20, 50]:
        if period < len(df):
            # Linear regression slope approximation
            def calculate_trend_slope(prices):
                if len(prices) < period:
                    return 0
                x = np.arange(len(prices))
                coeffs = np.polyfit(x, prices, 1)
                return coeffs[0]
            
            slope = df['Close'].rolling(period).apply(calculate_trend_slope)
            features_df[f'trend_slope_{period}'] = slope
            features_df[f'trend_strength_{period}'] = abs(slope) / (df['Close'] + 1e-10)
    
    # Moving average trends
    sma_10 = df['Close'].rolling(10).mean()
    sma_20 = df['Close'].rolling(20).mean()
    sma_50 = df['Close'].rolling(50).mean()
    
    features_df['ma_trend_short'] = (sma_10 > sma_20).astype(int)
    features_df['ma_trend_long'] = (sma_20 > sma_50).astype(int)
    features_df['ma_convergence'] = (sma_10 - sma_20) / (sma_20 + 1e-10)
    
    # Trend consistency
    for period in [10, 20]:
        if period < len(df):
            up_days = (df['Close'] > df['Close'].shift(1)).rolling(period).sum()
            features_df[f'trend_consistency_{period}'] = up_days / period
    
    return features_df

def create_pattern_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create pattern recognition features for individual stock"""
    
    features_df = df.copy()
    
    # Candlestick patterns (simplified)
    body_size = abs(df['Close'] - df['Open'])
    total_range = df['High'] - df['Low']
    upper_shadow = df['High'] - np.maximum(df['Open'], df['Close'])
    lower_shadow = np.minimum(df['Open'], df['Close']) - df['Low']
    
    # Doji pattern
    features_df['doji'] = (body_size < total_range * 0.1).astype(int)
    
    # Hammer pattern
    features_df['hammer'] = ((lower_shadow > body_size * 2) & 
                           (upper_shadow < body_size * 0.5) & 
                           (df['Close'] > df['Open'])).astype(int)
    
    # Shooting star pattern
    features_df['shooting_star'] = ((upper_shadow > body_size * 2) & 
                                  (lower_shadow < body_size * 0.5) & 
                                  (df['Close'] < df['Open'])).astype(int)
    
    # Engulfing patterns
    bullish_engulfing = ((df['Close'] > df['Open']) & 
                        (df['Close'].shift(1) < df['Open'].shift(1)) &
                        (df['Open'] < df['Close'].shift(1)) & 
                        (df['Close'] > df['Open'].shift(1)))
    features_df['bullish_engulfing'] = bullish_engulfing.astype(int)
    
    bearish_engulfing = ((df['Close'] < df['Open']) & 
                        (df['Close'].shift(1) > df['Open'].shift(1)) &
                        (df['Open'] > df['Close'].shift(1)) & 
                        (df['Close'] < df['Open'].shift(1)))
    features_df['bearish_engulfing'] = bearish_engulfing.astype(int)
    
    # Support and resistance levels (simplified)
    rolling_max = df['High'].rolling(20).max()
    rolling_min = df['Low'].rolling(20).min()
    
    features_df['near_resistance'] = (df['Close'] > rolling_max * 0.98).astype(int)
    features_df['near_support'] = (df['Close'] < rolling_min * 1.02).astype(int)
    
    return features_df

def create_microstructure_features_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create market microstructure features for individual stock"""
    
    features_df = df.copy()
    
    # Bid-Ask spread proxy (using high-low spread)
    spread_proxy = (df['High'] - df['Low']) / (df['Close'] + 1e-10)
    features_df['spread_proxy'] = spread_proxy
    features_df['spread_ma'] = spread_proxy.rolling(20).mean()
    
    # Liquidity proxies
    features_df['turnover_ratio'] = df['Volume'] / df['Volume'].rolling(50).mean()
    features_df['price_impact'] = abs(df['Close'].pct_change()) / (np.log(df['Volume'] + 1) + 1e-10)
    
    # Intraday patterns
    features_df['intraday_return'] = (df['Close'] - df['Open']) / (df['Open'] + 1e-10)
    features_df['overnight_return'] = (df['Open'] - df['Close'].shift(1)) / (df['Close'].shift(1) + 1e-10)
    
    # Market efficiency measures
    returns = df['Close'].pct_change()
    features_df['return_autocorr'] = returns.rolling(20).apply(lambda x: x.autocorr(lag=1))
    
    # Volume-weighted returns
    features_df['vwap_return'] = (df['Close'] - features_df.get('vwap', df['Close'])) / (df['Close'] + 1e-10)
    
    return features_df

def create_target_variables_individual(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """Create target variables for different investment horizons"""
    
    features_df = df.copy()
    
    for horizon_name, days in TARGET_HORIZONS.items():
        if horizon_name in config.get('target_horizons', []):
            # Future returns
            future_returns = (df['Close'].shift(-days) / df['Close'] - 1)
            
            # Binary classification target (positive returns)
            features_df[f'target_{horizon_name}'] = (future_returns > 0).astype(int)
            
            # Regression target (actual returns)
            features_df[f'target_{horizon_name}_returns'] = future_returns
            
            # Multi-class target (strong sell, sell, hold, buy, strong buy)
            if not future_returns.isna().all():
                q20 = future_returns.quantile(0.2)
                q40 = future_returns.quantile(0.4)
                q60 = future_returns.quantile(0.6)
                q80 = future_returns.quantile(0.8)
                
                conditions = [
                    future_returns <= q20,
                    (future_returns > q20) & (future_returns <= q40),
                    (future_returns > q40) & (future_returns <= q60),
                    (future_returns > q60) & (future_returns <= q80),
                    future_returns > q80
                ]
                choices = [0, 1, 2, 3, 4]  # Strong sell to strong buy
                
                features_df[f'target_{horizon_name}_multiclass'] = np.select(conditions, choices, default=2)
    
    return features_df

def clean_features_individual(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate features for individual stock"""
    
    # Replace infinite values with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Handle NaN values intelligently
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        if df[col].isnull().any():
            if 'ratio' in col.lower() or 'normalized' in col.lower():
                # Ratios: fill with 1
                df[col] = df[col].fillna(1.0)
            elif 'return' in col.lower() or 'change' in col.lower():
                # Returns and changes: fill with 0
                df[col] = df[col].fillna(0.0)
            elif 'ma' in col.lower() or 'sma' in col.lower() or 'ema' in col.lower():
                # Moving averages: forward fill then backward fill
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            elif 'rsi' in col.lower():
                # RSI: fill with 50 (neutral)
                df[col] = df[col].fillna(50.0)
            elif 'volume' in col.lower():
                # Volume: fill with median
                df[col] = df[col].fillna(df[col].median())
            else:
                # Other features: forward fill then backward fill
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
    
    # Final cleanup: any remaining NaN values
    df = df.fillna(0)
    
    return df

# ==================== FEATURE ANALYSIS FUNCTIONS ====================

def get_feature_summary(features: pd.DataFrame) -> Dict:
    """Get summary statistics of features"""
    
    summary = {
        'total_features': features.shape[1],
        'data_points': features.shape[0],
        'missing_values': features.isnull().sum().sum(),
        'infinite_values': np.isinf(features.select_dtypes(include=[np.number])).sum().sum(),
        'feature_types': {
            'price_features': len([col for col in features.columns if 'price' in col.lower()]),
            'volume_features': len([col for col in features.columns if 'volume' in col.lower()]),
            'technical_features': len([col for col in features.columns if any(tech in col.lower() for tech in ['rsi', 'macd', 'sma', 'ema'])]),
            'target_features': len([col for col in features.columns if col.startswith('target_')])
        }
    }
    
    return summary

def analyze_feature_importance_individual(features: pd.DataFrame, target_col: str) -> Dict[str, float]:
    """Analyze feature importance for individual stock"""
    
    if target_col not in features.columns:
        return {}
    
    try:
        from sklearn.feature_selection import mutual_info_classif
        from sklearn.ensemble import RandomForestClassifier
        
        # Separate features and target
        X = features.drop(columns=[col for col in features.columns if col.startswith('target_')])
        y = features[target_col].dropna()
        
        # Align X and y
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]
        
        if len(y.unique()) < 2:
            return {}
        
        # Calculate mutual information
        mutual_info_scores = mutual_info_classif(X.fillna(0), y, random_state=42)
        
        # Calculate feature importance using RandomForest
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X.fillna(0), y)
        rf_importance = rf.feature_importances_
        
        # Combine scores
        combined_importance = {}
        for i, feature in enumerate(X.columns):
            combined_score = (mutual_info_scores[i] + rf_importance[i]) / 2
            combined_importance[feature] = combined_score
        
        # Sort by importance
        sorted_importance = dict(sorted(combined_importance.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_importance
        
    except Exception as e:
        logging.warning(f"Feature importance analysis failed: {e}")
        return {}

def select_best_features_individual(features: pd.DataFrame, target_col: str, 
                                  max_features: int = None) -> List[str]:
    """Select best features for individual stock"""
    
    max_features = max_features or INDIVIDUAL_FEATURE_CONFIG['max_features']
    
    # Get feature importance
    importance_scores = analyze_feature_importance_individual(features, target_col)
    
    if not importance_scores:
        # Fallback: return non-target columns
        return [col for col in features.columns if not col.startswith('target_')][:max_features]
    
    # Select top features
    sorted_features = list(importance_scores.keys())
    selected_features = sorted_features[:max_features]
    
    return selected_features

def validate_features_individual(features: pd.DataFrame) -> Dict:
    """Validate features for individual stock"""
    
    validation_results = {
        'status': 'valid',
        'warnings': [],
        'errors': [],
        'stats': {}
    }
    
    # Check for empty dataframe
    if features.empty:
        validation_results['status'] = 'error'
        validation_results['errors'].append('Features dataframe is empty')
        return validation_results
    
    # Check for minimum data points
    if len(features) < 100:
        validation_results['warnings'].append(f'Low number of data points: {len(features)}')
    
    # Check for missing values
    missing_pct = (features.isnull().sum().sum() / (features.shape[0] * features.shape[1])) * 100
    if missing_pct > 5:
        validation_results['warnings'].append(f'High percentage of missing values: {missing_pct:.2f}%')
    
    # Check for infinite values
    numeric_features = features.select_dtypes(include=[np.number])
    if np.isinf(numeric_features).any().any():
        validation_results['warnings'].append('Infinite values detected')
    
    # Check for constant features
    constant_features = []
    for col in numeric_features.columns:
        if numeric_features[col].nunique() <= 1:
            constant_features.append(col)
    
    if constant_features:
        validation_results['warnings'].append(f'Constant features detected: {len(constant_features)}')
    
    # Statistics
    validation_results['stats'] = {
        'shape': features.shape,
        'missing_percentage': missing_pct,
        'constant_features_count': len(constant_features),
        'numeric_features_count': len(numeric_features.columns)
    }
    
    return validation_results

# ==================== MAIN EXPORTS ====================

__all__ = [
    'engineer_features_individual',
    'get_feature_summary',
    'analyze_feature_importance_individual',
    'select_best_features_individual',
    'validate_features_individual',
    'IndividualFeatureCache',
    'IndividualTechnicalIndicators',
    'TARGET_HORIZONS',
    'INDIVIDUAL_FEATURE_CONFIG'
]