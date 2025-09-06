"""
AI Stock Advisor Pro - API Keys Template
Copy this file to secrets.py and add your actual API keys
"""

# ==================== API KEYS (FREE TIERS AVAILABLE) ====================

# News API (newsapi.org) - 1000 requests/month free
NEWS_API_KEY = "your_news_api_key_here"

# Alpha Vantage (alphavantage.co) - 500 requests/day free
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key_here"

# Finnhub (finnhub.io) - 60 requests/minute free
FINNHUB_API_KEY = "your_finnhub_key_here"

# Reddit API (reddit.com/dev/api) - Free
REDDIT_CLIENT_ID = "your_reddit_client_id"
REDDIT_CLIENT_SECRET = "your_reddit_client_secret"
REDDIT_USER_AGENT = "AI-Stock-Advisor-Pro:v1.0"

# Twitter API (developer.twitter.com) - Free tier available
TWITTER_BEARER_TOKEN = "your_twitter_bearer_token"

# Telegram Bot (optional for notifications)
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"

# ==================== DATABASE CONFIGURATION ====================

# PostgreSQL (optional - for production)
DATABASE_URL = "postgresql://user:password@localhost/stockadvisor"

# MongoDB (optional - for unstructured data)
MONGODB_URI = "mongodb://localhost:27017/stockadvisor"

# ==================== CLOUD STORAGE (OPTIONAL) ====================

# AWS S3
AWS_ACCESS_KEY_ID = "your_aws_access_key"
AWS_SECRET_ACCESS_KEY = "your_aws_secret_key"
AWS_S3_BUCKET = "your-bucket-name"

# Google Cloud Storage
GOOGLE_CLOUD_PROJECT = "your-project-id"
GOOGLE_APPLICATION_CREDENTIALS = "path/to/service-account.json"

# ==================== SMTP CONFIGURATION (OPTIONAL) ====================

# Email notifications
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"

# ==================== SECURITY KEYS ====================

# Secret key for session management
SECRET_KEY = "your_secret_key_here_change_this_in_production"

# Encryption key for sensitive data
ENCRYPTION_KEY = "your_32_byte_encryption_key_here"

# ==================== HOW TO GET API KEYS ====================

"""
1. News API (newsapi.org):
   - Sign up for free account
   - Get 1000 requests/month free
   - No credit card required

2. Alpha Vantage (alphavantage.co):
   - Register for free API key
   - 500 requests/day limit
   - Premium plans available

3. Finnhub (finnhub.io):
   - Create free account
   - 60 requests/minute free
   - Real-time data available

4. Reddit API:
   - Create app at reddit.com/dev/api
   - Get client ID and secret
   - Completely free

5. Twitter API:
   - Apply at developer.twitter.com
   - Free tier: 500k tweets/month
   - Essential access available

All APIs offer generous free tiers perfect for this project!
"""

# ==================== VALIDATION FUNCTIONS ====================

def validate_api_keys():
    """Validate that API keys are configured"""
    keys_to_check = {
        'NEWS_API_KEY': NEWS_API_KEY,
        'ALPHA_VANTAGE_API_KEY': ALPHA_VANTAGE_API_KEY,
        'FINNHUB_API_KEY': FINNHUB_API_KEY
    }

    missing_keys = []
    placeholder_keys = []

    for key_name, key_value in keys_to_check.items():
        if not key_value or key_value == "":
            missing_keys.append(key_name)
        elif "your_" in key_value.lower() or "here" in key_value.lower():
            placeholder_keys.append(key_name)

    return {
        'missing': missing_keys,
        'placeholder': placeholder_keys,
        'valid': len(missing_keys) == 0 and len(placeholder_keys) == 0
    }

if __name__ == "__main__":
    validation = validate_api_keys()
    if not validation['valid']:
        print("⚠️ API Keys not configured properly:")
        if validation['missing']:
            print(f"   Missing: {', '.join(validation['missing'])}")
        if validation['placeholder']:
            print(f"   Placeholder: {', '.join(validation['placeholder'])}")
        print("\n📝 Please update config/secrets.py with your actual API keys")
    else:
        print("✅ All API keys configured")
