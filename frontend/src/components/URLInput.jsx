// File: frontend/src/components/URLInput.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Loader2, Landmark } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const URLInput = ({ onAnalysisStart }) => {
  const [url,     setUrl]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const detectPlatform = (u) => {
    const lower = u.toLowerCase();
    if (['vietcombank','techcombank','mbbank','bidv','acb','vietinbank'].some(b => lower.includes(b)))
      return { name: 'Ngân hàng', icon: <Landmark className="h-4 w-4" />, color: 'bg-emerald-600' };
    if (['shopee.vn','lazada.vn','tiki.vn'].some(s => lower.includes(s)))
      return { name: 'E-Commerce', icon: '🛒', color: 'bg-orange-500' };
    if (lower.includes('facebook.com'))
      return { name: 'Facebook', icon: '📘', color: 'bg-blue-600' };
    return { name: 'Website', icon: '🌐', color: 'bg-gray-600' };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError('');

    try {
      console.log('📤 Gửi request phân tích:', url.trim());

      const response = await axios.post('/api/v1/analyze', {
        url:          url.trim(),
        max_comments: 100,
      });

      const data = response.data;
      console.log('📥 Response từ server:', data);

      const jobId = data?.id;
      if (!jobId) {
        throw new Error('Server không trả về job id: ' + JSON.stringify(data));
      }

      console.log('🎯 Job ID nhận được:', jobId);

      // Gọi callback (App.jsx sẽ navigate)
      if (typeof onAnalysisStart === 'function') {
        console.log('📞 Gọi onAnalysisStart...');
        onAnalysisStart(data);
      } else {
        // Fallback: navigate bằng window nếu callback không hoạt động
        console.warn('⚠️ onAnalysisStart không phải function, dùng window.location');
        window.location.href = `/analysis/${jobId}`;
      }

    } catch (err) {
      console.error('❌ Lỗi submit:', err);
      const msg = err.response?.data?.detail || err.message || 'Không thể phân tích link này.';
      setError(msg);
      toast.error(msg, { duration: 4000 });
    } finally {
      setLoading(false);
    }
  };

  const platform = url.trim() ? detectPlatform(url) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto mt-10"
    >
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
        <h2 className="text-2xl font-bold text-white mb-2 text-center">
          🏛️ Phân tích Cảm xúc Ngân hàng &amp; Công ty
        </h2>
        <p className="text-gray-400 text-sm text-center mb-6">
          Dán link website để AI phân tích tích cực / tiêu cực / trung lập
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setError(''); }}
              placeholder="https://www.facebook.com/VietinBank/ ..."
              className="w-full pl-6 pr-36 py-4 bg-black/20 border border-white/10 rounded-xl text-white placeholder-gray-500 outline-none focus:ring-2 focus:ring-emerald-500 transition"
            />
            {platform && (
              <div className={`absolute right-3 top-1/2 -translate-y-1/2 px-3 py-1 rounded-full ${platform.color} text-white text-xs flex items-center gap-1.5`}>
                {platform.icon}
                <span>{platform.name}</span>
              </div>
            )}
          </div>

          <p className="text-gray-500 text-xs text-center">
            💡 Tối ưu cho: Website Ngân hàng, E-commerce, Facebook Page
          </p>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="w-full py-4 rounded-xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex justify-center items-center gap-2"
          >
            {loading
              ? <><Loader2 className="animate-spin" size={20} /> Đang phân tích...</>
              : <><Search size={20} /> Bắt đầu phân tích AI</>
            }
          </button>
        </form>
      </div>

      {/* Quick examples */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {[
          'https://www.facebook.com/VietinBank/',
          'https://www.vietcombank.com.vn',
          'https://shopee.vn',
        ].map((ex) => (
          <button
            key={ex}
            onClick={() => setUrl(ex)}
            className="text-xs text-gray-400 hover:text-cyan-400 bg-white/5 hover:bg-white/10 border border-white/10 px-3 py-1.5 rounded-full transition"
          >
            {ex}
          </button>
        ))}
      </div>
    </motion.div>
  );
};

export default URLInput;
