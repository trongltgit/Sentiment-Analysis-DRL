// AnalysisDashboard.jsx v3.0 — Enhanced with Detail Views & Strategy
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle, CheckCircle, Clock, BrainCircuit, RefreshCw,
  TrendingUp, TrendingDown, Zap, Shield, Target, ArrowLeft,
  BarChart3, Lightbulb, ChevronDown, ChevronUp, ExternalLink,
} from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';
import axios from 'axios';
import toast from 'react-hot-toast';
import SentimentDetailView from './SentimentDetailView';
import ConsultingStrategy from './ConsultingStrategy';

const API = '/api/v1';
const COLORS = { positive: '#10b981', negative: '#ef4444', neutral: '#6b7280' };

function StatusBadge({ status }) {
  const cfg = {
    pending:    { color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20', icon: <Clock size={14} className="animate-pulse" />,         label: 'Đang chờ' },
    processing: { color: 'text-blue-400  bg-blue-400/10  border-blue-400/20',  icon: <BrainCircuit size={14} className="animate-spin" />, label: 'Đang phân tích...' },
    completed:  { color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20', icon: <CheckCircle size={14} />,                  label: 'Hoàn tất' },
    failed:     { color: 'text-red-400   bg-red-400/10   border-red-400/20',   icon: <AlertCircle size={14} />,                       label: 'Thất bại' },
  }[status] || { color: 'text-gray-400', icon: null, label: status };

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold ${cfg.color}`}>
      {cfg.icon}{cfg.label}
    </span>
  );
}

export default function AnalysisDashboard() {
  const { id }     = useParams();
  const navigate   = useNavigate();
  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [polling,  setPolling]  = useState(true);
  const [tab,      setTab]      = useState('sentiment');  // sentiment | insights | strategy

  const fetchData = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/analysis/${id}`, { timeout: 15000 });
      setData(res.data);
      if (['completed', 'failed'].includes(res.data.status)) setPolling(false);
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('Không tìm thấy phân tích'); setPolling(false);
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
    if (!polling) return;
    const iv = setInterval(() => { if (polling) fetchData(); }, 2500);
    return () => clearInterval(iv);
  }, [fetchData, polling]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-32 gap-4">
      <BrainCircuit size={40} className="text-emerald-400 animate-spin" />
      <p className="text-gray-300">Đang tải phân tích...</p>
    </div>
  );

  if (!data) return (
    <div className="text-center py-20">
      <AlertCircle size={40} className="mx-auto text-red-400 mb-4" />
      <p className="text-gray-400">Không tìm thấy phân tích</p>
    </div>
  );

  const s = data.summary;
  const ins = data.insights || {};
  const bank = data.bank || 'Unknown Bank';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Back Button */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition"
      >
        <ArrowLeft size={18} />
        <span className="text-sm">Quay lại</span>
      </button>

      {/* Header */}
      <div className="bg-white/8 backdrop-blur-md rounded-2xl p-6 border border-white/15">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">{bank}</h1>
            <p className="text-gray-400 text-sm">{data.url}</p>
          </div>
          <StatusBadge status={data.status} />
        </div>

        {data.completed_at && (
          <p className="text-xs text-gray-500">
            ✓ Hoàn tất lúc {new Date(data.completed_at).toLocaleTimeString('vi-VN')}
            {data.processing_time && ` (${data.processing_time.toFixed(2)}s)`}
          </p>
        )}
      </div>

      {/* Error State */}
      {data.status === 'failed' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-500/10 border border-red-500/30 rounded-xl p-4"
        >
          <p className="text-red-300 text-sm">❌ Lỗi: {data.error}</p>
        </motion.div>
      )}

      {/* Tabs - Main Content */}
      {data.status === 'completed' && s && (
        <>
          <div className="flex gap-2 border-b border-white/10 overflow-x-auto">
            {[
              { id: 'sentiment', label: '📊 Phân tích Sentiment', icon: BarChart3 },
              { id: 'insights', label: '💡 Insights', icon: Lightbulb },
              { id: 'strategy', label: '🎯 Chiến lược', icon: Target },
            ].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`px-4 py-3 text-sm font-semibold transition border-b-2 flex items-center gap-2 whitespace-nowrap ${
                  tab === t.id
                    ? 'border-emerald-500 text-emerald-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}>
                {t.label}
              </button>
            ))}
          </div>

          {/* Sentiment Tab */}
          {tab === 'sentiment' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <SentimentDetailView data={data} bank={bank} />
            </motion.div>
          )}

          {/* Insights Tab */}
          {tab === 'insights' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {/* Executive Summary */}
              {ins.executive_summary && (
                <div className="bg-gradient-to-r from-emerald-900/40 to-teal-900/40 border border-emerald-500/20 rounded-xl p-4">
                  <p className="text-sm font-semibold text-emerald-300 mb-2">📋 Tóm tắt điều hành</p>
                  <p className="text-gray-200 text-sm">{ins.executive_summary}</p>
                </div>
              )}

              {/* Risk & Opportunity */}
              {(ins.risk_score !== undefined || ins.opportunity_score !== undefined) && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
                    <Shield size={20} className="mx-auto text-red-400 mb-2" />
                    <div className="text-2xl font-extrabold text-red-400">{ins.risk_score}</div>
                    <div className="text-gray-400 text-xs">Điểm Rủi ro / 100</div>
                  </div>
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
                    <Target size={20} className="mx-auto text-emerald-400 mb-2" />
                    <div className="text-2xl font-extrabold text-emerald-400">{ins.opportunity_score}</div>
                    <div className="text-gray-400 text-xs">Cơ hội / 100</div>
                  </div>
                </div>
              )}

              {/* Insights Cards */}
              <div className="space-y-4">
                {ins.risks?.length > 0 && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
                    <h4 className="font-semibold text-red-300 mb-3">⚠️ Rủi ro phát hiện</h4>
                    <div className="space-y-2">
                      {ins.risks.slice(0, 3).map((r, i) => (
                        <div key={i} className="bg-black/20 rounded p-2">
                          <p className="text-sm text-gray-200">{r.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {ins.opportunities?.length > 0 && (
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                    <h4 className="font-semibold text-emerald-300 mb-3">🚀 Cơ hội tiềm năng</h4>
                    <div className="space-y-2">
                      {ins.opportunities.slice(0, 3).map((o, i) => (
                        <div key={i} className="bg-black/20 rounded p-2">
                          <p className="text-sm text-gray-200">{o.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Strategy Tab */}
          {tab === 'strategy' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <ConsultingStrategy data={data} bank={bank} />
            </motion.div>
          )}
        </>
      )}
    </motion.div>
  );
}
