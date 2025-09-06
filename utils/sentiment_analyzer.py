"""
AI Stock Advisor Pro - Sentiment Analysis Engine
Advanced sentiment analysis from multiple sources
"""

import pandas as pd
import numpy as np
import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import re
from textblob import TextBlob
import json
from collections import Counter
from config.secrets import NEWS_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TWITTER_BEARER_TOKEN
from config.settings import API_CONFIG

logging.basicConfig(level=logging.INFO)

class SentimentAnalyzer:
    """Advanced sentiment analysis engine"""

    def __init__(self):
        self.news_api_key = NEWS_API_KEY
        self.reddit_client_id = REDDIT_CLIENT_ID  
        self.reddit_client_secret = REDDIT_CLIENT_SECRET
        self.twitter_bearer_token = TWITTER_BEARER_TOKEN
        self.db_path = "data/sentiment_data.db"
        self._init_database()
        self._init_keywords()

    def _init_database(self):
        """Initialize sentiment database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news_sentiment (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    title TEXT,
                    description TEXT,
                    source TEXT,
                    published_at DATETIME,
                    sentiment_score REAL,
                    sentiment_label TEXT,
                    url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS social_sentiment (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    platform TEXT,
                    content TEXT,
                    author TEXT,
                    created_at DATETIME,
                    sentiment_score REAL,
                    sentiment_label TEXT,
                    engagement_score INTEGER,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_summary (
                    symbol TEXT,
                    date DATE,
                    news_sentiment REAL,
                    social_sentiment REAL,
                    overall_sentiment REAL,
                    news_count INTEGER,
                    social_count INTEGER,
                    confidence_score REAL,
                    PRIMARY KEY (symbol, date)
                )
            """)

    def _init_keywords(self):
        """Initialize sentiment keywords"""
        self.positive_keywords = {
            'financial': ['profit', 'growth', 'revenue', 'earnings', 'beat', 'strong', 'outperform', 'upgrade', 'bullish', 'buy'],
            'general': ['good', 'great', 'excellent', 'positive', 'success', 'win', 'gain', 'rise', 'surge', 'boom'],
            'market': ['rally', 'bull market', 'momentum', 'breakout', 'support', 'resistance break']
        }

        self.negative_keywords = {
            'financial': ['loss', 'decline', 'miss', 'weak', 'underperform', 'downgrade', 'bearish', 'sell', 'debt'],
            'general': ['bad', 'terrible', 'negative', 'failure', 'lose', 'fall', 'drop', 'crash', 'collapse'],
            'market': ['correction', 'bear market', 'selloff', 'breakdown', 'resistance', 'support break']
        }

        # Create word weights
        self.word_weights = {}
        for category, words in self.positive_keywords.items():
            for word in words:
                self.word_weights[word] = 1.0 if category == 'general' else 1.5

        for category, words in self.negative_keywords.items():
            for word in words:
                self.word_weights[word] = -1.0 if category == 'general' else -1.5

    def analyze_text_sentiment(self, text: str) -> Tuple[float, str]:
        """Analyze sentiment of a text using multiple methods"""
        if not text:
            return 0.0, 'neutral'

        # Clean text
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())

        # Method 1: TextBlob (simple but effective)
        blob = TextBlob(text)
        textblob_score = blob.sentiment.polarity

        # Method 2: Keyword-based analysis
        keyword_score = self._analyze_keywords(text)

        # Method 3: Financial context analysis
        financial_score = self._analyze_financial_context(text)

        # Combine scores with weights
        combined_score = (
            textblob_score * 0.4 + 
            keyword_score * 0.4 + 
            financial_score * 0.2
        )

        # Normalize to [-1, 1] range
        final_score = max(-1.0, min(1.0, combined_score))

        # Determine label
        if final_score > 0.1:
            label = 'positive'
        elif final_score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'

        return final_score, label

    def _analyze_keywords(self, text: str) -> float:
        """Analyze text using keyword matching"""
        words = text.lower().split()
        score = 0.0

        for word in words:
            if word in self.word_weights:
                score += self.word_weights[word]

        # Normalize by text length
        if len(words) > 0:
            score = score / len(words) * 10  # Scale up

        return max(-1.0, min(1.0, score))

    def _analyze_financial_context(self, text: str) -> float:
        """Analyze financial context and terminology"""
        financial_patterns = {
            'positive': [
                r'beat expectations?', r'strong earnings', r'revenue growth',
                r'profit margin', r'outperform', r'upgrade', r'buy rating'
            ],
            'negative': [
                r'miss expectations?', r'weak earnings', r'revenue decline',
                r'loss', r'underperform', r'downgrade', r'sell rating'
            ]
        }

        score = 0.0

        for sentiment, patterns in financial_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                if sentiment == 'positive':
                    score += matches * 0.3
                else:
                    score -= matches * 0.3

        return max(-1.0, min(1.0, score))

    def get_news_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get news sentiment for a symbol"""
        if not self.news_api_key:
            logging.warning("News API key not configured")
            return self._get_cached_news_sentiment(symbol, days)

        try:
            # Fetch news articles
            articles = self._fetch_news_articles(symbol, days)

            if not articles:
                return self._get_cached_news_sentiment(symbol, days)

            sentiments = []
            processed_articles = []

            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                content = f"{title} {description}"

                sentiment_score, sentiment_label = self.analyze_text_sentiment(content)

                article_data = {
                    'symbol': symbol,
                    'title': title,
                    'description': description,
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': article.get('publishedAt', ''),
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label,
                    'url': article.get('url', '')
                }

                sentiments.append(sentiment_score)
                processed_articles.append(article_data)

                # Cache article
                self._cache_news_article(article_data)

            # Calculate overall sentiment
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                sentiment_std = np.std(sentiments)
                confidence = max(0, 1 - sentiment_std)  # Higher std = lower confidence

                return {
                    'symbol': symbol,
                    'average_sentiment': avg_sentiment,
                    'sentiment_label': self._score_to_label(avg_sentiment),
                    'confidence': confidence,
                    'article_count': len(sentiments),
                    'articles': processed_articles[:5],  # Return top 5
                    'sentiment_distribution': {
                        'positive': sum(1 for s in sentiments if s > 0.1),
                        'neutral': sum(1 for s in sentiments if -0.1 <= s <= 0.1),
                        'negative': sum(1 for s in sentiments if s < -0.1)
                    }
                }

        except Exception as e:
            logging.error(f"News sentiment error for {symbol}: {e}")

        return self._get_cached_news_sentiment(symbol, days)

    def _fetch_news_articles(self, symbol: str, days: int) -> List[Dict]:
        """Fetch news articles from News API"""
        try:
            # Convert symbol format (RELIANCE.NS -> RELIANCE)
            search_symbol = symbol.replace('.NS', '').replace('.BO', '')

            # Search queries
            queries = [
                search_symbol,
                f"{search_symbol} stock",
                f"{search_symbol} earnings",
                f"{search_symbol} India"
            ]

            all_articles = []

            for query in queries:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': query,
                    'apiKey': self.news_api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    'pageSize': 20
                }

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    all_articles.extend(articles)

                time.sleep(0.1)  # Rate limiting

            # Remove duplicates and filter relevance
            unique_articles = []
            seen_titles = set()

            for article in all_articles:
                title = article.get('title', '')
                if title not in seen_titles and len(title) > 10:
                    # Check if article is relevant to the symbol
                    content = f"{title} {article.get('description', '')}"
                    if search_symbol.lower() in content.lower():
                        unique_articles.append(article)
                        seen_titles.add(title)

            return unique_articles[:50]  # Limit to 50 most recent

        except Exception as e:
            logging.error(f"News API error: {e}")
            return []

    def get_social_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get social media sentiment (Reddit, Twitter)"""
        try:
            # For now, return cached or simulated data
            # In production, this would fetch from Reddit/Twitter APIs

            return self._get_cached_social_sentiment(symbol, days)

        except Exception as e:
            logging.error(f"Social sentiment error: {e}")
            return {}

    def get_overall_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get overall sentiment combining news and social"""
        news_sentiment = self.get_news_sentiment(symbol, days)
        social_sentiment = self.get_social_sentiment(symbol, days)

        # Combine sentiments with weights
        news_score = news_sentiment.get('average_sentiment', 0) * 0.7
        social_score = social_sentiment.get('average_sentiment', 0) * 0.3

        overall_score = news_score + social_score

        # Calculate confidence
        news_conf = news_sentiment.get('confidence', 0)
        social_conf = social_sentiment.get('confidence', 0)
        overall_conf = (news_conf * 0.7 + social_conf * 0.3)

        result = {
            'symbol': symbol,
            'overall_sentiment': overall_score,
            'sentiment_label': self._score_to_label(overall_score),
            'confidence': overall_conf,
            'components': {
                'news': news_sentiment,
                'social': social_sentiment
            },
            'recommendation': self._generate_recommendation(overall_score, overall_conf),
            'last_updated': datetime.now().isoformat()
        }

        # Cache overall sentiment
        self._cache_sentiment_summary(result)

        return result

    def _score_to_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.2:
            return 'positive'
        elif score < -0.2:
            return 'negative'
        else:
            return 'neutral'

    def _generate_recommendation(self, sentiment: float, confidence: float) -> str:
        """Generate investment recommendation based on sentiment"""
        if confidence < 0.3:
            return "Insufficient data for recommendation"

        if sentiment > 0.3 and confidence > 0.7:
            return "Strong positive sentiment - Consider buying"
        elif sentiment > 0.1 and confidence > 0.5:
            return "Positive sentiment - Monitor for entry"
        elif sentiment < -0.3 and confidence > 0.7:
            return "Strong negative sentiment - Consider selling"
        elif sentiment < -0.1 and confidence > 0.5:
            return "Negative sentiment - Exercise caution"
        else:
            return "Neutral sentiment - Hold or wait"

    def _cache_news_article(self, article_data: Dict):
        """Cache news article in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO news_sentiment
                    (symbol, title, description, source, published_at, 
                     sentiment_score, sentiment_label, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_data['symbol'],
                    article_data['title'],
                    article_data['description'], 
                    article_data['source'],
                    article_data['published_at'],
                    article_data['sentiment_score'],
                    article_data['sentiment_label'],
                    article_data['url']
                ))
        except Exception as e:
            logging.warning(f"Cache error: {e}")

    def _cache_sentiment_summary(self, sentiment_data: Dict):
        """Cache sentiment summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sentiment_summary
                    (symbol, date, news_sentiment, social_sentiment, overall_sentiment,
                     news_count, social_count, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sentiment_data['symbol'],
                    datetime.now().date(),
                    sentiment_data['components']['news'].get('average_sentiment', 0),
                    sentiment_data['components']['social'].get('average_sentiment', 0),
                    sentiment_data['overall_sentiment'],
                    sentiment_data['components']['news'].get('article_count', 0),
                    sentiment_data['components']['social'].get('post_count', 0),
                    sentiment_data['confidence']
                ))
        except Exception as e:
            logging.warning(f"Summary cache error: {e}")

    def _get_cached_news_sentiment(self, symbol: str, days: int) -> Dict:
        """Get cached news sentiment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("""
                    SELECT * FROM news_sentiment 
                    WHERE symbol = ? AND created_at >= date('now', '-{} days')
                    ORDER BY published_at DESC
                """.format(days), conn, params=(symbol,))

                if not df.empty:
                    avg_sentiment = df['sentiment_score'].mean()
                    confidence = 1.0 - df['sentiment_score'].std()

                    return {
                        'symbol': symbol,
                        'average_sentiment': avg_sentiment,
                        'sentiment_label': self._score_to_label(avg_sentiment),
                        'confidence': max(0, confidence),
                        'article_count': len(df),
                        'cached': True
                    }
        except Exception as e:
            logging.error(f"Cache retrieval error: {e}")

        return {
            'symbol': symbol,
            'average_sentiment': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0,
            'article_count': 0,
            'cached': True
        }

    def _get_cached_social_sentiment(self, symbol: str, days: int) -> Dict:
        """Get cached social sentiment"""
        return {
            'symbol': symbol,
            'average_sentiment': 0.0,
            'sentiment_label': 'neutral', 
            'confidence': 0.0,
            'post_count': 0,
            'cached': True
        }

    def batch_sentiment_analysis(self, symbols: List[str], days: int = 7) -> Dict[str, Dict]:
        """Analyze sentiment for multiple symbols"""
        results = {}

        for symbol in symbols:
            try:
                sentiment = self.get_overall_sentiment(symbol, days)
                results[symbol] = sentiment

                # Rate limiting
                time.sleep(0.2)

            except Exception as e:
                logging.error(f"Batch analysis error for {symbol}: {e}")
                results[symbol] = {
                    'symbol': symbol,
                    'overall_sentiment': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0,
                    'error': str(e)
                }

        return results

# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    # Test single symbol
    sentiment = analyzer.get_overall_sentiment("RELIANCE.NS")
    print(f"Sentiment for RELIANCE: {sentiment['sentiment_label']} ({sentiment['overall_sentiment']:.3f})")

    # Test batch analysis
    symbols = ["TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    batch_results = analyzer.batch_sentiment_analysis(symbols)

    for symbol, result in batch_results.items():
        print(f"{symbol}: {result['sentiment_label']} (confidence: {result['confidence']:.2f})")
