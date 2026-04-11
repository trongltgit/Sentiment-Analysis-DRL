# backend/app/services/crawler.py
import os
import httpx
import asyncio
import re
from typing import List, Dict, Set
from urllib.parse import urlparse, parse_qs
import hashlib

class CommentCrawler:
    def __init__(self):
        # Nhiều nguồn free
        self.scrapingbee_token = os.getenv("SCRAPINGBEE_TOKEN")  # 1000 req/tháng free
        self.scraperapi_token = os.getenv("SCRAPERAPI_TOKEN")    # 1000 req/tháng free
        self.proxyscrape_url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    
    def _extract_facebook_post_id(self, url: str) -> str:
        """Extract post ID từ Facebook URL"""
        # Pattern: facebook.com/page/posts/123456
        match = re.search(r'/posts/(\d+)', url)
        if match:
            return match.group(1)
        
        # Pattern: facebook.com/groups/xxx/posts/yyy
        match = re.search(r'/groups/[^/]+/posts/(\d+)', url)
        if match:
            return match.group(1)
        
        # Pattern: facebook.com/permalink.php?story_fbid=123
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'story_fbid' in params:
            return params['story_fbid'][0]
        
        return None
    
    async def crawl(self, url: str, max_comments: int = 30) -> Dict:
        """Thu thập từ nhiều nguồn, ưu tiên chất lượng"""
        
        platform = self._detect_platform(url)
        all_comments = []
        sources_used = []
        errors = []
        
        # === NGUỒN 1: ScrapingBee (chính xác nhất trong free) ===
        if self.scrapingbee_token and len(all_comments) < max_comments:
            try:
                comments = await self._scrape_with_scrapingbee(url, max_comments)
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("scrapingbee")
            except Exception as e:
                errors.append(f"ScrapingBee: {str(e)[:50]}")
        
        # === NGUỒN 2: ScraperAPI ===
        if self.scraperapi_token and len(all_comments) < max_comments:
            try:
                comments = await self._scrape_with_scraperapi(url, max_comments - len(all_comments))
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("scraperapi")
            except Exception as e:
                errors.append(f"ScraperAPI: {str(e)[:50]}")
        
        # === NGUỒN 3: Facebook Basic HTML (mobile version) ===
        if len(all_comments) < max_comments // 2:  # Chỉ dùng khi thiếu
            try:
                comments = await self._scrape_facebook_mobile(url, max_comments - len(all_comments))
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("facebook_mobile")
            except Exception as e:
                errors.append(f"FB Mobile: {str(e)[:50]}")
        
        # === NGUỒN 4: Proxy rotation + requests ===
        if len(all_comments) < 5:  # Chỉ dùng khi rất thiếu
            try:
                comments = await self._scrape_with_proxy(url, max_comments)
                if comments:
                    all_comments.extend(comments)
                    sources_used.append("proxy")
            except Exception as e:
                errors.append(f"Proxy: {str(e)[:50]}")
        
        # Lọc trùng và giới hạn
        unique = self._deduplicate(all_comments)
        final = unique[:max_comments]
        
        return {
            "comments": [{"text": c, "id": f"com_{i}"} for i, c in enumerate(final)],
            "total": len(final),
            "platform": platform,
            "sources": sources_used,
            "errors": errors if not final else [],
            "source": "+".join(sources_used) if sources_used else "none"
        }
    
    async def _scrape_with_scrapingbee(self, url: str, max: int) -> List[str]:
        """ScrapingBee - 1000 req free/tháng, chính xác nhất"""
        
        api_url = "https://app.scrapingbee.com/api/v1"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                api_url,
                params={
                    "api_key": self.scrapingbee_token,
                    "url": url,
                    "render_js": "true",
                    "wait": "8000",  # Đợi lâu hơn cho FB load
                    "premium_proxy": "true",  # Proxy tốt hơn
                    "country_code": "us",
                }
            )
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            comments = []
            
            # Tìm comments trong HTML đã render
            selectors = [
                'div[role="article"] span[dir="auto"]',
                'div[data-ad-preview="message"] span',
                'div[aria-label*="bình luận"] span',
                'div[aria-label*="comment"] span',
                '.userContent',  # Class cũ nhưng vẫn dùng được
                'div._4aen',  # Legacy class
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for el in elements:
                    text = el.get_text(strip=True)
                    if 15 < len(text) < 500 and self._is_valid_comment(text):
                        comments.append(text)
            
            return self._deduplicate(comments)[:max]
    
    async def _scrape_with_scraperapi(self, url: str, max: int) -> List[str]:
        """ScraperAPI - 1000 req free/tháng"""
        
        api_url = f"http://api.scraperapi.com?api_key={self.scraperapi_token}&url={url}&render=true&country_code=us"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(api_url)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tương tự scrapingbee...
            comments = []
            for span in soup.find_all('span', dir='auto'):
                text = span.get_text(strip=True)
                if 15 < len(text) < 500 and self._is_valid_comment(text):
                    comments.append(text)
            
            return self._deduplicate(comments)[:max]
    
    async def _scrape_facebook_mobile(self, url: str, max: int) -> List[str]:
        """Facebook Basic/Mobile - ít JS hơn, dễ parse hơn"""
        
        # Chuyển sang mobile version
        mobile_url = url.replace("www.facebook.com", "m.facebook.com")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        }
        
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            response = await client.get(mobile_url)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            comments = []
            
            # Mobile FB có cấu trúc khác
            for div in soup.find_all('div', class_=lambda x: x and ('comment' in x or '_14v8' in x)):
                text = div.get_text(strip=True)
                if 15 < len(text) < 500:
                    comments.append(text)
            
            return self._deduplicate(comments)[:max]
    
    async def _scrape_with_proxy(self, url: str, max: int) -> List[str]:
        """Dùng proxy free từ ProxyScrape - ít tin cậy nhất"""
        
        # Lấy proxy list
        async with httpx.AsyncClient(timeout=10) as client:
            proxy_list = await client.get(self.proxyscrape_url)
            proxies = [p for p in proxy_list.text.strip().split('\n') if ':' in p]
            
            if not proxies:
                return []
        
        # Thử từng proxy
        for proxy in proxies[:5]:  # Thử 5 proxy
            try:
                proxy_url = f"http://{proxy}"
                
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    timeout=15,
                    follow_redirects=True
                ) as client:
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200 and len(response.text) > 10000:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Tìm text có vẻ là comment
                        comments = []
                        for div in soup.find_all(['div', 'span']):
                            text = div.get_text(strip=True)
                            if 20 < len(text) < 400 and self._looks_like_comment(text):
                                comments.append(text)
                        
                        if len(comments) >= 3:
                            return self._deduplicate(comments)[:max]
                        
            except Exception as e:
                continue  # Thử proxy khác
        
        return []
    
    def _is_valid_comment(self, text: str) -> bool:
        """Kiểm tra text có vẻ là comment hợp lệ"""
        # Loại bỏ link, emoji spam, quá ngắn
        if re.search(r'http[s]?://', text):
            return False
        if len(re.sub(r'[^\w\s]', '', text)) < 10:  # Ít hơn 10 ký tự có nghĩa
            return False
        if text.count('😀') + text.count('😂') > 5:  # Spam emoji
            return False
        return True
    
    def _looks_like_comment(self, text: str) -> bool:
        """Heuristic để nhận diện comment"""
        # Có vẻ như tiếng Việt
        vietnamese_chars = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text.lower()))
        if vietnamese_chars > 0:
            return True
        
        # Có từ khóa thường gặp trong comment
        keywords = ['mua', 'bán', 'giá', 'tốt', 'tệ', 'đẹp', 'xấu', 'nhanh', 'chậm', 'ok', 'cảm ơn', 'shop', 'sp']
        if any(k in text.lower() for k in keywords):
            return True
        
        return False
    
    def _deduplicate(self, comments: List[str]) -> List[str]:
        """Lọc trùng dựa trên nội dung tương tự"""
        seen_hashes = set()
        unique = []
        
        for c in comments:
            # Hash dựa trên 50 ký tự đầu, lowercase, bỏ dấu câu
            normalized = re.sub(r'[^\w\s]', '', c.lower())[:50]
            h = hashlib.md5(normalized.encode()).hexdigest()[:12]
            
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique.append(c)
        
        return unique
    
    def _detect_platform(self, url: str) -> str:
        u = url.lower()
        if "facebook" in u or "fb.com" in u:
            return "facebook"
        if "youtube" in u or "youtu.be" in u:
            return "youtube"
        if "shopee" in u:
            return "shopee"
        return "generic"

crawler = CommentCrawler()
