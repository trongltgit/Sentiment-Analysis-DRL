"""
Experience Replay Buffer for DRL Training
"""
import torch
import numpy as np
from collections import deque, namedtuple
from typing import Tuple, List
import random

Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


class PrioritizedReplayBuffer:
    """
    Prioritized Experience Replay for efficient DRL learning
    """
    def __init__(self, capacity: int = 100000, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha  # Priority exponent
        self.beta = beta    # Importance sampling exponent
        self.beta_increment = 0.001
        
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        self.size = 0
    
    def add(self, state: np.ndarray, action: int, reward: float, 
            next_state: np.ndarray, done: bool):
        """
        Add experience with maximum priority
        """
        max_priority = self.priorities.max() if self.size > 0 else 1.0
        
        experience = Experience(state, action, reward, next_state, done)
        
        if self.size < self.capacity:
            self.buffer.append(experience)
            self.size += 1
        else:
            self.buffer[self.position] = experience
        
        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> Tuple:
        """
        Sample batch with prioritized experience replay
        """
        if self.size < batch_size:
            batch_size = self.size
        
        # Calculate sampling probabilities
        priorities = self.priorities[:self.size]
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        # Sample indices
        indices = np.random.choice(self.size, batch_size, p=probabilities, replace=False)
        
        # Calculate importance sampling weights
        weights = (self.size * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        # Extract experiences
        experiences = [self.buffer[idx] for idx in indices]
        
        # Convert to tensors
        states = torch.FloatTensor([e.state for e in experiences])
        actions = torch.LongTensor([e.action for e in experiences])
        rewards = torch.FloatTensor([e.reward for e in experiences])
        next_states = torch.FloatTensor([e.next_state for e in experiences])
        dones = torch.FloatTensor([e.done for e in experiences])
        weights = torch.FloatTensor(weights)
        
        return states, actions, rewards, next_states, dones, indices, weights
    
    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """
        Update priorities based on TD errors
        """
        for idx, error in zip(indices, td_errors):
            self.priorities[idx] = abs(error) + 1e-6  # Small constant for stability
    
    def __len__(self):
        return self.size


class MultiStepBuffer:
    """
    N-step returns buffer for temporal difference learning
    """
    def __init__(self, n_step: int = 3, gamma: float = 0.99):
        self.n_step = n_step
        self.gamma = gamma
        self.buffer = deque(maxlen=n_step)
    
    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
        
        if len(self.buffer) == self.n_step or done:
            return self._get_n_step_experience()
        return None
    
    def _get_n_step_experience(self):
        # Calculate n-step return
        reward = 0
        for i, (_, _, r, _, _) in enumerate(self.buffer):
            reward += (self.gamma ** i) * r
        
        state, action, _, _, _ = self.buffer[0]
        _, _, _, next_state, done = self.buffer[-1]
        
        return state, action, reward, next_state, done
    
    def reset(self):
        self.buffer.clear()