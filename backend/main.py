from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio
import os

app = FastAPI(title="AI Sentiment Analysis DRL")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analysis_jobs = {}

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
    comments: Optional[List[dict]] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
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
    
    background_tasks.add_task(process_analysis, job_id, request)
    return AnalysisResponse(**job)

async def process_analysis(job_id: str, request: AnalyzeRequest):
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    
    try:
        # TODO: Thay bằng code crawl thật + AI model
        await asyncio.sleep(3)   # Giả lập
        
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": 3.0,
            "summary": {
                "total_comments": 120,
                "positive": 78,
                "negative": 25,
                "neutral": 17,
                "positive_pct": 65.0,
                "negative_pct": 20.8,
                "neutral_pct": 14.2,
            },
            "comments": [
                {"text": "Rất hài lòng!", "sentiment": "positive", "confidence": 0.92},
            ]
        })
        print(f"✅ Hoàn thành job {job_id}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        job["status"] = "failed"
        job["error"] = str(e)

@app.get("/api/v1/analysis/{job_id}")
def get_analysis(job_id: str):
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisResponse(**analysis_jobs[job_id])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
