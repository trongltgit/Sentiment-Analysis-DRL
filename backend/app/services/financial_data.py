"""
Financial Data Service v2.0
FREE APIs only:
  - yfinance      → VN stocks + international indices
  - frankfurter   → Forex rates (no API key)
  - feedparser    → VnExpress / CafeF RSS news
"""
import logging
import httpx
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)

# ─── Vietnamese Banking Stocks ────────────────────────────────
VN_BANK_STOCKS = {
    "VCB.VN":  "Vietcombank",
    "TCB.VN":  "Techcombank",
    "MBB.VN":  "MB Bank",
    "BID.VN":  "BIDV",
    "ACB.VN":  "ACB",
    "VPB.VN":  "VPBank",
    "HDB.VN":  "HDBank",
    "STB.VN":  "Sacombank",
    "LPB.VN":  "LienVietPostBank",
    "VIB.VN":  "VIB",
}

INTL_INDICES = {
    "^GSPC":  "S&P 500",
    "^IXIC":  "NASDAQ",
    "^N225":  "Nikkei 225",
    "^HSI":   "Hang Seng",
    "GC=F":   "Gold (USD/oz)",
}

# ─── RSS Feeds ────────────────────────────────────────────────
RSS_FEEDS = [
    ("VnExpress - Kinh doanh", "https://vnexpress.net/rss/kinh-doanh.rss"),
    ("VnExpress - Tài chính",  "https://vnexpress.net/rss/kinh-doanh/tien-te.rss"),
    ("CafeF",                  "https://cafef.vn/rss/cafef.rss"),
    ("NDH - Tài chính",        "https://ndh.vn/rss/tai-chinh-ngan-hang.rss"),
]


async def fetch_vn_stocks() -> List[Dict]:
    """Lấy giá cổ phiếu ngân hàng Việt Nam qua yfinance"""
    try:
        import yfinance as yf
        tickers = list(VN_BANK_STOCKS.keys())
        results = []

        loop = asyncio.get_event_loop()

        def _download():
            data = yf.download(
                tickers,
                period="2d",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            return data

        data = await loop.run_in_executor(None, _download)

        for ticker, name in VN_BANK_STOCKS.items():
            try:
                closes = data["Close"][ticker].dropna()
                if len(closes) < 2:
                    continue
                price_today    = float(closes.iloc[-1])
                price_yesterday = float(closes.iloc[-2])
                change_pct     = (price_today - price_yesterday) / price_yesterday * 100

                results.append({
                    "ticker": ticker.replace(".VN", ""),
                    "name":   name,
                    "price":  round(price_today / 1000, 1),   # VND nghìn đồng
                    "change": round(change_pct, 2),
                    "trend":  "up" if change_pct >= 0 else "down",
                })
            except Exception:
                continue

        logger.info(f"✅ Fetched {len(results)} VN bank stocks")
        return results

    except Exception as e:
        logger.warning(f"yfinance error: {e}")
        return _mock_vn_stocks()


async def fetch_international_indices() -> List[Dict]:
    """S&P 500, NASDAQ, Nikkei, Hang Seng, Gold"""
    try:
        import yfinance as yf
        loop = asyncio.get_event_loop()

        def _download():
            return yf.download(
                list(INTL_INDICES.keys()),
                period="2d", interval="1d",
                progress=False, auto_adjust=True
            )

        data = await loop.run_in_executor(None, _download)
        results = []

        for ticker, name in INTL_INDICES.items():
            try:
                closes = data["Close"][ticker].dropna()
                if len(closes) < 2:
                    continue
                p_today = float(closes.iloc[-1])
                p_prev  = float(closes.iloc[-2])
                chg     = (p_today - p_prev) / p_prev * 100

                results.append({
                    "ticker": ticker,
                    "name":   name,
                    "price":  round(p_today, 2),
                    "change": round(chg, 2),
                    "trend":  "up" if chg >= 0 else "down",
                })
            except Exception:
                continue

        return results

    except Exception as e:
        logger.warning(f"Intl indices error: {e}")
        return []


async def fetch_forex_rates() -> Dict:
    """Tỷ giá hối đoái — frankfurter.app (hoàn toàn miễn phí)"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Lấy USD làm gốc
            resp = await client.get(
                "https://api.frankfurter.app/latest",
                params={"from": "USD", "to": "EUR,GBP,JPY,CNY,SGD,KRW,THB,AUD"}
            )
            data = resp.json()
            rates = data.get("rates", {})

            # Thêm VND từ nguồn khác (open.er-api.com)
            resp2 = await client.get(
                "https://open.er-api.com/v6/latest/USD"
            )
            data2 = resp2.json()
            vnd_rate = data2.get("rates", {}).get("VND", 25400)

            return {
                "base": "USD",
                "updated": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "VND":  round(vnd_rate, 0),
                "EUR":  round(rates.get("EUR", 0.92), 4),
                "GBP":  round(rates.get("GBP", 0.79), 4),
                "JPY":  round(rates.get("JPY", 150.0), 2),
                "CNY":  round(rates.get("CNY", 7.24), 4),
                "SGD":  round(rates.get("SGD", 1.34), 4),
                "KRW":  round(rates.get("KRW", 1330), 0),
                "AUD":  round(rates.get("AUD", 1.53), 4),
            }
    except Exception as e:
        logger.warning(f"Forex fetch error: {e}")
        return {"base": "USD", "VND": 25400, "EUR": 0.92, "JPY": 150.0,
                "GBP": 0.79, "CNY": 7.24, "SGD": 1.34, "error": str(e)}


async def fetch_financial_news(limit: int = 15) -> List[Dict]:
    """Tin tức tài chính từ VnExpress, CafeF (RSS miễn phí)"""
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()

    articles = []
    loop = asyncio.get_event_loop()

    def _parse_feeds():
        items = []
        for source_name, feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    title   = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    pub     = entry.get("published", "")
                    link    = entry.get("link", "")

                    if not title:
                        continue

                    # Sentiment từ title + summary
                    text_for_analysis = f"{title}. {summary[:300]}"
                    scores  = vader.polarity_scores(text_for_analysis)
                    compound = scores["compound"]
                    if compound >= 0.05:
                        sent = "positive"
                    elif compound <= -0.05:
                        sent = "negative"
                    else:
                        sent = "neutral"

                    items.append({
                        "title":     title[:120],
                        "source":    source_name,
                        "link":      link,
                        "published": pub[:20] if pub else "",
                        "sentiment": sent,
                        "score":     round(compound, 3),
                    })
            except Exception as ex:
                logger.debug(f"RSS error {source_name}: {ex}")
        return items

    try:
        articles = await loop.run_in_executor(None, _parse_feeds)
        articles.sort(key=lambda x: abs(x["score"]), reverse=True)
        logger.info(f"✅ Fetched {len(articles)} financial news")
    except Exception as e:
        logger.warning(f"News fetch error: {e}")

    return articles[:limit]


def _mock_vn_stocks() -> List[Dict]:
    """Mock data nếu yfinance không hoạt động"""
    import random
    mock = []
    for ticker, name in VN_BANK_STOCKS.items():
        chg = round(random.uniform(-2.5, 3.0), 2)
        mock.append({
            "ticker": ticker.replace(".VN", ""),
            "name":   name,
            "price":  round(random.uniform(15, 95), 1),
            "change": chg,
            "trend":  "up" if chg >= 0 else "down",
        })
    return mock[:6]


# ─── Aggregate endpoint ───────────────────────────────────────
async def get_market_overview() -> Dict:
    """Gộp tất cả dữ liệu thị trường"""
    stocks, forex, news = await asyncio.gather(
        fetch_vn_stocks(),
        fetch_forex_rates(),
        fetch_financial_news(10),
        return_exceptions=True,
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "vn_stocks": stocks if isinstance(stocks, list) else [],
        "forex":     forex  if isinstance(forex,  dict) else {},
        "news":      news   if isinstance(news,   list) else [],
    }
