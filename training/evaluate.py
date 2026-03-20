"""
Evaluation script for trained DRL Agent
"""
import torch
import numpy as np
import json
from collections import defaultdict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.models.sentiment_model import DRLPolicyNetwork, CommentEnvironment
from backend.app.services.analyzer import SentimentAnalyzer


class DRLEvaluator:
    """
    Comprehensive evaluation of DRL agent performance
    """
    
    def __init__(self, checkpoint_path='models/drl_checkpoint_final.pt'):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model
        self.policy_net = DRLPolicyNetwork().to(self.device)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_state_dict'])
        self.policy_net.eval()
        
        self.analyzer = SentimentAnalyzer()
    
    async def evaluate_on_dataset(self, test_data):
        """
        Evaluate agent on test dataset
        """
        processed_data = []
        for item in test_data:
            analysis = await self.analyzer._analyze_single(item, 'standard')
            processed_data.append(analysis)
        
        env = CommentEnvironment(processed_data)
        
        results = {
            'total_comments': len(processed_data),
            'actions_taken': defaultdict(int),
            'sentiment_distribution': defaultdict(int),
            'action_by_sentiment': defaultdict(lambda: defaultdict(int)),
            'rewards': [],
            'confidences': []
        }
        
        state = env.reset()
        done = False
        
        while not done:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                action_probs, _, confidence = self.policy_net(state_tensor)
                action = torch.argmax(action_probs).item()
            
            next_state, reward, done, info = env.step(action)
            
            current_comment = processed_data[len(results['rewards'])]
            
            # Record metrics
            results['actions_taken'][action] += 1
            results['sentiment_distribution'][current_comment['sentiment']] += 1
            results['action_by_sentiment'][current_comment['sentiment']][action] += 1
            results['rewards'].append(reward)
            results['confidences'].append(confidence.item())
            
            state = next_state
        
        # Calculate metrics
        metrics = {
            'total_reward': sum(results['rewards']),
            'average_reward': np.mean(results['rewards']),
            'average_confidence': np.mean(results['confidences']),
            'action_distribution': dict(results['actions_taken']),
            'action_accuracy': self._calculate_action_accuracy(results),
            'efficiency_score': self._calculate_efficiency(results)
        }
        
        return metrics, results
    
    def _calculate_action_accuracy(self, results):
        """
        Calculate how appropriate actions were
        """
        correct = 0
        total = len(results['rewards'])
        
        for reward in results['rewards']:
            if reward > 0:
                correct += 1
        
        return correct / total if total > 0 else 0
    
    def _calculate_efficiency(self, results):
        """
        Calculate efficiency metric
        """
        # Reward high confidence and positive rewards
        confidence_bonus = np.mean(results['confidences'])
        reward_rate = sum(1 for r in results['rewards'] if r > 0) / len(results['rewards'])
        
        return (confidence_bonus + reward_rate) / 2
    
    def generate_report(self, metrics, results):
        """
        Generate detailed evaluation report
        """
        report = {
            'timestamp': str(datetime.now()),
            'metrics': metrics,
            'action_labels': {
                0: 'prioritize',
                1: 'filter', 
                2: 'highlight',
                3: 'respond',
                4: 'ignore'
            },
            'recommendations': []
        }
        
        # Generate recommendations
        if metrics['action_accuracy'] < 0.7:
            report['recommendations'].append(
                "Action accuracy below 70%. Consider more training on edge cases."
            )
        
        if metrics['average_confidence'] < 0.8:
            report['recommendations'].append(
                "Low average confidence. Model may need more diverse training data."
            )
        
        # Save report
        with open('evaluation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report


async def main():
    evaluator = DRLEvaluator()
    
    # Generate test data
    test_data = [
        {'text': 'Sản phẩm tuyệt vời!', 'sentiment': 'positive', 'likes': 50},
        {'text': 'Dịch vụ quá tệ', 'sentiment': 'negative', 'likes': 5},
        {'text': 'Bình thường', 'sentiment': 'neutral', 'likes': 10},
        # Add more test cases...
    ]
    
    metrics, results = await evaluator.evaluate_on_dataset(test_data)
    
    print("📊 Evaluation Results:")
    print(f"Total Reward: {metrics['total_reward']:.2f}")
    print(f"Average Reward: {metrics['average_reward']:.2f}")
    print(f"Action Accuracy: {metrics['action_accuracy']:.2%}")
    print(f"Average Confidence: {metrics['average_confidence']:.2%}")
    print(f"Efficiency Score: {metrics['efficiency_score']:.2f}")


if __name__ == "__main__":
    from datetime import datetime
    import asyncio
    asyncio.run(main())