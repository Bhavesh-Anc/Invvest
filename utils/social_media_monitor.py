"""
AI Stock Advisor Pro - Social Media Monitoring System
Monitor social media sentiment and discussions about stocks
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
import re
from config.secrets import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TWITTER_BEARER_TOKEN
from .sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO)

class SocialMediaMonitor:
    """Social media monitoring for stock sentiment"""

    def __init__(self):
        self.reddit_client_id = REDDIT_CLIENT_ID
        self.reddit_client_secret = REDDIT_CLIENT_SECRET
        self.twitter_bearer_token = TWITTER_BEARER_TOKEN
        self.sentiment_analyzer = SentimentAnalyzer()
        self.db_path = "data/social_media.db"
        self._init_database()
        self._reddit_token = None

    def _init_database(self):
        """Initialize social media database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS social_posts (
                    id INTEGER PRIMARY KEY,
                    platform TEXT,
                    post_id TEXT UNIQUE,
                    symbol TEXT,
                    content TEXT,
                    author TEXT,
                    created_at DATETIME,
                    score INTEGER,
                    comments_count INTEGER,
                    sentiment_score REAL,
                    engagement_score REAL,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS social_trends (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    platform TEXT,
                    date DATE,
                    mention_count INTEGER,
                    avg_sentiment REAL,
                    total_engagement INTEGER,
                    trending_keywords TEXT,
                    PRIMARY KEY (symbol, platform, date)
                )
            """)

    def _get_reddit_token(self) -> str:
        """Get Reddit API access token"""
        if not self.reddit_client_id or not self.reddit_client_secret:
            return None

        try:
            auth = (self.reddit_client_id, self.reddit_client_secret)
            data = {
                'grant_type': 'client_credentials'
            }
            headers = {'User-Agent': 'AI-Stock-Advisor-Pro:v1.0'}

            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')

        except Exception as e:
            logging.error(f"Reddit token error: {e}")

        return None

    def monitor_reddit(self, symbol: str, subreddits: List[str] = None) -> List[Dict]:
        """Monitor Reddit for stock discussions"""
        if subreddits is None:
            subreddits = ['stocks', 'investing', 'SecurityAnalysis', 'IndiaInvestments']

        if not self._reddit_token:
            self._reddit_token = self._get_reddit_token()

        if not self._reddit_token:
            return self._get_cached_reddit_posts(symbol)

        all_posts = []
        search_term = symbol.replace('.NS', '').replace('.BO', '')

        try:
            headers = {
                'Authorization': f'Bearer {self._reddit_token}',
                'User-Agent': 'AI-Stock-Advisor-Pro:v1.0'
            }

            for subreddit in subreddits:
                url = f"https://oauth.reddit.com/r/{subreddit}/search"
                params = {
                    'q': search_term,
                    'sort': 'new',
                    'limit': 25,
                    'restrict_sr': True,
                    't': 'week'
                }

                response = requests.get(url, headers=headers, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])

                    for post_data in posts:
                        post = post_data.get('data', {})
                        processed_post = self._process_reddit_post(symbol, post, subreddit)
                        if processed_post:
                            all_posts.append(processed_post)
                            self._cache_social_post(processed_post)

                time.sleep(1)  # Rate limiting

        except Exception as e:
            logging.error(f"Reddit monitoring error: {e}")
            return self._get_cached_reddit_posts(symbol)

        return all_posts

    def _process_reddit_post(self, symbol: str, post: Dict, subreddit: str) -> Dict:
        """Process Reddit post"""
        try:
            title = post.get('title', '')
            selftext = post.get('selftext', '')
            content = f"{title} {selftext}"

            if len(content) < 10:
                return None

            # Analyze sentiment
            sentiment_score, sentiment_label = self.sentiment_analyzer.analyze_text_sentiment(content)

            # Calculate engagement score
            score = post.get('score', 0)
            num_comments = post.get('num_comments', 0)
            engagement_score = np.log1p(score + num_comments * 2)

            processed_post = {
                'platform': 'reddit',
                'post_id': post.get('id'),
                'symbol': symbol,
                'content': content[:1000],  # Limit content length
                'author': post.get('author', ''),
                'created_at': datetime.fromtimestamp(post.get('created_utc', 0)),
                'score': score,
                'comments_count': num_comments,
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'engagement_score': engagement_score,
                'subreddit': subreddit
            }

            return processed_post

        except Exception as e:
            logging.error(f"Reddit post processing error: {e}")
            return None

    def monitor_twitter(self, symbol: str) -> List[Dict]:
        """Monitor Twitter for stock discussions"""
        if not self.twitter_bearer_token:
            return self._get_cached_twitter_posts(symbol)

        # Note: Twitter API v2 requires different implementation
        # This is a placeholder for the structure
        return []

    def get_social_sentiment(self, symbol: str, days: int = 7, platforms: List[str] = None) -> Dict:
        """Get social media sentiment for a symbol"""
        if platforms is None:
            platforms = ['reddit', 'twitter']

        try:
            all_posts = []

            # Collect posts from different platforms
            if 'reddit' in platforms:
                reddit_posts = self.monitor_reddit(symbol)
                all_posts.extend(reddit_posts)

            if 'twitter' in platforms:
                twitter_posts = self.monitor_twitter(symbol)
                all_posts.extend(twitter_posts)

            # If no new posts, get from cache
            if not all_posts:
                all_posts = self._get_cached_social_posts(symbol, days)

            if not all_posts:
                return {
                    'symbol': symbol,
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'post_count': 0,
                    'platforms': platforms
                }

            # Calculate metrics
            sentiment_scores = [post['sentiment_score'] for post in all_posts]
            engagement_scores = [post['engagement_score'] for post in all_posts]

            avg_sentiment = np.mean(sentiment_scores)
            total_engagement = sum(engagement_scores)

            # Weight sentiment by engagement
            weighted_sentiment = np.average(
                sentiment_scores, 
                weights=engagement_scores
            ) if engagement_scores else avg_sentiment

            # Calculate confidence based on post count and engagement
            confidence = min(1.0, len(all_posts) / 20 + total_engagement / 100)

            # Get trending keywords
            trending_keywords = self._extract_trending_keywords(all_posts)

            result = {
                'symbol': symbol,
                'sentiment_score': float(weighted_sentiment),
                'sentiment_label': self._score_to_label(weighted_sentiment),
                'confidence': float(confidence),
                'post_count': len(all_posts),
                'total_engagement': float(total_engagement),
                'trending_keywords': trending_keywords,
                'platforms': platforms,
                'platform_breakdown': self._get_platform_breakdown(all_posts),
                'last_updated': datetime.now().isoformat()
            }

            # Cache the summary
            self._cache_social_trend(result, days)

            return result

        except Exception as e:
            logging.error(f"Social sentiment error for {symbol}: {e}")
            return {
                'symbol': symbol,
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'post_count': 0,
                'error': str(e)
            }

    def _extract_trending_keywords(self, posts: List[Dict]) -> List[str]:
        """Extract trending keywords from posts"""
        all_content = ' '.join([post['content'] for post in posts])

        # Simple keyword extraction
        words = re.findall(r'\b\w{4,}\b', all_content.lower())

        # Filter out common words
        stopwords = {
            'that', 'this', 'with', 'from', 'they', 'been', 'have', 'were',
            'said', 'each', 'which', 'their', 'time', 'will', 'about', 'would',
            'there', 'could', 'other', 'after', 'first', 'well', 'just', 'also'
        }

        filtered_words = [word for word in words if word not in stopwords]

        # Count frequency and return top keywords
        from collections import Counter
        word_counts = Counter(filtered_words)

        return [word for word, count in word_counts.most_common(10)]

    def _get_platform_breakdown(self, posts: List[Dict]) -> Dict:
        """Get breakdown by platform"""
        breakdown = {}

        for post in posts:
            platform = post['platform']
            if platform not in breakdown:
                breakdown[platform] = {
                    'count': 0,
                    'avg_sentiment': 0.0,
                    'total_engagement': 0.0
                }

            breakdown[platform]['count'] += 1
            breakdown[platform]['total_engagement'] += post['engagement_score']

        # Calculate averages
        for platform in breakdown:
            platform_posts = [p for p in posts if p['platform'] == platform]
            sentiments = [p['sentiment_score'] for p in platform_posts]
            breakdown[platform]['avg_sentiment'] = np.mean(sentiments) if sentiments else 0.0

        return breakdown

    def _score_to_label(self, score: float) -> str:
        """Convert score to label"""
        if score > 0.2:
            return 'positive'
        elif score < -0.2:
            return 'negative'
        else:
            return 'neutral'

    def _cache_social_post(self, post: Dict):
        """Cache social media post"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO social_posts
                    (platform, post_id, symbol, content, author, created_at,
                     score, comments_count, sentiment_score, engagement_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post['platform'],
                    post['post_id'],
                    post['symbol'],
                    post['content'],
                    post['author'],
                    post['created_at'],
                    post['score'],
                    post['comments_count'],
                    post['sentiment_score'],
                    post['engagement_score']
                ))
        except Exception as e:
            logging.warning(f"Social post cache error: {e}")

    def _cache_social_trend(self, trend_data: Dict, days: int):
        """Cache social media trend"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for platform in trend_data['platform_breakdown']:
                    platform_data = trend_data['platform_breakdown'][platform]

                    conn.execute("""
                        INSERT OR REPLACE INTO social_trends
                        (symbol, platform, date, mention_count, avg_sentiment,
                         total_engagement, trending_keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trend_data['symbol'],
                        platform,
                        datetime.now().date(),
                        platform_data['count'],
                        platform_data['avg_sentiment'],
                        platform_data['total_engagement'],
                        json.dumps(trend_data['trending_keywords'])
                    ))
        except Exception as e:
            logging.warning(f"Trend cache error: {e}")

    def _get_cached_social_posts(self, symbol: str, days: int) -> List[Dict]:
        """Get cached social media posts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("""
                    SELECT * FROM social_posts
                    WHERE symbol = ? AND created_at >= date('now', '-{} days')
                    ORDER BY created_at DESC
                """.format(days), conn, params=(symbol,))

                return df.to_dict('records')

        except Exception as e:
            logging.error(f"Social cache error: {e}")
            return []

    def _get_cached_reddit_posts(self, symbol: str) -> List[Dict]:
        """Get cached Reddit posts"""
        return self._get_cached_social_posts(symbol, 7)

    def _get_cached_twitter_posts(self, symbol: str) -> List[Dict]:
        """Get cached Twitter posts"""  
        return self._get_cached_social_posts(symbol, 7)

    def get_social_trends(self, symbol: str = None, days: int = 30) -> List[Dict]:
        """Get social media trends"""
        try:
            query = """
                SELECT * FROM social_trends
                WHERE date >= date('now', '-{} days')
            """.format(days)

            params = []
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            query += " ORDER BY date DESC, total_engagement DESC"

            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql(query, conn, params=params)
                return df.to_dict('records')

        except Exception as e:
            logging.error(f"Social trends error: {e}")
            return []

# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    monitor = SocialMediaMonitor()

    # Test Reddit monitoring
    reddit_posts = monitor.monitor_reddit("RELIANCE.NS")
    print(f"Found {len(reddit_posts)} Reddit posts for RELIANCE")

    # Get social sentiment
    sentiment = monitor.get_social_sentiment("TCS.NS")
    print(f"Social sentiment for TCS: {sentiment['sentiment_label']} ({sentiment['sentiment_score']:.3f})")

    # Get social trends
    trends = monitor.get_social_trends(days=7)
    print(f"Found {len(trends)} social trends")
