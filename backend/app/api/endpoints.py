from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.services.crawler import crawler
from app.services.analyzer import analyzer

router = APIRouter()

class AnalyzeRequest(BaseModel):
    url: str
    max_comments: Optional[int] = 25

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
    job_id = str(uuid.uuid4())
    
    try:
        print(f"🔍 [{job_id}] Crawl: {request.url}")
        
        # Crawl
        crawl_result = await crawler.crawl(request.url, request.max_comments)
        raw_comments = [c["text"] for c in crawl_result["comments"]]
        sources = crawl_result.get("sources", [])
        
        if not raw_comments:
            raise HTTPException(
                status_code=400,
                detail=f"Không thu thập được. Đã thử: {crawl_result.get('errors', [])}"
            )
        
        print(f"✓ [{job_id}] {len(raw_comments)} comments từ {sources}")
        
        # Phân tích
        print(f"🤖 [{job_id}] Phân tích...")
        analyzed = await analyzer.analyze_batch(raw_comments)
        
        # Phân loại
        positive = [c for c in analyzed if c["sentiment"] == "positive"]
        negative = [c for c in analyzed if c["sentiment"] == "negative"]
        neutral = [c for c in analyzed if c["sentiment"] == "neutral"]
        
        total = len(analyzed)
        
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
            "message": f"✅ Phân tích {total} bình luận từ {', '.join(sources)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [{job_id}] Lỗi: {e}")
        raise HTTPException(status_code=500, detail=str(e))
