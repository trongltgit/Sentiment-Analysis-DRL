"""
Web Crawler - Tách riêng comments tốt/xấu/trung lập, lọc trùng & spam
"""
import asyncio
import random
import time
import hashlib
from typing import List, Dict, Set
from urllib.parse import urlparse
import re


class CommentCrawler:
    """Crawl và phân loại comments"""
    
    def __init__(self):
        self.seen_texts: Set[str] = set()  # Track để tránh trùng lặp
    
    def _normalize_text(self, text: str) -> str:
        """Chuẩn hóa text để so sánh trùng lặp"""
        # Bỏ dấu câu, chuyển lowercase, bỏ extra spaces
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = ' '.join(text.split())
        return text.strip()
    
    def _is_duplicate(self, text: str) -> bool:
        """Kiểm tra text đã tồn tại chưa"""
        normalized = self._normalize_text(text)
        if len(normalized) < 10:  # Quá ngắn, coi như trùng
            return True
        
        # Hash để so sánh nhanh
        text_hash = hashlib.md5(normalized.encode()).hexdigest()[:16]
        
        if text_hash in self.seen_texts:
            return True
        
        self.seen_texts.add(text_hash)
        return False
    
    def _is_spam(self, text: str) -> bool:
        """Lọc spam/comments xấu"""
        text_lower = text.lower()
        
        # Spam indicators
        spam_patterns = [
            r'http[s]?://',  # Link
            r'@\w+',         # Mention nhiều
            r'#\w+',         # Hashtag spam
            r'(.)\1{4,}',    # Lặp ký tự (ví dụ: "aaaaa")
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Quá ngắn hoặc quá dài
        if len(text) < 15 or len(text) > 500:
            return True
        
        # Chỉ có emoji/ký tự đặc biệt
        if len(re.sub(r'[^\w\s]', '', text)) < 10:
            return True
        
        return False
    
    def _classify_quality(self, text: str, sentiment: str) -> str:
        """Phân loại chất lượng comment"""
        text_lower = text.lower()
        
        # Từ khóa tích cực mạnh
        strong_positive = ['tuyệt vời', 'xuất sắc', 'hoàn hảo', 'rất hài lòng', 'quá tốt']
        # Từ khóa tiêu cực mạnh  
        strong_negative = ['thất vọng', 'tệ hại', 'kinh khủng', 'tồi tệ', 'khiếu nại', 'lừa đảo']
        # Từ khóa trung lập
        neutral_indicators = ['bình thường', 'tạm được', 'cũng được', 'không có gì']
        
        if sentiment == "positive":
            if any(w in text_lower for w in strong_positive):
                return "high"
            return "medium"
        elif sentiment == "negative":
            if any(w in text_lower for w in strong_negative):
                return "high"  # Negative high = cần chú ý
            return "medium"
        else:
            if any(w in text_lower for w in neutral_indicators):
                return "high"
            return "low"
    
    async def crawl(self, url: str, max_comments: int = 100) -> Dict[str, List[Dict]]:
        """
        Crawl và phân loại comments thành 3 nhóm: tốt, xấu, trung lập
        Trả về dict với keys: good, bad, neutral
        """
        platform = self._detect_platform(url)
        print(f"🔍 Platform: {platform}")
        
        # Reset tracker
        self.seen_texts = set()
        
        # Generate comments theo platform
        if platform == "facebook":
            raw = await self._gen_facebook(url, max_comments)
        elif platform == "youtube":
            raw = await self._gen_youtube(url, max_comments)
        elif platform == "shopee":
            raw = await self._gen_shopee(url, max_comments)
        else:
            raw = await self._gen_generic(url, max_comments)
        
        # Lọc và phân loại
        result = {
            "good": [],      # Tích cực + chất lượng cao
            "bad": [],       # Tiêu cực + cần chú ý
            "neutral": []    # Trung lập hoặc không rõ ràng
        }
        
        for comment in raw:
            text = comment.get("text", "")
            
            # Lọc spam và trùng lặp
            if self._is_spam(text):
                continue
            if self._is_duplicate(text):
                continue
            
            sentiment = comment.get("sentiment", "neutral")
            quality = self._classify_quality(text, sentiment)
            
            # Thêm metadata
            enriched = {
                **comment,
                "quality_score": quality,
                "text_length": len(text),
                "word_count": len(text.split())
            }
            
            # Phân loại vào 3 nhóm
            if sentiment == "positive" and quality in ["high", "medium"]:
                result["good"].append(enriched)
            elif sentiment == "negative":
                result["bad"].append(enriched)  # Tất cả negative đều vào bad
            else:
                result["neutral"].append(enriched)
        
        # Sắp xếp: good theo likes, bad theo urgency, neutral theo confidence
        result["good"].sort(key=lambda x: (x.get("likes", 0), x.get("confidence", 0)), reverse=True)
        result["bad"].sort(key=lambda x: (x.get("confidence", 0), x.get("likes", 0)), reverse=True)
        result["neutral"].sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        print(f"✅ Filtered: {len(result['good'])} good, {len(result['bad'])} bad, {len(result['neutral'])} neutral")
        print(f"   (Removed: {len(raw) - sum(len(v) for v in result.values())} duplicates/spam)")
        
        return result
    
    def _detect_platform(self, url: str) -> str:
        url_lower = url.lower()
        if "facebook" in url_lower:
            return "facebook"
        elif "youtube" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "shopee" in url_lower:
            return "shopee"
        return "generic"
    
    def _url_to_seed(self, url: str) -> int:
        return sum(ord(c) * (i + 1) for i, c in enumerate(url)) % 10000
    
    def _random_time(self) -> str:
        from datetime import datetime, timedelta
        days = random.randint(0, 30)
        return (datetime.now() - timedelta(days=days)).isoformat()
    
    async def _gen_facebook(self, url: str, max: int) -> List[Dict]:
        """Generate Facebook comments - đa dạng, có trùng lặp để test filter"""
        seed = self._url_to_seed(url)
        random.seed(seed)
        
        # Templates với độ dài và sentiment khác nhau
        templates = {
            "positive": [
                {"text": "Sản phẩm tuyệt vời! Mình rất hài lòng 😍", "likes": 50},
                {"text": "Chất lượng quá tốt, ủng hộ shop dài dài", "likes": 30},
                {"text": "Giao hàng nhanh, đóng gói cẩn thận", "likes": 20},
                {"text": "Nhân viên nhiệt tình, sản phẩm đúng mô tả", "likes": 15},
                {"text": "Mua lần thứ 3 rồi, vẫn rất ưng ý!", "likes": 45},
                {"text": "Giá hợp lý, chất lượng xứng đáng", "likes": 25},
                {"text": "Recommend cho mọi người nha! 👍", "likes": 35},
                {"text": "Không thể hài lòng hơn được nữa", "likes": 40},
                # Trùng lặp để test
                {"text": "Sản phẩm tuyệt vời! Mình rất hài lòng 😍", "likes": 10},  # DUPLICATE
                {"text": "Tuyệt vời!", "likes": 5},  # SPAM (quá ngắn)
            ],
            "negative": [
                {"text": "Thất vọng quá, sản phẩm không như hình", "likes": 5},
                {"text": "Giao hàng chậm 3 ngày, không ai liên lạc", "likes": 12},
                {"text": "Chất lượng kém, dùng 2 ngày đã hỏng", "likes": 20},
                {"text": "Giá đắt mà chất lượng tệ, phí tiền", "likes": 8},
                {"text": "Thái độ nhân viên phục vụ quá tệ", "likes": 15},
                {"text": "Khiếu nại hoài không được giải quyết", "likes": 25},
                {"text": "Sản phẩm lỗi, đổi trả rườm rà", "likes": 10},
                {"text": "Không đáng tiền, mọi người đừng mua", "likes": 18},
                # Trùng lặp
                {"text": "Thất vọng quá, sản phẩm không như hình", "likes": 3},  # DUPLICATE
            ],
            "neutral": [
                {"text": "Tạm được, không có gì đặc biệt", "likes": 8},
                {"text": "Giá cả hợp lý, chất lượng tầm trung", "likes": 12},
                {"text": "Giao hàng đúng hẹn, sản phẩm bình thường", "likes": 6},
                {"text": "Cũng được, xài tạm ổn", "likes": 5},
                {"text": "Sẽ cân nhắc mua lại", "likes": 7},
                {"text": "Không tốt không xấu", "likes": 4},
                # Spam
                {"text": "Ok", "likes": 1},  # SPAM
                {"text": "Được", "likes": 2},  # SPAM
            ]
        }
        
        comments = []
        n = min(max, random.randint(60, 150))
        
        for i in range(n):
            # Chọn sentiment với tỷ lệ
            sentiment = random.choices(
                ["positive", "negative", "neutral"],
                weights=[0.4, 0.3, 0.3]
            )[0]
            
            template = random.choice(templates[sentiment])
            
            # Thêm biến thể nhỏ để không phải 100% trùng
            text = template["text"]
            if random.random() > 0.7:
                text += random.choice(["!", " 👍", " ❤️", "..."])
            
            comments.append({
                "id": f"fb_{i}_{int(time.time()*1000)}",
                "text": text,
                "sentiment": sentiment,
                "likes": template["likes"] + random.randint(-5, 10),
                "timestamp": self._random_time(),
                "platform": "facebook"
            })
        
        return comments
    
    async def _gen_youtube(self, url: str, max: int) -> List[Dict]:
        """Generate YouTube comments"""
        seed = self._url_to_seed(url) + 1000
        random.seed(seed)
        
        templates = {
            "positive": [
                {"text": "Video hay quá, rất hữu ích!", "likes": 100},
                {"text": "Giải thích rõ ràng, dễ hiểu", "likes": 80},
                {"text": "Content chất lượng, đăng ký ủng hộ", "likes": 120},
                {"text": "Xem xong hiểu luôn, cảm ơn!", "likes": 60},
            ],
            "negative": [
                {"text": "Video chán, nói lòng vòng không vào đề", "likes": 20},
                {"text": "Sai thông tin, cần fact check lại", "likes": 35},
                {"text": "Âm thanh kém, nghe không rõ", "likes": 15},
                {"text": "Dài dòng quá, 10 phút chỉ có 1 ý", "likes": 25},
            ],
            "neutral": [
                {"text": "Video cũng được, xem cho biết", "likes": 30},
                {"text": "Thông tin bình thường, không mới", "likes": 20},
                {"text": "Cũng ok, nhưng có thể làm tốt hơn", "likes": 25},
            ]
        }
        
        comments = []
        n = min(max, random.randint(80, 200))
        
        for i in range(n):
            sentiment = random.choices(
                ["positive", "negative", "neutral"],
                weights=[0.35, 0.25, 0.4]
            )[0]
            
            template = random.choice(templates[sentiment])
            text = template["text"]
            
            if random.random() > 0.8:
                text += random.choice([" 👍", " 👎", " 🤔", ""])
            
            comments.append({
                "id": f"yt_{i}",
                "text": text,
                "sentiment": sentiment,
                "likes": template["likes"] + random.randint(-10, 20),
                "timestamp": self._random_time(),
                "platform": "youtube"
            })
        
        return comments
    
    async def _gen_shopee(self, url: str, max: int) -> List[Dict]:
        """Generate Shopee reviews"""
        seed = self._url_to_seed(url) + 2000
        random.seed(seed)
        
        templates = {
            "positive": [
                {"text": "Đã nhận hàng, chất lượng tốt đúng mô tả", "rating": 5},
                {"text": "Sản phẩm đẹp, giao nhanh, shop uy tín", "rating": 5},
                {"text": "Rất ưng ý, sẽ ủng hộ shop lần sau", "rating": 5},
                {"text": "Hàng chuẩn auth, đóng gói cẩn thận", "rating": 5},
            ],
            "negative": [
                {"text": "Hàng lỗi, liên hệ shop không trả lời", "rating": 1},
                {"text": "Chất liệu kém, mỏng và dễ rách", "rating": 2},
                {"text": "Size nhỏ hơn bảng size, không mặc vừa", "rating": 2},
                {"text": "Màu sắc khác hình, thất vọng", "rating": 1},
            ],
            "neutral": [
                {"text": "Hàng cũng được, tạm ổn với giá này", "rating": 3},
                {"text": "Không đẹp như hình nhưng cũng tạm dùng", "rating": 3},
                {"text": "Giao hàng bình thường, sản phẩm tạm được", "rating": 3},
            ]
        }
        
        comments = []
        n = min(max, random.randint(30, 80))
        
        for i in range(n):
            sentiment = random.choices(
                ["positive", "negative", "neutral"],
                weights=[0.5, 0.2, 0.3]
            )[0]
            
            template = random.choice(templates[sentiment])
            
            comments.append({
                "id": f"sp_{i}",
                "text": template["text"],
                "sentiment": sentiment,
                "rating": template["rating"],
                "likes": random.randint(0, 30),
                "has_image": random.random() > 0.8,
                "timestamp": self._random_time(),
                "platform": "shopee"
            })
        
        return comments
    
    async def _gen_generic(self, url: str, max: int) -> List[Dict]:
        """Generate generic comments"""
        seed = self._url_to_seed(url)
        random.seed(seed)
        
        domain = urlparse(url).netloc
        
        texts = {
            "positive": [
                f"Rất hài lòng với dịch vụ của {domain}",
                "Sản phẩm chất lượng, đáng tiền",
                "Trải nghiệm tuyệt vời, sẽ quay lại",
            ],
            "negative": [
                f"Thất vọng về {domain}, cần cải thiện",
                "Chất lượng không như mong đợi",
                "Dịch vụ kém, không recommend",
            ],
            "neutral": [
                "Bình thường, không có gì đặc biệt",
                "Cũng được, giá hợp lý",
                "Tạm chấp nhận được",
            ]
        }
        
        comments = []
        n = min(max, random.randint(20, 50))
        
        for i in range(n):
            sentiment = random.choice(["positive", "negative", "neutral"])
            
            comments.append({
                "id": f"gen_{i}",
                "text": random.choice(texts[sentiment]),
                "sentiment": sentiment,
                "likes": random.randint(0, 20),
                "timestamp": self._random_time(),
                "platform": "generic"
            })
        
        return comments


# Singleton
crawler = CommentCrawler()
