"""
File: backend/app/services/crawler.py
"""
import os
import httpx
import re
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime


POSITIVE_KEYWORDS = [
    # Hài lòng chung
    "tốt", "tuyệt", "tuyệt vời", "xuất sắc", "hoàn hảo", "hài lòng", "ưng ý",
    "thích", "yêu thích", "ổn", "ok", "được", "hay", "đỉnh", "xịn",
    # Khen dịch vụ
    "nhanh", "nhiệt tình", "chu đáo", "chuyên nghiệp", "thân thiện", "tận tâm",
    "hỗ trợ tốt", "phục vụ tốt", "nhân viên tốt", "uy tín", "đáng tin",
    # Khen sản phẩm / app
    "dễ dùng", "tiện lợi", "tiện ích", "giao diện đẹp", "mượt", "ổn định",
    "an toàn", "bảo mật tốt", "lãi suất tốt", "phí thấp", "miễn phí",
    # Recommend
    "recommend", "giới thiệu", "5 sao", "10/10", "đáng dùng", "xứng đáng",
    "sẽ dùng lại", "tiếp tục dùng", "ủng hộ"
]

NEGATIVE_KEYWORDS = [
    # Không hài lòng chung
    "tệ", "tệ quá", "kém", "dở", "thất vọng", "chán", "tức", "bực",
    "không hài lòng", "không ổn", "không tốt", "quá tệ", "cực kỳ tệ",
    # Phàn nàn dịch vụ
    "chậm", "lâu", "trễ", "không phản hồi", "không hỗ trợ", "thái độ tệ",
    "nhân viên thô lỗ", "không giải quyết", "vô trách nhiệm", "lừa đảo",
    # Phàn nàn sản phẩm / app
    "lỗi", "bug", "crash", "đứng app", "không vào được", "đăng nhập không được",
    "chuyển tiền lỗi", "giao dịch thất bại", "mất tiền", "trừ tiền oan",
    "khóa tài khoản", "không rút được", "không nạp được",
    # Phí / lãi
    "phí cao", "lãi suất cao", "thu phí vô lý", "tính phí sai",
    # Cảnh báo mạnh
    "nguy hiểm", "rủi ro", "không nên dùng", "tránh xa", "1 sao", "0 sao",
    "khiếu nại", "tố cáo", "report"
]

NEUTRAL_KEYWORDS = [
    "hỏi", "hỏi giá", "bao nhiêu", "như thế nào", "thủ tục", "hướng dẫn",
    "cảm ơn", "thanks", "ok", "vâng", "ạ", "cho hỏi", "tư vấn",
    "bình thường", "tạm ổn", "tạm được", "cũng được", "không đặc biệt"
]


class CommentCrawler:
    def __init__(self):
        self.scrapingbee_token = os.getenv("SCRAPINGBEE_TOKEN")
        self.scraperapi_token  = os.getenv("SCRAPERAPI_TOKEN")

    def detect_platform(self, url: str) -> str:
        url_lower = url.lower()
        if any(b in url_lower for b in [
            'vietcombank', 'techcombank', 'vietinbank', 'bidv', 'acb', 'mbbank'
        ]):
            return 'bank_website'
        if any(s in url_lower for s in ['shopee.vn', 'lazada.vn', 'tiki.vn']):
            return 'ecommerce'
        if 'facebook.com' in url_lower:
            return 'facebook'
        return 'generic_website'

    async def crawl(self, url: str, max_comments: int = 100) -> Dict:
        print(f"🚀 Bắt đầu crawl: {url}")
        comments = await self._scrape_real_data(url, max_comments)
        return self._classify_comments(comments, url)

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------
    async def _scrape_real_data(self, url: str, max: int) -> List[Dict]:
        if not self.scrapingbee_token:
            print("⚠️ Không có SCRAPINGBEE_TOKEN, dùng httpx cơ bản.")
            return await self._basic_http_scrape(url, max)

        api_url = "https://app.scrapingbee.com/api/v1"
        params = {
            "api_key": self.scrapingbee_token,
            "url": url,
            "render_js": "true",
            "wait": "3000",
            "block_ads": "true",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    return self._extract_comments_from_html(resp.text, max)
                print(f"❌ ScrapingBee lỗi HTTP {resp.status_code}, fallback httpx")
                return await self._basic_http_scrape(url, max)
            except Exception as e:
                print(f"❌ Lỗi kết nối ScrapingBee: {e}")
                return await self._basic_http_scrape(url, max)

    def _extract_comments_from_html(self, html_content: str, max_comments: int) -> List[Dict]:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Xoá script / style để tránh lấy code
        for tag in soup(['script', 'style', 'noscript', 'head']):
            tag.decompose()

        extracted = []
        seen = set()
        for tag in soup.find_all(['p', 'span', 'div', 'article', 'li', 'blockquote']):
            text = tag.get_text(separator=' ', strip=True)
            if (20 < len(text) < 600
                    and text not in seen
                    and not any(x in text for x in [
                        '{', '}', 'window.', 'function(', 'var ', 'const ', 'import '
                    ])):
                seen.add(text)
                extracted.append({
                    "text": text,
                    "id": f"item_{len(extracted)}",
                    "created_at": datetime.now().isoformat(),
                    "platform": "web",
                    "author": "Ẩn danh",
                    "likes": 0,
                })
            if len(extracted) >= max_comments:
                break

        print(f"📝 Trích xuất {len(extracted)} đoạn văn bản")
        return extracted

    async def _basic_http_scrape(self, url: str, max: int) -> List[Dict]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        async with httpx.AsyncClient(
            headers=headers, timeout=20, follow_redirects=True
        ) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return self._extract_comments_from_html(resp.text, max)
            except Exception as e:
                print(f"❌ basic_http_scrape lỗi: {e}")
                return []

    # ------------------------------------------------------------------
    # Phân loại — ĐÂY LÀ HÀM QUAN TRỌNG NHẤT, đã được điền đầy đủ
    # ------------------------------------------------------------------
    def _classify_comments(self, comments: List[Dict], url: str) -> Dict:
        good    = []
        bad     = []
        neutral = []

        for comment in comments:
            text       = comment.get("text", "").lower()
            sentiment, score = self._score_text(text)

            enriched = {
                **comment,
                "sentiment":  sentiment,
                "confidence": round(min(abs(score) / 5, 1.0), 2),
                "score":      score,
            }

            if sentiment == "positive":
                good.append(enriched)
            elif sentiment == "negative":
                bad.append(enriched)
            else:
                neutral.append(enriched)

        print(f"✅ Phân loại xong: {len(good)} good | {len(bad)} bad | {len(neutral)} neutral")
        return {"good": good, "bad": bad, "neutral": neutral}

    def _score_text(self, text: str):
        """
        Trả về (sentiment_label, raw_score).
        raw_score > 0 → positive, < 0 → negative, = 0 → neutral
        """
        pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
        neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

        score = pos_count - neg_count

        if score > 0:
            return "positive", score
        elif score < 0:
            return "negative", score
        else:
            # Kiểm tra từ khoá neutral rõ ràng
            neu_count = sum(1 for kw in NEUTRAL_KEYWORDS if kw in text)
            return "neutral", neu_count


# Singleton dùng trong main.py và tasks.py
crawler = CommentCrawler()
