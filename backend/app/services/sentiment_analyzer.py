"""
Professional Financial Sentiment Analyzer v2.0
Engine: Groq API (LLaMA 3.3 70B) — FREE
Fallback: VADER + Vietnamese financial keywords
"""
import os
import json
import logging
import re
from typing import List, Dict
from dataclasses import dataclass, field
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# ─── Vietnamese + Financial Keyword Lexicon ──────────────────
FINANCIAL_POSITIVE = [
    # Dịch vụ tốt
    "tuyệt vời", "xuất sắc", "hài lòng", "chuyên nghiệp", "tận tâm",
    "nhanh chóng", "uy tín", "đáng tin", "an toàn", "bảo mật",
    # Sản phẩm tài chính
    "lãi suất tốt", "phí thấp", "miễn phí", "ưu đãi", "sinh lời",
    "tăng trưởng", "lợi nhuận", "hiệu quả", "tiết kiệm được",
    # Ngân hàng số
    "dễ dùng", "mượt", "ổn định", "tiện lợi", "giao diện đẹp",
    # Tích cực chung
    "tốt", "ok", "được", "hay", "đỉnh", "5 sao", "recommend",
]

FINANCIAL_NEGATIVE = [
    # Dịch vụ tệ
    "tệ", "thất vọng", "chán", "lừa đảo", "không hỗ trợ", "thô lỗ",
    "vô trách nhiệm", "không giải quyết", "chậm trễ",
    # Vấn đề tài chính
    "mất tiền", "trừ tiền oan", "phí cao", "lãi suất cao", "thu phí sai",
    "giao dịch thất bại", "chuyển tiền lỗi", "không rút được",
    # App/Tech
    "lỗi", "bug", "crash", "đứng app", "không đăng nhập được",
    "khóa tài khoản", "bảo trì mãi",
    # Cảnh báo
    "nguy hiểm", "rủi ro", "tránh xa", "1 sao", "tố cáo", "khiếu nại",
]


@dataclass
class SentimentResult:
    text: str
    sentiment: str          # positive | negative | neutral
    confidence: float       # 0.0 – 1.0
    confidence_level: str   # very_high | high | medium | low
    keywords: List[str] = field(default_factory=list)
    source: str = "vader"   # groq | vader | keyword


# ─── VADER Fallback ──────────────────────────────────────────
_vader = SentimentIntensityAnalyzer()

def _vader_analyze(text: str) -> SentimentResult:
    scores = _vader.polarity_scores(text)
    compound = scores["compound"]

    # Vietnamese keyword boost
    text_lower = text.lower()
    pos_hits = [kw for kw in FINANCIAL_POSITIVE if kw in text_lower]
    neg_hits = [kw for kw in FINANCIAL_NEGATIVE if kw in text_lower]
    keyword_delta = (len(pos_hits) - len(neg_hits)) * 0.12
    compound = max(-1.0, min(1.0, compound + keyword_delta))

    if compound >= 0.05:
        sentiment, confidence = "positive", min(0.99, 0.60 + abs(compound) * 0.35)
    elif compound <= -0.05:
        sentiment, confidence = "negative", min(0.99, 0.60 + abs(compound) * 0.35)
    else:
        sentiment, confidence = "neutral", 0.55

    def level(c):
        if c >= 0.85: return "very_high"
        if c >= 0.70: return "high"
        if c >= 0.55: return "medium"
        return "low"

    return SentimentResult(
        text=text,
        sentiment=sentiment,
        confidence=round(confidence, 3),
        confidence_level=level(confidence),
        keywords=(pos_hits + neg_hits)[:5],
        source="vader",
    )


# ─── Groq Batch Analyzer ─────────────────────────────────────
class GroqSentimentAnalyzer:
    """Phân tích sentiment bằng Groq LLaMA 3.3 70B — miễn phí"""

    BATCH_SIZE = 20   # Số comment mỗi lần gọi API

    SYSTEM_PROMPT = """Bạn là chuyên gia phân tích cảm xúc tài chính ngân hàng cấp quốc tế.
Nhiệm vụ: Phân tích sentiment của các bình luận khách hàng về sản phẩm/dịch vụ tài chính.

Trả về JSON hợp lệ THEO ĐÚNG FORMAT sau, không có text khác:
{
  "results": [
    {
      "idx": 0,
      "sentiment": "positive|negative|neutral",
      "confidence": 0.92,
      "keywords": ["keyword1", "keyword2"],
      "reason": "Ngắn gọn lý do trong 1 câu"
    }
  ]
}

Quy tắc:
- sentiment: chỉ 1 trong 3 giá trị: positive, negative, neutral
- confidence: số thực 0.0-1.0
- keywords: tối đa 4 từ khóa quan trọng nhất
- Hiểu cả tiếng Việt, tiếng Anh, teencode
- Ngữ cảnh tài chính: ngân hàng, đầu tư, bảo hiểm, fintech"""

    def __init__(self):
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY_DRL", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY_DRL not set")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        logger.info(f"✅ Groq client initialized | model={self.model}")

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Phân tích một batch comments, trả về list SentimentResult"""
        if not texts:
            return []

        # Tạo prompt
        items = "\n".join(
            f'[{i}] "{t[:400]}"' for i, t in enumerate(texts)
        )
        user_msg = f"Phân tích sentiment cho {len(texts)} bình luận sau:\n\n{items}"

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
            raw = resp.choices[0].message.content.strip()

            # Parse JSON
            # Groq đôi khi bọc trong ```json ... ```
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            data = json.loads(raw)

            results_map = {r["idx"]: r for r in data.get("results", [])}
            output = []
            for i, text in enumerate(texts):
                r = results_map.get(i)
                if r:
                    conf = float(r.get("confidence", 0.80))
                    sent = r.get("sentiment", "neutral")
                    if sent not in ("positive", "negative", "neutral"):
                        sent = "neutral"

                    def level(c):
                        if c >= 0.85: return "very_high"
                        if c >= 0.70: return "high"
                        if c >= 0.55: return "medium"
                        return "low"

                    output.append(SentimentResult(
                        text=text,
                        sentiment=sent,
                        confidence=round(conf, 3),
                        confidence_level=level(conf),
                        keywords=r.get("keywords", [])[:5],
                        source="groq",
                    ))
                else:
                    # Fallback cho item không có trong response
                    output.append(_vader_analyze(text))

            return output

        except Exception as e:
            logger.warning(f"Groq batch error: {e} — fallback to VADER")
            return [_vader_analyze(t) for t in texts]

    def generate_financial_insights(
        self,
        positive_pct: float,
        negative_pct: float,
        neutral_pct: float,
        avg_confidence: float,
        top_negative_keywords: List[str],
        top_positive_keywords: List[str],
        url: str,
    ) -> Dict:
        """Sinh phân tích chiến lược tài chính chuyên sâu bằng Groq"""

        prompt = f"""Dữ liệu phân tích sentiment khách hàng tài chính:
URL phân tích: {url}
- Tích cực: {positive_pct:.1f}%
- Tiêu cực: {negative_pct:.1f}%
- Trung lập: {neutral_pct:.1f}%
- Độ tự tin trung bình: {avg_confidence:.1%}
- Từ khóa tiêu cực nổi bật: {', '.join(top_negative_keywords[:5]) or 'N/A'}
- Từ khóa tích cực nổi bật: {', '.join(top_positive_keywords[:5]) or 'N/A'}

Với vai trò chuyên gia tư vấn tài chính ngân hàng quốc tế, hãy trả về JSON:
{{
  "overall_sentiment": "very_positive|positive|mixed|negative|very_negative",
  "trend": "positive|stable|negative",
  "risk_score": 0-100,
  "opportunity_score": 0-100,
  "risks": [
    {{"type": "...", "severity": "high|medium|low", "description": "...", "impact": "..."}}
  ],
  "opportunities": [
    {{"type": "...", "potential": "high|medium|low", "description": "...", "action": "..."}}
  ],
  "recommendations": [
    {{"priority": "high|medium|low", "action": "...", "details": "...", "timeline": "...", "owner": "..."}}
  ],
  "executive_summary": "Tóm tắt 2-3 câu cho ban lãnh đạo"
}}"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia phân tích tài chính ngân hàng. Trả lời bằng JSON hợp lệ, không thêm text khác."},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Groq insights error: {e}")
            return _fallback_insights(positive_pct, negative_pct)


# ─── Fallback Insights ───────────────────────────────────────
def _fallback_insights(pos_pct: float, neg_pct: float) -> Dict:
    if pos_pct >= 60:
        overall = "positive"
    elif neg_pct >= 50:
        overall = "negative"
    elif neg_pct >= 35:
        overall = "mixed"
    else:
        overall = "mixed"

    return {
        "overall_sentiment": overall,
        "trend": "positive" if pos_pct > neg_pct else "negative",
        "risk_score": min(100, int(neg_pct * 1.5)),
        "opportunity_score": min(100, int(pos_pct)),
        "risks": [{"type": "negative_sentiment", "severity": "medium",
                   "description": f"{neg_pct:.1f}% phản hồi tiêu cực",
                   "impact": "Uy tín thương hiệu"}] if neg_pct > 20 else [],
        "opportunities": [{"type": "positive_sentiment", "potential": "high",
                           "description": f"{pos_pct:.1f}% khách hàng hài lòng",
                           "action": "Khai thác testimonial cho marketing"}] if pos_pct > 40 else [],
        "recommendations": [{"priority": "high", "action": "Xem xét phản hồi tiêu cực",
                              "details": "Phân tích root cause", "timeline": "1-2 tuần",
                              "owner": "Customer Experience Team"}],
        "executive_summary": f"Tỷ lệ hài lòng {pos_pct:.1f}%, cần chú ý {neg_pct:.1f}% phản hồi tiêu cực."
    }


# ─── Main Analyzer (Groq primary + VADER fallback) ───────────
class ProfessionalSentimentAnalyzer:
    """Facade: dùng Groq nếu có key, fallback VADER"""

    def __init__(self):
        self._groq: GroqSentimentAnalyzer | None = None
        try:
            self._groq = GroqSentimentAnalyzer()
            logger.info("✅ Using Groq LLaMA 3.3 70B for sentiment analysis")
        except Exception as e:
            logger.warning(f"⚠️ Groq not available ({e}), using VADER fallback")

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        if self._groq:
            results = []
            batch_size = GroqSentimentAnalyzer.BATCH_SIZE
            for i in range(0, len(texts), batch_size):
                batch = texts[i: i + batch_size]
                logger.info(f"   🤖 Groq batch {i//batch_size + 1}: {len(batch)} texts")
                results.extend(self._groq.analyze_batch(batch))
            return results
        else:
            return [_vader_analyze(t) for t in texts]

    def analyze_single(self, text: str) -> SentimentResult:
        return self.analyze_batch([text])[0]

    def generate_insights(
        self,
        results: List[SentimentResult],
        url: str,
    ) -> Dict:
        if not results:
            return _fallback_insights(0, 0)

        total = len(results)
        pos = [r for r in results if r.sentiment == "positive"]
        neg = [r for r in results if r.sentiment == "negative"]
        neu = [r for r in results if r.sentiment == "neutral"]

        pos_pct  = len(pos) / total * 100
        neg_pct  = len(neg) / total * 100
        neu_pct  = len(neu) / total * 100
        avg_conf = sum(r.confidence for r in results) / total

        all_neg_kw = [kw for r in neg for kw in r.keywords]
        all_pos_kw = [kw for r in pos for kw in r.keywords]
        from collections import Counter
        top_neg = [k for k, _ in Counter(all_neg_kw).most_common(5)]
        top_pos = [k for k, _ in Counter(all_pos_kw).most_common(5)]

        base = {
            "positive_pct":  round(pos_pct, 1),
            "negative_pct":  round(neg_pct, 1),
            "neutral_pct":   round(neu_pct, 1),
            "average_confidence": round(avg_conf, 3),
            "confidence_distribution": {
                "very_high": sum(1 for r in results if r.confidence >= 0.85),
                "high":      sum(1 for r in results if 0.70 <= r.confidence < 0.85),
                "medium":    sum(1 for r in results if 0.55 <= r.confidence < 0.70),
                "low":       sum(1 for r in results if r.confidence < 0.55),
            },
            "ai_engine": "groq_llama3.3_70b" if self._groq else "vader_financial",
        }

        if self._groq:
            ai_insights = self._groq.generate_financial_insights(
                pos_pct, neg_pct, neu_pct, avg_conf, top_neg, top_pos, url
            )
        else:
            ai_insights = _fallback_insights(pos_pct, neg_pct)

        return {**base, **ai_insights}
