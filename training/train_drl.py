"""
Training script for Deep Reinforcement Learning Agent
"""
import torch
import numpy as np
from tqdm import tqdm
import json
import os
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.models.sentiment_model import DRLPolicyNetwork, CommentEnvironment
from backend.app.models.replay_buffer import PrioritizedReplayBuffer
from backend.app.services.analyzer import SentimentAnalyzer


class DRLTrainer:
    """
    Trainer for DRL Agent with curriculum learning
    """
    
    def __init__(self, config=None):
        self.config = config or {
            'episodes': 1000,
            'batch_size': 64,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.01,
            'epsilon_decay': 0.995,
            'learning_rate': 3e-4,
            'target_update': 10,
            'save_interval': 100
        }
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize networks
        self.policy_net = DRLPolicyNetwork().to(self.device)
        self.target_net = DRLPolicyNetwork().to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = torch.optim.Adam(
            self.policy_net.parameters(), 
            lr=self.config['learning_rate']
        )
        
        self.replay_buffer = PrioritizedReplayBuffer(capacity=100000)
        self.analyzer = SentimentAnalyzer()
        
        # Metrics
        self.episode_rewards = []
        self.losses = []
        
    def generate_synthetic_data(self, n_samples=1000):
        """
        Generate synthetic training data with various sentiment patterns
        """
        templates = {
            'positive': [
                "Sản phẩm rất tốt, tôi rất hài lòng",
                "Dịch vụ tuyệt vời, sẽ ủng hộ lại",
                "Chất lượng xuất sắc, đáng đồng tiền",
                "Giao hàng nhanh, đóng gói cẩn thận",
                "Nhân viên nhiệt tình, chu đáo"
            ],
            'negative': [
                "Sản phẩm quá tệ, thất vọng hoàn toàn",
                "Dịch vụ kém, không bao giờ quay lại",
                "Giao hàng chậm, thái độ nhân viên tệ",
                "Chất lượng không như mong đợi",
                "Giá quá cao so với chất lượng"
            ],
            'neutral': [
                "Sản phẩm bình thường, không có gì đặc biệt",
                "Giao hàng đúng hẹn, đóng gói ổn",
                "Chất lượng tạm được",
                "Giá cả hợp lý",
                "Sẽ cân nhắc mua lại"
            ]
        }
        
        data = []
        for _ in range(n_samples):
            sentiment = np.random.choice(['positive', 'negative', 'neutral'], 
                                        p=[0.4, 0.3, 0.3])
            text = np.random.choice(templates[sentiment])
            
            # Add variations
            if np.random.random() > 0.5:
                text += " " + np.random.choice(["!", "...", " 😊", " 😠", " 🤔"])
            
            data.append({
                'text': text,
                'sentiment': sentiment,
                'likes': np.random.randint(0, 100),
                'length': len(text)
            })
        
        return data
    
    async def preprocess_data(self, raw_data):
        """
        Preprocess raw data through sentiment analyzer
        """
        processed = []
        for item in raw_data:
            analysis = await self.analyzer._analyze_single(item, 'standard')
            processed.append(analysis)
        return processed
    
    def train_episode(self, env):
        """
        Single training episode
        """
        state = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            # Epsilon-greedy action selection
            if np.random.random() < self.epsilon:
                action = np.random.randint(0, 5)
            else:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                    action_probs, _, _ = self.policy_net(state_tensor)
                    action = torch.argmax(action_probs).item()
            
            # Execute action
            next_state, reward, done, info = env.step(action)
            episode_reward += reward
            
            # Store experience
            self.replay_buffer.add(state, action, reward, next_state, done)
            
            # Train if enough samples
            if len(self.replay_buffer) > self.config['batch_size']:
                loss = self._train_step()
                self.losses.append(loss)
            
            state = next_state
        
        return episode_reward
    
    def _train_step(self):
        """
        Single gradient update step
        """
        import torch.nn.functional as F
        
        states, actions, rewards, next_states, dones, indices, weights = \
            self.replay_buffer.sample(self.config['batch_size'])
        
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        weights = weights.to(self.device)
        
        # Current Q values
        current_action_probs, current_values, _ = self.policy_net(states)
        current_q = current_action_probs.gather(1, actions.unsqueeze(1)).squeeze()
        
        # Double DQN target
        with torch.no_grad():
            next_action_probs, _, _ = self.policy_net(next_states)
            next_actions = next_action_probs.argmax(dim=1)
            
            target_action_probs, target_values, _ = self.target_net(next_states)
            next_q = target_action_probs.gather(1, next_actions.unsqueeze(1)).squeeze()
            
            target_q = rewards + (1 - dones) * self.config['gamma'] * next_q
        
        # TD errors for priority update
        td_errors = torch.abs(current_q - target_q).detach().cpu().numpy()
        
        # Weighted loss
        loss = (weights * F.smooth_l1_loss(current_q, target_q, reduction='none')).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Update priorities
        self.replay_buffer.update_priorities(indices, td_errors)
        
        return loss.item()
    
    async def train(self):
        """
        Main training loop
        """
        print("🚀 Starting DRL Training...")
        print(f"Device: {self.device}")
        
        # Generate training data
        print("Generating synthetic training data...")
        raw_data = self.generate_synthetic_data(2000)
        processed_data = await self.preprocess_data(raw_data)
        
        self.epsilon = self.config['epsilon_start']
        
        for episode in tqdm(range(self.config['episodes']), desc="Training"):
            # Create environment with shuffled data
            np.random.shuffle(processed_data)
            env = CommentEnvironment(processed_data[:500])
            
            # Train episode
            episode_reward = self.train_episode(env)
            self.episode_rewards.append(episode_reward)
            
            # Decay epsilon
            self.epsilon = max(
                self.config['epsilon_end'],
                self.epsilon * self.config['epsilon_decay']
            )
            
            # Update target network
            if episode % self.config['target_update'] == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())
            
            # Save checkpoint
            if episode % self.config['save_interval'] == 0:
                self._save_checkpoint(episode)
            
            # Logging
            if episode % 50 == 0:
                avg_reward = np.mean(self.episode_rewards[-50:])
                avg_loss = np.mean(self.losses[-500:]) if self.losses else 0
                print(f"\nEpisode {episode}: Avg Reward = {avg_reward:.2f}, "
                      f"Loss = {avg_loss:.4f}, Epsilon = {self.epsilon:.3f}")
        
        # Final save
        self._save_checkpoint('final')
        self._plot_training_curves()
        
        print("✅ Training completed!")
    
    def _save_checkpoint(self, episode):
        """Save model checkpoint"""
        os.makedirs('models', exist_ok=True)
        checkpoint = {
            'episode': episode,
            'policy_state_dict': self.policy_net.state_dict(),
            'target_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'config': self.config
        }
        torch.save(checkpoint, f'models/drl_checkpoint_{episode}.pt')
    
    def _plot_training_curves(self):
        """Plot training metrics"""
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Episode rewards
        axes[0].plot(self.episode_rewards, alpha=0.3, color='blue')
        # Moving average
        window = 50
        if len(self.episode_rewards) > window:
            moving_avg = np.convolve(
                self.episode_rewards, 
                np.ones(window)/window, 
                mode='valid'
            )
            axes[0].plot(range(window-1, len(self.episode_rewards)), 
                        moving_avg, color='red', linewidth=2)
        axes[0].set_title('Episode Rewards')
        axes[0].set_xlabel('Episode')
        axes[0].set_ylabel('Total Reward')
        axes[0].grid(True, alpha=0.3)
        
        # Losses
        if self.losses:
            axes[1].plot(self.losses, alpha=0.3, color='green')
            if len(self.losses) > window:
                moving_avg = np.convolve(
                    self.losses, 
                    np.ones(window)/window, 
                    mode='valid'
                )
                axes[1].plot(range(window-1, len(self.losses)), 
                            moving_avg, color='darkgreen', linewidth=2)
        axes[1].set_title('Training Loss')
        axes[1].set_xlabel('Training Step')
        axes[1].set_ylabel('Loss')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('training_curves.png', dpi=150, bbox_inches='tight')
        plt.close()


async def main():
    trainer = DRLTrainer()
    await trainer.train()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())