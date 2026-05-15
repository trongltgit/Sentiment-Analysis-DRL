"""
FastAPI Backend — Professional Financial Sentiment Analysis v2.0
Engine: Groq LLaMA 3.3 70B (free) + yfinance + Open Exchange Rates
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid, os, sys, time, traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Professional Financial Sentiment Analysis API",
    description="Groq LLaMA 3.3 70B • yfinance • Open Exchange Rates — All Free",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs: Dict[str, dict] = {}

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 100

class CommentData(BaseModel):
    id: str
    text: str
    sentiment: str
    confidence: float
    confidence_level: str
    keywords: List[str] = []
    source: str = "groq"

class SentimentSummary(BaseModel):
    total_comments: int
    positive: int
    negative: int
    neutral: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    average_confidence: float
    confidence_distribution: Dict[str, int]
    ai_engine: str = "groq_llama3.3_70b"

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    summary: Optional[SentimentSummary] = None
    comments: Optional[Dict] = None
    insights: Optional[Dict] = None

# ═══════════════════════════════════════════════════════════════
# STATIC FILES
# ═══════════════════════════════════════════════════════════════

_static_dir = "/usr/share/nginx/html"
if os.path.isdir(_static_dir):
    _assets = f"{_static_dir}/assets"
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

# ═══════════════════════════════════════════════════════════════
# CORE API
# ═══════════════════════════════════════════════════════════════

@app.get("/api/")
def api_root():
    return {
        "service": "Professional Financial Sentiment Analysis",
        "version": "2.0.0",
        "ai_engine": "Groq LLaMA 3.3 70B (free)",
        "market_data": ["yfinance VN stocks", "Open Exchange Rates", "VnExpress RSS"],
        "features": [
            "Deep learning sentiment via Groq LLaMA 3.3 70B",
            "Vietnamese + English + Financial terminology",
            "Real-time VN banking stocks (yfinance)",
            "Live forex rates (USD/VND/EUR/JPY/CNY)",
            "Financial news sentiment (VnExpress, CafeF RSS)",
            "Strategic insights for banking executives",
        ]
    }

@app.get("/api/v1/health")
def health():
    groq_key = os.getenv("GROQ_API_KEY", "")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "groq_configured": bool(groq_key),
        "ai_engine": "groq_llama3.3_70b" if groq_key else "vader_fallback",
    }

# ─── Sentiment Analysis ───────────────────────────────────────

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest, bg: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "url": req.url,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "processing_time": None,
        "error": None,
        "summary": None,
        "comments": {"positive": [], "negative": [], "neutral": []},
        "insights": None,
    }
    jobs[job_id] = job
    bg.add_task(process_analysis, job_id, req)
    print(f"\n{'='*65}")
    print(f"📊 NEW ANALYSIS | {job_id[:8]} | {req.url}")
    print(f"{'='*65}\n")
    return AnalysisResponse(**job)

@app.get("/api/v1/analysis/{job_id}", response_model=AnalysisResponse)
def get_analysis(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Analysis not found")
    return AnalysisResponse(**jobs[job_id])

@app.get("/api/v1/analysis/{job_id}/comments/{category}")
def get_comments(job_id: str, category: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    if category not in ("positive", "negative", "neutral"):
        raise HTTPException(400, "Category: positive | negative | neutral")
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Analysis still processing")
    comments = job.get("comments", {}).get(category, [])
    return {"job_id": job_id, "category": category, "count": len(comments), "comments": comments}

# ─── Financial Market Data (Free) ────────────────────────────

@app.get("/api/v1/market/overview")
async def market_overview():
    """Tổng quan thị trường: VN stocks + forex + news"""
    from app.services.financial_data import get_market_overview
    data = await get_market_overview()
    return data

@app.get("/api/v1/market/stocks")
async def market_stocks():
    """Cổ phiếu ngân hàng Việt Nam (yfinance)"""
    from app.services.financial_data import fetch_vn_stocks
    return {"stocks": await fetch_vn_stocks(), "updated": datetime.now().isoformat()}

@app.get("/api/v1/market/forex")
async def market_forex():
    """Tỷ giá hối đoái (frankfurter + open.er-api)"""
    from app.services.financial_data import fetch_forex_rates
    return await fetch_forex_rates()

@app.get("/api/v1/market/news")
async def market_news(limit: int = 15):
    """Tin tài chính với sentiment (VnExpress, CafeF RSS)"""
    from app.services.financial_data import fetch_financial_news
    news = await fetch_financial_news(limit)
    pos = sum(1 for n in news if n["sentiment"] == "positive")
    neg = sum(1 for n in news if n["sentiment"] == "negative")
    return {
        "articles": news,
        "summary": {"positive": pos, "negative": neg, "neutral": len(news)-pos-neg},
        "updated": datetime.now().isoformat(),
    }

# ═══════════════════════════════════════════════════════════════
# BACKGROUND PROCESSING
# ═══════════════════════════════════════════════════════════════

async def process_analysis(job_id: str, req: AnalyzeRequest):
    job = jobs[job_id]
    job["status"] = "processing"
    start = time.time()

    try:
        from app.services.crawler import crawler
        from app.services.sentiment_analyzer import ProfessionalSentimentAnalyzer

        print(f"🔄 [{job_id[:8]}] Crawling: {req.url}")
        raw = await crawler.crawl(req.url, req.max_comments)

        all_texts = [
            c.get("text", "") if isinstance(c, dict) else str(c)
            for c in (raw.get("good", []) + raw.get("bad", []) + raw.get("neutral", []))
            if (c.get("text", "") if isinstance(c, dict) else str(c)).strip()
        ]

        if not all_texts:
            raise ValueError("Không tìm thấy nội dung để phân tích. Hãy thử URL khác.")

        print(f"📝 [{job_id[:8]}] {len(all_texts)} texts → Groq analysis...")
        analyzer = ProfessionalSentimentAnalyzer()
        results  = analyzer.analyze_batch(all_texts)

        pos_comments, neg_comments, neu_comments = [], [], []
        for r in results:
            item = {
                "id":               str(uuid.uuid4())[:8],
                "text":             r.text,
                "sentiment":        r.sentiment,
                "confidence":       round(r.confidence, 3),
                "confidence_level": r.confidence_level,
                "keywords":         r.keywords,
                "source":           r.source,
            }
            if r.sentiment == "positive":
                pos_comments.append(item)
            elif r.sentiment == "negative":
                neg_comments.append(item)
            else:
                neu_comments.append(item)

        insights = analyzer.generate_insights(results, req.url)
        total    = len(results)

        summary = {
            "total_comments":         total,
            "positive":               len(pos_comments),
            "negative":               len(neg_comments),
            "neutral":                len(neu_comments),
            "positive_pct":           round(len(pos_comments)/total*100, 1),
            "negative_pct":           round(len(neg_comments)/total*100, 1),
            "neutral_pct":            round(len(neu_comments)/total*100, 1),
            "average_confidence":     insights.get("average_confidence", 0),
            "confidence_distribution":insights.get("confidence_distribution", {}),
            "ai_engine":              insights.get("ai_engine", "groq_llama3.3_70b"),
        }

        proc = round(time.time() - start, 2)
        job.update({
            "status":          "completed",
            "completed_at":    datetime.now().isoformat(),
            "processing_time": proc,
            "summary":         summary,
            "comments":        {"positive": pos_comments, "negative": neg_comments, "neutral": neu_comments},
            "insights":        insights,
        })

        print(f"✅ [{job_id[:8]}] Done in {proc}s | +"
              f"{len(pos_comments)} -{len(neg_comments)} ~{len(neu_comments)}"
              f" | {insights.get('overall_sentiment','?')}")

    except Exception as e:
        print(f"❌ [{job_id[:8]}] ERROR: {e}")
        traceback.print_exc()
        job.update({
            "status": "failed",
            "error":  str(e),
            "processing_time": round(time.time() - start, 2),
            "comments": {"positive": [], "negative": [], "neutral": []},
        })

# ═══════════════════════════════════════════════════════════════
# SPA FALLBACK
# ═══════════════════════════════════════════════════════════════

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404, "API endpoint not found")
    static_file = f"{_static_dir}/{full_path}"
    if os.path.exists(static_file) and os.path.isfile(static_file):
        return FileResponse(static_file)
    idx = f"{_static_dir}/index.html"
    if os.path.exists(idx):
        return FileResponse(idx)
    raise HTTPException(404, "Not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
