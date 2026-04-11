# backend/app/services/crawler.py - Đơn giản hóa
import httpx
from typing import List, Dict
import os

class CommentCrawler:
    def __init__(self):
        self.access_token = os.getenv("FB_ACCESS_TOKEN")  # Cần set trong Render env vars
    
    async def crawl_facebook(self, url: str, max_comments: int = 50) -> List[str]:
        """Dùng Facebook Graph API thay vì Playwright"""
        if not self.access_token:
            print("⚠️ Chưa có FB_ACCESS_TOKEN, dùng demo data")
            return self._demo_data(url, max_comments)
        
        # Extract post ID từ URL
        post_id = self._extract_post_id(url)
        if not post_id:
            return []
        
        api_url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
        params = {
            'access_token': self.access_token,
            'fields': 'message,from,created_time',
            'limit': max_comments
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, params=params)
            data = resp.json()
            
            comments = []
            for item in data.get('data', []):
                msg = item.get('message', '')
                if msg and len(msg) > 10:
                    comments.append(msg)
            
            return comments
    
    def _extract_post_id(self, url: str) -> str:
        """Extract post ID từ Facebook URL"""
        import re
        # Pattern cho facebook.com/page/posts/post_id
        match = re.search(r'facebook\.com/.+/posts/(\d+)', url)
        if match:
            return match.group(1)
        
        # Pattern cho fb.com/page/posts/post_id  
        match = re.search(r'fb\.com/.+/posts/(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _demo_data(self, url: str, max_comments: int) -> List[str]:
        """Demo data khi không có API token"""
        return [
            "Sản phẩm rất tốt, mình rất hài lòng! Đáng đồng tiền bát gạo.",
            "Giao hàng nhanh, đóng gói cẩn thận. Sẽ ủng hộ shop lần sau.",
            "Chất lượng kém, dùng 2 ngày đã hỏng. Thất vọng quá!",
            "Giá hơi đắt nhưng chất lượng tạm được, không như mong đợi lắm.",
            "Bình thường, không có gì đặc biệt. Cũng được thôi.",
            "Tuyệt vời! Vượt xa mong đợi, recommend cho mọi người.",
            "Dịch vụ tệ, nhân viên thái độ không tốt. Không quay lại nữa.",
            "Tạm ổn, xài được. Không tốt không xấu.",
        ][:max_comments]
    
    async def crawl(self, url: str, max_comments: int = 50) -> Dict:
        comments = await self.crawl_facebook(url, max_comments)
        
        return {
            "comments": [{"text": c, "id": f"c{i}"} for i, c in enumerate(comments)],
            "total": len(comments),
            "platform": "facebook",
            "source": "api" if self.access_token else "demo"
        }

crawler = CommentCrawler()
