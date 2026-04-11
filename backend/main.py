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

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import services
try:
    from app.services.analyzer import analyzer
    from app.services.crawler import crawler
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Services not available: {e}")
    SERVICES_AVAILABLE = False

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


@app.get("/")
def root():
    return {"status": "AI Sentiment Analysis API", "version": "1.0.0"}

@app.head("/")
def root_head():
    return None

# Storage
analysis_jobs = {}

# ==================== MODELS ====================

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
    comments: Optional[Dict[str, List[dict]]] = None  # Phân loại theo sentiment
    statistics: Optional[dict] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

# ==================== ENDPOINTS ====================

@app.get("/api/v1/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": "available" if SERVICES_AVAILABLE else "limited",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Bắt đầu phân tích sentiment cho URL
    """
    print(f"📝 Nhận request phân tích: {request.url}")
    print(f"   - Max comments: {request.max_comments}")
    print(f"   - Depth: {request.analysis_depth}")
    
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
    
    job = analysis_jobs[job_id]
    return AnalysisResponse(**job)

@app.get("/api/v1/analysis/{job_id}/comments/{sentiment}")
def get_comments_by_sentiment(job_id: str, sentiment: str):
    """
    Lấy chi tiết comments theo sentiment type
    sentiment: positive, negative, neutral
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    comments = job.get("comments", {})
    if sentiment not in comments:
        raise HTTPException(status_code=400, detail=f"Invalid sentiment type. Choose from: positive, negative, neutral")
    
    return {
        "job_id": job_id,
        "sentiment": sentiment,
        "count": len(comments[sentiment]),
        "comments": comments[sentiment][:50]  # Limit 50
    }

# ==================== BACKGROUND PROCESSING ====================

async def process_analysis_real(job_id: str, request: AnalyzeRequest):
    """
    Xử lý phân tích thực tế - Không còn giả lập!
    """
    job = analysis_jobs[job_id]
    job["status"] = "processing"
    start_time = time.time()
    
    try:
        # Step 1: Crawl comments
        print(f"🔍 Đang crawl comments từ: {request.url}")
        raw_comments = await crawler.crawl(request.url, request.max_comments)
        
        if not raw_comments:
            raise ValueError("Không thể lấy comments từ URL này. Vui lòng kiểm tra lại URL.")
        
        print(f"✅ Đã lấy {len(raw_comments)} comments")
        
        # Step 2: Phân tích sentiment
        print(f"🧠 Đang phân tích sentiment với PhoBERT...")
        
        if SERVICES_AVAILABLE:
            # Dùng PhoBERT thực
            analyzed_comments = await analyzer.analyze_batch_async(
                raw_comments, 
                depth=request.analysis_depth
            )
        else:
            # Fallback: keyword-based
            analyzed_comments = await fallback_analyze(raw_comments)
        
        # Step 3: Phân loại và thống kê
        categorized = categorize_and_sort(analyzed_comments)
        statistics = calculate_statistics(analyzed_comments)
        
        processing_time = time.time() - start_time
        
        # Update job
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time": round(processing_time, 2),
            "summary": {
                "total_comments": len(analyzed_comments),
                "positive_count": len(categorized["positive"]),
                "negative_count": len(categorized["negative"]),
                "neutral_count": len(categorized["neutral"]),
                "positive_pct": round(len(categorized["positive"]) / len(analyzed_comments) * 100, 1),
                "negative_pct": round(len(categorized["negative"]) / len(analyzed_comments) * 100, 1),
                "neutral_pct": round(len(categorized["neutral"]) / len(analyzed_comments) * 100, 1),
            },
            "comments": categorized,  # Phân loại sẵn để frontend dễ hiển thị
            "statistics": statistics
        })
        
        print(f"✅ Hoàn thành job {job_id}")
        print(f"   - Tổng: {len(analyzed_comments)} comments")
        print(f"   - Positive: {len(categorized['positive'])} ({job['summary']['positive_pct']}%)")
        print(f"   - Negative: {len(categorized['negative'])} ({job['summary']['negative_pct']}%)")
        print(f"   - Neutral: {len(categorized['neutral'])} ({job['summary']['neutral_pct']}%)")
        print(f"   - Thời gian: {processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Lỗi job {job_id}: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = time.time() - start_time

def categorize_and_sort(comments: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Phân loại comments và sắp xếp theo confidence
    """
    categorized = {
        "positive": [],
        "negative": [],
        "neutral": []
    }
    
    for c in comments:
        sentiment = c.get("sentiment", "neutral")
        if sentiment in categorized:
            categorized[sentiment].append(c)
    
    # Sắp xếp: confidence cao nhất lên đầu, sau đó đến likes
    for key in categorized:
        categorized[key].sort(
            key=lambda x: (x.get("confidence", 0), x.get("likes", 0)), 
            reverse=True
        )
    
    return categorized

def calculate_statistics(comments: List[Dict]) -> Dict:
    """
    Tính toán thống kê chi tiết
    """
    if not comments:
        return {}
    
    confidences = [c.get("confidence", 0) for c in comments]
    likes = [c.get("likes", 0) for c in comments]
    
    # Aspect analysis
    aspect_counts = {}
    for c in comments:
        aspects = c.get("aspects", {})
        if aspects:
            for aspect in aspects.keys():
                aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
    
    return {
        "avg_confidence": round(sum(confidences) / len(confidences), 3),
        "high_confidence_count": sum(1 for c in confidences if c > 0.8),
        "total_likes": sum(likes),
        "avg_likes": round(sum(likes) / len(likes), 1),
        "top_aspects": dict(sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    }

async def fallback_analyze(comments: List[Dict]) -> List[Dict]:
    """
    Phân tích fallback khi không có PhoBERT (dùng keyword)
    """
    positive_words = ['tốt', 'hay', 'tuyệt', 'hài lòng', 'xuất sắc', 'ủng hộ', 'nhiệt tình', 
                      'chu đáo', 'nhanh', 'đẹp', 'chất lượng', 'hợp lý', 'vừa ý', 'tuyệt vời',
                      'đáng mua', ' recommend', '❤️', '👍', '😍', '5 sao', 'tuyệt']
    negative_words = ['tệ', 'kém', 'chậm', 'thất vọng', 'tồi', 'dở', 'lỗi', 'hỏng', 
                      'đắt', 'lừa', 'khiếu nại', 'phàn nàn', 'bực', 'tức', 'không tốt',
                      'không hài lòng', 'tệ hại', 'kém chất lượng', '😠', '👎']
    
    results = []
    for comment in comments:
        text = comment.get("text", "").lower()
        
        pos_score = sum(2 if w in text else 0 for w in positive_words)
        neg_score = sum(2 if w in text else 0 for w in negative_words)
        
        if pos_score > neg_score:
            sentiment = "positive"
            confidence = min(0.6 + pos_score * 0.05, 0.95)
        elif neg_score > pos_score:
            sentiment = "negative"
            confidence = min(0.6 + neg_score * 0.05, 0.95)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        results.append({
            **comment,
            "sentiment": sentiment,
            "confidence": round(confidence, 3),
            "aspects": {},
            "emotions": None
        })
    
    return results

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
