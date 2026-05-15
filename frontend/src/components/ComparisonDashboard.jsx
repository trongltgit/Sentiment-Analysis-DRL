// ComparisonDashboard.jsx — Main Comparison View
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import BankComparison from './BankComparison';

const API = '/api/v1';
const TABS = [
  { id: 'comparison', label: '📊 So sánh', icon: 'So sánh Ngân hàng' },
  { id: 'individual', label: '🏦 Chi tiết Ngân hàng', icon: 'Phân tích từng ngân hàng' },
];

export default function ComparisonDashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('comparison');
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pollingJobs, setPollingJobs] = useState(new Set());
  const [completedAnalyses, setCompletedAnalyses] = useState({});

  // Fetch initial analyses from location state or URL
  useEffect(() => {
    const state = location.state;
    if (state?.analyses && Array.isArray(state.analyses)) {
      setAnalyses(state.analyses);
      // Start polling for incomplete jobs
      const incompleteJobs = state.analyses.filter(a => a.status !== 'completed');
      if (incompleteJobs.length > 0) {
        setPollingJobs(new Set(incompleteJobs.map(j => j.id)));
        pollAnalyses(incompleteJobs);
      } else {
        setLoading(false);
      }
    } else {
      toast.error('Không tìm thấy dữ liệu phân tích');
      navigate('/');
      setLoading(false);
    }
  }, []);

  // Poll for job completion
  const pollAnalyses = async (jobs) => {
    const pollInterval = setInterval(async () => {
      let allCompleted = true;

      for (const job of jobs) {
        if (completedAnalyses[job.id]) continue; // Skip if already completed

        try {
          const res = await axios.get(`${API}/analysis/${job.id}`, { timeout: 10000 });
          if (res.data.status === 'completed') {
            setCompletedAnalyses(prev => ({
              ...prev,
              [job.id]: res.data,
            }));
            // Update analyses
            setAnalyses(prev =>
              prev.map(a => a.id === job.id ? { ...a, ...res.data } : a)
            );
          } else if (res.data.status === 'failed') {
            setCompletedAnalyses(prev => ({
              ...prev,
              [job.id]: { error: res.data.error },
            }));
            toast.error(`Phân tích ${res.data.bank} thất bại`);
          } else {
            allCompleted = false;
          }
        } catch (err) {
          console.error('Polling error:', err);
          allCompleted = false;
        }
      }

      if (allCompleted) {
        clearInterval(pollInterval);
        setLoading(false);
        toast.success('Tất cả phân tích hoàn tất!');
      }
    }, 2500);

    return pollInterval;
  };

  const completedCount = Object.keys(completedAnalyses).length;
  const totalCount = analyses.length;
  const isAllCompleted = completedCount === totalCount && totalCount > 0;

  if (loading && !isAllCompleted) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <Loader2 size={40} className="text-emerald-400 animate-spin" />
        <p className="text-gray-300 text-sm">
          Đang phân tích {completedCount}/{totalCount} ngân hàng...
        </p>
        <div className="w-64 h-2 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${(completedCount / totalCount) * 100}%` }}
            transition={{ duration: 0.5 }}
            className="h-2 bg-emerald-500"
          />
        </div>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <AlertCircle size={40} className="text-red-400" />
        <p className="text-gray-300">Không tìm thấy dữ liệu phân tích</p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition"
        >
          ← Quay lại
        </button>
      </div>
    );
  }

  const validAnalyses = analyses.filter(a => a.summary && !a.error);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Back Button & Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-white/10 rounded-lg transition"
        >
          <ArrowLeft size={20} className="text-gray-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">So sánh Sentiment Ngân hàng</h1>
          <p className="text-gray-400 text-sm mt-1">
            Phân tích chi tiết {validAnalyses.length} ngân hàng với chiến lược AI
          </p>
        </div>
      </div>

      {/* Progress */}
      {!isAllCompleted && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <p className="text-sm text-blue-300">
            ⏳ Đang phân tích... {completedCount}/{totalCount} hoàn tất
          </p>
          <div className="mt-2 h-2 bg-blue-500/20 rounded-full overflow-hidden">
            <motion.div
              animate={{ width: `${(completedCount / totalCount) * 100}%` }}
              transition={{ duration: 0.5 }}
              className="h-2 bg-blue-500"
            />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10">
        {TABS.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-semibold transition border-b-2 ${
              activeTab === tab.id
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'comparison' && validAnalyses.length > 1 && (
          <motion.div
            key="comparison"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <BankComparison analyses={validAnalyses} />
          </motion.div>
        )}

        {activeTab === 'comparison' && validAnalyses.length === 1 && (
          <motion.div
            key="single"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-6 text-center"
          >
            <p className="text-yellow-300">Cần ít nhất 2 ngân hàng để so sánh</p>
          </motion.div>
        )}

        {activeTab === 'individual' && (
          <motion.div
            key="individual"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {validAnalyses.map((analysis, idx) => (
              <div key={analysis.id} className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-lg font-bold text-white mb-4">
                  {idx + 1}. {analysis.bank || analysis.url}
                </h3>
                {/* Placeholder - You would add individual dashboard views here */}
                <p className="text-gray-400 text-sm">
                  Phân tích chi tiết cho {analysis.bank} - Xem thêm công cụ phân tích chi tiết
                </p>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Messages */}
      {analyses.filter(a => a.error).map(a => (
        <div key={a.id} className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-300 text-sm">
            ❌ {a.bank}: {a.error}
          </p>
        </div>
      ))}
    </motion.div>
  );
}
