"""
FastAPI - Phân tích sentiment: GOOD / BAD / NEUTRAL
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

app = FastAPI(
    title="Sentiment Analysis",
    description="Phân tích bình luận thành 3 nhóm: Tích cực (GOOD), Tiêu cực (BAD), Trung lập (NEUTRAL)",
    version="3.0.0"
)

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
    return {
        "service": "Sentiment Analysis API",
        "version": "3.0.0",
        "groups": {
            "good": "Bình luận TÍCH CỰC (hài lòng, recommend, 5 sao)",
            "bad": "Bình luận TIÊU CỰC (phàn nàn, khiếu nại, thất vọng)",
            "neutral": "Bình luận TRUNG LẬP (không rõ ràng, bình thường)"
        }
    }

@app.head("/")
def head_root():
    return None

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest, bg: BackgroundTasks):
    print(f"\n{'='*60}")
    print(f"📝 NHẬN YÊU CẦU MỚI")
    print(f"   URL: {req.url}")
    print(f"   Max comments: {req.max_comments}")
    print(f"{'='*60}\n")
    
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
        raise HTTPException(404, "Không tìm thấy job")
    return AnalysisResponse(**jobs[job_id])

@app.get("/api/v1/analysis/{job_id}/{category}")
def get_category(job_id: str, category: str):
    """
    Lấy bình luận theo nhóm:
    - good: Tích cực
    - bad: Tiêu cực  
    - neutral: Trung lập
    """
    if job_id not in jobs:
        raise HTTPException(404, "Không tìm thấy job")
    if category not in ["good", "bad", "neutral"]:
        raise HTTPException(400, "Category phải là: good, bad, hoặc neutral")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Đang xử lý, vui lòng đợi...")
    
    comments = job.get("comments", {}).get(category, [])
    
    descriptions = {
        "good": {
            "name": "TÍCH CỰC",
            "description": "Bình luận hài lòng, khen ngợi, recommend sản phẩm/dịch vụ",
            "icon": "👍",
            "color": "green"
        },
        "bad": {
            "name": "TIÊU CỰC", 
            "description": "Bình luận phàn nàn, khiếu nại, thất vọng, cần chú ý xử lý",
            "icon": "⚠️",
            "color": "red"
        },
        "neutral": {
            "name": "TRUNG LẬP",
            "description": "Bình luận không rõ ràng, bình thường, không tích cực cũng không tiêu cực",
            "icon": "➖",
            "color": "gray"
        }
    }
    
    return {
        "job_id": job_id,
        "category": category,
        "info": descriptions[category],
        "count": len(comments),
        "sample_comments": comments[:10] if len(comments) > 10 else comments
    }

async def process(job_id: str, req: AnalyzeRequest):
    job = jobs[job_id]
    job["status"] = "processing"
    start = time.time()
    
    try:
        from app.services.crawler import crawler
        
        print(f"🔍 Đang phân tích: {req.url}")
        result = await crawler.crawl(req.url, req.max_comments)
        
        proc_time = time.time() - start
        
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": round(proc_time, 2),
            "summary": {
                "total": sum(len(v) for v in result.values()),
                "good": len(result["good"]),
                "bad": len(result["bad"]),
                "neutral": len(result["neutral"]),
                "platform": result.get("good", [{}])[0].get("platform", "unknown") if result["good"] else "unknown"
            },
            "comments": result
        })
        
        print(f"\n✅ HOÀN THÀNH JOB {job_id}")
        print(f"   Thời gian: {proc_time:.2f}s")
        print(f"   Kết quả: {job['summary']['good']} good, {job['summary']['bad']} bad, {job['summary']['neutral']} neutral\n")
        
    except Exception as e:
        print(f"\n❌ LỖI JOB {job_id}: {e}\n")
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = time.time() - start

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
