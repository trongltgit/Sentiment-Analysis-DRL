# backend/app/services/tasks.py
"""
Background tasks for Celery - Phiên bản đã fix
"""
import asyncio
import logging
from datetime import datetime
from celery import shared_task
from app.services.crawler import crawler
from app.services.analyzer import analyzer

logger = logging.getLogger(__name__)

# In-memory store (tạm thời - sau này nên thay bằng database)
analysis_store = {}

@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def analyze_fanpage_task(self, analysis_id: str, url: str, max_comments: int = 100, depth: str = "basic"):
    """
    Task phân tích Fanpage Facebook
    """
    try:
        logger.info(f"🔍 Bắt đầu task {analysis_id} cho URL: {url}")

        # Cập nhật trạng thái đang xử lý
        analysis_store[analysis_id] = {
            "id": analysis_id,
            "url": url,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }

        # === 1. CRAWL COMMENTS ===
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        crawl_result = loop.run_until_complete(crawler.crawl(url, max_comments))
        
        comments_list = [c["text"] for c in crawl_result.get("comments", [])]
        total_comments = len(comments_list)

        logger.info(f"✓ Crawled {total_comments} comments from {crawl_result.get('source', 'none')}")

        if total_comments == 0:
            analysis_store[analysis_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "comments_count": 0,
                "summary": {"positive": 0, "negative": 0, "neutral": 0, "score": 0, "message": "Không tìm thấy bình luận"}
            })
            loop.close()
            return {"status": "completed", "comments_count": 0}

        # === 2. ANALYZE SENTIMENT ===
        logger.info(f"🤖 Phân tích sentiment cho {total_comments} bình luận...")
        analyzed = loop.run_until_complete(analyzer.analyze_batch(comments_list))

        # === 3. Tính toán summary ===
        positive = sum(1 for x in analyzed if x["sentiment"] == "positive")
        negative = sum(1 for x in analyzed if x["sentiment"] == "negative")
        neutral = total_comments - positive - negative

        score = round(((positive - negative) / total_comments) * 100, 2) if total_comments > 0 else 0

        summary = {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "total": total_comments,
            "score": score,
            "sentiment": "positive" if score > 20 else "negative" if score < -20 else "neutral"
        }

        # Cập nhật kết quả cuối cùng
        analysis_store[analysis_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "comments_count": total_comments,
            "summary": summary,
            "details": analyzed[:30],   # chỉ lưu 30 mẫu
            "source": crawl_result.get("source")
        })

        logger.info(f"✅ Hoàn thành task {analysis_id} | Score: {score}")

        loop.close()
        return {"status": "success", "comments_count": total_comments, "score": score}

    except Exception as exc:
        logger.exception(f"❌ Task {analysis_id} failed")
        
        analysis_store[analysis_id] = analysis_store.get(analysis_id, {})
        analysis_store[analysis_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error": str(exc)
        })
        
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
