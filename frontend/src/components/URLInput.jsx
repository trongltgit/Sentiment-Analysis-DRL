import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Globe, Loader2 } from 'lucide-react';
import axios from 'axios';

const URLInput = ({ onAnalysisStart }) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ✅ SỬA: Chấp nhận mọi URL hợp lệ, không chỉ Facebook
  const isValidUrl = (string) => {
    try {
      const urlObj = new URL(string);
      // Chấp nhận http hoặc https
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch (_) {
      return false;
    }
  };

  // ✅ THÊM: Detect platform từ URL để hiển thị
  const detectPlatform = (url) => {
    if (url.includes('facebook.com') || url.includes('fb.com')) {
      return { name: 'Facebook', icon: '📘', color: 'bg-blue-600' };
    } else if (url.includes('shopee.vn')) {
      return { name: 'Shopee', icon: '🛒', color: 'bg-orange-500' };
    } else if (url.includes('lazada.vn')) {
      return { name: 'Lazada', icon: '🛍️', color: 'bg-blue-500' };
    } else if (url.includes('tiki.vn')) {
      return { name: 'Tiki', icon: '📚', color: 'bg-blue-400' };
    } else if (url.includes('youtube.com') || url.includes('youtu.be')) {
      return { name: 'YouTube', icon: '📺', color: 'bg-red-600' };
    } else if (url.includes('tiktok.com')) {
      return { name: 'TikTok', icon: '🎵', color: 'bg-black' };
    } else if (url.includes('google.com/maps')) {
      return { name: 'Google Maps', icon: '🗺️', color: 'bg-green-500' };
    } else if (url.includes('vietcombank') || url.includes('techcombank') || 
               url.includes('vietinbank') || url.includes('bidv') || 
               url.includes('acb') || url.includes('mbbank')) {
      return { name: 'Ngân hàng VN', icon: '🏦', color: 'bg-blue-700' };
    } else {
      return { name: 'Website', icon: '🌐', color: 'bg-gray-600' };
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!isValidUrl(url)) {
      setError('❌ Vui lòng nhập URL hợp lệ (ví dụ: https://example.com)');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/v1/analyze', {
        url: url,
        max_comments: 100
      });
      
      onAnalysisStart(response.data);
    } catch (err) {
      setError('❌ Không thể phân tích URL này. Vui lòng thử lại.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const platform = url ? detectPlatform(url) : null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto"
    >
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 shadow-2xl">
        <h2 className="text-2xl font-bold text-white mb-6 text-center">
          🔍 Phân tích cảm xúc từ bất kỳ URL nào
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Globe className="h-5 w-5 text-gray-400" />
            </div>
            
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Nhập URL: Facebook, Shopee, Website ngân hàng..."
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            
            {/* ✅ Hiển thị platform detected */}
            {platform && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`absolute right-3 top-1/2 transform -translate-y-1/2 px-3 py-1 rounded-full ${platform.color} text-white text-sm font-medium flex items-center gap-2`}
              >
                <span>{platform.icon}</span>
                <span>{platform.name}</span>
              </motion.div>
            )}
          </div>

          {error && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-red-400 text-sm text-center"
            >
              {error}
            </motion.div>
          )}

          <div className="text-gray-400 text-xs text-center space-y-1">
            <p>💡 Hỗ trợ: Facebook, Shopee, Lazada, Website ngân hàng, Google Maps...</p>
            <p>Ví dụ: https://shopee.vn/shop/123, https://www.facebook.com/page/</p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            disabled={loading || !url}
            className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${
              loading || !url
                ? 'bg-gray-600 cursor-not-allowed text-gray-300'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Đang phân tích...
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                🚀 Bắt đầu phân tích AI
              </>
            )}
          </motion.button>
        </form>
      </div>
    </motion.div>
  );
};

export default URLInput;
