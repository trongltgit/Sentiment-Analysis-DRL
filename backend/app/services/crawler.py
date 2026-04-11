import os
import httpx
import asyncio
import re
import hashlib
from typing import List, Dict, Set
from urllib.parse import urlparse, parse_qs

class CommentCrawler:
    def __init__(self):
        self.scrapingbee_token = os.getenv("SCRAPINGBEE_TOKEN")
        self.scraperapi_token = os.getenv("SCRAPERAPI_TOKEN")
    
    async def crawl(self, url: str, max_comments: int = 25) -> Dict:
        """Thu thập từ nhiều nguồn free"""
        
        all_comments = []
        sources_used = []
        errors = []
        
        # Nguồn 1: ScrapingBee (chính xác nhất)
        if self.scrapingbee_token and len(all_comments) < max_comments:
            try:
                comments = await self._scrape_scrapingbee(url, max_comments)
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("scrapingbee")
                    print(f"✓ ScrapingBee: {len(comments)} comments")
            except Exception as e:
                errors.append(f"ScrapingBee: {str(e)[:50]}")
        
        # Nguồn 2: ScraperAPI
        if self.scraperapi_token and len(all_comments) < max_comments:
            try:
                comments = await self._scrape_scraperapi(url, max_comments - len(all_comments))
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("scraperapi")
                    print(f"✓ ScraperAPI: {len(comments)} comments")
            except Exception as e:
                errors.append(f"ScraperAPI: {str(e)[:50]}")
        
        # Nguồn 3: Facebook Mobile (backup)
        if len(all_comments) < max_comments // 2:
            try:
                comments = await self._scrape_fb_mobile(url, max_comments - len(all_comments))
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("fb_mobile")
                    print(f"✓ FB Mobile: {len(comments)} comments")
            except Exception as e:
                errors.append(f"FB Mobile: {str(e)[:50]}")
        
        # Lọc trùng
        unique = self._deduplicate(all_comments)
        final = unique[:max_comments]
        
        return {
            "comments": [{"text": c, "id": f"c{i}"} for i, c in enumerate(final)],
            "total": len(final),
            "sources": sources_used,
            "errors": errors,
            "source": "+".join(sources_used) if sources_used else "none"
        }
    
    async def _scrape_scrapingbee(self, url: str, max: int) -> List[str]:
        api_url = "https://app.scrapingbee.com/api/v1"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                api_url,
                params={
                    "api_key": self.scrapingbee_token,
                    "url": url,
                    "render_js": "true",
                    "wait": "10000",
                    "premium_proxy": "true",
                    "country_code": "us",
                }
            )
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            comments = []
            selectors = [
                'div[role="article"] span[dir="auto"]',
                'div[data-ad-preview="message"] span',
                'div[aria-label*="bình luận"] span',
                'div[aria-label*="comment"] span',
            ]
            
            for selector in selectors:
                for el in soup.select(selector):
                    text = el.get_text(strip=True)
                    if 15 < len(text) < 500 and self._is_valid(text):
                        comments.append(text)
            
            return self._deduplicate(comments)[:max]
    
    async def _scrape_scraperapi(self, url: str, max: int) -> List[str]:
        api_url = f"http://api.scraperapi.com?api_key={self.scraperapi_token}&url={url}&render=true&wait=10000"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(api_url)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            comments = []
            for span in soup.find_all('span', dir='auto'):
                text = span.get_text(strip=True)
                if 15 < len(text) < 500 and self._is_valid(text):
                    comments.append(text)
            
            return self._deduplicate(comments)[:max]
    
    async def _scrape_fb_mobile(self, url: str, max: int) -> List[str]:
        mobile_url = url.replace("www.facebook.com", "m.facebook.com")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        }
        
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            resp = await client.get(mobile_url)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            comments = []
            for div in soup.find_all(['div', 'span']):
                text = div.get_text(strip=True)
                if 20 < len(text) < 400 and self._is_valid(text):
                    comments.append(text)
            
            return self._deduplicate(comments)[:max]
    
    def _is_valid(self, text: str) -> bool:
        if re.search(r'http[s]?://', text):
            return False
        if len(re.sub(r'[^\w\s]', '', text)) < 10:
            return False
        return True
    
    def _deduplicate(self, comments: List[str]) -> List[str]:
        seen = set()
        unique = []
        for c in comments:
            key = hashlib.md5(c.lower()[:50].encode()).hexdigest()[:12]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

crawler = CommentCrawler()
