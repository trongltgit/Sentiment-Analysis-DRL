import os
import httpx
import asyncio
import re
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

class CommentCrawler:
    def __init__(self):
        # Bạn BẮT BUỘC phải có 1 trong 2 token này để cào thật các trang lớn
        self.scrapingbee_token = os.getenv("SCRAPINGBEE_TOKEN")
        self.scraperapi_token = os.getenv("SCRAPERAPI_TOKEN")

    def detect_platform(self, url: str) -> str:
        url_lower = url.lower()
        if any(b in url_lower for b in ['vietcombank', 'techcombank', 'vietinbank', 'bidv', 'acb', 'mbbank']):
            return 'bank_website'
        if any(s in url_lower for s in ['shopee.vn', 'lazada.vn', 'tiki.vn']):
            return 'ecommerce'
        return 'generic_website'

    async def crawl(self, url: str, max_comments: int = 100) -> Dict:
        """Hàm cào chính: Ép buộc cào thật"""
        print(f"🚀 Khởi động cào thật cho: {url}")
        
        # Nếu không có Token, code sẽ dùng httpx cơ bản (dễ bị chặn)
        comments = await self._scrape_real_data(url, max_comments)
        
        # Phân loại dựa trên kết quả thực tế thu được
        return self._classify_comments(comments, url)

    async def _scrape_real_data(self, url: str, max: int) -> List[Dict]:
        """Sử dụng ScrapingBee để lách qua Anti-bot (Hỗ trợ Render JS)"""
        if not self.scrapingbee_token:
            print("⚠️ Cảnh báo: Không có API Token, khả năng cao sẽ bị web chặn.")
            return await self._basic_http_scrape(url, max)

        api_url = "https://app.scrapingbee.com/api/v1"
        params = {
            "api_key": self.scrapingbee_token,
            "url": url,
            "render_js": "true", # Bật JS để cào được các trang Single Page App như Shopee/Bank
            "wait": "3000",      # Đợi 3 giây để nội dung load xong
            "block_ads": "true"
        }

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await client.get(api_url, params=params)
                if resp.status_code == 200:
                    return self._extract_comments_from_html(resp.text, max)
                else:
                    print(f"❌ ScrapingBee trả về lỗi: {resp.status_code}")
                    return []
            except Exception as e:
                print(f"❌ Lỗi kết nối: {e}")
                return []

    def _extract_comments_from_html(self, html_content: str, max_comments: int) -> List[Dict]:
        """Trích xuất text thực tế từ HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted = []
        
        # Tìm các thẻ chứa nội dung có khả năng là bình luận
        # Với web ngân hàng/blog, thường nằm trong các thẻ article, p, hoặc div có class 'comment'
        potential_tags = soup.find_all(['p', 'span', 'div', 'article'])
        
        for tag in potential_tags:
            text = tag.get_text(strip=True)
            # Lọc bỏ rác: Chỉ lấy text từ 20-500 ký tự và không phải code/link
            if 20 < len(text) < 500 and not any(x in text for x in ['{', '}', 'window.', 'function']):
                if text not in [c['text'] for c in extracted]: # Tránh trùng lặp
                    extracted.append({
                        "text": text,
                        "id": f"real_{len(extracted)}",
                        "created_at": datetime.now().isoformat()
                    })
            
            if len(extracted) >= max_comments:
                break
                
        return extracted

    async def _basic_http_scrape(self, url: str, max: int) -> List[Dict]:
        """Cách cào cơ bản (Dễ bị 403 Forbidden trên Render)"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            try:
                resp = await client.get(url)
                return self._extract_comments_from_html(resp.text, max)
            except:
                return []

    def _classify_comments(self, comments: List[Dict], url: str) -> Dict:
        """Giữ nguyên logic phân loại từ khóa đã gửi ở trên"""
        # ... (Sử dụng bộ từ khóa Ngân hàng/Công ty đã cung cấp ở bước trước) ...
        good, bad, neutral = [], [], []
        # (Tự động phân loại comments vào 3 mảng này)
        return {"good": good, "bad": bad, "neutral": neutral}

crawler = CommentCrawler()
