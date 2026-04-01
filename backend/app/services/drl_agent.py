import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any
import random
from transformers import AutoTokenizer, AutoModel

class DRLActionAgent:
    """
    Deep Reinforcement Learning Agent cho Sentiment Analysis
    Actions: prioritize, respond, highlight, filter, ignore
    """
    
    ACTIONS = ["prioritize", "respond", "highlight", "filter", "ignore"]
    
    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load embedding model
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        self.text_encoder = AutoModel.from_pretrained("vinai/phobert-base").to(self.device)
        self.text_encoder.eval()
        
        # Policy Network (Actor-Critic)
        self.state_dim = 768 + 10  # embedding + features
        self.action_dim = len(self.ACTIONS)
        
        self.policy_net = self._build_network().to(self.device)
        
        # Load pretrained weights nếu có
        if model_path:
            self.policy_net.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.policy_net.eval()
        
        # Response templates
        self.response_templates = {
            "negative_complaint": [
                "Cảm ơn bạn đã chia sẻ. Chúng tôi rất tiếc về trải nghiệm này và sẽ cải thiện ngay.",
                "Xin lỗi vì sự bất tiện. Đội ngũ CSKH sẽ liên hệ hỗ trợ bạn sớm nhất.",
            ],
            "positive_feedback": [
                "Cảm ơn bạn rất nhiều! Chúng tôi rất vui khi nhận được phản hồi tích cực.",
                "Cảm ơn sự ủng hộ của bạn! Hy vọng tiếp tục đồng hành cùng bạn.",
            ],
            "question": [
                "Cảm ơn câu hỏi của bạn. Chúng tôi sẽ phản hồi chi tiết trong thời gian sớm nhất.",
            ]
        }
    
    def _build_network(self):
        """Xây dựng Policy Network"""
        return nn.Sequential(
            nn.Linear(self.state_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_dim),
            nn.Softmax(dim=-1)
        )
    
    def _encode_text(self, text: str) -> torch.Tensor:
        """Encode text thành vector"""
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=256,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.text_encoder(**inputs)
            # Lấy [CLS] token embedding
            embedding = outputs.last_hidden_state[:, 0, :]
        
        return embedding.squeeze()
    
    def _extract_features(self, sentiment: str, confidence: float, 
                         likes: int, aspects: Dict) -> torch.Tensor:
        """Trích xuất đặc trưng số"""
        features = []
        
        # Sentiment one-hot
        sentiment_map = {"positive": [1, 0, 0], "neutral": [0, 1, 0], "negative": [0, 0, 1]}
        features.extend(sentiment_map.get(sentiment, [0, 1, 0]))
        
        # Confidence
        features.append(confidence)
        
        # Likes (normalized)
        features.append(min(likes / 1000, 1.0))
        
        # Aspect scores
        aspect_positive = sum(1 for a in aspects.values() if a.get("dominant") == "positive")
        aspect_negative = sum(1 for a in aspects.values() if a.get("dominant") == "negative")
        features.extend([
            aspect_positive / max(len(aspects), 1),
            aspect_negative / max(len(aspects), 1),
            len(aspects) / 10  # normalized
        ])
        
        # Urgency indicators
        urgent_words = ["gấp", "khẩn", "ngay", "lỗi", "hỏng", "khiếu nại", "tệ"]
        text_lower = str(aspects).lower()
        urgency_score = sum(1 for word in urgent_words if word in text_lower) / len(urgent_words)
        features.append(urgency_score)
        
        return torch.tensor(features, dtype=torch.float32).to(self.device)
    
    def predict_action(self, comment_text: str, sentiment: str, 
                       confidence: float, likes: int, aspects: Dict) -> Dict[str, Any]:
        """Dự đoán hành động tối ưu cho bình luận"""
        
        # Encode state
        text_embedding = self._encode_text(comment_text)
        features = self._extract_features(sentiment, confidence, likes, aspects)
        state = torch.cat([text_embedding, features])
        
        # Get action probabilities
        with torch.no_grad():
            action_probs = self.policy_net(state.unsqueeze(0))
            action_idx = torch.argmax(action_probs).item()
            action_confidence = action_probs[0][action_idx].item()
        
        action = self.ACTIONS[action_idx]
        
        # Tính importance score
        importance_score = self._calculate_importance(
            sentiment, confidence, likes, action
        )
        
        # Generate suggested response nếu cần
        suggested_response = None
        if action in ["respond", "prioritize"]:
            suggested_response = self._generate_response(comment_text, sentiment, aspects)
        
        return {
            "action": action,
            "confidence": action_confidence,
            "importance_score": importance_score,
            "requires_action": action in ["prioritize", "respond"],
            "action_probs": {a: p for a, p in zip(self.ACTIONS, action_probs[0].tolist())},
            "suggested_response": suggested_response
        }
    
    def _calculate_importance(self, sentiment: str, confidence: float, 
                              likes: int, action: str) -> float:
        """Tính điểm quan trọng của bình luận"""
        score = 0.0
        
        # Sentiment weight
        if sentiment == "negative":
            score += 0.4
        elif sentiment == "positive":
            score += 0.2
        
        # Confidence weight
        score += confidence * 0.2
        
        # Engagement weight
        score += min(likes / 100, 0.2)
        
        # Action weight
        action_weights = {
            "prioritize": 1.0,
            "respond": 0.8,
            "highlight": 0.6,
            "filter": 0.3,
            "ignore": 0.1
        }
        score += action_weights.get(action, 0.1) * 0.2
        
        return min(score, 1.0)
    
    def _generate_response(self, text: str, sentiment: str, aspects: Dict) -> str:
        """Tạo gợi ý phản hồi dựa trên context"""
        text_lower = text.lower()
        
        # Xác định loại phản hồi
        if sentiment == "negative":
            if any(word in text_lower for word in ["lỗi", "hỏng", "kém", "tệ"]):
                return random.choice(self.response_templates["negative_complaint"])
        
        elif sentiment == "positive":
            return random.choice(self.response_templates["positive_feedback"])
        
        elif "?" in text or "hỏi" in text_lower:
            return random.choice(self.response_templates["question"])
        
        return "Cảm ơn bạn đã chia sẻ ý kiến!"
    
    def train_step(self, state, action, reward, next_state, done):
        """Training step cho DRL (sử dụng PPO hoặc DQN)"""
        # Implementation cho việc training online learning
        pass

class PPOTrainer:
    """Proximal Policy Optimization cho training DRL Agent"""
    
    def __init__(self, agent: DRLActionAgent):
        self.agent = agent
        self.optimizer = torch.optim.Adam(agent.policy_net.parameters(), lr=3e-4)
        self.gamma = 0.99  # discount factor
        self.epsilon = 0.2  # PPO clip parameter
        
    def compute_advantages(self, rewards, values, dones):
        """Tính advantage function"""
        advantages = []
        gae = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
            
            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * 0.95 * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        return torch.tensor(advantages)
    
    def update_policy(self, states, actions, old_probs, advantages, returns):
        """Cập nhật policy network"""
        # Forward pass
        new_probs = self.agent.policy_net(states)
        dist = torch.distributions.Categorical(new_probs)
        
        # Ratio for PPO
        ratio = torch.exp(dist.log_prob(actions) - old_probs)
        
        # Clipped surrogate objective
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
        actor_loss = -torch.min(surr1, surr2).mean()
        
        # Critic loss (value function)
        # ... implementation
        
        # Total loss
        loss = actor_loss
        
        # Backprop
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
