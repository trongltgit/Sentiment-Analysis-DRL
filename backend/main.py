"""
Main FastAPI Application - AI Sentiment Analysis with DRL
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import os
import sys
import time
import logging

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="AI Sentiment Analysis DRL", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
analysis_jobs: Dict[str, dict] = {}
_services = None

# ============================================
# LAZY LOAD SERVICES
# ============================================
def get_services():
    global _services
    if _services is None:
        try:
            logger.info("Loading services...")
            from app.services.analyzer import SentimentAnalyzer
            from app.services.crawler import CommentCrawler
            
            _services = {
                "analyzer": SentimentAnalyzer(),
                "crawler": CommentCrawler(),
                "ok": True
            }
            logger.info("✅ Services loaded")
        except Exception as e:
            logger.error(f"❌ Service load failed: {e}")
            _services = {"ok": False, "error": str(e)}
    return _services

# ============================================
# MODELS
# ============================================
class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 100
    analysis_depth: str = "standard"

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
# ENDPOINTS (quan trọng cho Render!)
# ============================================
@app.get("/")
def root():
    svcs = get_services()
    return {
        "status": "running",
        "services": "ok" if svcs["ok"] else "error",
        "version": "1.0.0"
    }

@app.head("/")
def root_head():
    return None

@app.get("/api/v1/health")
def health_check():
    svcs = get_services()
    return {
        "status": "healthy" if svcs["ok"] else "degraded",
        "services_loaded": svcs["ok"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    logger.info(f"📥 Analysis request: {request.url}")
    
    svcs = get_services()
    if not svcs["ok"]:
        raise HTTPException(status_code=503, detail="Services not available")
    
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
    
    background_tasks.add_task(process_analysis, job_id, request)
    return AnalysisResponse(**job)

@app.get("/api/v1/analysis/{job_id}")
def get_analysis(job_id: str):
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisResponse(**analysis_jobs[job_id])

@app.get("/api/v1/analysis/{job_id}/comments/{sentiment}")
def get_comments_by_sentiment(job_id: str, sentiment: str):
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Not completed")
    
    if sentiment not in ["positive", "negative", "neutral"]:
        raise HTTPException(status_code=400, detail="Invalid sentiment")
    
    comments = job.get("comments", {}).get(sentiment, [])
    return {
        "job_id": job_id,
        "sentiment": sentiment,
        "count": len(comments),
        "comments": comments[:50]
    }

# ============================================
# BACKGROUND PROCESSING
# ============================================
async def process_analysis(job_id: str, request: AnalyzeRequest):
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    start = time.time()
    
    try:
        svcs = get_services()
        crawler = svcs["crawler"]
        analyzer = svcs["analyzer"]
        
        # Crawl
        logger.info(f"🔍 Crawling: {request.url}")
        raw = await crawler.crawl(request.url, request.max_comments)
        logger.info(f"✅ Crawled {len(raw)} comments")
        
        # Analyze
        logger.info("🧠 Analyzing...")
        analyzed = await analyzer.analyze_batch_async(raw, request.analysis_depth)
        
        # Categorize
        cat = {"positive": [], "negative": [], "neutral": []}
        for c in analyzed:
            s = c.get("sentiment", "neutral")
            if s in cat:
                cat[s].append(c)
        
        for k in cat:
            cat[k].sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        total = len(analyzed)
        proc_time = time.time() - start
        
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": round(proc_time, 2),
            "summary": {
                "total_comments": total,
                "positive_count": len(cat["positive"]),
                "negative_count": len(cat["negative"]),
                "neutral_count": len(cat["neutral"]),
                "positive_pct": round(len(cat["positive"])/total*100, 1) if total else 0,
                "negative_pct": round(len(cat["negative"])/total*100, 1) if total else 0,
                "neutral_pct": round(len(cat["neutral"])/total*100, 1) if total else 0,
            },
            "comments": cat,
            "statistics": {
                "avg_confidence": round(sum(c.get("confidence",0) for c in analyzed)/len(analyzed), 3) if analyzed else 0,
                "total_likes": sum(c.get("likes",0) for c in analyzed)
            }
        })
        
        logger.info(f"✅ Job {job_id} done: {proc_time:.1f}s")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = time.time() - start

# ============================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
