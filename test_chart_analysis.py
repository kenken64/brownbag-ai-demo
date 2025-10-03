#!/usr/bin/env python3
"""
Test Chart Analysis System
Validates chart generation, OpenAI analysis, and chart analysis bot components
"""

import os
import sys

print("=" * 60)
print("📋 CHART ANALYSIS SYSTEM TEST")
print("=" * 60)
print()

# Check if virtual environment is activated
print("1. Checking Python environment...")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("   ✅ Virtual environment detected")
else:
    print("   ⚠️  Virtual environment not detected")
    print("      Recommended: source venv/bin/activate")
print()

# Check for required dependencies
print("2. Checking dependencies...")
required_modules = [
    'pandas', 'mplfinance', 'matplotlib', 'dotenv',
    'openai', 'binance'
]

missing_modules = []
for module in required_modules:
    try:
        __import__(module)
        print(f"   ✅ {module}")
    except ImportError:
        print(f"   ❌ {module} - NOT INSTALLED")
        missing_modules.append(module)

if missing_modules:
    print()
    print("   ⚠️  Missing dependencies detected!")
    print("   Run: pip install -r requirements.txt")
    print()
else:
    print()
    print("   ✅ All dependencies installed!")
    print()

# Check for .env configuration
print("3. Checking .env configuration...")
if os.path.exists('.env'):
    print("   ✅ .env file exists")

    from dotenv import load_dotenv
    load_dotenv()

    # Check critical keys
    required_keys = [
        'BINANCE_API_KEY',
        'BINANCE_API_SECRET',
        'OPENAI_API_KEY',
        'TRADING_PAIR',
        'USE_TESTNET'
    ]

    missing_keys = []
    for key in required_keys:
        value = os.getenv(key)
        if value:
            # Mask sensitive values
            if 'KEY' in key or 'SECRET' in key:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"   ✅ {key} = {display_value}")
        else:
            print(f"   ❌ {key} - NOT SET")
            missing_keys.append(key)

    if missing_keys:
        print()
        print("   ⚠️  Missing configuration keys!")
        print("   Edit .env and add required API keys")

else:
    print("   ❌ .env file not found")
    print("   Run: cp .env.example .env")
    print("   Then edit .env with your API keys")

print()

# Check if components are importable
if not missing_modules:
    print("4. Checking component imports...")
    try:
        from src.chart_generator import ChartGenerator
        print("   ✅ ChartGenerator imported")
    except Exception as e:
        print(f"   ❌ ChartGenerator import failed: {e}")

    try:
        from src.openai_analyzer import OpenAIChartAnalyzer
        print("   ✅ OpenAIChartAnalyzer imported")
    except Exception as e:
        print(f"   ❌ OpenAIChartAnalyzer import failed: {e}")

    try:
        from src.chart_analysis_bot import ChartAnalysisBot
        print("   ✅ ChartAnalysisBot imported")
    except Exception as e:
        print(f"   ❌ ChartAnalysisBot import failed: {e}")

    print()

    # If all components imported, run actual tests
    if os.path.exists('.env') and not missing_keys:
        print("5. Running component tests...")
        print()

        try:
            # Test 1: Chart Generator
            print("   TEST 1: Chart Generator")
            print("   " + "-" * 56)
            from src.binance_client import BinanceFuturesClient
            from src.chart_generator import ChartGenerator

            testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
            symbol = os.getenv('TRADING_PAIR', 'BTCUSDT')

            print(f"   Fetching {symbol} data (testnet: {testnet})...")
            binance = BinanceFuturesClient(testnet=testnet)
            klines = binance.get_klines(symbol=symbol, interval='15m', limit=100)

            if klines:
                print(f"   ✅ Fetched {len(klines)} candles")

                generator = ChartGenerator(output_dir="charts")
                df = generator.prepare_dataframe(klines)

                print(f"   📊 Generating chart...")
                chart_path = generator.generate_chart_with_all_indicators(
                    df=df,
                    symbol=symbol,
                    timeframe='15m'
                )

                if os.path.exists(chart_path):
                    print(f"   ✅ Chart generated: {chart_path}")

                    # Test 2: OpenAI Analyzer
                    print()
                    print("   TEST 2: OpenAI Chart Analyzer")
                    print("   " + "-" * 56)
                    from src.openai_analyzer import OpenAIChartAnalyzer

                    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
                    analyzer = OpenAIChartAnalyzer(model=model)

                    print(f"   Analyzing chart with {model}...")
                    analysis = analyzer.analyze_chart(
                        image_path=chart_path,
                        symbol=symbol,
                        timeframe='15m'
                    )

                    if analysis:
                        print(f"   ✅ Analysis completed")
                        print(f"      Recommendation: {analysis.get('recommendation', 'N/A')}")
                        print(f"      Confidence: {analysis.get('confidence', 'N/A')}")
                        print(f"      Trend: {analysis.get('trend', 'N/A')}")
                        print(f"      Score: {analysis.get('overall_score', 'N/A')}/10")

                        # Test 3: Chart Analysis Bot (single cycle)
                        print()
                        print("   TEST 3: Chart Analysis Bot (single cycle)")
                        print("   " + "-" * 56)
                        from src.chart_analysis_bot import ChartAnalysisBot

                        bot = ChartAnalysisBot()
                        result = bot.generate_and_analyze(timeframe='15m')

                        if result:
                            print(f"   ✅ Chart Analysis Bot cycle completed")
                            print(f"      Analysis saved to database")

                            # Check latest analysis from DB
                            latest = bot.get_latest_analysis()
                            if latest:
                                print(f"      Latest DB entry: {latest.get('recommendation', 'N/A')}")
                        else:
                            print(f"   ❌ Chart Analysis Bot cycle failed")
                    else:
                        print(f"   ❌ OpenAI analysis failed")
                else:
                    print(f"   ❌ Chart generation failed")
            else:
                print(f"   ❌ Failed to fetch market data")

        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

print()
print("=" * 60)
print("📋 TEST SUMMARY")
print("=" * 60)

if missing_modules:
    print("❌ CANNOT RUN TESTS - Missing dependencies")
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure .env: cp .env.example .env")
    print("3. Add API keys to .env")
    print("4. Run tests again: python3 test_chart_analysis.py")
elif not os.path.exists('.env'):
    print("❌ CANNOT RUN TESTS - Missing .env file")
    print()
    print("Next steps:")
    print("1. Configure .env: cp .env.example .env")
    print("2. Add API keys to .env")
    print("3. Run tests again: python3 test_chart_analysis.py")
else:
    print("✅ Test validation complete!")
    print()
    print("To run the Chart Analysis Bot continuously:")
    print("  python3 -m src.chart_analysis_bot")
    print()
    print("The bot will:")
    print("  • Generate charts every 15 minutes")
    print("  • Analyze with OpenAI GPT-4o Vision")
    print("  • Store results in database")
    print("  • Provide trading recommendations")

print()
print("=" * 60)
