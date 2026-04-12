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
        """Thu thập và phân loại comments thành good/bad/neutral"""
        
        all_comments = []
        sources_used = []
        errors = []
        
        # Nguồn 1: ScrapingBee
        if self.scrapingbee_token and len(all_comments) < max_comments:
            try:
                comments = await self._scrape_scrapingbee(url, max_comments)
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("scrapingbee")
                    print(f"✓ ScrapingBee: {len(comments)} comments")
            except Exception as e:
                errors.append(f"ScrapingBee: {str(e)[:100]}")
                print(f"❌ ScrapingBee error: {e}")
        
        # Nguồn 2: ScraperAPI
        if self.scraperapi_token and len(all_comments) < max_comments:
            try:
                comments = await self._scrape_scraperapi(url, max_comments - len(all_comments))
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("scraperapi")
                    print(f"✓ ScraperAPI: {len(comments)} comments")
            except Exception as e:
                errors.append(f"ScraperAPI: {str(e)[:100]}")
                print(f"❌ ScraperAPI error: {e}")
        
        # Nguồn 3: Facebook Mobile
        if len(all_comments) < max_comments // 2:
            try:
                comments = await self._scrape_fb_mobile(url, max_comments - len(all_comments))
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("fb_mobile")
                    print(f"✓ FB Mobile: {len(comments)} comments")
            except Exception as e:
                errors.append(f"FB Mobile: {str(e)[:100]}")
                print(f"❌ FB Mobile error: {e}")
        
        # Lọc trùng
        unique_comments = self._deduplicate(all_comments)
        final_comments = unique_comments[:max_comments]
        
        print(f"📊 Total unique comments: {len(final_comments)}")
        
        # ✅ FIX: Truyền sources_used vào _classify_comments
        classified = self._classify_comments(final_comments, url, sources_used)
        
        return classified
    
    def _classify_comments(self, comments: List[str], url: str, sources_used: List[str]) -> Dict:
        """Phân loại comments thành good/bad/neutral dựa trên từ khóa"""
        
        good_keywords = [
            "tốt", "hay", "đẹp", "thích", "tuyệt", "xuất sắc", "tuyệt vời",
            "hài lòng", "ưng ý", "chất lượng", "recommend", "5 sao", "5 star",
            "good", "great", "excellent", "love", "perfect", "amazing",
            "cảm ơn", "thank", "hữu ích", "đáng tin cậy", "uy tín"
        ]
        
        bad_keywords = [
            "tệ", "kém", "xấu", "chán", "thất vọng", "khiếu nại", "phàn nàn",
            "không hài lòng", "bực mình", "tức giận", "lừa đảo", "lừa",
            "bad", "hate", "terrible", "awful", "worst", "scam", "fraud",
            "chậm", "lỗi", "bug", "crash", "không được", "tệ hại"
        ]
        
        good = []
        bad = []
        neutral = []
        
        for text in comments:
            text_lower = text.lower()
            good_score = sum(1 for kw in good_keywords if kw in text_lower)
            bad_score = sum(1 for kw in bad_keywords if kw in text_lower)
            
            # Xác định sentiment
            if good_score > bad_score:
                sentiment = "good"
                good.append({
                    "text": text,
                    "sentiment": "good",
                    "platform": self._detect_platform(url),
                    "created_at": None
                })
            elif bad_score > good_score:
                sentiment = "bad"
                bad.append({
                    "text": text,
                    "sentiment": "bad",
                    "platform": self._detect_platform(url),
                    "created_at": None
                })
            else:
                sentiment = "neutral"
                neutral.append({
                    "text": text,
                    "sentiment": "neutral",
                    "platform": self._detect_platform(url),
                    "created_at": None
                })
            
            print(f"  [{sentiment.upper()}] {text[:50]}...")
        
        print(f"✅ Classified: {len(good)} good, {len(bad)} bad, {len(neutral)} neutral")
        
        return {
            "good": good,
            "bad": bad,
            "neutral": neutral,
            "total": len(good) + len(bad) + len(neutral),
            "sources": "+".join(sources_used) if sources_used else "none"
        }
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform từ URL"""
        if "facebook.com" in url or "fb.com" in url:
            return "facebook"
        elif "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "tiktok.com" in url:
            return "tiktok"
        elif "shopee.vn" in url:
            return "shopee"
        elif "lazada.vn" in url:
            return "lazada"
        elif "tiki.vn" in url:
            return "tiki"
        else:
            return "web"
    
    async def _scrape_scrapingbee(self, url: str, max: int) -> List[str]:
        """Scrape using ScrapingBee API"""
        if not self.scrapingbee_token:
            return []
        
        api_url = "https://app.scrapingbee.com/api/v1"
        
        try:
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
                
                if resp.status_code != 200:
                    print(f"⚠️ ScrapingBee status: {resp.status_code}")
                    return []
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                comments = []
                selectors = [
                    'div[role="article"] span[dir="auto"]',
                    'div[data-ad-preview="message"] span',
                    'div[aria-label*="bình luận"] span',
                    'div[aria-label*="comment"] span',
                    'div[data-testid="post_message"] span',
                ]
                
                for selector in selectors:
                    for el in soup.select(selector):
                        text = el.get_text(strip=True)
                        if 15 < len(text) < 500 and self._is_valid(text):
                            comments.append(text)
                
                return self._deduplicate(comments)[:max]
                
        except Exception as e:
            print(f"❌ ScrapingBee exception: {e}")
            return []
    
    async def _scrape_scraperapi(self, url: str, max: int) -> List[str]:
        """Scrape using ScraperAPI"""
        if not self.scraperapi_token:
            return []
        
        api_url = f"http://api.scraperapi.com"
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(
                    api_url,
                    params={
                        "api_key": self.scraperapi_token,
                        "url": url,
                        "render": "true",
                        "wait": "10000"
                    }
                )
                
                if resp.status_code != 200:
                    return []
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                comments = []
                for span in soup.find_all('span', dir='auto'):
                    text = span.get_text(strip=True)
                    if 15 < len(text) < 500 and self._is_valid(text):
                        comments.append(text)
                
                return self._deduplicate(comments)[:max]
                
        except Exception as e:
            print(f"❌ ScraperAPI exception: {e}")
            return []
    
    async def _scrape_fb_mobile(self, url: str, max: int) -> List[str]:
        """Scrape Facebook Mobile version"""
        mobile_url = url.replace("www.facebook.com", "m.facebook.com")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        }
        
        try:
            async with httpx.AsyncClient(timeout=30, headers=headers) as client:
                resp = await client.get(mobile_url)
                
                if resp.status_code != 200:
                    return []
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                comments = []
                for div in soup.find_all(['div', 'span']):
                    text = div.get_text(strip=True)
                    if 20 < len(text) < 400 and self._is_valid(text):
                        comments.append(text)
                
                return self._deduplicate(comments)[:max]
                
        except Exception as e:
            print(f"❌ FB Mobile exception: {e}")
            return []
    
    def _is_valid(self, text: str) -> bool:
        """Kiểm tra text có hợp lệ không"""
        if re.search(r'http[s]?://', text):
            return False
        if len(re.sub(r'[^\w\s]', '', text)) < 10:
            return False
        # Đếm số digit đúng cách
        digit_count = len([c for c in text if c.isdigit()])
        if digit_count > len(text) * 0.3:
            return False
        return True
    
    def _deduplicate(self, comments: List[str]) -> List[str]:
        """Loại bỏ comments trùng lặp"""
        seen = set()
        unique = []
        for c in comments:
            key = hashlib.md5(c.lower()[:50].encode()).hexdigest()[:12]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

crawler = CommentCrawler()
