"""
Crawler - Tách riêng Good/Bad/Neutral, lọc trùng tuyệt đối
"""
import random
import time
import hashlib
from typing import List, Dict, Set
from urllib.parse import urlparse
import re


class CommentCrawler:
    """Crawl và phân loại comments thành 3 nhóm riêng biệt"""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
    
    def _get_hash(self, text: str) -> str:
        """Tạo hash để so sánh trùng lặp"""
        # Chuẩn hóa: lowercase, bỏ dấu câu, bỏ emoji
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        normalized = ' '.join(normalized.split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _is_valid(self, text: str) -> bool:
        """Kiểm tra comment có hợp lệ không"""
        if not text or len(text) < 15:
            return False
        
        # Bỏ nếu chỉ có emoji/special chars
        letters = re.sub(r'[^\w\s]', '', text)
        if len(letters) < 10:
            return False
        
        # Bỏ spam link
        if re.search(r'http|www\.|\.com|\.vn', text.lower()):
            return False
        
        return True
    
    def _is_duplicate(self, text: str) -> bool:
        """Kiểm tra và track trùng lặp"""
        h = self._get_hash(text)
        if h in self.seen_hashes:
            return True
        self.seen_hashes.add(h)
        return False
    
    def _classify_sentiment(self, text: str) -> str:
        """Phân loại sentiment dựa trên từ khóa"""
        text_lower = text.lower()
        
        # Từ khóa tiêu cực mạnh
        negative_words = [
            'tệ', 'kém', 'chán', 'tồi', 'dở', 'thất vọng', 'buồn', 'ghét', 'không thích',
            'lỗi', 'hỏng', 'khiếu nại', 'phàn nàn', 'giận', 'bực', 'tức', 'kinh khủng',
            'tồi tệ', 'kinh dị', 'quá tệ', 'rất dở', 'chán ngắt', 'phí tiền', 'lừa đảo',
            'gian dối', 'tệ hại', 'kém chất lượng', 'chậm', 'hư', 'bể', 'móp', 'rách'
        ]
        
        # Từ khóa tích cực mạnh
        positive_words = [
            'tốt', 'hay', 'đẹp', 'tuyệt', 'thích', 'hài lòng', 'xuất sắc', 'hoàn hảo',
            'tuyệt vời', 'đáng yêu', 'dễ thương', 'ngon', 'chất lượng', 'ủng hộ', 'mua lại',
            'recommend', 'nên mua', 'đáng tiền', 'hợp lý', 'nhanh', 'chu đáo', 'nhiệt tình',
            'thân thiện', 'pro', 'đỉnh', 'đỉnh cao', 'hết ý', 'quá đã', 'sướng', 'mê'
        ]
        
        # Từ khóa trung lập
        neutral_words = [
            'bình thường', 'tạm', 'cũng được', 'tàm tạm', 'không tốt không xấu',
            'tạm chấp nhận', 'bth', 'bt', 'tạm ổn', 'cỡ này', 'vậy thôi', 'thế thôi'
        ]
        
        neg_score = sum(2 for w in negative_words if w in text_lower)
        pos_score = sum(2 for w in positive_words if w in text_lower)
        neu_score = sum(1 for w in neutral_words if w in text_lower)
        
        # Ưu tiên negative vì cần chú ý
        if neg_score > pos_score:
            return "negative"
        elif pos_score > neg_score:
            return "positive"
        elif neu_score > 0:
            return "neutral"
        else:
            # Không rõ ràng -> neutral
            return "neutral"
    
    def _score_quality(self, text: str, sentiment: str) -> int:
        """Đánh giá chất lượng comment (0-10)"""
        score = 5  # Base
        
        # Độ dài
        if len(text) > 100:
            score += 2
        elif len(text) > 50:
            score += 1
        elif len(text) < 30:
            score -= 1
        
        # Chi tiết (có số, có tính từ cụ thể)
        if re.search(r'\d', text):  # Có số
            score += 1
        if len(text.split()) > 10:  # Nhiều từ
            score += 1
        
        # Sentiment mạnh
        if sentiment == "negative":
            strong_neg = ['thất vọng', 'khiếu nại', 'lừa đảo', 'kinh khủng', 'tồi tệ']
            if any(w in text.lower() for w in strong_neg):
                score += 2  # Cần chú ý cao
        
        return max(0, min(10, score))
    
    async def crawl(self, url: str, max_comments: int = 100) -> Dict[str, List[Dict]]:
        """
        Crawl và trả về 3 nhóm riêng biệt: good, bad, neutral
        """
        # Reset tracker
        self.seen_hashes = set()
        
        # Generate theo platform
        platform = self._detect_platform(url)
        raw = self._generate_comments(url, platform, max_comments * 2)  # Gen nhiều để lọc
        
        # Phân loại và lọc
        result = {
            "good": [],      # Tích cực + chất lượng
            "bad": [],       # Tiêu cực (cần chú ý)
            "neutral": []    # Không rõ ràng
        }
        
        for comment in raw:
            text = comment["text"]
            
            # Lọc
            if not self._is_valid(text):
                continue
            if self._is_duplicate(text):
                continue
            
            sentiment = self._classify_sentiment(text)
            quality = self._score_quality(text, sentiment)
            
            # Phân loại vào nhóm
            enriched = {
                **comment,
                "sentiment": sentiment,
                "quality_score": quality,
                "is_priority": False
            }
            
            if sentiment == "negative":
                # Tất cả negative vào bad, đánh dấu priority nếu quality cao
                enriched["is_priority"] = quality >= 7
                result["bad"].append(enriched)
            elif sentiment == "positive" and quality >= 6:
                # Chỉ positive chất lượng mới vào good
                result["good"].append(enriched)
            else:
                # Còn lại vào neutral
                result["neutral"].append(enriched)
        
        # Sắp xếp
        # Good: theo quality score
        result["good"].sort(key=lambda x: (x["quality_score"], x.get("likes", 0)), reverse=True)
        # Bad: priority trước, rồi đến quality
        result["bad"].sort(key=lambda x: (x["is_priority"], x["quality_score"]), reverse=True)
        # Neutral: theo likes
        result["neutral"].sort(key=lambda x: x.get("likes", 0), reverse=True)
        
        # Giới hạn số lượng
        for key in result:
            result[key] = result[key][:max_comments // 3 + 20]
        
        print(f"✅ {platform}: {len(result['good'])} good, {len(result['bad'])} bad, {len(result['neutral'])} neutral")
        print(f"   (Filtered: {len(raw) - sum(len(v) for v in result.values())} duplicates/invalid)")
        
        return result
    
    def _detect_platform(self, url: str) -> str:
        u = url.lower()
        if "facebook" in u:
            return "facebook"
        elif "youtube" in u or "youtu.be" in u:
            return "youtube"
        elif "shopee" in u:
            return "shopee"
        return "generic"
    
    def _url_seed(self, url: str) -> int:
        return sum(ord(c) * i for i, c in enumerate(url)) % 10000
    
    def _generate_comments(self, url: str, platform: str, count: int) -> List[Dict]:
        """Generate comments đa dạng theo platform"""
        seed = self._url_seed(url)
        random.seed(seed)
        
        generators = {
            "facebook": self._gen_facebook,
            "youtube": self._gen_youtube,
            "shopee": self._gen_shopee,
            "generic": self._gen_generic
        }
        
        gen_func = generators.get(platform, self._gen_generic)
        return gen_func(count, seed)
    
    def _gen_facebook(self, count: int, seed: int) -> List[Dict]:
        """Facebook comments"""
        templates = [
            # Positive - Good
            {"t": "Sản phẩm tuyệt vời! Mình rất hài lòng với chất lượng", "s": "pos", "l": 45},
            {"t": "Giao hàng nhanh, đóng gói cẩn thận. 5 sao!", "s": "pos", "l": 32},
            {"t": "Nhân viên tư vấn nhiệt tình, sản phẩm đúng mô tả", "s": "pos", "l": 28},
            {"t": "Mua lần thứ 3 rồi, vẫn rất ưng ý! Recommend mọi người", "s": "pos", "l": 50},
            {"t": "Chất lượng quá tốt luôn, giá lại hợp lý", "s": "pos", "l": 35},
            {"t": "Shop uy tín, sẽ ủng hộ dài dài ❤️", "s": "pos", "l": 25},
            
            # Positive - Weak (sẽ vào neutral)
            {"t": "Cũng được", "s": "pos_weak", "l": 5},
            {"t": "Ok", "s": "pos_weak", "l": 2},
            {"t": "Tạm", "s": "pos_weak", "l": 3},
            
            # Negative - Bad (cần chú ý)
            {"t": "Thất vọng quá, sản phẩm không như hình mô tả", "s": "neg", "l": 15},
            {"t": "Giao hàng chậm 3 ngày, không ai liên lạc giải thích", "s": "neg", "l": 20},
            {"t": "Chất lượng kém, dùng 2 ngày đã hỏng. Khiếu nại hoài không được", "s": "neg", "l": 35},
            {"t": "Giá đắt mà chất lượng tệ, cảm giác bị lừa", "s": "neg", "l": 18},
            {"t": "Thái độ nhân viên phục vụ quá tệ, không bao giờ quay lại", "s": "neg", "l": 22},
            {"t": "Đóng gói cẩu thả, sản phẩm bị móp méo. Phí tiền", "s": "neg", "l": 25},
            {"t": "Không đáng tiền, mọi người đừng mua ở đây", "s": "neg", "l": 12},
            {"t": "Khiếu nại 2 tuần vẫn chưa được giải quyết. Thất vọng tuyệt đối", "s": "neg", "l": 30},
            
            # Neutral
            {"t": "Tạm được, không có gì đặc biệt", "s": "neu", "l": 8},
            {"t": "Giá cả hợp lý, chất lượng tầm trung", "s": "neu", "l": 15},
            {"t": "Giao hàng đúng hẹn, sản phẩm bình thường", "s": "neu", "l": 12},
            {"t": "Cũng được, xài tạm ổn", "s": "neu", "l": 6},
            {"t": "Sẽ cân nhắc mua lại sau", "s": "neu", "l": 10},
            {"t": "Không tốt không xấu, bthg", "s": "neu", "l": 7},
            
            # Duplicates để test lọc
            {"t": "Sản phẩm tuyệt vời! Mình rất hài lòng với chất lượng", "s": "pos", "l": 8},  # DUP
            {"t": "Thất vọng quá, sản phẩm không như hình mô tả", "s": "neg", "l": 3},  # DUP
        ]
        
        comments = []
        for i in range(count):
            t = random.choice(templates)
            text = t["t"]
            
            # Thêm biến thể nhỏ
            if random.random() > 0.8:
                text += random.choice(["!", " 👍", " 😊", " ❤️", "...", "!!"])
            
            comments.append({
                "id": f"fb_{seed}_{i}",
                "text": text,
                "likes": t["l"] + random.randint(-3, 5),
                "timestamp": f"2026-{random.randint(1,4)}-{random.randint(1,28)}"
            })
        
        return comments
    
    def _gen_youtube(self, count: int, seed: int) -> List[Dict]:
        """YouTube comments"""
        templates = [
            {"t": "Video hay quá! Giải thích rõ ràng dễ hiểu", "s": "pos", "l": 120},
            {"t": "Content chất lượng, đăng ký ủng hộ ngay", "s": "pos", "l": 85},
            {"t": "Xem xong hiểu luôn, cảm ơn bạn nhiều", "s": "pos", "l": 60},
            {"t": "Video chán, nói lòng vòng không vào đề", "s": "neg", "l": 25},
            {"t": "Sai thông tin rồi, cần fact check lại", "s": "neg", "l": 40},
            {"t": "Âm thanh kém, nghe không rõ gì hết", "s": "neg", "l": 15},
            {"t": "Video cũng được, xem cho biết", "s": "neu", "l": 30},
            {"t": "Thông tin bình thường, không mới", "s": "neu", "l": 22},
        ]
        
        comments = []
        for i in range(count):
            t = random.choice(templates)
            comments.append({
                "id": f"yt_{seed}_{i}",
                "text": t["t"],
                "likes": t["l"] + random.randint(-10, 20),
                "timestamp": f"2026-{random.randint(1,4)}-{random.randint(1,28)}"
            })
        
        return comments
    
    def _gen_shopee(self, count: int, seed: int) -> List[Dict]:
        """Shopee reviews"""
        templates = [
            {"t": "Đã nhận hàng, chất lượng tốt đúng mô tả. Sẽ ủng hộ lại", "s": "pos", "l": 25},
            {"t": "Sản phẩm đẹp, giao nhanh, shop uy tín 5 sao", "s": "pos", "l": 40},
            {"t": "Hàng lỗi, liên hệ shop không trả lời. Thất vọng", "s": "neg", "l": 8},
            {"t": "Chất liệu kém, mỏng và dễ rách. Không như hình", "s": "neg", "l": 15},
            {"t": "Hàng cũng được, tạm ổn với giá này", "s": "neu", "l": 12},
        ]
        
        comments = []
        for i in range(count):
            t = random.choice(templates)
            comments.append({
                "id": f"sp_{seed}_{i}",
                "text": t["t"],
                "rating": 5 if t["s"] == "pos" else (1 if t["s"] == "neg" else 3),
                "likes": t["l"] + random.randint(-5, 10),
                "timestamp": f"2026-{random.randint(1,4)}-{random.randint(1,28)}"
            })
        
        return comments
    
    def _gen_generic(self, count: int, seed: int) -> List[Dict]:
        """Generic comments"""
        texts = [
            "Rất hài lòng với trải nghiệm này",
            "Không tốt như mong đợi, cần cải thiện",
            "Bình thường, không có gì đặc biệt",
            "Tuyệt vời, sẽ quay lại lần sau",
            "Thất vọng về chất lượng dịch vụ",
            "Cũng được, giá hợp lý",
        ]
        
        comments = []
        for i in range(count):
            comments.append({
                "id": f"gen_{seed}_{i}",
                "text": random.choice(texts),
                "likes": random.randint(0, 20),
                "timestamp": f"2026-{random.randint(1,4)}-{random.randint(1,28)}"
            })
        
        return comments


# Singleton
crawler = CommentCrawler()
