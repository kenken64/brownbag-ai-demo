"""
OpenAI Analyzer Module
Uses OpenAI GPT-4o Vision API to analyze candlestick charts
Extracts trading recommendations, support/resistance levels, and market insights
"""

import os
import base64
from typing import Dict, Optional, Any
import json
from datetime import datetime

from openai import OpenAI

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class OpenAIChartAnalyzer:
    """
    Analyzes candlestick charts using OpenAI GPT-4o Vision API
    Provides trading recommendations based on visual chart analysis
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI chart analyzer

        Args:
            api_key: OpenAI API key (reads from env if not provided)
            model: Model to use (gpt-4o-mini or gpt-4o)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env")

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

        print(f"🤖 OpenAI Chart Analyzer initialized (model: {model})")

    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def create_analysis_prompt(self, symbol: str, timeframe: str) -> str:
        """
        Create structured prompt for chart analysis

        Args:
            symbol: Trading pair symbol
            timeframe: Chart timeframe

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert cryptocurrency technical analyst. Analyze this {symbol} chart ({timeframe} timeframe) and provide a comprehensive trading analysis.

Please analyze the chart and provide your insights in the following JSON format:

{{
  "trend": "bullish/bearish/neutral/sideways",
  "trend_strength": "strong/moderate/weak",
  "support_levels": [price1, price2, price3],
  "resistance_levels": [price1, price2, price3],
  "recommendation": "BUY/SELL/HOLD",
  "confidence": "high/medium/low",
  "key_observations": [
    "observation 1",
    "observation 2",
    "observation 3"
  ],
  "risk_factors": [
    "risk 1",
    "risk 2"
  ],
  "price_target_short_term": {{
    "bullish": price,
    "bearish": price
  }},
  "technical_signals": {{
    "ema_alignment": "bullish/bearish/mixed",
    "rsi_condition": "overbought/oversold/neutral",
    "macd_signal": "bullish/bearish/neutral",
    "bollinger_position": "upper/middle/lower/outside",
    "volume_trend": "increasing/decreasing/stable"
  }},
  "entry_strategy": "brief entry recommendation",
  "exit_strategy": "brief exit recommendation",
  "overall_score": 0-10
}}

Focus on:
1. Overall trend direction and strength
2. Key support and resistance levels (actual price levels from the chart)
3. Technical indicator alignment (EMAs, RSI, MACD, Bollinger Bands)
4. Volume analysis
5. Potential entry and exit points
6. Risk factors and market conditions

Provide ONLY the JSON response, no additional text."""

        return prompt

    def analyze_chart(
        self,
        image_path: str,
        symbol: str,
        timeframe: str = "15m",
        max_tokens: int = 1500
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze chart image using OpenAI Vision API

        Args:
            image_path: Path to chart image
            symbol: Trading pair symbol
            timeframe: Chart timeframe
            max_tokens: Maximum tokens for response

        Returns:
            Dict with analysis results or None if error
        """
        try:
            print(f"\n🔍 Analyzing chart: {image_path}")
            print(f"   Symbol: {symbol} | Timeframe: {timeframe}")

            # Encode image
            base64_image = self.encode_image(image_path)

            # Create prompt
            prompt = self.create_analysis_prompt(symbol, timeframe)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for more consistent analysis
            )

            # Extract response
            content = response.choices[0].message.content.strip()

            # Parse JSON response
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            analysis = json.loads(content)

            # Add metadata
            analysis['analyzed_at'] = datetime.now().isoformat()
            analysis['model'] = self.model
            analysis['tokens_used'] = response.usage.total_tokens

            # Print summary
            print(f"\n📊 Analysis Results:")
            print(f"   Trend: {analysis.get('trend', 'N/A').upper()} ({analysis.get('trend_strength', 'N/A')})")
            print(f"   Recommendation: {analysis.get('recommendation', 'N/A')} (Confidence: {analysis.get('confidence', 'N/A')})")
            print(f"   Overall Score: {analysis.get('overall_score', 'N/A')}/10")
            print(f"   Tokens Used: {response.usage.total_tokens}")

            if analysis.get('support_levels'):
                print(f"   Support: {', '.join([f'${x:,.2f}' for x in analysis['support_levels']])}")
            if analysis.get('resistance_levels'):
                print(f"   Resistance: {', '.join([f'${x:,.2f}' for x in analysis['resistance_levels']])}")

            return analysis

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"   Raw response: {content[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return None

    def get_simple_recommendation(
        self,
        image_path: str,
        symbol: str,
        timeframe: str = "15m"
    ) -> Optional[Dict[str, Any]]:
        """
        Get simplified recommendation (faster, cheaper)

        Args:
            image_path: Path to chart image
            symbol: Trading pair symbol
            timeframe: Chart timeframe

        Returns:
            Dict with simple recommendation
        """
        try:
            # Encode image
            base64_image = self.encode_image(image_path)

            # Simple prompt
            prompt = f"""Analyze this {symbol} chart ({timeframe}) and provide a brief trading recommendation.

Return ONLY a JSON object with:
{{
  "recommendation": "BUY/SELL/HOLD",
  "confidence": "high/medium/low",
  "reason": "one sentence explanation",
  "trend": "bullish/bearish/neutral"
}}"""

            # Call API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )

            # Parse response
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            content = content.strip()

            result = json.loads(content)
            result['tokens_used'] = response.usage.total_tokens

            print(f"\n💡 Quick Recommendation:")
            print(f"   Action: {result.get('recommendation', 'N/A')} (Confidence: {result.get('confidence', 'N/A')})")
            print(f"   Reason: {result.get('reason', 'N/A')}")
            print(f"   Tokens: {result['tokens_used']}")

            return result

        except Exception as e:
            print(f"❌ Error getting recommendation: {e}")
            return None


if __name__ == "__main__":
    # Test OpenAI analyzer
    print("Testing OpenAI Chart Analyzer...\n")

    # Check for test chart
    import glob

    charts = glob.glob("charts/*.png")
    if not charts:
        print("❌ No charts found in charts/ directory")
        print("   Run chart_generator.py first to create test charts")
        exit(1)

    # Use most recent chart
    latest_chart = max(charts, key=os.path.getctime)
    print(f"📊 Using chart: {latest_chart}\n")

    # Initialize analyzer
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    analyzer = OpenAIChartAnalyzer(model=model)

    # Test 1: Simple recommendation (faster, cheaper)
    print("\n" + "=" * 60)
    print("TEST 1: Simple Recommendation")
    print("=" * 60)

    simple_result = analyzer.get_simple_recommendation(
        image_path=latest_chart,
        symbol='BTCUSDT',
        timeframe='15m'
    )

    # Test 2: Full analysis (more detailed, more tokens)
    print("\n" + "=" * 60)
    print("TEST 2: Comprehensive Analysis")
    print("=" * 60)

    full_result = analyzer.analyze_chart(
        image_path=latest_chart,
        symbol='BTCUSDT',
        timeframe='15m'
    )

    if full_result:
        print("\n📋 Full Analysis Summary:")
        print(json.dumps(full_result, indent=2))

    print("\n✅ OpenAI Chart Analyzer test completed!")
