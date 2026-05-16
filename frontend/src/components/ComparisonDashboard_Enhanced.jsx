// ComparisonDashboard_Enhanced.jsx v4.1 — Fixed: polling restored + null-safe summary
import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import BankComparison from './BankComparison';
import SentimentDetailView from './SentimentDetailView';
import ConsultingStrategy from './ConsultingStrategy_Enhanced';
import DetailedReviewTab from './DetailedReviewTab';

const API = '/api/v1';

const MAIN_TABS = [
  { id: 'comparison',      label: '📊 So sánh Tổng quan'       },
  { id: 'detailed-review', label: '📋 Bình luận chi tiết'      },
  { id: 'individual',      label: '🏦 Chi tiết Từng Ngân hàng' },
  { id: 'strategies',      label: '🎯 Chiến lược Riêng Biệt'   },
];

// ── Per-Bank Panel ─────────────────────────────────────────────────────────
function BankDetailPanel({ analysis, allAnalyses }) {
  const [subTab, setSubTab] = useState('sentiment');
  const bank = analysis.bank || analysis.url;

  const allBankComments = {};
  if (allAnalyses) {
    allAnalyses.forEach((a) => {
      const name = a.bank || a.url;
      if (a.summary?.comments) allBankComments[name] = a.summary.comments;
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 border-b border-white/10 overflow-x-auto">
        {[
          { id: 'sentiment', label: '📊 Phân tích Sentiment & Bình luận' },
          { id: 'strategy',  label: '🎯 Chiến lược Tư vấn'              },
        ].map((t) => (
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
          <motion.div key="sentiment" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            <SentimentDetailView data={analysis} bank={bank} />
          </motion.div>
        )}
        {subTab === 'strategy' && (
          <motion.div key="strategy" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            <ConsultingStrategy data={analysis} bank={bank} allBankComments={allBankComments} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────
export default function ComparisonDashboard() {
  const location = useLocation();
  const navigate  = useNavigate();

  const [mainTab,   setMainTab]   = useState('comparison');
  const [analyses,  setAnalyses]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [completed, setCompleted] = useState(0);
  const [error,     setError]     = useState(null);
  const completedRef = useRef(0);

  // ── Init & Polling ─────────────────────────────────────────────────────
  useEffect(() => {
    const state = location.state;
    if (!state?.analyses?.length) {
      toast.error('Không tìm thấy dữ liệu phân tích');
      navigate('/');
      return;
    }

    const initial = state.analyses;
    setAnalyses(initial);

    const alreadyDone = initial.filter((a) => a.status === 'completed');
    const pending     = initial.filter((a) => a.status !== 'completed');

    completedRef.current = alreadyDone.length;
    setCompleted(alreadyDone.length);

    if (pending.length === 0) {
      setLoading(false);
      return;
    }

    const total  = initial.length;
    const doneSet = new Set(alreadyDone.map((a) => a.id));

    const iv = setInterval(async () => {
      for (const job of pending) {
        if (doneSet.has(job.id)) continue;
        try {
          const res = await axios.get(`${API}/analysis/${job.id}`, { timeout: 12000 });
          const d   = res.data;

          if (d.status === 'completed' || d.status === 'failed') {
            doneSet.add(job.id);
            completedRef.current += 1;
            setCompleted(completedRef.current);
            setAnalyses((prev) =>
              prev.map((a) => (a.id === job.id ? { ...a, ...d } : a))
            );
            if (d.status === 'failed') {
              toast.error(`Phân tích ${d.bank || job.id} thất bại`);
            }
          }
        } catch {
          // transient network error — will retry
        }
      }

      if (doneSet.size >= total) {
        clearInterval(iv);
        setLoading(false);
        toast.success('Tất cả phân tích hoàn tất! 🎉');
      }
    }, 2500);

    return () => clearInterval(iv);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Derived: only banks with a fully-populated summary ────────────────
  const validAnalyses = analyses.filter(
    (a) => a.status === 'completed' && a.summary && a.summary.positive_pct != null
  );

  const bankComments = {};
  validAnalyses.forEach((a) => {
    const name = a.bank || a.url;
    if (a.summary?.comments) bankComments[name] = a.summary.comments;
  });

  // ── Loading Screen ─────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <Loader2 size={40} className="text-emerald-400 animate-spin" />
        <p className="text-gray-300 text-sm">
          Đang phân tích {completed}/{analyses.length} ngân hàng...
        </p>
        <div className="w-64 h-2 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${analyses.length ? (completed / analyses.length) * 100 : 0}%` }}
            transition={{ duration: 0.5 }}
            className="h-2 bg-emerald-500"
          />
        </div>
        {validAnalyses.length > 0 && (
          <>
            <p className="text-emerald-400 text-xs">
              ✅ {validAnalyses.length} ngân hàng đã xong
            </p>
            <button
              onClick={() => setLoading(false)}
              className="px-4 py-2 text-sm rounded-lg bg-white/10 hover:bg-white/20 text-gray-300 transition"
            >
              Xem kết quả tạm thời
            </button>
          </>
        )}
        <p className="text-gray-500 text-xs">Quá trình này có thể mất vài phút...</p>
      </div>
    );
  }

  if (error || !validAnalyses.length) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 max-w-md mx-auto"
      >
        <AlertCircle size={32} className="text-red-400 mb-3" />
        <h2 className="font-bold text-red-400 mb-2">Không có dữ liệu hợp lệ</h2>
        <p className="text-red-200 text-sm mb-4">
          {error || 'Tất cả phân tích đều thất bại hoặc chưa hoàn tất.'}
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
        >
          Quay lại
        </button>
      </motion.div>
    );
  }

  // ── Main Render ────────────────────────────────────────────────────────
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">

      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-2 hover:bg-white/10 rounded-lg transition">
          <ArrowLeft size={20} className="text-gray-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">
            📊 So sánh {validAnalyses.length} Ngân hàng
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Phân tích toàn diện, so sánh sentiment và chiến lược tư vấn chi tiết
          </p>
        </div>
      </div>

      {/* Still-polling banner */}
      {completed < analyses.length && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-sm text-blue-300">
          ⏳ {analyses.length - completed} ngân hàng vẫn đang xử lý — trang sẽ tự cập nhật
        </div>
      )}

      {/* Failed rows */}
      {analyses.filter((a) => a.status === 'failed').map((a) => (
        <div key={a.id} className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-300">
          ❌ {a.bank || a.url}: {a.error}
        </div>
      ))}

      {/* Main Tabs */}
      <div className="border-b border-white/10 overflow-x-auto">
        <div className="flex gap-2">
          {MAIN_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setMainTab(tab.id)}
              className={`px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition ${
                mainTab === tab.id
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">

        {mainTab === 'comparison' && (
          <motion.div key="comparison" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            {validAnalyses.length >= 2
              ? <BankComparison analyses={validAnalyses} />
              : (
                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-6 text-center">
                  <p className="text-yellow-300 font-medium">Cần ít nhất 2 ngân hàng để so sánh.</p>
                  <p className="text-gray-400 text-sm mt-2">Xem chi tiết trong tab "Chi tiết Từng Ngân hàng".</p>
                </div>
              )
            }
          </motion.div>
        )}

        {mainTab === 'detailed-review' && (
          <motion.div key="detailed-review" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            <DetailedReviewTab
              bankComments={bankComments}
              bankData={validAnalyses.reduce((acc, a) => {
                acc[a.bank || a.url] = a.summary || {};
                return acc;
              }, {})}
            />
          </motion.div>
        )}

        {mainTab === 'individual' && (
          <motion.div key="individual" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-8">
            {validAnalyses.map((analysis, idx) => (
              <motion.div
                key={analysis.bank || analysis.url}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-white/5 border border-white/10 rounded-xl p-6"
              >
                <h2 className="text-2xl font-bold text-white mb-4">
                  {analysis.bank || analysis.url}
                </h2>
                <BankDetailPanel analysis={analysis} allAnalyses={validAnalyses} />
              </motion.div>
            ))}
          </motion.div>
        )}

        {mainTab === 'strategies' && (
          <motion.div key="strategies" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-8">
            {validAnalyses.map((analysis, idx) => {
              const allBankComments = {};
              validAnalyses.forEach((a) => {
                const n = a.bank || a.url;
                if (a.summary?.comments) allBankComments[n] = a.summary.comments;
              });
              return (
                <motion.div
                  key={analysis.bank || analysis.url}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="bg-white/5 border border-white/10 rounded-xl p-6"
                >
                  <h2 className="text-2xl font-bold text-white mb-4">
                    🎯 Chiến lược cho {analysis.bank || analysis.url}
                  </h2>
                  <ConsultingStrategy
                    data={analysis}
                    bank={analysis.bank || analysis.url}
                    allBankComments={allBankComments}
                  />
                </motion.div>
              );
            })}
          </motion.div>
        )}

      </AnimatePresence>
    </motion.div>
  );
}
