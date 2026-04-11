# backend/app/services/analyzer.py
import os
import httpx
import json
import asyncio
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY_DRL")
        if not self.api_key:
            raise ValueError("Thiếu GROQ_API_KEY_DRL trên Render Environment Variables")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
   
    async def analyze_one(self, text: str) -> Dict:
        prompt = f"""Phân tích sentiment bình luận tiếng Việt:
"{text}"

Trả về JSON: {{"sentiment": "positive|negative|neutral", "confidence": 0.85, "reason": "giải thích ngắn gọn"}}

Quy tắc:
- positive: hài lòng, khen, recommend, tốt, đẹp, nhanh, tuyệt
- negative: phàn nàn, chê, tệ, chậm, hỏng, thất vọng, lỗi
- neutral: hỏi giá, cảm ơn, tạm được, không rõ

Chỉ trả về JSON, không thêm text nào khác."""

        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 120,
                    "response_format": {"type": "json_object"}
                }
            )
            resp.raise_for_status()
            
            content = resp.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
            
            sentiment = result.get("sentiment", "neutral")
            if sentiment not in ["positive", "negative", "neutral"]:
                sentiment = "neutral"
            
            return {
                "text": text,
                "sentiment": sentiment,
                "confidence": float(result.get("confidence", 0.5)),
                "reason": result.get("reason", "")
            }
   
    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Phân tích batch comment - có bảo vệ lỗi"""
        if not isinstance(texts, list):
            logger.error(f"analyze_batch nhận sai kiểu dữ liệu: {type(texts)}")
            texts = [texts] if texts else []
        
        if not texts:
            return []
            
        semaphore = asyncio.Semaphore(5)
       
        async def process(text):
            async with semaphore:
                try:
                    return await self.analyze_one(text)
                except Exception as e:
                    logger.error(f"Lỗi phân tích sentiment: {e}")
                    return {
                        "text": text,
                        "sentiment": "neutral",
                        "confidence": 0.0,
                        "reason": f"Lỗi API: {str(e)[:100]}"
                    }
       
        tasks = [process(t) for t in texts]
        return await asyncio.gather(*tasks)


# Khởi tạo instance
analyzer = SentimentAnalyzer()
