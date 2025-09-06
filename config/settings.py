"""
AI Stock Advisor Pro - Enhanced Configuration Settings
Centralized configuration management for the entire system
"""

import os
from pathlib import Path
from datetime import datetime

# ==================== BASE CONFIGURATION ====================

BASE_CONFIG = {
    'project_name': 'AI Stock Advisor Pro',
    'version': '2.0.0',
    'debug': False,
    'timezone': 'Asia/Kolkata',
    'base_currency': 'INR',
    'market': 'NSE'
}

# ==================== DATA CONFIGURATION ====================

DATA_CONFIG = {
    # Data Sources
    'primary_source': 'yfinance',
    'backup_sources': ['alpha_vantage', 'finnhub'],
    'default_period': '15y',
    'max_period': '20y',
    'default_interval': '1d',

    # Data Quality
    'min_data_points': 200,
    'data_quality_threshold': 0.7,
    'outlier_threshold': 3.0,
    'missing_data_limit': 0.1,

    # Caching
    'cache_enabled': True,
    'cache_duration_hours': 12,
    'database_enabled': True,
    'database_path': 'data/stock_data.db',

    # Performance
    'max_workers': 6,
    'batch_size': 8,
    'request_delay': 0.5,
    'timeout': 45,
    'retry_attempts': 3
}

# ==================== MODEL CONFIGURATION ====================

MODEL_CONFIG = {
    # Model Types
    'available_models': [
        'xgboost', 'lightgbm', 'catboost', 
        'random_forest', 'neural_network', 'svm'
    ],
    'default_models': ['xgboost', 'lightgbm', 'random_forest'],

    # Training Parameters
    'test_size': 0.2,
    'validation_size': 0.1,
    'cv_folds': 5,
    'random_state': 42,

    # Feature Engineering
    'max_features': 200,
    'feature_selection_enabled': True,
    'feature_importance_threshold': 0.001,

    # Hyperparameter Optimization
    'hyperparameter_tuning': True,
    'optuna_trials': 50,
    'early_stopping': True,
    'early_stopping_rounds': 20,

    # Ensemble Methods
    'ensemble_enabled': True,
    'ensemble_methods': ['voting', 'stacking'],
    'model_calibration': True,

    # Performance Monitoring
    'model_monitoring': True,
    'drift_detection': True,
    'performance_threshold': 0.6,
    'retrain_threshold': 0.05
}

# ==================== FEATURE CONFIGURATION ====================

FEATURE_CONFIG = {
    # Feature Categories
    'price_features': True,
    'volume_features': True,
    'technical_indicators': True,
    'volatility_features': True,
    'momentum_features': True,
    'trend_features': True,
    'pattern_features': True,
    'sentiment_features': True,
    'macro_features': True,

    # Technical Indicators
    'indicators': [
        'sma', 'ema', 'rsi', 'macd', 'bollinger',
        'stochastic', 'atr', 'adx', 'cci', 'obv'
    ],
    'lookback_periods': [5, 10, 20, 50, 100, 200],

    # Advanced Features
    'pattern_recognition': True,
    'market_microstructure': True,
    'correlation_features': True,
    'regime_detection': True,

    # Caching
    'feature_caching': True,
    'cache_expiry_hours': 24
}

# ==================== UI CONFIGURATION ====================

UI_CONFIG = {
    # Streamlit Settings
    'page_title': 'AI Stock Advisor Pro',
    'page_icon': '🚀',
    'layout': 'wide',
    'sidebar_state': 'expanded',

    # Theme
    'primary_color': '#1E88E5',
    'background_color': '#FFFFFF', 
    'secondary_background_color': '#F5F5F5',
    'text_color': '#262730',

    # Dashboard
    'refresh_interval': 300,  # 5 minutes
    'max_display_rows': 100,
    'chart_height': 400,
    'default_chart_type': 'plotly',

    # Performance
    'cache_ttl': 1800,  # 30 minutes
    'max_cache_entries': 10
}

# ==================== TRADING CONFIGURATION ====================

TRADING_CONFIG = {
    # Risk Management
    'max_portfolio_risk': 0.02,  # 2% max daily risk
    'max_single_position': 0.15,  # 15% max single position
    'stop_loss_threshold': 0.05,  # 5% stop loss
    'take_profit_threshold': 0.1,  # 10% take profit

    # Portfolio Construction
    'min_stocks': 5,
    'max_stocks': 25,
    'rebalance_frequency': 'monthly',
    'diversification_constraints': True,

    # Investment Horizons
    'available_horizons': {
        'short_term': 30,    # days
        'medium_term': 90,   # days  
        'long_term': 365     # days
    },
    'default_horizon': 'medium_term',

    # Execution
    'paper_trading': True,
    'commission_rate': 0.001,  # 0.1%
    'slippage_rate': 0.0005    # 0.05%
}

# ==================== API CONFIGURATION ====================

API_CONFIG = {
    # Rate Limits
    'yfinance_delay': 0.1,
    'alpha_vantage_calls_per_minute': 5,
    'finnhub_calls_per_minute': 30,
    'news_api_calls_per_day': 1000,

    # Timeouts
    'default_timeout': 30,
    'data_timeout': 60,
    'news_timeout': 15,

    # Retry Logic
    'max_retries': 3,
    'retry_delay': 2,
    'backoff_factor': 2
}

# ==================== LOGGING CONFIGURATION ====================

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

# ==================== ENVIRONMENT CONFIGURATION ====================

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development')

    if env == 'production':
        DATA_CONFIG['cache_duration_hours'] = 6
        MODEL_CONFIG['hyperparameter_tuning'] = False
        UI_CONFIG['cache_ttl'] = 3600
        BASE_CONFIG['debug'] = False
    elif env == 'testing':
        DATA_CONFIG['default_period'] = '2y'
        MODEL_CONFIG['optuna_trials'] = 10
        BASE_CONFIG['debug'] = True
    # development is default

    return {
        'base': BASE_CONFIG,
        'data': DATA_CONFIG,
        'model': MODEL_CONFIG,
        'features': FEATURE_CONFIG,
        'ui': UI_CONFIG,
        'trading': TRADING_CONFIG,
        'api': API_CONFIG,
        'logging': LOGGING_CONFIG
    }

# Export main configuration
CONFIG = get_config()

# ==================== UTILITY FUNCTIONS ====================

def update_config(section: str, key: str, value):
    """Update configuration dynamically"""
    if section in CONFIG and key in CONFIG[section]:
        CONFIG[section][key] = value
        return True
    return False

def get_config_value(section: str, key: str, default=None):
    """Get configuration value with default fallback"""
    return CONFIG.get(section, {}).get(key, default)

def validate_config():
    """Validate configuration settings"""
    errors = []

    # Validate paths exist
    required_dirs = ['data', 'logs', 'models', 'cache']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            Path(dir_name).mkdir(parents=True, exist_ok=True)

    # Validate numeric ranges
    if not 0 < CONFIG['data']['data_quality_threshold'] <= 1:
        errors.append("data_quality_threshold must be between 0 and 1")

    if not 0 < CONFIG['trading']['max_portfolio_risk'] <= 1:
        errors.append("max_portfolio_risk must be between 0 and 1")

    return errors

if __name__ == "__main__":
    # Validate configuration on import
    validation_errors = validate_config()
    if validation_errors:
        print("Configuration validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration validated successfully")
