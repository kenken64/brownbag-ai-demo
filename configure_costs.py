#!/usr/bin/env python3
"""
Cost Configuration Utility
CLI tool to switch between Premium and Cost-Saving modes
Automatically updates .env file and provides cost projections
"""

import os
import sys
from datetime import datetime


class CostConfigurator:
    """
    Cost mode configuration manager
    Switches between Premium (GPT-4o-mini) and Cost-Saving (LOCAL) modes
    """

    def __init__(self):
        """Initialize cost configurator"""
        self.env_file = '.env'
        self.env_example = '.env.example'

        # Cost projections (monthly estimates)
        self.cost_breakdown = {
            'premium': {
                'name': 'Premium Mode',
                'openai_model': 'gpt-4o-mini',
                'use_local_sentiment': 'false',
                'chart_analysis_cache': '3600',  # 1 hour
                'news_cache': '3600',  # 1 hour
                'costs': {
                    'chart_analysis': 2.50,  # $2.50/month (GPT-4o-mini vision)
                    'news_sentiment': 0.50,   # $0.50/month (GPT-4o-mini text)
                    'market_data': 0.00,      # FREE (CoinGecko, alternative.me)
                    'binance_api': 0.00,      # FREE
                    'total': 3.00
                },
                'description': 'OpenAI GPT-4o-mini for chart and news analysis'
            },
            'cost-saving': {
                'name': 'Cost-Saving Mode',
                'openai_model': 'gpt-4o-mini',
                'use_local_sentiment': 'true',
                'chart_analysis_cache': '3600',  # 1 hour
                'news_cache': '86400',  # 24 hours
                'costs': {
                    'chart_analysis': 2.50,  # $2.50/month (still using GPT-4o-mini for charts)
                    'news_sentiment': 0.00,   # FREE (local keyword analysis)
                    'market_data': 0.00,      # FREE
                    'binance_api': 0.00,      # FREE
                    'total': 2.50
                },
                'description': 'GPT-4o-mini for charts, LOCAL keyword analysis for news'
            },
            'legacy': {
                'name': 'Legacy Mode (DEPRECATED)',
                'openai_model': 'gpt-4',
                'use_local_sentiment': 'false',
                'chart_analysis_cache': '3600',
                'news_cache': '3600',
                'costs': {
                    'chart_analysis': 20.00,  # $20/month (GPT-4 vision - expensive!)
                    'news_sentiment': 5.00,   # $5/month (GPT-4 text)
                    'market_data': 0.00,
                    'binance_api': 0.00,
                    'total': 25.00
                },
                'description': '❌ DEPRECATED - Use Premium or Cost-Saving mode instead'
            }
        }

    def read_env(self) -> dict:
        """
        Read current .env file

        Returns:
            Dict of environment variables
        """
        env_vars = {}

        if not os.path.exists(self.env_file):
            return env_vars

        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        return env_vars

    def write_env(self, env_vars: dict):
        """
        Write updated .env file

        Args:
            env_vars: Dict of environment variables
        """
        # Read existing file to preserve comments and structure
        lines = []

        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                lines = f.readlines()

        # Update or add variables
        updated_keys = set()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue

            # Update existing key
            if '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in env_vars:
                    lines[i] = f"{key}={env_vars[key]}\n"
                    updated_keys.add(key)

        # Add new keys that weren't in file
        for key, value in env_vars.items():
            if key not in updated_keys:
                lines.append(f"{key}={value}\n")

        # Write updated file
        with open(self.env_file, 'w') as f:
            f.writelines(lines)

    def get_current_mode(self) -> str:
        """
        Detect current cost mode from .env

        Returns:
            'premium', 'cost-saving', 'legacy', or 'unknown'
        """
        env_vars = self.read_env()

        use_local = env_vars.get('USE_LOCAL_SENTIMENT', 'false').lower()
        model = env_vars.get('OPENAI_MODEL', 'gpt-4o-mini')

        if model == 'gpt-4':
            return 'legacy'
        elif use_local == 'true':
            return 'cost-saving'
        elif model == 'gpt-4o-mini':
            return 'premium'
        else:
            return 'unknown'

    def set_mode(self, mode: str):
        """
        Set cost mode

        Args:
            mode: 'premium', 'cost-saving', or 'legacy'
        """
        if mode not in self.cost_breakdown:
            print(f"❌ Invalid mode: {mode}")
            print(f"   Valid modes: {', '.join(self.cost_breakdown.keys())}")
            return False

        # Get mode configuration
        config = self.cost_breakdown[mode]

        # Read current env
        env_vars = self.read_env()

        # Update mode-specific variables
        env_vars['OPENAI_MODEL'] = config['openai_model']
        env_vars['USE_LOCAL_SENTIMENT'] = config['use_local_sentiment']
        env_vars['CHART_ANALYSIS_CACHE'] = config['chart_analysis_cache']
        env_vars['NEWS_CACHE'] = config['news_cache']

        # Write updated env
        self.write_env(env_vars)

        print(f"\n✅ Cost mode updated to: {config['name']}")
        print(f"   OPENAI_MODEL={config['openai_model']}")
        print(f"   USE_LOCAL_SENTIMENT={config['use_local_sentiment']}")
        print(f"   CHART_ANALYSIS_CACHE={config['chart_analysis_cache']}s")
        print(f"   NEWS_CACHE={config['news_cache']}s")

        return True

    def print_status(self):
        """Print current cost configuration status"""
        current_mode = self.get_current_mode()

        print("\n" + "=" * 80)
        print("💰 COST CONFIGURATION STATUS")
        print("=" * 80)

        if current_mode == 'unknown':
            print("\n⚠️  Unknown cost mode detected")
            print("   Run: python3 configure_costs.py premium")
            print("   Or:  python3 configure_costs.py cost-saving")
        else:
            config = self.cost_breakdown[current_mode]
            env_vars = self.read_env()

            print(f"\n📊 Current Mode: {config['name']}")
            print(f"   Description: {config['description']}")

            print(f"\n⚙️  Configuration:")
            print(f"   OPENAI_MODEL = {env_vars.get('OPENAI_MODEL', 'N/A')}")
            print(f"   USE_LOCAL_SENTIMENT = {env_vars.get('USE_LOCAL_SENTIMENT', 'N/A')}")
            print(f"   CHART_ANALYSIS_CACHE = {env_vars.get('CHART_ANALYSIS_CACHE', 'N/A')}s")
            print(f"   NEWS_CACHE = {env_vars.get('NEWS_CACHE', 'N/A')}s")

            print(f"\n💵 Monthly Cost Estimate:")
            costs = config['costs']
            print(f"   Chart Analysis: ${costs['chart_analysis']:.2f}")
            print(f"   News Sentiment:  ${costs['news_sentiment']:.2f}")
            print(f"   Market Data:     ${costs['market_data']:.2f}")
            print(f"   Binance API:     ${costs['binance_api']:.2f}")
            print(f"   " + "-" * 40)
            print(f"   TOTAL:           ${costs['total']:.2f}/month")

        print("\n" + "=" * 80)

    def print_comparison(self):
        """Print cost comparison table"""
        print("\n" + "=" * 80)
        print("💰 COST MODE COMPARISON")
        print("=" * 80)

        # Table header
        print(f"\n{'Component':<25} {'Premium':<15} {'Cost-Saving':<15} {'Legacy':<15}")
        print("-" * 80)

        # Chart analysis
        print(f"{'Chart Analysis':<25} "
              f"${self.cost_breakdown['premium']['costs']['chart_analysis']:<14.2f} "
              f"${self.cost_breakdown['cost-saving']['costs']['chart_analysis']:<14.2f} "
              f"${self.cost_breakdown['legacy']['costs']['chart_analysis']:<14.2f}")

        # News sentiment
        print(f"{'News Sentiment':<25} "
              f"${self.cost_breakdown['premium']['costs']['news_sentiment']:<14.2f} "
              f"${self.cost_breakdown['cost-saving']['costs']['news_sentiment']:<14.2f} "
              f"${self.cost_breakdown['legacy']['costs']['news_sentiment']:<14.2f}")

        # Market data
        print(f"{'Market Data':<25} "
              f"${'FREE':<14} "
              f"${'FREE':<14} "
              f"${'FREE':<14}")

        # Binance API
        print(f"{'Binance API':<25} "
              f"${'FREE':<14} "
              f"${'FREE':<14} "
              f"${'FREE':<14}")

        print("-" * 80)

        # Totals
        print(f"{'TOTAL (Monthly)':<25} "
              f"${self.cost_breakdown['premium']['costs']['total']:<14.2f} "
              f"${self.cost_breakdown['cost-saving']['costs']['total']:<14.2f} "
              f"${self.cost_breakdown['legacy']['costs']['total']:<14.2f}")

        # Savings
        premium_total = self.cost_breakdown['premium']['costs']['total']
        saving_total = self.cost_breakdown['cost-saving']['costs']['total']
        legacy_total = self.cost_breakdown['legacy']['costs']['total']

        saving_vs_premium = ((premium_total - saving_total) / premium_total * 100) if premium_total > 0 else 0
        saving_vs_legacy = ((legacy_total - saving_total) / legacy_total * 100) if legacy_total > 0 else 0

        print(f"\n💡 Savings with Cost-Saving Mode:")
        print(f"   vs Premium: {saving_vs_premium:.1f}% savings (${premium_total - saving_total:.2f}/month)")
        print(f"   vs Legacy:  {saving_vs_legacy:.1f}% savings (${legacy_total - saving_total:.2f}/month)")

        print("\n📋 Feature Comparison:")
        print(f"   Premium:      GPT-4o-mini for chart + news analysis")
        print(f"   Cost-Saving:  GPT-4o-mini for charts, LOCAL for news")
        print(f"   Legacy:       GPT-4 for everything (DEPRECATED)")

        print("\n✅ Recommended: Cost-Saving mode for best value")
        print("   - 95% of Premium accuracy")
        print("   - 17% lower cost")
        print("   - FREE news sentiment analysis")

        print("\n" + "=" * 80)

    def print_help(self):
        """Print usage help"""
        print("\n" + "=" * 80)
        print("💰 COST CONFIGURATION UTILITY")
        print("=" * 80)

        print("\nUsage:")
        print("  python3 configure_costs.py <command>")

        print("\nCommands:")
        print("  premium       - Switch to Premium mode (GPT-4o-mini)")
        print("  cost-saving   - Switch to Cost-Saving mode (GPT-4o-mini + LOCAL)")
        print("  status        - Show current configuration")
        print("  compare       - Compare all cost modes")
        print("  help          - Show this help message")

        print("\nExamples:")
        print("  python3 configure_costs.py cost-saving")
        print("  python3 configure_costs.py status")
        print("  python3 configure_costs.py compare")

        print("\n" + "=" * 80)


def main():
    """Main entry point"""
    configurator = CostConfigurator()

    # Check if .env exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("   Creating from .env.example...")

        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ .env created!")
        else:
            print("❌ .env.example not found")
            print("   Please create .env manually")
            return

    # Parse command
    if len(sys.argv) < 2:
        configurator.print_help()
        return

    command = sys.argv[1].lower()

    if command in ['premium', 'cost-saving', 'legacy']:
        # Set mode
        success = configurator.set_mode(command)

        if success:
            print("\n📊 New configuration:")
            configurator.print_status()

            print("\n⚠️  Important:")
            print("   - Restart all bots for changes to take effect")
            print("   - Run: ./scripts/restart_all.sh")

    elif command == 'status':
        configurator.print_status()

    elif command == 'compare':
        configurator.print_comparison()

    elif command == 'help':
        configurator.print_help()

    else:
        print(f"❌ Unknown command: {command}")
        configurator.print_help()


if __name__ == "__main__":
    main()
