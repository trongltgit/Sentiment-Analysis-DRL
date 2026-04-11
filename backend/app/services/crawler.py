# backend/app/services/crawler.py
import os
import httpx
from bs4 import BeautifulSoup

class CommentCrawler:
    def __init__(self):
        self.token = os.getenv("SCRAPINGBEE_TOKEN")
        if not self.token:
            raise ValueError("Thiếu SCRAPINGBEE_TOKEN")
    
    async def crawl_facebook(self, url: str, max_comments: int = 30) -> list:
        """Dùng ScrapingBee free tier"""
        
        api_url = "https://app.scrapingbee.com/api/v1"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                api_url,
                params={
                    "api_key": self.token,
                    "url": url,
                    "render_js": "true",
                    "wait": "5000",
                    "extract_rules": '{"comments":"div[role=article] span"}'
                }
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            comments = []
            for span in soup.find_all('span'):
                text = span.get_text(strip=True)
                if 20 < len(text) < 500:
                    comments.append(text)
            
            # Lọc trùng
            seen = set()
            unique = []
            for c in comments:
                key = c.lower()[:50]
                if key not in seen:
                    seen.add(key)
                    unique.append(c)
            
            return unique[:max_comments]
