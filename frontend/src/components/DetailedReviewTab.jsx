// DetailedReviewTab.jsx - Component hiển thị bình luận chi tiết theo ngân hàng + sentiment
// Cho phép người dùng xem và kiểm chứng các bình luận thực tế được phân tích
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronUp,
  Filter,
  Search,
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Clock,
  ThumbsUp,
} from 'lucide-react';

const DetailedReviewTab = ({ bankComments = {}, bankData = {} }) => {
  const [expandedBanks, setExpandedBanks] = useState({});
  const [selectedSentiment, setSelectedSentiment] = useState('all'); // all, positive, negative, neutral
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('recent'); // recent, likes, confidence

  // Normalize and structure data
  const structuredData = useMemo(() => {
    const result = {};
    
    Object.entries(bankComments).forEach(([bankName, comments]) => {
      if (!Array.isArray(comments)) return;
      
      // Group comments by sentiment
      const grouped = {
        positive: [],
        negative: [],
        neutral: [],
      };

      comments.forEach((comment) => {
        const sentiment = comment.sentiment || 'neutral';
        if (grouped[sentiment]) {
          grouped[sentiment].push(comment);
        }
      });

      // Apply sorting
      Object.keys(grouped).forEach((sentiment) => {
        grouped[sentiment].sort((a, b) => {
          if (sortBy === 'recent') {
            return new Date(b.timestamp || 0) - new Date(a.timestamp || 0);
          }
          if (sortBy === 'likes') {
            return (b.likes || 0) - (a.likes || 0);
          }
          if (sortBy === 'confidence') {
            return (b.confidence || 0) - (a.confidence || 0);
          }
          return 0;
        });
      });

      result[bankName] = {
        summary: {
          positive: grouped.positive.length,
          negative: grouped.negative.length,
          neutral: grouped.neutral.length,
          total: comments.length,
        },
        comments: grouped,
        bankStats: bankData[bankName] || {},
      };
    });

    return result;
  }, [bankComments, bankData, sortBy]);

  // Filter comments based on search and sentiment
  const getFilteredComments = (comments) => {
    const allComments = [];
    
    Object.entries(comments).forEach(([sentiment, list]) => {
      if (selectedSentiment !== 'all' && sentiment !== selectedSentiment) {
        return;
      }
      
      list.forEach((comment) => {
        if (
          !searchTerm ||
          (comment.text || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
          (comment.cleaned_text || '').toLowerCase().includes(searchTerm.toLowerCase())
        ) {
          allComments.push({ ...comment, sentiment });
        }
      });
    });

    return allComments;
  };

  const toggleBank = (bankName) => {
    setExpandedBanks((prev) => ({
      ...prev,
      [bankName]: !prev[bankName],
    }));
  };

  const sentimentColor = {
    positive: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      icon: '😊',
      label: 'Tích cực',
    },
    negative: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      text: 'text-red-400',
      icon: '😤',
      label: 'Tiêu cực',
    },
    neutral: {
      bg: 'bg-gray-500/10',
      border: 'border-gray-500/30',
      text: 'text-gray-400',
      icon: '😐',
      label: 'Trung lập',
    },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 border border-white/10 rounded-xl p-6"
      >
        <h2 className="text-2xl font-bold text-white mb-4">
          📋 Bình luận chi tiết theo ngân hàng
        </h2>
        <p className="text-gray-300 text-sm mb-6">
          Xem bình luận thực tế được phân tích, nhóm theo ngân hàng và mức độ tích cực/tiêu cực.
          Tất cả dữ liệu này được sử dụng làm cơ sở cho các khuyến nghị chiến lược.
        </p>

        {/* Filter Controls */}
        <div className="space-y-3">
          {/* Sentiment Filter */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setSelectedSentiment('all')}
              className={`px-4 py-2 rounded-lg font-semibold text-sm transition ${
                selectedSentiment === 'all'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              Tất cả
            </button>
            {Object.entries(sentimentColor).map(([sentiment, config]) => (
              <button
                key={sentiment}
                onClick={() => setSelectedSentiment(sentiment)}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition flex items-center gap-2 ${
                  selectedSentiment === sentiment
                    ? `${config.bg} ${config.text} border ${config.border}`
                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                }`}
              >
                <span>{config.icon}</span>
                {config.label}
                <span className="text-xs">
                  ({Object.values(structuredData).reduce(
                    (sum, bank) => sum + (bank.summary[sentiment] || 0),
                    0
                  )})
                </span>
              </button>
            ))}
          </div>

          {/* Search and Sort */}
          <div className="flex gap-3 flex-col sm:flex-row">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-2.5 text-gray-500" size={18} />
              <input
                type="text"
                placeholder="Tìm kiếm bình luận..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-white/40"
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none"
            >
              <option value="recent">Gần đây nhất</option>
              <option value="likes">Lượt thích cao</option>
              <option value="confidence">Độ tin cậy cao</option>
            </select>
          </div>
        </div>
      </motion.div>

      {/* Banks List */}
      <div className="space-y-3">
        <AnimatePresence>
          {Object.entries(structuredData).map(([bankName, bankData], bankIdx) => {
            const isExpanded = expandedBanks[bankName];
            const filteredComments = getFilteredComments(bankData.comments);
            const stats = bankData.summary;
            
            return (
              <motion.div
                key={bankName}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: bankIdx * 0.1 }}
                className="bg-white/5 border border-white/10 rounded-xl overflow-hidden"
              >
                {/* Bank Header - Expandable */}
                <button
                  onClick={() => toggleBank(bankName)}
                  className="w-full p-4 flex items-center justify-between hover:bg-white/10 transition"
                >
                  <div className="flex-1 text-left">
                    <h3 className="text-lg font-bold text-white">{bankName}</h3>
                    <div className="flex gap-3 mt-2 flex-wrap text-sm">
                      <span className="flex items-center gap-1 px-3 py-1 bg-emerald-500/10 text-emerald-300 rounded-full border border-emerald-500/30">
                        😊 {stats.positive} tích cực
                      </span>
                      <span className="flex items-center gap-1 px-3 py-1 bg-red-500/10 text-red-300 rounded-full border border-red-500/30">
                        😤 {stats.negative} tiêu cực
                      </span>
                      <span className="flex items-center gap-1 px-3 py-1 bg-gray-500/10 text-gray-300 rounded-full border border-gray-500/30">
                        😐 {stats.neutral} trung lập
                      </span>
                      <span className="flex items-center gap-1 px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/30">
                        Cộng: {stats.total}
                      </span>
                    </div>
                  </div>
                  <div className="text-gray-400 ml-4">
                    {isExpanded ? (
                      <ChevronUp size={24} />
                    ) : (
                      <ChevronDown size={24} />
                    )}
                  </div>
                </button>

                {/* Expanded Comments View */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-white/10 bg-black/20"
                    >
                      <div className="p-4 space-y-3">
                        {filteredComments.length === 0 ? (
                          <div className="text-center py-8 text-gray-400">
                            Không tìm thấy bình luận phù hợp
                          </div>
                        ) : (
                          filteredComments.map((comment, idx) => {
                            const sentiment = comment.sentiment || 'neutral';
                            const config = sentimentColor[sentiment];
                            
                            return (
                              <motion.div
                                key={comment.id || idx}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                className={`p-4 rounded-lg border ${config.bg} ${config.border}`}
                              >
                                {/* Comment Header */}
                                <div className="flex items-start justify-between gap-3 mb-3">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className="font-semibold text-cyan-300 text-sm">
                                        {comment.author || 'Ẩn danh'}
                                      </span>
                                      <span className="text-xs text-gray-500">
                                        {comment.timestamp
                                          ? new Date(comment.timestamp).toLocaleDateString('vi-VN')
                                          : 'Không xác định'}
                                      </span>
                                      {comment.likes > 0 && (
                                        <span className="flex items-center gap-1 text-xs text-pink-400">
                                          <ThumbsUp size={12} />
                                          {comment.likes}
                                        </span>
                                      )}
                                    </div>
                                    <span className={`inline-block px-2 py-1 text-xs font-bold rounded ${config.text}`}>
                                      {config.icon} {config.label}
                                    </span>
                                  </div>

                                  {/* Confidence Score */}
                                  <div className="text-right">
                                    <div className="text-xl font-bold text-cyan-400">
                                      {((comment.confidence || 0.5) * 100).toFixed(0)}%
                                    </div>
                                    <div className="text-xs text-gray-500">tin cậy</div>
                                  </div>
                                </div>

                                {/* Comment Text */}
                                <p className="text-gray-200 text-sm leading-relaxed mb-3">
                                  "{comment.cleaned_text || comment.text || ''}"
                                </p>

                                {/* Keywords/Aspects if available */}
                                {comment.keywords && comment.keywords.length > 0 && (
                                  <div className="flex flex-wrap gap-1 text-xs">
                                    {comment.keywords.map((kw, i) => (
                                      <span
                                        key={i}
                                        className="px-2 py-1 bg-white/10 text-gray-300 rounded"
                                      >
                                        {kw}
                                      </span>
                                    ))}
                                  </div>
                                )}

                                {/* Reason if available */}
                                {comment.reason && (
                                  <div className="mt-2 p-2 bg-white/5 rounded text-xs text-gray-400 italic">
                                    Lý do: {comment.reason}
                                  </div>
                                )}
                              </motion.div>
                            );
                          })
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Summary Stats */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 border border-white/10 rounded-xl p-6"
      >
        <h3 className="text-lg font-bold text-white mb-4">📊 Thống kê tổng hợp</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            {
              label: 'Tổng bình luận',
              value: Object.values(structuredData).reduce(
                (sum, bank) => sum + bank.summary.total,
                0
              ),
              icon: MessageSquare,
              color: 'blue',
            },
            {
              label: 'Tích cực',
              value: Object.values(structuredData).reduce(
                (sum, bank) => sum + bank.summary.positive,
                0
              ),
              icon: TrendingUp,
              color: 'emerald',
            },
            {
              label: 'Tiêu cực',
              value: Object.values(structuredData).reduce(
                (sum, bank) => sum + bank.summary.negative,
                0
              ),
              icon: AlertTriangle,
              color: 'red',
            },
            {
              label: 'Tỷ lệ tích cực',
              value: `${(
                (Object.values(structuredData).reduce((sum, bank) => sum + bank.summary.positive, 0) /
                  Math.max(
                    Object.values(structuredData).reduce(
                      (sum, bank) => sum + bank.summary.total,
                      0
                    ),
                    1
                  )) *
                100
              ).toFixed(1)}%`,
              icon: DollarSign,
              color: 'green',
            },
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className={`bg-${stat.color}-500/10 border border-${stat.color}-500/30 rounded-lg p-4 text-center`}
            >
              <stat.icon size={20} className={`text-${stat.color}-400 mx-auto mb-2`} />
              <p className="text-sm text-gray-400">{stat.label}</p>
              <p className={`text-2xl font-bold text-${stat.color}-400 mt-2`}>
                {stat.value}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default DetailedReviewTab;
