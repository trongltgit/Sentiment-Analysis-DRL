import os
import httpx
import asyncio
import re
import random
from typing import List, Dict
from datetime import datetime

class CommentCrawler:
    def __init__(self):
        self.scrapingbee_token = os.getenv("SCRAPINGBEE_TOKEN")
        self.scraperapi_token = os.getenv("SCRAPERAPI_TOKEN")
    
    def detect_platform(self, url: str) -> str:
        """Ưu tiên nhận diện Ngân hàng trước, sau đó mới đến các nền tảng khác"""
        url_lower = url.lower()
        
        # --- ƯU TIÊN 1: NHÓM NGÂN HÀNG & TÀI CHÍNH ---
        banks = ['vietcombank', 'techcombank', 'vietinbank', 'bidv', 'acb', 'mbbank', 
                 'sacombank', 'vpbank', 'tpbank', 'vbi', 'shb', 'hdbank', 'agribank']
        if any(bank in url_lower for bank in banks):
            return 'bank_website'

        # --- ƯU TIÊN 2: THƯƠNG MẠI ĐIỆN TỬ & MXH ---
        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        elif any(shop in url_lower for shop in ['shopee.vn', 'lazada.vn', 'tiki.vn']):
            return 'ecommerce'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'google.com/maps' in url_lower:
            return 'google_maps'
        
        return 'generic_website'

    def _classify_comments(self, comments: List[Dict], url: str) -> Dict:
        """Phân loại sentiment với bộ từ khóa tối ưu cho tài chính/ngân hàng"""
        platform = self.detect_platform(url)
        
        # Từ khóa chung + chuyên sâu Ngân hàng
        good_keywords = [
            "tốt", "hài lòng", "uy tín", "nhanh", "tiện lợi", "hiện đại", "nhiệt tình",
            "lãi suất cao", "duyệt nhanh", "app mượt", "miễn phí chuyển tiền", "an toàn",
            "bảo mật", "ưu đãi", "cạnh tranh", "tận tâm", "5 sao"
        ]
        
        bad_keywords = [
            "tệ", "kém", "thất vọng", "chậm", "lỗi", "phí ẩn", "khóa thẻ", "nuốt thẻ",
            "đợi lâu", "thái độ hách dịch", "lừa đảo", "không phản hồi", "rườm rà",
            "phức tạp", "app lag", "treo máy", "phiền phức", "bực mình"
        ]

        good, bad, neutral = [], [], []
        
        for comment in comments:
            text = comment['text'].lower() if isinstance(comment, dict) else str(comment).lower()
            
            # Tính điểm dựa trên từ khóa
            good_score = sum(1 for kw in good_keywords if kw in text)
            bad_score = sum(1 for kw in bad_keywords if kw in text)
            
            comment_obj = {
                'text': comment['text'] if isinstance(comment, dict) else comment,
                'id': f'c_{random.randint(1000, 9999)}',
                'platform': platform,
                'created_at': datetime.now().isoformat()
            }
            
            if good_score > bad_score:
                good.append(comment_obj)
            elif bad_score > good_score:
                bad.append(comment_obj)
            else:
                neutral.append(comment_obj)
        
        return {"good": good, "bad": bad, "neutral": neutral}

    async def crawl(self, url: str, max_comments: int = 100) -> Dict:
        platform = self.detect_platform(url)
        
        # Giả lập cào dữ liệu (Demo Mode)
        if not self.scrapingbee_token and not self.scraperapi_token:
            return self._generate_mock_data(url, platform, max_comments)
        
        # Logic cào thật (Generic Scrape)
        # ... (giữ nguyên logic ScrapingBee cũ của bạn) ...
        return {"good": [], "bad": [], "neutral": []}

    def _generate_mock_data(self, url: str, platform: str, max_comments: int) -> Dict:
        """Dữ liệu mẫu tập trung vào các tình huống thực tế của Ngân hàng"""
        bank_samples = [
            "App dùng rất mượt, chuyển tiền 24/7 không bao giờ lỗi.",
            "Lãi suất tiết kiệm online cao hơn tại quầy, rất ổn.",
            "Nhân viên phòng giao dịch hỗ trợ rất nhiệt tình.",
            "Thủ tục vay vốn rườm rà, bắt mua kèm bảo hiểm mới cho vay.",
            "Phí duy trì tài khoản cao quá, nhiều loại phí ẩn không rõ ràng.",
            "Thẻ bị khóa vô lý, gọi hotline 30 phút không ai nghe máy.",
            "Giao diện mới của App hơi khó dùng so với phiên bản cũ.",
            "Vừa mới nạp tiền vào đã bị trừ phí dịch vụ lạ.",
            "An tâm khi gửi tiền ở đây, uy tín lâu năm.",
            "Rút tiền ATM khác hệ thống bị nuốt thẻ, xử lý quá chậm."
        ]
        
        num_to_gen = min(max_comments, 10)
        chosen = random.sample(bank_samples, num_to_gen)
        return self._classify_comments(chosen, url)

crawler = CommentCrawler()
