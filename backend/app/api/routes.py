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

    asyncio.create_task(run_analysis_fixed(analysis_id, str(request.url), request.max_comments))

    return AnalysisResponse(**analysis_store[analysis_id])


async def run_analysis_fixed(analysis_id: str, url: str, max_comments: int):
    try:
        logger.info(f"🔍 Crawling: {url}")
        result = await crawler.crawl(url, max_comments or 50)

        logger.info(f"📦 Result type: {type(result)}")

        # FIX CHÍNH: Xử lý an toàn
        comments_data = result.get("comments") if isinstance(result, dict) else result

        if isinstance(comments_data, int):   # Sai kiểu
            logger.warning("comments là int, dùng total thay thế")
            comments_data = []

        if not isinstance(comments_data, list):
            comments_data = []

        # Lấy text
        comments_list = []
        for item in comments_data:
            if isinstance(item, dict) and "text" in item:
                comments_list.append(item["text"])
            elif isinstance(item, str):
                comments_list.append(item)

        total = len(comments_list)
        logger.info(f"✅ Crawled {total} comments")

        if total == 0:
            analysis_store[analysis_id].update({
                "status": AnalysisStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "summary": {"score": 0, "message": "Không có bình luận"}
            })
            return

        # Phân tích
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

        logger.info(f"🎉 SUCCESS - Score: {score}")

    except Exception as e:
        logger.exception(f"💥 ERROR: {e}")
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
