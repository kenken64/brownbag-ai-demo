#!/usr/bin/env python3
"""
RL Model Retraining System
Retrain Q-Learning model using historical trading signals and outcomes
Implements episodic training with backups and analytics
"""

import os
import sys
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import TradingDatabase
from src.rl_model import QLearningAgent


class RLRetrainer:
    """
    RL Model Retraining System
    Collects historical data and retrains Q-Learning agent
    """

    def __init__(
        self,
        model_path: str = "models/rl_trading_model.pkl",
        backup_dir: str = "models",
        log_file: str = "logs/rl_retraining.log"
    ):
        """
        Initialize RL retrainer

        Args:
            model_path: Path to current model
            backup_dir: Directory for backups
            log_file: Log file path
        """
        self.model_path = model_path
        self.backup_dir = backup_dir
        self.log_file = log_file

        # Create directories
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Initialize components
        self.db = TradingDatabase()

        # Training configuration
        self.min_signals = 50
        self.optimal_signals = 2000
        self.num_episodes = 150
        self.backup_frequency = 50  # Backup every N episodes

        print("=" * 80)
        print("🧠 RL MODEL RETRAINING SYSTEM")
        print("=" * 80)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def log(self, message: str):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"

        print(log_line)

        with open(self.log_file, 'a') as f:
            f.write(log_line + '\n')

    def check_data_requirements(self) -> Tuple[bool, Dict]:
        """
        Check if sufficient data exists for retraining

        Returns:
            (is_sufficient, stats_dict)
        """
        self.log("📊 Checking data requirements...")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Count signals
        cursor.execute("SELECT COUNT(*) FROM signals")
        signal_count = cursor.fetchone()[0]

        # Count trades
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]

        # Get signal date range
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM signals")
        date_range = cursor.fetchone()

        stats = {
            'signal_count': signal_count,
            'trade_count': trade_count,
            'min_date': date_range[0] if date_range[0] else 'N/A',
            'max_date': date_range[1] if date_range[1] else 'N/A',
            'sufficient': signal_count >= self.min_signals
        }

        self.log(f"   Signals: {signal_count} (min: {self.min_signals}, optimal: {self.optimal_signals})")
        self.log(f"   Trades: {trade_count}")
        self.log(f"   Date range: {stats['min_date']} to {stats['max_date']}")

        if signal_count < self.min_signals:
            self.log(f"❌ Insufficient data! Need at least {self.min_signals} signals")
            self.log(f"   Run trading bot for ~{(self.min_signals - signal_count) * 60 // 60} hours to collect more data")
            return False, stats

        if signal_count < self.optimal_signals:
            self.log(f"⚠️  Suboptimal data! Recommended: {self.optimal_signals} signals")
            self.log(f"   Current data will work but model may not be well-trained")

        self.log("✅ Sufficient data available for retraining\n")
        return True, stats

    def backup_current_model(self) -> Optional[str]:
        """
        Create backup of current model

        Returns:
            Backup file path or None
        """
        if not os.path.exists(self.model_path):
            self.log("ℹ️  No existing model to backup")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(
            self.backup_dir,
            f"rl_trading_model_backup_{timestamp}.pkl"
        )

        shutil.copy2(self.model_path, backup_path)
        self.log(f"💾 Model backed up to: {backup_path}")

        # Cleanup old backups (keep last 10)
        self._cleanup_old_backups()

        return backup_path

    def _cleanup_old_backups(self):
        """Remove old backup files, keeping last 10"""
        import glob

        backups = glob.glob(os.path.join(self.backup_dir, "rl_trading_model_backup_*.pkl"))
        backups.sort(reverse=True)  # Most recent first

        if len(backups) > 10:
            for old_backup in backups[10:]:
                os.remove(old_backup)
                self.log(f"🗑️  Removed old backup: {os.path.basename(old_backup)}")

    def load_training_data(self) -> List[Dict]:
        """
        Load historical signals and trade outcomes

        Returns:
            List of training samples
        """
        self.log("📥 Loading training data from database...")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get signals with optional trade outcomes
        cursor.execute('''
            SELECT
                s.timestamp,
                s.price,
                s.rsi,
                s.macd,
                s.macd_signal,
                s.vwap,
                s.ema_9,
                s.ema_21,
                s.sma_50,
                s.bb_upper,
                s.bb_lower,
                s.signal_type,
                s.signal_strength,
                t.side,
                t.pnl,
                t.pnl_percentage
            FROM signals s
            LEFT JOIN trades t ON s.id = t.signal_id
            ORDER BY s.timestamp DESC
            LIMIT 5000
        ''')

        rows = cursor.fetchall()

        training_data = []
        for row in rows:
            sample = {
                'timestamp': row['timestamp'],
                'price': row['price'],
                'rsi': row['rsi'],
                'macd': row['macd'],
                'macd_signal': row['macd_signal'],
                'vwap': row['vwap'],
                'ema_9': row['ema_9'],
                'ema_21': row['ema_21'],
                'sma_50': row['sma_50'],
                'bb_upper': row['bb_upper'],
                'bb_lower': row['bb_lower'],
                'signal_type': row['signal_type'],
                'signal_strength': row['signal_strength'],
                'trade_side': row['side'],
                'pnl': row['pnl'],
                'pnl_percentage': row['pnl_percentage']
            }

            training_data.append(sample)

        self.log(f"✅ Loaded {len(training_data)} training samples\n")
        return training_data

    def calculate_reward(self, sample: Dict) -> float:
        """
        Calculate reward based on trade outcome

        Args:
            sample: Training sample with trade outcome

        Returns:
            Reward value
        """
        # If no trade was executed, reward = 0
        if sample['pnl'] is None:
            return 0.0

        pnl_pct = sample['pnl_percentage']

        # Reward structure based on PnL percentage
        if pnl_pct > 2.0:  # Good profit
            reward = 20.0
        elif pnl_pct > 0:  # Small profit
            reward = 10.0
        elif pnl_pct > -2.0:  # Small loss
            reward = -10.0
        else:  # Bad loss
            reward = -20.0

        # Scale by actual PnL percentage
        reward *= abs(pnl_pct) / 2.0

        return reward

    def prepare_state(self, sample: Dict) -> Dict:
        """
        Prepare state dict from training sample

        Args:
            sample: Training sample

        Returns:
            State dict for RL agent
        """
        return {
            'price': sample['price'],
            'rsi': sample['rsi'],
            'macd': sample['macd'],
            'macd_signal': sample['macd_signal'],
            'vwap': sample['vwap'],
            'ema_9': sample['ema_9'],
            'ema_21': sample['ema_21'],
            'sma_50': sample['sma_50'],
            'bb_upper': sample['bb_upper'],
            'bb_lower': sample['bb_lower'],
            'signal': sample['signal_type'],
            'signal_strength': sample['signal_strength']
        }

    def train_episode(
        self,
        agent: QLearningAgent,
        training_data: List[Dict],
        episode: int
    ) -> Dict:
        """
        Train one episode

        Args:
            agent: RL agent
            training_data: Training samples
            episode: Episode number

        Returns:
            Episode statistics
        """
        episode_trades = 0
        episode_rewards = 0.0
        episode_wins = 0

        for i, sample in enumerate(training_data):
            # Prepare current state
            state = self.prepare_state(sample)

            # Get signal action
            if sample['signal_type'] == 'BUY':
                signal_action = 0  # BUY
            elif sample['signal_type'] == 'SELL':
                signal_action = 1  # SELL
            else:
                signal_action = 2  # HOLD

            # Get RL action
            rl_action = agent.get_action(state)

            # Calculate reward if trade was executed
            reward = self.calculate_reward(sample)

            # Update Q-values
            if i < len(training_data) - 1:
                next_state = self.prepare_state(training_data[i + 1])
                agent.update_q_value(state, rl_action, reward, next_state, done=False)
            else:
                agent.update_q_value(state, rl_action, reward, state, done=True)

            # Track statistics
            if reward != 0:
                episode_trades += 1
                episode_rewards += reward
                if reward > 0:
                    episode_wins += 1

        # Calculate metrics
        win_rate = (episode_wins / episode_trades * 100) if episode_trades > 0 else 0
        avg_reward = episode_rewards / len(training_data) if training_data else 0

        return {
            'episode': episode,
            'trades': episode_trades,
            'rewards': episode_rewards,
            'wins': episode_wins,
            'win_rate': win_rate,
            'avg_reward': avg_reward
        }

    def retrain(self) -> bool:
        """
        Execute full retraining workflow

        Returns:
            True if successful
        """
        start_time = datetime.now()

        # 1. Check data requirements
        sufficient, stats = self.check_data_requirements()
        if not sufficient:
            return False

        # 2. Backup current model
        self.log("💾 Creating backup...")
        backup_path = self.backup_current_model()

        # 3. Load or create agent
        self.log("🧠 Loading RL agent...")
        agent = QLearningAgent(learning_rate=0.1, epsilon=0.1)

        if os.path.exists(self.model_path):
            agent.load_model(self.model_path)
            self.log(f"   Loaded existing model from {self.model_path}")
        else:
            self.log("   Creating new model")

        # 4. Load training data
        training_data = self.load_training_data()

        if len(training_data) < self.min_signals:
            self.log(f"❌ Insufficient training data: {len(training_data)}")
            return False

        # 5. Training loop
        self.log(f"🎓 Starting training: {self.num_episodes} episodes...")
        self.log("=" * 80)

        best_win_rate = 0
        best_episode = 0
        episode_stats = []

        for episode in range(1, self.num_episodes + 1):
            stats = self.train_episode(agent, training_data, episode)
            episode_stats.append(stats)

            # Track best
            if stats['win_rate'] > best_win_rate:
                best_win_rate = stats['win_rate']
                best_episode = episode

            # Print progress every 10 episodes
            if episode % 10 == 0:
                recent_stats = episode_stats[-10:]
                avg_win_rate = sum(s['win_rate'] for s in recent_stats) / len(recent_stats)
                avg_trades = sum(s['trades'] for s in recent_stats) / len(recent_stats)

                self.log(f"Episode {episode}/{self.num_episodes} | "
                        f"Win Rate: {avg_win_rate:.1f}% | "
                        f"Trades: {avg_trades:.0f} | "
                        f"Best: {best_win_rate:.1f}% (ep {best_episode})")

            # Episodic backup
            if episode % self.backup_frequency == 0:
                episode_backup = os.path.join(
                    self.backup_dir,
                    f"rl_trading_model_episode_{episode}.pkl"
                )
                agent.save_model(episode_backup)

        # 6. Save retrained model
        self.log("\n" + "=" * 80)
        self.log("💾 Saving retrained model...")
        agent.save_model(self.model_path)

        # 7. Print analytics
        self._print_analytics(episode_stats, start_time)

        self.log("\n✅ Retraining completed successfully!")
        return True

    def _print_analytics(self, episode_stats: List[Dict], start_time: datetime):
        """Print training analytics"""
        duration = datetime.now() - start_time

        self.log("\n" + "=" * 80)
        self.log("📊 RETRAINING ANALYTICS")
        self.log("=" * 80)

        # Best performance
        best = max(episode_stats, key=lambda x: x['win_rate'])
        self.log(f"\n🏆 Best Performance:")
        self.log(f"   Episode: {best['episode']}")
        self.log(f"   Win Rate: {best['win_rate']:.1f}%")
        self.log(f"   Avg Reward: {best['avg_reward']:.2f}")

        # Recent performance (last 50 episodes)
        recent = episode_stats[-50:]
        avg_win_rate = sum(s['win_rate'] for s in recent) / len(recent)
        avg_trades = sum(s['trades'] for s in recent) / len(recent)

        self.log(f"\n📈 Recent Performance (Last 50 Episodes):")
        self.log(f"   Avg Win Rate: {avg_win_rate:.1f}%")
        self.log(f"   Avg Trades/Episode: {avg_trades:.0f}")

        # Improvement
        early = episode_stats[:50]
        early_win_rate = sum(s['win_rate'] for s in early) / len(early)
        improvement = ((avg_win_rate - early_win_rate) / early_win_rate * 100) if early_win_rate > 0 else 0

        self.log(f"\n🎯 Learning Progress:")
        self.log(f"   Early Win Rate: {early_win_rate:.1f}%")
        self.log(f"   Recent Win Rate: {avg_win_rate:.1f}%")
        self.log(f"   Improvement: {improvement:+.1f}%")

        # Training metadata
        self.log(f"\n⏱️  Training Summary:")
        self.log(f"   Episodes: {len(episode_stats)}")
        self.log(f"   Duration: {duration.total_seconds():.0f} seconds")
        self.log(f"   Model: {self.model_path}")

        self.log("=" * 80)


def main():
    """Main entry point"""
    print("\n🧠 RL Model Retraining System\n")

    # Create retrainer
    retrainer = RLRetrainer()

    # Run retraining
    success = retrainer.retrain()

    if success:
        print("\n✅ Retraining complete! Model ready for use.")
        print("\nNext steps:")
        print("1. Restart trading bot to use retrained model")
        print("2. Monitor performance improvements")
        print("3. Retrain again after collecting more data")
    else:
        print("\n❌ Retraining failed!")
        print("\nTroubleshooting:")
        print("1. Ensure trading bot has been running for at least 24 hours")
        print("2. Check database for signals: sqlite3 trading_bot.db 'SELECT COUNT(*) FROM signals'")
        print("3. Review logs: cat logs/rl_retraining.log")

    print()


if __name__ == "__main__":
    main()
