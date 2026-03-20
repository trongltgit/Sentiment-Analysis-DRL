"""
Sentiment Analysis Service using Deep Learning
"""
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Optional
import numpy as np
import re
import asyncio
from collections import Counter

from ..models.sentiment_model import SentimentFeatureExtractor


class SentimentAnalyzer:
    """
    Multi-aspect sentiment analysis with Vietnamese language support
    """
    
    def __init__(self, model_name: str = "vinai/phobert-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load tokenizer and base model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.feature_extractor = SentimentFeatureExtractor(model_name).to(self.device)
        
        # Aspect definitions
        self.aspects = ["quality", "service", "price", "delivery", "overall"]
        self.emotions = ["joy", "sadness", "anger", "fear", "surprise", 
                        "disgust", "trust", "anticipation"]
        
        self.max_length = 256
    
    async def analyze_batch(self, comments: List[Dict], 
                           depth: str = "standard") -> List[Dict]:
        """
        Analyze batch of comments with specified depth
        """
        results = []
        
        for comment in comments:
            analysis = await self._analyze_single(comment, depth)
            results.append(analysis)
            
            # Small delay to prevent overwhelming
            if len(comments) > 50:
                await asyncio.sleep(0.01)
        
        return results
    
    async def _analyze_single(self, comment: Dict, depth: str) -> Dict:
        """
        Deep analysis of single comment
        """
        text = comment.get("text", "")
        cleaned_text = self._preprocess_text(text)
        
        # Tokenize
        inputs = self.tokenizer(
            cleaned_text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.max_length
        ).to(self.device)
        
        with torch.no_grad():
            features = self.feature_extractor(
                inputs["input_ids"], 
                inputs["attention_mask"]
            )
        
        # Extract predictions
        aspect_sentiments = self._process_aspects(features["aspect_sentiments"])
        emotion_scores = features["emotions"].squeeze().cpu().numpy()
        importance = features["importance"].item()
        quality = features["quality"].item()
        
        # Determine overall sentiment
        overall_sentiment = self._determine_overall_sentiment(aspect_sentiments)
        
        # Generate embeddings for DRL
        embeddings = features["embeddings"].squeeze().cpu().numpy().tolist()
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(cleaned_text) if depth == "deep" else []
        
        return {
            **comment,
            "cleaned_text": cleaned_text,
            "sentiment": overall_sentiment["label"],
            "confidence": overall_sentiment["confidence"],
            "aspects": aspect_sentiments,
            "aspect_scores": self._flatten_aspect_scores(aspect_sentiments),
            "emotions": {emo: float(score) for emo, score in zip(self.emotions, emotion_scores)},
            "emotion_scores": emotion_scores.tolist(),
            "importance_score": importance,
            "quality_score": quality,
            "key_phrases": key_phrases,
            "embedding": embeddings[:768],  # Truncate for efficiency
            "requires_action": importance > 0.7 and overall_sentiment["label"] == "negative",
            "suggested_response": self._generate_response(overall_sentiment["label"], aspect_sentiments) if importance > 0.6 else None
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove special characters but keep Vietnamese diacritics
        text = re.sub(r'[^\w\sđĐáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.lower().strip()
    
    def _process_aspects(self, aspect_logits: List[torch.Tensor]) -> Dict:
        """Process aspect sentiment predictions"""
        results = {}
        for i, aspect in enumerate(self.aspects):
            probs = aspect_logits[i].squeeze().cpu().numpy()
            results[aspect] = {
                "positive": float(probs[0]),
                "neutral": float(probs[1]),
                "negative": float(probs[2]),
                "dominant": ["positive", "neutral", "negative"][np.argmax(probs)]
            }
        return results
    
    def _flatten_aspect_scores(self, aspects: Dict) -> List[float]:
        """Flatten aspect scores for state representation"""
        scores = []
        for aspect in self.aspects:
            scores.extend([
                aspects[aspect]["positive"],
                aspects[aspect]["neutral"],
                aspects[aspect]["negative"]
            ])
        return scores
    
    def _determine_overall_sentiment(self, aspects: Dict) -> Dict:
        """Calculate weighted overall sentiment"""
        weights = {"quality": 0.3, "service": 0.25, "price": 0.2, 
                  "delivery": 0.15, "overall": 0.1}
        
        pos_score = sum(aspects[a]["positive"] * w for a, w in weights.items())
        neg_score = sum(aspects[a]["negative"] * w for a, w in weights.items())
        neu_score = sum(aspects[a]["neutral"] * w for a, w in weights.items())
        
        scores = [pos_score, neu_score, neg_score]
        labels = ["positive", "neutral", "negative"]
        
        max_idx = np.argmax(scores)
        
        return {
            "label": labels[max_idx],
            "confidence": float(scores[max_idx]),
            "scores": {
                "positive": pos_score,
                "neutral": neu_score,
                "negative": neg_score
            }
        }
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract important phrases using simple heuristics"""
        # This could be enhanced with NER or dependency parsing
        words = text.split()
        phrases = []
        
        # Extract bigrams with sentiment words
        sentiment_indicators = ["tốt", "xấu", "tệ", "tuyệt vời", "kém", 
                               "giá", "chất lượng", "giao hàng", "phục vụ"]
        
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if any(ind in bigram for ind in sentiment_indicators):
                phrases.append(bigram)
        
        return list(set(phrases))[:5]
    
    def _generate_response(self, sentiment: str, aspects: Dict) -> Optional[str]:
        """Generate suggested response based on sentiment"""
        if sentiment == "negative":
            worst_aspect = min(aspects.items(), 
                             key=lambda x: x[1]["negative"] - x[1]["positive"])[0]
            
            templates = {
                "quality": "Cảm ơn bạn đã phản hồi. Chúng tôi rất tiếc về vấn đề chất lượng. Đội ngũ CSKH sẽ liên hệ ngay để hỗ trợ.",
                "service": "Chúng tôi xin lỗi về trải nghiệm dịch vụ của bạn. Chúng tôi sẽ cải thiện ngay lập tức.",
                "price": "Cảm ơn góp ý về giá cả. Chúng tôi luôn cố gắng cân bằng giá trị và chi phí.",
                "delivery": "Rất tiếc về sự cố giao hàng. Chúng tôi sẽ kiểm tra và đẩy nhanh đơn hàng của bạn.",
                "overall": "Cảm ơn bạn đã chia sẻ. Chúng tôi rất tiếc và sẽ liên hệ để khắc phục sớm nhất."
            }
            return templates.get(worst_aspect, templates["overall"])
        
        elif sentiment == "positive":
            return "Cảm ơn bạn rất nhiều về phản hồi tích cực! Chúng tôi rất vui khi bạn hài lòng với sản phẩm/dịch vụ."
        
        return None
    
    def generate_summary(self, analyzed_comments: List[Dict]) -> Dict:
        """Generate overall summary of analyzed comments"""
        total = len(analyzed_comments)
        if total == 0:
            return {}
        
        # Sentiment distribution
        sentiments = [c["sentiment"] for c in analyzed_comments]
        sentiment_dist = dict(Counter(sentiments))
        
        # Average metrics
        avg_confidence = np.mean([c["confidence"] for c in analyzed_comments])
        avg_importance = np.mean([c["importance_score"] for c in analyzed_comments])
        
        # Top aspects mentioned
        aspect_counts = Counter()
        for comment in analyzed_comments:
            for aspect, scores in comment.get("aspects", {}).items():
                if scores["dominant"] != "neutral":
                    aspect_counts[aspect] += 1
        
        # Risk factors
        risk_factors = []
        negative_rate = sentiment_dist.get("negative", 0) / total
        if negative_rate > 0.3:
            risk_factors.append(f"Cao điểm phản hồi tiêu cực ({negative_rate:.1%})")
        
        high_importance_neg = [c for c in analyzed_comments 
                              if c["sentiment"] == "negative" and c["importance_score"] > 0.8]
        if len(high_importance_neg) > 3:
            risk_factors.append(f"Có {len(high_importance_neg)} phản hồi tiêu cực quan trọng cần xử lý ngay")
        
        # Recommendations
        recommendations = []
        if negative_rate > 0.2:
            recommendations.append("Ưu tiên phản hồi các bình luận tiêu cực trong 2 giờ")
        if aspect_counts.get("quality", 0) > total * 0.15:
            recommendations.append("Kiểm tra lại quy trình kiểm soát chất lượng sản phẩm")
        if aspect_counts.get("delivery", 0) > total * 0.15:
            recommendations.append("Đánh giá lại đối tác vận chuyển")
        
        return {
            "total_comments": total,
            "sentiment_distribution": sentiment_dist,
            "average_confidence": float(avg_confidence),
            "average_importance": float(avg_importance),
            "key_topics": [asp for asp, _ in aspect_counts.most_common(3)],
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "trend_analysis": {
                "dominant_sentiment": max(set(sentiments), key=sentiments.count),
                "engagement_level": "high" if avg_importance > 0.6 else "medium" if avg_importance > 0.4 else "low"
            }
        }