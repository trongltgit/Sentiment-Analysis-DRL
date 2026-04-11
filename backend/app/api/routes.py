# backend/app/api/routes.py
"""
API Routes for Sentiment Analysis System
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import uuid
from datetime import datetime
from app.services.tasks import analyze_fanpage_task
from .schemas import PageAnalysisRequest, AnalysisResponse, AnalysisStatus

router = APIRouter()

# In-memory storage (tạm thời)
analysis_store = {}

@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_fanpage(request: PageAnalysisRequest):
    """Bắt đầu phân tích Fanpage"""
    analysis_id = str(uuid.uuid4())

    analysis_store[analysis_id] = {
        "analysis_id": analysis_id,
        "status": AnalysisStatus.PENDING,
        "url": str(request.url),
        "created_at": datetime.utcnow(),
        "max_comments": request.max_comments,
        "depth": request.analysis_depth,
        "completed_at": None,
        "summary": None,
        "error": None
    }

    # Gọi Celery task (quan trọng)
    task = analyze_fanpage_task.delay(
        analysis_id=analysis_id,
        url=str(request.url),
        max_comments=request.max_comments
    )

    logger.info(f"✅ Đã gửi task Celery: {analysis_id} | Task ID: {task.id}")

    return AnalysisResponse(**analysis_store[analysis_id])


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(analysis_id: str):
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    return AnalysisResponse(**analysis_store[analysis_id])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "scraper": "available",
            "analyzer": "available",
            "celery": "active"
        }
    }
