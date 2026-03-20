"""
Neural Network Architecture for Sentiment Analysis with DRL
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
from typing import Dict, List, Tuple
import numpy as np


class SentimentFeatureExtractor(nn.Module):
    """
    Multi-task neural network for extracting sentiment features
    """
    def __init__(self, pretrained_model: str = "vinai/phobert-base", num_aspects: int = 5):
        super().__init__()
        self.bert = AutoModel.from_pretrained(pretrained_model)
        self.hidden_size = self.bert.config.hidden_size
        
        # Aspect-based sentiment heads
        self.aspect_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(self.hidden_size, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, 3)  # pos, neu, neg
            ) for _ in range(num_aspects)
        ])
        
        # Emotion detection head
        self.emotion_head = nn.Sequential(
            nn.Linear(self.hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 8)  # joy, sadness, anger, fear, surprise, disgust, trust, anticipation
        )
        
        # Importance scoring head (for DRL)
        self.importance_head = nn.Sequential(
            nn.Linear(self.hidden_size + 8, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
        # Text quality assessment
        self.quality_head = nn.Sequential(
            nn.Linear(self.hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        # Extract BERT features
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]  # CLS token
        
        # Aspect sentiments
        aspect_logits = [head(pooled_output) for head in self.aspect_heads]
        aspect_probs = [F.softmax(logits, dim=-1) for logits in aspect_logits]
        
        # Emotions
        emotion_logits = self.emotion_head(pooled_output)
        emotion_probs = F.softmax(emotion_logits, dim=-1)
        
        # Importance score (combines semantic + emotional features)
        combined_features = torch.cat([pooled_output, emotion_probs], dim=-1)
        importance_score = self.importance_head(combined_features)
        
        # Quality score
        quality_score = self.quality_head(pooled_output)
        
        return {
            "embeddings": pooled_output,
            "aspect_sentiments": aspect_probs,
            "emotions": emotion_probs,
            "importance": importance_score,
            "quality": quality_score
        }


class DRLPolicyNetwork(nn.Module):
    """
    Policy network for Deep Reinforcement Learning agent
    Actions: [prioritize, filter, highlight, respond, ignore]
    """
    def __init__(self, state_dim: int = 768 + 5*3 + 8 + 2, action_dim: int = 5):
        super().__init__()
        
        self.shared_layers = nn.Sequential(
            nn.Linear(state_dim, 512),
            nn.ReLU(),
            nn.LayerNorm(512),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.LayerNorm(256)
        )
        
        # Policy head (action probabilities)
        self.policy_head = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Value head (state value estimation)
        self.value_head = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
        
        # Confidence head (uncertainty estimation)
        self.confidence_head = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.shared_layers(state)
        
        action_probs = self.policy_head(features)
        state_value = self.value_head(features)
        confidence = self.confidence_head(features)
        
        return action_probs, state_value, confidence
    
    def get_action(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[int, float]:
        with torch.no_grad():
            action_probs, _, confidence = self.forward(state)
            
            if deterministic:
                action = torch.argmax(action_probs).item()
            else:
                action = torch.multinomial(action_probs, 1).item()
            
            return action, confidence.item()


class CommentEnvironment:
    """
    Gym-like environment for DRL training
    """
    def __init__(self, comments_data: List[Dict]):
        self.comments = comments_data
        self.current_idx = 0
        self.state_dim = 768 + 15 + 8 + 2  # embedding + aspects + emotions + meta
        
    def reset(self):
        self.current_idx = 0
        return self._get_state(self.comments[0])
    
    def _get_state(self, comment: Dict) -> np.ndarray:
        # Combine all features into state vector
        embedding = np.array(comment.get("embedding", np.zeros(768)))
        aspects = np.array(comment.get("aspect_scores", np.zeros(15)))
        emotions = np.array(comment.get("emotion_scores", np.zeros(8)))
        meta = np.array([
            comment.get("length", 0) / 500,
            comment.get("likes", 0) / 1000
        ])
        
        return np.concatenate([embedding, aspects, emotions, meta])
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return (next_state, reward, done, info)
        Actions: 0=prioritize, 1=filter, 2=highlight, 3=respond, 4=ignore
        """
        current_comment = self.comments[self.current_idx]
        
        # Calculate reward based on action appropriateness
        reward = self._calculate_reward(action, current_comment)
        
        self.current_idx += 1
        done = self.current_idx >= len(self.comments)
        
        next_state = (self._get_state(self.comments[self.current_idx]) 
                   if not done else np.zeros(self.state_dim))
        
        info = {
            "comment_id": current_comment.get("id"),
            "action_taken": action,
            "confidence": current_comment.get("confidence", 0)
        }
        
        return next_state, reward, done, info
    
    def _calculate_reward(self, action: int, comment: Dict) -> float:
        """
        Reward shaping based on action quality
        """
        sentiment = comment.get("sentiment")
        confidence = comment.get("confidence", 0.5)
        importance = comment.get("importance_score", 0.5)
        
        reward = 0.0
        
        # Prioritize important negative comments
        if action == 0 and sentiment == "negative" and importance > 0.7:
            reward = 2.0
        elif action == 0 and importance > 0.8:
            reward = 1.5
            
        # Filter spam/low quality
        elif action == 1 and comment.get("quality_score", 1) < 0.3:
            reward = 1.0
            
        # Highlight positive feedback
        elif action == 2 and sentiment == "positive" and confidence > 0.8:
            reward = 1.5
            
        # Respond to complaints
        elif action == 3 and sentiment == "negative" and "complaint" in str(comment.get("aspects", {})):
            reward = 2.5
            
        # Ignore neutral/low impact
        elif action == 4 and sentiment == "neutral" and importance < 0.4:
            reward = 0.5
            
        else:
            reward = -0.5  # Penalize inappropriate actions
        
        # Scale by confidence
        return reward * confidence