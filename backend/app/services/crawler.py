"""
Web Crawler cho các nền tảng social media
"""
import asyncio
import random
import time
from typing import List, Dict
from urllib.parse import urlparse
import re


class CommentCrawler:
    """Crawl comments từ nhiều nguồn khác nhau"""
    
    def __init__(self):
        self.platform_patterns = {
            'facebook': r'facebook\.com',
            'youtube': r'youtube\.com|youtu\.be',
            'tiktok': r'tiktok\.com',
            'shopee': r'shopee\.vn|shopee\.co\.id|shopee\.com',
            'lazada': r'lazada\.vn|lazada\.com',
            'tiki': r'tiki\.vn'
        }
    
    async def crawl(self, url: str, max_comments: int = 100) -> List[Dict]:
        """
        Crawl comments từ URL
        """
        platform = self._detect_platform(url)
        print(f"🔍 Platform detected: {platform}")
        
        if platform == "facebook":
            return await self._crawl_facebook(url, max_comments)
        elif platform == "youtube":
            return await self._crawl_youtube(url, max_comments)
        elif platform == "shopee":
            return await self._crawl_shopee(url, max_comments)
        else:
            return await self._crawl_generic(url, max_comments)
    
    def _detect_platform(self, url: str) -> str:
        """Nhận diện nền tảng từ URL"""
        url_lower = url.lower()
        for platform, pattern in self.platform_patterns.items():
            if re.search(pattern, url_lower):
                return platform
        return "generic"
    
    def _url_to_seed(self, url: str) -> int:
        """Chuyển URL thành seed để tạo dữ liệu consistent"""
        return sum(ord(c) * (i + 1) for i, c in enumerate(url)) % 10000
    
    def _random_timestamp(self) -> str:
        """Tạo timestamp ngẫu nhiên trong 30 ngày qua"""
        from datetime import datetime, timedelta
        days_ago = random.randint(0, 30)
        date = datetime.now() - timedelta(days=days_ago)
        return date.isoformat()
    
    async def _crawl_facebook(self, url: str, max: int) -> List[Dict]:
        """Demo crawl Facebook"""
        seed = self._url_to_seed(url)
        random.seed(seed)
        
        templates = {
            'positive': [
                "Sản phẩm tuyệt vời! Mình rất hài lòng 😍",
                "Chất lượng quá tốt luôn, ủng hộ shop dài dài",
                "Giao hàng nhanh, đóng gói cẩn thận, 5 sao!",
                "Nhân viên tư vấn nhiệt tình, sản phẩm đúng mô tả",
                "Mua lần thứ 3 rồi, vẫn rất ưng ý!",
                "Giá hợp lý, chất lượng xứng đáng",
                "Recommend cho mọi người nha!",
                "Không thể hài lòng hơn được nữa ❤️"
            ],
            'negative': [
                "Thất vọng quá, sản phẩm không như hình",
                "Giao hàng chậm 3 ngày, không ai liên lạc",
                "Chất lượng kém, dùng 2 ngày đã hỏng",
                "Giá đắt mà chất lượng tệ, phí tiền",
                "Thái độ nhân viên phục vụ quá tệ",
                "Đóng gói cẩu thả, sản phẩm bị móp méo",
                "Không đáng tiền, mọi người đừng mua",
                "Khiếu nại hoài không được giải quyết 😠"
            ],
            'neutral': [
                "Tạm được, không có gì đặc biệt",
                "Giá cả hợp lý, chất lượng tầm trung",
                "Giao hàng đúng hẹn, sản phẩm bình thường",
                "Cũng được, xài tạm ổn",
                "Không tốt không xấu, bình thường",
                "Sẽ cân nhắc mua lại",
                "Tư vấn ổn, sản phẩm tạm được"
            ],
            'mixed': [
                "Sản phẩm tốt nhưng giao hơi chậm",
                "Chất lượng ok nhưng giá hơi cao",
                "Đóng gói đẹp nhưng sản phẩm không như mong đợi",
                "Nhân viên nhiệt tình nhưng hàng giao sai màu"
            ]
        }
        
        comments = []
        n_comments = min(max, random.randint(50, 200))
        
        for i in range(n_comments):
            sentiment_type = random.choices(
                ['positive', 'negative', 'neutral', 'mixed'],
                weights=[0.35, 0.25, 0.30, 0.10]
            )[0]
            
            text = random.choice(templates[sentiment_type])
            
            # Add variation
            if random.random() > 0.5:
                text += random.choice(["!", "!!", " 😊", " 👍", " ❤️", "", ".", "..."])
            
            comments.append({
                "id": f"fb_{i}_{int(time.time())}",
                "text": text,
                "likes": random.randint(0, 500),
                "replies": random.randint(0, 20),
                "timestamp": self._random_timestamp(),
                "platform": "facebook"
            })
        
        return comments
    
    async def _crawl_youtube(self, url: str, max: int) -> List[Dict]:
        """Demo crawl YouTube"""
        seed = self._url_to_seed(url) + 1000
        random.seed(seed)
        
        templates = {
            'positive': [
                "Video hay quá! Cho em xin 1 tim ❤️",
                "Content chất lượng, đăng ký ủng hộ ngay",
                "Giải thích rõ ràng, dễ hiểu, cảm ơn!",
                "Xem xong hiểu luôn, quá tuyệt",
                "Kênh này đáng sub nhất mình từng xem",
                "Chất lượng video ngày càng tốt, ủng hộ!"
            ],
            'negative': [
                "Video chán quá, nói lòng vòng không vào đề",
                "Sai thông tin rồi bạn ơi, fact check lại đi",
                "Âm thanh kém, nghe không rõ gì hết",
                "Dài dòng quá, 10 phút mà chỉ có 1 ý",
                "Không hữu ích như title nói"
            ],
            'neutral': [
                "Video cũng được, xem cho biết",
                "Thông tin bình thường, không mới",
                "Cũng ok, nhưng có thể làm tốt hơn",
                "Xem qua cho vui thôi"
            ],
            'question': [
                "Cho mình hỏi làm sao để...?",
                "Bạn làm video này bằng phần mềm gì vậy?",
                "Có ai biết link ở phút 3:20 không?",
                "Hướng dẫn chi tiết hơn được không bạn?"
            ]
        }
        
        comments = []
        n_comments = min(max, random.randint(80, 300))
        
        for i in range(n_comments):
            sentiment_type = random.choices(
                ['positive', 'negative', 'neutral', 'question'],
                weights=[0.30, 0.20, 0.35, 0.15]
            )[0]
            
            text = random.choice(templates[sentiment_type])
            
            comments.append({
                "id": f"yt_{i}_{int(time.time())}",
                "text": text,
                "likes": random.randint(0, 1000),
                "replies": random.randint(0, 50),
                "timestamp": self._random_timestamp(),
                "platform": "youtube"
            })
        
        return comments
    
    async def _crawl_shopee(self, url: str, max: int) -> List[Dict]:
        """Demo crawl Shopee"""
        seed = self._url_to_seed(url) + 2000
        random.seed(seed)
        
        templates = {
            'positive': [
                "Đã nhận hàng, chất lượng tốt, đúng mô tả",
                "Sản phẩm đẹp, giao nhanh, shop uy tín",
                "Rất ưng ý, sẽ ủng hộ shop lần sau",
                "Hàng chuẩn auth, đóng gói cẩn thận",
                "Giá rẻ mà chất lượng quá tốt, recommend!",
                "Ship nhanh, sản phẩm y hình, 5 sao"
            ],
            'negative': [
                "Hàng lỗi, liên hệ shop không trả lời",
                "Chất liệu kém, mỏng và dễ rách",
                "Size nhỏ hơn bảng size, không mặc vừa",
                "Màu sắc khác hình, thất vọng",
                "Giao sai sản phẩm, đổi trả rườm rà"
            ],
            'neutral': [
                "Hàng cũng được, tạm ổn với giá này",
                "Không đẹp như hình nhưng cũng tạm dùng",
                "Giao hàng bình thường, sản phẩm tạm được",
                "Chất lượng trung bình, không nổi bật"
            ]
        }
        
        comments = []
        n_comments = min(max, random.randint(20, 100))
        
        for i in range(n_comments):
            sentiment_type = random.choices(
                ['positive', 'negative', 'neutral'],
                weights=[0.50, 0.20, 0.30]
            )[0]
            
            text = random.choice(templates[sentiment_type])
            
            comments.append({
                "id": f"sp_{i}_{int(time.time())}",
                "text": text,
                "rating": 5 if sentiment_type == 'positive' else (1 if sentiment_type == 'negative' else 3),
                "likes": random.randint(0, 50),
                "has_image": random.random() > 0.7,
                "timestamp": self._random_timestamp(),
                "platform": "shopee"
            })
        
        return comments
    
    async def _crawl_generic(self, url: str, max: int) -> List[Dict]:
        """Generic crawler"""
        seed = self._url_to_seed(url)
        random.seed(seed)
        
        domain = urlparse(url).netloc
        
        comments = []
        n_comments = min(max, random.randint(30, 80))
        
        texts = [
            "Sản phẩm rất tốt, đáng mua!",
            "Chất lượng ổn, giá hợp lý",
            "Giao hàng chậm, cần cải thiện",
            "Không như mong đợi",
            "Tuyệt vời!",
            "Bình thường, không có gì đặc biệt",
            "Rất hài lòng với dịch vụ",
            "Thất vọng về chất lượng"
        ]
        
        for i in range(n_comments):
            comments.append({
                "id": f"gen_{i}_{int(time.time())}",
                "text": f"[{domain}] {random.choice(texts)}",
                "likes": random.randint(0, 30),
                "timestamp": self._random_timestamp(),
                "platform": "generic"
            })
        
        return comments
