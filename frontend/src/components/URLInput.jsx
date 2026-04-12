import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Globe, Loader2, Landmark } from 'lucide-react'; // Thêm icon Landmark
import axios from 'axios';

const URLInput = ({ onAnalysisStart }) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const detectPlatform = (url) => {
    const u = url.toLowerCase();
    // Ưu tiên hiển thị badge Ngân hàng
    if (u.includes('vietcombank') || u.includes('techcombank') || u.includes('mbbank') || u.includes('bidv')) {
      return { name: 'Ngân hàng', icon: <Landmark className="h-4 w-4" />, color: 'bg-emerald-600' };
    }
    if (u.includes('shopee.vn') || u.includes('lazada.vn')) {
      return { name: 'E-Commerce', icon: '🛒', color: 'bg-orange-500' };
    }
    if (u.includes('facebook.com')) {
      return { name: 'Facebook', icon: '📘', color: 'bg-blue-600' };
    }
    return { name: 'Website', icon: '🌐', color: 'bg-gray-600' };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    try {
      const response = await axios.post('/api/v1/analyze', { url, max_comments: 100 });
      onAnalysisStart(response.data);
    } catch (err) {
      setError('❌ Không thể phân tích link này. Thử lại sau nhé!');
    } finally {
      setLoading(false);
    }
  };

  const platform = url ? detectPlatform(url) : null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="w-full max-w-2xl mx-auto">
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
        <h2 className="text-2xl font-bold text-white mb-6 text-center">
          🏛️ Phân tích Cảm xúc Ngân hàng & Công ty
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Dán link Vietcombank, Techcombank, Shopee..."
              className="w-full pl-6 pr-32 py-4 bg-black/20 border border-white/10 rounded-xl text-white outline-none focus:ring-2 focus:ring-emerald-500"
            />
            {platform && (
              <div className={`absolute right-3 top-1/2 -translate-y-1/2 px-3 py-1 rounded-full ${platform.color} text-white text-xs flex items-center gap-2`}>
                {platform.icon} {platform.name}
              </div>
            )}
          </div>

          <div className="text-gray-400 text-xs text-center">
            💡 Hệ thống tối ưu cho: Website Ngân hàng, Dịch vụ tài chính và các shop online.
          </div>

          <button
            disabled={loading || !url}
            className="w-full py-4 rounded-xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:opacity-90 transition-all flex justify-center items-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Search size={20} />}
            Bắt đầu phân tích AI
          </button>
        </form>
      </div>
    </motion.div>
  );
};

export default URLInput;
