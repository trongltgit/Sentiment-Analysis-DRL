// File: frontend/src/components/AnalysisDashboard.jsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  BrainCircuit,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Minus,
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AnalysisDashboard = () => {
  const { id }        = useParams();
  const navigate      = useNavigate();
  const [analysis,  setAnalysis]  = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [polling,   setPolling]   = useState(true);
  const [error,     setError]     = useState(null);
  const [debugInfo, setDebugInfo] = useState('');

  // Tự động dùng relative URL — nginx sẽ proxy /api/ → backend
  const apiBase = '/api/v1';

  useEffect(() => {
    let interval;
    let retryCount = 0;
    const maxRetries = 5;

    const fetchAnalysis = async () => {
      const url = `${apiBase}/analysis/${id}`;
      setDebugInfo(`Đang gọi: ${url}`);

      try {
        const response = await axios.get(url, { timeout: 15000 });
        console.log('📊 Data:', response.data);
        setAnalysis(response.data);
        setError(null);
        retryCount = 0;

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('❌ Lỗi fetch:', err);
        retryCount++;

        let errorMsg = 'Không thể tải dữ liệu phân tích';
        if (err.response?.status === 404) {
          errorMsg = `Không tìm thấy phân tích ID: ${id}`;
        } else if (err.code === 'ECONNABORTED') {
          errorMsg = 'Kết nối quá chậm, thử lại...';
        } else if (err.message) {
          errorMsg = err.message;
        }

        setDebugInfo(`Lỗi: ${errorMsg} (retry ${retryCount}/${maxRetries})`);

        if (retryCount >= maxRetries) {
          setError(errorMsg);
          setPolling(false);
          clearInterval(interval);
          toast.error(errorMsg, { duration: 5000 });
        }
      } finally {
        setLoading(false);
      }
    };

    // Gọi ngay lập tức lần đầu
    fetchAnalysis();

    // Polling mỗi 3 giây
    interval = setInterval(() => {
      if (polling) fetchAnalysis();
    }, 3000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // ---------------------------------------------------------------
  // Trạng thái loading
  // ---------------------------------------------------------------
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <BrainCircuit className="animate-spin h-12 w-12 text-cyan-400 mb-4" />
        <p className="text-gray-400">Đang tải dữ liệu phân tích...</p>
        <p className="text-xs text-gray-500 mt-2">{debugInfo}</p>
      </div>
    );
  }

  // ---------------------------------------------------------------
  // Trạng thái lỗi
  // ---------------------------------------------------------------
  if (error) {
    return (
      <div className="text-center py-20">
        <AlertCircle size={64} className="mx-auto text-red-500 mb-6" />
        <h2 className="text-2xl font-semibold mb-2 text-red-400">Đã xảy ra lỗi</h2>
        <p className="text-gray-400 mb-4">{error}</p>

        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6 max-w-lg mx-auto text-left">
          <p className="text-xs text-red-300 font-mono break-all">
            ID: {id}<br />
            {debugInfo}
          </p>
        </div>

        <div className="flex gap-4 justify-center">
          <button
            onClick={() => {
              setLoading(true);
              setError(null);
              setPolling(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg"
          >
            <RefreshCw size={18} />
            Thử lại
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg"
          >
            Về trang chủ
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400">Không có dữ liệu</p>
        <p className="text-xs text-gray-500 mt-2">{debugInfo}</p>
      </div>
    );
  }

  // ---------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------
  const getStatusColor = (status) =>
    ({ pending: 'text-yellow-400', processing: 'text-blue-400', completed: 'text-green-400', failed: 'text-red-400' }[status] || 'text-gray-400');

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':    return <Clock className="animate-pulse" />;
      case 'processing': return <BrainCircuit className="animate-spin" />;
      case 'completed':  return <CheckCircle />;
      default:           return <AlertCircle />;
    }
  };

  // ✅ Đọc đúng field từ backend (positive_pct / negative_pct / neutral_pct)
  const summary = analysis.summary || {};
  const positivePct = summary.positive_pct ?? 0;
  const negativePct = summary.negative_pct ?? 0;
  const neutralPct  = summary.neutral_pct  ?? 0;
  const totalComments = summary.total_comments ?? 0;

  // Comments từ 3 nhóm
  const comments = analysis.comments || {};
  const goodList    = comments.good    || [];
  const badList     = comments.bad     || [];
  const neutralList = comments.neutral || [];

  // ---------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------
  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 border border-white/10 rounded-2xl p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0 mr-4">
            <h1 className="text-2xl font-bold mb-2">Kết quả phân tích</h1>
            <p className="text-gray-400 text-sm truncate">{analysis.url}</p>
          </div>
          <div className={`flex items-center gap-2 ${getStatusColor(analysis.status)}`}>
            {getStatusIcon(analysis.status)}
            <span className="font-semibold capitalize">{analysis.status}</span>
          </div>
        </div>

        {analysis.processing_time != null && (
          <div className="mt-4 text-sm text-gray-400">
            ⏱️ {analysis.processing_time.toFixed(2)}s &nbsp;|&nbsp;
            📝 {totalComments} bình luận
          </div>
        )}

        {/* Trạng thái đang xử lý */}
        {(analysis.status === 'pending' || analysis.status === 'processing') && (
          <div className="mt-4 flex items-center gap-2 text-blue-400 text-sm">
            <BrainCircuit size={16} className="animate-spin" />
            Đang phân tích, tự động cập nhật sau vài giây...
          </div>
        )}
      </motion.div>

      {/* Kết quả */}
      {analysis.status === 'completed' && (
        <>
          {/* Tổng quan 3 nhóm */}
          <div className="grid grid-cols-3 gap-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 text-center"
            >
              <ThumbsUp className="mx-auto text-green-400 mb-2" size={28} />
              <div className="text-3xl font-bold text-green-400">{positivePct}%</div>
              <div className="text-gray-400 text-sm mt-1">Tích cực</div>
              <div className="text-green-500 text-xs mt-1">{goodList.length} bình luận</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center"
            >
              <ThumbsDown className="mx-auto text-red-400 mb-2" size={28} />
              <div className="text-3xl font-bold text-red-400">{negativePct}%</div>
              <div className="text-gray-400 text-sm mt-1">Tiêu cực</div>
              <div className="text-red-500 text-xs mt-1">{badList.length} bình luận</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-gray-500/10 border border-gray-500/20 rounded-xl p-4 text-center"
            >
              <Minus className="mx-auto text-gray-400 mb-2" size={28} />
              <div className="text-3xl font-bold text-gray-400">{neutralPct}%</div>
              <div className="text-gray-400 text-sm mt-1">Trung lập</div>
              <div className="text-gray-500 text-xs mt-1">{neutralList.length} bình luận</div>
            </motion.div>
          </div>

          {/* Danh sách mẫu */}
          {[
            { list: goodList,    label: '👍 Tích cực', colorClass: 'border-green-500/30 bg-green-500/5' },
            { list: badList,     label: '⚠️ Tiêu cực', colorClass: 'border-red-500/30 bg-red-500/5'   },
            { list: neutralList, label: '➖ Trung lập', colorClass: 'border-gray-500/30 bg-gray-500/5' },
          ].map(({ list, label, colorClass }) =>
            list.length > 0 && (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`border rounded-2xl p-5 ${colorClass}`}
              >
                <h3 className="font-semibold text-lg mb-3">
                  {label} ({list.length})
                </h3>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {list.slice(0, 20).map((c, i) => (
                    <div key={c.id || i} className="text-sm text-gray-300 bg-black/20 rounded-lg p-3">
                      {c.text}
                      {c.confidence != null && (
                        <span className="ml-2 text-xs text-gray-500">
                          ({Math.round(c.confidence * 100)}%)
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            )
          )}
        </>
      )}

      {/* Lỗi phân tích */}
      {analysis.status === 'failed' && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
          <AlertCircle size={40} className="mx-auto text-red-400 mb-3" />
          <p className="text-red-300">{analysis.error || 'Phân tích thất bại'}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-sm"
          >
            Thử URL khác
          </button>
        </div>
      )}
    </div>
  );
};

export default AnalysisDashboard;
