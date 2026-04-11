import functools
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Giới hạn thread
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

# MODEL SENTIMENT CHUYÊN DỤNG - Đã fine-tune cho 3 lớp: negative, neutral, positive
# Option 1: Model nhẹ nhất (~66MB) - DistilBERT fine-tune sentiment
MODEL_NAME = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"

# Option 2: Model chuẩn hơn nhưng nặng hơn (~500MB)
# MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# Option 3: Model tiếng Việt tốt nhất (~1.2GB)
# MODEL_NAME = "vinai/phobert-base-v2"  # Cần thêm classifier head

# Mapping labels cho model "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
LABEL_MAPPING = {
    0: "negative",  # Tiêu cực
    1: "neutral",   # Trung lập  
    2: "positive"   # Tích cực
}

@functools.lru_cache(maxsize=1)
def get_model():
    """Lazy load - chỉ chạy khi có request đầu tiên"""
    print(f"🤖 Loading sentiment model: {MODEL_NAME}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        device_map="cpu"
    )
    model.eval()
    
    print("✅ Sentiment model loaded")
    return tokenizer, model

class SentimentAnalyzer:
    def __init__(self):
        self._tokenizer = None
        self._model = None
    
    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self._tokenizer, self._model = get_model()
        return self._tokenizer
    
    @property  
    def model(self):
        if self._model is None:
            self._tokenizer, self._model = get_model()
        return self._model
    
    def analyze(self, text: str):
        """
        Phân tích sentiment của 1 bình luận
        Trả về: dict với sentiment và confidence
        """
        if not text or not text.strip():
            return {"sentiment": "neutral", "confidence": 0.0, "text": text}
        
        # Tokenize
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512,
            padding=True
        )
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()
        
        sentiment = LABEL_MAPPING.get(predicted_class, "neutral")
        
        return {
            "text": text,
            "sentiment": sentiment,  # "positive", "negative", "neutral"
            "confidence": round(confidence, 4),
            "probabilities": {
                "negative": round(probabilities[0][0].item(), 4),
                "neutral": round(probabilities[0][1].item(), 4),
                "positive": round(probabilities[0][2].item(), 4)
            }
        }
    
    def analyze_batch(self, texts: list):
        """
        Phân tích nhiều bình luận cùng lúc
        """
        results = []
        for text in texts:
            try:
                result = self.analyze(text)
                results.append(result)
            except Exception as e:
                print(f"❌ Error analyzing text: {e}")
                results.append({
                    "text": text,
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "error": str(e)
                })
        return results
