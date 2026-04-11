"""
Main FastAPI Application - AI Sentiment Analysis with DRL
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import asyncio
import os
import sys
import time
import logging
import traceback

# Setup logging ngay đầu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.dirname(current_dir))

logger.info(f"Python path: {sys.path}")
logger.info(f"Current dir: {current_dir}")

# ============================================
# LAZY IMPORT SERVICES (quan trọng!)
# ============================================
_services = None

def get_services():
    """Lazy load services để tránh crash khi khởi động"""
    global _services
    if _services is None:
        try:
            logger.info("🔄 Loading services...")
            from app.services.analyzer import SentimentAnalyzer
            from app.services.crawler import CommentCrawler
            
            analyzer = SentimentAnalyzer()
            crawler = CommentCrawler()
            
            _services = {
                "analyzer": analyzer,
                "crawler": crawler,
                "available": True
            }
            logger.info("✅ Services loaded successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to load services: {e}")
            logger.error(traceback.format_exc())
            _services = {
                "analyzer": None,
                "crawler": None,
                "available": False,
                "error": str(e)
            }
    return _services

# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(
    title="AI Sentiment Analysis DRL",
    description="Phân tích sentiment bình luận sử dụng PhoBERT và Deep Reinforcement Learning",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
analysis_jobs = {}

# ============================================
# MODELS
# ============================================
class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 100
    analysis_depth: str = "standard"  # basic, standard, deep

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    summary: Optional[dict] = None
    comments: Optional[Dict[str, List[dict]]] = None
    statistics: Optional[dict] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

# ============================================
# ROOT & HEALTH ENDPOINTS (quan trọng cho Render!)
# ============================================
@app.get("/")
def root():
    """Root endpoint - kiểm tra service alive"""
    svcs = get_services()
    return {
        "status": "AI Sentiment Analysis API is running",
        "version": "1.0.0",
        "services_available": svcs["available"],
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.head("/")
def root_head():
    """HEAD request cho health check"""
    return None

@app.get("/api/v1/health")
def health_check():
    """Health check chi tiết"""
    svcs = get_services()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "available": svcs["available"],
            "error": svcs.get("error") if not svcs["available"] else None
        }
    }

# ============================================
# MAIN API ENDPOINTS
# ============================================
@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Bắt đầu phân tích sentiment cho URL
    """
    logger.info(f"📝 Nhận request phân tích: {request.url}")
    logger.info(f"   - Max comments: {request.max_comments}")
    logger.info(f"   - Depth: {request.analysis_depth}")
    
    # Kiểm tra services trước
    svcs = get_services()
    if not svcs["available"]:
        raise HTTPException(status_code=503, detail=f"Services not available: {svcs.get('error')}")
    
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "url": request.url,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "summary": None,
        "comments": None,
        "statistics": None,
        "processing_time": None,
        "error": None
    }
    analysis_jobs[job_id] = job
    
    background_tasks.add_task(process_analysis_real, job_id, request)
    return AnalysisResponse(**job)

@app.get("/api/v1/analysis/{job_id}")
def get_analysis(job_id: str):
    """Lấy kết quả phân tích"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return AnalysisResponse(**analysis_jobs[job_id])

@app.get("/api/v1/analysis/{job_id}/comments/{sentiment}")
def get_comments_by_sentiment(job_id: str, sentiment: str):
    """
    Lấy chi tiết comments theo sentiment type
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    if sentiment not in ["positive", "negative", "neutral"]:
        raise HTTPException(status_code=400, detail="Invalid sentiment. Use: positive, negative, neutral")
    
    comments = job.get("comments", {})
    sentiment_comments = comments.get(sentiment, [])
    
    return {
        "job_id": job_id,
        "sentiment": sentiment,
        "count": len(sentiment_comments),
        "comments": sentiment_comments[:50]
    }

# ============================================
# BACKGROUND PROCESSING
# ============================================
async def process_analysis_real(job_id: str, request: AnalyzeRequest):
    """
    Xử lý phân tích thực tế
    """
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    start_time = time.time()
    
    try:
        svcs = get_services()
        crawler = svcs["crawler"]
        analyzer = svcs["analyzer"]
        
        # Step 1: Crawl
        logger.info(f"🔍 Crawling comments from: {request.url}")
        raw_comments = await crawler.crawl(request.url, request.max_comments)
        
        if not raw_comments:
            raise ValueError("Không thể lấy comments từ URL này")
        
        logger.info(f"✅ Crawled {len(raw_comments)} comments")
        
        # Step 2: Analyze
        logger.info(f"🧠 Analyzing sentiment...")
        analyzed_comments = await analyzer.analyze_batch_async(
            raw_comments, 
            depth=request.analysis_depth
        )
        
        # Step 3: Categorize & stats
        categorized = categorize_and_sort(analyzed_comments)
        statistics = calculate_statistics(analyzed_comments)
        
        processing_time = time.time() - start_time
        
        total = len(analyzed_comments)
        
        # Update job
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": round(processing_time, 2),
            "summary": {
                "total_comments": total,
                "positive_count": len(categorized["positive"]),
                "negative_count": len(categorized["negative"]),
                "neutral_count": len(categorized["neutral"]),
                "positive_pct": round(len(categorized["positive"]) / total * 100, 1) if total > 0 else 0,
                "negative_pct": round(len(categorized["negative"]) / total * 100, 1) if total > 0 else 0,
                "neutral_pct": round(len(categorized["neutral"]) / total * 100, 1) if total > 0 else 0,
            },
            "comments": categorized,
            "statistics": statistics
        })
        
        logger.info(f"✅ Job {job_id} completed in {processing_time:.2f}s")
        logger.info(f"   Results: +{job['summary']['positive_count']}/-{job['summary']['negative_count']}/={job['summary']['neutral_count']}")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        logger.error(traceback.format_exc())
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = time.time() - start_time

def categorize_and_sort(comments: List[Dict]) -> Dict[str, List[Dict]]:
    """Phân loại và sắp xếp comments"""
    categorized = {"positive": [], "negative": [], "neutral": []}
    
    for c in comments:
        sentiment = c.get("sentiment", "neutral")
        if sentiment in categorized:
            categorized[sentiment].append(c)
    
    # Sort by confidence, then likes
    for key in categorized:
        categorized[key].sort(
            key=lambda x: (x.get("confidence", 0), x.get("likes", 0)), 
            reverse=True
        )
    
    return categorized

def calculate_statistics(comments: List[Dict]) -> Dict:
    """Tính toán thống kê"""
    if not comments:
        return {}
    
    confidences = [c.get("confidence", 0) for c in comments]
    likes = [c.get("likes", 0) for c in comments]
    
    aspect_counts = {}
    for c in comments:
        aspects = c.get("aspects", {}) or {}
        for aspect in aspects.keys():
            aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
    
    return {
        "avg_confidence": round(sum(confidences) / len(confidences), 3),
        "high_confidence_count": sum(1 for c in confidences if c > 0.8),
        "total_likes": sum(likes),
        "avg_likes": round(sum(likes) / len(likes), 1) if likes else 0,
        "top_aspects": dict(sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    }

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
