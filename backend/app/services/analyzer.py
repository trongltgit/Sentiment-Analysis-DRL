import os
import httpx
import json
import asyncio
from typing import List, Dict

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY+DRL")
        if not self.api_key:
            raise ValueError("Thiếu GROQ_API_KEY_DRL")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def analyze_one(self, text: str) -> Dict:
        prompt = f"""Phân tích sentiment bình luận tiếng Việt:

"{text}"

Trả về JSON: {{"sentiment": "positive|negative|neutral", "confidence": 0.0-1.0, "reason": "giải thích ngắn"}}

Quy tắc:
- positive: Hài lòng, khen, recommend, tốt, đẹp, nhanh
- negative: Phàn nàn, chê, tệ, chậm, hỏng, thất vọng
- neutral: Hỏi giá, cảm ơn, tạm được, không rõ

Chỉ trả JSON:"""

        async with httpx.AsyncClient(timeout=30) as client:
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
                    "max_tokens": 100,
                    "response_format": {"type": "json_object"}
                }
            )
            
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
        semaphore = asyncio.Semaphore(5)
        
        async def process(text):
            async with semaphore:
                try:
                    return await self.analyze_one(text)
                except Exception as e:
                    print(f"⚠️ Lỗi: {e}")
                    return {
                        "text": text,
                        "sentiment": "neutral",
                        "confidence": 0,
                        "reason": "Lỗi API"
                    }
        
        tasks = [process(t) for t in texts]
        return await asyncio.gather(*tasks)

analyzer = SentimentAnalyzer()
