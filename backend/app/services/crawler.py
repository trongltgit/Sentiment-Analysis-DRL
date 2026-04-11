# backend/app/services/crawler.py
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict, Set
import hashlib
import re
from urllib.parse import urlparse


class CommentCrawler:
    def __init__(self):
        self.seen_hashes: Set[str] = set()
    
    def _hash(self, text: str) -> str:
        """Hash để lọc trùng"""
        normalized = re.sub(r'[^\w\s]', '', text.lower().strip())
        normalized = ' '.join(normalized.split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _is_duplicate(self, text: str) -> bool:
        h = self._hash(text)
        if h in self.seen_hashes:
            return True
        self.seen_hashes.add(h)
        return False
    
    def _is_valid(self, text: str) -> bool:
        """Lọc spam/invalid"""
        if not text or len(text.strip()) < 10:
            return False
        # Bỏ link
        if re.search(r'http|www\.|\.com|\.vn|bit\.ly', text.lower()):
            return False
        # Bỏ emoji-only
        letters = re.sub(r'[^\w\s]', '', text)
        if len(letters) < 5:
            return False
        return True
    
    async def crawl_facebook(self, url: str, max_comments: int = 50) -> List[str]:
        """
        Crawl Facebook comments bằng Playwright (browser thật)
        Lưu ý: Facebook thường yêu cầu đăng nhập để xem comments đầy đủ
        """
        comments = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='vi-VN'
            )
            
            page = await context.new_page()
            
            try:
                print(f"🔍 Đang mở {url}...")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Đợi trang load
                await page.wait_for_timeout(5000)
                
                # Tìm và click "Xem thêm bình luận" nếu có
                for _ in range(3):
                    try:
                        # Các selector khác nhau cho nút "Xem thêm"
                        selectors = [
                            'text="Xem thêm bình luận"',
                            'text="View more comments"',
                            '[role="button"]:has-text("bình luận")',
                            'div[role="button"]:has-text("Xem")'
                        ]
                        
                        for sel in selectors:
                            try:
                                btn = await page.query_selector(sel)
                                if btn:
                                    await btn.click()
                                    await page.wait_for_timeout(2000)
                                    break
                            except:
                                continue
                    except:
                        break
                
                # Cuộn để load thêm comments (lazy load)
                for _ in range(5):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(2000)
                
                # Trích xuất comments - Cần cập nhật selector theo cấu trúc Facebook thực tế
                # Lưu ý: Facebook thay đổi selector thường xuyên
                possible_selectors = [
                    # Các selector phổ biến cho Facebook comments
                    'div[role="article"] div[data-ad-preview="message"] span',
                    'div[role="article"] span[dir="auto"]',
                    'div[data-testid="UFI2Comment/body"] span',
                    'div[aria-label*="bình luận"] span',
                    'div[aria-label*="comment"] span',
                    # Selector chung hơn
                    'div[role="main"] div[dir="auto"] span',
                    'div.x1y1aw1k span.x193iq5w',  # Class-based (hay thay đổi)
                ]
                
                for selector in possible_selectors:
                    elements = await page.query_selector_all(selector)
                    print(f"  Thử selector '{selector}': {len(elements)} elements")
                    
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if self._is_valid(text) and not self._is_duplicate(text):
                                comments.append(text.strip())
                                print(f"  ✓ Tìm thấy: {text[:50]}...")
                                
                                if len(comments) >= max_comments:
                                    break
                        except:
                            continue
                    
                    if len(comments) >= max_comments:
                        break
                
                # Nếu vẫn không có, thử trích xuất tất cả text
                if not comments:
                    print("  ⚠️ Không tìm thấy bằng selector, thử trích xuất tất cả text...")
                    all_texts = await page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('div[role="article"] span, div[dir="auto"] span'))
                            .map(el => el.innerText)
                            .filter(text => text.length > 20 && text.length < 500);
                    }''')
                    
                    for text in all_texts:
                        if self._is_valid(text) and not self._is_duplicate(text):
                            comments.append(text.strip())
                            if len(comments) >= max_comments:
                                break
                
            except Exception as e:
                print(f"❌ Lỗi crawl: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                await browser.close()
        
        print(f"✅ Tìm thấy {len(comments)} bình luận thật")
        return comments
    
    async def crawl(self, url: str, max_comments: int = 50) -> Dict[str, List[Dict]]:
        """
        Crawl và trả về dạng phân loại sẵn (good/bad/neutral)
        Nhưng dùng AI model để phân loại thay vì rule-based
        """
        platform = self._detect_platform(url)
        
        if platform == "facebook":
            raw_comments = await self.crawl_facebook(url, max_comments)
        else:
            # Các platform khác - tương tự
            raw_comments = []
        
        # Trả về dạng đơn giản để AI model phân loại sau
        result = {
            "comments": [{"text": c, "id": f"real_{i}"} for i, c in enumerate(raw_comments)],
            "total": len(raw_comments),
            "platform": platform,
            "source": "real_crawl"
        }
        
        return result
    
    def _detect_platform(self, url: str) -> str:
        u = url.lower()
        if "facebook" in u: return "facebook"
        if "youtube" in u: return "youtube"
        return "generic"


# Singleton
crawler = CommentCrawler()
