"""
Background tasks for Celery
"""
from app.celery_app import celery_app
from app.services.scraper import FacebookScraper
from app.services.analyzer import SentimentAnalyzer
from app.services.drl_agent import DRLAgentService
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def analyze_fanpage_task(self, analysis_id: str, url: str, max_comments: int, depth: str):
    """
    Background task for fanpage analysis
    """
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Step 1: Scrape
        scraper = FacebookScraper()
        comments = loop.run_until_complete(scraper.scrape_comments(url, max_comments))
        
        # Step 2: Analyze
        analyzer = SentimentAnalyzer()
        analyzed = loop.run_until_complete(analyzer.analyze_batch(comments, depth))
        
        # Step 3: DRL Optimization
        drl = DRLAgentService()
        optimized = loop.run_until_complete(drl.optimize_analysis(analyzed))
        
        # Update database with results
        from app.api.routes import analysis_store
        from datetime import datetime
        
        analysis_store[analysis_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "comments": optimized,
            "summary": analyzer.generate_summary(optimized)
        })
        
        loop.close()
        
        return {"status": "success", "comments_count": len(optimized)}
        
    except Exception as exc:
        logger.error(f"Analysis failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def cleanup_old_analyses():
    """Remove analyses older than 24 hours"""
    from app.api.routes import analysis_store
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=24)
    to_remove = [
        aid for aid, data in analysis_store.items() 
        if data.get("created_at") < cutoff
    ]
    
    for aid in to_remove:
        del analysis_store[aid]
    
    return {"cleaned": len(to_remove)}


@celery_app.task
def warm_up_models():
    """Keep models warm to prevent cold start"""
    import torch
    from app.models.sentiment_model import DRLPolicyNetwork
    
    # Simple forward pass to keep GPU/CPU warm
    model = DRLPolicyNetwork()
    dummy_input = torch.randn(1, 793)  # State dimension
    _ = model(dummy_input)
    
    return {"status": "warmed"}