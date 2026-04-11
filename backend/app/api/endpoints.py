# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import asyncio

from app.services.crawler import crawler
from app.services.analyzer import analyzer  # AI model phân loại

router = APIRouter()

class AnalyzeRequest(BaseModel):
    url: str

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    total_comments: int
    statistics: dict
    comments: List[dict]

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_url(request: AnalyzeRequest):
    try:
        # 1. CRAWL THẬT - không còn giả lập
        print(f"🔍 Đang crawl thật: {request.url}")
        crawl_result = await crawler.crawl(request.url, max_comments=50)
        
        raw_comments = [c["text"] for c in crawl_result["comments"]]
        
        if not raw_comments:
            return {
                "id": str(uuid.uuid4()),
                "url": request.url,
                "status": "completed",
                "total_comments": 0,
                "statistics": {
                    "positive": 0, "negative": 0, "neutral": 0,
                    "positive_percent": 0, "negative_percent": 0, "neutral_percent": 0
                },
                "comments": [],
                "warning": "Không thể trích xuất bình luận. Facebook có thể yêu cầu đăng nhập hoặc đã chặn truy cập."
            }
        
        # 2. PHÂN TÍCH BẰNG AI MODEL THẬT
        print(f"🤖 Đang phân tích {len(raw_comments)} bình luận bằng AI...")
        analyzed = analyzer.analyze_batch(raw_comments)
        
        # 3. THỐNG KÊ
        stats = {"positive": 0, "negative": 0, "neutral": 0}
        for item in analyzed:
            sentiment = item["sentiment"]
            if sentiment in stats:
                stats[sentiment] += 1
        
        total = len(analyzed)
        
        return {
            "id": str(uuid.uuid4()),
            "url": request.url,
            "status": "completed",
            "total_comments": total,
            "statistics": {
                "positive": stats["positive"],
                "negative": stats["negative"],
                "neutral": stats["neutral"],
                "positive_percent": round(stats["positive"] / total * 100, 1) if total > 0 else 0,
                "negative_percent": round(stats["negative"] / total * 100, 1) if total > 0 else 0,
                "neutral_percent": round(stats["neutral"] / total * 100, 1) if total > 0 else 0
            },
            "comments": analyzed,
            "source": "real_crawl"
        }
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=str(e))
