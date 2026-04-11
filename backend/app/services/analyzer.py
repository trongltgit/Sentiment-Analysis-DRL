import functools
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Giới hạn thread ngay từ đầu
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

# Model nhỏ hơn cho sentiment (distilled)
MODEL_NAME = "distilbert-base-multilingual-cased"  # Hoặc model sentiment cụ thể

@functools.lru_cache(maxsize=1)
def get_model():
    """Lazy load - chỉ chạy khi có request đầu tiên"""
    print("🤖 Loading sentiment model (first time)...")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,  # Hoặc float16 nếu cần
        low_cpu_mem_usage=True,
        device_map="cpu"
    )
    model.eval()  # Chế độ inference tiết kiệm RAM
    
    print("✅ Model loaded")
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
        # Model sẽ load lần đầu ở đây
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # ... xử lý kết quả ...
