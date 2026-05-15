// BankComparison.jsx — Multi-Bank Sentiment Comparison
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, Zap, BarChart3, Award, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

function BankCard({ bank, data, rank, totalBanks }) {
  const stats = data.summary;
  const isLeader = rank === 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.1 }}
      className={`rounded-xl border p-4 transition ${
        isLeader
          ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border-emerald-500/40'
          : 'bg-white/5 border-white/10'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {isLeader && <Award size={14} className="text-yellow-400" />}
            <h3 className="font-bold text-white">{bank}</h3>
          </div>
          <p className={`text-xs ${isLeader ? 'text-emerald-300' : 'text-gray-500'}`}>
            Xếp hạng #{rank}/{totalBanks}
          </p>
        </div>
        <div className={`text-2xl font-bold ${
          stats.positive_pct >= stats.negative_pct
            ? 'text-emerald-400'
            : 'text-red-400'
        }`}>
          {stats.positive_pct.toFixed(1)}%
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="bg-black/20 rounded p-2">
          <p className="text-gray-400">Tích cực</p>
          <p className="font-bold text-emerald-400">{stats.positive}</p>
        </div>
        <div className="bg-black/20 rounded p-2">
          <p className="text-gray-400">Tiêu cực</p>
          <p className="font-bold text-red-400">{stats.negative}</p>
        </div>
        <div className="bg-black/20 rounded p-2">
          <p className="text-gray-400">Tin cậy</p>
          <p className="font-bold text-blue-400">{(stats.average_confidence * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Sentiment bar */}
      <div className="mt-3 space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 flex-1">Phân bố</span>
          <span className="text-xs text-white font-bold">{stats.total_comments}</span>
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
    </motion.div>
  );
}

export default function BankComparison({ analyses }) {
  const [viewMode, setViewMode] = useState('cards');
  const [sortBy, setSortBy] = useState('positive');

  const banksData = useMemo(() => {
    return analyses.map(a => ({
      bank: a.bank,
      data: a,
      positive: a.summary.positive_pct,
      negative: a.summary.negative_pct,
      neutral: a.summary.neutral_pct,
      confidence: a.summary.average_confidence * 100,
      total: a.summary.total_comments,
    }));
  }, [analyses]);

  const sortedBanks = useMemo(() => {
    const copy = [...banksData];
    if (sortBy === 'positive') {
      copy.sort((a, b) => b.positive - a.positive);
    } else if (sortBy === 'negative') {
      copy.sort((a, b) => a.negative - b.negative);
    } else if (sortBy === 'confidence') {
      copy.sort((a, b) => b.confidence - a.confidence);
    }
    return copy;
  }, [banksData, sortBy]);

  const chartData = useMemo(() => {
    return sortedBanks.map(b => ({
      bank: b.bank,
      'Tích cực': b.positive,
      'Tiêu cực': b.negative,
      'Trung lập': b.neutral,
    }));
  }, [sortedBanks]);

  const radarData = useMemo(() => {
    return sortedBanks.map(b => ({
      bank: b.bank.slice(0, 8),
      'Tích cực': b.positive,
      'Tin cậy': b.confidence / 100 * 100,
      'Bình luận': (b.total / Math.max(...sortedBanks.map(x => x.total))) * 100,
    }));
  }, [sortedBanks]);

  const insights = useMemo(() => {
    if (sortedBanks.length === 0) return { leader: null, worrying: null, balanced: null };

    const leader = sortedBanks[0];
    const worrying = [...sortedBanks].sort((a, b) => b.negative - a.negative)[0];
    const balanced = [...sortedBanks].sort((a, b) => 
      Math.abs(50 - a.positive) - Math.abs(50 - b.positive)
    )[0];

    return { leader, worrying, balanced };
  }, [sortedBanks]);

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 size={18} className="text-blue-400" />
              So sánh {sortedBanks.length} Ngân hàng
            </h2>
            <p className="text-xs text-gray-400 mt-1">Xếp hạng theo sentiment</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1.5 text-xs bg-black/25 border border-white/15 rounded-lg text-white outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="positive">😊 Xếp hạng: Tích cực</option>
              <option value="negative">😤 Xếp hạng: Tiêu cực</option>
              <option value="confidence">🎯 Xếp hạng: Tin cậy</option>
            </select>
          </div>
        </div>
      </div>

      {/* Quick Insights */}
      {insights.leader && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Leader */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <Award size={16} className="text-yellow-400" />
              <p className="text-xs font-semibold text-emerald-300">Dẫn đầu</p>
            </div>
            <p className="font-bold text-white">{insights.leader.bank}</p>
            <p className="text-sm text-emerald-300 mt-1">{insights.leader.positive.toFixed(1)}% tích cực</p>
          </motion.div>

          {/* Worrying */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-red-500/20 to-rose-500/20 border border-red-500/30 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle size={16} className="text-red-400" />
              <p className="text-xs font-semibold text-red-300">Cảnh báo</p>
            </div>
            <p className="font-bold text-white">{insights.worrying.bank}</p>
            <p className="text-sm text-red-300 mt-1">{insights.worrying.negative.toFixed(1)}% tiêu cực</p>
          </motion.div>

          {/* Balanced */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <Zap size={16} className="text-blue-400" />
              <p className="text-xs font-semibold text-blue-300">Cân bằng</p>
            </div>
            <p className="font-bold text-white">{insights.balanced.bank}</p>
            <p className="text-sm text-blue-300 mt-1">
              {Math.abs(insights.balanced.positive - insights.balanced.negative).toFixed(1)}% chênh lệch
            </p>
          </motion.div>
        </div>
      )}

      {/* Bank Cards */}
      <div>
        <p className="text-sm font-semibold text-gray-300 mb-3">Xếp hạng ngân hàng</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedBanks.map((bank, idx) => (
            <BankCard
              key={bank.bank}
              bank={bank.bank}
              data={bank.data}
              rank={idx + 1}
              totalBanks={sortedBanks.length}
            />
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="space-y-4">
        {/* Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 border border-white/10 rounded-xl p-6"
        >
          <h3 className="font-semibold text-white text-sm mb-4">Phân bố Sentiment theo Ngân hàng</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
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
          <h3 className="font-semibold text-white text-sm mb-4">Biểu đồ Radar - So sánh Toàn diện</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="bank" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <PolarRadiusAxis tick={{ fill: '#9ca3af', fontSize: 10 }} />
              <Radar name="Tích cực" dataKey="Tích cực" stroke="#10b981" fill="#10b981" fillOpacity={0.25} />
              <Radar name="Tin cậy" dataKey="Tin cậy" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Comparative Insights */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4">Phân tích So sánh</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <TrendingUp size={16} className="text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold">Khoảng cách lớn nhất</p>
              <p className="text-gray-400 text-xs mt-0.5">
                {sortedBanks[0]?.bank} dẫn trước với {(
                  sortedBanks[0]?.positive - 
                  [...sortedBanks].sort((a, b) => a.positive - b.positive)[0]?.positive
                ).toFixed(1)}% so với ngân hàng yếu nhất
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <AlertCircle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold">Ngân hàng cần chú ý</p>
              <p className="text-gray-400 text-xs mt-0.5">
                {insights.worrying?.bank} có tỷ lệ tiêu cực cao nhất ({insights.worrying?.negative.toFixed(1)}%)
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Zap size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold">Số lượng bình luận</p>
              <p className="text-gray-400 text-xs mt-0.5">
                Tổng cộng {sortedBanks.reduce((sum, b) => sum + b.total, 0).toLocaleString()} bình luận từ {sortedBanks.length} ngân hàng
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
