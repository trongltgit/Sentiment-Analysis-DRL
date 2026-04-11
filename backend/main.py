"""
Main FastAPI - Tương thích với crawler tách good/bad/neutral
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="AI Sentiment Analysis DRL", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analysis_jobs: Dict[str, dict] = {}
_services = None

def get_services():
    global _services
    if _services is None:
        try:
            logger.info("Loading services...")
            from app.services.analyzer import analyzer
            from app.services.crawler import crawler
            _services = {"analyzer": analyzer, "crawler": crawler, "ok": True}
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
    comments: Optional[Dict[str, List[dict]]] = None  # good, bad, neutral
    statistics: Optional[dict] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

# ============================================
# ENDPOINTS
# ============================================
@app.get("/")
def root():
    svcs = get_services()
    return {
        "status": "AI Sentiment Analysis API",
        "version": "2.0.0",
        "features": ["good/bad/neutral classification", "duplicate filtering", "spam detection"],
        "services": "ok" if svcs["ok"] else "error"
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
    logger.info(f"📥 New analysis: {request.url}")
    
    svcs = get_services()
    if not svcs["ok"]:
        raise HTTPException(status_code=503, detail=f"Services unavailable: {svcs.get('error')}")
    
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

@app.get("/api/v1/analysis/{job_id}/{category}")
def get_comments_by_category(job_id: str, category: str):
    """
    Lấy comments theo nhóm: good, bad, neutral
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if category not in ["good", "bad", "neutral"]:
        raise HTTPException(status_code=400, detail="Category must be: good, bad, or neutral")
    
    job = analysis_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    comments = job.get("comments", {}).get(category, [])
    
    return {
        "job_id": job_id,
        "category": category,
        "description": {
            "good": "Comments tích cực, chất lượng cao",
            "bad": "Comments tiêu cực, cần chú ý",
            "neutral": "Comments trung lập hoặc không rõ ràng"
        }[category],
        "count": len(comments),
        "comments": comments
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
        
        # Step 1: Crawl + phân loại sơ bộ
        logger.info(f"🔍 Crawling and pre-classifying: {request.url}")
        categorized = await crawler.crawl(request.url, request.max_comments)
        
        # Flatten để phân tích
        all_comments = []
        for cat, items in categorized.items():
            for item in items:
                item["pre_category"] = cat  # Lưu category gốc
                all_comments.append(item)
        
        logger.info(f"📊 Pre-filtered: {len(categorized['good'])} good, {len(categorized['bad'])} bad, {len(categorized['neutral'])} neutral")
        
        # Step 2: Phân tích sentiment chi tiết bằng PhoBERT
        logger.info(f"🧠 Analyzing with PhoBERT...")
        analyzed = await analyzer.analyze_batch_async(all_comments, request.analysis_depth)
        
        # Step 3: Tính toán statistics
        proc_time = time.time() - start
        
        # Tính confidence trung bình cho mỗi nhóm
        stats = {}
        for cat in ["good", "bad", "neutral"]:
            items = [c for c in analyzed if c.get("pre_category") == cat]
            if items:
                avg_conf = sum(c.get("confidence", 0) for c in items) / len(items)
                stats[f"{cat}_avg_confidence"] = round(avg_conf, 3)
                stats[f"{cat}_count"] = len(items)
        
        # Update job
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": round(proc_time, 2),
            "summary": {
                "total_analyzed": len(analyzed),
                "good_comments": len(categorized["good"]),
                "bad_comments": len(categorized["bad"]),
                "neutral_comments": len(categorized["neutral"]),
                "spam_filtered": request.max_comments - len(all_comments),
            },
            "comments": categorized,  # good, bad, neutral đã tách sẵn
            "statistics": {
                **stats,
                "total_processing_time": round(proc_time, 2),
                "platform": categorized.get("good", [{}])[0].get("platform", "unknown") if categorized["good"] else "unknown"
            }
        })
        
        logger.info(f"✅ Job {job_id} completed: {proc_time:.1f}s")
        logger.info(f"   Results: {job['summary']['good_comments']} good, {job['summary']['bad_comments']} bad, {job['summary']['neutral_comments']}")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = time.time() - start

# ============================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
