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
        logger.info(f"🚀 Task bắt đầu - ID: {analysis_id} | URL: {url}")

        analysis_store[analysis_id] = {
            "id": analysis_id,
            "url": url,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }

        # ====================== CRAWL ======================
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        crawl_result = loop.run_until_complete(crawler.crawl(url, max_comments))

        # BẢO VỆ MẠNH - phòng trường hợp crawler trả về sai kiểu
        comments_data = crawl_result.get("comments")
        if not isinstance(comments_data, list):
            logger.error(f"❌ Crawler trả về sai kiểu comments: {type(comments_data)}")
            comments_data = []

        comments_list = []
        for item in comments_data:
            if isinstance(item, dict) and "text" in item:
                comments_list.append(item["text"])
            elif isinstance(item, str):
                comments_list.append(item)

        total_comments = len(comments_list)
        logger.info(f"✓ Crawled {total_comments} comments | Source: {crawl_result.get('source')}")

        if total_comments == 0:
            analysis_store[analysis_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "comments_count": 0,
                "summary": {"positive": 0, "negative": 0, "neutral": 0, "score": 0, "message": "Không tìm thấy bình luận nào"}
            })
            loop.close()
            return {"status": "completed", "comments_count": 0}

        # ====================== SENTIMENT ANALYSIS ======================
        logger.info(f"🤖 Phân tích sentiment {total_comments} comments...")
        analyzed = loop.run_until_complete(analyzer.analyze_batch(comments_list))

        # Tính summary
        positive = sum(1 for x in analyzed if x.get("sentiment") == "positive")
        negative = sum(1 for x in analyzed if x.get("sentiment") == "negative")
        neutral = total_comments - positive - negative
        score = round(((positive - negative) / total_comments * 100), 2) if total_comments > 0 else 0

        summary = {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "total": total_comments,
            "score": score
        }

        analysis_store[analysis_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "comments_count": total_comments,
            "summary": summary,
            "details": analyzed[:25],
            "source": crawl_result.get("source", "unknown")
        })

        logger.info(f"✅ TASK HOÀN THÀNH - Score: {score} | Positive: {positive}/{total_comments}")
        loop.close()
        return {"status": "success", "score": score}

    except Exception as exc:
        logger.exception(f"💥 Task lỗi hoàn toàn: {exc}")
        analysis_store[analysis_id] = analysis_store.get(analysis_id, {})
        analysis_store[analysis_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error": str(exc)[:200]
        })
        raise
