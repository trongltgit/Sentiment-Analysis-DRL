"""
FastAPI Backend - Professional Sentiment Analysis v4.0
Ghi chú: Thay thế hoàn toàn file main.py cũ
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import os, sys, time, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Professional Sentiment Analysis API",
    description="Enterprise-grade sentiment analysis with strategic insights",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage
jobs: Dict[str, dict] = {}


# ==================== PYDANTIC MODELS ====================

class CommentData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: str  # high, medium, low, very_high
    keywords: List[str] = []


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


class StrategicInsights(BaseModel):
    overall_sentiment: str
    trend: str
    risks: List[Dict] = []
    opportunities: List[Dict] = []
    recommendations: List[Dict] = []


class CommentsByCategory(BaseModel):
    positive: List[CommentData] = []
    negative: List[CommentData] = []
    neutral: List[CommentData] = []


class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str  # pending, processing, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    summary: Optional[SentimentSummary] = None
    comments: Optional[CommentsByCategory] = None
    insights: Optional[StrategicInsights] = None


class AnalyzeRequest(BaseModel):
    url: str
    max_comments: int = 100


# ==================== STATIC FILES ====================

_static_dir = "/usr/share/nginx/html"
if os.path.isdir(_static_dir):
    app.mount("/assets", StaticFiles(directory=f"{_static_dir}/assets"), name="assets")


# ==================== API ROUTES ====================

@app.get("/api/")
def api_root():
    return {
        "service": "Professional Sentiment Analysis API",
        "version": "4.0.0",
        "features": [
            "Advanced deep learning analysis",
            "Strategic insights & recommendations",
            "Financial-grade confidence scores",
            "Tabbed comment organization",
            "Multi-language support"
        ]
    }


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0"
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest, bg: BackgroundTasks):
    """Start sentiment analysis for a URL"""
    print(f"\n{'='*70}")
    print(f"📊 NEW ANALYSIS REQUEST | URL: {req.url}")
    print(f"   Max comments: {req.max_comments}")
    print(f"{'='*70}\n")

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
    
    # Run analysis in background
    bg.add_task(process_analysis, job_id, req)

    return AnalysisResponse(**job)


@app.get("/api/v1/analysis/{job_id}", response_model=AnalysisResponse)
def get_analysis(job_id: str):
    """Get analysis results by job_id"""
    if job_id not in jobs:
        raise HTTPException(404, detail="Analysis not found")
    return AnalysisResponse(**jobs[job_id])


@app.get("/api/v1/analysis/{job_id}/comments/{category}")
def get_category_comments(job_id: str, category: str):
    """Get comments by category (positive, negative, neutral)"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    if category not in ["positive", "negative", "neutral"]:
        raise HTTPException(400, "Category must be: positive, negative, or neutral")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Analysis still processing...")
    
    comments = job.get("comments", {}).get(category, [])
    return {
        "job_id": job_id,
        "category": category,
        "count": len(comments),
        "comments": comments,
    }


@app.get("/api/v1/analysis/{job_id}/insights")
def get_insights(job_id: str):
    """Get strategic insights"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, "Analysis still processing...")
    
    return job.get("insights", {})


# ==================== BACKGROUND PROCESSING ====================

async def process_analysis(job_id: str, req: AnalyzeRequest):
    """Process sentiment analysis in background"""
    job = jobs[job_id]
    job["status"] = "processing"
    start_time = time.time()

    try:
        from app.services.sentiment_analyzer import (
            ProfessionalSentimentAnalyzer,
            StrategicInsightGenerator
        )

        print(f"🔄 Processing: {job_id}")
        print(f"📥 Fetching comments from: {req.url}")

        # Initialize analyzer
        analyzer = ProfessionalSentimentAnalyzer()

        # Step 1: Crawl comments
        from app.services.crawler import crawler
        
        raw_result = await crawler.crawl(req.url, req.max_comments)
        
        # Thích ứng với format cũ: good/bad/neutral → positive/negative/neutral
        good_list = raw_result.get("good", [])
        bad_list = raw_result.get("bad", [])
        neutral_list = raw_result.get("neutral", [])
        
        all_comments_text = good_list + bad_list + neutral_list

        if not all_comments_text:
            raise ValueError("No comments found")

        # Step 2: Analyze sentiment
        print(f"🔍 Analyzing {len(all_comments_text)} comments...")
        
        analyzed_results = []
        for idx, text in enumerate(all_comments_text):
            result = analyzer.analyze_professional(text)
            analyzed_results.append(result)
            
            if (idx + 1) % 50 == 0:
                print(f"   ✓ Analyzed {idx + 1}/{len(all_comments_text)}")

        # Step 3: Organize by category
        positive_comments = []
        negative_comments = []
        neutral_comments = []

        for result in analyzed_results:
            comment_data = {
                "id": str(uuid.uuid4())[:8],
                "text": result.text,
                "sentiment": result.sentiment,
                "confidence": round(result.confidence, 3),
                "confidence_level": result.confidence_level,
                "keywords": result.keywords,
            }

            if result.sentiment == "positive":
                positive_comments.append(comment_data)
            elif result.sentiment == "negative":
                negative_comments.append(comment_data)
            else:
                neutral_comments.append(comment_data)

        # Step 4: Generate insights
        print("💡 Generating strategic insights...")
        insights = StrategicInsightGenerator.generate_insights(
            analyzed_results,
            len(all_comments_text)
        )

        # Step 5: Calculate summary
        total = len(analyzed_results)
        
        summary = {
            "total_comments": total,
            "positive": len(positive_comments),
            "negative": len(negative_comments),
            "neutral": len(neutral_comments),
            "positive_pct": round(len(positive_comments) / total * 100, 1) if total > 0 else 0,
            "negative_pct": round(len(negative_comments) / total * 100, 1) if total > 0 else 0,
            "neutral_pct": round(len(neutral_comments) / total * 100, 1) if total > 0 else 0,
            "average_confidence": insights.get("average_confidence", 0),
            "confidence_distribution": insights.get("confidence_distribution", {}),
        }

        # Step 6: Update job
        proc_time = round(time.time() - start_time, 2)

        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()
        job["processing_time"] = proc_time
        job["summary"] = summary
        job["comments"] = {
            "positive": positive_comments,
            "negative": negative_comments,
            "neutral": neutral_comments,
        }
        job["insights"] = insights

        print(f"\n✅ COMPLETED: {job_id}")
        print(f"   ⏱️  Time: {proc_time}s")
        print(f"   📊 Positive: {len(positive_comments)} | Negative: {len(negative_comments)} | Neutral: {len(neutral_comments)}")
        print(f"   🎯 Overall: {insights.get('overall_sentiment')}")
        print(f"   📈 Confidence: {summary['average_confidence']:.1%}\n")

    except Exception as e:
        print(f"\n❌ ERROR: {job_id}")
        print(f"   {str(e)}\n")
        traceback.print_exc()
        
        job["status"] = "failed"
        job["error"] = str(e)
        job["processing_time"] = round(time.time() - start_time, 2)
        job["comments"] = {"positive": [], "negative": [], "neutral": []}


# ==================== SPA FALLBACK ====================

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """Serve React SPA for all non-API routes"""
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
    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 Starting Professional Sentiment Analysis API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
