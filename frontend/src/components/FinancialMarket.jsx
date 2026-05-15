// FinancialMarket.jsx — Live market data panel
import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Newspaper, DollarSign } from 'lucide-react';
import axios from 'axios';

const API = '/api/v1/market';

function ChangeTag({ change }) {
  const up = change >= 0;
  return (
    <span className={`flex items-center gap-0.5 text-xs font-semibold ${up ? 'text-emerald-400' : 'text-red-400'}`}>
      {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
      {up ? '+' : ''}{change?.toFixed(2)}%
    </span>
  );
}

function SentimentDot({ sentiment }) {
  const colors = { positive: 'bg-emerald-400', negative: 'bg-red-400', neutral: 'bg-gray-400' };
  return <span className={`inline-block w-2 h-2 rounded-full ${colors[sentiment] || 'bg-gray-400'}`} />;
}

export default function FinancialMarket() {
  const [stocks, setStocks]   = useState([]);
  const [forex,  setForex]    = useState(null);
  const [news,   setNews]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState('');
  const [tab, setTab] = useState('stocks'); // stocks | forex | news

  const load = async () => {
    setLoading(true);
    try {
      const [sRes, fRes, nRes] = await Promise.allSettled([
        axios.get(`${API}/stocks`),
        axios.get(`${API}/forex`),
        axios.get(`${API}/news?limit=10`),
      ]);
      if (sRes.status === 'fulfilled') setStocks(sRes.value.data.stocks || []);
      if (fRes.status === 'fulfilled') setForex(fRes.value.data);
      if (nRes.status === 'fulfilled') setNews(nRes.value.data.articles || []);
      setLastUpdate(new Date().toLocaleTimeString('vi-VN'));
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const tabs = [
    { key: 'stocks', label: '📈 VN Banks' },
    { key: 'forex',  label: '💱 Forex' },
    { key: 'news',   label: '📰 News' },
  ];

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <DollarSign size={15} className="text-emerald-400" />
          Live Market Data
        </h3>
        <button
          onClick={load}
          disabled={loading}
          className="text-gray-400 hover:text-white transition p-1 rounded-lg hover:bg-white/10"
          title="Refresh"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-3">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 text-xs py-1.5 rounded-lg font-medium transition ${
              tab === t.key
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="text-center py-4 text-gray-500 text-xs animate-pulse">Đang tải dữ liệu thị trường...</div>
      )}

      {/* Stocks Tab */}
      {!loading && tab === 'stocks' && (
        <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
          {stocks.length === 0 ? (
            <p className="text-gray-500 text-xs text-center py-3">Không tải được dữ liệu cổ phiếu</p>
          ) : stocks.map(s => (
            <div key={s.ticker}
              className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2 hover:bg-white/10 transition">
              <div>
                <span className="text-white font-bold text-xs">{s.ticker}</span>
                <span className="text-gray-400 text-xs ml-2">{s.name}</span>
              </div>
              <div className="text-right">
                <div className="text-white text-xs font-semibold">{s.price?.toLocaleString()}k</div>
                <ChangeTag change={s.change} />
              </div>
            </div>
          ))}
          <p className="text-gray-600 text-xs text-center pt-1">via Yahoo Finance (yfinance)</p>
        </div>
      )}

      {/* Forex Tab */}
      {!loading && tab === 'forex' && forex && (
        <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
          {[
            { pair: 'USD/VND', rate: forex.VND?.toLocaleString(), note: '1 USD' },
            { pair: 'USD/EUR', rate: forex.EUR, note: '1 USD' },
            { pair: 'USD/JPY', rate: forex.JPY, note: '1 USD' },
            { pair: 'USD/GBP', rate: forex.GBP, note: '1 USD' },
            { pair: 'USD/CNY', rate: forex.CNY, note: '1 USD' },
            { pair: 'USD/SGD', rate: forex.SGD, note: '1 USD' },
            { pair: 'USD/KRW', rate: forex.KRW?.toLocaleString(), note: '1 USD' },
            { pair: 'USD/AUD', rate: forex.AUD, note: '1 USD' },
          ].map(r => (
            <div key={r.pair}
              className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2">
              <span className="text-gray-300 text-xs font-semibold">{r.pair}</span>
              <span className="text-emerald-300 text-xs font-bold">{r.rate}</span>
            </div>
          ))}
          <p className="text-gray-600 text-xs text-center pt-1">
            {forex.updated} · frankfurter.app + open.er-api.com
          </p>
        </div>
      )}

      {/* News Tab */}
      {!loading && tab === 'news' && (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {news.length === 0 ? (
            <p className="text-gray-500 text-xs text-center py-3">Không tải được tin tức</p>
          ) : news.map((n, i) => (
            <a key={i} href={n.link} target="_blank" rel="noreferrer"
              className="block bg-white/5 rounded-lg px-3 py-2 hover:bg-white/10 transition">
              <div className="flex items-start gap-2">
                <SentimentDot sentiment={n.sentiment} />
                <div className="flex-1 min-w-0">
                  <p className="text-white text-xs leading-tight line-clamp-2">{n.title}</p>
                  <p className="text-gray-500 text-xs mt-0.5">{n.source}</p>
                </div>
              </div>
            </a>
          ))}
          <p className="text-gray-600 text-xs text-center pt-1">VnExpress · CafeF RSS</p>
        </div>
      )}

      {lastUpdate && (
        <p className="text-gray-600 text-xs text-center mt-2">Cập nhật: {lastUpdate}</p>
      )}
    </div>
  );
}
