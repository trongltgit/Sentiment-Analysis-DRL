"""
Backend API for Sentiment Analysis with DRL
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
from datetime import datetime

app = FastAPI(title="AI Sentiment Analysis DRL")

# 🔴 SỬA: CORS cho phép tất cả origins
# Production nên restrict lại sau khi test xong
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True if allow_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store jobs (tạm, nên dùng Redis/DB)
analysis_jobs = {}

class AnalyzeRequest(BaseModel):
    url: str
    depth: str = "standard"

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    summary: Optional[dict] = None
    comments: Optional[List[dict]] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/analysis/test")
def test():
    return {
        "status": "ok",
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Bắt đầu phân tích"""
    job_id = str(uuid.uuid4())
    
    job = {
        "id": job_id,
        "url": request.url,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "summary": None,
        "comments": [],
        "processing_time": None,
        "error": None
    }
    analysis_jobs[job_id] = job
    
    # TODO: Implement actual analysis with Celery
    background_tasks.add_task(process_analysis_mock, job_id, request.url, request.depth)
    
    return AnalysisResponse(**job)

async def process_analysis_mock(job_id: str, url: str, depth: str):
    """Mock processing - thay bằng Celery task thực tế"""
    import asyncio
    
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    
    try:
        await asyncio.sleep(3)  # Giả lập processing
        
        # Mock data
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": 3.0,
            "summary": {
                "total_comments": 100,
                "positive": 65,
                "negative": 20,
                "neutral": 15,
                "positive_pct": 65.0,
                "negative_pct": 20.0,
                "neutral_pct": 15.0,
            },
            "comments": [
                {"text": "Sản phẩm tuyệt vời!", "sentiment": "positive", "confidence": 0.95},
                {"text": "Giao hàng chậm", "sentiment": "negative", "confidence": 0.87},
            ]
        })
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)

@app.get("/api/v1/analysis/{job_id}", response_model=AnalysisResponse)
def get_analysis(job_id: str):
    """Lấy kết quả phân tích"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(**analysis_jobs[job_id])

@app.get("/api/v1/analysis")
def list_analysis():
    """List all analyses"""
    return list(analysis_jobs.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
