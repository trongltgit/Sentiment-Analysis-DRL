# backend/app/services/analyzer.py
import os
import httpx
import json
import asyncio
from typing import List, Dict

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Thiếu GROQ_API_KEY - đăng ký free tại console.groq.com")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def analyze_one(self, text: str) -> Dict:
        """Phân tích chính xác bằng LLM"""
        
        prompt = f"""Phân tích sentiment bình luận tiếng Việt sau đây một cách chính xác.

Bình luận: "{text}"

Phân loại:
- **positive**: Khách hàng hài lòng, khen, recommend, có ý định mua lại, từ tích cực (tuyệt vời, xuất sắc, đáng tiền, chất lượng, nhanh, đẹp)
- **negative**: Phàn nàn, chê, khiếu nại, từ tiêu cực (tệ, chậm, hỏng, lừa đảo, thất vọng, kém)
- **neutral**: Hỏi giá, cảm ơn đơn thuần, không rõ ràng, tạm được, bình thường

Trả về JSON:
{{"sentiment": "positive|negative|neutral", "confidence": 0.0-1.0, "reason": "giải thích ngắn gọn 2-4 từ"}}

Chỉ trả JSON, không thêm text:"""

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):  # Retry 3 lần
                try:
                    resp = await client.post(
                        self.url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.05,  # Ít random nhất
                            "max_tokens": 100,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    
                    if resp.status_code == 429:  # Rate limit
                        await asyncio.sleep(2 ** attempt)
                        continue
                    
                    content = resp.json()["choices"][0]["message"]["content"]
                    result = json.loads(content)
                    
                    sentiment = result.get("sentiment", "neutral")
                    # Validate
                    if sentiment not in ["positive", "negative", "neutral"]:
                        sentiment = "neutral"
                    
                    return {
                        "text": text,
                        "sentiment": sentiment,
                        "confidence": float(result.get("confidence", 0.5)),
                        "reason": result.get("reason", "")[:50]
                    }
                    
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    await asyncio.sleep(1)
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Phân tích nhiều bình luận"""
        
        # Giới hạn 5 concurrent để tránh rate limit Groq free
        semaphore = asyncio.Semaphore(5)
        
        async def process(text):
            async with semaphore:
                try:
                    return await self.analyze_one(text)
                except Exception as e:
                    print(f"⚠️ Lỗi phân tích: {e}")
                    return {
                        "text": text,
                        "sentiment": "neutral",
                        "confidence": 0,
                        "reason": "Lỗi API"
                    }
        
        tasks = [process(t) for t in texts]
        return await asyncio.gather(*tasks)

analyzer = SentimentAnalyzer()
