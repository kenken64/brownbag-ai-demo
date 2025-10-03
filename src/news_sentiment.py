"""
News Sentiment Analysis Module
Dual-mode sentiment analysis: OpenAI GPT-4o-mini (Premium) or Local (Cost-Saving)
Integrates with cache manager to reduce API costs
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

from dotenv import load_dotenv
load_dotenv()


class NewsSentimentAnalyzer:
    """
    Dual-mode news sentiment analyzer
    Switches between OpenAI and local analysis based on USE_LOCAL_SENTIMENT
    """

    def __init__(
        self,
        use_local: Optional[bool] = None,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None
    ):
        """
        Initialize news sentiment analyzer

        Args:
            use_local: Use local sentiment (True) or OpenAI (False). Reads from env if None
            openai_api_key: OpenAI API key (reads from env if not provided)
            openai_model: OpenAI model to use (default: gpt-4o-mini)
        """
        # Determine mode
        if use_local is None:
            use_local = os.getenv('USE_LOCAL_SENTIMENT', 'false').lower() == 'true'

        self.use_local = use_local
        self.openai_model = openai_model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

        # Initialize appropriate analyzer
        if self.use_local:
            from src.sentiment_local import LocalSentimentAnalyzer
            self.analyzer = LocalSentimentAnalyzer()
            self.mode = 'LOCAL (Cost-Saving)'
        else:
            # Initialize OpenAI
            try:
                from openai import OpenAI
                api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OpenAI API key not found")
                self.openai_client = OpenAI(api_key=api_key)
                self.mode = f'OPENAI ({self.openai_model})'
            except ImportError:
                print("⚠️ OpenAI package not installed, falling back to local")
                from src.sentiment_local import LocalSentimentAnalyzer
                self.analyzer = LocalSentimentAnalyzer()
                self.use_local = True
                self.mode = 'LOCAL (Fallback)'

        # Initialize cache
        try:
            from src.cache_manager import SentimentCache
            self.cache = SentimentCache()
            self.use_cache = True
        except ImportError:
            print("⚠️ Cache manager not available")
            self.cache = None
            self.use_cache = False

        print(f"📊 News Sentiment Analyzer initialized (mode: {self.mode})")

    def analyze_article(
        self,
        title: str,
        description: str = "",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of news article

        Args:
            title: Article headline
            description: Article description/summary
            use_cache: Use cached results if available

        Returns:
            Sentiment analysis dict
        """
        # Combine title and description
        combined_text = f"{title} {description}".strip()

        if not combined_text:
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'reason': 'Empty article text',
                'mode': self.mode
            }

        # Try cache first
        if use_cache and self.use_cache:
            mode_key = 'cost-saving' if self.use_local else 'premium'
            cached = self.cache.get_sentiment(combined_text, mode=mode_key)

            if cached:
                cached['cached'] = True
                return cached

        # Analyze based on mode
        if self.use_local:
            result = self._analyze_local(title, description)
        else:
            result = self._analyze_openai(title, description)

        # Add metadata
        result['mode'] = self.mode
        result['cached'] = False
        result['analyzed_at'] = datetime.now().isoformat()

        # Cache the result
        if self.use_cache:
            self.cache.set_sentiment(combined_text, result)

        return result

    def _analyze_local(self, title: str, description: str) -> Dict[str, Any]:
        """
        Analyze using local keyword-based sentiment

        Args:
            title: Article title
            description: Article description

        Returns:
            Sentiment analysis dict
        """
        result = self.analyzer.analyze_news_article(title, description)

        # Normalize to standard format
        return {
            'sentiment': result['sentiment'],
            'confidence': result['confidence'],
            'score': result.get('score', 0),
            'reason': result['reason'],
            'bullish_signals': len(result.get('bullish_matches', [])),
            'bearish_signals': len(result.get('bearish_matches', [])),
            'method': 'local_keyword'
        }

    def _analyze_openai(self, title: str, description: str) -> Dict[str, Any]:
        """
        Analyze using OpenAI GPT-4o-mini

        Args:
            title: Article title
            description: Article description

        Returns:
            Sentiment analysis dict
        """
        # Combine title and description, weight title more
        text = f"Headline: {title}\n\nDescription: {description}"

        # Create prompt
        prompt = f"""Analyze the sentiment of this cryptocurrency news article.

{text}

Provide your analysis in JSON format:
{{
  "sentiment": "bullish/bearish/neutral",
  "confidence": 0-100,
  "reason": "brief explanation (1-2 sentences)",
  "key_points": ["point 1", "point 2"]
}}

Focus on:
1. Overall market sentiment (bullish/bearish/neutral)
2. Impact on cryptocurrency prices
3. Key factors driving the sentiment

Provide ONLY the JSON response, no additional text."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a cryptocurrency market analyst specializing in sentiment analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            import json
            analysis = json.loads(content)

            # Normalize confidence to 0-100
            confidence = analysis.get('confidence', 50)
            if confidence > 100:
                confidence = 100
            elif confidence < 0:
                confidence = 0

            return {
                'sentiment': analysis.get('sentiment', 'neutral'),
                'confidence': int(confidence),
                'reason': analysis.get('reason', 'OpenAI analysis'),
                'key_points': analysis.get('key_points', []),
                'tokens_used': response.usage.total_tokens,
                'method': 'openai'
            }

        except Exception as e:
            print(f"❌ OpenAI sentiment analysis failed: {e}")

            # Fallback to local
            print("   Falling back to local sentiment analysis...")
            return self._analyze_local(title, description)

    def batch_analyze(
        self,
        articles: List[Dict],
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple articles

        Args:
            articles: List of article dicts (must have 'title' and 'description')
            use_cache: Use cached results

        Returns:
            List of sentiment analysis results
        """
        results = []

        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')

            sentiment = self.analyze_article(
                title=title,
                description=description,
                use_cache=use_cache
            )

            # Add article metadata
            sentiment['article_title'] = title
            sentiment['article_url'] = article.get('url', '')
            sentiment['article_source'] = article.get('source', {}).get('name', 'Unknown')
            sentiment['published_at'] = article.get('publishedAt', '')

            results.append(sentiment)

        return results

    def get_overall_sentiment(
        self,
        sentiment_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate overall market sentiment from multiple articles

        Args:
            sentiment_results: List of sentiment analysis results

        Returns:
            Overall sentiment summary
        """
        if not sentiment_results:
            return {
                'overall_sentiment': 'neutral',
                'confidence': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'total_articles': 0
            }

        bullish_count = sum(1 for r in sentiment_results if r['sentiment'] == 'bullish')
        bearish_count = sum(1 for r in sentiment_results if r['sentiment'] == 'bearish')
        neutral_count = sum(1 for r in sentiment_results if r['sentiment'] == 'neutral')

        # Calculate weighted sentiment based on confidence
        weighted_score = 0
        total_confidence = 0

        for result in sentiment_results:
            confidence = result.get('confidence', 50) / 100.0
            sentiment = result['sentiment']

            if sentiment == 'bullish':
                weighted_score += confidence
            elif sentiment == 'bearish':
                weighted_score -= confidence

            total_confidence += confidence

        # Determine overall sentiment
        if weighted_score > 0.3:
            overall = 'bullish'
        elif weighted_score < -0.3:
            overall = 'bearish'
        else:
            overall = 'neutral'

        # Calculate overall confidence
        avg_confidence = int((total_confidence / len(sentiment_results)) * 100) if sentiment_results else 0

        return {
            'overall_sentiment': overall,
            'confidence': avg_confidence,
            'weighted_score': round(weighted_score, 2),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'total_articles': len(sentiment_results),
            'bullish_percentage': round((bullish_count / len(sentiment_results)) * 100, 1),
            'bearish_percentage': round((bearish_count / len(sentiment_results)) * 100, 1),
            'mode': self.mode
        }

    def print_sentiment_summary(self, results: List[Dict]):
        """
        Print formatted sentiment analysis summary

        Args:
            results: List of sentiment results
        """
        if not results:
            print("No sentiment results to display")
            return

        overall = self.get_overall_sentiment(results)

        print("\n" + "=" * 80)
        print("📊 NEWS SENTIMENT ANALYSIS")
        print("=" * 80)

        print(f"\n🔍 Analysis Mode: {self.mode}")
        print(f"📰 Articles Analyzed: {overall['total_articles']}")

        # Overall sentiment
        sentiment_emoji = {
            'bullish': '🟢',
            'bearish': '🔴',
            'neutral': '🟡'
        }

        print(f"\n{sentiment_emoji[overall['overall_sentiment']]} Overall Sentiment: {overall['overall_sentiment'].upper()}")
        print(f"💯 Confidence: {overall['confidence']}%")
        print(f"📊 Weighted Score: {overall['weighted_score']}")

        # Breakdown
        print(f"\n📈 Sentiment Breakdown:")
        print(f"   🟢 Bullish: {overall['bullish_count']} ({overall['bullish_percentage']}%)")
        print(f"   🔴 Bearish: {overall['bearish_count']} ({overall['bearish_percentage']}%)")
        print(f"   🟡 Neutral: {overall['neutral_count']}")

        # Top articles by sentiment
        print(f"\n📰 Sample Articles:")

        for sentiment_type in ['bullish', 'bearish']:
            typed_results = [r for r in results if r['sentiment'] == sentiment_type]
            if typed_results:
                # Sort by confidence
                typed_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                top = typed_results[0]

                emoji = sentiment_emoji[sentiment_type]
                print(f"\n{emoji} {sentiment_type.upper()} ({top.get('confidence', 0)}%):")
                print(f"   {top.get('article_title', 'No title')[:80]}...")
                print(f"   {top.get('reason', 'No reason')[:100]}...")

        # Cache statistics
        cached_count = sum(1 for r in results if r.get('cached', False))
        if cached_count > 0:
            cache_rate = (cached_count / len(results)) * 100
            print(f"\n💾 Cache: {cached_count}/{len(results)} cached ({cache_rate:.1f}% hit rate)")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test news sentiment analyzer
    print("Testing News Sentiment Analyzer...\n")

    # Test articles
    test_articles = [
        {
            'title': 'Bitcoin Surges to New All-Time High Amid Institutional Adoption',
            'description': 'Bitcoin reached a new record high today as major institutions continue to invest in the cryptocurrency market.',
            'source': {'name': 'CoinDesk'},
            'url': 'https://example.com/1'
        },
        {
            'title': 'Crypto Market Faces Regulatory Concerns',
            'description': 'New regulations could impact cryptocurrency trading as governments increase scrutiny.',
            'source': {'name': 'Bloomberg'},
            'url': 'https://example.com/2'
        },
        {
            'title': 'Ethereum Upgrade Shows Promise',
            'description': 'The latest Ethereum upgrade demonstrates improved scalability and reduced transaction costs.',
            'source': {'name': 'CryptoNews'},
            'url': 'https://example.com/3'
        },
        {
            'title': 'Market Consolidates After Recent Rally',
            'description': 'Cryptocurrency prices remain stable as traders await the next market direction.',
            'source': {'name': 'Reuters'},
            'url': 'https://example.com/4'
        }
    ]

    # Test both modes
    for use_local in [True, False]:
        print("\n" + "=" * 80)
        mode_name = "LOCAL (Cost-Saving)" if use_local else "OPENAI (Premium)"
        print(f"Testing {mode_name} Mode")
        print("=" * 80)

        try:
            analyzer = NewsSentimentAnalyzer(use_local=use_local)

            # Analyze articles
            results = analyzer.batch_analyze(test_articles, use_cache=False)

            # Print summary
            analyzer.print_sentiment_summary(results)

        except Exception as e:
            print(f"❌ Error in {mode_name} mode: {e}")
            if not use_local:
                print("   (This is expected if OpenAI API key is not configured)")

    print("\n\n" + "=" * 80)
    print("✅ News Sentiment Analyzer test completed!")
    print("=" * 80)
