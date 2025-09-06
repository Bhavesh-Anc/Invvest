"""
AI Stock Advisor Pro - News Monitoring System
Advanced news monitoring and analysis for market events
"""

import pandas as pd
import numpy as np
import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from config.secrets import NEWS_API_KEY
from config.settings import API_CONFIG
from .sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO)

class NewsMonitor:
    """Advanced news monitoring system"""

    def __init__(self):
        self.api_key = NEWS_API_KEY
        self.sentiment_analyzer = SentimentAnalyzer()
        self.db_path = "data/news.db"
        self.monitoring = False
        self.monitored_symbols = set()
        self._init_database()

    def _init_database(self):
        """Initialize news database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    title TEXT,
                    description TEXT,
                    content TEXT,
                    source TEXT,
                    author TEXT,
                    url TEXT UNIQUE,
                    published_at DATETIME,
                    sentiment_score REAL,
                    impact_score REAL,
                    category TEXT,
                    keywords TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS news_alerts (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    alert_type TEXT,
                    title TEXT,
                    description TEXT,
                    impact_level TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_symbol_date 
                ON news_articles(symbol, published_at);
            """)

    def add_symbol_monitoring(self, symbol: str):
        """Add symbol to monitoring list"""
        self.monitored_symbols.add(symbol)
        logging.info(f"Added {symbol} to news monitoring")

    def remove_symbol_monitoring(self, symbol: str):
        """Remove symbol from monitoring"""
        self.monitored_symbols.discard(symbol)
        logging.info(f"Removed {symbol} from news monitoring")

    def start_monitoring(self, interval_minutes: int = 30):
        """Start continuous news monitoring"""
        self.monitoring = True

        def monitor_loop():
            while self.monitoring:
                try:
                    self._check_news_updates()
                    time.sleep(interval_minutes * 60)
                except Exception as e:
                    logging.error(f"Monitoring error: {e}")
                    time.sleep(300)  # 5 minute error recovery

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

        logging.info(f"Started news monitoring for {len(self.monitored_symbols)} symbols")

    def stop_monitoring(self):
        """Stop news monitoring"""
        self.monitoring = False
        logging.info("Stopped news monitoring")

    def _check_news_updates(self):
        """Check for news updates for monitored symbols"""
        if not self.api_key or not self.monitored_symbols:
            return

        for symbol in self.monitored_symbols:
            try:
                latest_news = self.get_latest_news(symbol, hours=1)

                if latest_news:
                    # Process new articles
                    for article in latest_news:
                        self._process_article(symbol, article)

                    # Check for significant news
                    self._check_for_alerts(symbol, latest_news)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logging.error(f"News update error for {symbol}: {e}")

    def get_latest_news(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get latest news for a symbol"""
        if not self.api_key:
            return self._get_cached_news(symbol, hours)

        try:
            search_term = symbol.replace('.NS', '').replace('.BO', '')

            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'"{search_term}" AND (stock OR shares OR trading OR market)',
                'apiKey': self.api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': (datetime.now() - timedelta(hours=hours)).isoformat(),
                'pageSize': 50
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])

                # Filter and enrich articles
                processed_articles = []
                for article in articles:
                    processed_article = self._enrich_article(symbol, article)
                    if processed_article:
                        processed_articles.append(processed_article)

                return processed_articles

        except Exception as e:
            logging.error(f"News API error for {symbol}: {e}")

        return self._get_cached_news(symbol, hours)

    def _enrich_article(self, symbol: str, article: Dict) -> Dict:
        """Enrich article with additional analysis"""
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            content = f"{title} {description}"

            if not content or len(content) < 20:
                return None

            # Analyze sentiment
            sentiment_score, sentiment_label = self.sentiment_analyzer.analyze_text_sentiment(content)

            # Calculate impact score
            impact_score = self._calculate_impact_score(content, article)

            # Categorize news
            category = self._categorize_news(content)

            # Extract keywords
            keywords = self._extract_keywords(content)

            enriched_article = {
                'symbol': symbol,
                'title': title,
                'description': description,
                'source': article.get('source', {}).get('name', ''),
                'author': article.get('author', ''),
                'url': article.get('url', ''),
                'published_at': article.get('publishedAt', ''),
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'impact_score': impact_score,
                'category': category,
                'keywords': json.dumps(keywords)
            }

            return enriched_article

        except Exception as e:
            logging.error(f"Article enrichment error: {e}")
            return None

    def _calculate_impact_score(self, content: str, article: Dict) -> float:
        """Calculate potential market impact score"""
        impact_score = 0.0

        # Source credibility weight
        source = article.get('source', {}).get('name', '').lower()
        credible_sources = ['reuters', 'bloomberg', 'cnbc', 'financial times', 'wall street journal']
        if any(cs in source for cs in credible_sources):
            impact_score += 0.3

        # High impact keywords
        high_impact_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'merger', 'acquisition',
            'lawsuit', 'regulation', 'ban', 'approval', 'partnership',
            'ipo', 'split', 'dividend', 'buyback', 'ceo', 'management'
        ]

        content_lower = content.lower()
        for keyword in high_impact_keywords:
            if keyword in content_lower:
                impact_score += 0.1

        # Urgency indicators
        urgency_words = ['breaking', 'urgent', 'alert', 'immediate', 'now']
        for word in urgency_words:
            if word in content_lower:
                impact_score += 0.2

        # Market timing (market hours increase impact)
        published_time = datetime.fromisoformat(
            article.get('publishedAt', '').replace('Z', '+00:00')
        )

        if self._is_market_hours(published_time):
            impact_score += 0.2

        return min(1.0, impact_score)

    def _categorize_news(self, content: str) -> str:
        """Categorize news article"""
        content_lower = content.lower()

        categories = {
            'earnings': ['earnings', 'quarterly results', 'profit', 'revenue', 'eps'],
            'corporate': ['merger', 'acquisition', 'partnership', 'management', 'ceo'],
            'regulatory': ['regulation', 'policy', 'government', 'law', 'compliance'],
            'market': ['market', 'trading', 'price', 'volume', 'index'],
            'analyst': ['analyst', 'rating', 'target price', 'upgrade', 'downgrade'],
            'product': ['product', 'service', 'launch', 'innovation', 'technology']
        }

        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category

        return 'general'

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        # Simple keyword extraction (in production, use NLP libraries)
        financial_terms = [
            'earnings', 'revenue', 'profit', 'growth', 'market share',
            'competition', 'innovation', 'expansion', 'merger', 'acquisition'
        ]

        content_lower = content.lower()
        found_keywords = []

        for term in financial_terms:
            if term in content_lower:
                found_keywords.append(term)

        return found_keywords[:10]  # Limit to top 10

    def _process_article(self, symbol: str, article: Dict):
        """Process and store article"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO news_articles
                    (symbol, title, description, source, author, url, published_at,
                     sentiment_score, impact_score, category, keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article['symbol'],
                    article['title'],
                    article['description'],
                    article['source'],
                    article['author'],
                    article['url'],
                    article['published_at'],
                    article['sentiment_score'],
                    article['impact_score'],
                    article['category'],
                    article['keywords']
                ))

        except Exception as e:
            logging.error(f"Article storage error: {e}")

    def _check_for_alerts(self, symbol: str, articles: List[Dict]):
        """Check for high-impact news that require alerts"""
        for article in articles:
            # High impact + extreme sentiment = alert
            if (article['impact_score'] > 0.7 and 
                abs(article['sentiment_score']) > 0.5):

                self._create_alert(symbol, article)

    def _create_alert(self, symbol: str, article: Dict):
        """Create news alert"""
        try:
            impact_level = 'HIGH' if article['impact_score'] > 0.8 else 'MEDIUM'
            alert_type = f"NEWS_{article['category'].upper()}"

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO news_alerts
                    (symbol, alert_type, title, description, impact_level)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    symbol,
                    alert_type,
                    article['title'],
                    article['description'],
                    impact_level
                ))

            logging.info(f"Created {impact_level} alert for {symbol}: {article['title'][:50]}...")

        except Exception as e:
            logging.error(f"Alert creation error: {e}")

    def get_news_alerts(self, symbol: str = None, hours: int = 24) -> List[Dict]:
        """Get recent news alerts"""
        try:
            query = """
                SELECT * FROM news_alerts 
                WHERE created_at >= datetime('now', '-{} hours')
            """.format(hours)

            params = []
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            query += " ORDER BY created_at DESC"

            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql(query, conn, params=params)
                return df.to_dict('records')

        except Exception as e:
            logging.error(f"Alert retrieval error: {e}")
            return []

    def get_news_summary(self, symbol: str, days: int = 7) -> Dict:
        """Get news summary for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("""
                    SELECT * FROM news_articles
                    WHERE symbol = ? AND published_at >= date('now', '-{} days')
                    ORDER BY published_at DESC
                """.format(days), conn, params=(symbol,))

                if df.empty:
                    return {'symbol': symbol, 'article_count': 0}

                # Calculate metrics
                avg_sentiment = df['sentiment_score'].mean()
                avg_impact = df['impact_score'].mean()

                # Category distribution
                categories = df['category'].value_counts().to_dict()

                # Recent high-impact articles
                high_impact = df[df['impact_score'] > 0.6].head(5)

                return {
                    'symbol': symbol,
                    'article_count': len(df),
                    'average_sentiment': float(avg_sentiment),
                    'average_impact': float(avg_impact),
                    'sentiment_label': self.sentiment_analyzer._score_to_label(avg_sentiment),
                    'categories': categories,
                    'high_impact_articles': high_impact[['title', 'published_at', 'impact_score']].to_dict('records'),
                    'period_days': days
                }

        except Exception as e:
            logging.error(f"News summary error: {e}")
            return {'symbol': symbol, 'error': str(e)}

    def _get_cached_news(self, symbol: str, hours: int) -> List[Dict]:
        """Get cached news articles"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("""
                    SELECT * FROM news_articles
                    WHERE symbol = ? AND created_at >= datetime('now', '-{} hours')
                    ORDER BY published_at DESC
                """.format(hours), conn, params=(symbol,))

                return df.to_dict('records')

        except Exception as e:
            logging.error(f"Cache retrieval error: {e}")
            return []

    def _is_market_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during market hours"""
        # Convert to IST
        ist_time = timestamp.astimezone()

        # Check if weekday and between 9:15 AM - 3:30 PM
        if ist_time.weekday() < 5:  # Monday-Friday
            market_start = ist_time.replace(hour=9, minute=15)
            market_end = ist_time.replace(hour=15, minute=30)
            return market_start <= ist_time <= market_end

        return False

    def get_trending_news(self, limit: int = 20) -> List[Dict]:
        """Get trending news across all monitored symbols"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("""
                    SELECT * FROM news_articles
                    WHERE published_at >= date('now', '-1 day')
                    ORDER BY impact_score DESC, published_at DESC
                    LIMIT ?
                """, conn, params=(limit,))

                return df.to_dict('records')

        except Exception as e:
            logging.error(f"Trending news error: {e}")
            return []

# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    monitor = NewsMonitor()

    # Add symbols to monitor
    symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
    for symbol in symbols:
        monitor.add_symbol_monitoring(symbol)

    # Get latest news
    news = monitor.get_latest_news("RELIANCE.NS", hours=24)
    print(f"Found {len(news)} news articles for RELIANCE")

    # Get news summary
    summary = monitor.get_news_summary("RELIANCE.NS")
    print(f"News summary: {summary.get('article_count', 0)} articles, sentiment: {summary.get('sentiment_label', 'N/A')}")

    # Start monitoring (uncomment to run)
    # monitor.start_monitoring(interval_minutes=30)
