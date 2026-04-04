import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Link2, Loader2, Settings } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const URLInput = ({ onAnalysisStart }) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null); // 🔴 THÊM: State lưu lỗi
  const [options, setOptions] = useState({
    max_comments: 100,
    analysis_depth: 'standard'
  });
  const [showOptions, setShowOptions] = useState(false);
  const navigate = useNavigate();

  const apiBase = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api/v1`
    : 'http://localhost:8000/api/v1';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); // Clear previous error
    
    if (!url.includes('facebook.com')) {
      const msg = 'Vui lòng nhập URL Facebook hợp lệ';
      setError(msg);
      toast.error(msg, { duration: 5000 });
      return;
    }

    setLoading(true);
    console.log('🚀 Đang gửi request...');
    console.log('📍 API URL:', `${apiBase}/analyze`);
    console.log('📦 Payload:', { url, max_comments: options.max_comments, analysis_depth: options.analysis_depth });

    try {
      const response = await axios.post(`${apiBase}/analyze`, {
        url: url,
        max_comments: options.max_comments,
        analysis_depth: options.analysis_depth
      }, {
        timeout: 30000,
        headers: { 'Content-Type': 'application/json' }
      });

      console.log('✅ Thành công:', response.data);
      
      const analysisId = response.data.id || response.data.analysis_id;
      
      if (!analysisId) {
        throw new Error('Server không trả về analysis_id');
      }

      onAnalysisStart?.(response.data);
      toast.success('Phân tích đã bắt đầu!', { duration: 3000 });
      navigate(`/analysis/${analysisId}`);
      
    } catch (error) {
      console.error('❌ Chi tiết lỗi:', error);
      console.error('❌ Response:', error.response);
      console.error('❌ Request config:', error.config);
      
      let message = 'Có lỗi xảy ra khi phân tích';
      let details = '';
      
      if (error.code === 'ERR_NETWORK') {
        message = 'Không thể kết nối đến server';
        details = 'Kiểm tra xem backend đã chạy chưa hoặc CORS đã bật chưa';
      } else if (error.code === 'ECONNABORTED') {
        message = 'Kết nối quá chậm (timeout)';
      } else if (error.response?.status === 404) {
        message = 'API endpoint không tồn tại (404)';
        details = `URL: ${error.config?.url}`;
      } else if (error.response?.status === 500) {
        message = 'Lỗi server nội bộ (500)';
        details = error.response?.data?.detail || '';
      } else if (error.response?.status === 400) {
        message = 'Dữ liệu không hợp lệ (400)';
        details = error.response?.data?.detail || '';
      } else if (error.message) {
        message = error.message;
      }
      
      // 🔴 HIỂN THỊ LỖI TRÊN UI (không biến mất)
      setError(`${message}${details ? `: ${details}` : ''}`);
      
      // Toast lâu hơn
      toast.error(message, { duration: 10000 });
      
      // 🔴 ALERT để chắc chắn thấy lỗi
      alert(`❌ LỖI PHÂN TÍCH\n\n${message}\n${details ? '\nChi tiết: ' + details : ''}\n\nAPI: ${apiBase}\nStatus: ${error.response?.status || 'Network Error'}`);
      
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto mt-20"
    >
      <div className="text-center mb-8">
        <h2 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-400">
          Phân tích cảm xúc bằng Deep RL
        </h2>
        <p className="text-gray-400">
          Nhập URL fanpage Facebook để AI phân tích bình luận
        </p>
      </div>

      {/* 🔴 HIỂN THỊ LỖI RÕ RÀNG TRÊN UI */}
      {error && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200"
        >
          <div className="flex items-start gap-3">
            <span className="text-2xl">❌</span>
            <div className="flex-1">
              <p className="font-semibold mb-1">Đã xảy ra lỗi:</p>
              <p className="text-sm break-all">{error}</p>
              <p className="text-xs text-red-300 mt-2">API: {apiBase}</p>
            </div>
            <button 
              onClick={() => setError(null)}
              className="text-red-300 hover:text-white"
            >
              ✕
            </button>
          </div>
        </motion.div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Link2 className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://facebook.com/..."
            className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:border-cyan-400 transition-colors text-white placeholder-gray-500"
            required
          />
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          type="button"
          onClick={() => setShowOptions(!showOptions)}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <Settings size={16} />
          Tùy chọn phân tích
        </motion.button>

        {showOptions && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-4"
          >
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Số lượng bình luận: {options.max_comments}
              </label>
              <input
                type="range"
                min="10"
                max="1000"
                step="10"
                value={options.max_comments}
                onChange={(e) => setOptions({...options, max_comments: parseInt(e.target.value)})}
                className="w-full accent-cyan-400"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Độ sâu phân tích
              </label>
              <select
                value={options.analysis_depth}
                onChange={(e) => setOptions({...options, analysis_depth: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-white"
              >
                <option value="basic">Cơ bản - Nhanh</option>
                <option value="standard">Tiêu chuẩn - Cân bằng</option>
                <option value="deep">Sâu - Chi tiết nhất</option>
              </select>
            </div>
          </motion.div>
        )}

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          type="submit"
          disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-semibold text-white shadow-lg shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" />
              Đang khởi tạo...
            </>
          ) : (
            'Bắt đầu phân tích AI'
          )}
        </motion.button>
      </form>

      {/* Debug info */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-600 font-mono">API: {apiBase}</p>
      </div>

      <div className="mt-12 grid grid-cols-3 gap-4 text-center">
        {[
          { icon: '🧠', label: 'Deep RL', desc: 'Tự động học' },
          { icon: '📊', label: 'Multi-Aspect', desc: 'Phân tích đa chiều' },
          { icon: '⚡', label: 'Real-time', desc: 'Xử lý nhanh' }
        ].map((feature, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="p-4 bg-white/5 border border-white/10 rounded-xl"
          >
            <div className="text-3xl mb-2">{feature.icon}</div>
            <div className="font-semibold text-cyan-400">{feature.label}</div>
            <div className="text-sm text-gray-400">{feature.desc}</div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default URLInput;
