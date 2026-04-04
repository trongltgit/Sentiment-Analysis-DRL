import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  BrainCircuit,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AnalysisDashboard = () => {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(true);
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState('');

  const apiBase = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api/v1`
    : '/api/v1';

  useEffect(() => {
    let interval;
    let retryCount = 0;
    const maxRetries = 3;

    const fetchAnalysis = async () => {
      const url = `${apiBase}/analysis/${id}`;
      setDebugInfo(`Đang gọi: ${url}`);
      
      try {
        const response = await axios.get(url, {
          timeout: 15000,
        });

        console.log('📊 Data:', response.data);
        setAnalysis(response.data);
        setError(null);
        retryCount = 0;

        // Dừng polling nếu xong hoặc lỗi
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
        }

      } catch (err) {
        console.error('❌ Lỗi fetch:', err);
        retryCount++;
        
        let errorMsg = 'Không thể tải dữ liệu phân tích';
        
        if (err.response?.status === 404) {
          errorMsg = `Không tìm thấy phân tích ID: ${id}`;
        } else if (err.code === 'ECONNABORTED') {
          errorMsg = 'Kết nối quá chậm';
        } else if (err.message) {
          errorMsg = err.message;
        }
        
        setDebugInfo(`Lỗi: ${errorMsg} (retry ${retryCount}/${maxRetries})`);
        
        // Dừng sau nhiều lần thử
        if (retryCount >= maxRetries) {
          setError(errorMsg);
          setPolling(false);
          toast.error(errorMsg, { duration: 5000 });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();

    if (polling) {
      interval = setInterval(fetchAnalysis, 3000);
    }

    return () => clearInterval(interval);
  }, [id, polling, apiBase]);

  // Loading
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <BrainCircuit className="animate-spin h-12 w-12 text-cyan-400 mb-4" />
        <p className="text-gray-400">Đang tải dữ liệu phân tích...</p>
        <p className="text-xs text-gray-500 mt-2">{debugInfo}</p>
      </div>
    );
  }

  // Error
  if (error) {
    return (
      <div className="text-center py-20">
        <AlertCircle size={64} className="mx-auto text-red-500 mb-6" />
        <h2 className="text-2xl font-semibold mb-2 text-red-400">Đã xảy ra lỗi</h2>
        <p className="text-gray-400 mb-4">{error}</p>
        
        {/* Debug info */}
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6 max-w-lg mx-auto text-left">
          <p className="text-xs text-red-300 font-mono break-all">
            ID: {id}<br/>
            API: {apiBase}<br/>
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
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg"
          >
            Về trang chủ
          </button>
        </div>
      </div>
    );
  }

  // No data
  if (!analysis) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400">Không có dữ liệu</p>
        <p className="text-xs text-gray-500 mt-2">{debugInfo}</p>
      </div>
    );
  }

  // Render result
  const getStatusColor = (status) => ({
    pending: 'text-yellow-400',
    processing: 'text-blue-400',
    completed: 'text-green-400',
    failed: 'text-red-400'
  }[status] || 'text-gray-400');

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
          <div className="mt-4 text-sm text-gray-400">
            ⏱️ {analysis.processing_time.toFixed(2)}s | 
            📝 {analysis.summary?.total_comments || 0} bình luận
          </div>
        )}
      </motion.div>

      {analysis.status === 'completed' && analysis.summary && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-green-500/10 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-green-400">{analysis.summary.positive_pct}%</div>
            <div className="text-gray-400 text-sm">Tích cực</div>
          </div>
          <div className="bg-red-500/10 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-red-400">{analysis.summary.negative_pct}%</div>
            <div className="text-gray-400 text-sm">Tiêu cực</div>
          </div>
          <div className="bg-gray-500/10 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-gray-400">{analysis.summary.neutral_pct}%</div>
            <div className="text-gray-400 text-sm">Trung lập</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisDashboard;
