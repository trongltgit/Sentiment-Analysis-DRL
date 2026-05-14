// File: frontend/src/components/AnalysisDashboard.jsx
// Professional Dashboard v4.0 - Thay thế hoàn toàn file cũ

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle, CheckCircle, Clock, BrainCircuit, RefreshCw,
  TrendingUp, TrendingDown, Zap, Shield, Target, Users,
  Filter, Download, Share2, Lightbulb, BarChart3
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AnalysisDashboard = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedCategory, setSelectedCategory] = useState('positive');
  const [searchFilter, setSearchFilter] = useState('');

  const apiBase = '/api/v1';

  // Fetch analysis data
  useEffect(() => {
    let interval;
    let retryCount = 0;
    const maxRetries = 5;

    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(`${apiBase}/analysis/${id}`, { timeout: 15000 });
        setAnalysis(response.data);
        setError(null);
        retryCount = 0;

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
          clearInterval(interval);
        }
      } catch (err) {
        retryCount++;
        let errorMsg = 'Unable to load analysis';
        if (err.response?.status === 404) errorMsg = `Analysis not found: ${id}`;
        else if (err.code === 'ECONNABORTED') errorMsg = 'Connection timeout, retrying...';

        if (retryCount >= maxRetries) {
          setError(errorMsg);
          setPolling(false);
          clearInterval(interval);
          toast.error(errorMsg);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
    interval = setInterval(() => {
      if (polling) fetchAnalysis();
    }, 2000);

    return () => clearInterval(interval);
  }, [id]);

  // ===== HELPER FUNCTIONS =====

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-yellow-400',
      processing: 'text-blue-400',
      completed: 'text-green-400',
      failed: 'text-red-400',
    };
    return colors[status] || 'text-gray-400';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: <Clock className="animate-pulse" size={20} />,
      processing: <BrainCircuit className="animate-spin" size={20} />,
      completed: <CheckCircle size={20} />,
      failed: <AlertCircle size={20} />,
    };
    return icons[status];
  };

  const getSentimentColor = (sentiment) => {
    const colors = {
      positive: 'bg-green-500/20 border-green-500/30',
      negative: 'bg-red-500/20 border-red-500/30',
      neutral: 'bg-gray-500/20 border-gray-500/30',
    };
    return colors[sentiment] || 'bg-gray-500/20 border-gray-500/30';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.85) return 'text-green-400';
    if (confidence >= 0.70) return 'text-yellow-400';
    return 'text-orange-400';
  };

  const getCategoryComments = () => {
    const comments = analysis?.comments || {};
    const categoryMap = { positive: 'positive', negative: 'negative', neutral: 'neutral' };
    return comments[categoryMap[selectedCategory]] || [];
  };

  const filteredComments = getCategoryComments().filter(c =>
    c.text.toLowerCase().includes(searchFilter.toLowerCase())
  );

  // ===== LOADING STATE =====

  if (loading && !analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <BrainCircuit className="h-16 w-16 text-cyan-400 mb-4" />
        </motion.div>
        <p className="text-lg text-gray-300">Analyzing sentiment...</p>
        <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
      </div>
    );
  }

  // ===== ERROR STATE =====

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <AlertCircle size={64} className="text-red-500 mb-6" />
        <h2 className="text-2xl font-bold text-red-400 mb-2">Analysis Failed</h2>
        <p className="text-gray-400 text-center max-w-md mb-6">{error}</p>
        <div className="flex gap-4">
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg font-semibold transition"
          >
            Retry
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition"
          >
            Back Home
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const summary = analysis.summary || {};
  const insights = analysis.insights || {};
  const comments = analysis.comments || {};

  // ===== TAB DEFINITIONS =====

  const tabs = [
    { id: 'overview', label: '📊 Overview', icon: BarChart3 },
    { id: 'insights', label: '💡 Strategic Insights', icon: Lightbulb },
    { id: 'comments', label: '💬 Comments', icon: Users },
    { id: 'quality', label: '🎯 Quality Metrics', icon: Zap },
  ];

  // ===== RENDER =====

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white pb-10">
      {/* HEADER */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40"
      >
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">Sentiment Analysis Report</h1>
              <p className="text-gray-400 text-sm truncate">{analysis.url}</p>
            </div>
            <div className={`flex items-center gap-3 px-4 py-2 rounded-lg ${getStatusColor(analysis.status)} bg-white/5`}>
              {getStatusIcon(analysis.status)}
              <span className="font-semibold capitalize">{analysis.status}</span>
            </div>
          </div>

          {analysis.processing_time && (
            <div className="flex gap-4 text-sm text-gray-400">
              <span>⏱️ {analysis.processing_time.toFixed(2)}s</span>
              <span>📊 {summary.total_comments || 0} comments analyzed</span>
              <span>📈 {summary.average_confidence ? (summary.average_confidence * 100).toFixed(1) : 0}% confidence</span>
            </div>
          )}
        </div>

        {/* TAB NAVIGATION */}
        {analysis.status === 'completed' && (
          <div className="bg-black/20 px-6 py-4 flex gap-2 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg whitespace-nowrap font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-600 text-white'
                    : 'bg-white/5 text-gray-300 hover:bg-white/10'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </motion.div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {/* TAB: OVERVIEW */}
          {activeTab === 'overview' && analysis.status === 'completed' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* MAIN SENTIMENT CARDS */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    label: 'Positive',
                    value: summary.positive_pct || 0,
                    count: summary.positive || 0,
                    color: 'from-green-500 to-emerald-600',
                    icon: '👍',
                  },
                  {
                    label: 'Negative',
                    value: summary.negative_pct || 0,
                    count: summary.negative || 0,
                    color: 'from-red-500 to-rose-600',
                    icon: '👎',
                  },
                  {
                    label: 'Neutral',
                    value: summary.neutral_pct || 0,
                    count: summary.neutral || 0,
                    color: 'from-gray-500 to-slate-600',
                    icon: '➡️',
                  },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    className={`bg-gradient-to-br ${item.color} rounded-2xl p-6 shadow-2xl`}
                  >
                    <div className="text-4xl mb-3">{item.icon}</div>
                    <div className="text-5xl font-bold mb-2">{item.value.toFixed(1)}%</div>
                    <div className="text-white/80 text-sm">{item.label}</div>
                    <div className="text-white/60 text-xs mt-2">{item.count} comments</div>
                  </motion.div>
                ))}
              </div>

              {/* KEY METRICS */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="bg-white/5 backdrop-blur border border-white/10 rounded-xl p-5"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Shield className="text-blue-400" size={20} />
                    <h3 className="font-semibold">Sentiment Trend</h3>
                  </div>
                  <div className="text-2xl font-bold capitalize text-cyan-400">
                    {insights.overall_sentiment || 'Analyzing...'}
                  </div>
                  <p className="text-gray-400 text-xs mt-2">
                    {insights.trend === 'positive' ? '📈 Trending positive' : '📉 Trending negative'}
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="bg-white/5 backdrop-blur border border-white/10 rounded-xl p-5"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Target className="text-purple-400" size={20} />
                    <h3 className="font-semibold">Analysis Quality</h3>
                  </div>
                  <div className="text-2xl font-bold text-purple-400">
                    {(summary.average_confidence * 100).toFixed(1)}%
                  </div>
                  <p className="text-gray-400 text-xs mt-2">Average confidence score</p>
                </motion.div>
              </div>
            </motion.div>
          )}

          {/* TAB: STRATEGIC INSIGHTS */}
          {activeTab === 'insights' && analysis.status === 'completed' && (
            <motion.div
              key="insights"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* RISKS */}
              {insights.risks && insights.risks.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6">
                  <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center gap-2">
                    <AlertCircle size={20} /> Identified Risks
                  </h3>
                  <div className="space-y-3">
                    {insights.risks.map((risk, idx) => (
                      <div key={idx} className="bg-black/30 rounded-lg p-4">
                        <div className="flex justify-between mb-2">
                          <span className="font-semibold capitalize">{risk.type.replace(/_/g, ' ')}</span>
                          <span className={`text-xs px-2 py-1 rounded capitalize ${
                            risk.severity === 'high' ? 'bg-red-600' : 'bg-yellow-600'
                          }`}>
                            {risk.severity} severity
                          </span>
                        </div>
                        <p className="text-gray-400 text-sm">{risk.description}</p>
                        <p className="text-gray-500 text-xs mt-2">Impact: {risk.impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* OPPORTUNITIES */}
              {insights.opportunities && insights.opportunities.length > 0 && (
                <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-6">
                  <h3 className="text-xl font-bold text-green-400 mb-4 flex items-center gap-2">
                    <Lightbulb size={20} /> Growth Opportunities
                  </h3>
                  <div className="space-y-3">
                    {insights.opportunities.map((opp, idx) => (
                      <div key={idx} className="bg-black/30 rounded-lg p-4">
                        <div className="flex justify-between mb-2">
                          <span className="font-semibold capitalize">{opp.type.replace(/_/g, ' ')}</span>
                          <span className={`text-xs px-2 py-1 rounded capitalize ${
                            opp.potential === 'high' ? 'bg-green-600' : 'bg-blue-600'
                          }`}>
                            {opp.potential} potential
                          </span>
                        </div>
                        <p className="text-gray-400 text-sm">{opp.description}</p>
                        <p className="text-green-400 text-xs mt-2">→ {opp.action}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* RECOMMENDATIONS */}
              {insights.recommendations && insights.recommendations.length > 0 && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-2xl p-6">
                  <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2">
                    <Target size={20} /> Strategic Recommendations
                  </h3>
                  <div className="space-y-3">
                    {insights.recommendations.map((rec, idx) => (
                      <div key={idx} className="bg-black/30 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-semibold">{rec.action}</span>
                          <span className={`text-xs px-2 py-1 rounded capitalize ${
                            rec.priority === 'high' ? 'bg-red-600' :
                            rec.priority === 'medium' ? 'bg-yellow-600' : 'bg-blue-600'
                          }`}>
                            {rec.priority}
                          </span>
                        </div>
                        <p className="text-gray-400 text-sm">{rec.details}</p>
                        <div className="flex gap-4 text-xs text-gray-500 mt-2">
                          <span>⏱️ {rec.timeline}</span>
                          <span>👤 {rec.owner}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* TAB: COMMENTS */}
          {activeTab === 'comments' && analysis.status === 'completed' && (
            <motion.div
              key="comments"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              {/* CATEGORY SELECTOR */}
              <div className="flex gap-3 flex-wrap">
                {[
                  { id: 'positive', label: '👍 Positive', color: 'green' },
                  { id: 'negative', label: '👎 Negative', color: 'red' },
                  { id: 'neutral', label: '➡️ Neutral', color: 'gray' },
                ].map(cat => (
                  <button
                    key={cat.id}
                    onClick={() => { setSelectedCategory(cat.id); setSearchFilter(''); }}
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      selectedCategory === cat.id
                        ? `bg-${cat.color}-600`
                        : `bg-${cat.color}-500/20 border border-${cat.color}-500/30 hover:bg-${cat.color}-500/30`
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* SEARCH FILTER */}
              <div className="relative">
                <Filter className="absolute left-3 top-3 text-gray-500" size={20} />
                <input
                  type="text"
                  placeholder="Search comments..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
                />
              </div>

              {/* COMMENTS LIST */}
              <div className="space-y-3">
                {filteredComments.length > 0 ? (
                  filteredComments.map((comment, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className={`border rounded-lg p-4 ${getSentimentColor(comment.sentiment)}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <p className="text-gray-200 flex-1">{comment.text}</p>
                        <span className={`text-xs px-2 py-1 rounded-full ml-2 whitespace-nowrap ${getConfidenceColor(comment.confidence)} font-semibold`}>
                          {(comment.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {comment.keywords.length > 0 && (
                        <div className="flex gap-2 flex-wrap mt-2">
                          {comment.keywords.map((kw, i) => (
                            <span key={i} className="text-xs bg-black/20 px-2 py-1 rounded text-gray-300">
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No comments found in this category
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* TAB: QUALITY METRICS */}
          {activeTab === 'quality' && analysis.status === 'completed' && (
            <motion.div
              key="quality"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { label: 'Very High Confidence', count: summary.confidence_distribution?.very_high || 0, color: 'green' },
                  { label: 'High Confidence', count: summary.confidence_distribution?.high || 0, color: 'blue' },
                  { label: 'Medium Confidence', count: summary.confidence_distribution?.medium || 0, color: 'yellow' },
                  { label: 'Low Confidence', count: summary.confidence_distribution?.low || 0, color: 'red' },
                ].map((item, idx) => (
                  <div key={idx} className={`bg-${item.color}-500/10 border border-${item.color}-500/20 rounded-lg p-4`}>
                    <p className={`text-${item.color}-400 font-semibold`}>{item.label}</p>
                    <p className="text-2xl font-bold text-white mt-2">{item.count}</p>
                    <p className="text-gray-500 text-xs mt-1">
                      {summary.total_comments ? ((item.count / summary.total_comments) * 100).toFixed(1) : 0}% of total
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AnalysisDashboard;
