"""
Q-Learning Model for Trading
Implements Q-learning algorithm for reinforcement learning-based trading decisions
"""

import pickle
import numpy as np
from typing import Dict, Any, Tuple, List
from datetime import datetime
from collections import deque
import os


class QLearningTrader:
    """Q-Learning based trading model"""

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        experience_buffer_size: int = 10000
    ):
        """
        Initialize Q-Learning trader

        Args:
            learning_rate: Learning rate for Q-value updates
            discount_factor: Discount factor for future rewards
            epsilon: Initial exploration rate
            epsilon_min: Minimum exploration rate
            epsilon_decay: Decay rate for epsilon
            experience_buffer_size: Size of experience replay buffer
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Q-table: {state: {action: q_value}}
        self.q_table = {}

        # Experience replay buffer
        self.experience_buffer = deque(maxlen=experience_buffer_size)

        # Actions: 0 = HOLD, 1 = BUY, 2 = SELL
        self.actions = ['HOLD', 'BUY', 'SELL']

        # Statistics
        self.total_episodes = 0
        self.total_rewards = 0
        self.win_streak = 0
        self.loss_streak = 0

    def discretize_state(self, state_data: Dict[str, Any]) -> str:
        """
        Convert continuous state to discrete state string

        Args:
            state_data: Dictionary containing state information

        Returns:
            Discrete state string
        """
        # Extract key state features
        signal = state_data.get('signal', 'HOLD')
        signal_strength = state_data.get('signal_strength', 0)

        # RSI bins: oversold (<30), neutral (30-70), overbought (>70)
        rsi = state_data.get('rsi', 50)
        rsi_state = 'low' if rsi < 30 else 'high' if rsi > 70 else 'mid'

        # MACD state: bullish or bearish
        macd_hist = state_data.get('macd_histogram', 0)
        macd_state = 'bullish' if macd_hist > 0 else 'bearish'

        # Price vs VWAP
        price = state_data.get('price', 0)
        vwap = state_data.get('vwap', 0)
        vwap_state = 'above' if price > vwap else 'below'

        # Market regime
        market_regime = state_data.get('market_regime', 'neutral')

        # Fear & Greed Index
        fear_greed = state_data.get('fear_greed_index', 50)
        fg_state = 'fear' if fear_greed < 40 else 'greed' if fear_greed > 60 else 'neutral'

        # BTC correlation
        btc_correlation = state_data.get('btc_correlation', 0)
        btc_corr_state = 'high' if abs(btc_correlation) > 0.7 else 'low'

        # Position status
        has_position = state_data.get('has_position', False)
        position_pnl = state_data.get('position_pnl', 0)
        position_state = 'none'
        if has_position:
            if position_pnl > 0:
                position_state = 'profit'
            else:
                position_state = 'loss'

        # Create discrete state string
        state_str = f"{signal}_{signal_strength}_{rsi_state}_{macd_state}_{vwap_state}_{market_regime}_{fg_state}_{btc_corr_state}_{position_state}"

        return state_str

    def get_q_value(self, state: str, action: int) -> float:
        """
        Get Q-value for state-action pair

        Args:
            state: State string
            action: Action index (0=HOLD, 1=BUY, 2=SELL)

        Returns:
            Q-value
        """
        if state not in self.q_table:
            self.q_table[state] = {0: 0.0, 1: 0.0, 2: 0.0}

        return self.q_table[state][action]

    def update_q_value(self, state: str, action: int, reward: float, next_state: str):
        """
        Update Q-value using Q-learning formula

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Resulting next state
        """
        if state not in self.q_table:
            self.q_table[state] = {0: 0.0, 1: 0.0, 2: 0.0}

        if next_state not in self.q_table:
            self.q_table[next_state] = {0: 0.0, 1: 0.0, 2: 0.0}

        # Q-learning update formula
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state][action] = new_q

    def choose_action(self, state_data: Dict[str, Any], explore: bool = True) -> Tuple[int, str, float]:
        """
        Choose action using epsilon-greedy strategy

        Args:
            state_data: Current state information
            explore: Whether to use exploration

        Returns:
            Tuple of (action_index, action_name, confidence)
        """
        state = self.discretize_state(state_data)

        # Epsilon-greedy exploration
        if explore and np.random.random() < self.epsilon:
            action = np.random.randint(0, 3)
            confidence = 0.0  # Low confidence for random action
        else:
            # Exploit: choose best action
            if state not in self.q_table:
                self.q_table[state] = {0: 0.0, 1: 0.0, 2: 0.0}

            q_values = self.q_table[state]
            action = max(q_values, key=q_values.get)

            # Calculate confidence based on Q-value difference
            q_vals = list(q_values.values())
            max_q = max(q_vals)
            min_q = min(q_vals)
            confidence = (max_q - min_q) if max_q != min_q else 0.5

        return action, self.actions[action], confidence

    def add_experience(self, state_data: Dict[str, Any], action: int, reward: float, next_state_data: Dict[str, Any]):
        """
        Add experience to replay buffer

        Args:
            state_data: Current state
            action: Action taken
            reward: Reward received
            next_state_data: Next state
        """
        state = self.discretize_state(state_data)
        next_state = self.discretize_state(next_state_data)

        self.experience_buffer.append((state, action, reward, next_state))

    def replay_experience(self, batch_size: int = 32):
        """
        Replay random experiences from buffer for training

        Args:
            batch_size: Number of experiences to replay
        """
        if len(self.experience_buffer) < batch_size:
            return

        # Random sample from experience buffer
        indices = np.random.choice(len(self.experience_buffer), batch_size, replace=False)
        batch = [self.experience_buffer[i] for i in indices]

        for state, action, reward, next_state in batch:
            self.update_q_value(state, action, reward, next_state)

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def calculate_reward(self, pnl: float, streak_bonus: float = 0, market_context: Dict[str, Any] = None) -> float:
        """
        Calculate reward based on profit/loss and other factors

        Args:
            pnl: Profit and loss amount
            streak_bonus: Bonus/penalty for win/loss streaks
            market_context: Additional market context for reward shaping

        Returns:
            Calculated reward
        """
        # Base reward from PnL
        if pnl > 0:
            # Profitable trade
            if pnl > 0.02:  # >2% profit
                reward = 20.0
            else:  # 0-2% profit
                reward = 10.0
            self.win_streak += 1
            self.loss_streak = 0
        elif pnl < 0:
            # Losing trade
            if pnl < -0.02:  # >2% loss
                reward = -20.0
            else:  # 0-2% loss
                reward = -10.0
            self.loss_streak += 1
            self.win_streak = 0
        else:
            # No trade or break-even
            reward = 0.0

        # Add streak bonus/penalty
        if self.win_streak >= 3:
            reward += 5.0  # Winning streak bonus
        elif self.loss_streak >= 3:
            reward -= 5.0  # Losing streak penalty

        # Market context adjustments
        if market_context:
            # Reward alignment with market trend
            if market_context.get('market_trend') == 'bullish' and pnl > 0:
                reward += 2.0
            elif market_context.get('market_trend') == 'bearish' and pnl < 0:
                reward -= 2.0

        self.total_rewards += reward
        return reward

    def save_model(self, file_path: str = "rl_trading_model.pkl"):
        """
        Save model to file

        Args:
            file_path: Path to save model
        """
        model_data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'total_episodes': self.total_episodes,
            'total_rewards': self.total_rewards,
            'win_streak': self.win_streak,
            'loss_streak': self.loss_streak,
            'timestamp': datetime.now().isoformat()
        }

        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"✅ Model saved to {file_path}")

    def load_model(self, file_path: str = "rl_trading_model.pkl") -> bool:
        """
        Load model from file

        Args:
            file_path: Path to load model from

        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            print(f"⚠️ Model file not found: {file_path}")
            return False

        try:
            with open(file_path, 'rb') as f:
                model_data = pickle.load(f)

            self.q_table = model_data.get('q_table', {})
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.total_episodes = model_data.get('total_episodes', 0)
            self.total_rewards = model_data.get('total_rewards', 0)
            self.win_streak = model_data.get('win_streak', 0)
            self.loss_streak = model_data.get('loss_streak', 0)

            print(f"✅ Model loaded from {file_path}")
            print(f"   Total states learned: {len(self.q_table)}")
            print(f"   Total episodes: {self.total_episodes}")
            print(f"   Current epsilon: {self.epsilon:.4f}")
            return True

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False

    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get model statistics

        Returns:
            Dictionary of model statistics
        """
        return {
            'total_states': len(self.q_table),
            'total_episodes': self.total_episodes,
            'total_rewards': self.total_rewards,
            'current_epsilon': self.epsilon,
            'win_streak': self.win_streak,
            'loss_streak': self.loss_streak,
            'experience_buffer_size': len(self.experience_buffer)
        }


if __name__ == "__main__":
    # Test Q-learning model
    print("Testing Q-Learning Model...")

    model = QLearningTrader()

    # Test state discretization
    test_state = {
        'signal': 'BUY',
        'signal_strength': 5,
        'rsi': 35,
        'macd_histogram': 0.5,
        'price': 100,
        'vwap': 98,
        'market_regime': 'risk_on',
        'fear_greed_index': 65,
        'btc_correlation': 0.8,
        'has_position': False,
        'position_pnl': 0
    }

    discrete_state = model.discretize_state(test_state)
    print(f"\nDiscrete state: {discrete_state}")

    # Test action selection
    action, action_name, confidence = model.choose_action(test_state)
    print(f"Chosen action: {action_name} (confidence: {confidence:.2f})")

    # Test reward calculation
    reward = model.calculate_reward(0.03)
    print(f"Reward for 3% profit: {reward}")

    # Save and load model
    model.save_model("test_model.pkl")
    model.load_model("test_model.pkl")

    print("\n✅ Q-Learning model test completed")
