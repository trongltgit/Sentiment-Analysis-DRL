import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np
from typing import Dict, List
import re

class SentimentAnalyzer:
    """Phân tích sentiment đa chiều sử dụng PhoBERT và aspect-based analysis"""
    
    ASPECTS = ["chất_lượng", "dịch_vụ", "giá_cả", "giao_hàng", "sản_phẩm", "nhân_viên"]
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load PhoBERT cho sentiment classification
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "vinai/phobert-base",
            num_labels=3  # positive, neutral, negative
        ).to(self.device)
        
        # Emotion detection pipeline
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Aspect keywords
        self.aspect_keywords = {
            "chất_lượng": ["chất lượng", "bền", "tốt", "xấu", "kém", "tuyệt vời", "ổn"],
            "dịch_vụ": ["dịch vụ", "chăm sóc", "hỗ trợ", "tư vấn", "phục vụ"],
            "giá_cả": ["giá", "đắt", "rẻ", "hợp lý", "chi phí", "tiền"],
            "giao_hàng": ["giao hàng", "ship", "vận chuyển", "giao nhanh", "chậm"],
            "sản_phẩm": ["sản phẩm", "hàng", "món", "đồ", "mẫu mã"],
            "nhân_viên": ["nhân viên", "thái độ", "nhiệt tình", "thân thiện"]
        }
        
        self.sentiment_labels = ["positive", "neutral", "negative"]
    
    def clean_text(self, text: str) -> str:
        """Làm sạch văn bản"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove special characters nhưng giữ tiếng Việt
        text = re.sub(r'[^\w\sđĐáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]', '', text)
        # Normalize spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def analyze_aspects(self, text: str) -> Dict:
        """Phân tích sentiment theo từng khía cạnh"""
        text_lower = text.lower()
        aspects = {}
        
        for aspect, keywords in self.aspect_keywords.items():
            # Tìm mention của aspect
            mentions = [kw for kw in keywords if kw in text_lower]
            
            if mentions:
                # Trích xuất context xung quanh keyword
                contexts = []
                for keyword in mentions:
                    idx = text_lower.find(keyword)
                    start = max(0, idx - 50)
                    end = min(len(text), idx + 50)
                    contexts.append(text[start:end])
                
                # Phân tích sentiment cho context
                context_sentiments = []
                for ctx in contexts:
                    inputs = self.tokenizer(
                        ctx, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=128
                    ).to(self.device)
                    
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        probs = torch.softmax(outputs.logits, dim=-1)
                        pred = torch.argmax(probs, dim=-1).item()
                        conf = probs[0][pred].item()
                    
                    context_sentiments.append({
                        "label": self.sentiment_labels[pred],
                        "confidence": conf
                    })
                
                # Tổng hợp
                pos_count = sum(1 for s in context_sentiments if s["label"] == "positive")
                neg_count = sum(1 for s in context_sentiments if s["label"] == "negative")
                
                if pos_count > neg_count:
                    dominant = "positive"
                elif neg_count > pos_count:
                    dominant = "negative"
                else:
                    dominant = "neutral"
                
                avg_conf = sum(s["confidence"] for s in context_sentiments) / len(context_sentiments)
                
                aspects[aspect] = {
                    "dominant": dominant,
                    "confidence": avg_conf,
                    "mentions": len(mentions),
                    "details": context_sentiments
                }
        
        return aspects
    
    def analyze_emotions(self, text: str) -> Dict[str, float]:
        """Phân tích cảm xúc chi tiết"""
        try:
            results = self.emotion_classifier(text[:512])  # Limit length
            emotions = {r["label"]: r["score"] for r in results}
            return emotions
        except:
            # Fallback nếu model emotion không hoạt động
            return {
                "neutral": 0.7,
                "joy": 0.1,
                "anger": 0.1,
                "sadness": 0.1
            }
    
    def analyze(self, text: str, depth: str = "standard") -> Dict:
        """
        Phân tích tổng thể
        
        depth: 'basic', 'standard', 'deep'
        """
        cleaned = self.clean_text(text)
        
        if not cleaned:
            return {
                "overall": "neutral",
                "confidence": 0.0,
                "cleaned_text": "",
                "aspects": {},
                "emotions": {}
            }
        
        # Basic sentiment
        inputs = self.tokenizer(
            cleaned, 
            return_tensors="pt", 
            truncation=True, 
            max_length=256
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            pred = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][pred].item()
        
        overall = self.sentiment_labels[pred]
        
        result = {
            "overall": overall,
            "confidence": confidence,
            "cleaned_text": cleaned,
            "raw_probs": {
                "positive": probs[0][0].item(),
                "neutral": probs[0][1].item(),
                "negative": probs[0][2].item()
            }
        }
        
        # Aspect analysis (standard và deep)
        if depth in ["standard", "deep"]:
            result["aspects"] = self.analyze_aspects(cleaned)
        
        # Emotion analysis (chỉ deep)
        if depth == "deep":
            result["emotions"] = self.analyze_emotions(cleaned)
        
        return result
    
    def batch_analyze(self, texts: List[str], depth: str = "standard", batch_size: int = 32):
        """Phân tích batch cho hiệu suất cao hơn"""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = [self.analyze(t, depth) for t in batch]
            results.extend(batch_results)
        return results
