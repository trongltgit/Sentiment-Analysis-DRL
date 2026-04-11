"""
FastAPI - Phân tích sentiment đơn giản, tách 3 nhóm rõ ràng
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Sentiment Analysis", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, dict] = {}

class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 100

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    summary: Optional[dict] = None
    comments: Optional[Dict[str, List[dict]]] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

@app.get("/")
def root():
    return {"status": "running", "version": "2.0.0"}

@app.head("/")
def head_root():
    return None

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest, bg: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "url": req.url,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "summary": None,
        "comments": None,
        "processing_time": None,
        "error": None
    }
    jobs[job_id] = job
    bg.add_task(process, job_id, req)
    return AnalysisResponse(**job)

@app.get("/api/v1/analysis/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Not found")
    return AnalysisResponse(**jobs[job_id])

@app.get("/api/v1/analysis/{job_id}/{category}")
def get_category(job_id: str, category: str):
    if job_id not in jobs:
        raise HTTPException(404, "Not found")
    if category not in ["good", "bad", "neutral"]:
        raise HTTPException(400, "Category: good, bad, neutral")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Not completed")
    
    comments = job.get("comments", {}).get(category, [])
    return {
        "job_id": job_id,
        "category": category,
        "description": {
            "good": "Bình luận TÍCH CỰC (hài lòng, khen ngợi)",
            "bad": "Bình luận TIÊU CỰC (phàn nàn, khiếu nại)",
            "neutral": "Bình luận TRUNG LẬP (không rõ ràng)"
        }[category],
        "count": len(comments),
        "comments": comments[:50]
    }

async def process(job_id: str, req: AnalyzeRequest):
    job = jobs[job_id]
    job["status"] = "processing"
    start = time.time()
    
    try:
        from app.services.crawler import crawler
        
        # Crawl và phân loại
        result = await crawler.crawl(req.url, req.max_comments)
        
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": round(time.time() - start, 2),
            "summary": {
                "total": sum(len(v) for v in result.values()),
                "good": len(result["good"]),
                "bad": len(result["bad"]),
                "neutral": len(result["neutral"])
            },
            "comments": result
        })
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = time.time() - start

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
