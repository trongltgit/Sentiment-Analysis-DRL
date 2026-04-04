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

const AnalysisDashboard = () => {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(true);
  const [error, setError] = useState(null);

  // 🔴 SỬA: Dùng VITE_API_URL từ env
  const apiBase = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api/v1`
    : '/api/v1';

  useEffect(() => {
    let interval;

    const fetchAnalysis = async () => {
      try {
        console.log("Fetching from:", `${apiBase}/analysis/${id}`);
        
        const response = await axios.get(`${apiBase}/analysis/${id}`, {
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json',
          }
        });

        console.log("Response:", response.data);
        setAnalysis(response.data);
        setError(null);

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
        }
      } catch (err) {
        console.error("API Error:", err);
        
        let errorMsg = "Không thể kết nối đến server phân tích.";
        
        if (err.code === 'ECONNABORTED') {
          errorMsg = "Kết nối quá chậm, vui lòng thử lại.";
        } else if (err.response?.status === 404) {
          errorMsg = "Không tìm thấy dữ liệu phân tích.";
        } else if (err.response?.status >= 500) {
          errorMsg = "Lỗi server, vui lòng thử lại sau.";
        }
        
        setError(errorMsg);
        toast.error(errorMsg);
        setPolling(false);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();

    if (polling) {
      interval = setInterval(fetchAnalysis, 4000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, polling, apiBase]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
        <p className="ml-4 text-gray-400">Đang tải dữ liệu...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-20">
        <AlertCircle size={64} className="mx-auto text-red-500 mb-6" />
        <h2 className="text-2xl font-semibold mb-2 text-red-400">Lỗi kết nối</h2>
        <p className="text-gray-400 mb-6 max-w-md mx-auto">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white"
        >
          Thử lại
        </button>
        <p className="text-sm text-gray-500 mt-4">
          API URL: {apiBase}
        </p>
      </div>
    );
  }

  // No data
  if (!analysis) {
    return <div className="text-center py-20 text-gray-400">Không tìm thấy dữ liệu</div>;
  }

  // Render analysis data
  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-yellow-400',
      processing: 'text-blue-400',
      completed: 'text-green-400',
      failed: 'text-red-400'
    };
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
      <motion.div 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }} 
        className="bg-white/5 border border-white/10 rounded-2xl p-6"
      >
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
        <motion.div 
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
            <div className="text-3xl font-bold text-green-400">
              {analysis.summary.positive_pct}%
            </div>
            <div className="text-gray-400 text-sm">Tích cực</div>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
            <div className="text-3xl font-bold text-red-400">
              {analysis.summary.negative_pct}%
            </div>
            <div className="text-gray-400 text-sm">Tiêu cực</div>
          </div>
          <div className="bg-gray-500/10 border border-gray-500/20 rounded-xl p-4">
            <div className="text-3xl font-bold text-gray-400">
              {analysis.summary.neutral_pct}%
            </div>
            <div className="text-gray-400 text-sm">Trung lập</div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AnalysisDashboard;
