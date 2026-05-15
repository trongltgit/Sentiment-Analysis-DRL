// URLInput.jsx v2.0
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Loader2, Landmark, ShoppingCart, Globe, Facebook } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const EXAMPLES = [
  { url: 'https://www.facebook.com/VietinBank/',    label: 'VietinBank FB' },
  { url: 'https://www.vietcombank.com.vn',          label: 'Vietcombank' },
  { url: 'https://www.techcombank.com.vn',          label: 'Techcombank' },
  { url: 'https://www.facebook.com/MBBankofficial', label: 'MB Bank FB' },
  { url: 'https://shopee.vn',                       label: 'Shopee' },
];

function detectPlatform(url) {
  const u = url.toLowerCase();
  if (['vietcombank','techcombank','mbbank','bidv','acb','vietinbank','vpbank','hdbank'].some(b => u.includes(b)))
    return { name: 'Ngân hàng', Icon: Landmark, color: 'bg-emerald-600 text-white' };
  if (['shopee.vn','lazada.vn','tiki.vn'].some(s => u.includes(s)))
    return { name: 'E-Commerce', Icon: ShoppingCart, color: 'bg-orange-500 text-white' };
  if (u.includes('facebook.com'))
    return { name: 'Facebook', Icon: Facebook, color: 'bg-blue-600 text-white' };
  return { name: 'Website', Icon: Globe, color: 'bg-slate-600 text-white' };
}

export default function URLInput({ onAnalysisStart }) {
  const [url,     setUrl]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post('/api/v1/analyze', { url: url.trim(), max_comments: 100 });
      if (!data?.id) throw new Error('Không nhận được job ID từ server');
      onAnalysisStart?.(data);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Lỗi phân tích';
      setError(msg);
      toast.error(msg, { duration: 5000 });
    } finally {
      setLoading(false);
    }
  };

  const platform = url.trim() ? detectPlatform(url) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      {/* Hero */}
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-3">
          🏦 Phân tích Sentiment{' '}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
            Tài chính AI
          </span>
        </h1>
        <p className="text-gray-400 text-sm max-w-lg mx-auto">
          Dùng <strong className="text-emerald-400">Groq LLaMA 3.3 70B</strong> để phân tích cảm xúc
          khách hàng ngân hàng, fintech, bảo hiểm — cấp độ chuyên nghiệp quốc tế
        </p>
      </div>

      {/* Input card */}
      <div className="bg-white/8 backdrop-blur-md rounded-2xl p-6 border border-white/15 shadow-2xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setError(''); }}
              placeholder="https://www.vietcombank.com.vn  hoặc  facebook.com/VietinBank/"
              className="w-full pl-4 pr-36 py-4 bg-black/25 border border-white/15 rounded-xl text-white text-sm placeholder-gray-500 outline-none focus:ring-2 focus:ring-emerald-500 transition"
            />
            {platform && (
              <div className={`absolute right-3 top-1/2 -translate-y-1/2 px-3 py-1.5 rounded-full ${platform.color} text-xs flex items-center gap-1.5 font-medium`}>
                <platform.Icon size={12} />
                {platform.name}
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm">
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="w-full py-4 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex justify-center items-center gap-2 shadow-lg"
          >
            {loading
              ? <><Loader2 className="animate-spin" size={18} /> Đang phân tích với Groq AI...</>
              : <><Search size={18} /> Phân tích Sentiment AI</>
            }
          </button>
        </form>

        {/* Features row */}
        <div className="mt-5 grid grid-cols-3 gap-3 text-center">
          {[
            { icon: '🤖', label: 'Groq LLaMA 70B', sub: 'Deep Learning' },
            { icon: '🇻🇳', label: 'Tiếng Việt', sub: 'Vietnamese AI' },
            { icon: '⚡', label: '< 30 giây', sub: 'Siêu nhanh' },
          ].map(f => (
            <div key={f.label} className="bg-white/5 rounded-xl p-2.5">
              <div className="text-xl mb-1">{f.icon}</div>
              <div className="text-white text-xs font-semibold">{f.label}</div>
              <div className="text-gray-500 text-xs">{f.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick examples */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {EXAMPLES.map(ex => (
          <button
            key={ex.url}
            onClick={() => setUrl(ex.url)}
            className="text-xs text-gray-400 hover:text-emerald-400 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 px-3 py-1.5 rounded-full transition"
          >
            {ex.label}
          </button>
        ))}
      </div>
    </motion.div>
  );
}
