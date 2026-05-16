// ConsultingStrategy.jsx - Phiên bản nâng cao với phân tích chuyên sâu dựa trên dữ liệu
// Cung cấp chiến lược cụ thể, có bằng chứng từ bình luận thực tế
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  Shield,
  Target,
  AlertCircle,
  Lightbulb,
  Clock,
  CheckCircle,
  AlertTriangle,
  Activity,
  Zap,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Users,
  RefreshCw,
} from 'lucide-react';

// Advanced analysis: Deep-dive strategy based on sentiment patterns
function AdvancedStrategyAnalyzer({ stats, allBankComments = {} }) {
  // Analyze patterns across all banks
  const bankAnalysis = useMemo(() => {
    const analysis = {};
    
    Object.entries(allBankComments).forEach(([bankName, comments]) => {
      if (!Array.isArray(comments)) return;
      
      const positiveComments = comments.filter(c => c.sentiment === 'positive');
      const negativeComments = comments.filter(c => c.sentiment === 'negative');
      const neutralComments = comments.filter(c => c.sentiment === 'neutral');

      // Extract keywords from comments
      const positiveKeywords = {};
      const negativeKeywords = {};

      positiveComments.forEach((c) => {
        (c.keywords || []).forEach((kw) => {
          positiveKeywords[kw] = (positiveKeywords[kw] || 0) + 1;
        });
      });

      negativeComments.forEach((c) => {
        (c.keywords || []).forEach((kw) => {
          negativeKeywords[kw] = (negativeKeywords[kw] || 0) + 1;
        });
      });

      analysis[bankName] = {
        total: comments.length,
        positiveCount: positiveComments.length,
        negativeCount: negativeComments.length,
        neutralCount: neutralComments.length,
        positivePercent: (positiveComments.length / comments.length) * 100,
        negativePercent: (negativeComments.length / comments.length) * 100,
        topPositiveKeywords: Object.entries(positiveKeywords)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([kw]) => kw),
        topNegativeKeywords: Object.entries(negativeKeywords)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([kw]) => kw),
        topPositiveComments: positiveComments.slice(0, 3),
        topNegativeComments: negativeComments.slice(0, 3),
      };
    });

    return analysis;
  }, [allBankComments]);

  // Determine overall market position
  const marketAnalysis = useMemo(() => {
    const bankList = Object.values(bankAnalysis);
    if (bankList.length === 0) return null;

    const avgPositive = bankList.reduce((sum, b) => sum + b.positivePercent, 0) / bankList.length;
    const avgNegative = bankList.reduce((sum, b) => sum + b.negativePercent, 0) / bankList.length;

    return {
      marketAvgPositive: avgPositive,
      marketAvgNegative: avgNegative,
      bestPerformer: bankList.reduce((best, current) =>
        current.positivePercent > best.positivePercent ? current : best
      ),
      worstPerformer: bankList.reduce((worst, current) =>
        current.negativePercent > worst.negativePercent ? current : worst
      ),
    };
  }, [bankAnalysis]);

  return { bankAnalysis, marketAnalysis };
}

// Risk Assessment with real evidence
function RiskAssessment({ stats, comments, bankAnalysis }) {
  const risks = [];
  const opportunities = [];

  // Analyze risks based on actual negative comments
  if (stats.negative_pct > 40) {
    risks.push({
      level: 'high',
      title: 'Tiêu cực cao',
      description: `${stats.negative_pct.toFixed(1)}% bình luận là tiêu cực - cảnh báo về sự hài lòng khách hàng`,
      evidence: comments?.negative?.[0],
    });
  }

  if (stats.positive_pct > 60) {
    opportunities.push({
      level: 'high',
      title: 'Lợi thế cạnh tranh',
      description: `${stats.positive_pct.toFixed(1)}% tích cực cao - có thể khai thác thị trường`,
      evidence: comments?.positive?.[0],
    });
  }

  if (stats.negative_pct > 20 && stats.negative_pct < 40) {
    risks.push({
      level: 'medium',
      title: 'Vấn đề cơ bản',
      description: 'Có những vấn đề cần giải quyết để tăng tỷ lệ tích cực',
      evidence: comments?.negative?.[0],
    });
  }

  return { risks, opportunities };
}

// Action Card with actual comment evidence
function ActionCard({ action, index, comments, evidenceComments }) {
  const [expanded, setExpanded] = useState(false);

  const priorityStyle = {
    high: 'bg-red-500/20 text-red-300 border-red-500/30',
    medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  };

  const priorityLabel = {
    high: '🔴 Cao',
    medium: '🟡 Trung bình',
    low: '🟢 Thấp',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white/5 border border-white/10 rounded-xl overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 cursor-pointer hover:bg-white/10 transition" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="font-semibold text-white text-sm">{action.title}</h4>
              <span className={`px-2 py-1 rounded text-xs font-semibold whitespace-nowrap ${priorityStyle[action.priority]}`}>
                {priorityLabel[action.priority]}
              </span>
            </div>
            <p className="text-xs text-gray-400">{action.description}</p>
          </div>
          <div className="text-gray-400">
            {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/10 bg-black/20 p-4 space-y-3"
          >
            {/* Timeline and Impact */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-yellow-400" />
                <div>
                  <p className="text-xs text-gray-500">Timeline</p>
                  <p className="text-white font-semibold">{action.timeline}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Target size={16} className="text-emerald-400" />
                <div>
                  <p className="text-xs text-gray-500">Impact</p>
                  <p className="text-white font-semibold">{action.impact}</p>
                </div>
              </div>
            </div>

            {/* Evidence from Comments */}
            {evidenceComments && evidenceComments.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/10">
                <p className="text-xs font-semibold text-gray-300 mb-2 flex items-center gap-1">
                  <MessageSquare size={14} />
                  Bằng chứng từ bình luận thực tế
                </p>
                <div className="space-y-2">
                  {evidenceComments.slice(0, 2).map((comment, i) => (
                    <div
                      key={i}
                      className="p-2 bg-white/5 border border-white/10 rounded text-xs text-gray-300 italic"
                    >
                      "{(comment.text || comment.cleaned_text || '').slice(0, 100)}..."
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Main Export
export default function ConsultingStrategy({ data = {}, bank = '', allBankData = {} }) {
  const stats = data.summary || {};
  const comments = data.comments || {};
  const allBankComments = data.allBankComments || allBankData;

  // Run advanced analysis
  const { bankAnalysis, marketAnalysis } = AdvancedStrategyAnalyzer({ stats, allBankComments });
  const currentBankAnalysis = bankAnalysis[bank] || {};
  const { risks, opportunities } = RiskAssessment({ stats, comments, bankAnalysis });

  // Determine strategy type based on data
  const getStrategyType = () => {
    const { positive_pct: pos = 0, negative_pct: neg = 0 } = stats;
    if (pos >= 60 && neg <= 15) return 'highPositive';
    if (neg >= 50 && pos <= 20) return 'highNegative';
    return 'balanced';
  };

  const strategyType = getStrategyType();

  // Generate actions based on actual data
  const generateActions = () => {
    const { positive_pct: pos = 0, negative_pct: neg = 0 } = stats;
    const actions = [];

    // High Positive Strategy
    if (pos >= 60 && neg <= 15) {
      actions.push(
        {
          title: '🚀 Mở rộng thị trường mới',
          description: `Dựa trên ${pos.toFixed(1)}% bình luận tích cực, khách hàng sẵn sàng cho sản phẩm mới`,
          priority: 'high',
          timeline: '1-2 tháng',
          impact: 'Tăng doanh thu 15-20%',
          evidenceComments: comments?.positive || [],
        },
        {
          title: '💎 Chương trình khách hàng VIP',
          description: 'Khai thác nhóm khách hàng hài lòng cao với các ưu đãi độc quyền',
          priority: 'high',
          timeline: 'Ngay lập tức',
          impact: 'Giữ chân 95% khách hàng',
          evidenceComments: comments?.positive || [],
        },
        {
          title: '📣 Marketing từ khách hàng',
          description: 'Khách hàng hài lòng là công cụ quảng cáo tốt nhất - khuyến khích review & referral',
          priority: 'medium',
          timeline: 'Liên tục',
          impact: 'Giảm chi phí quảng cáo 20-30%',
          evidenceComments: comments?.positive || [],
        }
      );
    }
    // High Negative Strategy
    else if (neg >= 50 && pos <= 20) {
      actions.push(
        {
          title: '🚨 Điều tra nguyên nhân gốc rễ',
          description: `${neg.toFixed(1)}% bình luận tiêu cực cho thấy các vấn đề cơ bản cần giải quyết ngay`,
          priority: 'high',
          timeline: '3-5 ngày',
          impact: 'Ngăn chặn mất thêm khách hàng',
          evidenceComments: comments?.negative || [],
        },
        {
          title: '✅ Kế hoạch cải thiện dịch vụ',
          description: 'Phân tích chi tiết từ bình luận tiêu cực để xác định 3-5 vấn đề chính',
          priority: 'high',
          timeline: '1-2 tuần',
          impact: 'Phục hồi 30-40% khách hàng không hài lòng',
          evidenceComments: comments?.negative || [],
        },
        {
          title: '📞 Liên hệ trực tiếp khách hàng',
          description: 'Ưu tiên xử lý các khiếu nại từ bình luận tiêu cực - thể hiện cam kết cải thiện',
          priority: 'high',
          timeline: '48 giờ',
          impact: 'Giảm nguy cơ mất khách hàng lâu dài',
          evidenceComments: comments?.negative || [],
        },
        {
          title: '🔄 Truyền thông về cải tiến',
          description: 'Cập nhật công khai về các biện pháp khắc phục được thực hiện',
          priority: 'medium',
          timeline: '2-3 tuần',
          impact: 'Khôi phục niềm tin khách hàng',
          evidenceComments: comments?.neutral || [],
        }
      );
    }
    // Balanced Strategy
    else {
      actions.push(
        {
          title: '📊 Phân tích chi tiết các vấn đề',
          description: `Mặc dù có ${pos.toFixed(1)}% tích cực, nhưng ${neg.toFixed(1)}% tiêu cực cần được giải quyết`,
          priority: 'high',
          timeline: '1 tuần',
          impact: 'Xác định 3-5 lĩnh vực cải thiện',
          evidenceComments: comments?.negative || [],
        },
        {
          title: '⭐ Khuếch đại điểm mạnh',
          description: 'Tăng cường những điểm khách hàng đánh giá tích cực',
          priority: 'high',
          timeline: 'Liên tục',
          impact: 'Nâng tỷ lệ tích cực từ 50% lên 70%',
          evidenceComments: comments?.positive || [],
        },
        {
          title: '🛠️ Lộ trình cải thiện 60 ngày',
          description: 'Đặt mục tiêu cụ thể dựa trên vấn đề phát hiện từ bình luận',
          priority: 'medium',
          timeline: '30-60 ngày',
          impact: 'Giảm tiêu cực 20-30%',
          evidenceComments: comments?.negative || [],
        }
      );
    }

    return actions;
  };

  const actions = generateActions();

  const strategyHeaders = {
    highPositive: {
      title: '📈 Chiến lược tối ưu hóa & mở rộng',
      subtitle: 'Tình hình tích cực cao - tập trung vào phát triển',
      color: 'emerald',
      gradient: 'from-emerald-600 to-teal-600',
    },
    highNegative: {
      title: '⚠️ Chiến lược khẩn cấp - Khắc phục sự cố',
      subtitle: 'Tiêu cực cao - cần hành động ngay lập tức',
      color: 'red',
      gradient: 'from-red-600 to-rose-600',
    },
    balanced: {
      title: '⚖️ Chiến lược cân bằng & tối ưu hóa',
      subtitle: 'Sentiment cân bằng - cân bằng giữa khuếch đại sức mạnh và khắc phục yếu điểm',
      color: 'blue',
      gradient: 'from-blue-600 to-cyan-600',
    },
  };

  const strategy = strategyHeaders[strategyType];
  const colorMap = {
    emerald: 'border-emerald-500/30',
    red: 'border-red-500/30',
    blue: 'border-blue-500/30',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`bg-gradient-to-r ${strategy.gradient} bg-opacity-20 border ${colorMap[strategy.color]} rounded-xl p-6`}
      >
        <h2 className="text-2xl font-bold text-white">{strategy.title}</h2>
        <p className="text-sm text-gray-200 mt-2">{strategy.subtitle}</p>
        <div className="flex flex-wrap gap-3 mt-4 text-xs">
          <span className="px-3 py-1 bg-white/10 rounded-full text-emerald-200">
            😊 {stats.positive || 0} tích cực ({(stats.positive_pct || 0).toFixed(1)}%)
          </span>
          <span className="px-3 py-1 bg-white/10 rounded-full text-red-200">
            😤 {stats.negative || 0} tiêu cực ({(stats.negative_pct || 0).toFixed(1)}%)
          </span>
          <span className="px-3 py-1 bg-white/10 rounded-full text-gray-200">
            😐 {stats.neutral || 0} trung lập ({(stats.neutral_pct || 0).toFixed(1)}%)
          </span>
          <span className="px-3 py-1 bg-white/10 rounded-full text-blue-200">
            Cộng: {stats.total || 0} bình luận
          </span>
        </div>
      </motion.div>

      {/* Risk & Opportunity Assessment */}
      {(risks.length > 0 || opportunities.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {opportunities.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5"
            >
              <h3 className="font-bold text-emerald-400 mb-3 flex items-center gap-2">
                <Lightbulb size={18} />
                💡 Cơ hội
              </h3>
              <div className="space-y-2">
                {opportunities.map((opp, i) => (
                  <div key={i} className="text-sm text-emerald-200">
                    <p className="font-semibold">{opp.title}</p>
                    <p className="text-xs text-emerald-300/70">{opp.description}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {risks.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-500/10 border border-red-500/30 rounded-xl p-5"
            >
              <h3 className="font-bold text-red-400 mb-3 flex items-center gap-2">
                <AlertTriangle size={18} />
                ⚠️ Rủi ro
              </h3>
              <div className="space-y-2">
                {risks.map((risk, i) => (
                  <div key={i} className="text-sm text-red-200">
                    <p className="font-semibold">{risk.title}</p>
                    <p className="text-xs text-red-300/70">{risk.description}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Key Insights from Data */}
      {currentBankAnalysis.topPositiveKeywords && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-6">
          <h3 className="font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 size={18} className="text-yellow-400" />
            📊 Từ khóa nổi bật từ dữ liệu
          </h3>
          <div className="space-y-4">
            {currentBankAnalysis.topPositiveKeywords && (
              <div>
                <p className="text-sm text-emerald-400 font-semibold mb-2">😊 Điểm mạnh thường được nhắc đến:</p>
                <div className="flex flex-wrap gap-2">
                  {currentBankAnalysis.topPositiveKeywords.map((kw, i) => (
                    <span key={i} className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-full text-xs font-semibold">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {currentBankAnalysis.topNegativeKeywords && (
              <div>
                <p className="text-sm text-red-400 font-semibold mb-2">😤 Vấn đề hay được phản ánh:</p>
                <div className="flex flex-wrap gap-2">
                  {currentBankAnalysis.topNegativeKeywords.map((kw, i) => (
                    <span key={i} className="px-3 py-1 bg-red-500/10 border border-red-500/20 text-red-300 rounded-full text-xs font-semibold">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recommended Actions */}
      <div className="space-y-3">
        <h3 className="font-bold text-white text-lg flex items-center gap-2">
          <CheckCircle size={20} className="text-emerald-400" />
          🎯 Hành động khuyến nghị (dựa trên phân tích dữ liệu)
        </h3>
        {actions.map((action, idx) => (
          <ActionCard
            key={idx}
            action={action}
            index={idx}
            comments={comments}
            evidenceComments={action.evidenceComments}
          />
        ))}
      </div>

      {/* KPI Targets */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-bold text-white mb-4 flex items-center gap-2">
          <Target size={18} className="text-blue-400" />
          🎯 Mục tiêu KPI (90 ngày)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: 'Tăng Tích cực',
              target: `+${Math.ceil((stats.positive_pct || 0) * 0.15).toFixed(0)}%`,
              color: 'emerald',
            },
            {
              label: 'Giảm Tiêu cực',
              target: `-${Math.ceil((stats.negative_pct || 0) * 0.25).toFixed(0)}%`,
              color: 'red',
            },
            {
              label: 'Hài lòng KH',
              target: '+25%',
              color: 'blue',
            },
            {
              label: 'Tỷ lệ giữ chân',
              target: '+15%',
              color: 'purple',
            },
          ].map((kpi, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`bg-${kpi.color}-500/10 border border-${kpi.color}-500/20 rounded-lg p-4 text-center`}
            >
              <p className="text-xs text-gray-400">{kpi.label}</p>
              <p className={`text-lg font-bold text-${kpi.color}-400 mt-2`}>{kpi.target}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Implementation Steps */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-bold text-white mb-4 flex items-center gap-2">
          <Activity size={18} className="text-cyan-400" />
          📋 Các bước tiếp theo
        </h3>
        <ol className="space-y-3">
          {[
            'Xem chi tiết tất cả bình luận trong tab "Bình luận chi tiết" → xác nhận các vấn đề tìm thấy',
            'Họp để lập kế hoạch hành động cụ thể cho mỗi hành động được đề xuất',
            'Gán trách nhiệm rõ ràng cho mỗi thành viên nhóm với deadline cụ thể',
            'Theo dõi tiến độ hàng tuần và điều chỉnh kế hoạch nếu cần',
            'Chạy lại phân tích sau 30 ngày để đo lường tiến bộ và hiệu ứng của các hành động',
          ].map((step, i) => (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex gap-3"
            >
              <span className="font-bold text-emerald-400 shrink-0">{i + 1}.</span>
              <span className="text-sm text-gray-300">{step}</span>
            </motion.li>
          ))}
        </ol>
      </div>

      {/* Data-Driven Footer */}
      <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-4">
        <p className="text-xs text-cyan-300 text-center">
          💡 <strong>Chú ý:</strong> Tất cả khuyến nghị trên dựa trên phân tích thực tế từ{' '}
          {stats.total || 0} bình luận được thu thập. Vui lòng xem chi tiết từng bình luận
          trong tab "Bình luận chi tiết" để xác nhận các phát hiện.
        </p>
      </div>
    </div>
  );
}
