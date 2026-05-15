// MultiURLInput.jsx — Multi-bank URL Input with Comparison
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, Landmark, X, Plus, Zap } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const BANK_EXAMPLES = [
  { url: 'https://www.facebook.com/VietinBank/',    label: 'VietinBank FB',      bank: 'VietinBank' },
  { url: 'https://www.vietcombank.com.vn',          label: 'Vietcombank',        bank: 'Vietcombank' },
  { url: 'https://www.techcombank.com.vn',          label: 'Techcombank',        bank: 'Techcombank' },
  { url: 'https://www.facebook.com/MBBankofficial', label: 'MB Bank FB',         bank: 'MB Bank' },
  { url: 'https://www.vpbank.com.vn',               label: 'VPBank',             bank: 'VPBank' },
  { url: 'https://www.hdbank.com.vn',               label: 'HDBank',             bank: 'HDBank' },
];

function detectBank(url) {
  const u = url.toLowerCase();
  const bankMap = {
    'vietcombank': 'Vietcombank',
    'techcombank': 'Techcombank',
    'mbbank': 'MB Bank',
    'vpbank': 'VPBank',
    'hdbank': 'HDBank',
    'bidv': 'BIDV',
    'acb': 'ACB',
    'vietinbank': 'VietinBank',
  };
  
  for (const [key, name] of Object.entries(bankMap)) {
    if (u.includes(key)) return name;
  }
  return 'Unknown';
}

export default function MultiURLInput({ onAnalysisStart }) {
  const [urls, setUrls] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const addURL = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) {
      toast.error('Vui lòng nhập URL');
      return;
    }
    
    if (urls.some(u => u.url === trimmed)) {
      toast.error('URL này đã được thêm');
      return;
    }

    const bank = detectBank(trimmed);
    setUrls([...urls, { url: trimmed, bank, id: Date.now() }]);
    setInputValue('');
    setErrors({});
  };

  const removeURL = (id) => {
    setUrls(urls.filter(u => u.id !== id));
  };

  const addExample = (example) => {
    if (urls.some(u => u.url === example.url)) {
      toast.error('URL này đã được thêm');
      return;
    }
    setUrls([...urls, { url: example.url, bank: example.bank, id: Date.now() }]);
  };

  const handleAnalyze = async () => {
    if (urls.length === 0) {
      toast.error('Vui lòng thêm ít nhất một URL');
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const results = [];
      for (const urlItem of urls) {
        try {
          const { data } = await axios.post('/api/v1/analyze', {
            url: urlItem.url,
            max_comments: 100,
            bank_name: urlItem.bank,
          }, { timeout: 30000 });
          
          if (!data?.id) throw new Error('Không nhận được job ID');
          results.push({ ...data, bank: urlItem.bank, urlId: urlItem.id });
        } catch (err) {
          setErrors(prev => ({
            ...prev,
            [urlItem.id]: err.response?.data?.detail || err.message
          }));
        }
      }

      if (results.length > 0) {
        onAnalysisStart?.(results);
      } else {
        toast.error('Phân tích thất bại. Vui lòng kiểm tra URL');
      }
    } finally {
      setLoading(false);
    }
  };

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
          🏦 So sánh Sentiment Ngân hàng{' '}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
            Với AI
          </span>
        </h1>
        <p className="text-gray-400 text-sm max-w-lg mx-auto">
          Phân tích và so sánh cảm xúc khách hàng từ nhiều ngân hàng cùng lúc với{' '}
          <strong className="text-emerald-400">Groq LLaMA 3.3 70B</strong>
        </p>
      </div>

      {/* URL Input Card */}
      <div className="bg-white/8 backdrop-blur-md rounded-2xl p-6 border border-white/15 shadow-2xl mb-6">
        <div className="space-y-4">
          {/* Input row */}
          <div className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addURL()}
              placeholder="https://www.vietcombank.com.vn hoặc facebook.com/VietinBank/"
              className="flex-1 pl-4 pr-4 py-3 bg-black/25 border border-white/15 rounded-xl text-white text-sm placeholder-gray-500 outline-none focus:ring-2 focus:ring-emerald-500 transition"
            />
            <button
              onClick={addURL}
              disabled={loading}
              className="px-4 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center gap-2 transition disabled:opacity-50"
            >
              <Plus size={18} /> Thêm
            </button>
          </div>

          {/* URL List */}
          {urls.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-gray-400 font-semibold">Ngân hàng đã thêm ({urls.length})</p>
              <div className="space-y-2">
                {urls.map(urlItem => (
                  <motion.div
                    key={urlItem.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center justify-between bg-black/40 border border-white/10 rounded-lg p-3"
                  >
                    <div className="flex-1 flex items-center gap-3">
                      <Landmark size={16} className="text-emerald-400 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-white truncate">{urlItem.bank}</p>
                        <p className="text-xs text-gray-500 truncate">{urlItem.url}</p>
                      </div>
                    </div>
                    {errors[urlItem.id] && (
                      <div className="text-xs text-red-400 mr-2">⚠️ Lỗi</div>
                    )}
                    <button
                      onClick={() => removeURL(urlItem.id)}
                      className="p-1 hover:bg-red-500/20 rounded transition"
                    >
                      <X size={16} className="text-red-400" />
                    </button>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Analyze Button */}
          <button
            onClick={handleAnalyze}
            disabled={loading || urls.length === 0}
            className="w-full py-4 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex justify-center items-center gap-2 shadow-lg"
          >
            {loading
              ? <><Loader2 className="animate-spin" size={18} /> Đang phân tích {urls.length} ngân hàng...</>
              : <><Zap size={18} /> Phân tích so sánh ngay</>
            }
          </button>
        </div>

        {/* Features */}
        <div className="mt-5 grid grid-cols-3 gap-3 text-center">
          {[
            { icon: '🤖', label: 'Groq LLaMA 70B', sub: 'Deep Learning' },
            { icon: '📊', label: 'So sánh', sub: 'Multi-bank' },
            { icon: '⚡', label: '< 60 giây', sub: 'Siêu nhanh' },
          ].map(f => (
            <div key={f.label} className="bg-white/5 rounded-xl p-2.5">
              <div className="text-xl mb-1">{f.icon}</div>
              <div className="text-white text-xs font-semibold">{f.label}</div>
              <div className="text-gray-500 text-xs">{f.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Examples */}
      <div>
        <p className="text-xs text-gray-400 font-semibold mb-3">Các ngân hàng phổ biến</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {BANK_EXAMPLES.map(ex => (
            <button
              key={ex.url}
              onClick={() => addExample(ex)}
              disabled={loading}
              className="text-xs bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 px-3 py-2 rounded-lg transition text-gray-400 hover:text-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
