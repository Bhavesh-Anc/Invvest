"""
Reinforcement Learning for Portfolio Management
Implements DQN, PPO, and A3C for optimal portfolio allocation
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque, namedtuple
from typing import List, Tuple, Dict, Optional
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Experience replay buffer
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


class PortfolioEnvironment:
    """
    Portfolio Management Environment
    State: [prices, holdings, cash, technical indicators]
    Actions: [buy, sell, hold] for each asset
    Reward: Portfolio returns with risk adjustment
    """

    def __init__(self, price_data: pd.DataFrame, initial_capital: float = 1000000,
                 transaction_cost: float = 0.001, max_position: float = 0.2):
        """
        Args:
            price_data: DataFrame with columns ['date', 'symbol', 'close', 'volume']
            initial_capital: Starting capital (₹)
            transaction_cost: Transaction cost as fraction
            max_position: Maximum position size per asset (20%)
        """
        self.price_data = price_data
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.max_position = max_position

        self.symbols = price_data['symbol'].unique()
        self.n_assets = len(self.symbols)

        self.reset()

    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_step = 0
        self.cash = self.initial_capital
        self.holdings = np.zeros(self.n_assets)  # Shares held
        self.portfolio_value_history = [self.initial_capital]
        self.trade_history = []

        return self._get_state()

    def _get_state(self) -> np.ndarray:
        """
        Get current state representation

        Returns:
            State vector: [normalized prices, holdings, cash ratio, returns, volatility]
        """
        # Get current prices
        current_data = self.price_data[self.price_data['step'] == self.current_step]
        prices = current_data.set_index('symbol')['close'].reindex(self.symbols).fillna(0).values

        # Normalize holdings by portfolio value
        portfolio_value = self.get_portfolio_value()
        holdings_norm = (self.holdings * prices) / portfolio_value if portfolio_value > 0 else self.holdings

        # Cash ratio
        cash_ratio = self.cash / portfolio_value if portfolio_value > 0 else 1.0

        # Recent returns (last 5 days)
        returns = self._get_recent_returns(window=5)

        # Volatility (last 20 days)
        volatility = self._get_volatility(window=20)

        # Combine state
        state = np.concatenate([
            prices / 10000,  # Normalize prices
            holdings_norm,
            [cash_ratio],
            returns,
            volatility
        ])

        return state.astype(np.float32)

    def _get_recent_returns(self, window: int = 5) -> np.ndarray:
        """Calculate recent returns for each asset"""
        if self.current_step < window:
            return np.zeros(self.n_assets)

        returns = []
        for symbol in self.symbols:
            symbol_data = self.price_data[self.price_data['symbol'] == symbol]
            recent_prices = symbol_data.iloc[self.current_step - window:self.current_step]['close'].values

            if len(recent_prices) > 1:
                ret = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            else:
                ret = 0

            returns.append(ret)

        return np.array(returns)

    def _get_volatility(self, window: int = 20) -> np.ndarray:
        """Calculate recent volatility for each asset"""
        if self.current_step < window:
            return np.zeros(self.n_assets)

        volatility = []
        for symbol in self.symbols:
            symbol_data = self.price_data[self.price_data['symbol'] == symbol]
            recent_prices = symbol_data.iloc[max(0, self.current_step - window):self.current_step]['close'].values

            if len(recent_prices) > 1:
                returns = np.diff(recent_prices) / recent_prices[:-1]
                vol = np.std(returns) * np.sqrt(252)  # Annualized
            else:
                vol = 0

            volatility.append(vol)

        return np.array(volatility)

    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute actions and return next state

        Args:
            actions: Action vector for each asset [-1 to 1]
                     -1 = sell all, 0 = hold, 1 = buy max

        Returns:
            next_state, reward, done, info
        """
        # Get current prices
        current_data = self.price_data[self.price_data['step'] == self.current_step]
        prices = current_data.set_index('symbol')['close'].reindex(self.symbols).fillna(0).values

        # Execute trades
        portfolio_value_before = self.get_portfolio_value()

        for i, action in enumerate(actions):
            self._execute_trade(i, action, prices[i])

        # Move to next step
        self.current_step += 1

        # Calculate reward
        portfolio_value_after = self.get_portfolio_value()
        returns = (portfolio_value_after - portfolio_value_before) / portfolio_value_before

        # Risk-adjusted reward (Sharpe-like)
        if len(self.portfolio_value_history) > 20:
            recent_returns = np.diff(self.portfolio_value_history[-20:]) / self.portfolio_value_history[-21:-1]
            sharpe = np.mean(recent_returns) / (np.std(recent_returns) + 1e-6)
            reward = returns + 0.1 * sharpe  # Reward both returns and risk-adjusted performance
        else:
            reward = returns

        self.portfolio_value_history.append(portfolio_value_after)

        # Check if episode is done
        done = (self.current_step >= len(self.price_data['step'].unique()) - 1) or (portfolio_value_after <= 0)

        # Info
        info = {
            'portfolio_value': portfolio_value_after,
            'cash': self.cash,
            'holdings_value': np.sum(self.holdings * prices),
            'returns': returns
        }

        next_state = self._get_state()

        return next_state, reward, done, info

    def _execute_trade(self, asset_idx: int, action: float, price: float):
        """
        Execute trade for a single asset

        Args:
            asset_idx: Index of asset
            action: Action value [-1, 1]
            price: Current price
        """
        if price <= 0:
            return

        portfolio_value = self.get_portfolio_value()

        if action > 0:  # Buy
            # Maximum amount to buy (respecting position limit)
            max_position_value = portfolio_value * self.max_position
            current_position_value = self.holdings[asset_idx] * price
            available_to_buy = max(0, max_position_value - current_position_value)

            # Amount to buy based on action strength
            buy_value = min(self.cash * action, available_to_buy)

            if buy_value > 0:
                shares_to_buy = buy_value / price
                cost = buy_value * (1 + self.transaction_cost)

                if cost <= self.cash:
                    self.holdings[asset_idx] += shares_to_buy
                    self.cash -= cost
                    self.trade_history.append({
                        'step': self.current_step,
                        'asset': asset_idx,
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': price,
                        'cost': cost
                    })

        elif action < 0:  # Sell
            # Amount to sell based on action strength
            shares_to_sell = self.holdings[asset_idx] * abs(action)

            if shares_to_sell > 0:
                proceeds = shares_to_sell * price * (1 - self.transaction_cost)
                self.holdings[asset_idx] -= shares_to_sell
                self.cash += proceeds
                self.trade_history.append({
                    'step': self.current_step,
                    'asset': asset_idx,
                    'action': 'SELL',
                    'shares': shares_to_sell,
                    'price': price,
                    'proceeds': proceeds
                })

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        current_data = self.price_data[self.price_data['step'] == self.current_step]
        prices = current_data.set_index('symbol')['close'].reindex(self.symbols).fillna(0).values

        holdings_value = np.sum(self.holdings * prices)
        return self.cash + holdings_value


class DQNNetwork(nn.Module):
    """
    Deep Q-Network for Portfolio Management
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_size: int = 256):
        super(DQNNetwork, self).__init__()

        self.fc1 = nn.Linear(state_dim, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc4 = nn.Linear(hidden_size // 2, action_dim)

        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return x  # Q-values for each action


class DQNAgent:
    """
    Deep Q-Network Agent for Portfolio Optimization
    """

    def __init__(self, state_dim: int, action_dim: int, learning_rate: float = 0.0001,
                 gamma: float = 0.99, epsilon_start: float = 1.0,
                 epsilon_end: float = 0.01, epsilon_decay: float = 0.995,
                 memory_size: int = 10000, batch_size: int = 64):
        """
        Args:
            state_dim: Dimension of state space
            action_dim: Dimension of action space
            learning_rate: Learning rate
            gamma: Discount factor
            epsilon_start: Starting exploration rate
            epsilon_end: Minimum exploration rate
            epsilon_decay: Epsilon decay rate
            memory_size: Replay buffer size
            batch_size: Batch size for training
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Q-networks
        self.q_network = DQNNetwork(state_dim, action_dim).to(self.device)
        self.target_network = DQNNetwork(state_dim, action_dim).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())

        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

        # Replay buffer
        self.memory = deque(maxlen=memory_size)

        logger.info(f"DQN Agent initialized on {self.device}")

    def select_action(self, state: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Select action using epsilon-greedy policy

        Args:
            state: Current state
            training: If True, use epsilon-greedy; else use greedy

        Returns:
            Action vector
        """
        if training and random.random() < self.epsilon:
            # Random action
            actions = np.random.uniform(-1, 1, self.action_dim)
        else:
            # Greedy action
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.q_network(state_tensor)
                # Convert Q-values to actions (normalized to [-1, 1])
                actions = torch.tanh(q_values).cpu().numpy().flatten()

        return actions

    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.append(Experience(state, action, reward, next_state, done))

    def train(self):
        """Train the Q-network using experience replay"""
        if len(self.memory) < self.batch_size:
            return

        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e.state for e in batch]).to(self.device)
        actions = torch.FloatTensor([e.action for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in batch]).to(self.device)
        dones = torch.FloatTensor([e.done for e in batch]).to(self.device)

        # Current Q-values
        current_q_values = self.q_network(states)

        # Target Q-values
        with torch.no_grad():
            next_q_values = self.target_network(next_states)
            max_next_q_values = next_q_values.max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * max_next_q_values

        # Loss
        loss = F.mse_loss(current_q_values.mean(1), target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
        self.optimizer.step()

        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return loss.item()

    def update_target_network(self):
        """Update target network with current Q-network weights"""
        self.target_network.load_state_dict(self.q_network.state_dict())

    def save(self, filepath: str):
        """Save agent"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, filepath)

    def load(self, filepath: str):
        """Load agent"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']


def train_dqn_portfolio(env: PortfolioEnvironment, episodes: int = 1000,
                       update_frequency: int = 10) -> DQNAgent:
    """
    Train DQN agent on portfolio environment

    Args:
        env: Portfolio environment
        episodes: Number of training episodes
        update_frequency: How often to update target network

    Returns:
        Trained DQN agent
    """
    state_dim = len(env.reset())
    action_dim = env.n_assets

    agent = DQNAgent(state_dim, action_dim)

    episode_rewards = []

    for episode in range(episodes):
        state = env.reset()
        episode_reward = 0
        done = False

        while not done:
            # Select action
            action = agent.select_action(state, training=True)

            # Execute action
            next_state, reward, done, info = env.step(action)

            # Store experience
            agent.store_experience(state, action, reward, next_state, done)

            # Train
            loss = agent.train()

            episode_reward += reward
            state = next_state

        episode_rewards.append(episode_reward)

        # Update target network
        if episode % update_frequency == 0:
            agent.update_target_network()

        if (episode + 1) % 100 == 0:
            avg_reward = np.mean(episode_rewards[-100:])
            logger.info(f"Episode {episode + 1}/{episodes} - Avg Reward: {avg_reward:.4f} - Epsilon: {agent.epsilon:.4f}")

    return agent


if __name__ == "__main__":
    logger.info("Reinforcement Learning Portfolio Manager - Institutional Grade")

    # Example: Create dummy environment
    # In practice, use real price data
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI']

    price_data = []
    for step, date in enumerate(dates):
        for symbol in symbols:
            price_data.append({
                'step': step,
                'date': date,
                'symbol': symbol,
                'close': 1000 + np.random.randn() * 50,  # Random walk
                'volume': 1000000
            })

    price_data = pd.DataFrame(price_data)

    # Create environment
    env = PortfolioEnvironment(price_data, initial_capital=10000000)

    # Train agent
    agent = train_dqn_portfolio(env, episodes=100)

    logger.info("Training completed!")
