import numpy as np

class EpsilonGreedyMetaLearner:
    def __init__(self, n_models, epsilon=0.1, decay=0.999):
        self.n_models = n_models
        self.epsilon = epsilon
        self.decay = decay
        self.model_weights = np.ones(n_models) / n_models
        self.model_rewards = np.zeros(n_models)
        self.model_counts = np.zeros(n_models)
    
    def select_model(self):
        if np.random.random() < self.epsilon:
            # Exploration: random selection
            return np.random.randint(self.n_models)
        else:
            # Exploitation: select best model
            return np.argmax(self.model_weights)
    
    def update(self, model_idx, reward):
        # Update counts and rewards
        self.model_counts[model_idx] += 1
        self.model_rewards[model_idx] += reward
        
        # Update weights
        avg_reward = self.model_rewards[model_idx] / self.model_counts[model_idx]
        self.model_weights[model_idx] = avg_reward
        
        # Decay epsilon
        self.epsilon *= self.decay
        
        # Normalize weights
        self.model_weights = self.model_weights / np.sum(self.model_weights)
    
    def get_weights(self):
        return self.model_weights.copy()