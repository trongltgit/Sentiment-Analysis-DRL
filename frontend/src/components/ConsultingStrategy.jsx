// ConsultingStrategy.jsx — AI-Powered Consulting Strategy
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, Shield, Target, AlertCircle, Lightbulb, Clock,
  CheckCircle, AlertTriangle, Activity, Zap
} from 'lucide-react';

const STRATEGY_TEMPLATES = {
  highPositive: {
    title: '📈 Chiến lược Tối ưu hóa',
    color: 'emerald',
    description: 'Tích cực cao: Tập trung vào giữ chân khách hàng',
    actions: [
      {
        title: 'Mở rộng thị trường',
        description: 'Tính cảm xúc tích cực cao cho phép mở rộng dịch vụ mới',
        priority: 'high',
        timeline: '1-2 tháng',
        impact: 'Tăng doanh thu 15-20%'
      },
      {
        title: 'Chương trình Khách hàng thân thiết',
        description: 'Khuyến khích tái khách mua với chương trình độc quyền',
        priority: 'high',
        timeline: 'Ngay lập tức',
        impact: 'Tăng tỷ lệ giữ chân 25%'
      },
      {
        title: 'Tiếp thị qua Word-of-mouth',
        description: 'Khách hàng hài lòng là đại sứ thương hiệu tốt nhất',
        priority: 'medium',
        timeline: 'Liên tục',
        impact: 'Giảm chi phí quảng cáo 20%'
      }
    ]
  },
  highNegative: {
    title: '⚠️ Chiến lược Khẩn cấp',
    color: 'red',
    description: 'Tiêu cực cao: Cần hành động ngay lập tức',
    actions: [
      {
        title: 'Điều tra các vấn đề chính',
        description: 'Xác định nguyên nhân gốc rễ của sự không hài lòng',
        priority: 'high',
        timeline: '3-5 ngày',
        impact: 'Ngăn chặn mất khách hàng'
      },
      {
        title: 'Kế hoạch cải thiện dịch vụ',
        description: 'Đưa ra các giải pháp cụ thể và lộ trình cải thiện',
        priority: 'high',
        timeline: 'Tuần này',
        impact: 'Phục hồi 30-40% khách hàng'
      },
      {
        title: 'Liên hệ trực tiếp với khách hàng',
        description: 'Ghi nhớ các khách hàng chủ chốt và thể hiện cam kết',
        priority: 'high',
        timeline: 'Trong 48h',
        impact: 'Giảm rủi ro mất khách hàng'
      },
      {
        title: 'Chiến dịch quảng cáo tái định hướng',
        description: 'Sử dụng khuyến nghị để chiếm lại niềm tin',
        priority: 'medium',
        timeline: '2-3 tuần',
        impact: 'Phục hồi danh tiếng'
      }
    ]
  },
  balanced: {
    title: '⚖️ Chiến lược Cân bằng',
    color: 'blue',
    description: 'Tích cực và tiêu cực cân bằng: Tối ưu hóa từng phần',
    actions: [
      {
        title: 'Phân tích chi tiết các khiếu nại',
        description: 'Hiểu rõ những điểm yếu và cơ hội cải thiện',
        priority: 'high',
        timeline: '1 tuần',
        impact: 'Xác định 3-5 lĩnh vực cải thiện'
      },
      {
        title: 'Tăng cường tiêu điểm tích cực',
        description: 'Khuếch đại những gì đang làm tốt',
        priority: 'high',
        timeline: 'Liên tục',
        impact: 'Tăng tổng thể tích cực 10-15%'
      },
      {
        title: 'Lập lịch cải thiệm',
        description: 'Đặt ra các mục tiêu cụ thể để giải quyết vấn đề',
        priority: 'medium',
        timeline: '30-60 ngày',
        impact: 'Giảm tiêu cực 20-30%'
      }
    ]
  }
};

function getStrategyType(stats) {
  const posPct = stats.positive_pct;
  const negPct = stats.negative_pct;
  
  if (posPct >= 60 && negPct <= 15) return 'highPositive';
  if (negPct >= 50 && posPct <= 20) return 'highNegative';
  return 'balanced';
}

function ActionCard({ action, index }) {
  const priorityColor = {
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
      className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <h4 className="font-semibold text-white text-sm">{action.title}</h4>
          <p className="text-xs text-gray-400 mt-1">{action.description}</p>
        </div>
        <div className={`px-2 py-1 rounded text-xs font-semibold border ${priorityColor[action.priority]} whitespace-nowrap`}>
          {priorityLabel[action.priority]}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <div className="flex items-center gap-1 text-gray-400">
          <Clock size={12} />
          {action.timeline}
        </div>
        <div className="flex items-center gap-1 text-emerald-400">
          <TrendingUp size={12} />
          {action.impact}
        </div>
      </div>
    </motion.div>
  );
}

function RiskAssessment({ stats }) {
  const risks = [];
  const opportunities = [];

  if (stats.negative_pct > 40) {
    risks.push({
      title: 'Mất khách hàng cao',
      level: 'critical',
      description: 'Tỷ lệ tiêu cực vượt 40% đe dọa chuyển đổi'
    });
  }

  if (stats.positive_pct < 30) {
    risks.push({
      title: 'Thiếu tâm điểm tích cực',
      level: 'high',
      description: 'Không có lợi thế cạnh tranh rõ ràng'
    });
  }

  if (stats.average_confidence < 0.65) {
    risks.push({
      title: 'Kết quả không đáng tin cậy',
      level: 'medium',
      description: 'Có thể cần thu thập thêm phản hồi'
    });
  }

  if (stats.positive_pct > 50) {
    opportunities.push({
      title: 'Cơ hội lãnh đạo thị trường',
      level: 'high',
      description: 'Dùng lợi thế tích cực để mở rộng'
    });
  }

  if (stats.positive_pct - stats.negative_pct > 30) {
    opportunities.push({
      title: 'Mạnh mẽ so với đối thủ',
      level: 'high',
      description: 'Khoảng cách lớn: sử dụng trong tiếp thị'
    });
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Risks */}
      <div className="space-y-3">
        <h3 className="font-semibold text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle size={16} /> Rủi ro
        </h3>
        {risks.length > 0 ? (
          risks.map((risk, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-500/10 border border-red-500/20 rounded-lg p-3"
            >
              <p className="font-semibold text-red-300 text-xs">{risk.title}</p>
              <p className="text-gray-400 text-xs mt-1">{risk.description}</p>
            </motion.div>
          ))
        ) : (
          <p className="text-gray-500 text-xs">Không có rủi ro đáng kể 😊</p>
        )}
      </div>

      {/* Opportunities */}
      <div className="space-y-3">
        <h3 className="font-semibold text-emerald-400 text-sm flex items-center gap-2">
          <Zap size={16} /> Cơ hội
        </h3>
        {opportunities.length > 0 ? (
          opportunities.map((opp, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3"
            >
              <p className="font-semibold text-emerald-300 text-xs">{opp.title}</p>
              <p className="text-gray-400 text-xs mt-1">{opp.description}</p>
            </motion.div>
          ))
        ) : (
          <p className="text-gray-500 text-xs">Không có cơ hội lớn hiện tại</p>
        )}
      </div>
    </div>
  );
}

export default function ConsultingStrategy({ data, bank }) {
  const stats = data.summary;
  const strategyType = getStrategyType(stats);
  const strategy = STRATEGY_TEMPLATES[strategyType];

  const scoreColor = {
    emerald: 'from-emerald-600 to-teal-600',
    red: 'from-red-600 to-rose-600',
    blue: 'from-blue-600 to-cyan-600',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`bg-gradient-to-r ${scoreColor[strategy.color]} bg-opacity-20 border border-${strategy.color}-500/30 rounded-xl p-6`}
      >
        <div className="flex items-start gap-4">
          <div className="text-4xl">{strategy.title.charAt(0)}</div>
          <div>
            <h2 className="text-xl font-bold text-white">{strategy.title}</h2>
            <p className="text-sm text-gray-300 mt-1">{strategy.description}</p>
          </div>
        </div>
      </motion.div>

      {/* Risk Assessment */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
          <AlertCircle size={16} className="text-yellow-400" />
          Đánh giá Rủi ro & Cơ hội
        </h3>
        <RiskAssessment stats={stats} />
      </div>

      {/* Action Items */}
      <div className="space-y-3">
        <h3 className="font-semibold text-white text-sm flex items-center gap-2">
          <CheckCircle size={16} className="text-emerald-400" />
          Hành động khuyến nghị
        </h3>
        {strategy.actions.map((action, idx) => (
          <ActionCard key={idx} action={action} index={idx} />
        ))}
      </div>

      {/* KPI Targets */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
          <Target size={16} className="text-blue-400" />
          Mục tiêu KPI (90 ngày)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { label: 'Tăng Tích cực', target: `+${Math.ceil(stats.positive_pct * 0.15)}%`, color: 'emerald' },
            { label: 'Giảm Tiêu cực', target: `-${Math.ceil(stats.negative_pct * 0.25)}%`, color: 'red' },
            { label: 'Tăng Độ tin cậy', target: '+15%', color: 'blue' },
            { label: 'Tăng Khách hàng', target: '+20%', color: 'purple' },
          ].map((kpi, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`bg-${kpi.color}-500/10 border border-${kpi.color}-500/20 rounded-lg p-4 text-center`}
            >
              <p className="text-xs text-gray-400">{kpi.label}</p>
              <p className={`text-lg font-bold text-${kpi.color}-400 mt-1`}>{kpi.target}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Next Steps */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
          <Activity size={16} className="text-cyan-400" />
          Bước tiếp theo
        </h3>
        <ol className="space-y-3">
          {[
            'Xem chi tiết các bình luận tiêu cực để hiểu vấn đề',
            'Lập kế hoạch hành động chi tiết cho mỗi vấn đề',
            'Gán trách nhiệm và đặt thời hạn',
            'Theo dõi tiến độ hàng tuần',
            'Phân tích lại sau 30 ngày để đánh giá cải thiện'
          ].map((step, i) => (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex gap-3 text-sm"
            >
              <span className="font-bold text-emerald-400 shrink-0">{i + 1}.</span>
              <span className="text-gray-300">{step}</span>
            </motion.li>
          ))}
        </ol>
      </div>
    </div>
  );
}
