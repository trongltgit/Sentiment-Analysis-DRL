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

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        // Sử dụng biến môi trường hoặc fallback về /api (sẽ proxy qua nginx sau)
        const baseURL = import.meta.env.VITE_API_URL 
          ? `${import.meta.env.VITE_API_URL}/api/v1/analysis/${id}`
          : `/api/v1/analysis/${id}`;

        const response = await axios.get(baseURL);
        
        setAnalysis(response.data);
       
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
        }
      } catch (error) {
        console.error("Lỗi tải dữ liệu phân tích:", error);
        
        // Nếu chưa có backend, hiển thị thông báo thân thiện
        if (!import.meta.env.VITE_API_URL) {
          toast.error('Backend chưa được kết nối. Đang hiển thị chế độ demo.');
        } else {
          toast.error('Không thể tải dữ liệu phân tích');
        }
        
        setPolling(false);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
   
    // Polling chỉ chạy nếu đang ở trạng thái pending/processing
    if (polling) {
      const interval = setInterval(fetchAnalysis, 3000);
      return () => clearInterval(interval);
    }
  }, [id, polling]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center py-20">
        <AlertCircle size={48} className="mx-auto text-red-400 mb-4" />
        <p className="text-gray-400">Không tìm thấy dữ liệu phân tích</p>
      </div>
    );
  }

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
      {/* Header */}
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
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              {
                label: 'Tích cực',
                value: analysis.summary.sentiment_distribution?.positive || 0,
                color: 'from-green-500 to-emerald-600',
                icon: '😊'
              },
              {
                label: 'Trung lập',
                value: analysis.summary.sentiment_distribution?.neutral || 0,
                color: 'from-gray-500 to-slate-600',
                icon: '😐'
              },
              {
                label: 'Tiêu cực',
                value: analysis.summary.sentiment_distribution?.negative || 0,
                color: 'from-red-500 to-rose-600',
                icon: '😠'
              },
              {
                label: 'Độ tin cậy TB',
                value: `${(analysis.summary.average_confidence * 100 || 0).toFixed(1)}%`,
                color: 'from-cyan-500 to-blue-600',
                icon: '🎯'
              }
            ].map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.1 }}
                className={`bg-gradient-to-br ${stat.color} p-6 rounded-2xl`}
              >
                <div className="text-3xl mb-2">{stat.icon}</div>
                <div className="text-3xl font-bold">{stat.value}</div>
                <div className="text-white/80 text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </div>

          {/* Charts & Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SentimentChart
              distribution={analysis.summary.sentiment_distribution}
            />
           
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 border border-white/10 rounded-2xl p-6"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="text-cyan-400" />
                Phân tích xu hướng
              </h3>
             
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-400 mb-1">Chủ đề chính</div>
                  <div className="flex flex-wrap gap-2">
                    {analysis.summary.key_topics?.map((topic, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded-full text-sm"
                      >
                        #{topic}
                      </span>
                    )) || <p className="text-gray-500">Không có chủ đề chính</p>}
                  </div>
                </div>

                {analysis.summary.risk_factors?.length > 0 && (
                  <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <div className="text-red-400 font-semibold mb-2 flex items-center gap-2">
                      <AlertCircle size={16} />
                      Yếu tố rủi ro
                    </div>
                    <ul className="space-y-1 text-sm text-red-200">
                      {analysis.summary.risk_factors.map((risk, idx) => (
                        <li key={idx}>• {risk}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <div className="text-sm text-gray-400 mb-2">Đề xuất hành động</div>
                  <ul className="space-y-2">
                    {analysis.summary.recommendations?.map((rec, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2 text-sm"
                      >
                        <span className="text-cyan-400 mt-1">➤</span>
                        {rec}
                      </li>
                    )) || <p className="text-gray-500">Không có đề xuất</p>}
                  </ul>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Comments List */}
          <CommentList comments={analysis.comments || []} />
        </>
      )}
    </div>
  );
};

export default AnalysisDashboard;
