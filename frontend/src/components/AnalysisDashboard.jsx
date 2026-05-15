// AnalysisDashboard.jsx v2.0 — Groq-powered Financial Sentiment Dashboard
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

const API = '/api/v1';
const COLORS = { positive: '#10b981', negative: '#ef4444', neutral: '#6b7280' };

// ─── Helpers ─────────────────────────────────────────────────

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

function SentimentMeter({ positive_pct, negative_pct, neutral_pct }) {
  return (
    <div className="space-y-2">
      {[
        { label: '😊 Tích cực', pct: positive_pct, color: 'bg-emerald-500' },
        { label: '😤 Tiêu cực', pct: negative_pct, color: 'bg-red-500' },
        { label: '😐 Trung lập', pct: neutral_pct,  color: 'bg-gray-500' },
      ].map(r => (
        <div key={r.label}>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-300">{r.label}</span>
            <span className="text-white font-bold">{r.pct?.toFixed(1)}%</span>
          </div>
          <div className="bg-white/10 rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${r.pct}%` }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className={`h-2 rounded-full ${r.color}`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function CommentCard({ comment, idx }) {
  const [expanded, setExpanded] = useState(false);
  const colors = {
    positive: 'border-emerald-500/30 bg-emerald-500/5',
    negative: 'border-red-500/30 bg-red-500/5',
    neutral:  'border-gray-500/30 bg-gray-500/5',
  };
  const confColor = comment.confidence >= 0.85 ? 'text-emerald-400'
    : comment.confidence >= 0.70 ? 'text-blue-400'
    : comment.confidence >= 0.55 ? 'text-yellow-400' : 'text-gray-400';

  const isLong = comment.text?.length > 160;
  const text   = isLong && !expanded ? comment.text.slice(0, 160) + '…' : comment.text;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: idx * 0.03 }}
      className={`rounded-xl border p-3 ${colors[comment.sentiment] || colors.neutral}`}
    >
      <p className="text-sm text-gray-200 leading-relaxed">{text}</p>

      {isLong && (
        <button onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-400 mt-1 flex items-center gap-0.5 hover:text-blue-300">
          {expanded ? <><ChevronUp size={12} />Thu gọn</> : <><ChevronDown size={12} />Xem thêm</>}
        </button>
      )}

      <div className="flex flex-wrap gap-1.5 mt-2 items-center">
        <span className={`text-xs font-semibold ${confColor}`}>
          {(comment.confidence * 100).toFixed(0)}% tin cậy
        </span>
        {comment.source === 'groq' && (
          <span className="text-xs px-1.5 py-0.5 bg-purple-500/20 text-purple-300 rounded border border-purple-500/20">
            🤖 Groq
          </span>
        )}
        {comment.keywords?.map(kw => (
          <span key={kw} className="text-xs px-1.5 py-0.5 bg-white/10 text-gray-300 rounded">{kw}</span>
        ))}
      </div>
    </motion.div>
  );
}

function InsightCard({ icon: Icon, title, items, color }) {
  if (!items?.length) return null;
  return (
    <div className={`rounded-xl border p-4 ${color}`}>
      <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
        <Icon size={15} />{title}
      </h4>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={i} className="bg-black/20 rounded-lg p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm text-gray-200">{item.description || item.action}</p>
              {(item.severity || item.priority || item.potential) && (
                <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${
                  (item.severity || item.priority || item.potential) === 'high'
                    ? 'bg-red-500/20 text-red-300'
                    : (item.severity || item.priority || item.potential) === 'medium'
                    ? 'bg-yellow-500/20 text-yellow-300'
                    : 'bg-green-500/20 text-green-300'
                }`}>
                  {item.severity || item.priority || item.potential}
                </span>
              )}
            </div>
            {item.impact && <p className="text-xs text-gray-500 mt-1">{item.impact}</p>}
            {item.timeline && <p className="text-xs text-gray-500 mt-1">⏱ {item.timeline} · {item.owner}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────

export default function AnalysisDashboard() {
  const { id }     = useParams();
  const navigate   = useNavigate();
  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [polling,  setPolling]  = useState(true);
  const [tab,      setTab]      = useState('overview');    // overview | comments | insights
  const [commCat,  setCommCat]  = useState('positive');

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
      <p className="text-gray-300 text-sm">Đang tải kết quả phân tích...</p>
    </div>
  );

  if (!data) return (
    <div className="text-center py-32">
      <AlertCircle size={40} className="mx-auto text-red-400 mb-4" />
      <p className="text-red-300">Không tìm thấy phân tích. <a href="/" className="underline text-blue-400">Quay về</a></p>
    </div>
  );

  const s  = data.summary;
  const ins = data.insights || {};

  // Pie chart data
  const pieData = s ? [
    { name: 'Tích cực', value: s.positive, color: COLORS.positive },
    { name: 'Tiêu cực', value: s.negative, color: COLORS.negative },
    { name: 'Trung lập', value: s.neutral,  color: COLORS.neutral  },
  ].filter(d => d.value > 0) : [];

  const confDist = s?.confidence_distribution
    ? Object.entries(s.confidence_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const tabs = ['overview', 'comments', 'insights'];
  const tabLabels = { overview: '📊 Tổng quan', comments: '💬 Bình luận', insights: '💡 Insights' };

  return (
    <div className="max-w-5xl mx-auto">

      {/* Back + Status bar */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/')} className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-gray-400 text-xs truncate">{data.url}</p>
          <div className="flex items-center gap-3 mt-1">
            <StatusBadge status={data.status} />
            {data.processing_time && (
              <span className="text-gray-500 text-xs">⏱ {data.processing_time}s</span>
            )}
            {s?.ai_engine && (
              <span className="text-purple-400 text-xs">🤖 {s.ai_engine}</span>
            )}
          </div>
        </div>
        {data.status === 'processing' && (
          <RefreshCw size={16} className="text-blue-400 animate-spin shrink-0" />
        )}
      </div>

      {/* Error */}
      {data.status === 'failed' && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 text-red-300 text-sm">
          <AlertCircle size={16} className="inline mr-2" />{data.error}
        </div>
      )}

      {/* Processing message */}
      {data.status === 'processing' && (
        <motion.div
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6 mb-6 text-center"
        >
          <BrainCircuit size={32} className="mx-auto text-blue-400 mb-3 animate-spin" />
          <p className="text-blue-300 font-semibold">Groq LLaMA 3.3 70B đang phân tích...</p>
          <p className="text-gray-400 text-xs mt-1">Xử lý từng bình luận với AI chuyên nghiệp</p>
        </motion.div>
      )}

      {/* Tabs */}
      {data.status === 'completed' && s && (
        <>
          <div className="flex gap-2 mb-6">
            {tabs.map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
                  tab === t
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}>
                {tabLabels[t]}
              </button>
            ))}
          </div>

          {/* ── OVERVIEW TAB ── */}
          {tab === 'overview' && (
            <div className="space-y-5">

              {/* Executive summary */}
              {ins.executive_summary && (
                <div className="bg-gradient-to-r from-emerald-900/40 to-teal-900/40 border border-emerald-500/20 rounded-xl p-4">
                  <p className="text-sm font-semibold text-emerald-300 mb-1">📋 Tóm tắt điều hành</p>
                  <p className="text-gray-200 text-sm">{ins.executive_summary}</p>
                </div>
              )}

              {/* KPI row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Tổng bình luận', value: s.total_comments, icon: '📝', color: 'text-white' },
                  { label: 'Tích cực',        value: `${s.positive_pct}%`, icon: '😊', color: 'text-emerald-400' },
                  { label: 'Tiêu cực',        value: `${s.negative_pct}%`, icon: '😤', color: 'text-red-400' },
                  { label: 'Độ tin cậy',      value: `${(s.average_confidence * 100).toFixed(0)}%`, icon: '🎯', color: 'text-blue-400' },
                ].map(k => (
                  <div key={k.label} className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
                    <div className="text-2xl mb-1">{k.icon}</div>
                    <div className={`text-xl font-extrabold ${k.color}`}>{k.value}</div>
                    <div className="text-gray-400 text-xs mt-0.5">{k.label}</div>
                  </div>
                ))}
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Pie */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-sm font-semibold text-gray-300 mb-3">Phân bố Sentiment</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} dataKey="value">
                        {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                      </Pie>
                      <Tooltip formatter={(v, n) => [v, n]} contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-4 mt-2">
                    {pieData.map(d => (
                      <span key={d.name} className="flex items-center gap-1 text-xs text-gray-400">
                        <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: d.color }} />
                        {d.name}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Confidence bar */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-sm font-semibold text-gray-300 mb-3">Phân bố Độ tin cậy</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={confDist} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                      <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                      <Bar dataKey="value" fill="#10b981" radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Sentiment meters */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <p className="text-sm font-semibold text-gray-300 mb-4">Chỉ số Sentiment</p>
                <SentimentMeter
                  positive_pct={s.positive_pct}
                  negative_pct={s.negative_pct}
                  neutral_pct={s.neutral_pct}
                />
              </div>

              {/* Risk / Opportunity scores */}
              {(ins.risk_score !== undefined || ins.opportunity_score !== undefined) && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
                    <Shield size={20} className="mx-auto text-red-400 mb-1" />
                    <div className="text-2xl font-extrabold text-red-400">{ins.risk_score}</div>
                    <div className="text-gray-400 text-xs">Điểm Rủi ro / 100</div>
                  </div>
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
                    <Target size={20} className="mx-auto text-emerald-400 mb-1" />
                    <div className="text-2xl font-extrabold text-emerald-400">{ins.opportunity_score}</div>
                    <div className="text-gray-400 text-xs">Cơ hội / 100</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── COMMENTS TAB ── */}
          {tab === 'comments' && (
            <div>
              <div className="flex gap-2 mb-4">
                {['positive','negative','neutral'].map(cat => {
                  const count = data.comments?.[cat]?.length || 0;
                  const colors = {
                    positive: 'bg-emerald-500/20 border-emerald-500/30 text-emerald-300',
                    negative: 'bg-red-500/20 border-red-500/30 text-red-300',
                    neutral:  'bg-gray-500/20 border-gray-500/30 text-gray-300',
                  };
                  return (
                    <button key={cat} onClick={() => setCommCat(cat)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                        commCat === cat ? colors[cat] : 'text-gray-500 border-transparent hover:bg-white/5'
                      }`}>
                      {{positive:'😊 Tích cực',negative:'😤 Tiêu cực',neutral:'😐 Trung lập'}[cat]} ({count})
                    </button>
                  );
                })}
              </div>

              <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
                {(data.comments?.[commCat] || []).length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-10">Không có bình luận trong danh mục này</p>
                ) : (
                  (data.comments[commCat] || []).map((c, i) => (
                    <CommentCard key={c.id || i} comment={c} idx={i} />
                  ))
                )}
              </div>
            </div>
          )}

          {/* ── INSIGHTS TAB ── */}
          {tab === 'insights' && (
            <div className="space-y-4">
              <InsightCard
                icon={Shield}
                title="⚠️ Rủi ro phát hiện"
                items={ins.risks}
                color="border-red-500/20 bg-red-500/5"
              />
              <InsightCard
                icon={TrendingUp}
                title="🚀 Cơ hội tiềm năng"
                items={ins.opportunities}
                color="border-emerald-500/20 bg-emerald-500/5"
              />
              <InsightCard
                icon={Lightbulb}
                title="📋 Khuyến nghị chiến lược"
                items={ins.recommendations}
                color="border-blue-500/20 bg-blue-500/5"
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
