"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CommentInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    likes: int = 0


class CommentAnalysis(BaseModel):
    id: str
    original_text: str
    cleaned_text: str
    sentiment: SentimentLabel
    confidence: float = Field(..., ge=0, le=1)
    aspects: Dict[str, float]  # Aspect-based sentiment
    emotion_scores: Dict[str, float]
    importance_score: float
    action_recommendation: str


class PageAnalysisRequest(BaseModel):
    url: HttpUrl
    max_comments: int = Field(default=100, ge=10, le=1000)
    analysis_depth: str = Field(default="standard", pattern="^(basic|standard|deep)$")


class AnalysisSummary(BaseModel):
    total_comments: int
    sentiment_distribution: Dict[SentimentLabel, int]
    average_confidence: float
    key_topics: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    trend_analysis: Dict[str, Any]


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    url: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    summary: Optional[AnalysisSummary] = None
    comments: Optional[List[CommentAnalysis]] = None
    processing_time: Optional[float] = None


class DRLAction(BaseModel):
    action_type: str  # prioritize, filter, highlight, respond
    target_comments: List[str]
    confidence: float
    explanation: str


class FeedbackInput(BaseModel):
    analysis_id: str
    user_rating: int = Field(..., ge=1, le=5)
    corrections: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None