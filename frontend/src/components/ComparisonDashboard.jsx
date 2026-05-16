// ComparisonDashboard.jsx v3.1 — Enhanced: Per-Bank Detail + Individual Strategies
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import BankComparison from './BankComparison';
import SentimentDetailView from './SentimentDetailView';
import ConsultingStrategy from './ConsultingStrategy';

const API = '/api/v1';

const MAIN_TABS = [
  { id: 'comparison', label: '📊 So sánh Tổng quan' },
  { id: 'individual', label: '🏦 Chi tiết Từng Ngân hàng' },
  { id: 'strategies', label: '🎯 Chiến lược Riêng Biệt' },
];

// ── Per-Bank Panel: Sentiment sub-tabs + Consulting strategy ──────────────────
function BankDetailPanel({ analysis }) {
  const [subTab, setSubTab] = useState('sentiment');
  const bank = analysis.bank || analysis.url;

  return (
    <div className="space-y-4">
      {/* Sub-tabs */}
      <div className="flex gap-2 border-b border-white/10 overflow-x-auto">
        {[
          { id: 'sentiment', label: '📊 Phân tích Sentiment & Bình luận' },
          { id: 'strategy', label: '🎯 Chiến lược Tư vấn' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setSubTab(t.id)}
            className={`px-4 py-2.5 text-sm font-semibold whitespace-nowrap border-b-2 transition ${
              subTab === t.id
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {subTab === 'sentiment' && (
          <motion.div
            key="sentiment"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            {/* SentimentDetailView has its own tabs:
                Phân bố Sentiment | Độ tin cậy | Bình luận chi tiết (with positive/neutral/negative filter) */}
            <SentimentDetailView data={analysis} bank={bank} />
          </motion.div>
        )}

        {subTab === 'strategy' && (
          <motion.div
            key="strategy"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <ConsultingStrategy data={analysis} bank={bank} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function ComparisonDashboard() {
  const location = useLocation();
  const navigate  = useNavigate();

  const [activeTab,          setActiveTab]          = useState('comparison');
  const [selectedBankId,     setSelectedBankId]     = useState(null);
  const [analyses,           setAnalyses]           = useState([]);
  const [loading,            setLoading]            = useState(true);
  const [completedAnalyses,  setCompletedAnalyses]  = useState({});

  // ── Init ──
  useEffect(() => {
    const state = location.state;
    if (state?.analyses && Array.isArray(state.analyses)) {
      setAnalyses(state.analyses);
      const incomplete = state.analyses.filter(a => a.status !== 'completed');
      if (incomplete.length > 0) {
        pollAnalyses(incomplete);
      } else {
        const map = {};
        state.analyses.forEach(a => { map[a.id] = a; });
        setCompletedAnalyses(map);
        setLoading(false);
      }
    } else {
      toast.error('Không tìm thấy dữ liệu phân tích');
      navigate('/');
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Polling ──
  const pollAnalyses = (jobs) => {
    const iv = setInterval(async () => {
      let allDone = true;
      for (const job of jobs) {
        try {
          const res = await axios.get(`${API}/analysis/${job.id}`, { timeout: 10000 });
          const d   = res.data;
          if (d.status === 'completed') {
            setCompletedAnalyses(prev => ({ ...prev, [job.id]: d }));
            setAnalyses(prev => prev.map(a => a.id === job.id ? { ...a, ...d } : a));
          } else if (d.status === 'failed') {
            setCompletedAnalyses(prev => ({ ...prev, [job.id]: { error: d.error } }));
            toast.error(`Phân tích ${d.bank} thất bại`);
          } else {
            allDone = false;
          }
        } catch {
          allDone = false;
        }
      }
      if (allDone) {
        clearInterval(iv);
        setLoading(false);
        toast.success('Tất cả phân tích hoàn tất! 🎉');
      }
    }, 2500);
  };

  const completedCount  = Object.keys(completedAnalyses).length;
  const totalCount      = analyses.length;
  const isAllCompleted  = completedCount >= totalCount && totalCount > 0;
  const validAnalyses   = analyses.filter(a => a.summary && !a.error);

  // Auto-select first bank when data arrives
  useEffect(() => {
    if (validAnalyses.length > 0 && !selectedBankId) {
      setSelectedBankId(validAnalyses[0].id);
    }
  }, [validAnalyses.length]);

  // ── Loading Screen ──
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
            animate={{ width: `${totalCount ? (completedCount / totalCount) * 100 : 0}%` }}
            transition={{ duration: 0.5 }}
            className="h-2 bg-emerald-500"
          />
        </div>
        <p className="text-gray-500 text-xs">Quá trình này có thể mất vài phút...</p>
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

  const selectedAnalysis = validAnalyses.find(a => a.id === selectedBankId) || validAnalyses[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
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
            Phân tích chi tiết{' '}
            <span className="text-emerald-400 font-semibold">{validAnalyses.length} ngân hàng</span>{' '}
            — bình luận theo nhóm & chiến lược riêng biệt
          </p>
        </div>
      </div>

      {/* ── Progress Bar (while polling) ── */}
      {!isAllCompleted && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <p className="text-sm text-blue-300">⏳ Đang phân tích... {completedCount}/{totalCount} hoàn tất</p>
          <div className="mt-2 h-2 bg-blue-500/20 rounded-full overflow-hidden">
            <motion.div
              animate={{ width: `${(completedCount / totalCount) * 100}%` }}
              transition={{ duration: 0.5 }}
              className="h-2 bg-blue-500"
            />
          </div>
        </div>
      )}

      {/* ── Main Tabs ── */}
      <div className="flex gap-1 border-b border-white/10 overflow-x-auto">
        {MAIN_TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition ${
              activeTab === tab.id
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <AnimatePresence mode="wait">

        {/* TAB 1 — Comparison Overview */}
        {activeTab === 'comparison' && (
          <motion.div
            key="comparison"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {validAnalyses.length >= 2 ? (
              <BankComparison
                analyses={validAnalyses}
                onSelectBank={(id) => {
                  setSelectedBankId(id);
                  setActiveTab('individual');
                }}
              />
            ) : (
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-6 text-center">
                <p className="text-yellow-300 font-medium">
                  Cần ít nhất 2 ngân hàng để xem so sánh.
                </p>
                <p className="text-gray-400 text-sm mt-2">
                  Bạn có thể xem chi tiết ngân hàng trong tab bên cạnh.
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* TAB 2 — Individual Bank Detail */}
        {activeTab === 'individual' && (
          <motion.div
            key="individual"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-5"
          >
            {/* Bank Selector Pills */}
            <div className="flex gap-2 flex-wrap">
              {validAnalyses.map(a => {
                const isSelected = selectedBankId === a.id;
                return (
                  <button
                    key={a.id}
                    onClick={() => setSelectedBankId(a.id)}
                    className={`px-4 py-2 rounded-xl text-sm font-semibold border transition ${
                      isSelected
                        ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-lg shadow-emerald-500/10'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:border-white/20'
                    }`}
                  >
                    🏦 {a.bank || a.url}
                    {a.summary && (
                      <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${
                        a.summary.positive_pct >= 50
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {a.summary.positive_pct.toFixed(0)}%+
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Selected Bank Panel */}
            {selectedAnalysis ? (
              <motion.div
                key={selectedAnalysis.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 border border-white/10 rounded-2xl p-6"
              >
                <div className="flex items-center gap-3 mb-6">
                  <span className="text-3xl">🏦</span>
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {selectedAnalysis.bank || selectedAnalysis.url}
                    </h2>
                    <p className="text-xs text-gray-500">{selectedAnalysis.url}</p>
                  </div>
                </div>
                <BankDetailPanel analysis={selectedAnalysis} />
              </motion.div>
            ) : (
              <div className="text-center py-16 text-gray-500">
                Chọn một ngân hàng ở trên để xem chi tiết
              </div>
            )}
          </motion.div>
        )}

        {/* TAB 3 — Individual Strategies */}
        {activeTab === 'strategies' && (
          <motion.div
            key="strategies"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-8"
          >
            <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-500/20 rounded-xl p-4">
              <p className="text-sm text-purple-300 font-semibold">
                🎯 Chiến lược tư vấn được tạo riêng cho từng ngân hàng dựa trên dữ liệu bình luận thực tế
              </p>
            </div>

            {validAnalyses.map((analysis, idx) => (
              <motion.div
                key={analysis.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden"
              >
                {/* Bank Header */}
                <div className="flex items-center gap-4 px-6 py-4 bg-white/5 border-b border-white/10">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center font-bold text-white text-lg">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <h2 className="text-lg font-bold text-white">
                      {analysis.bank || analysis.url}
                    </h2>
                    {analysis.summary && (
                      <div className="flex gap-3 text-xs mt-1">
                        <span className="text-emerald-400">
                          😊 {analysis.summary.positive_pct.toFixed(1)}% tích cực
                        </span>
                        <span className="text-red-400">
                          😤 {analysis.summary.negative_pct.toFixed(1)}% tiêu cực
                        </span>
                        <span className="text-gray-400">
                          📝 {analysis.summary.total_comments} bình luận
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Quick summary badge */}
                  {analysis.summary && (
                    <div className={`px-3 py-1.5 rounded-full text-xs font-bold ${
                      analysis.summary.positive_pct >= 60
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : analysis.summary.negative_pct >= 50
                        ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    }`}>
                      {analysis.summary.positive_pct >= 60
                        ? '📈 Tích cực cao'
                        : analysis.summary.negative_pct >= 50
                        ? '⚠️ Cần cải thiện'
                        : '⚖️ Cân bằng'}
                    </div>
                  )}
                </div>

                {/* Strategy Content */}
                <div className="p-6">
                  <ConsultingStrategy data={analysis} bank={analysis.bank} />
                </div>
              </motion.div>
            ))}

            {validAnalyses.length === 0 && (
              <div className="text-center py-16 text-gray-500">
                Chưa có dữ liệu phân tích
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Error Messages ── */}
      {analyses.filter(a => a.error).map(a => (
        <div key={a.id} className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-300 text-sm">❌ {a.bank}: {a.error}</p>
        </div>
      ))}
    </motion.div>
  );
}
