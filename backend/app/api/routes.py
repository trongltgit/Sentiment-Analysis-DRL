"""
API Routes for Sentiment Analysis System
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from datetime import datetime

from .schemas import (
    PageAnalysisRequest, 
    AnalysisResponse, 
    FeedbackInput,
    AnalysisStatus,
    DRLAction
)
from ..services.scraper import FacebookScraper
from ..services.analyzer import SentimentAnalyzer
from ..services.drl_agent import DRLAgentService

router = APIRouter()


# In-memory storage (replace with Redis/DB in production)
analysis_store = {}


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_fanpage(
    request: PageAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start analysis of a Facebook fanpage URL
    """
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis record
    analysis_store[analysis_id] = {
        "analysis_id": analysis_id,
        "status": AnalysisStatus.PENDING,
        "url": str(request.url),
        "created_at": datetime.utcnow(),
        "max_comments": request.max_comments,
        "depth": request.analysis_depth
    }
    
    # Start background processing
    background_tasks.add_task(
        process_analysis,
        analysis_id=analysis_id,
        url=str(request.url),
        max_comments=request.max_comments,
        depth=request.analysis_depth
    )
    
    return AnalysisResponse(**analysis_store[analysis_id])


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(analysis_id: str):
    """
    Get analysis results by ID
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return AnalysisResponse(**analysis_store[analysis_id])


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackInput):
    """
    Submit feedback to improve DRL agent
    """
    # Update DRL agent with feedback (reinforcement learning)
    drl_service = DRLAgentService()
    await drl_service.process_feedback(feedback)
    
    return {"message": "Feedback received and will be used for model improvement"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "scraper": "available",
            "analyzer": "available",
            "drl_agent": "available"
        }
    }


async def process_analysis(analysis_id: str, url: str, max_comments: int, depth: str):
    """
    Background task to process fanpage analysis
    """
    try:
        # Update status
        analysis_store[analysis_id]["status"] = AnalysisStatus.PROCESSING
        start_time = datetime.utcnow()
        
        # Step 1: Scrape comments
        scraper = FacebookScraper()
        comments = await scraper.scrape_comments(url, max_comments)
        
        # Step 2: Analyze sentiment
        analyzer = SentimentAnalyzer()
        analyzed_comments = await analyzer.analyze_batch(comments, depth)
        
        # Step 3: DRL Agent optimization
        drl_service = DRLAgentService()
        optimized_results = await drl_service.optimize_analysis(analyzed_comments)
        
        # Step 4: Generate summary
        summary = analyzer.generate_summary(optimized_results)
        
        # Update store with results
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        analysis_store[analysis_id].update({
            "status": AnalysisStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "summary": summary,
            "comments": optimized_results,
            "processing_time": processing_time
        })
        
    except Exception as e:
        analysis_store[analysis_id].update({
            "status": AnalysisStatus.FAILED,
            "error": str(e)
        })