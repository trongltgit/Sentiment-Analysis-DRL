import os
import httpx
import asyncio
import re
import hashlib
import random
from typing import List, Dict, Set
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class CommentCrawler:
    def __init__(self):
        self.scrapingbee_token = os.getenv("SCRAPINGBEE_TOKEN")
        self.scraperapi_token = os.getenv("SCRAPERAPI_TOKEN")
    
    def detect_platform(self, url: str) -> str:
        """Tự động detect platform từ URL"""
        url_lower = url.lower()
        
        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        elif 'shopee.vn' in url_lower:
            return 'shopee'
        elif 'lazada.vn' in url_lower:
            return 'lazada'
        elif 'tiki.vn' in url_lower:
            return 'tiki'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'google.com/maps' in url_lower:
            return 'google_maps'
        elif any(bank in url_lower for bank in ['vietcombank', 'techcombank', 'vietinbank', 'bidv', 'acb', 'mbbank', 'sacombank', 'vpbank']):
            return 'bank_website'
        else:
            return 'generic_website'
    
    async def crawl(self, url: str, max_comments: int = 100) -> Dict:
        """Crawl từ bất kỳ URL nào dựa trên platform detected"""
        
        platform = self.detect_platform(url)
        print(f"🔍 Platform detected: {platform}")
        
        # ✅ DEMO MODE: Nếu không có API keys, dùng mock data
        if not self.scrapingbee_token and not self.scraperapi_token:
            print("⚠️ Không có API keys, dùng demo data")
            return self._generate_mock_data(url, platform, max_comments)
        
        all_comments = []
        sources_used = []
        
        # Crawl theo từng platform
        if platform == 'facebook':
            all_comments = await self._crawl_facebook(url, max_comments)
            sources_used.append('facebook')
        elif platform == 'shopee':
            all_comments = await self._crawl_shopee(url, max_comments)
            sources_used.append('shopee')
        elif platform == 'lazada':
            all_comments = await self._crawl_lazada(url, max_comments)
            sources_used.append('lazada')
        elif platform == 'google_maps':
            all_comments = await self._crawl_google_maps(url, max_comments)
            sources_used.append('google_maps')
        else:
            # Generic crawl cho website bất kỳ
            all_comments = await self._crawl_generic(url, max_comments)
            sources_used.append('website')
        
        # Nếu không lấy được gì, dùng mock data
        if not all_comments:
            print("⚠️ Không lấy được dữ liệu, dùng demo mode")
            return self._generate_mock_data(url, platform, max_comments)
        
        # Phân loại sentiment
        return self._classify_comments(all_comments, url)
    
    def _generate_mock_data(self, url: str, platform: str, max_comments: int) -> Dict:
        """Tạo mock data giống thật cho demo"""
        
        # Mock data theo ngân hàng
        bank_comments = {
            'vietcombank': [
                "Dịch vụ rất tốt, nhân viên nhiệt tình, gửi tiết kiệm lãi suất cao 6.8%/năm",
                "App VCB Digibank dùng rất mượt, chuyển tiền nhanh, không mất phí",
                "Chi nhánh Quận 1 phục vụ tốt, xếp hàng có số thứ tự rõ ràng",
                "Thẻ tín dụng VCB cashback 3% rất hợp lý, đã dùng 2 năm rất hài lòng",
                "Lãi suất vay mua nhà hơi cao so với Techcombank, nhưng uy tín",
                "Thủ tục vay vốn rườm rà, phê duyệt chậm, nhân viên thái độ tệ",
                "ATM hay hết tiền, tết xếp hàng 30 phút mới đến lượt",
                "Phí duy trì tài khoản 11k/tháng hơi cao so với ngân hàng khác",
                "App đôi khi bảo trì cuối tuần, không chuyển tiền được",
                "Lãi suất tiết kiệm giảm liên tục, từ 7% xuống còn 5.5%",
                "Dịch vụ khách hàng 24/7 rất tiện lợi, giải quyết vấn đề nhanh",
                "Internet banking an toàn, có xác thực sinh trắc học",
            ],
            'techcombank': [
                "Techcombank Digital rất hiện đại, giao diện đẹp, dễ dùng",
                "Lãi suất tiết kiệm cao nhất thị trường 7.4%/năm, rất hài lòng",
                "Chuyển tiền quốc tế nhanh, phí hợp lý, dùng cho con du học",
                "Nhân viên tư vấn bảo hiểm liên tục gọi điện làm phiền, khó chịu",
                "Thẻ ghi nợ không miễn phí rút tiền ngoài hệ thống, phí 3.300đ/lần",
                "App hay bị đơ khi check số dư, phải tắt mở lại",
                "Quy trình mở tài khoản online nhanh, không cần ra chi nhánh",
                "Lãi suất vay mua ô tô cạnh tranh, bảo hiểm kèm theo hợp lý",
            ],
            'vietinbank': [
                "VietinBank iPay tiện lợi, thanh toán hóa đơn điện nước không mất phí",
                "Gói tài khoản zero phí rất phù hợp sinh viên, không lo phí duy trì",
                "Chi nhánh nhiều, gần nhà, rút tiền thuận tiện",
                "Thủ tục đăng ký Internet banking phức tạp, phải ra quầy 2 lần",
                "Lãi suất tiết kiệm thấp hơn VCB, nhưng dịch vụ ổn định",
                "Thẻ tín dụng ưu đãi Grab, Shopee nhiều, tiết kiệm được kha khá",
            ],
            'default': [
                "Dịch vụ tốt, nhân viên nhiệt tình hỗ trợ",
                "Giao diện website/app dễ sử dụng, thân thiện",
                "Thủ tục đơn giản, xử lý nhanh gọn",
                "Phí dịch vụ hợp lý, minh bạch",
                "Đôi khi app lag, cần cải thiện hiệu năng",
                "Thủ tục rườm rà, mất thời gian chờ đợi",
                "Nhân viên thái độ không tốt, cần training lại",
                "Phí ẩn nhiều, không rõ ràng với khách hàng",
                "Lãi suất cạnh tranh, tốt hơn ngân hàng khác",
                "Uy tín, đã dùng 5 năm không vấn đề gì",
            ]
        }
        
        # Chọn comments phù hợp
        url_lower = url.lower()
        selected_comments = []
        for bank, comments in bank_comments.items():
            if bank in url_lower:
                selected_comments = comments
                break
        
        if not selected_comments:
            selected_comments = bank_comments['default']
        
        # Random chọn và shuffle
        num_comments = min(max_comments, len(selected_comments))
        chosen = random.sample(selected_comments, num_comments)
        
        # Thêm metadata
        final_comments = []
        for i, text in enumerate(chosen):
            final_comments.append({
                'text': text,
                'id': f'mock_{i}',
                'author': f'User_{random.randint(1000, 9999)}',
                'created_at': datetime.now().isoformat(),
                'likes': random.randint(0, 50),
                'platform': platform
            })
        
        print(f"✅ Generated {len(final_comments)} mock comments for {platform}")
        return self._classify_comments(final_comments, url)
    
    def _classify_comments(self, comments: List[Dict], url: str) -> Dict:
        """Phân loại comments thành good/bad/neutral"""
        
        good_keywords = [
            "tốt", "hay", "đẹp", "thích", "tuyệt", "xuất sắc", "tuyệt vời",
            "hài lòng", "ưng ý", "chất lượng", "recommend", "5 sao", "5 star",
            "good", "great", "excellent", "love", "perfect", "amazing",
            "cảm ơn", "thank", "hữu ích", "đáng tin cậy", "uy tín", "nhanh",
            "tiện lợi", "hiện đại", "dễ dùng", "miễn phí", "không phí",
            "lãi suất cao", "cạnh tranh", "ổn định", "hài lòng", "tận tình"
        ]
        
        bad_keywords = [
            "tệ", "kém", "xấu", "chán", "thất vọng", "khiếu nại", "phàn nàn",
            "không hài lòng", "bực mình", "tức giận", "lừa đảo", "lừa",
            "bad", "hate", "terrible", "awful", "worst", "scam", "fraud",
            "chậm", "lỗi", "bug", "crash", "không được", "tệ hại",
            "rườm rà", "phức tạp", "phiền phức", "mất thời gian", "lag",
            "đơ", "treo", "khó chịu", "thái độ tệ", "phí ẩn", "cao"
        ]
        
        good = []
        bad = []
        neutral = []
        
        for comment in comments:
            # Nếu đã có sentiment từ trước (mock), giữ nguyên
            if isinstance(comment, dict) and 'sentiment' in comment:
                sentiment = comment['sentiment']
                if sentiment == 'good':
                    good.append(comment)
                elif sentiment == 'bad':
                    bad.append(comment)
                else:
                    neutral.append(comment)
                continue
            
            # Phân loại dựa trên text
            text = comment['text'] if isinstance(comment, dict) else comment
            text_lower = text.lower()
            
            good_score = sum(1 for kw in good_keywords if kw in text_lower)
            bad_score = sum(1 for kw in bad_keywords if kw in text_lower)
            
            comment_obj = {
                'text': text,
                'id': f'c{len(good)+len(bad)+len(neutral)}',
                'platform': self.detect_platform(url),
                'created_at': datetime.now().isoformat()
            } if isinstance(comment, str) else comment
            
            if good_score > bad_score:
                good.append(comment_obj)
            elif bad_score > good_score:
                bad.append(comment_obj)
            else:
                neutral.append(comment_obj)
        
        print(f"✅ Classified: {len(good)} good, {len(bad)} bad, {len(neutral)} neutral")
        
        return {
            "good": good,
            "bad": bad,
            "neutral": neutral
        }
    
    async def _crawl_facebook(self, url: str, max: int) -> List[Dict]:
        """Crawl Facebook - hiện tại chỉ trả về mock vì Facebook chặn"""
        print("⚠️ Facebook hiện đang chặn scraper, dùng demo data")
        return []
    
    async def _crawl_shopee(self, url: str, max: int) -> List[Dict]:
        """Crawl Shopee reviews"""
        # TODO: Implement Shopee crawler
        return []
    
    async def _crawl_lazada(self, url: str, max: int) -> List[Dict]:
        """Crawl Lazada reviews"""
        # TODO: Implement Lazada crawler
        return []
    
    async def _crawl_google_maps(self, url: str, max: int) -> List[Dict]:
        """Crawl Google Maps reviews"""
        # TODO: Implement Google Maps crawler
        return []
    
    async def _crawl_generic(self, url: str, max: int) -> List[Dict]:
        """Crawl website bất kỳ bằng ScrapingBee/ScraperAPI"""
        comments = []
        
        if self.scrapingbee_token:
            try:
                comments = await self._scrape_with_scrapingbee(url, max)
            except Exception as e:
                print(f"❌ ScrapingBee failed: {e}")
        
        if not comments and self.scraperapi_token:
            try:
                comments = await self._scrape_with_scraperapi(url, max)
            except Exception as e:
                print(f"❌ ScraperAPI failed: {e}")
        
        return comments
    
    async def _scrape_with_scrapingbee(self, url: str, max: int) -> List[Dict]:
        """Scrape dùng ScrapingBee"""
        api_url = "https://app.scrapingbee.com/api/v1"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                api_url,
                params={
                    "api_key": self.scrapingbee_token,
                    "url": url,
                    "render_js": "true",
                    "wait": "5000",
                }
            )
            
            if resp.status_code != 200:
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Tìm tất cả text có thể là comment/review
            comments = []
            for tag in soup.find_all(['p', 'span', 'div']):
                text = tag.get_text(strip=True)
                if 20 < len(text) < 500 and self._is_valid_comment(text):
                    comments.append({
                        'text': text,
                        'id': f'sb_{len(comments)}',
                        'platform': 'website'
                    })
            
            return comments[:max]
    
    async def _scrape_with_scraperapi(self, url: str, max: int) -> List[Dict]:
        """Scrape dùng ScraperAPI"""
        # Tương tự ScrapingBee
        return []
    
    def _is_valid_comment(self, text: str) -> bool:
        """Kiểm tra text có phải comment hợp lệ"""
        if len(text) < 15:
            return False
        if re.search(r'http[s]?://', text):
            return False
        # Loại bỏ text có quá nhiều số
        digits = sum(c.isdigit() for c in text)
        if digits > len(text) * 0.3:
            return False
        return True

crawler = CommentCrawler()
