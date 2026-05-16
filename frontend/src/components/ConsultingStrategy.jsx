// ConsultingStrategy.jsx v3.1 — AI Consulting Strategy with Comment Evidence
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, Shield, Target, AlertCircle, Lightbulb,
  Clock, CheckCircle, AlertTriangle, Activity, Zap,
  MessageSquare, ChevronDown, ChevronUp,
} from 'lucide-react';

// ── Strategy templates ────────────────────────────────────────────────────────
const STRATEGY_TEMPLATES = {
  highPositive: {
    title:       '📈 Chiến lược Tối ưu hóa',
    color:       'emerald',
    gradient:    'from-emerald-600 to-teal-600',
    description: 'Tích cực cao: Tập trung vào giữ chân & mở rộng thị trường',
    actions: [
      {
        title:       'Mở rộng thị trường',
        description: 'Sentiment tích cực cao cho phép tự tin triển khai sản phẩm mới',
        priority:    'high',
        timeline:    '1–2 tháng',
        impact:      'Tăng doanh thu 15–20%',
        evidenceGroup: 'positive',
      },
      {
        title:       'Chương trình Khách hàng thân thiết',
        description: 'Khai thác nhóm hài lòng cao với ưu đãi độc quyền',
        priority:    'high',
        timeline:    'Ngay lập tức',
        impact:      'Tăng tỷ lệ giữ chân 25%',
        evidenceGroup: 'positive',
      },
      {
        title:       'Marketing qua Word-of-mouth',
        description: 'Khách hàng hài lòng là đại sứ thương hiệu tốt nhất',
        priority:    'medium',
        timeline:    'Liên tục',
        impact:      'Giảm chi phí quảng cáo 20%',
        evidenceGroup: 'positive',
      },
    ],
  },
  highNegative: {
    title:       '⚠️ Chiến lược Khẩn cấp',
    color:       'red',
    gradient:    'from-red-600 to-rose-600',
    description: 'Tiêu cực cao: Cần hành động khắc phục ngay lập tức',
    actions: [
      {
        title:       'Điều tra nguyên nhân gốc rễ',
        description: 'Phân tích bình luận tiêu cực để xác định vấn đề cụ thể',
        priority:    'high',
        timeline:    '3–5 ngày',
        impact:      'Ngăn chặn mất thêm khách hàng',
        evidenceGroup: 'negative',
      },
      {
        title:       'Kế hoạch cải thiện dịch vụ',
        description: 'Đưa ra giải pháp và lộ trình cải thiện cụ thể từ phản hồi',
        priority:    'high',
        timeline:    'Tuần này',
        impact:      'Phục hồi 30–40% khách hàng',
        evidenceGroup: 'negative',
      },
      {
        title:       'Liên hệ trực tiếp khách hàng bức xúc',
        description: 'Ưu tiên xử lý các khiếu nại nghiêm trọng và thể hiện cam kết',
        priority:    'high',
        timeline:    'Trong 48h',
        impact:      'Giảm nguy cơ mất khách hàng',
        evidenceGroup: 'negative',
      },
      {
        title:       'Chiến dịch tái định hướng niềm tin',
        description: 'Truyền thông chủ động về các cải tiến đã thực hiện',
        priority:    'medium',
        timeline:    '2–3 tuần',
        impact:      'Phục hồi danh tiếng',
        evidenceGroup: 'neutral',
      },
    ],
  },
  balanced: {
    title:       '⚖️ Chiến lược Cân bằng',
    color:       'blue',
    gradient:    'from-blue-600 to-cyan-600',
    description: 'Sentiment cân bằng: Tối ưu điểm mạnh, giải quyết điểm yếu',
    actions: [
      {
        title:       'Phân tích chi tiết khiếu nại',
        description: 'Hiểu rõ từng nhóm vấn đề trong bình luận tiêu cực và trung lập',
        priority:    'high',
        timeline:    '1 tuần',
        impact:      'Xác định 3–5 lĩnh vực cải thiện',
        evidenceGroup: 'negative',
      },
      {
        title:       'Khuếch đại điểm mạnh',
        description: 'Nhân rộng những gì đang làm tốt theo bình luận tích cực',
        priority:    'high',
        timeline:    'Liên tục',
        impact:      'Tăng tổng tích cực thêm 10–15%',
        evidenceGroup: 'positive',
      },
      {
        title:       'Lộ trình cải thiện 60 ngày',
        description: 'Đặt mục tiêu cụ thể dựa trên các vấn đề bình luận trung lập',
        priority:    'medium',
        timeline:    '30–60 ngày',
        impact:      'Giảm tiêu cực 20–30%',
        evidenceGroup: 'neutral',
      },
    ],
  },
};

function getStrategyType(stats) {
  const { positive_pct: pos, negative_pct: neg } = stats;
  if (pos >= 60 && neg <= 15) return 'highPositive';
  if (neg >= 50 && pos <= 20) return 'highNegative';
  return 'balanced';
}

// ── Comment Evidence snippet ──────────────────────────────────────────────────
function CommentEvidence({ comments, group, maxShow = 2 }) {
  const [open, setOpen] = useState(false);
  const list = (comments?.[group] || []).slice(0, maxShow);
  if (!list.length) return null;

  const groupColor = {
    positive: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300',
    negative: 'border-red-500/30 bg-red-500/5 text-red-300',
    neutral:  'border-gray-500/30 bg-gray-500/5 text-gray-300',
  };

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition"
      >
        <MessageSquare size={11} />
        Bằng chứng từ bình luận ({list.length})
        {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5">
              {list.map((c, i) => (
                <div
                  key={i}
                  className={`rounded-lg border p-2.5 text-xs leading-relaxed ${groupColor[group]}`}
                >
                  "{c.text?.length > 120 ? c.text.slice(0, 120) + '…' : c.text}"
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Action Card ───────────────────────────────────────────────────────────────
function ActionCard({ action, index, comments }) {
  const priorityStyle = {
    high:   'bg-red-500/20 text-red-300 border-red-500/30',
    medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    low:    'bg-blue-500/20 text-blue-300 border-blue-500/30',
  };
  const priorityLabel = { high: '🔴 Cao', medium: '🟡 Trung bình', low: '🟢 Thấp' };

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
          {/* Comment Evidence */}
          {action.evidenceGroup && (
            <CommentEvidence comments={comments} group={action.evidenceGroup} />
          )}
        </div>
        <div className={`px-2 py-1 rounded border text-xs font-semibold whitespace-nowrap ${priorityStyle[action.priority]}`}>
          {priorityLabel[action.priority]}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 text-xs">
        <div className="flex items-center gap-1 text-gray-400">
          <Clock size={12} />{action.timeline}
        </div>
        <div className="flex items-center gap-1 text-emerald-400">
          <TrendingUp size={12} />{action.impact}
        </div>
      </div>
    </motion.div>
  );
}

// ── Risk Assessment ───────────────────────────────────────────────────────────
function RiskAssessment({ stats, comments }) {
  const risks = [];
  const opps  = [];

  if (stats.negative_pct > 40) {
    risks.push({
      title: 'Mất khách hàng cao',
      desc:  'Tỷ lệ tiêu cực >40% đe dọa tỷ lệ chuyển đổi',
      level: 'critical',
    });
  }
  if (stats.positive_pct < 30) {
    risks.push({
      title: 'Thiếu lợi thế cạnh tranh',
      desc:  'Không có điểm nổi bật rõ ràng trong mắt khách hàng',
      level: 'high',
    });
  }
  if (stats.average_confidence < 0.65) {
    risks.push({
      title: 'Độ tin cậy phân tích thấp',
      desc:  'Cần thu thập thêm phản hồi để có kết quả chính xác hơn',
      level: 'medium',
    });
  }
  if (stats.positive_pct > 50) {
    opps.push({
      title: 'Cơ hội dẫn đầu thị trường',
      desc:  'Dùng lợi thế sentiment tích cực để mở rộng thị phần',
    });
  }
  if (stats.positive_pct - stats.negative_pct > 30) {
    opps.push({
      title: 'Khoảng cách vượt trội',
      desc:  'Tận dụng trong truyền thông & marketing so sánh',
    });
  }
  if ((comments?.positive?.length || 0) > 10) {
    opps.push({
      title: `${comments.positive.length} bình luận tích cực để khai thác`,
      desc:  'Chuyển thành testimonials, case studies, review chính thức',
    });
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div className="space-y-3">
        <h3 className="font-semibold text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle size={16} /> Rủi ro phát hiện
        </h3>
        {risks.length > 0 ? (
          risks.map((r, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              className="bg-red-500/10 border border-red-500/20 rounded-lg p-3"
            >
              <p className="font-semibold text-red-300 text-xs">{r.title}</p>
              <p className="text-gray-400 text-xs mt-1">{r.desc}</p>
            </motion.div>
          ))
        ) : (
          <p className="text-gray-500 text-xs">Không có rủi ro đáng kể 😊</p>
        )}
      </div>

      <div className="space-y-3">
        <h3 className="font-semibold text-emerald-400 text-sm flex items-center gap-2">
          <Zap size={16} /> Cơ hội tiềm năng
        </h3>
        {opps.length > 0 ? (
          opps.map((o, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3"
            >
              <p className="font-semibold text-emerald-300 text-xs">{o.title}</p>
              <p className="text-gray-400 text-xs mt-1">{o.desc}</p>
            </motion.div>
          ))
        ) : (
          <p className="text-gray-500 text-xs">Chưa có cơ hội lớn rõ ràng</p>
        )}
      </div>
    </div>
  );
}

// ── Comment Summary Banner ────────────────────────────────────────────────────
function CommentSummaryBanner({ comments, stats }) {
  const topPositive = comments?.positive?.[0];
  const topNegative = comments?.negative?.[0];

  if (!topPositive && !topNegative) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {topPositive && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-1">
            <MessageSquare size={12} /> Bình luận tích cực tiêu biểu
          </p>
          <p className="text-xs text-gray-300 leading-relaxed italic">
            "{topPositive.text?.slice(0, 150)}{topPositive.text?.length > 150 ? '…' : ''}"
          </p>
        </div>
      )}
      {topNegative && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-red-400 mb-2 flex items-center gap-1">
            <MessageSquare size={12} /> Bình luận tiêu cực tiêu biểu
          </p>
          <p className="text-xs text-gray-300 leading-relaxed italic">
            "{topNegative.text?.slice(0, 150)}{topNegative.text?.length > 150 ? '…' : ''}"
          </p>
        </div>
      )}
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function ConsultingStrategy({ data, bank }) {
  const stats        = data.summary;
  const comments     = data.comments || {};
  const strategyType = getStrategyType(stats);
  const strategy     = STRATEGY_TEMPLATES[strategyType];

  const colorMap = {
    emerald: 'border-emerald-500/30',
    red:     'border-red-500/30',
    blue:    'border-blue-500/30',
  };

  // Build keyword summary from negative comments
  const topNegKeywords = useMemo(() => {
    const kw = {};
    (comments.negative || []).forEach(c => {
      (c.keywords || []).forEach(k => { kw[k] = (kw[k] || 0) + 1; });
    });
    return Object.entries(kw).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k]) => k);
  }, [comments]);

  const topPosKeywords = useMemo(() => {
    const kw = {};
    (comments.positive || []).forEach(c => {
      (c.keywords || []).forEach(k => { kw[k] = (kw[k] || 0) + 1; });
    });
    return Object.entries(kw).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k]) => k);
  }, [comments]);

  return (
    <div className="space-y-6">

      {/* ── Header ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`bg-gradient-to-r ${strategy.gradient} bg-opacity-20 border ${colorMap[strategy.color]} rounded-xl p-6`}
      >
        <h2 className="text-xl font-bold text-white">{strategy.title}</h2>
        <p className="text-sm text-gray-200 mt-2">{strategy.description}</p>
        <div className="flex flex-wrap gap-3 mt-4 text-xs">
          <span className="px-2 py-1 bg-white/10 rounded-full text-emerald-200">
            😊 {stats.positive} bình luận tích cực
          </span>
          <span className="px-2 py-1 bg-white/10 rounded-full text-red-200">
            😤 {stats.negative} bình luận tiêu cực
          </span>
          <span className="px-2 py-1 bg-white/10 rounded-full text-gray-200">
            😐 {stats.neutral} bình luận trung lập
          </span>
        </div>
      </motion.div>

      {/* ── Comment Sample Banner ── */}
      <CommentSummaryBanner comments={comments} stats={stats} />

      {/* ── Keyword Analysis from Comments ── */}
      {(topNegKeywords.length > 0 || topPosKeywords.length > 0) && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
            <Lightbulb size={15} className="text-yellow-400" />
            Từ khóa nổi bật từ bình luận
          </h3>
          <div className="space-y-3">
            {topPosKeywords.length > 0 && (
              <div>
                <p className="text-xs text-emerald-400 font-semibold mb-2">😊 Điểm mạnh được nhắc đến:</p>
                <div className="flex flex-wrap gap-2">
                  {topPosKeywords.map(kw => (
                    <span key={kw} className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-full text-xs">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {topNegKeywords.length > 0 && (
              <div>
                <p className="text-xs text-red-400 font-semibold mb-2">😤 Vấn đề được phản ánh:</p>
                <div className="flex flex-wrap gap-2">
                  {topNegKeywords.map(kw => (
                    <span key={kw} className="px-2 py-1 bg-red-500/10 border border-red-500/20 text-red-300 rounded-full text-xs">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Risk & Opportunity ── */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
          <AlertCircle size={16} className="text-yellow-400" />
          Đánh giá Rủi ro &amp; Cơ hội (từ bình luận thực tế)
        </h3>
        <RiskAssessment stats={stats} comments={comments} />
      </div>

      {/* ── Action Items (with comment evidence) ── */}
      <div className="space-y-3">
        <h3 className="font-semibold text-white text-sm flex items-center gap-2">
          <CheckCircle size={16} className="text-emerald-400" />
          Hành động khuyến nghị — dựa trên bình luận thực tế
        </h3>
        {strategy.actions.map((action, idx) => (
          <ActionCard key={idx} action={action} index={idx} comments={comments} />
        ))}
      </div>

      {/* ── KPI Targets ── */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
          <Target size={16} className="text-blue-400" />
          Mục tiêu KPI (90 ngày)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Tăng Tích cực',  target: `+${Math.ceil(stats.positive_pct * 0.15).toFixed(0)}%`, color: 'emerald' },
            { label: 'Giảm Tiêu cực',  target: `-${Math.ceil(stats.negative_pct * 0.25).toFixed(0)}%`, color: 'red'     },
            { label: 'Tăng Tin cậy',   target: '+15%',                                                  color: 'blue'    },
            { label: 'Tăng KH mới',    target: '+20%',                                                  color: 'purple'  },
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

      {/* ── Next Steps ── */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-6">
        <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
          <Activity size={16} className="text-cyan-400" />
          Bước tiếp theo
        </h3>
        <ol className="space-y-3">
          {[
            'Đọc kỹ tab "Bình luận chi tiết" → chọn nhóm Tiêu cực để xác định vấn đề cốt lõi',
            'Lập kế hoạch hành động cụ thể cho từng vấn đề phát hiện',
            'Gán trách nhiệm và đặt deadline rõ ràng',
            'Theo dõi tiến độ và phản hồi khách hàng mỗi tuần',
            'Chạy lại phân tích sau 30 ngày để đo lường cải thiện',
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
