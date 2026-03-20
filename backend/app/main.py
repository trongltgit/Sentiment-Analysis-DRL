"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .api.routes import router
from .config import settings
from .services.drl_agent import DRLAgentService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    print("🚀 Starting Sentiment Analysis DRL System...")
    
    # Load DRL model
    drl_service = DRLAgentService()
    await drl_service.load_checkpoint()
    app.state.drl_service = drl_service
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered sentiment analysis using Deep Reinforcement Learning",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.API_V1_PREFIX)

# Health check
@app.get("/")
async def root():
    return {
        "message": "Sentiment Analysis DRL API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )