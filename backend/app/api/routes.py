# backend/app/api/routes.py
from fastapi import APIRouter, HTTPException, status
import uuid
from datetime import datetime
import logging
import asyncio

from app.services.crawler import crawler
from app.services.analyzer import analyzer
from .schemas import PageAnalysisRequest, AnalysisResponse, AnalysisStatus

logger = logging.getLogger(__name__)
router = APIRouter()

analysis_store = {}

@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_fanpage(request: PageAnalysisRequest):
    analysis_id = str(uuid.uuid4())

    analysis_store[analysis_id] = {
        "analysis_id": analysis_id,
        "status": AnalysisStatus.PROCESSING,
        "url": str(request.url),
        "created_at": datetime.utcnow(),
        "max_comments": request.max_comments,
        "completed_at": None,
        "summary": None,
        "error": None
    }

    # Chạy trực tiếp (không Celery) để test nhanh
    asyncio.create_task(run_analysis(analysis_id, str(request.url), request.max_comments))

    return AnalysisResponse(**analysis_store[analysis_id])


async def run_analysis(analysis_id: str, url: str, max_comments: int = 100):
    try:
        logger.info(f"🔍 Bắt đầu crawl: {url}")
        
        crawl_result = await crawler.crawl(url, max_comments)
        comments_list = [c["text"] for c in crawl_result.get("comments", []) if isinstance(c, dict) and "text" in c]

        logger.info(f"✓ Crawled {len(comments_list)} comments")

        if not comments_list:
            analysis_store[analysis_id].update({
                "status": AnalysisStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "summary": {"score": 0, "message": "Không tìm thấy bình luận"}
            })
            return

        analyzed = await analyzer.analyze_batch(comments_list)

        positive = sum(1 for x in analyzed if x.get("sentiment") == "positive")
        negative = sum(1 for x in analyzed if x.get("sentiment") == "negative")
        neutral = len(comments_list) - positive - negative
        score = round((positive - negative) / len(comments_list) * 100, 2) if comments_list else 0

        analysis_store[analysis_id].update({
            "status": AnalysisStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "comments_count": len(comments_list),
            "summary": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "total": len(comments_list),
                "score": score
            }
        })
        logger.info(f"✅ Hoàn thành! Score: {score}")

    except Exception as e:
        logger.exception(f"❌ Lỗi phân tích: {e}")
        analysis_store[analysis_id].update({
            "status": AnalysisStatus.FAILED,
            "error": str(e)[:200]
        })


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(analysis_id: str):
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse(**analysis_store[analysis_id])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
