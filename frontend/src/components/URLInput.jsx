import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Link2, Loader2, Settings } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const URLInput = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState({
    max_comments: 100,
    analysis_depth: 'standard'
  });
  const [showOptions, setShowOptions] = useState(false);
  const navigate = useNavigate();

  // 🔴 SỬA: Dùng relative URL (cùng domain)
  const apiBase = '/api/v1';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!url.includes('facebook.com')) {
      const msg = 'Vui lòng nhập URL Facebook hợp lệ';
      setError(msg);
      toast.error(msg);
      return;
    }

    setLoading(true);
    console.log('🚀 Gửi request:', `${apiBase}/analyze`);

    try {
      const response = await axios.post(`${apiBase}/analyze`, {
        url: url,
        max_comments: options.max_comments,
        analysis_depth: options.analysis_depth
      }, {
        timeout: 30000,
        headers: { 'Content-Type': 'application/json' }
      });

      console.log('✅ Response:', response.data);
      
      const analysisId = response.data.id;
      if (!analysisId) throw new Error('Không có ID');

      toast.success('Phân tích đã bắt đầu!');
      navigate(`/analysis/${analysisId}`);

    } catch (error) {
      console.error('❌ Lỗi:', error);
      
      let message = 'Có lỗi xảy ra';
      if (error.code === 'ERR_NETWORK') message = 'Không thể kết nối server';
      else if (error.response?.status === 404) message = 'API không tồn tại';
      else if (error.response?.status === 500) message = 'Lỗi server';
      else if (error.message) message = error.message;
      
      setError(message);
      toast.error(message, { duration: 5000 });
      
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
        <p className="text-gray-400">Nhập URL fanpage Facebook</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200">
          <p className="font-semibold">❌ Lỗi: {error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Link2 className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://facebook.com/..."
            className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:border-cyan-400 text-white"
            required
          />
        </div>

        <button
          type="button"
          onClick={() => setShowOptions(!showOptions)}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
        >
          <Settings size={16} />
          Tùy chọn
        </button>

        {showOptions && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Số bình luận: {options.max_comments}
              </label>
              <input
                type="range"
                min="10"
                max="1000"
                value={options.max_comments}
                onChange={(e) => setOptions({...options, max_comments: parseInt(e.target.value)})}
                className="w-full accent-cyan-400"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Độ sâu</label>
              <select
                value={options.analysis_depth}
                onChange={(e) => setOptions({...options, analysis_depth: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-white"
              >
                <option value="basic">Cơ bản</option>
                <option value="standard">Tiêu chuẩn</option>
                <option value="deep">Sâu</option>
              </select>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-semibold text-white disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" />
              Đang xử lý...
            </>
          ) : (
            'Bắt đầu phân tích AI'
          )}
        </button>
      </form>
    </motion.div>
  );
};

export default URLInput;
