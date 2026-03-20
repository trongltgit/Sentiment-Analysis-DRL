"""
Facebook Fanpage Scraper Service
"""
import asyncio
import re
import json
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import aiohttp


class FacebookScraper:
    """
    Advanced scraper for Facebook fanpage comments with anti-detection
    """
    
    def __init__(self):
        self.ua = UserAgent()
        self.session_cookies = None
        self.driver = None
    
    async def _init_driver(self):
        """Initialize undetected Chrome driver"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-agent={self.ua.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    async def scrape_comments(self, page_url: str, max_comments: int = 100) -> List[Dict]:
        """
        Scrape comments from Facebook fanpage post
        """
        if not self.driver:
            await self._init_driver()
        
        comments = []
        
        try:
            self.driver.get(page_url)
            await asyncio.sleep(3)  # Wait for page load
            
            # Scroll to load comments
            last_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            
            while len(comments) < max_comments:
                # Scroll down
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await asyncio.sleep(2)
                
                # Extract comments using multiple selectors
                comment_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "[data-testid='UFI2Comment/root_depth_0']"
                )
                
                for elem in comment_elements:
                    if len(comments) >= max_comments:
                        break
                    
                    comment_data = await self._parse_comment_element(elem)
                    if comment_data and not self._is_duplicate(comments, comment_data):
                        comments.append(comment_data)
                
                # Check if reached end
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height
                
        except Exception as e:
            print(f"Scraping error: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return comments
    
    async def _parse_comment_element(self, element) -> Optional[Dict]:
        """Parse individual comment element"""
        try:
            # Extract text
            text_elem = element.find_element(
                By.CSS_SELECTOR, 
                "[data-testid='UFI2Comment/body']"
            )
            text = text_elem.text.strip()
            
            # Extract author
            author_elem = element.find_element(
                By.CSS_SELECTOR, 
                "a[role='link']"
            )
            author = author_elem.text
            
            # Extract timestamp
            time_elem = element.find_element(By.TAG_NAME, "abbr")
            timestamp = time_elem.get_attribute("data-utime")
            
            # Extract likes
            try:
                likes_elem = element.find_element(
                    By.CSS_SELECTOR, 
                    "[data-testid='UFI2Comment/reactions_count']"
                )
                likes_text = likes_elem.text
                likes = int(re.findall(r'\d+', likes_text)[0]) if likes_text else 0
            except:
                likes = 0
            
            # Generate unique ID
            comment_id = hashlib.md5(f"{author}:{text[:50]}".encode()).hexdigest()
            
            return {
                "id": comment_id,
                "text": text,
                "author": author,
                "timestamp": datetime.fromtimestamp(int(timestamp)) if timestamp else datetime.now(),
                "likes": likes,
                "source": "facebook",
                "raw_html": element.get_attribute("outerHTML")[:500]
            }
            
        except Exception as e:
            return None
    
    def _is_duplicate(self, existing_comments: List[Dict], new_comment: Dict) -> bool:
        """Check for duplicate comments"""
        for comment in existing_comments:
            if comment["id"] == new_comment["id"]:
                return True
            # Fuzzy match on text similarity
            if self._text_similarity(comment["text"], new_comment["text"]) > 0.9:
                return True
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def scrape_with_api_fallback(self, page_url: str) -> List[Dict]:
        """
        Fallback method using Facebook Graph API if available
        """
        # This would use official API if credentials are available
        # Implementation depends on having Facebook App credentials
        pass