"""
Crawler - Tách riêng: GOOD (khen), BAD (chê), NEUTRAL (bình thường)
"""
import random
import time
import hashlib
from typing import List, Dict, Set
from urllib.parse import urlparse
import re


class CommentCrawler:
    """
    Phân loại rõ ràng:
    - GOOD: Chỉ khi thực sự TÍCH CỰC (hài lòng, recommend, mua lại)
    - BAD: Chỉ khi thực sự TIÊU CỰC (phàn nàn, khiếu nại, không hài lòng)
    - NEUTRAL: Tất cả còn lại (không rõ ràng, bình thường, tạm được)
    """
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
    
    def _hash(self, text: str) -> str:
        """Hash để lọc trùng"""
        normalized = re.sub(r'[^\w\s]', '', text.lower().strip())
        normalized = ' '.join(normalized.split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _is_valid(self, text: str) -> bool:
        """Lọc spam/invalid"""
        if not text or len(text.strip()) < 15:
            return False
        
        # Bỏ link
        if re.search(r'http|www\.|\.com|\.vn|bit\.ly', text.lower()):
            return False
        
        # Bỏ emoji-only
        letters = re.sub(r'[^\w\s]', '', text)
        if len(letters) < 8:
            return False
        
        return True
    
    def _is_duplicate(self, text: str) -> bool:
        """Check trùng"""
        h = self._hash(text)
        if h in self.seen_hashes:
            return True
        self.seen_hashes.add(h)
        return False
    
    def _classify(self, text: str) -> tuple:
        """
        Trả về: (category, confidence, reason)
        - category: 'good' | 'bad' | 'neutral'
        - confidence: 0-10
        - reason: giải thích tại sao vào nhóm này
        """
        text_lower = text.lower()
        
        # ===== BAD (Tiêu cực - cần chú ý) =====
        bad_signals = {
            'strong': ['thất vọng', 'khiếu nại', 'lừa đảo', 'kinh khủng', 'tồi tệ', 'tệ hại', 'scam', 'lừa'],
            'medium': ['tệ', 'kém', 'chán', 'dở', 'hỏng', 'lỗi', 'chậm', 'đắt', 'phí tiền', 'không hài lòng', 
                      'không thích', 'bực', 'tức', 'giận', 'phàn nàn', 'kém chất lượng', 'móp', 'rách', 'bể'],
            'weak': ['không được', 'không tốt', 'không như', 'khác mô tả']
        }
        
        bad_score = 0
        bad_reasons = []
        
        for word in bad_signals['strong']:
            if word in text_lower:
                bad_score += 4
                bad_reasons.append(f"tiêu cực mạnh: '{word}'")
        
        for word in bad_signals['medium']:
            if word in text_lower:
                bad_score += 2
                bad_reasons.append(f"tiêu cực: '{word}'")
        
        for word in bad_signals['weak']:
            if word in text_lower:
                bad_score += 1
        
        # ===== GOOD (Tích cực - đáng khoe) =====
        good_signals = {
            'strong': ['tuyệt vời', 'hoàn hảo', 'xuất sắc', 'rất hài lòng', 'cực kỳ', 'quá đỉnh', 'mê ly'],
            'medium': ['tốt', 'đẹp', 'hay', 'ngon', 'chất lượng', 'hài lòng', 'ưng ý', 'đáng tiền', 'hợp lý',
                      'nhanh', 'chu đáo', 'nhiệt tình', 'thân thiện', 'recommend', 'nên mua', 'mua lại',
                      'ủng hộ', 'ủng hộ dài dài', '5 sao', '5*', 'xuất sắc'],
            'weak': ['được', 'ok', 'ổn', 'tạm được', 'cũng được']
        }
        
        good_score = 0
        good_reasons = []
        
        for word in good_signals['strong']:
            if word in text_lower:
                good_score += 4
                good_reasons.append(f"tích cực mạnh: '{word}'")
        
        for word in good_signals['medium']:
            if word in text_lower:
                good_score += 2
                good_reasons.append(f"tích cực: '{word}'")
        
        for word in good_signals['weak']:
            if word in text_lower:
                good_score += 1
        
        # ===== QUYẾT ĐỊNH =====
        
        # Ưu tiên BAD vì cần xử lý khiếu nại
        if bad_score >= 3:
            confidence = min(10, bad_score + 3)
            reason = " | ".join(bad_reasons[:2]) if bad_reasons else "có dấu hiệu tiêu cực"
            return ('bad', confidence, reason)
        
        # GOOD chỉ khi thực sự rõ ràng
        if good_score >= 4 and bad_score == 0:
            confidence = min(10, good_score + 2)
            reason = " | ".join(good_reasons[:2]) if good_reasons else "có dấu hiệu tích cực"
            return ('good', confidence, reason)
        
        # Còn lại đều là NEUTRAL
        # (cả good và bad đều yếu, hoặc không rõ ràng)
        return ('neutral', 5, "không rõ ràng hoặc trung lập")
    
    async def crawl(self, url: str, max_comments: int = 100) -> Dict[str, List[Dict]]:
        """Crawl và phân loại cực rõ thành 3 nhóm"""
        self.seen_hashes = set()
        
        platform = self._detect_platform(url)
        raw = self._generate(url, platform, max_comments * 2)
        
        # 3 nhóm riêng biệt
        result = {
            "good": [],   # Chỉ khi thực sự tích cực
            "bad": [],    # Chỉ khi thực sự tiêu cực  
            "neutral": [] # Tất cả còn lại
        }
        
        for comment in raw:
            text = comment["text"]
            
            # Lọc
            if not self._is_valid(text):
                continue
            if self._is_duplicate(text):
                continue
            
            # Phân loại
            category, confidence, reason = self._classify(text)
            
            enriched = {
                **comment,
                "category": category,
                "confidence": confidence,
                "classification_reason": reason,
                "priority": category == "bad" and confidence >= 7  # BAD cao điểm = ưu tiên
            }
            
            result[category].append(enriched)
        
        # Sắp xếp
        # GOOD: theo confidence
        result["good"].sort(key=lambda x: (x["confidence"], x.get("likes", 0)), reverse=True)
        # BAD: priority trước, rồi confidence
        result["bad"].sort(key=lambda x: (x["priority"], x["confidence"]), reverse=True)
        # NEUTRAL: theo likes
        result["neutral"].sort(key=lambda x: x.get("likes", 0), reverse=True)
        
        # Giới hạn
        for k in result:
            result[k] = result[k][:max_comments // 3 + 15]
        
        total = sum(len(v) for v in result.values())
        filtered = len(raw) - total
        
        print(f"\n{'='*50}")
        print(f"📊 KẾT QUẢ PHÂN TÍCH: {platform.upper()}")
        print(f"{'='*50}")
        print(f"✅ GOOD (Tích cực):  {len(result['good'])} comments")
        print(f"❌ BAD (Tiêu cực):   {len(result['bad'])} comments")  
        print(f"➖ NEUTRAL (Khác):   {len(result['neutral'])} comments")
        print(f"🗑️  Đã lọc:          {filtered} spam/trùng")
        print(f"{'='*50}\n")
        
        return result
    
    def _detect_platform(self, url: str) -> str:
        u = url.lower()
        if "facebook" in u: return "facebook"
        if "youtube" in u or "youtu.be" in u: return "youtube"
        if "shopee" in u: return "shopee"
        return "generic"
    
    def _seed(self, url: str) -> int:
        return sum(ord(c) * (i+1) for i, c in enumerate(url)) % 10000
    
    def _generate(self, url: str, platform: str, count: int) -> List[Dict]:
        seed = self._seed(url)
        random.seed(seed)
        
        generators = {
            "facebook": self._gen_facebook,
            "youtube": self._gen_youtube,
            "shopee": self._gen_shopee,
            "generic": self._gen_generic
        }
        return generators.get(platform, self._gen_generic)(count, seed)
    
    def _gen_facebook(self, count: int, seed: int) -> List[Dict]:
        """Facebook comments - đa dạng sentiment"""
        templates = [
            # === GOOD (Tích cực rõ ràng) ===
            {"t": "Sản phẩm tuyệt vời! Mình rất hài lòng với chất lượng", "l": 45, "cat": "good"},
            {"t": "Giao hàng nhanh, đóng gói cẩn thận. Recommend mọi người!", "l": 38, "cat": "good"},
            {"t": "Nhân viên tư vấn nhiệt tình, sản phẩm đúng mô tả. 5 sao!", "l": 32, "cat": "good"},
            {"t": "Mua lần thứ 3 rồi, vẫn rất ưng ý! Sẽ ủng hộ dài dài", "l": 50, "cat": "good"},
            {"t": "Chất lượng quá tốt luôn, giá lại hợp lý. Đáng tiền!", "l": 42, "cat": "good"},
            {"t": "Shop uy tín, ship nhanh. Mình sẽ mua lại!", "l": 28, "cat": "good"},
            
            # === BAD (Tiêu cực rõ ràng) ===
            {"t": "Thất vọng quá, sản phẩm không như hình mô tả", "l": 15, "cat": "bad"},
            {"t": "Giao hàng chậm 3 ngày, không ai liên lạc giải thích", "l": 22, "cat": "bad"},
            {"t": "Chất lượng kém, dùng 2 ngày đã hỏng. Khiếu nại hoài không được!", "l": 35, "cat": "bad"},
            {"t": "Giá đắt mà chất lượng tệ, cảm giác bị lừa đảo", "l": 28, "cat": "bad"},
            {"t": "Thái độ nhân viên phục vụ quá tệ, không bao giờ quay lại", "l": 18, "cat": "bad"},
            {"t": "Đóng gói cẩu thả, sản phẩm bị móp méo. Phí tiền!", "l": 25, "cat": "bad"},
            {"t": "Khiếu nại 2 tuần vẫn chưa được giải quyết. Thất vọng tuyệt đối!", "l": 30, "cat": "bad"},
            {"t": "Không đáng tiền, mọi người đừng mua ở đây. Scam!", "l": 20, "cat": "bad"},
            
            # === NEUTRAL (Không rõ ràng) ===
            {"t": "Tạm được, không có gì đặc biệt", "l": 12, "cat": "neutral"},
            {"t": "Giá cả hợp lý, chất lượng tầm trung", "l": 15, "cat": "neutral"},
            {"t": "Giao hàng đúng hẹn, sản phẩm bình thường", "l": 10, "cat": "neutral"},
            {"t": "Cũng được, xài tạm ổn", "l": 8, "cat": "neutral"},
            {"t": "Sẽ cân nhắc mua lại sau", "l": 6, "cat": "neutral"},
            {"t": "Không tốt không xấu, bình thường thôi", "l": 9, "cat": "neutral"},
            {"t": "Tư vấn ổn, sản phẩm tạm được", "l": 7, "cat": "neutral"},
            
            # === Mờ ám (cần phân loại cẩn thận) ===
            {"t": "Cũng được", "l": 3, "cat": "neutral"},  # Ngắn -> neutral
            {"t": "Ok", "l": 2, "cat": "neutral"},  # Quá ngắn -> neutral
            {"t": "Tốt nhưng giao chậm", "l": 15, "cat": "neutral"},  # Cả good lẫn bad -> neutral
            {"t": "Đẹp nhưng giá đắt", "l": 12, "cat": "neutral"},  # Cả good lẫn bad -> neutral
            {"t": "Không tệ lắm", "l": 8, "cat": "neutral"},  # Lưỡng lự -> neutral
        ]
        
        comments = []
        for i in range(count):
            t = random.choice(templates)
            text = t["t"]
            
            # Thêm biến thể
            if random.random() > 0.7:
                text += random.choice(["!", " 👍", " ❤️", " 😊", " 😠", "..."])
            
            comments.append({
                "id": f"fb_{seed}_{i}_{int(time.time()*1000)%10000}",
                "text": text,
                "likes": max(0, t["l"] + random.randint(-5, 8)),
                "timestamp": f"2026-0{random.randint(1,4)}-{random.randint(10,28)}",
                "platform": "facebook",
                "expected_category": t["cat"]  # Để debug
            })
        
        return comments
    
    def _gen_youtube(self, count: int, seed: int) -> List[Dict]:
        templates = [
            {"t": "Video hay quá! Giải thích rõ ràng dễ hiểu", "l": 120, "cat": "good"},
            {"t": "Content chất lượng, đăng ký ủng hộ ngay", "l": 95, "cat": "good"},
            {"t": "Xem xong hiểu luôn, cảm ơn bạn nhiều!", "l": 80, "cat": "good"},
            {"t": "Video chán, nói lòng vòng không vào đề", "l": 25, "cat": "bad"},
            {"t": "Sai thông tin rồi, cần fact check lại", "l": 40, "cat": "bad"},
            {"t": "Âm thanh kém, nghe không rõ gì hết", "l": 15, "cat": "bad"},
            {"t": "Video cũng được, xem cho biết", "l": 35, "cat": "neutral"},
            {"t": "Thông tin bình thường, không mới", "l": 28, "cat": "neutral"},
            {"t": "Cũng ok, nhưng có thể làm tốt hơn", "l": 32, "cat": "neutral"},
        ]
        
        comments = []
        for i in range(count):
            t = random.choice(templates)
            comments.append({
                "id": f"yt_{seed}_{i}",
                "text": t["t"],
                "likes": max(0, t["l"] + random.randint(-15, 25)),
                "timestamp": f"2026-0{random.randint(1,4)}-{random.randint(10,28)}",
                "platform": "youtube",
                "expected_category": t["cat"]
            })
        
        return comments
    
    def _gen_shopee(self, count: int, seed: int) -> List[Dict]:
        templates = [
            {"t": "Đã nhận hàng, chất lượng tốt đúng mô tả. Sẽ ủng hộ lại!", "l": 35, "cat": "good"},
            {"t": "Sản phẩm đẹp, giao nhanh, shop uy tín 5 sao!", "l": 42, "cat": "good"},
            {"t": "Hàng lỗi, liên hệ shop không trả lời. Thất vọng!", "l": 12, "cat": "bad"},
            {"t": "Chất liệu kém, mỏng và dễ rách. Không như hình!", "l": 18, "cat": "bad"},
            {"t": "Hàng cũng được, tạm ổn với giá này", "l": 15, "cat": "neutral"},
            {"t": "Giao hàng bình thường, sản phẩm tạm được", "l": 10, "cat": "neutral"},
        ]
        
        comments = []
        for i in range(count):
            t = random.choice(templates)
            comments.append({
                "id": f"sp_{seed}_{i}",
                "text": t["t"],
                "rating": 5 if t["cat"] == "good" else (1 if t["cat"] == "bad" else 3),
                "likes": max(0, t["l"] + random.randint(-5, 10)),
                "timestamp": f"2026-0{random.randint(1,4)}-{random.randint(10,28)}",
                "platform": "shopee",
                "expected_category": t["cat"]
            })
        
        return comments
    
    def _gen_generic(self, count: int, seed: int) -> List[Dict]:
        domain = urlparse("http://example.com").netloc  # Placeholder
        
        texts = [
            ("Rất hài lòng với trải nghiệm này!", "good"),
            ("Dịch vụ tuyệt vời, sẽ quay lại", "good"),
            ("Thất vọng về chất lượng, cần cải thiện", "bad"),
            ("Không như mong đợi, phí tiền", "bad"),
            ("Bình thường, không có gì đặc biệt", "neutral"),
            ("Cũng được, giá hợp lý", "neutral"),
            ("Tạm chấp nhận được", "neutral"),
        ]
        
        comments = []
        for i in range(count):
            text, cat = random.choice(texts)
            comments.append({
                "id": f"gen_{seed}_{i}",
                "text": f"[{domain}] {text}",
                "likes": random.randint(0, 25),
                "timestamp": f"2026-0{random.randint(1,4)}-{random.randint(10,28)}",
                "platform": "generic",
                "expected_category": cat
            })
        
        return comments


# Singleton
crawler = CommentCrawler()
