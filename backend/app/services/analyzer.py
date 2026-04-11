"""
Sentiment Analysis using PhoBERT - Tối ưu cho 3 nhóm: good/bad/neutral
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import Dict, List
import re
import logging

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Phân tích sentiment đa chiều với PhoBERT"""
    
    ASPECTS = ["chất_lượng", "dịch_vụ", "giá_cả", "giao_hàng", "sản_phẩm", "nhân_viên"]
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load PhoBERT
        logger.info("Loading PhoBERT...")
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "vinai/phobert-base",
            num_labels=3
        ).to(self.device)
        self.model.eval()
        
        # Aspect keywords
        self.aspect_keywords = {
            "chất_lượng": ["chất lượng", "bền", "tốt", "xấu", "kém", "tuyệt vời", "ổn", "đẹp", "tệ", "hỏng"],
            "dịch_vụ": ["dịch vụ", "chăm sóc", "hỗ trợ", "tư vấn", "phục vụ", "CSKH", "nhân viên"],
            "giá_cả": ["giá", "đắt", "rẻ", "hợp lý", "chi phí", "tiền", "cost", "đáng tiền"],
            "giao_hàng": ["giao hàng", "ship", "vận chuyển", "nhanh", "chậm", "delivery", "đóng gói"],
            "sản_phẩm": ["sản phẩm", "hàng", "món", "đồ", "mẫu mã", "item", "packaging"],
            "nhân_viên": ["nhân viên", "thái độ", "nhiệt tình", "thân thiện", "staff", "tư vấn viên"]
        }
        
        self.sentiment_labels = ["positive", "neutral", "negative"]
        logger.info("✅ Analyzer ready!")
    
    def clean_text(self, text: str) -> str:
        """Làm sạch văn bản"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Giữ tiếng Việt, remove special chars
        text = re.sub(r'[^\w\sđĐáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]', '', text)
        # Normalize spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def analyze_aspects(self, text: str) -> Dict:
        """Phân tích aspect-based sentiment"""
        text_lower = text.lower()
        aspects = {}
        
        for aspect, keywords in self.aspect_keywords.items():
            mentions = [kw for kw in keywords if kw in text_lower]
            
            if mentions:
                # Simple sentiment for aspect
                pos = sum(1 for m in mentions if m in ["tốt", "đẹp", "nhanh", "rẻ", "hợp lý", "nhiệt tình"])
                neg = sum(1 for m in mentions if m in ["kém", "xấu", "chậm", "đắt", "tệ", "hỏng"])
                
                if pos > neg:
                    dominant = "positive"
                elif neg > pos:
                    dominant = "negative"
                else:
                    dominant = "neutral"
                
                aspects[aspect] = {
                    "sentiment": dominant,
                    "mentions": len(mentions)
                }
        
        return aspects
    
    def analyze(self, text: str, depth: str = "standard") -> Dict:
        """Phân tích tổng thể"""
        cleaned = self.clean_text(text)
        
        if not cleaned or len(cleaned) < 5:
            return {
                "overall": "neutral",
                "confidence": 0.5,
                "cleaned_text": cleaned,
                "aspects": {}
            }
        
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
            logger.error(f"Analysis error: {e}")
            return {
                "overall": "neutral",
                "confidence": 0.5,
                "cleaned_text": cleaned,
                "aspects": {},
                "error": str(e)
            }
        
        overall = self.sentiment_labels[pred]
        
        result = {
            "overall": overall,
            "confidence": round(confidence, 3),
            "cleaned_text": cleaned,
            "probs": {
                "positive": round(probs[0][0].item(), 3),
                "neutral": round(probs[0][1].item(), 3),
                "negative": round(probs[0][2].item(), 3)
            }
        }
        
        if depth in ["standard", "deep"]:
            result["aspects"] = self.analyze_aspects(cleaned)
        
        return result
    
    async def analyze_batch_async(self, comments: List[Dict], depth: str = "standard") -> List[Dict]:
        """Phân tích batch với progress log"""
        results = []
        total = len(comments)
        
        for i, comment in enumerate(comments):
            text = comment.get("text", "")
            
            analysis = self.analyze(text, depth)
            
            # Merge với data gốc
            enriched = {
                **comment,
                "sentiment": analysis["overall"],
                "confidence": analysis["confidence"],
                "sentiment_probs": analysis.get("probs", {}),
                "aspects": analysis.get("aspects", {}),
                "cleaned_text": analysis.get("cleaned_text", text)
            }
            
            results.append(enriched)
            
            # Log progress
            if (i + 1) % 20 == 0 or (i + 1) == total:
                logger.info(f"   Analyzed {i + 1}/{total} comments...")
        
        return results


# Singleton
analyzer = SentimentAnalyzer()
