"""
Configuration settings for the Sentiment Analysis DRL System
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sentiment Analysis DRL"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite:///./sentiment_analysis.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Model Paths
    MODEL_DIR: str = "./models"
    DRL_MODEL_PATH: str = "./models/drl_agent.zip"
    SENTIMENT_MODEL_PATH: str = "./models/sentiment_model.pt"
    
    # Training Hyperparameters
    LEARNING_RATE: float = 3e-4
    GAMMA: float = 0.99
    BUFFER_SIZE: int = 100000
    BATCH_SIZE: int = 64
    TARGET_UPDATE_FREQ: int = 1000
    
    # Scraping
    SCRAPE_TIMEOUT: int = 30
    MAX_COMMENTS_PER_PAGE: int = 500
    FACEBOOK_COOKIE: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()