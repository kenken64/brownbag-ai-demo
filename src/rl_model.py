"""
Reinforcement Learning Model (Q-Learning) for Trading Decisions
Implements enhanced Q-learning with experience replay and market context awareness
"""

import numpy as np
import pickle
import os
from typing import Tuple, Dict, Any, List
from collections import deque
import random
from datetime import datetime


class QLearningAgent:
    """Q-Learning agent for trading decisions with enhanced state representation"""

    # Action space
    ACTION_BUY = 0
    ACTION_SELL = 1
    ACTION_HOLD = 2
    ACTION_NAMES = ['BUY', 'SELL', 'HOLD']

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        buffer_size: int = 10000
    ):
        """
        Initialize Q-Learning agent

        Args:
            learning_rate: Learning rate for Q-value updates
            discount_factor: Discount factor for future rewards
            epsilon: Initial exploration rate
            epsilon_decay: Decay rate for epsilon
            epsilon_min: Minimum epsilon value
            buffer_size: Size of experience replay buffer
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        # Q-table: dict mapping state -> action values
        self.q_table = {}

        # Experience replay buffer
        self.experience_buffer = deque(maxlen=buffer_size)

        # Statistics
        self.total_episodes = 0
        self.total_states_learned = 0

        print("🧠 Q-Learning agent initialized")

    def get_state_key(self, state: Dict[str, Any]) -> str:
        """
        Convert state dictionary to a hashable string key for Q-table

        Enhanced state representation includes:
        - Market conditions (price trend, volatility)
        - Technical indicators (RSI, MACD, signal strength)
        - Market context (BTC correlation, Fear & Greed)
        - Position status
        """
        # Discretize continuous values into bins
        signal_strength = state.get('signal_strength', 0)
        rsi = state.get('rsi', 50)
        macd_histogram = state.get('macd_histogram', 0)
        fear_greed = state.get('fear_greed_index', 50)
        position_pnl = state.get('position_pnl', 0)
        btc_trend = state.get('btc_trend', 'neutral')
        market_regime = state.get('market_regime', 'neutral')

        # Create discrete state representation
        state_key = (
            f"sig:{self._discretize(signal_strength, bins=[-10, -3, -1, 1, 3, 10])}|"
            f"rsi:{self._discretize(rsi, bins=[30, 40, 50, 60, 70])}|"
            f"macd:{self._discretize(macd_histogram, bins=[-0.1, -0.01, 0, 0.01, 0.1])}|"
            f"fg:{self._discretize(fear_greed, bins=[25, 45, 55, 75])}|"
            f"pnl:{self._discretize(position_pnl, bins=[-0.05, -0.02, 0, 0.02, 0.05])}|"
            f"btc:{btc_trend}|"
            f"regime:{market_regime}"
        )

        return state_key

    def _discretize(self, value: float, bins: List[float]) -> int:
        """Discretize a continuous value into bins"""
        for i, threshold in enumerate(bins):
            if value < threshold:
                return i
        return len(bins)

    def get_q_values(self, state_key: str) -> np.ndarray:
        """Get Q-values for a state, initialize if not exists"""
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(3)  # 3 actions: BUY, SELL, HOLD
            self.total_states_learned += 1
        return self.q_table[state_key]

    def choose_action(self, state: Dict[str, Any], training: bool = True) -> int:
        """
        Choose action using epsilon-greedy policy

        Args:
            state: Current state dictionary
            training: If True, use exploration; if False, use greedy policy

        Returns:
            Action index (0=BUY, 1=SELL, 2=HOLD)
        """
        state_key = self.get_state_key(state)
        q_values = self.get_q_values(state_key)

        # Exploration vs exploitation
        if training and random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, 2)
        else:
            # Exploit: choose best action
            return int(np.argmax(q_values))

    def get_action_confidence(self, state: Dict[str, Any]) -> Tuple[int, float]:
        """
        Get action and confidence score

        Returns:
            (action, confidence): action index and confidence (0-1)
        """
        state_key = self.get_state_key(state)
        q_values = self.get_q_values(state_key)

        action = int(np.argmax(q_values))
        max_q = q_values[action]
        min_q = np.min(q_values)

        # Confidence based on Q-value separation
        if max_q == min_q:
            confidence = 0.0
        else:
            confidence = min(1.0, (max_q - min_q) / 10.0)  # Normalize to 0-1

        return action, confidence

    def update_q_value(
        self,
        state: Dict[str, Any],
        action: int,
        reward: float,
        next_state: Dict[str, Any],
        done: bool
    ):
        """
        Update Q-value using Q-learning update rule

        Q(s,a) = Q(s,a) + α * [R + γ * max Q(s',a') - Q(s,a)]
        """
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)

        current_q = self.get_q_values(state_key)[action]
        next_max_q = np.max(self.get_q_values(next_state_key)) if not done else 0

        # Q-learning update
        target = reward + self.discount_factor * next_max_q
        new_q = current_q + self.learning_rate * (target - current_q)

        self.q_table[state_key][action] = new_q

    def store_experience(
        self,
        state: Dict[str, Any],
        action: int,
        reward: float,
        next_state: Dict[str, Any],
        done: bool
    ):
        """Store experience in replay buffer"""
        self.experience_buffer.append((state, action, reward, next_state, done))

    def replay_experiences(self, batch_size: int = 32):
        """Learn from random batch of past experiences"""
        if len(self.experience_buffer) < batch_size:
            return

        batch = random.sample(self.experience_buffer, batch_size)

        for state, action, reward, next_state, done in batch:
            self.update_q_value(state, action, reward, next_state, done)

    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def calculate_reward(
        self,
        action: int,
        pnl: float,
        signal_strength: int,
        position_status: str,
        streak_bonus: int = 0
    ) -> float:
        """
        Enhanced reward function based on PnL and trading outcomes

        Reward structure:
        - Large positive rewards for profitable trades (+10 to +20)
        - Heavy penalties for losses (-10 to -20)
        - Streak bonuses/penalties (±5)
        - Smart HOLD rewards (avoiding bad trades)
        """
        reward = 0.0

        if action == self.ACTION_BUY or action == self.ACTION_SELL:
            # Reward/penalty based on PnL
            if pnl > 0.02:  # > 2% profit
                reward = 20
            elif pnl > 0:
                reward = 10
            elif pnl > -0.02:  # Small loss
                reward = -10
            else:  # > 2% loss
                reward = -20

            # Streak bonus/penalty
            reward += streak_bonus

        elif action == self.ACTION_HOLD:
            # Reward HOLD if it avoided a bad trade
            if signal_strength == 0:
                reward = 5  # Good HOLD decision
            else:
                reward = -2  # Missed opportunity

        return reward

    def save_model(self, filepath: str = "models/rl_trading_model.pkl"):
        """Save Q-table and parameters to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        model_data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'total_episodes': self.total_episodes,
            'total_states_learned': self.total_states_learned,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"✅ Model saved to {filepath} ({self.total_states_learned} states)")

    def load_model(self, filepath: str = "models/rl_trading_model.pkl"):
        """Load Q-table and parameters from file"""
        if not os.path.exists(filepath):
            print(f"⚠️ Model file not found: {filepath}. Starting with new model.")
            return False

        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.q_table = model_data['q_table']
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.total_episodes = model_data.get('total_episodes', 0)
            self.total_states_learned = model_data.get('total_states_learned', 0)

            print(f"✅ Model loaded from {filepath} ({self.total_states_learned} states)")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            'total_states': len(self.q_table),
            'total_episodes': self.total_episodes,
            'epsilon': self.epsilon,
            'buffer_size': len(self.experience_buffer),
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor
        }


if __name__ == "__main__":
    # Test RL model
    agent = QLearningAgent()

    # Test state
    test_state = {
        'signal_strength': 3,
        'rsi': 65,
        'macd_histogram': 0.05,
        'fear_greed_index': 60,
        'position_pnl': 0.01,
        'btc_trend': 'up_strong',
        'market_regime': 'risk_on'
    }

    action, confidence = agent.get_action_confidence(test_state)
    print(f"Action: {agent.ACTION_NAMES[action]}, Confidence: {confidence:.2f}")

    # Save test
    agent.save_model("models/test_model.pkl")
    print("RL model module loaded successfully")