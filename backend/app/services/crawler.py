# backend/app/services/crawler.py
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async  # Thêm thư viện này
from typing import List, Dict, Set
import hashlib
import re


class CommentCrawler:
    def __init__(self):
        self.seen_hashes: Set[str] = set()
    
    def _hash(self, text: str) -> str:
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
        if not text or len(text.strip()) < 10:
            return False
        if re.search(r'http|www\.|\.com|\.vn|bit\.ly', text.lower()):
            return False
        letters = re.sub(r'[^\w\s]', '', text)
        if len(letters) < 5:
            return False
        return True
    
    async def crawl_facebook(self, url: str, max_comments: int = 50) -> List[str]:
        """Crawl Facebook với stealth mode để tránh bị chặn"""
        comments = []
        
        async with async_playwright() as p:
            # Launch với args chống phát hiện
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    # Thêm args chống phát hiện
                    '--disable-blink-features=AutomationControlled',
                    '--disable-automation',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--window-size=1920,1080',
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='vi-VN',
                timezone_id='Asia/Ho_Chi_Minh',
                # Giả lập máy thật
                permissions=['notifications'],
                color_scheme='light',
            )
            
            page = await context.new_page()
            
            # Thêm stealth script
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = { runtime: {} };
            """)
            
            try:
                print(f"🔍 Đang mở {url}...")
                
                # Đi đến trang với timeout dài hơn
                response = await page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=60000
                )
                
                print(f"  ✓ Page loaded: {response.status if response else 'unknown'}")
                
                # Đợi lâu hơn cho Facebook render
                await page.wait_for_timeout(8000)
                
                # Chụp ảnh debug (tùy chọn)
                # await page.screenshot(path='/tmp/debug.png')
                
                # Tìm comments với nhiều selector khác nhau
                selectors = [
                    # Facebook comment selectors (thay đổi thường xuyên)
                    '[data-testid="UFI2Comment/body"] span',
                    'div[role="article"] div[data-ad-preview="message"] span',
                    'div[role="article"] span[dir="auto"]',
                    'div[aria-label*="bình luận"] span',
                    'div[aria-label*="comment"] span',
                    # Generic
                    '.userContent',
                    '.text_exposed_root',
                ]
                
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        print(f"  Thử selector '{selector}': {len(elements)} elements")
                        
                        for element in elements:
                            try:
                                text = await element.inner_text()
                                if self._is_valid(text) and not self._is_duplicate(text):
                                    comments.append(text.strip())
                                    print(f"    ✓ Tìm thấy: {text[:60]}...")
                                    
                                    if len(comments) >= max_comments:
                                        break
                            except:
                                continue
                        
                        if len(comments) >= max_comments:
                            break
                            
                    except Exception as e:
                        print(f"    ✗ Selector lỗi: {e}")
                        continue
                
                # Nếu vẫn không có, thử JavaScript evaluation
                if not comments:
                    print("  ⚠️ Thử trích xuất bằng JavaScript...")
                    js_comments = await page.evaluate('''() => {
                        const texts = [];
                        const elements = document.querySelectorAll('div[role="article"] span, div[dir="auto"] span, .userContent');
                        elements.forEach(el => {
                            const text = el.innerText.trim();
                            if (text.length > 20 && text.length < 500) {
                                texts.push(text);
                            }
                        });
                        return texts;
                    }''')
                    
                    for text in js_comments:
                        if self._is_valid(text) and not self._is_duplicate(text):
                            comments.append(text)
                            if len(comments) >= max_comments:
                                break
                
            except Exception as e:
                print(f"❌ Lỗi crawl: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                await browser.close()
        
        print(f"✅ Tổng cộng tìm thấy {len(comments)} bình luận")
        return comments
    
    async def crawl(self, url: str, max_comments: int = 50) -> Dict:
        """Crawl và trả về kết quả"""
        platform = "facebook" if "facebook" in url.lower() else "generic"
        
        if platform == "facebook":
            raw_comments = await self.crawl_facebook(url, max_comments)
        else:
            raw_comments = []
        
        return {
            "comments": [{"text": c, "id": f"real_{i}"} for i, c in enumerate(raw_comments)],
            "total": len(raw_comments),
            "platform": platform,
            "source": "real_crawl"
        }


# Singleton
crawler = CommentCrawler()
