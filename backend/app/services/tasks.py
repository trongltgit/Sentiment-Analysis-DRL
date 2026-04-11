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
        logger.info(f"🚀 TASK START | ID: {analysis_id} | URL: {url}")

        analysis_store[analysis_id] = {
            "id": analysis_id,
            "url": url,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # ====================== CRAWL ======================
        crawl_result = loop.run_until_complete(crawler.crawl(url, max_comments))

        logger.info(f"📦 Crawl result type: {type(crawl_result)}")

        # BẢO VỆ SIÊU MẠNH
        if not isinstance(crawl_result, dict):
            raise TypeError(f"Crawler trả về sai kiểu: {type(crawl_result)}")

        comments_data = crawl_result.get("comments", [])
        total_from_crawler = crawl_result.get("total", 0)

        logger.info(f"✓ ScrapingBee/others: {total_from_crawler} comments | Type of comments: {type(comments_data)}")

        # Extract comments an toàn
        comments_list = []
        if isinstance(comments_data, list):
            for item in comments_data:
                if isinstance(item, dict) and "text" in item:
                    comments_list.append(item["text"])
                elif isinstance(item, str):
                    comments_list.append(item)
        else:
            logger.error(f"comments_data không phải list mà là {type(comments_data)}")

        total_comments = len(comments_list)
        logger.info(f"✅ Chuẩn bị phân tích {total_comments} comments")

        if total_comments == 0:
            analysis_store[analysis_id].update({
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "comments_count": 0,
                "summary": {"positive": 0, "negative": 0, "neutral": 0, "score": 0, "message": "Không tìm thấy bình luận"}
            })
            loop.close()
            return {"status": "completed", "comments_count": 0}

        # ====================== SENTIMENT ANALYSIS ======================
        analyzed = loop.run_until_complete(analyzer.analyze_batch(comments_list))

        positive = sum(1 for x in analyzed if x.get("sentiment") == "positive")
        negative = sum(1 for x in analyzed if x.get("sentiment") == "negative")
        neutral = total_comments - positive - negative
        score = round((positive - negative) / total_comments * 100, 2) if total_comments > 0 else 0

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
            "details": analyzed[:25]
        })

        logger.info(f"🎉 TASK SUCCESS | Score: {score} | Positive: {positive}/{total_comments}")
        loop.close()
        return {"status": "success", "score": score}

    except Exception as exc:
        logger.exception(f"💥 TASK FAILED: {exc}")
        analysis_store[analysis_id] = analysis_store.get(analysis_id, {})
        analysis_store[analysis_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error": str(exc)[:250]
        })
        raise
