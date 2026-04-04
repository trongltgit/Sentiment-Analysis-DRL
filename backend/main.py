"""
Backend API for Sentiment Analysis with DRL
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import asyncio
from datetime import datetime

# Import analyzer của bạn
from app.services.analyzer import SentimentAnalyzer

app = FastAPI(title="AI Sentiment Analysis DRL")

# CORS - cho phép tất cả origins (vì cùng domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cùng domain nên an toàn
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store analysis jobs (dùng dict tạm, production nên dùng Redis/DB)
analysis_jobs = {}

# Khởi tạo analyzer
analyzer = SentimentAnalyzer()

class AnalyzeRequest(BaseModel):
    url: str
    depth: str = "standard"  # basic, standard, deep

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str  # pending, processing, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    summary: Optional[dict] = None
    comments: Optional[List[dict]] = None
    processing_time: Optional[float] = None

@app.get("/api/v1/analysis/test")
def test():
    """Test endpoint"""
    return {
        "status": "ok",
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat()
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
        "processing_time": None
    }
    analysis_jobs[job_id] = job
    
    # Chạy async
    background_tasks.add_task(process_analysis, job_id, request.url, request.depth)
    
    return AnalysisResponse(**job)

async def process_analysis(job_id: str, url: str, depth: str):
    """Xử lý phân tích background"""
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    
    try:
        start_time = datetime.now()
        
        # TODO: Crawl comments từ Facebook
        # Tạm thời mock data để test
        await asyncio.sleep(2)  # Giả lập processing
        
        mock_comments = [
            {"text": "Sản phẩm rất tốt, giao hàng nhanh!", "likes": 10},
            {"text": "Chất lượng kém, không đáng tiền", "likes": 5},
            {"text": "Dịch vụ tuyệt vời", "likes": 8},
        ]
        
        # Phân tích từng comment
        analyzed_comments = []
        for comment in mock_comments:
            result = analyzer.analyze(comment["text"], depth=depth)
            analyzed_comments.append({
                **comment,
                "sentiment": result["overall"],
                "confidence": result["confidence"],
                "aspects": result.get("aspects", {}),
                "emotions": result.get("emotions", {})
            })
        
        # Tính summary
        total = len(analyzed_comments)
        positive = sum(1 for c in analyzed_comments if c["sentiment"] == "positive")
        negative = sum(1 for c in analyzed_comments if c["sentiment"] == "negative")
        neutral = total - positive - negative
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": processing_time,
            "summary": {
                "total_comments": total,
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_pct": round(positive/total*100, 1),
                "negative_pct": round(negative/total*100, 1),
                "neutral_pct": round(neutral/total*100, 1),
            },
            "comments": analyzed_comments
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
    """List all analyses (debug)"""
    return list(analysis_jobs.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
