# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uuid
import asyncio
from datetime import datetime

from app.services.crawler import crawler
from app.services.analyzer import analyzer

router = APIRouter()

# Lưu trữ tạm thời (thay bằng Redis trong production)
job_results = {}

class AnalyzeRequest(BaseModel):
    url: str
    max_comments: Optional[int] = 30  # Giảm mặc định để nhanh hơn

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str  # pending, processing, completed, failed
    total_comments: int
    statistics: dict
    comments: List[dict]
    message: Optional[str] = None

async def process_analysis_job(job_id: str, url: str, max_comments: int):
    """Xử lý phân tích trong background"""
    try:
        job_results[job_id] = {
            "id": job_id,
            "url": url,
            "status": "processing",
            "total_comments": 0,
            "statistics": {},
            "comments": [],
            "message": "Đang crawl dữ liệu..."
        }
        
        # 1. CRAWL với timeout ngắn hơn
        print(f"[{job_id}] 🔍 Đang crawl: {url}")
        
        try:
            crawl_result = await asyncio.wait_for(
                crawler.crawl(url, max_comments=max_comments),
                timeout=45  # Giới hạn 45 giây cho crawl
            )
        except asyncio.TimeoutError:
            job_results[job_id].update({
                "status": "failed",
                "message": "Crawl timeout - Facebook chặn truy cập hoặc load quá chậm"
            })
            return
        
        raw_comments = [c["text"] for c in crawl_result.get("comments", [])]
        
        if not raw_comments:
            job_results[job_id].update({
                "status": "completed",
                "total_comments": 0,
                "statistics": {
                    "positive": 0, "negative": 0, "neutral": 0,
                    "positive_percent": 0, "negative_percent": 0, "neutral_percent": 0
                },
                "message": "Không tìm thấy bình luận. Facebook có thể yêu cầu đăng nhập."
            })
            return
        
        # 2. PHÂN TÍCH
        print(f"[{job_id}] 🤖 Phân tích {len(raw_comments)} bình luận...")
        job_results[job_id]["message"] = f"Đang phân tích {len(raw_comments)} bình luận..."
        
        try:
            analyzed = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,  # Default executor
                    lambda: analyzer.analyze_batch(raw_comments)
                ),
                timeout=60  # Giới hạn 60 giây cho AI
            )
        except asyncio.TimeoutError:
            job_results[job_id].update({
                "status": "failed",
                "message": "AI analysis timeout - Model quá chậm hoặc quá tải"
            })
            return
        
        # 3. THỐNG KÊ
        stats = {"positive": 0, "negative": 0, "neutral": 0}
        for item in analyzed:
            sentiment = item.get("sentiment", "neutral")
            if sentiment in stats:
                stats[sentiment] += 1
        
        total = len(analyzed)
        
        job_results[job_id].update({
            "status": "completed",
            "total_comments": total,
            "statistics": {
                "positive": stats["positive"],
                "negative": stats["negative"],
                "neutral": stats["neutral"],
                "positive_percent": round(stats["positive"] / total * 100, 1) if total > 0 else 0,
                "negative_percent": round(stats["negative"] / total * 100, 1) if total > 0 else 0,
                "neutral_percent": round(stats["neutral"] / total * 100, 1) if total > 0 else 0
            },
            "comments": analyzed,
            "message": f"Hoàn thành! {total} bình luận đã phân tích."
        })
        
        print(f"[{job_id}] ✅ Hoàn thành: {total} comments")
        
    except Exception as e:
        print(f"[{job_id}] ❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
        job_results[job_id].update({
            "status": "failed",
            "message": f"Lỗi: {str(e)}"
        })

@router.post("/analyze")
async def analyze_url(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """Tạo job phân tích và trả về ngay job_id"""
    job_id = str(uuid.uuid4())
    
    # Khởi tạo job
    job_results[job_id] = {
        "id": job_id,
        "url": request.url,
        "status": "pending",
        "total_comments": 0,
        "statistics": {},
        "comments": [],
        "message": "Đang khởi tạo..."
    }
    
    # Chạy trong background
    background_tasks.add_task(
        process_analysis_job,
        job_id,
        request.url,
        request.max_comments
    )
    
    return {
        "id": job_id,
        "url": request.url,
        "status": "pending",
        "message": "Job đã tạo, đang xử lý..."
    }

@router.get("/analysis/{job_id}")
async def get_analysis_result(job_id: str):
    """Lấy kết quả phân tích theo job_id"""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
    
    return job_results[job_id]

@router.get("/analysis/{job_id}/status")
async def get_job_status(job_id: str):
    """Chỉ lấy status (nhẹ hơn cho polling)"""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
    
    job = job_results[job_id]
    return {
        "id": job_id,
        "status": job["status"],
        "total_comments": job.get("total_comments", 0),
        "message": job.get("message", "")
    }
