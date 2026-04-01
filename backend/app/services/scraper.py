from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import asyncio
from typing import List, Dict
import random
import time
from fake_useragent import UserAgent

class FacebookScraper:
    """Crawl bình luận từ Facebook"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.driver = None
    
    def _init_driver(self):
        """Khởi tạo Selenium WebDriver"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={self.ua.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Thêm preferences để tránh detection
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Không load ảnh
            "profile.default_content_setting_values.notifications": 2  # Block notifications
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    async def scrape_comments(self, url: str, max_comments: int = 100) -> List[Dict]:
        """Crawl bình luận từ Facebook post"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._scrape_sync, url, max_comments)
    
    def _scrape_sync(self, url: str, max_comments: int) -> List[Dict]:
        """Scraper đồng bộ"""
        if not self.driver:
            self._init_driver()
        
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)
            
            # Đợi comments load
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='UFI2CommentsList']")
                ))
            except:
                # Thử selector khác
                pass
            
            comments = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = min(max_comments // 10 + 5, 50)
            
            while len(comments) < max_comments and scroll_attempts < max_scrolls:
                # Scroll để load thêm comments
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                
                # Parse comments hiện tại
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Tìm comment elements (selectors có thể thay đổi)
                comment_divs = soup.find_all("div", {"role": "article"})
                
                for div in comment_divs:
                    if len(comments) >= max_comments:
                        break
                    
                    try:
                        comment_data = self._parse_comment(div)
                        if comment_data and comment_data not in comments:
                            comments.append(comment_data)
                    except Exception as e:
                        continue
                
                # Check nếu đã scroll hết
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_height = new_height
            
            return comments[:max_comments]
            
        except Exception as e:
            print(f"Lỗi scrape: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _parse_comment(self, div) -> Dict:
        """Parse thông tin từ comment element"""
        try:
            # Tìm text
            text_elem = div.find("span", string=lambda t: t and len(t) > 5)
            text = text_elem.get_text(strip=True) if text_elem else ""
            
            if not text or len(text) < 3:
                return None
            
            # Tìm author
            author_elem = div.find("a", href=lambda h: h and "profile.php" in h if h else False)
            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
            
            # Tìm likes
            likes_elem = div.find("span", {"data-testid": "UFI2CommentTopReactions/tooltip"})
            likes = 0
            if likes_elem:
                likes_text = likes_elem.get_text(strip=True)
                try:
                    likes = int(likes_text.replace("K", "000").replace("M", "000000"))
                except:
                    pass
            
            # Timestamp
            time_elem = div.find("abbr")
            timestamp = time_elem.get("title") if time_elem else ""
            
            return {
                "text": text,
                "author": author,
                "likes": likes,
                "timestamp": timestamp
            }
            
        except Exception as e:
            return None
    
    def close(self):
        if self.driver:
            self.driver.quit()
