"""
Chart Analysis Bot
Runs on 15-minute cycles to generate charts and analyze them with OpenAI GPT-4o
Stores analysis results in database for use by main trading bot
"""

import os
import sys
import time
import signal
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import TradingDatabase
from src.binance_client import BinanceFuturesClient
from src.chart_generator import ChartGenerator
from src.openai_analyzer import OpenAIChartAnalyzer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class ChartAnalysisBot:
    """
    Automated chart analysis bot
    Generates charts every 15 minutes and analyzes with AI
    """

    def __init__(self):
        """Initialize chart analysis bot"""
        print("=" * 60)
        print("📊 CHART ANALYSIS BOT")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Configuration
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.analysis_interval = int(os.getenv('CHART_ANALYSIS_INTERVAL', '900'))  # 15 minutes = 900 seconds
        self.testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

        print(f"⚙️ Configuration:")
        print(f"   Trading Pair: {self.trading_pair}")
        print(f"   Analysis Interval: {self.analysis_interval}s ({self.analysis_interval // 60} minutes)")
        print(f"   OpenAI Model: {self.openai_model}")
        print(f"   Mode: {'TESTNET' if self.testnet else 'LIVE'}\n")

        # Initialize components
        print("🔧 Initializing components...")
        self.db = TradingDatabase()
        self.binance = BinanceFuturesClient(testnet=self.testnet)
        self.chart_generator = ChartGenerator(output_dir="charts")
        self.ai_analyzer = OpenAIChartAnalyzer(model=self.openai_model)

        # State
        self.running = True
        self.analysis_count = 0

        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        print("✅ Chart Analysis Bot initialized!\n")
        print("=" * 60)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n\n⚠️ Received shutdown signal ({signum})")
        print("🛑 Stopping Chart Analysis Bot...")
        self.running = False

    def fetch_chart_data(self, timeframe: str = '15m', limit: int = 100) -> Optional[list]:
        """
        Fetch chart data from Binance

        Args:
            timeframe: Chart timeframe (15m recommended for analysis)
            limit: Number of candles

        Returns:
            Klines data or None if error
        """
        try:
            klines = self.binance.get_klines(
                symbol=self.trading_pair,
                interval=timeframe,
                limit=limit
            )
            return klines
        except Exception as e:
            print(f"❌ Error fetching chart data: {e}")
            return None

    def generate_and_analyze(self, timeframe: str = '15m') -> Optional[Dict[str, Any]]:
        """
        Generate chart and analyze with AI

        Args:
            timeframe: Chart timeframe

        Returns:
            Analysis results dict or None
        """
        try:
            print(f"\n{'=' * 60}")
            print(f"📊 Chart Analysis Cycle #{self.analysis_count + 1}")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 60}\n")

            # 1. Fetch market data
            print(f"📈 Fetching market data for {self.trading_pair}...")
            klines = self.fetch_chart_data(timeframe=timeframe, limit=100)

            if not klines:
                print("❌ Failed to fetch market data")
                return None

            print(f"✅ Fetched {len(klines)} candles")

            # 2. Prepare DataFrame
            print("\n📊 Preparing chart...")
            df = self.chart_generator.prepare_dataframe(klines)

            # 3. Generate comprehensive chart
            print("🎨 Generating chart with all indicators...")
            chart_path = self.chart_generator.generate_chart_with_all_indicators(
                df=df,
                symbol=self.trading_pair,
                timeframe=timeframe
            )

            # 4. Analyze with AI
            print("\n🤖 Analyzing chart with OpenAI...")
            analysis = self.ai_analyzer.analyze_chart(
                image_path=chart_path,
                symbol=self.trading_pair,
                timeframe=timeframe
            )

            if not analysis:
                print("❌ AI analysis failed")
                return None

            # 5. Store in database
            print("\n💾 Saving analysis to database...")
            self.save_analysis_to_db(
                timeframe=timeframe,
                chart_path=chart_path,
                analysis=analysis
            )

            # 6. Print summary
            self._print_analysis_summary(analysis)

            self.analysis_count += 1
            return analysis

        except Exception as e:
            print(f"❌ Error in generate_and_analyze: {e}")
            return None

    def save_analysis_to_db(
        self,
        timeframe: str,
        chart_path: str,
        analysis: Dict[str, Any]
    ):
        """
        Save chart analysis to database

        Args:
            timeframe: Chart timeframe
            chart_path: Path to saved chart image
            analysis: Analysis results from AI
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Extract key fields
            recommendation = analysis.get('recommendation', 'HOLD')
            confidence = analysis.get('confidence', 'low')
            trend = analysis.get('trend', 'neutral')
            trend_strength = analysis.get('trend_strength', 'weak')

            # Convert arrays to JSON strings
            key_observations = json.dumps(analysis.get('key_observations', []))
            risk_factors = json.dumps(analysis.get('risk_factors', []))
            support_levels = json.dumps(analysis.get('support_levels', []))
            resistance_levels = json.dumps(analysis.get('resistance_levels', []))

            # Full AI analysis as JSON
            ai_analysis = json.dumps(analysis)

            # Insert into database
            cursor.execute('''
                INSERT INTO chart_analyses (
                    trading_pair, timeframe, recommendation, confidence,
                    key_observations, risk_factors, ai_analysis,
                    support_levels, resistance_levels, chart_image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.trading_pair,
                timeframe,
                recommendation,
                confidence,
                key_observations,
                risk_factors,
                ai_analysis,
                support_levels,
                resistance_levels,
                chart_path
            ))

            conn.commit()
            print("✅ Analysis saved to database")

        except Exception as e:
            print(f"❌ Error saving to database: {e}")

    def _print_analysis_summary(self, analysis: Dict[str, Any]):
        """Print formatted analysis summary"""
        print("\n" + "=" * 60)
        print("📋 ANALYSIS SUMMARY")
        print("=" * 60)

        # Main recommendation
        rec = analysis.get('recommendation', 'HOLD')
        conf = analysis.get('confidence', 'low')
        score = analysis.get('overall_score', 0)

        rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
        print(f"{rec_emoji} Recommendation: {rec} (Confidence: {conf.upper()})")
        print(f"⭐ Overall Score: {score}/10")

        # Trend
        trend = analysis.get('trend', 'neutral')
        trend_strength = analysis.get('trend_strength', 'weak')
        trend_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➡️", "sideways": "↔️"}.get(trend, "❓")
        print(f"{trend_emoji} Trend: {trend.upper()} ({trend_strength})")

        # Technical signals
        if 'technical_signals' in analysis:
            tech = analysis['technical_signals']
            print(f"\n🔧 Technical Signals:")
            print(f"   EMA Alignment: {tech.get('ema_alignment', 'N/A')}")
            print(f"   RSI: {tech.get('rsi_condition', 'N/A')}")
            print(f"   MACD: {tech.get('macd_signal', 'N/A')}")
            print(f"   Bollinger: {tech.get('bollinger_position', 'N/A')}")
            print(f"   Volume: {tech.get('volume_trend', 'N/A')}")

        # Support/Resistance
        support = analysis.get('support_levels', [])
        resistance = analysis.get('resistance_levels', [])
        if support:
            print(f"\n🟢 Support: {', '.join([f'${x:,.2f}' for x in support])}")
        if resistance:
            print(f"🔴 Resistance: {', '.join([f'${x:,.2f}' for x in resistance])}")

        # Key observations
        observations = analysis.get('key_observations', [])
        if observations:
            print(f"\n💡 Key Observations:")
            for i, obs in enumerate(observations[:3], 1):
                print(f"   {i}. {obs}")

        # Risks
        risks = analysis.get('risk_factors', [])
        if risks:
            print(f"\n⚠️ Risk Factors:")
            for i, risk in enumerate(risks[:2], 1):
                print(f"   {i}. {risk}")

        # Entry/Exit strategy
        entry = analysis.get('entry_strategy', '')
        exit_strat = analysis.get('exit_strategy', '')
        if entry:
            print(f"\n📥 Entry: {entry}")
        if exit_strat:
            print(f"📤 Exit: {exit_strat}")

        print("=" * 60)

    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Get latest analysis from database

        Returns:
            Latest analysis dict or None
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT ai_analysis FROM chart_analyses
                WHERE trading_pair = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (self.trading_pair,))

            row = cursor.fetchone()
            if row and row['ai_analysis']:
                return json.loads(row['ai_analysis'])

            return None

        except Exception as e:
            print(f"❌ Error getting latest analysis: {e}")
            return None

    def run(self):
        """Main bot loop"""
        print(f"\n{'=' * 60}")
        print("🤖 CHART ANALYSIS BOT IS NOW RUNNING")
        print(f"{'=' * 60}\n")
        print(f"⏱️ Analysis interval: {self.analysis_interval // 60} minutes")
        print("🛑 Press Ctrl+C to stop\n")

        while self.running:
            try:
                # Run analysis
                self.generate_and_analyze(timeframe='15m')

                # Wait for next cycle
                if self.running:
                    next_run = datetime.now().timestamp() + self.analysis_interval
                    next_run_time = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
                    print(f"\n⏳ Next analysis at {next_run_time} ({self.analysis_interval // 60} minutes)...")
                    print(f"{'=' * 60}\n")

                    time.sleep(self.analysis_interval)

            except KeyboardInterrupt:
                print("\n\n⚠️ Keyboard interrupt received")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("⏳ Retrying in 5 minutes...\n")
                time.sleep(300)

        # Cleanup
        print(f"\n{'=' * 60}")
        print("🛑 CHART ANALYSIS BOT SHUTDOWN")
        print(f"{'=' * 60}")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total analyses: {self.analysis_count}")
        print("\n✅ Shutdown complete")
        self.db.close_connection()


def main():
    """Entry point for chart analysis bot"""
    try:
        bot = ChartAnalysisBot()
        bot.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("🛑 Bot terminated")


if __name__ == "__main__":
    main()
