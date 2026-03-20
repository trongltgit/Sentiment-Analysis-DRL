import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  ThumbsUp, 
  AlertTriangle, 
  CheckCircle,
  Filter,
  BrainCircuit,
  Sparkles
} from 'lucide-react';

const CommentList = ({ comments }) => {
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('importance');

  const getActionColor = (action) => {
    const colors = {
      prioritize: 'bg-red-500/20 text-red-400 border-red-500/30',
      filter: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      highlight: 'bg-green-500/20 text-green-400 border-green-500/30',
      respond: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      ignore: 'bg-slate-500/20 text-slate-400 border-slate-500/30'
    };
    return colors[action] || colors.ignore;
  };

  const getActionLabel = (action) => {
    const labels = {
      prioritize: 'Ưu tiên cao',
      filter: 'Lọc bỏ',
      highlight: 'Nổi bật',
      respond: 'Cần phản hồi',
      ignore: 'Bỏ qua'
    };
    return labels[action] || action;
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'positive': return <CheckCircle className="text-green-400" size={16} />;
      case 'negative': return <AlertTriangle className="text-red-400" size={16} />;
      default: return <MessageSquare className="text-gray-400" size={16} />;
    }
  };

  const filteredComments = comments.filter(comment => {
    if (filter === 'all') return true;
    if (filter === 'actionable') return comment.requires_action;
    if (filter === 'negative') return comment.sentiment === 'negative';
    if (filter === 'positive') return comment.sentiment === 'positive';
    return comment.drl_action === filter;
  }).sort((a, b) => {
    if (sortBy === 'importance') return b.importance_score - a.importance_score;
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'likes') return (b.likes || 0) - (a.likes || 0);
    return 0;
  });

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 border border-white/10 rounded-2xl p-6"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <MessageSquare className="text-cyan-400" />
          Chi tiết bình luận ({filteredComments.length})
        </h3>
        
        <div className="flex flex-wrap gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="all">Tất cả</option>
            <option value="actionable">Cần xử lý</option>
            <option value="negative">Tiêu cực</option>
            <option value="positive">Tích cực</option>
            <option value="prioritize">Ưu tiên</option>
            <option value="respond">Cần phản hồi</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="importance">Sắp xếp: Mức độ quan trọng</option>
            <option value="confidence">Sắp xếp: Độ tin cậy</option>
            <option value="likes">Sắp xếp: Lượt thích</option>
          </select>
        </div>
      </div>

      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
        <AnimatePresence>
          {filteredComments.map((comment, idx) => (
            <motion.div
              key={comment.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: idx * 0.05 }}
              className={`p-4 rounded-xl border ${
                comment.highlighted 
                  ? 'bg-green-500/10 border-green-500/30' 
                  : 'bg-black/20 border-white/10'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-cyan-400 text-sm">
                      {comment.author || 'Ẩn danh'}
                    </span>
                    <span className="text-gray-500 text-xs">
                      {new Date(comment.timestamp).toLocaleString('vi-VN')}
                    </span>
                    {comment.likes > 0 && (
                      <span className="flex items-center gap-1 text-xs text-pink-400">
                        <ThumbsUp size={12} />
                        {comment.likes}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-gray-200 text-sm leading-relaxed mb-3">
                    {comment.cleaned_text}
                  </p>

                  {/* Aspect Tags */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {Object.entries(comment.aspects || {}).map(([aspect, scores]) => (
                      scores.dominant !== 'neutral' && (
                        <span 
                          key={aspect}
                          className={`text-xs px-2 py-1 rounded-full border ${
                            scores.dominant === 'positive' 
                              ? 'bg-green-500/10 text-green-400 border-green-500/20' 
                              : scores.dominant === 'negative'
                              ? 'bg-red-500/10 text-red-400 border-red-500/20'
                              : 'bg-gray-500/10 text-gray-400 border-gray-500/20'
                          }`}
                        >
                          {aspect}: {scores.dominant}
                        </span>
                      )
                    ))}
                  </div>

                  {/* Emotions */}
                  <div className="flex flex-wrap gap-1 mb-3">
                    {Object.entries(comment.emotions || {})
                      .filter(([_, score]) => score > 0.3)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 3)
                      .map(([emotion, score]) => (
                        <span 
                          key={emotion}
                          className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded"
                        >
                          {emotion}: {(score * 100).toFixed(0)}%
                        </span>
                      ))}
                  </div>

                  {/* AI Action Badge */}
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-3 py-1 rounded-full border flex items-center gap-1 ${getActionColor(comment.drl_action)}`}>
                      <BrainCircuit size={12} />
                      AI: {getActionLabel(comment.drl_action)}
                      <span className="opacity-75">
                        ({(comment.action_confidence * 100).toFixed(0)}%)
                      </span>
                    </span>
                    
                    {comment.requires_action && (
                      <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded-full flex items-center gap-1">
                        <AlertTriangle size={12} />
                        Cần xử lý ngay
                      </span>
                    )}
                  </div>

                  {/* Suggested Response */}
                  {comment.suggested_response && (
                    <div className="mt-3 p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
                      <div className="text-xs text-cyan-400 mb-1 flex items-center gap-1">
                        <Sparkles size={12} />
                        Gợi ý phản hồi từ AI:
                      </div>
                      <p className="text-sm text-cyan-100 italic">
                        "{comment.suggested_response}"
                      </p>
                    </div>
                  )}
                </div>

                {/* Confidence Score */}
                <div className="text-center min-w-[60px]">
                  <div className="text-2xl font-bold text-cyan-400">
                    {(comment.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500">tin cậy</div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default CommentList;