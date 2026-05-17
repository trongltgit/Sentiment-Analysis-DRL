// DetailedReviewTab.jsx — Hiển thị bình luận THẬT theo ngân hàng + sentiment
// Dữ liệu thật từ API: bankComments[bankName] = { positive: [...], negative: [...], neutral: [...] }
// Mỗi comment: { id, text, sentiment, confidence, confidence_level, keywords, source }

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

// ─── Cấu hình màu sắc theo sentiment ─────────────────────────────────────────
const SENT_CONFIG = {
  positive: {
    label: 'Tích cực',
    icon: '😊',
    badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    card: 'bg-emerald-500/5 border-emerald-500/25',
    dot: 'bg-emerald-400',
    activeFilter: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  },
  negative: {
    label: 'Tiêu cực',
    icon: '😤',
    badge: 'bg-red-500/15 text-red-300 border-red-500/30',
    card: 'bg-red-500/5 border-red-500/25',
    dot: 'bg-red-400',
    activeFilter: 'bg-red-500/20 text-red-300 border-red-500/30',
  },
  neutral: {
    label: 'Trung lập',
    icon: '😐',
    badge: 'bg-gray-500/15 text-gray-300 border-gray-500/30',
    card: 'bg-gray-500/5 border-gray-500/25',
    dot: 'bg-gray-400',
    activeFilter: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
  },
};

function confColor(conf) {
  if (conf >= 0.85) return 'text-emerald-400';
  if (conf >= 0.70) return 'text-blue-400';
  if (conf >= 0.55) return 'text-yellow-400';
  return 'text-gray-400';
}

// ─── Card từng bình luận ──────────────────────────────────────────────────────
function CommentCard({ comment, idx }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = SENT_CONFIG[comment.sentiment] || SENT_CONFIG.neutral;
  const text = comment.text || '';
  const isLong = text.length > 200;
  const displayText = isLong && !expanded ? text.slice(0, 200) + '…' : text;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(idx * 0.04, 0.5) }}
      className={`rounded-xl border p-4 ${cfg.card}`}
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${cfg.badge}`}>
          {cfg.icon} {cfg.label}
        </span>
        <span className={`text-sm font-bold tabular-nums ${confColor(comment.confidence || 0)}`}>
          🎯 {(((comment.confidence || 0)) * 100).toFixed(0)}%
          <span className="text-xs font-normal opacity-60 ml-1">tin cậy</span>
        </span>
      </div>

      <p className="text-sm text-gray-200 leading-relaxed mb-2">"{displayText}"</p>

      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mb-2 transition"
        >
          {expanded
            ? <><ChevronUp size={12} />Thu gọn</>
            : <><ChevronDown size={12} />Xem thêm ({text.length - 200} ký tự còn lại)</>}
        </button>
      )}

      {comment.keywords?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {comment.keywords.map((kw, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-gray-300">
              {kw}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// ─── Panel bình luận một ngân hàng ────────────────────────────────────────────
function BankPanel({ groups }) {
  const [activeSent, setActiveSent] = useState('all');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('default');

  const totals = useMemo(() => ({
    positive: (groups.positive || []).length,
    negative: (groups.negative || []).length,
    neutral:  (groups.neutral  || []).length,
    all: (groups.positive || []).length + (groups.negative || []).length + (groups.neutral || []).length,
  }), [groups]);

  const positiveRate = totals.all > 0
    ? ((totals.positive / totals.all) * 100).toFixed(1)
    : '0.0';

  const filtered = useMemo(() => {
    const lists = activeSent === 'all'
      ? ['positive', 'negative', 'neutral']
      : [activeSent];

    let base = [];
    lists.forEach(s => {
      (groups[s] || []).forEach(c => base.push({ ...c, sentiment: s }));
    });

    if (search.trim()) {
      const q = search.toLowerCase();
      base = base.filter(c =>
        (c.text || '').toLowerCase().includes(q) ||
        (c.keywords || []).some(k => k.toLowerCase().includes(q))
      );
    }

    if (sortBy === 'confidence_desc') {
      base = [...base].sort((a, b) => (b.confidence || 0) - (a.confidence || 0));
    } else if (sortBy === 'confidence_asc') {
      base = [...base].sort((a, b) => (a.confidence || 0) - (b.confidence || 0));
    }

    return base;
  }, [groups, activeSent, search, sortBy]);

  return (
    <div className="space-y-4">
      {/* Thống kê nhanh */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Tổng bình luận', value: totals.all,        color: 'text-white',       icon: <MessageSquare size={16} className="text-blue-400" /> },
          { label: 'Tích cực',       value: totals.positive,   color: 'text-emerald-400', icon: <TrendingUp    size={16} className="text-emerald-400" /> },
          { label: 'Tiêu cực',       value: totals.negative,   color: 'text-red-400',     icon: <AlertTriangle size={16} className="text-red-400" /> },
          { label: 'Tỷ lệ tích cực', value: `${positiveRate}%`, color: 'text-cyan-400',  icon: <BarChart3     size={16} className="text-cyan-400" /> },
        ].map((s, i) => (
          <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-3 flex items-center gap-3">
            <div className="shrink-0">{s.icon}</div>
            <div>
              <p className={`text-lg font-bold leading-none ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Bộ lọc sentiment */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveSent('all')}
          className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition border ${
            activeSent === 'all'
              ? 'bg-blue-500/20 text-blue-300 border-blue-500/30'
              : 'bg-white/5 text-gray-400 border-white/10 hover:text-white hover:bg-white/10'
          }`}
        >
          📋 Tất cả ({totals.all})
        </button>
        {['positive', 'negative', 'neutral'].map(s => {
          const cfg = SENT_CONFIG[s];
          const isActive = activeSent === s;
          return (
            <button
              key={s}
              onClick={() => setActiveSent(s)}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition border flex items-center gap-1.5 ${
                isActive
                  ? cfg.activeFilter
                  : 'bg-white/5 text-gray-400 border-white/10 hover:text-white hover:bg-white/10'
              }`}
            >
              {cfg.icon} {cfg.label}
              <span className={`text-xs font-normal ${isActive ? '' : 'opacity-60'}`}>
                ({totals[s]})
              </span>
            </button>
          );
        })}
      </div>

      {/* Tìm kiếm + sắp xếp */}
      <div className="flex gap-2 flex-col sm:flex-row">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Tìm trong bình luận hoặc từ khóa..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-black/25 border border-white/15 rounded-lg text-white text-sm placeholder-gray-500 outline-none focus:ring-1 focus:ring-emerald-500/50 focus:border-emerald-500/40 transition"
          />
        </div>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          className="px-3 py-2 bg-black/25 border border-white/15 rounded-lg text-white text-sm outline-none focus:ring-1 focus:ring-emerald-500/50"
        >
          <option value="default">Thứ tự gốc</option>
          <option value="confidence_desc">Độ tin cậy cao → thấp</option>
          <option value="confidence_asc">Độ tin cậy thấp → cao</option>
        </select>
      </div>

      {/* Danh sách bình luận */}
      <AnimatePresence mode="wait">
        {filtered.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12 text-gray-500"
          >
            <MessageSquare size={32} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">Không tìm thấy bình luận phù hợp</p>
          </motion.div>
        ) : (
          <motion.div
            key={`${activeSent}-${search}-${sortBy}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-3 max-h-[65vh] overflow-y-auto pr-1"
          >
            {/* Hiển thị theo nhóm nếu đang xem "Tất cả" */}
            {activeSent === 'all'
              ? ['positive', 'negative', 'neutral'].map(s => {
                  const list = filtered.filter(c => c.sentiment === s);
                  if (list.length === 0) return null;
                  const cfg = SENT_CONFIG[s];
                  return (
                    <div key={s}>
                      {/* Tiêu đề nhóm */}
                      <div className="flex items-center gap-2 py-2 sticky top-0 bg-slate-900/80 backdrop-blur-sm z-10">
                        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${cfg.dot}`} />
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                          {cfg.icon} {cfg.label} — {list.length} bình luận
                        </span>
                        <div className="flex-1 h-px bg-white/10" />
                      </div>
                      <div className="space-y-2">
                        {list.map((c, idx) => (
                          <CommentCard key={c.id || idx} comment={c} idx={idx} />
                        ))}
                      </div>
                    </div>
                  );
                })
              : filtered.map((c, idx) => (
                  <CommentCard key={c.id || idx} comment={c} idx={idx} />
                ))
            }
          </motion.div>
        )}
      </AnimatePresence>

      <p className="text-xs text-gray-600 text-right">
        Đang hiển thị {filtered.length} / {totals.all} bình luận
      </p>
    </div>
  );
}

// ─── Component chính ──────────────────────────────────────────────────────────
// Props:
//   bankComments = { "VCB": { positive: [...], negative: [...], neutral: [...] }, ... }
//   bankData     = { "VCB": { summary... }, ... }  (không dùng trực tiếp ở đây)
const DetailedReviewTab = ({ bankComments = {}, bankData = {} }) => {
  const bankNames = Object.keys(bankComments);
  const [activeBank, setActiveBank] = useState(bankNames[0] || '');

  // Sync activeBank nếu dữ liệu thay đổi
  React.useEffect(() => {
    if (bankNames.length && !bankNames.includes(activeBank)) {
      setActiveBank(bankNames[0]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bankNames.join(',')]);

  if (bankNames.length === 0) {
    return (
      <div className="text-center py-20">
        <MessageSquare size={40} className="mx-auto text-gray-600 mb-3" />
        <p className="text-gray-400">Chưa có dữ liệu bình luận.</p>
        <p className="text-gray-600 text-sm mt-1">
          Hãy đảm bảo phân tích đã hoàn tất và có bình luận được thu thập.
        </p>
      </div>
    );
  }

  const currentGroups = bankComments[activeBank] || { positive: [], negative: [], neutral: [] };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h2 className="text-xl font-bold text-white mb-1">
          📋 Bình luận chi tiết theo ngân hàng
        </h2>
        <p className="text-gray-400 text-sm">
          Xem từng bình luận thật được thu thập và phân tích — nhóm theo Tích cực, Tiêu cực, Trung lập.
        </p>
      </div>

      {/* Tab chọn ngân hàng */}
      <div className="border-b border-white/10 overflow-x-auto">
        <div className="flex gap-1">
          {bankNames.map(name => {
            const g = bankComments[name] || {};
            const total = (g.positive?.length || 0) + (g.negative?.length || 0) + (g.neutral?.length || 0);
            const isActive = activeBank === name;
            return (
              <button
                key={name}
                onClick={() => setActiveBank(name)}
                className={`px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition-all flex items-center gap-2 ${
                  isActive
                    ? 'border-emerald-500 text-emerald-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                🏦 {name}
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  isActive
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-white/10 text-gray-500'
                }`}>
                  {total}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Nội dung ngân hàng đang chọn */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeBank}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
        >
          <BankPanel groups={currentGroups} />
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default DetailedReviewTab;
