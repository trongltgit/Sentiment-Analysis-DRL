# backend/app/services/tasks.py
import asyncio
import logging
from datetime import datetime
from celery import shared_task
from app.services.crawler import crawler
from app.services.analyzer import analyzer

logger = logging.getLogger(__name__)

analysis_store = {}

@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def analyze_fanpage_task(self, analysis_id: str, url: str, max_comments: int = 100):
    try:
        logger.info(f"🚀 [TASK START] ID={analysis_id} | URL={url} | Max={max_comments}")

        analysis_store[analysis_id] = {
            "id": analysis_id,
            "url": url,
            "status": "processing",
            "created_at": datetime.utcnow(),
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # ====================== CRAWL ======================
        logger.info("🔍 Đang crawl comments...")
        crawl_result = loop.run_until_complete(crawler.crawl(url, max_comments))

        logger.info(f"📦 Kết quả crawl: {type(crawl_result)} keys={list(crawl_result.keys()) if isinstance(crawl_result, dict) else 'NOT DICT'}")

        # BẢO VỆ RẤT MẠNH
        comments_data = crawl_result.get("comments") if isinstance(crawl_result, dict) else None
        
        if isinstance(comments_data, int):   # ← Đây là nguyên nhân lỗi!
            logger.error(f"❌ BUG: 'comments' là int thay vì list! Value = {comments_data}")
            comments_data = []

        if not isinstance(comments_data, list):
            logger.error(f"❌ 'comments' không phải list, kiểu hiện tại: {type(comments_data)}")
            comments_data = []

        # Extract text an toàn
        comments_list = []
        for item in comments_data:
            if isinstance(item, dict) and "text" in item:
                comments_list.append(item["text"])
            elif isinstance(item, str):
                comments_list.append(item)

        total = len(comments_list)
        logger.info(f"✓ Crawled thành công {total} comments | Source: {crawl_result.get('source', 'unknown')}")

        if total == 0:
            analysis_store[analysis_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "comments_count": 0,
                "summary": {"score": 0, "message": "Không có bình luận"}
            })
            loop.close()
            return {"status": "completed", "comments_count": 0}

        # ====================== SENTIMENT ======================
        logger.info(f"🤖 Bắt đầu phân tích sentiment {total} comments...")
        analyzed = loop.run_until_complete(analyzer.analyze_batch(comments_list))

        positive = sum(1 for x in analyzed if x.get("sentiment") == "positive")
        negative = sum(1 for x in analyzed if x.get("sentiment") == "negative")
        neutral = total - positive - negative
        score = round((positive - negative) / total * 100, 2) if total > 0 else 0

        summary = {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "total": total,
            "score": score
        }

        analysis_store[analysis_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "comments_count": total,
            "summary": summary,
            "details": analyzed[:20]
        })

        logger.info(f"🎉 TASK HOÀN THÀNH - Score: {score}")
        loop.close()
        return {"status": "success", "score": score}

    except Exception as exc:
        logger.exception(f"💥 TASK CRASH: {exc}")
        analysis_store[analysis_id] = analysis_store.get(analysis_id, {})
        analysis_store[analysis_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error": str(exc)[:300]
        })
        raise
