// ComparisonDashboard.jsx v4.0 — Enhanced with Detailed Review Tab + Professional Strategy
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import BankComparison from './BankComparison';
import SentimentDetailView from './SentimentDetailView';
import ConsultingStrategy from './ConsultingStrategy_Enhanced';
import DetailedReviewTab from './DetailedReviewTab';

const API = '/api/v1';

const MAIN_TABS = [
  { id: 'comparison', label: '📊 So sánh Tổng quan' },
  { id: 'detailed-review', label: '📋 Bình luận chi tiết' },
  { id: 'individual', label: '🏦 Chi tiết Từng Ngân hàng' },
  { id: 'strategies', label: '🎯 Chiến lược Riêng Biệt' },
];

// ── Per-Bank Panel: Sentiment sub-tabs + Consulting strategy ──────────────────
function BankDetailPanel({ analysis, allAnalyses }) {
  const [subTab, setSubTab] = useState('sentiment');
  const bank = analysis.bank || analysis.url;

  // Aggregate all comments by bank for enhanced strategy analysis
  const allBankComments = {};
  if (allAnalyses) {
    allAnalyses.forEach((a) => {
      const bankName = a.bank || a.url;
      if (a.summary && a.summary.comments) {
        allBankComments[bankName] = a.summary.comments;
      }
    });
  }

  return (
    <div className="space-y-4">
      {/* Sub-tabs */}
      <div className="flex gap-2 border-b border-white/10 overflow-x-auto">
        {[
          { id: 'sentiment', label: '📊 Phân tích Sentiment & Bình luận' },
          { id: 'strategy', label: '🎯 Chiến lược Tư vấn' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setSubTab(t.id)}
            className={`px-4 py-2.5 text-sm font-semibold whitespace-nowrap border-b-2 transition ${
              subTab === t.id
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {subTab === 'sentiment' && (
          <motion.div
            key="sentiment"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <SentimentDetailView data={analysis} bank={bank} />
          </motion.div>
        )}

        {subTab === 'strategy' && (
          <motion.div
            key="strategy"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <ConsultingStrategy
              data={analysis}
              bank={bank}
              allBankComments={allBankComments}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function ComparisonDashboard() {
  const location = useLocation();
  const navigate = useNavigate();

  const [mainTab, setMainTab] = useState('comparison');
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Aggregate data for detailed review
  const bankComments = {};
  analyses.forEach((analysis) => {
    const bankName = analysis.bank || analysis.url;
    if (analysis.summary && analysis.summary.comments) {
      bankComments[bankName] = analysis.summary.comments;
    }
  });

  useEffect(() => {
    const init = async () => {
      try {
        if (location.state?.analyses) {
          setAnalyses(location.state.analyses);
        } else {
          toast.error('No analysis data provided');
          navigate('/');
        }
      } catch (err) {
        setError(err.message);
        toast.error('Error loading comparison data');
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [location, navigate]);

  if (loading)
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin mr-2" />
        <span>Loading comparison dashboard...</span>
      </div>
    );

  if (error || !analyses.length)
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 max-w-md mx-auto"
      >
        <h2 className="font-bold text-red-400 mb-2">Error Loading Comparison</h2>
        <p className="text-red-200 text-sm mb-4">{error || 'No analysis data found'}</p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
        >
          Back to Home
        </button>
      </motion.div>
    );

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/')}
            className="mb-4 flex items-center gap-2 text-gray-400 hover:text-white transition"
          >
            <ArrowLeft size={18} />
            Back
          </button>
          <h1 className="text-3xl font-bold text-white">
            📊 So sánh {analyses.length} Ngân hàng
          </h1>
          <p className="text-gray-400 text-sm mt-2">
            Phân tích toàn diện, so sánh sentiment và chiến lược tư vấn chi tiết
          </p>
        </div>
      </div>

      {/* Main Tabs */}
      <div className="border-b border-white/10 overflow-x-auto">
        <div className="flex gap-2">
          {MAIN_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setMainTab(tab.id)}
              className={`px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition ${
                mainTab === tab.id
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {mainTab === 'comparison' && (
          <motion.div
            key="comparison"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <BankComparison analyses={analyses} />
          </motion.div>
        )}

        {mainTab === 'detailed-review' && (
          <motion.div
            key="detailed-review"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <DetailedReviewTab
              bankComments={bankComments}
              bankData={analyses.reduce((acc, a) => {
                const bankName = a.bank || a.url;
                acc[bankName] = a.summary || {};
                return acc;
              }, {})}
            />
          </motion.div>
        )}

        {mainTab === 'individual' && (
          <motion.div
            key="individual"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="space-y-8"
          >
            {analyses.map((analysis, idx) => {
              const bankName = analysis.bank || analysis.url;
              return (
                <motion.div
                  key={bankName}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="bg-white/5 border border-white/10 rounded-xl p-6"
                >
                  <h2 className="text-2xl font-bold text-white mb-4">{bankName}</h2>
                  <BankDetailPanel analysis={analysis} allAnalyses={analyses} />
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {mainTab === 'strategies' && (
          <motion.div
            key="strategies"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="space-y-8"
          >
            {analyses.map((analysis, idx) => {
              const bankName = analysis.bank || analysis.url;
              
              // Aggregate all comments for comprehensive strategy
              const allBankComments = {};
              analyses.forEach((a) => {
                const name = a.bank || a.url;
                if (a.summary && a.summary.comments) {
                  allBankComments[name] = a.summary.comments;
                }
              });

              return (
                <motion.div
                  key={bankName}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="bg-white/5 border border-white/10 rounded-xl p-6"
                >
                  <h2 className="text-2xl font-bold text-white mb-4">
                    🎯 Chiến lược cho {bankName}
                  </h2>
                  <ConsultingStrategy
                    data={analysis}
                    bank={bankName}
                    allBankComments={allBankComments}
                  />
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
