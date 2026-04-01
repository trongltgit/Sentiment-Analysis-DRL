import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  BrainCircuit
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import SentimentChart from './SentimentChart';
import CommentList from './CommentList';

const AnalysisDashboard = () => {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;

    const fetchAnalysis = async () => {
      try {
        const apiBase = import.meta.env.VITE_API_URL 
          ? `${import.meta.env.VITE_API_URL}/api/v1`
          : '/api/v1';

        const response = await axios.get(`${apiBase}/analysis/${id}`, {
          timeout: 10000 // tránh treo quá lâu
        });

        setAnalysis(response.data);
        setError(null);

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
        }
      } catch (err) {
        console.error("API Error:", err);
        
        if (!import.meta.env.VITE_API_URL) {
          setError("Backend chưa được deploy. Vui lòng deploy backend trước.");
        } else {
          setError("Không thể kết nối đến server phân tích.");
        }

        toast.error("Lỗi kết nối backend");
        setPolling(false);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();

    if (polling) {
      interval = setInterval(fetchAnalysis, 4000); // tăng lên 4 giây để đỡ spam
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, polling]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <AlertCircle size={64} className="mx-auto text-red-500 mb-6" />
        <h2 className="text-2xl font-semibold mb-2 text-red-400">Không kết nối được Backend</h2>
        <p className="text-gray-400 mb-6 max-w-md mx-auto">{error}</p>
        <p className="text-sm text-gray-500">
          Frontend đã live, nhưng backend chưa chạy.<br />
          Vui lòng deploy backend và set biến <code>VITE_API_URL</code>.
        </p>
      </div>
    );
  }

  if (!analysis) {
    return <div className="text-center py-20 text-gray-400">Không tìm thấy dữ liệu</div>;
  }

  // Phần return còn lại giữ nguyên như code cũ của bạn (stats, chart, comment...)
  const getStatusColor = (status) => {
    const colors = { pending: 'text-yellow-400', processing: 'text-blue-400', completed: 'text-green-400', failed: 'text-red-400' };
    return colors[status] || 'text-gray-400';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="animate-pulse" />;
      case 'processing': return <BrainCircuit className="animate-spin" />;
      case 'completed': return <CheckCircle />;
      default: return <AlertCircle />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header - giữ nguyên code cũ của bạn */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/5 border border-white/10 rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Kết quả phân tích</h1>
            <p className="text-gray-400 text-sm truncate max-w-xl">{analysis.url}</p>
          </div>
          <div className={`flex items-center gap-2 ${getStatusColor(analysis.status)}`}>
            {getStatusIcon(analysis.status)}
            <span className="font-semibold capitalize">{analysis.status}</span>
          </div>
        </div>
        {analysis.processing_time && (
          <div className="mt-4 flex items-center gap-4 text-sm text-gray-400">
            <span>⏱️ Thời gian xử lý: {analysis.processing_time.toFixed(2)}s</span>
            <span>📝 Tổng bình luận: {analysis.summary?.total_comments || 0}</span>
          </div>
        )}
      </motion.div>

      {analysis.status === 'completed' && analysis.summary && (
        <>
          {/* Stats Grid, Chart, Insights, CommentList giữ nguyên như code cũ của bạn */}
          {/* ... (bạn có thể giữ phần này từ code cũ) */}
        </>
      )}
    </div>
  );
};

export default AnalysisDashboard;
