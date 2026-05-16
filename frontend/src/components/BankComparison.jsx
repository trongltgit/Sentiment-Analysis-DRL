// BankComparison.jsx v3.1 — Multi-Bank Sentiment Comparison + Clickable Cards
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, TrendingDown, Zap, BarChart3,
  Award, AlertCircle, ArrowRight,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar,
} from 'recharts';

// ── Bank Card ─────────────────────────────────────────────────────────────────
function BankCard({ bank, data, rank, totalBanks, onClick }) {
  const stats    = data.summary;
  const isLeader = rank === 1;
  const isWorst  = rank === totalBanks && totalBanks > 1;

  const ringColor = isLeader
    ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border-emerald-500/40'
    : isWorst
    ? 'bg-gradient-to-br from-red-500/10 to-rose-500/10 border-red-500/30'
    : 'bg-white/5 border-white/10';

  return (
    <motion.button
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.08 }}
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`rounded-xl border p-4 text-left w-full transition group ${ringColor} hover:border-emerald-400/50`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {isLeader && <Award size={14} className="text-yellow-400" />}
            {isWorst  && <AlertCircle size={14} className="text-red-400" />}
            <h3 className="font-bold text-white">{bank}</h3>
          </div>
          <p className={`text-xs ${isLeader ? 'text-emerald-300' : isWorst ? 'text-red-300' : 'text-gray-500'}`}>
            Xếp hạng #{rank}/{totalBanks}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <div className={`text-2xl font-bold ${
            stats.positive_pct >= stats.negative_pct ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {stats.positive_pct.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs mb-3">
        {[
          { label: 'Tích cực', value: stats.positive, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
          { label: 'Tiêu cực', value: stats.negative, color: 'text-red-400',     bg: 'bg-red-500/10'     },
          { label: 'Trung lập', value: stats.neutral,  color: 'text-gray-400',   bg: 'bg-gray-500/10'   },
        ].map(s => (
          <div key={s.label} className={`${s.bg} rounded-lg p-2`}>
            <p className="text-gray-400">{s.label}</p>
            <p className={`font-bold ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Sentiment bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Phân bố</span>
          <span className="text-white font-bold">{stats.total_comments} bình luận</span>
        </div>
        <div className="flex gap-0.5 h-2 rounded-full overflow-hidden bg-white/10">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${stats.positive_pct}%` }}
            transition={{ duration: 0.8 }}
            className="bg-emerald-500"
          />
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${stats.negative_pct}%` }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="bg-red-500"
          />
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${stats.neutral_pct}%` }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="bg-gray-500"
          />
        </div>
      </div>

      {/* Click hint */}
      <div className="mt-3 flex items-center gap-1 text-xs text-gray-500 group-hover:text-emerald-400 transition justify-end">
        <span>Xem chi tiết & chiến lược</span>
        <ArrowRight size={12} />
      </div>
    </motion.button>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function BankComparison({ analyses, onSelectBank }) {
  const [sortBy, setSortBy] = useState('positive');

  const banksData = useMemo(() => analyses.map(a => ({
    id:         a.id,
    bank:       a.bank,
    data:       a,
    positive:   a.summary.positive_pct,
    negative:   a.summary.negative_pct,
    neutral:    a.summary.neutral_pct,
    confidence: a.summary.average_confidence * 100,
    total:      a.summary.total_comments,
  })), [analyses]);

  const sortedBanks = useMemo(() => {
    const copy = [...banksData];
    if (sortBy === 'positive')   copy.sort((a, b) => b.positive   - a.positive);
    if (sortBy === 'negative')   copy.sort((a, b) => a.negative   - b.negative);
    if (sortBy === 'confidence') copy.sort((a, b) => b.confidence - a.confidence);
    return copy;
  }, [banksData, sortBy]);

  const chartData = useMemo(() => sortedBanks.map(b => ({
    bank:     b.bank,
    'Tích cực': +b.positive.toFixed(1),
    'Tiêu cực': +b.negative.toFixed(1),
    'Trung lập': +b.neutral.toFixed(1),
  })), [sortedBanks]);

  const radarData = useMemo(() => {
    const maxTotal = Math.max(...sortedBanks.map(b => b.total), 1);
    return sortedBanks.map(b => ({
      bank:    b.bank.length > 10 ? b.bank.slice(0, 10) + '…' : b.bank,
      'Tích cực': +b.positive.toFixed(1),
      'Tin cậy':  +b.confidence.toFixed(1),
      'Lượng BL': +((b.total / maxTotal) * 100).toFixed(1),
    }));
  }, [sortedBanks]);

  const insights = useMemo(() => {
    if (!sortedBanks.length) return {};
    return {
      leader:   sortedBanks[0],
      worrying: [...sortedBanks].sort((a, b) => b.negative - a.negative)[0],
      balanced: [...sortedBanks].sort((a, b) =>
        Math.abs(50 - a.positive) - Math.abs(50 - b.positive))[0],
    };
  }, [sortedBanks]);

  return (
    <div className="space-y-6">

      {/* ── Controls ── */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 size={18} className="text-blue-400" />
              So sánh {sortedBanks.length} Ngân hàng
            </h2>
            <p className="text-xs text-gray-400 mt-1">
              Click vào từng ngân hàng để xem chi tiết bình luận &amp; chiến lược
            </p>
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1.5 text-xs bg-black/25 border border-white/15 rounded-lg text-white outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="positive">😊 Sắp xếp: Tích cực</option>
            <option value="negative">😤 Sắp xếp: Ít tiêu cực</option>
            <option value="confidence">🎯 Sắp xếp: Tin cậy</option>
          </select>
        </div>
      </div>

      {/* ── Quick Insights ── */}
      {insights.leader && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              icon: <Award size={16} className="text-yellow-400" />,
              label: 'Dẫn đầu',
              bank:  insights.leader.bank,
              value: `${insights.leader.positive.toFixed(1)}% tích cực`,
              color: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30 text-emerald-300',
              id:    insights.leader.id,
            },
            {
              icon: <AlertCircle size={16} className="text-red-400" />,
              label: 'Cảnh báo',
              bank:  insights.worrying.bank,
              value: `${insights.worrying.negative.toFixed(1)}% tiêu cực`,
              color: 'from-red-500/20 to-rose-500/20 border-red-500/30 text-red-300',
              id:    insights.worrying.id,
            },
            {
              icon: <Zap size={16} className="text-blue-400" />,
              label: 'Cân bằng',
              bank:  insights.balanced.bank,
              value: `${Math.abs(insights.balanced.positive - insights.balanced.negative).toFixed(1)}% chênh lệch`,
              color: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30 text-blue-300',
              id:    insights.balanced.id,
            },
          ].map((item, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              onClick={() => onSelectBank?.(item.id)}
              whileHover={{ scale: 1.03 }}
              className={`bg-gradient-to-br ${item.color} rounded-xl p-4 text-left border transition group`}
            >
              <div className="flex items-center gap-2 mb-2">
                {item.icon}
                <p className="text-xs font-semibold">{item.label}</p>
              </div>
              <p className="font-bold text-white text-sm">{item.bank}</p>
              <p className="text-xs mt-1">{item.value}</p>
              <p className="text-xs mt-2 opacity-0 group-hover:opacity-100 transition text-gray-300 flex items-center gap-1">
                Xem chi tiết <ArrowRight size={10} />
              </p>
            </motion.button>
          ))}
        </div>
      )}

      {/* ── Bank Cards Grid ── */}
      <div>
        <p className="text-sm font-semibold text-gray-300 mb-3">
          Xếp hạng ngân hàng — <span className="text-gray-500 text-xs font-normal">Click để xem bình luận chi tiết</span>
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedBanks.map((bank, idx) => (
            <BankCard
              key={bank.bank}
              bank={bank.bank}
              data={bank.data}
              rank={idx + 1}
              totalBanks={sortedBanks.length}
              onClick={() => onSelectBank?.(bank.id)}
            />
          ))}
        </div>
      </div>

      {/* ── Charts ── */}
      <div className="space-y-4">
        {/* Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 border border-white/10 rounded-xl p-6"
        >
          <h3 className="font-semibold text-white text-sm mb-4">
            Phân bố Sentiment theo Ngân hàng (%)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.07)" />
              <XAxis dataKey="bank" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8,
                }}
              />
              <Legend />
              <Bar dataKey="Tích cực" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Tiêu cực" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Trung lập" fill="#6b7280" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Radar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white/5 border border-white/10 rounded-xl p-6"
        >
          <h3 className="font-semibold text-white text-sm mb-4">
            Biểu đồ Radar — So sánh Toàn diện
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis dataKey="bank" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <PolarRadiusAxis tick={{ fill: '#9ca3af', fontSize: 10 }} />
              <Radar name="Tích cực" dataKey="Tích cực" stroke="#10b981" fill="#10b981" fillOpacity={0.25} />
              <Radar name="Tin cậy"  dataKey="Tin cậy"  stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
              <Radar name="Lượng BL" dataKey="Lượng BL" stroke="#a855f7" fill="#a855f7" fillOpacity={0.15} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* ── Comparative Insights ── */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4">Nhận xét So sánh</h3>
        <div className="space-y-4 text-sm">
          {[
            {
              icon: <TrendingUp size={16} className="text-emerald-400 flex-shrink-0 mt-0.5" />,
              title: 'Khoảng cách lớn nhất',
              body: insights.leader && sortedBanks.length > 1
                ? `${insights.leader.bank} dẫn trước ${(
                    insights.leader.positive -
                    [...sortedBanks].sort((a, b) => a.positive - b.positive)[0].positive
                  ).toFixed(1)}% so với ngân hàng thấp nhất`
                : '—',
            },
            {
              icon: <AlertCircle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />,
              title: 'Ngân hàng cần chú ý',
              body: insights.worrying
                ? `${insights.worrying.bank} có tỷ lệ tiêu cực cao nhất (${insights.worrying.negative.toFixed(1)}%)`
                : '—',
            },
            {
              icon: <Zap size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />,
              title: 'Tổng số bình luận',
              body: `${sortedBanks.reduce((s, b) => s + b.total, 0).toLocaleString()} bình luận từ ${sortedBanks.length} ngân hàng`,
            },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-3">
              {item.icon}
              <div>
                <p className="text-white font-semibold">{item.title}</p>
                <p className="text-gray-400 text-xs mt-0.5">{item.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
