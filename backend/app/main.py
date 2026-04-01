from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import uuid
from datetime import datetime
import asyncio

from services.analyzer import SentimentAnalyzer
from services.scraper import FacebookScraper
from models.database import AnalysisResult, get_db
from services.drl_agent import DRLActionAgent

app = FastAPI(
    title="AI Sentiment Analysis DRL",
    description="Deep Reinforcement Learning for Sentiment Analysis",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
analyzer = SentimentAnalyzer()
scraper = FacebookScraper()
drl_agent = DRLActionAgent()

# In-memory storage (thay bằng Redis/DB trong production)
analysis_store = {}

class AnalyzeRequest(BaseModel):
    url: HttpUrl
    max_comments: int = 100
    analysis_depth: str = "standard"  # basic, standard, deep

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Bắt đầu phân tích sentiment cho Facebook URL"""
    analysis_id = str(uuid.uuid4())
    
    # Khởi tạo trạng thái
    analysis_store[analysis_id] = {
        "id": analysis_id,
        "url": str(request.url),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "max_comments": request.max_comments,
        "depth": request.analysis_depth,
        "comments": [],
        "summary": None,
        "processing_time": None
    }
    
    # Chạy analysis trong background
    background_tasks.add_task(
        process_analysis,
        analysis_id,
        str(request.url),
        request.max_comments,
        request.analysis_depth
    )
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        status="pending",
        message="Phân tích đã được khởi tạo"
    )

@app.get("/api/v1/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Lấy kết quả phân tích"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Không tìm thấy phân tích")
    
    return analysis_store[analysis_id]

@app.get("/api/v1/analysis/{analysis_id}/comments")
async def get_comments(
    analysis_id: str,
    sentiment: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50
):
    """Lấy danh sách bình luận với filter"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Không tìm thấy phân tích")
    
    comments = analysis_store[analysis_id].get("comments", [])
    
    if sentiment:
        comments = [c for c in comments if c["sentiment"] == sentiment]
    if action:
        comments = [c for c in comments if c["drl_action"] == action]
    
    return {"comments": comments[:limit], "total": len(comments)}

async def process_analysis(analysis_id: str, url: str, max_comments: int, depth: str):
    """Xử lý phân tích chính"""
    import time
    start_time = time.time()
    
    try:
        # Cập nhật trạng thái
        analysis_store[analysis_id]["status"] = "processing"
        
        # 1. Scrape comments từ Facebook
        print(f"[{analysis_id}] Đang crawl dữ liệu từ {url}...")
        comments_data = await scraper.scrape_comments(url, max_comments)
        
        # 2. Phân tích sentiment đa chiều
        print(f"[{analysis_id}] Đang phân tích sentiment...")
        analyzed_comments = []
        
        for idx, comment in enumerate(comments_data):
            # Sentiment analysis
            sentiment_result = analyzer.analyze(comment["text"], depth)
            
            # DRL Agent đưa ra hành động
            drl_action = drl_agent.predict_action(
                comment_text=comment["text"],
                sentiment=sentiment_result["overall"],
                confidence=sentiment_result["confidence"],
                likes=comment.get("likes", 0),
                aspects=sentiment_result.get("aspects", {})
            )
            
            analyzed_comment = {
                "id": f"{analysis_id}_{idx}",
                "original_text": comment["text"],
                "cleaned_text": sentiment_result["cleaned_text"],
                "author": comment.get("author", "Ẩn danh"),
                "timestamp": comment.get("timestamp", datetime.now().isoformat()),
                "likes": comment.get("likes", 0),
                
                # Sentiment
                "sentiment": sentiment_result["overall"],
                "confidence": sentiment_result["confidence"],
                "aspects": sentiment_result.get("aspects", {}),
                "emotions": sentiment_result.get("emotions", {}),
                
                # DRL Action
                "drl_action": drl_action["action"],
                "action_confidence": drl_action["confidence"],
                "requires_action": drl_action["requires_action"],
                "importance_score": drl_action["importance_score"],
                "highlighted": drl_action["action"] in ["highlight", "prioritize"],
                "suggested_response": drl_action.get("suggested_response")
            }
            
            analyzed_comments.append(analyzed_comment)
        
        # 3. Tổng hợp kết quả
        summary = generate_summary(analyzed_comments)
        
        # Cập nhật kết quả
        processing_time = time.time() - start_time
        analysis_store[analysis_id].update({
            "status": "completed",
            "comments": analyzed_comments,
            "summary": summary,
            "processing_time": processing_time,
            "completed_at": datetime.now().isoformat()
        })
        
        print(f"[{analysis_id}] Hoàn thành trong {processing_time:.2f}s")
        
    except Exception as e:
        analysis_store[analysis_id]["status"] = "failed"
        analysis_store[analysis_id]["error"] = str(e)
        print(f"[{analysis_id}] Lỗi: {e}")

def generate_summary(comments: List[dict]) -> dict:
    """Tạo báo cáo tổng hợp"""
    total = len(comments)
    if total == 0:
        return {}
    
    # Phân bố sentiment
    sentiments = {"positive": 0, "neutral": 0, "negative": 0}
    for c in comments:
        sentiments[c["sentiment"]] += 1
    
    # Tính độ tin cậy trung bình
    avg_confidence = sum(c["confidence"] for c in comments) / total
    
    # Các chủ đề chính (từ aspects)
    all_aspects = {}
    for c in comments:
        for aspect, scores in c.get("aspects", {}).items():
            if aspect not in all_aspects:
                all_aspects[aspect] = {"positive": 0, "negative": 0, "neutral": 0}
            all_aspects[aspect][scores["dominant"]] += 1
    
    # Top topics
    key_topics = sorted(
        all_aspects.keys(),
        key=lambda x: sum(all_aspects[x].values()),
        reverse=True
    )[:5]
    
    # Yếu tố rủi ro
    risk_factors = []
    negative_ratio = sentiments["negative"] / total if total > 0 else 0
    if negative_ratio > 0.3:
        risk_factors.append(f"Tỷ lệ tiêu cực cao ({negative_ratio*100:.1f}%)")
    
    high_priority = [c for c in comments if c["drl_action"] == "prioritize"]
    if len(high_priority) > 5:
        risk_factors.append(f"Có {len(high_priority)} bình luận cần ưu tiên xử lý")
    
    # Đề xuất hành động
    recommendations = []
    if sentiments["negative"] > sentiments["positive"]:
        recommendations.append("Cần phản hồi nhanh các bình luận tiêu cực")
    if len([c for c in comments if c["drl_action"] == "respond"]) > 10:
        recommendations.append("Thiết lập quy trình phản hồi tự động")
    recommendations.append("Theo dõi các chủ đề: " + ", ".join(key_topics[:3]))
    
    return {
        "total_comments": total,
        "sentiment_distribution": sentiments,
        "average_confidence": avg_confidence,
        "key_topics": key_topics,
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "action_summary": {
            "prioritize": len([c for c in comments if c["drl_action"] == "prioritize"]),
            "respond": len([c for c in comments if c["drl_action"] == "respond"]),
            "highlight": len([c for c in comments if c["drl_action"] == "highlight"]),
            "filter": len([c for c in comments if c["drl_action"] == "filter"]),
            "ignore": len([c for c in comments if c["drl_action"] == "ignore"])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
