"""
File: backend/main.py
FastAPI — Phân tích sentiment: GOOD / BAD / NEUTRAL
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import os, sys, time, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Sentiment Analysis",
    description="Phân tích bình luận: Tích cực / Tiêu cực / Trung lập",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lưu jobs trong bộ nhớ (đủ dùng trên 1 worker Render)
jobs: Dict[str, dict] = {}


# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 100


class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    summary: Optional[dict] = None          # chứa các field thống nhất
    comments: Optional[Dict[str, List[dict]]] = None


# ------------------------------------------------------------------
# Static files (React build)
# ------------------------------------------------------------------
_static_dir = "/usr/share/nginx/html"
if os.path.isdir(_static_dir):
    app.mount("/assets", StaticFiles(directory=f"{_static_dir}/assets"), name="assets")


# ------------------------------------------------------------------
# API Routes
# ------------------------------------------------------------------
@app.get("/api/")
def api_root():
    return {
        "service": "Sentiment Analysis API",
        "version": "3.1.0",
    }


@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest, bg: BackgroundTasks):
    print(f"\n{'='*60}")
    print(f"📝 YÊU CẦU MỚI | URL: {req.url}")
    print(f"{'='*60}\n")

    job_id = str(uuid.uuid4())
    job = {
        "id":              job_id,
        "url":             req.url,
        "status":          "pending",
        "created_at":      datetime.now().isoformat(),
        "completed_at":    None,
        "processing_time": None,
        "error":           None,
        "summary":         None,
        "comments":        {"good": [], "bad": [], "neutral": []},
    }
    jobs[job_id] = job
    bg.add_task(process, job_id, req)

    return AnalysisResponse(**job)


@app.get("/api/v1/analysis/{job_id}", response_model=AnalysisResponse)
def get_job(job_id: str):
    print(f"🔍 GET job: {job_id} | jobs hiện có: {len(jobs)}")
    if job_id not in jobs:
        raise HTTPException(404, detail="Không tìm thấy phân tích")
    return AnalysisResponse(**jobs[job_id])


@app.get("/api/v1/analysis/{job_id}/{category}")
def get_category(job_id: str, category: str):
    if job_id not in jobs:
        raise HTTPException(404, "Không tìm thấy job")
    if category not in ["good", "bad", "neutral"]:
        raise HTTPException(400, "Category phải là: good, bad, hoặc neutral")
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Đang xử lý, vui lòng đợi...")
    return {
        "job_id":   job_id,
        "category": category,
        "count":    len(job.get("comments", {}).get(category, [])),
        "comments": job.get("comments", {}).get(category, []),
    }


# ------------------------------------------------------------------
# Background task
# ------------------------------------------------------------------
async def process(job_id: str, req: AnalyzeRequest):
    job   = jobs[job_id]
    job["status"] = "processing"
    start = time.time()

    try:
        from app.services.crawler import crawler

        print(f"🔍 Đang crawl: {req.url}")
        result = await crawler.crawl(req.url, req.max_comments)

        good_list    = result.get("good",    [])
        bad_list     = result.get("bad",     [])
        neutral_list = result.get("neutral", [])
        total        = len(good_list) + len(bad_list) + len(neutral_list)

        # Tính phần trăm an toàn (tránh chia 0)
        def pct(n):
            return round(n / total * 100, 1) if total > 0 else 0

        proc_time = round(time.time() - start, 2)

        # ✅ summary có đủ field cho cả backend lẫn frontend
        job["status"]          = "completed"
        job["completed_at"]    = datetime.now().isoformat()
        job["processing_time"] = proc_time
        job["summary"] = {
            # Số lượng tuyệt đối
            "total_comments": total,
            "good":    len(good_list),
            "bad":     len(bad_list),
            "neutral": len(neutral_list),
            # Phần trăm — frontend dùng các field này
            "positive_pct": pct(len(good_list)),
            "negative_pct": pct(len(bad_list)),
            "neutral_pct":  pct(len(neutral_list)),
            # Alias giữ tương thích cũ
            "positive": len(good_list),
            "negative": len(bad_list),
        }
        job["comments"] = result

        print(
            f"✅ XONG job {job_id} | {proc_time}s | "
            f"good={len(good_list)} bad={len(bad_list)} neutral={len(neutral_list)}"
        )

    except Exception as e:
        print(f"❌ LỖI job {job_id}: {e}")
        traceback.print_exc()
        job["status"]          = "failed"
        job["error"]           = str(e)
        job["processing_time"] = round(time.time() - start, 2)
        job["comments"]        = {"good": [], "bad": [], "neutral": []}


# ------------------------------------------------------------------
# SPA fallback — phục vụ React cho mọi route không phải /api/
# ------------------------------------------------------------------
@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404, "API endpoint not found")

    static_file = f"{_static_dir}/{full_path}"
    if os.path.exists(static_file) and os.path.isfile(static_file):
        return FileResponse(static_file)

    index_file = f"{_static_dir}/index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)

    raise HTTPException(404, "Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
