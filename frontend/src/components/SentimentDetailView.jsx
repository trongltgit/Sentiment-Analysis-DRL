// SentimentDetailView.jsx — Detailed Sentiment Analysis with Tabs
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, ZapOff, Search } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';

const COLORS = { positive: '#10b981', negative: '#ef4444', neutral: '#6b7280' };

function CommentCard({ comment, idx }) {
  const [expanded, setExpanded] = useState(false);
  const colors = {
    positive: 'border-emerald-500/30 bg-emerald-500/5',
    negative: 'border-red-500/30 bg-red-500/5',
    neutral: 'border-gray-500/30 bg-gray-500/5',
  };
  const confColor = comment.confidence >= 0.85 ? 'text-emerald-400'
    : comment.confidence >= 0.70 ? 'text-blue-400'
    : comment.confidence >= 0.55 ? 'text-yellow-400' : 'text-gray-400';

  const isLong = comment.text?.length > 160;
  const text = isLong && !expanded ? comment.text.slice(0, 160) + '…' : comment.text;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: idx * 0.03 }}
      className={`rounded-xl border p-4 ${colors[comment.sentiment] || colors.neutral}`}
    >
      <p className="text-sm text-gray-200 leading-relaxed font-medium mb-2">{text}</p>

      {isLong && (
        <button onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-400 mb-2 flex items-center gap-0.5 hover:text-blue-300">
          {expanded ? <><ChevronUp size={12} />Thu gọn</> : <><ChevronDown size={12} />Xem thêm</>}
        </button>
      )}

      <div className="flex flex-wrap gap-2 items-center">
        <span className={`text-xs font-bold ${confColor}`}>
          🎯 {(comment.confidence * 100).toFixed(0)}% tin cậy
        </span>
        {comment.keywords?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {comment.keywords.slice(0, 3).map(kw => (
              <span key={kw} className="text-xs px-2 py-0.5 bg-white/10 text-gray-300 rounded-full">
                {kw}
              </span>
            ))}
            {comment.keywords.length > 3 && (
              <span className="text-xs px-2 py-0.5 bg-white/10 text-gray-300 rounded-full">
                +{comment.keywords.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function SentimentDetailView({ data, bank }) {
  const [activeTab, setActiveTab] = useState('distribution');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('all');

  const stats = data.summary;
  const comments = data.comments || {};

  const pieData = useMemo(() => [
    { name: 'Tích cực', value: stats.positive, color: COLORS.positive },
    { name: 'Tiêu cực', value: stats.negative, color: COLORS.negative },
    { name: 'Trung lập', value: stats.neutral, color: COLORS.neutral },
  ].filter(d => d.value > 0), [stats]);

  const confidenceData = useMemo(() => {
    const dist = stats.confidence_distribution || {};
    return Object.entries(dist).map(([range, count]) => ({
      name: range,
      value: count,
    }));
  }, [stats]);

  // Filter comments based on search and sentiment
  const filteredComments = useMemo(() => {
    let result = [];
    
    if (selectedSentiment === 'all') {
      result = [
        ...(comments.positive || []),
        ...(comments.negative || []),
        ...(comments.neutral || []),
      ];
    } else {
      result = comments[selectedSentiment] || [];
    }

    if (searchTerm) {
      result = result.filter(c => 
        c.text.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return result;
  }, [comments, selectedSentiment, searchTerm]);

  const tabConfig = [
    { id: 'distribution', label: 'Phân bố Sentiment', icon: '📊' },
    { id: 'confidence', label: 'Độ tin cậy', icon: '🎯' },
    { id: 'comments', label: 'Bình luận chi tiết', icon: '💬' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Tổng bình luận', value: stats.total_comments, icon: '📝', color: 'text-white' },
          { label: 'Tích cực', value: `${stats.positive_pct.toFixed(1)}%`, icon: '😊', color: 'text-emerald-400' },
          { label: 'Tiêu cực', value: `${stats.negative_pct.toFixed(1)}%`, icon: '😤', color: 'text-red-400' },
          { label: 'Độ tin cậy', value: `${(stats.average_confidence * 100).toFixed(0)}%`, icon: '🎯', color: 'text-blue-400' },
        ].map(k => (
          <motion.div key={k.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/5 border border-white/10 rounded-xl p-4 text-center"
          >
            <div className="text-2xl mb-1">{k.icon}</div>
            <div className={`text-lg font-extrabold ${k.color}`}>{k.value}</div>
            <div className="text-gray-400 text-xs mt-0.5">{k.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10 overflow-x-auto">
        {tabConfig.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-semibold whitespace-nowrap transition border-b-2 ${
              activeTab === tab.id
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {/* Distribution Tab */}
        {activeTab === 'distribution' && (
          <motion.div
            key="distribution"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-4">Biểu đồ Sentiment</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={85} dataKey="value">
                      {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip 
                      formatter={(v) => v}
                      contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Sentiment Cards */}
              <div className="space-y-3">
                {[
                  { label: 'Tích cực', count: stats.positive, pct: stats.positive_pct, color: 'emerald', icon: '😊' },
                  { label: 'Tiêu cực', count: stats.negative, pct: stats.negative_pct, color: 'red', icon: '😤' },
                  { label: 'Trung lập', count: stats.neutral, pct: stats.neutral_pct, color: 'gray', icon: '😐' },
                ].map(item => (
                  <div key={item.label} className={`bg-${item.color}-500/10 border border-${item.color}-500/20 rounded-xl p-4`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-white">{item.icon} {item.label}</span>
                      <span className={`text-lg font-bold text-${item.color}-400`}>{item.pct.toFixed(1)}%</span>
                    </div>
                    <div className="bg-white/5 rounded-full h-2 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.pct}%` }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className={`h-2 bg-${item.color}-500`}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-2">{item.count} bình luận</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Confidence Tab */}
        {activeTab === 'confidence' && (
          <motion.div
            key="confidence"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-white/5 border border-white/10 rounded-xl p-6"
          >
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Phân bố Độ tin cậy</h3>
            {confidenceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={confidenceData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                  <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-center py-8">Không có dữ liệu</p>
            )}
          </motion.div>
        )}

        {/* Comments Tab */}
        {activeTab === 'comments' && (
          <motion.div
            key="comments"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {/* Filters */}
            <div className="space-y-4">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  placeholder="Tìm kiếm bình luận..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-black/25 border border-white/15 rounded-lg text-white text-sm placeholder-gray-500 outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex gap-2 flex-wrap">
                {['all', 'positive', 'negative', 'neutral'].map(sent => {
                  const labels = {
                    all: '📋 Tất cả',
                    positive: '😊 Tích cực',
                    negative: '😤 Tiêu cực',
                    neutral: '😐 Trung lập',
                  };
                  const count = sent === 'all' 
                    ? stats.total_comments
                    : comments[sent]?.length || 0;
                  
                  return (
                    <button key={sent}
                      onClick={() => setSelectedSentiment(sent)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        selectedSentiment === sent
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-white/5 text-gray-400 hover:text-white'
                      }`}
                    >
                      {labels[sent]} ({count})
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Comments List */}
            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
              {filteredComments.length === 0 ? (
                <div className="text-center py-12">
                  <ZapOff size={32} className="text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">Không tìm thấy bình luận</p>
                </div>
              ) : (
                filteredComments.map((comment, idx) => (
                  <CommentCard key={comment.id || idx} comment={comment} idx={idx} />
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
