# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.services.crawler import crawler
from app.services.analyzer import analyzer

router = APIRouter()

class AnalyzeRequest(BaseModel):
    url: str
    max_comments: Optional[int] = 25  # Giới hạn để tiết kiệm quota

class CommentDetail(BaseModel):
    text: str
    sentiment: str
    confidence: float
    reason: str

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    total_comments: int
    statistics: dict
    positive_comments: List[CommentDetail]
    negative_comments: List[CommentDetail]
    neutral_comments: List[CommentDetail]
    sources: List[str]
    message: str

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_url(request: AnalyzeRequest):
    """
    Phân tích URL - Free 100% với độ chính xác cao nhất có thể
    """
    job_id = str(uuid.uuid4())
    
    try:
        print(f"🔍 [{job_id}] Bắt đầu crawl: {request.url}")
        
        # 1. CRAWL từ nhiều nguồn free
        crawl_result = await crawler.crawl(request.url, request.max_comments)
        
        raw_comments = [c["text"] for c in crawl_result["comments"]]
        sources = crawl_result.get("sources", [])
        
        if not raw_comments:
            raise HTTPException(
                status_code=400,
                detail=f"Không thu thập được bình luận. "
                       f"Đã thử: {', '.join(crawl_result.get('errors', ['không có nguồn nào']))}. "
                       f"Vui lòng đăng ký ScrapingBee (1000 req free/tháng) tại scrapingbee.com"
            )
        
        print(f"✓ [{job_id}] Thu thập {len(raw_comments)} bình luận từ: {sources}")
        
        # 2. PHÂN TÍCH bằng Groq (free tier)
        print(f"🤖 [{job_id}] Phân tích {len(raw_comments)} bình luận...")
        analyzed = await analyzer.analyze_batch(raw_comments)
        
        # 3. PHÂN LOẠI 3 NHÓM
        positive = [c for c in analyzed if c["sentiment"] == "positive"]
        negative = [c for c in analyzed if c["sentiment"] == "negative"]
        neutral = [c for c in analyzed if c["sentiment"] == "neutral"]
        
        total = len(analyzed)
        
        # 4. TRẢ KẾT QUẢ CHI TIẾT
        return {
            "id": job_id,
            "url": request.url,
            "status": "completed",
            "total_comments": total,
            "statistics": {
                "positive": len(positive),
                "negative": len(negative),
                "neutral": len(neutral),
                "positive_percent": round(len(positive) / total * 100, 1),
                "negative_percent": round(len(negative) / total * 100, 1),
                "neutral_percent": round(len(neutral) / total * 100, 1)
            },
            "positive_comments": positive,
            "negative_comments": negative,
            "neutral_comments": neutral,
            "sources": sources,
            "message": f"✅ Phân tích thành công {total} bình luận từ {', '.join(sources)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [{job_id}] Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi hệ thống: {str(e)}. "
                   f"Đảm bảo đã cấu hình SCRAPINGBEE_TOKEN và GROQ_API_KEY"
        )
