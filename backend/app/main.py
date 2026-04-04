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
import asyncio

app = FastAPI(title="AI Sentiment Analysis DRL")

# CORS - cho phép tất cả origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store jobs
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
        "timestamp": datetime.now().isoformat()
    }

# 🔴 THÊM: POST /api/v1/analyze
@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Bắt đầu phân tích fan page"""
    print(f"📝 Nhận request phân tích: {request.url}")
    
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
    
    # Chạy async
    background_tasks.add_task(process_analysis, job_id, request.url, request.depth)
    
    return AnalysisResponse(**job)

async def process_analysis(job_id: str, url: str, depth: str):
    """Xử lý phân tích"""
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    print(f"🔄 Đang xử lý job {job_id}")
    
    try:
        start_time = datetime.now()
        
        # TODO: Thay bằng crawl Facebook thực tế
        await asyncio.sleep(2)
        
        # Mock data
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": 2.0,
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
                {"text": "Giao hàng chậm quá", "sentiment": "negative", "confidence": 0.87},
            ]
        })
        print(f"✅ Hoàn thành job {job_id}")
        
    except Exception as e:
        print(f"❌ Lỗi job {job_id}: {e}")
        job["status"] = "failed"
        job["error"] = str(e)

@app.get("/api/v1/analysis/{job_id}", response_model=AnalysisResponse)
def get_analysis(job_id: str):
    """Lấy kết quả"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Không tìm thấy phân tích")
    
    return AnalysisResponse(**analysis_jobs[job_id])

@app.get("/api/v1/analysis")
def list_analysis():
    return list(analysis_jobs.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
