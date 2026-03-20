"""
Deep Reinforcement Learning Agent Service
"""
import torch
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from typing import List, Dict, Tuple
import asyncio
from collections import defaultdict

from ..models.sentiment_model import DRLPolicyNetwork, CommentEnvironment
from ..models.replay_buffer import PrioritizedReplayBuffer, MultiStepBuffer
from ..config import settings


class DRLAgentService:
    """
    Service for DRL-based comment optimization and action selection
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize networks
        self.policy_net = DRLPolicyNetwork().to(self.device)
        self.target_net = DRLPolicyNetwork().to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.policy_net.parameters(), 
            lr=settings.LEARNING_RATE
        )
        
        # Replay buffer
        self.replay_buffer = PrioritizedReplayBuffer(
            capacity=settings.BUFFER_SIZE
        )
        
        # Multi-step buffer
        self.n_step_buffer = MultiStepBuffer(n_step=3)
        
        # Training state
        self.training_step = 0
        self.episode_count = 0
        
        # Action mapping
        self.actions = ["prioritize", "filter", "highlight", "respond", "ignore"]
    
    async def optimize_analysis(self, analyzed_comments: List[Dict]) -> List[Dict]:
        """
        Apply DRL optimization to analyzed comments
        """
        if len(analyzed_comments) == 0:
            return []
        
        # Create environment
        env = CommentEnvironment(analyzed_comments)
        
        optimized = []
        state = env.reset()
        done = False
        
        while not done:
            # Get action from policy
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action, confidence = self.policy_net.get_action(state_tensor)
            
            # Execute action
            next_state, reward, done, info = env.step(action)
            
            # Store experience
            self.replay_buffer.add(
                state, action, reward, next_state, done
            )
            
            # Apply action to comment
            comment_idx = len(optimized)
            comment = analyzed_comments[comment_idx].copy()
            comment["drl_action"] = self.actions[action]
            comment["action_confidence"] = confidence
            comment["predicted_reward"] = reward
            
            # Add action-specific metadata
            if action == 0:  # prioritize
                comment["priority_score"] = comment.get("importance_score", 0.5) * 1.5
            elif action == 1:  # filter
                comment["filtered"] = True
            elif action == 2:  # highlight
                comment["highlighted"] = True
            elif action == 3:  # respond
                comment["requires_response"] = True
            
            optimized.append(comment)
            state = next_state
            
            # Train if enough samples
            if len(self.replay_buffer) > settings.BATCH_SIZE:
                await self._train_step()
        
        # Sort by priority if applicable
        optimized.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        
        self.episode_count += 1
        return optimized
    
    async def _train_step(self):
        """Single training step using Double DQN"""
        # Sample from replay buffer
        states, actions, rewards, next_states, dones, indices, weights = \
            self.replay_buffer.sample(settings.BATCH_SIZE)
        
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        weights = weights.to(self.device)
        
        # Current Q values
        current_action_probs, current_values, _ = self.policy_net(states)
        current_q = current_action_probs.gather(1, actions.unsqueeze(1)).squeeze()
        
        # Target Q values (Double DQN)
        with torch.no_grad():
            next_action_probs, _, _ = self.policy_net(next_states)
            next_actions = next_action_probs.argmax(dim=1)
            
            target_action_probs, target_values, _ = self.target_net(next_states)
            next_q = target_action_probs.gather(1, next_actions.unsqueeze(1)).squeeze()
            
            target_q = rewards + (1 - dones) * settings.GAMMA * next_q
        
        # TD errors for priority update
        td_errors = torch.abs(current_q - target_q).detach().cpu().numpy()
        
        # Weighted MSE loss
        loss = (weights * F.mse_loss(current_q, target_q, reduction='none')).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Update priorities
        self.replay_buffer.update_priorities(indices, td_errors)
        
        # Update target network
        self.training_step += 1
        if self.training_step % settings.TARGET_UPDATE_FREQ == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
    
    async def process_feedback(self, feedback: Dict):
        """
        Process user feedback to improve agent (online learning)
        """
        analysis_id = feedback.get("analysis_id")
        rating = feedback.get("user_rating", 3)
        corrections = feedback.get("corrections", {})
        
        # Convert rating to reward signal
        reward_signal = (rating - 3) / 2.0  # Normalize to [-1, 1]
        
        # Adjust recent experiences based on feedback
        # This is a simplified version - full implementation would track
        # which experiences correspond to which analysis
        
        # Save model checkpoint
        if self.episode_count % 10 == 0:
            await self._save_checkpoint()
    
    async def _save_checkpoint(self):
        """Save model checkpoint"""
        checkpoint = {
            'policy_state_dict': self.policy_net.state_dict(),
            'target_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_step': self.training_step,
            'episode_count': self.episode_count
        }
        torch.save(checkpoint, settings.DRL_MODEL_PATH)
    
    async def load_checkpoint(self):
        """Load model checkpoint"""
        try:
            checkpoint = torch.load(settings.DRL_MODEL_PATH, map_location=self.device)
            self.policy_net.load_state_dict(checkpoint['policy_state_dict'])
            self.target_net.load_state_dict(checkpoint['target_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.training_step = checkpoint.get('training_step', 0)
            self.episode_count = checkpoint.get('episode_count', 0)
        except FileNotFoundError:
            print("No checkpoint found, starting from scratch")
    
    def get_action_explanation(self, action: int, comment: Dict) -> str:
        """Generate human-readable explanation for action"""
        explanations = {
            0: f"Ưu tiên xử lý vì độ quan trọng cao ({comment.get('importance_score', 0):.2f})",
            1: "Lọc bỏ do chất lượng thấp hoặc spam",
            2: "Đánh dấu nổi bật vì phản hồi tích cực giá trị",
            3: "Cần phản hồi ngay do nội dung tiêu cực/khiếu nại",
            4: "Bỏ qua vì nội dung trung lập và không quan trọng"
        }
        return explanations.get(action, "Không xác định")