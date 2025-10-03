"""
News Fetcher Module
Fetches cryptocurrency news from NewsAPI.org
Supports free tier (1000 requests/day) with rate limiting
"""

import os
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class NewsFetcher:
    """
    Cryptocurrency news fetcher using NewsAPI.org
    Free tier: 1000 requests/day
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize news fetcher

        Args:
            api_key: NewsAPI.org API key (reads from env if not provided)
        """
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError("NewsAPI key not found. Set NEWS_API_KEY in .env")

        self.base_url = "https://newsapi.org/v2"
        self.rate_limit_delay = 0.1  # 100ms between requests (safe for free tier)
        self.last_request_time = 0

        # Cryptocurrency-related keywords
        self.crypto_keywords = [
            'bitcoin', 'ethereum', 'cryptocurrency', 'crypto', 'blockchain',
            'BTC', 'ETH', 'altcoin', 'DeFi', 'NFT', 'Web3'
        ]

        print(f"📰 News Fetcher initialized (NewsAPI.org)")

    def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make API request with error handling

        Args:
            endpoint: API endpoint (e.g., 'everything', 'top-headlines')
            params: Query parameters

        Returns:
            Response JSON or None if error
        """
        # Apply rate limiting
        self._rate_limit()

        # Add API key to params
        params['apiKey'] = self.api_key

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("⚠️ NewsAPI rate limit exceeded")
                return None
            elif response.status_code == 401:
                print("❌ NewsAPI authentication failed - check API key")
                return None
            else:
                print(f"❌ NewsAPI error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("❌ NewsAPI request timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ NewsAPI request failed: {e}")
            return None

    def get_crypto_news(
        self,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        days_back: int = 7,
        language: str = 'en',
        sort_by: str = 'publishedAt'
    ) -> Optional[Dict[str, Any]]:
        """
        Get cryptocurrency news articles

        Args:
            query: Search query (default: 'cryptocurrency OR bitcoin OR ethereum')
            page: Page number (1-indexed)
            page_size: Articles per page (max 100)
            days_back: How many days back to search
            language: Language code (default: 'en')
            sort_by: 'publishedAt', 'relevancy', or 'popularity'

        Returns:
            Dict with articles and metadata or None
        """
        # Default query for crypto news
        if query is None:
            query = 'cryptocurrency OR bitcoin OR ethereum OR crypto'

        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        params = {
            'q': query,
            'from': from_date,
            'language': language,
            'sortBy': sort_by,
            'page': page,
            'pageSize': page_size
        }

        print(f"📰 Fetching crypto news (query: '{query}', page: {page})...")

        response = self._make_request('everything', params)

        if response and response.get('status') == 'ok':
            total_results = response.get('totalResults', 0)
            articles = response.get('articles', [])

            print(f"✅ Found {len(articles)} articles (total: {total_results})")

            return {
                'articles': articles,
                'total_results': total_results,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_results + page_size - 1) // page_size,
                'fetched_at': datetime.now().isoformat()
            }

        return None

    def get_top_headlines(
        self,
        category: str = 'business',
        country: str = 'us',
        page: int = 1,
        page_size: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Get top headlines (useful for general market sentiment)

        Args:
            category: News category
            country: Country code (us, gb, etc.)
            page: Page number
            page_size: Articles per page

        Returns:
            Dict with articles and metadata or None
        """
        params = {
            'category': category,
            'country': country,
            'page': page,
            'pageSize': page_size
        }

        print(f"📰 Fetching top headlines ({category}/{country})...")

        response = self._make_request('top-headlines', params)

        if response and response.get('status') == 'ok':
            articles = response.get('articles', [])
            total_results = response.get('totalResults', 0)

            print(f"✅ Found {len(articles)} headlines")

            return {
                'articles': articles,
                'total_results': total_results,
                'page': page,
                'page_size': page_size,
                'fetched_at': datetime.now().isoformat()
            }

        return None

    def search_specific_coin(
        self,
        coin_name: str,
        page: int = 1,
        page_size: int = 10,
        days_back: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Search news for specific cryptocurrency

        Args:
            coin_name: Coin name (e.g., 'Bitcoin', 'Ethereum', 'Solana')
            page: Page number
            page_size: Articles per page
            days_back: Days to search back

        Returns:
            News results dict or None
        """
        query = f'"{coin_name}" OR {coin_name.upper()}'
        return self.get_crypto_news(
            query=query,
            page=page,
            page_size=page_size,
            days_back=days_back
        )

    def filter_by_source(
        self,
        articles: List[Dict],
        sources: List[str]
    ) -> List[Dict]:
        """
        Filter articles by source

        Args:
            articles: List of article dicts
            sources: List of source names to include

        Returns:
            Filtered articles
        """
        sources_lower = [s.lower() for s in sources]

        return [
            article for article in articles
            if article.get('source', {}).get('name', '').lower() in sources_lower
        ]

    def filter_by_keywords(
        self,
        articles: List[Dict],
        keywords: List[str],
        field: str = 'title'
    ) -> List[Dict]:
        """
        Filter articles by keywords in title or description

        Args:
            articles: List of article dicts
            keywords: Keywords to search for
            field: 'title', 'description', or 'both'

        Returns:
            Filtered articles
        """
        keywords_lower = [k.lower() for k in keywords]
        filtered = []

        for article in articles:
            text_to_search = ""

            if field in ['title', 'both']:
                text_to_search += article.get('title', '').lower() + ' '

            if field in ['description', 'both']:
                text_to_search += article.get('description', '').lower()

            # Check if any keyword is in the text
            if any(keyword in text_to_search for keyword in keywords_lower):
                filtered.append(article)

        return filtered

    def get_article_summary(self, article: Dict) -> Dict[str, str]:
        """
        Extract summary information from article

        Args:
            article: Article dict from NewsAPI

        Returns:
            Simplified article dict
        """
        return {
            'title': article.get('title', 'No title'),
            'description': article.get('description', 'No description'),
            'source': article.get('source', {}).get('name', 'Unknown'),
            'author': article.get('author', 'Unknown'),
            'url': article.get('url', ''),
            'published_at': article.get('publishedAt', ''),
            'image_url': article.get('urlToImage', ''),
            'content_preview': article.get('content', '')[:200] if article.get('content') else ''
        }

    def print_articles(self, articles: List[Dict], limit: int = 5):
        """
        Print formatted article summaries

        Args:
            articles: List of articles
            limit: Maximum articles to print
        """
        if not articles:
            print("No articles to display")
            return

        print("\n" + "=" * 80)
        print(f"📰 ARTICLES ({len(articles)} total)")
        print("=" * 80)

        for i, article in enumerate(articles[:limit], 1):
            summary = self.get_article_summary(article)

            print(f"\n{i}. {summary['title']}")
            print(f"   Source: {summary['source']}")
            print(f"   Published: {summary['published_at']}")
            print(f"   {summary['description'][:150]}...")
            print(f"   URL: {summary['url']}")

        if len(articles) > limit:
            print(f"\n... and {len(articles) - limit} more articles")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test news fetcher
    print("Testing News Fetcher...\n")

    try:
        fetcher = NewsFetcher()

        # Test 1: Get crypto news
        print("=" * 80)
        print("TEST 1: Cryptocurrency News")
        print("=" * 80)

        result = fetcher.get_crypto_news(page=1, page_size=5, days_back=3)

        if result:
            articles = result['articles']
            print(f"\n📊 Results:")
            print(f"   Total articles: {result['total_results']}")
            print(f"   Page: {result['page']} of {result['total_pages']}")
            print(f"   Fetched: {len(articles)} articles")

            fetcher.print_articles(articles, limit=3)

        # Test 2: Search specific coin
        print("\n\n" + "=" * 80)
        print("TEST 2: Bitcoin-Specific News")
        print("=" * 80)

        result = fetcher.search_specific_coin('Bitcoin', page=1, page_size=3)

        if result:
            fetcher.print_articles(result['articles'], limit=3)

        # Test 3: Filter by keywords
        print("\n\n" + "=" * 80)
        print("TEST 3: Filter by Keywords")
        print("=" * 80)

        result = fetcher.get_crypto_news(page=1, page_size=20, days_back=7)

        if result:
            # Filter for bullish news
            bullish_keywords = ['surge', 'rally', 'breakthrough', 'adoption', 'bullish']
            bullish_articles = fetcher.filter_by_keywords(
                result['articles'],
                bullish_keywords,
                field='both'
            )

            print(f"\n🟢 Bullish articles: {len(bullish_articles)}")
            fetcher.print_articles(bullish_articles, limit=2)

        print("\n\n" + "=" * 80)
        print("✅ News Fetcher test completed!")
        print("=" * 80)

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nSetup instructions:")
        print("1. Get free API key from https://newsapi.org/")
        print("2. Add to .env: NEWS_API_KEY=your_api_key")
