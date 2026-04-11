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
        "completed_at": None,
        "summary": None,
        "error": None
    }

    asyncio.create_task(simple_run(analysis_id, str(request.url), request.max_comments))

    return AnalysisResponse(**analysis_store[analysis_id])


async def simple_run(analysis_id: str, url: str, max_comments: int):
    try:
        logger.info("=== BẮT ĐẦU PHÂN TÍCH ===")
        result = await crawler.crawl(url, max_comments or 50)
        
        logger.info(f"Type of result: {type(result)}")
        logger.info(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'Not dict'}")
        
        comments = result.get("comments", []) if isinstance(result, dict) else []
        if isinstance(comments, int):
            comments = []
            
        comments_list = [c["text"] if isinstance(c, dict) else c for c in comments if c]

        total = len(comments_list)
        logger.info(f"✅ Crawled {total} comments")

        if total == 0:
            analysis_store[analysis_id]["status"] = AnalysisStatus.COMPLETED
            analysis_store[analysis_id]["summary"] = {"score": 0, "message": "No comments"}
            return

        analyzed = await analyzer.analyze_batch(comments_list)

        pos = sum(1 for x in analyzed if x.get("sentiment") == "positive")
        neg = sum(1 for x in analyzed if x.get("sentiment") == "negative")
        score = round((pos - neg) / total * 100, 2) if total > 0 else 0

        analysis_store[analysis_id].update({
            "status": AnalysisStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "summary": {
                "positive": pos,
                "negative": neg,
                "neutral": total - pos - neg,
                "total": total,
                "score": score
            }
        })
        logger.info(f"🎉 HOÀN THÀNH - Score: {score}")

    except Exception as e:
        logger.exception(f"💥 LỖI: {e}")
        analysis_store[analysis_id].update({
            "status": AnalysisStatus.FAILED,
            "error": str(e)
        })


@router.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Not found")
    return analysis_store[analysis_id]


@router.get("/health")
async def health_check():
    return {"status": "healthy"}
