"""
Sentiment Analysis using PhoBERT
"""
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
        print(f"   Using device: {self.device}")
        
        # Load PhoBERT
        print("   Loading PhoBERT tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        
        print("   Loading PhoBERT model...")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "vinai/phobert-base",
            num_labels=3  # positive, neutral, negative
        ).to(self.device)
        self.model.eval()
        
        # Emotion classifier (optional, có thể skip nếu lỗi)
        try:
            print("   Loading emotion classifier...")
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if torch.cuda.is_available() else -1,
                top_k=None
            )
        except Exception as e:
            print(f"   Warning: Could not load emotion classifier: {e}")
            self.emotion_classifier = None
        
        # Aspect keywords
        self.aspect_keywords = {
            "chất_lượng": ["chất lượng", "bền", "tốt", "xấu", "kém", "tuyệt vời", "ổn", "đẹp", "tệ"],
            "dịch_vụ": ["dịch vụ", "chăm sóc", "hỗ trợ", "tư vấn", "phục vụ", "CSKH"],
            "giá_cả": ["giá", "đắt", "rẻ", "hợp lý", "chi phí", "tiền", "cost"],
            "giao_hàng": ["giao hàng", "ship", "vận chuyển", "giao nhanh", "chậm", "delivery"],
            "sản_phẩm": ["sản phẩm", "hàng", "món", "đồ", "mẫu mã", "item"],
            "nhân_viên": ["nhân viên", "thái độ", "nhiệt tình", "thân thiện", "staff"]
        }
        
        self.sentiment_labels = ["positive", "neutral", "negative"]
        print("   ✅ SentimentAnalyzer ready!")
    
    def clean_text(self, text: str) -> str:
        """Làm sạch văn bản"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove special chars nhưng giữ tiếng Việt
        text = re.sub(r'[^\w\sđĐáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]', '', text)
        # Normalize spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def analyze_aspects(self, text: str) -> Dict:
        """Phân tích sentiment theo từng khía cạnh"""
        text_lower = text.lower()
        aspects = {}
        
        for aspect, keywords in self.aspect_keywords.items():
            mentions = [kw for kw in keywords if kw in text_lower]
            
            if mentions:
                # Extract contexts
                contexts = []
                for keyword in mentions:
                    idx = text_lower.find(keyword)
                    start = max(0, idx - 50)
                    end = min(len(text), idx + 50)
                    contexts.append(text[start:end])
                
                # Analyze each context
                sentiments = []
                for ctx in contexts:
                    try:
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
                        
                        sentiments.append({
                            "label": self.sentiment_labels[pred],
                            "confidence": conf
                        })
                    except Exception as e:
                        continue
                
                if sentiments:
                    pos = sum(1 for s in sentiments if s["label"] == "positive")
                    neg = sum(1 for s in sentiments if s["label"] == "negative")
                    
                    dominant = "positive" if pos > neg else ("negative" if neg > pos else "neutral")
                    avg_conf = sum(s["confidence"] for s in sentiments) / len(sentiments)
                    
                    aspects[aspect] = {
                        "dominant": dominant,
                        "confidence": round(avg_conf, 3),
                        "mentions": len(mentions)
                    }
        
        return aspects
    
    def analyze_emotions(self, text: str) -> Dict[str, float]:
        """Phân tích cảm xúc chi tiết"""
        if not self.emotion_classifier:
            return {"neutral": 1.0}
        
        try:
            results = self.emotion_classifier(text[:512])
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list):
                    emotions = {r["label"]: r["score"] for r in results[0]}
                else:
                    emotions = {r["label"]: r["score"] for r in results}
                return emotions
            return {"neutral": 1.0}
        except Exception as e:
            return {"neutral": 1.0}
    
    def analyze(self, text: str, depth: str = "standard") -> Dict:
        """Phân tích tổng thể"""
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
        try:
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
        except Exception as e:
            return {
                "overall": "neutral",
                "confidence": 0.0,
                "cleaned_text": cleaned,
                "aspects": {},
                "emotions": {},
                "error": str(e)
            }
        
        overall = self.sentiment_labels[pred]
        
        result = {
            "overall": overall,
            "confidence": round(confidence, 3),
            "cleaned_text": cleaned,
            "raw_probs": {
                "positive": round(probs[0][0].item(), 3),
                "neutral": round(probs[0][1].item(), 3),
                "negative": round(probs[0][2].item(), 3)
            }
        }
        
        # Aspect analysis
        if depth in ["standard", "deep"]:
            result["aspects"] = self.analyze_aspects(cleaned)
        
        # Emotion analysis
        if depth == "deep":
            result["emotions"] = self.analyze_emotions(cleaned)
        
        return result
    
    async def analyze_batch_async(self, comments: List[Dict], depth: str = "standard") -> List[Dict]:
        """Phân tích batch comments (async version)"""
        results = []
        
        for i, comment in enumerate(comments):
            text = comment.get("text", "")
            if not text:
                continue
            
            # Analyze
            analysis = self.analyze(text, depth)
            
            # Merge with original data
            enriched = {
                **comment,
                "sentiment": analysis["overall"],
                "confidence": analysis["confidence"],
                "sentiment_probs": analysis.get("raw_probs", {}),
                "aspects": analysis.get("aspects", {}),
                "emotions": analysis.get("emotions") if depth == "deep" else None,
                "cleaned_text": analysis.get("cleaned_text", text)
            }
            
            results.append(enriched)
            
            # Log progress every 10 items
            if (i + 1) % 10 == 0:
                print(f"   Processed {i + 1}/{len(comments)} comments...")
        
        return results
