"""
RL Model Retraining System
Retrain the Q-learning model based on historical trading data
"""

import os
import sys
import logging
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

from database import TradingDatabase
from q_learning_model import QLearningTrader

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rl_retraining.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class RLRetrainer:
    """Handles RL model retraining"""

    def __init__(
        self,
        min_signals: int = 50,
        optimal_signals: int = 2000,
        episodes: int = 150,
        backup_interval: int = 50
    ):
        """
        Initialize retrainer

        Args:
            min_signals: Minimum signals required for training
            optimal_signals: Optimal number of signals for best results
            episodes: Number of training episodes
            backup_interval: Save backup every N episodes
        """
        self.min_signals = min_signals
        self.optimal_signals = optimal_signals
        self.episodes = episodes
        self.backup_interval = backup_interval

        # Initialize database
        db_path = os.getenv('DATABASE_PATH', 'trading_bot.db')
        self.db = TradingDatabase(db_path)
        self.db.connect()

        # Initialize RL model
        self.model = QLearningTrader()

        # Training statistics
        self.training_stats = {
            'best_win_rate': 0,
            'best_avg_return': 0,
            'episode_rewards': [],
            'episode_win_rates': [],
            'episode_trade_counts': []
        }

    def backup_current_model(self):
        """Backup current model before retraining"""
        if os.path.exists('rl_trading_model.pkl'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'rl_trading_model_backup_{timestamp}.pkl'
            shutil.copy('rl_trading_model.pkl', backup_path)
            logging.info(f"✅ Current model backed up to {backup_path}")

            # Clean up old backups (keep last 10)
            self.cleanup_old_backups()
        else:
            logging.info("ℹ️ No existing model to backup")

    def cleanup_old_backups(self, keep_last: int = 10):
        """Remove old backup files"""
        backups = [f for f in os.listdir('.') if f.startswith('rl_trading_model_backup_')]
        backups.sort(reverse=True)

        for old_backup in backups[keep_last:]:
            try:
                os.remove(old_backup)
                logging.info(f"🗑️ Removed old backup: {old_backup}")
            except Exception as e:
                logging.error(f"❌ Error removing backup {old_backup}: {e}")

    def collect_training_data(self) -> List[Dict[str, Any]]:
        """
        Collect historical signals and trades for training

        Returns:
            List of training examples
        """
        logging.info("📊 Collecting training data from database...")

        # Get signals from last 30 days
        cutoff_date = datetime.now() - timedelta(days=30)

        # Query signals
        query = """
            SELECT * FROM signals
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """
        self.db.cursor.execute(query, (cutoff_date,))
        columns = [description[0] for description in self.db.cursor.description]
        signals = [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

        logging.info(f"📈 Collected {len(signals)} signals")

        # Get trades
        query = """
            SELECT * FROM trades
            WHERE timestamp >= ? AND status = 'CLOSED'
            ORDER BY timestamp ASC
        """
        self.db.cursor.execute(query, (cutoff_date,))
        columns = [description[0] for description in self.db.cursor.description]
        trades = [dict(zip(columns, row)) for row in self.db.cursor.fetchall()]

        logging.info(f"💼 Collected {len(trades)} closed trades")

        # Categorize trade outcomes
        training_data = []
        for trade in trades:
            pnl_pct = trade.get('pnl_percentage', 0) or 0

            # Categorize outcome
            if pnl_pct > 0.02:
                outcome = 'good_profit'
                reward = 20.0
            elif pnl_pct > 0:
                outcome = 'small_profit'
                reward = 10.0
            elif pnl_pct > -0.02:
                outcome = 'small_loss'
                reward = -10.0
            else:
                outcome = 'bad_loss'
                reward = -20.0

            training_data.append({
                'trade': trade,
                'outcome': outcome,
                'reward': reward
            })

        logging.info(f"✅ Prepared {len(training_data)} training examples")
        return training_data

    def train_episode(self, training_data: List[Dict[str, Any]], episode: int) -> Dict[str, float]:
        """
        Train one episode

        Args:
            training_data: List of training examples
            episode: Episode number

        Returns:
            Episode statistics
        """
        total_reward = 0
        wins = 0
        losses = 0

        # Replay training data
        for example in training_data:
            trade = example['trade']
            reward = example['reward']

            # Create state from trade data
            state_data = {
                'signal': 'BUY' if trade['side'] == 'BUY' else 'SELL',
                'signal_strength': 3,  # Default
                'rsi': 50,  # Would come from signal data
                'macd_histogram': 0,
                'price': trade['entry_price'],
                'vwap': trade['entry_price'],
                'market_regime': 'neutral',
                'fear_greed_index': 50,
                'btc_correlation': 0.5,
                'has_position': False,
                'position_pnl': 0
            }

            # Get action
            action_idx, action, _ = self.model.choose_action(state_data, explore=True)

            # Create next state (after trade)
            next_state_data = state_data.copy()
            next_state_data['has_position'] = True
            next_state_data['position_pnl'] = trade.get('pnl_percentage', 0) or 0

            # Add experience and update
            self.model.add_experience(state_data, action_idx, reward, next_state_data)

            # Update Q-values
            state = self.model.discretize_state(state_data)
            next_state = self.model.discretize_state(next_state_data)
            self.model.update_q_value(state, action_idx, reward, next_state)

            total_reward += reward
            if reward > 0:
                wins += 1
            else:
                losses += 1

        # Replay experiences
        if len(training_data) > 32:
            self.model.replay_experience(batch_size=min(64, len(training_data)))

        # Calculate stats
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_return = total_reward / total_trades if total_trades > 0 else 0

        return {
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_reward': total_reward,
            'trades': total_trades
        }

    def run_retraining(self):
        """Execute full retraining workflow"""
        logging.info("🚀 Starting RL Model Retraining...")
        logging.info("=" * 60)

        # Step 1: Pre-flight checks
        logging.info("🔍 Running pre-flight checks...")

        training_data = self.collect_training_data()

        if len(training_data) < self.min_signals:
            logging.error(f"❌ Insufficient training data: {len(training_data)} (minimum: {self.min_signals})")
            logging.error("   Let the bot run for at least 2-3 hours to collect more data")
            return False

        if len(training_data) < self.optimal_signals:
            logging.warning(f"⚠️ Suboptimal training data: {len(training_data)} (optimal: {self.optimal_signals})")
            logging.warning("   For best results, let bot run for 24-48 hours")

        # Step 2: Backup current model
        logging.info("\n💾 Backing up current model...")
        self.backup_current_model()

        # Step 3: Load existing model if available
        if os.path.exists('rl_trading_model.pkl'):
            logging.info("\n📥 Loading existing model...")
            self.model.load_model('rl_trading_model.pkl')
        else:
            logging.info("\n🆕 Starting with fresh model...")

        # Step 4: Training loop
        logging.info(f"\n🎯 Starting training: {self.episodes} episodes")
        logging.info("=" * 60)

        start_time = datetime.now()

        for episode in range(1, self.episodes + 1):
            stats = self.train_episode(training_data, episode)

            # Update best stats
            if stats['win_rate'] > self.training_stats['best_win_rate']:
                self.training_stats['best_win_rate'] = stats['win_rate']

            if stats['avg_return'] > self.training_stats['best_avg_return']:
                self.training_stats['best_avg_return'] = stats['avg_return']

            # Store episode stats
            self.training_stats['episode_rewards'].append(stats['total_reward'])
            self.training_stats['episode_win_rates'].append(stats['win_rate'])
            self.training_stats['episode_trade_counts'].append(stats['trades'])

            # Log progress
            if episode % 10 == 0:
                logging.info(
                    f"Episode {episode}/{self.episodes} | "
                    f"Win Rate: {stats['win_rate']:.2f}% | "
                    f"Avg Return: {stats['avg_return']:.2f} | "
                    f"Epsilon: {self.model.epsilon:.4f}"
                )

            # Periodic backup
            if episode % self.backup_interval == 0:
                backup_path = f'rl_trading_model_episode_{episode}.pkl'
                self.model.save_model(backup_path)
                logging.info(f"💾 Episode backup saved: {backup_path}")

        # Step 5: Save final model
        logging.info("\n💾 Saving retrained model...")
        self.model.save_model('rl_trading_model.pkl')

        # Step 6: Generate report
        duration = datetime.now() - start_time
        logging.info("\n" + "=" * 60)
        logging.info("🎉 RETRAINING COMPLETED!")
        logging.info("=" * 60)

        self.print_final_report(training_data, duration)

        return True

    def print_final_report(self, training_data: List[Dict[str, Any]], duration):
        """Print final training report"""
        # Calculate statistics
        recent_episodes = 50
        recent_rewards = self.training_stats['episode_rewards'][-recent_episodes:]
        recent_win_rates = self.training_stats['episode_win_rates'][-recent_episodes:]
        recent_trades = self.training_stats['episode_trade_counts'][-recent_episodes:]

        avg_recent_reward = sum(recent_rewards) / len(recent_rewards) if recent_rewards else 0
        avg_recent_win_rate = sum(recent_win_rates) / len(recent_win_rates) if recent_win_rates else 0
        avg_recent_trades = sum(recent_trades) / len(recent_trades) if recent_trades else 0

        # Early vs recent comparison
        early_episodes = 50
        early_rewards = self.training_stats['episode_rewards'][:early_episodes]
        early_win_rates = self.training_stats['episode_win_rates'][:early_episodes]

        avg_early_reward = sum(early_rewards) / len(early_rewards) if early_rewards else 0
        avg_early_win_rate = sum(early_win_rates) / len(early_win_rates) if early_win_rates else 0

        improvement_reward = ((avg_recent_reward - avg_early_reward) / abs(avg_early_reward) * 100) if avg_early_reward != 0 else 0
        improvement_win_rate = avg_recent_win_rate - avg_early_win_rate

        logging.info(f"""
📊 TRAINING SUMMARY:
   Total Episodes: {self.episodes}
   Training Duration: {duration}
   Training Examples: {len(training_data)}

🏆 BEST PERFORMANCE:
   Best Win Rate: {self.training_stats['best_win_rate']:.2f}%
   Best Avg Return: {self.training_stats['best_avg_return']:.2f}

📈 RECENT PERFORMANCE (Last {recent_episodes} episodes):
   Average Win Rate: {avg_recent_win_rate:.2f}%
   Average Return: {avg_recent_reward:.2f}
   Average Trades/Episode: {avg_recent_trades:.1f}

📊 LEARNING PROGRESS:
   Early Win Rate: {avg_early_win_rate:.2f}%
   Recent Win Rate: {avg_recent_win_rate:.2f}%
   Improvement: {improvement_win_rate:+.2f}%

🧠 MODEL STATISTICS:
   Total States Learned: {len(self.model.q_table)}
   Total Episodes: {self.model.total_episodes + self.episodes}
   Final Epsilon: {self.model.epsilon:.4f}

💡 RECOMMENDATIONS:
   - Test the retrained model on testnet before live trading
   - Monitor performance for first 24 hours
   - Consider retraining weekly for continuous improvement
   - If performance is worse, restore from backup
        """)

        logging.info("=" * 60)


def main():
    """Main execution function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         RL MODEL RETRAINING SYSTEM                       ║
║         AI-Driven Cryptocurrency Trading Bot             ║
╚══════════════════════════════════════════════════════════╝
    """)

    retrainer = RLRetrainer(
        min_signals=50,
        optimal_signals=2000,
        episodes=150,
        backup_interval=50
    )

    success = retrainer.run_retraining()

    if success:
        print("\n✅ Retraining completed successfully!")
        print("📝 Check rl_retraining.log for detailed report")
        print("\n⚠️ NEXT STEPS:")
        print("   1. Test on testnet first")
        print("   2. Monitor performance closely")
        print("   3. Restore from backup if needed:")
        print("      cp rl_trading_model_backup_*.pkl rl_trading_model.pkl")
    else:
        print("\n❌ Retraining failed. Check logs for details.")

    retrainer.db.close()


if __name__ == "__main__":
    main()
