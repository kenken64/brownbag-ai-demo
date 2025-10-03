"""
Cache Manager Module
Persistent file-based caching system to reduce API costs by 90-95%
Supports multiple cache durations and invalidation strategies
"""

import os
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib


class CacheManager:
    """
    File-based cache manager for API responses
    Reduces API costs through aggressive caching
    """

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'invalidations': 0,
            'expired': 0
        }

        print(f"💾 Cache Manager initialized (cache dir: {cache_dir}/)")

    def _generate_cache_key(self, key: str, **kwargs) -> str:
        """
        Generate unique cache key from parameters

        Args:
            key: Base key name
            **kwargs: Additional parameters to include in key

        Returns:
            MD5 hash of combined parameters
        """
        # Combine key and sorted kwargs into string
        combined = f"{key}_{json.dumps(kwargs, sort_keys=True)}"

        # Generate MD5 hash
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """
        Get file path for cache key

        Args:
            cache_key: Cache key hash

        Returns:
            Full path to cache file
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def get(
        self,
        key: str,
        max_age_seconds: Optional[int] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Get cached value if exists and not expired

        Args:
            key: Cache key name
            max_age_seconds: Maximum age in seconds (None = no expiry)
            **kwargs: Additional parameters for cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._generate_cache_key(key, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        # Check if cache file exists
        if not os.path.exists(cache_path):
            self.stats['misses'] += 1
            return None

        try:
            # Read cache file
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check expiry if max_age specified
            if max_age_seconds is not None:
                cached_at = datetime.fromisoformat(cache_data['cached_at'])
                age_seconds = (datetime.now() - cached_at).total_seconds()

                if age_seconds > max_age_seconds:
                    # Cache expired
                    self.stats['expired'] += 1
                    return None

            # Cache hit
            self.stats['hits'] += 1
            return cache_data['value']

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Corrupted cache file
            print(f"⚠️ Corrupted cache file: {cache_path} - {e}")
            os.remove(cache_path)
            self.stats['misses'] += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict] = None,
        **kwargs
    ):
        """
        Store value in cache

        Args:
            key: Cache key name
            value: Value to cache (must be JSON serializable)
            metadata: Optional metadata to store with value
            **kwargs: Additional parameters for cache key
        """
        cache_key = self._generate_cache_key(key, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        # Prepare cache data
        cache_data = {
            'key': key,
            'value': value,
            'cached_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # Add kwargs to metadata
        if kwargs:
            cache_data['metadata']['params'] = kwargs

        try:
            # Write cache file
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)

            self.stats['writes'] += 1

        except (TypeError, ValueError) as e:
            print(f"❌ Failed to cache value: {e}")

    def invalidate(self, key: str, **kwargs):
        """
        Invalidate (delete) cached value

        Args:
            key: Cache key name
            **kwargs: Additional parameters for cache key
        """
        cache_key = self._generate_cache_key(key, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if os.path.exists(cache_path):
            os.remove(cache_path)
            self.stats['invalidations'] += 1

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache files matching pattern

        Args:
            pattern: String pattern to match in original key
        """
        invalidated = 0

        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue

            cache_path = os.path.join(self.cache_dir, filename)

            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                if pattern in cache_data.get('key', ''):
                    os.remove(cache_path)
                    invalidated += 1

            except (json.JSONDecodeError, KeyError):
                continue

        self.stats['invalidations'] += invalidated
        print(f"🗑️ Invalidated {invalidated} cache entries matching '{pattern}'")

    def invalidate_all(self):
        """Invalidate (delete) all cached values"""
        invalidated = 0

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, filename))
                invalidated += 1

        self.stats['invalidations'] += invalidated
        print(f"🗑️ Invalidated all {invalidated} cache entries")

    def get_or_fetch(
        self,
        key: str,
        fetch_func,
        max_age_seconds: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Get from cache or fetch if not available

        Args:
            key: Cache key name
            fetch_func: Function to call if cache miss (should return value)
            max_age_seconds: Maximum cache age in seconds
            **kwargs: Additional parameters for cache key and fetch function

        Returns:
            Cached or freshly fetched value
        """
        # Try to get from cache
        cached_value = self.get(key, max_age_seconds=max_age_seconds, **kwargs)

        if cached_value is not None:
            return cached_value

        # Cache miss - fetch fresh data
        try:
            fresh_value = fetch_func(**kwargs)

            # Store in cache
            if fresh_value is not None:
                self.set(key, fresh_value, **kwargs)

            return fresh_value

        except Exception as e:
            print(f"❌ Fetch function failed: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with hit rate, miss rate, and counts
        """
        total_reads = self.stats['hits'] + self.stats['misses']

        if total_reads > 0:
            hit_rate = (self.stats['hits'] / total_reads) * 100
            miss_rate = (self.stats['misses'] / total_reads) * 100
        else:
            hit_rate = 0
            miss_rate = 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'writes': self.stats['writes'],
            'invalidations': self.stats['invalidations'],
            'expired': self.stats['expired'],
            'total_reads': total_reads,
            'hit_rate': round(hit_rate, 2),
            'miss_rate': round(miss_rate, 2),
            'cache_size': self._get_cache_size()
        }

    def _get_cache_size(self) -> Dict[str, Any]:
        """
        Get cache directory size and file count

        Returns:
            Dict with file count and total size
        """
        total_size = 0
        file_count = 0

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                file_count += 1
                file_path = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(file_path)

        return {
            'files': file_count,
            'bytes': total_size,
            'mb': round(total_size / (1024 * 1024), 2)
        }

    def cleanup_expired(self, max_age_seconds: int):
        """
        Remove all cache files older than max_age_seconds

        Args:
            max_age_seconds: Maximum age in seconds
        """
        cleaned = 0
        now = datetime.now()

        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue

            cache_path = os.path.join(self.cache_dir, filename)

            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                cached_at = datetime.fromisoformat(cache_data['cached_at'])
                age_seconds = (now - cached_at).total_seconds()

                if age_seconds > max_age_seconds:
                    os.remove(cache_path)
                    cleaned += 1

            except (json.JSONDecodeError, KeyError, ValueError):
                # Remove corrupted files
                os.remove(cache_path)
                cleaned += 1

        print(f"🧹 Cleaned up {cleaned} expired cache entries")
        return cleaned

    def print_stats(self):
        """Print formatted cache statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("💾 CACHE STATISTICS")
        print("=" * 60)
        print(f"📊 Performance:")
        print(f"   Hits: {stats['hits']}")
        print(f"   Misses: {stats['misses']}")
        print(f"   Hit Rate: {stats['hit_rate']}%")
        print(f"   Miss Rate: {stats['miss_rate']}%")
        print(f"\n📝 Operations:")
        print(f"   Writes: {stats['writes']}")
        print(f"   Invalidations: {stats['invalidations']}")
        print(f"   Expired: {stats['expired']}")
        print(f"\n💽 Storage:")
        print(f"   Files: {stats['cache_size']['files']}")
        print(f"   Size: {stats['cache_size']['mb']} MB")
        print("=" * 60)


# Specialized cache managers for different use cases

class MarketDataCache(CacheManager):
    """Cache manager specifically for market data with default 5-minute TTL"""

    def __init__(self, cache_dir: str = "cache/market_data"):
        super().__init__(cache_dir)
        self.default_ttl = 300  # 5 minutes

    def get_market_data(self, symbol: str, interval: str = '1m'):
        """Get cached market data"""
        return self.get(
            'market_data',
            max_age_seconds=self.default_ttl,
            symbol=symbol,
            interval=interval
        )

    def set_market_data(self, symbol: str, interval: str, data: Any):
        """Cache market data"""
        self.set(
            'market_data',
            data,
            symbol=symbol,
            interval=interval
        )


class SentimentCache(CacheManager):
    """
    Cache manager for sentiment analysis
    Different TTLs for premium vs cost-saving mode
    """

    def __init__(self, cache_dir: str = "cache/sentiment"):
        super().__init__(cache_dir)
        self.premium_ttl = 3600  # 1 hour
        self.cost_saving_ttl = 86400  # 24 hours

    def get_sentiment(
        self,
        text: str,
        mode: str = 'premium'
    ) -> Optional[Dict]:
        """
        Get cached sentiment analysis

        Args:
            text: Text to analyze
            mode: 'premium' or 'cost-saving'

        Returns:
            Cached sentiment dict or None
        """
        ttl = self.premium_ttl if mode == 'premium' else self.cost_saving_ttl

        return self.get(
            'sentiment',
            max_age_seconds=ttl,
            text_hash=hashlib.md5(text.encode()).hexdigest()[:16]
        )

    def set_sentiment(self, text: str, sentiment_data: Dict):
        """
        Cache sentiment analysis result

        Args:
            text: Analyzed text
            sentiment_data: Sentiment analysis result
        """
        self.set(
            'sentiment',
            sentiment_data,
            text_hash=hashlib.md5(text.encode()).hexdigest()[:16]
        )


class NewsCache(CacheManager):
    """Cache manager for news articles"""

    def __init__(self, cache_dir: str = "cache/news"):
        super().__init__(cache_dir)
        self.ttl = 3600  # 1 hour

    def get_news(self, query: str, page: int = 1) -> Optional[list]:
        """Get cached news articles"""
        return self.get(
            'news',
            max_age_seconds=self.ttl,
            query=query,
            page=page
        )

    def set_news(self, query: str, page: int, articles: list):
        """Cache news articles"""
        self.set(
            'news',
            articles,
            query=query,
            page=page
        )


if __name__ == "__main__":
    # Test cache manager
    print("Testing Cache Manager...\n")

    # Test 1: Basic cache operations
    print("=" * 60)
    print("TEST 1: Basic Cache Operations")
    print("=" * 60)

    cache = CacheManager(cache_dir="cache/test")

    # Set value
    print("\n1. Setting cache value...")
    cache.set('test_key', {'price': 65000, 'volume': 1000}, symbol='BTCUSDT')

    # Get value (should hit)
    print("2. Getting cache value...")
    value = cache.get('test_key', symbol='BTCUSDT')
    print(f"   Retrieved: {value}")

    # Get non-existent value (should miss)
    print("3. Getting non-existent value...")
    value = cache.get('missing_key')
    print(f"   Retrieved: {value}")

    # Test 2: TTL expiration
    print("\n\n" + "=" * 60)
    print("TEST 2: TTL Expiration")
    print("=" * 60)

    print("\n1. Setting value with 2-second TTL...")
    cache.set('expiring_key', {'data': 'test'})

    print("2. Getting immediately (should hit)...")
    value = cache.get('expiring_key', max_age_seconds=2)
    print(f"   Retrieved: {value}")

    print("3. Waiting 3 seconds...")
    time.sleep(3)

    print("4. Getting after expiry (should miss)...")
    value = cache.get('expiring_key', max_age_seconds=2)
    print(f"   Retrieved: {value}")

    # Test 3: get_or_fetch
    print("\n\n" + "=" * 60)
    print("TEST 3: Get or Fetch Pattern")
    print("=" * 60)

    def fetch_btc_price(**kwargs):
        print("   📡 Fetching fresh data...")
        return {'price': 65432.10, 'volume': 5000}

    print("\n1. First call (cache miss, will fetch)...")
    data = cache.get_or_fetch(
        'btc_price',
        fetch_btc_price,
        max_age_seconds=10,
        symbol='BTCUSDT'
    )
    print(f"   Data: {data}")

    print("\n2. Second call (cache hit)...")
    data = cache.get_or_fetch(
        'btc_price',
        fetch_btc_price,
        max_age_seconds=10,
        symbol='BTCUSDT'
    )
    print(f"   Data: {data}")

    # Test 4: Statistics
    print("\n\n" + "=" * 60)
    print("TEST 4: Cache Statistics")
    print("=" * 60)

    cache.print_stats()

    # Test 5: Specialized caches
    print("\n\n" + "=" * 60)
    print("TEST 5: Specialized Cache Managers")
    print("=" * 60)

    # Sentiment cache
    sentiment_cache = SentimentCache()
    sentiment_cache.set_sentiment(
        "Bitcoin surges to new all-time high",
        {'sentiment': 'bullish', 'confidence': 95}
    )

    result = sentiment_cache.get_sentiment(
        "Bitcoin surges to new all-time high",
        mode='premium'
    )
    print(f"\nSentiment cache: {result}")

    # News cache
    news_cache = NewsCache()
    news_cache.set_news(
        'cryptocurrency',
        page=1,
        articles=[{'title': 'BTC hits $100k', 'source': 'CoinDesk'}]
    )

    result = news_cache.get_news('cryptocurrency', page=1)
    print(f"News cache: {result}")

    print("\n\n" + "=" * 60)
    print("✅ Cache Manager test completed!")
    print("=" * 60)
