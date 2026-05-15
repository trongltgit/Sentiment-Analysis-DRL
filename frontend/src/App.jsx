// App.jsx v3.0 — Enhanced with Multi-Bank Comparison
import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import MultiURLInput from './components/MultiURLInput';
import AnalysisDashboard from './components/AnalysisDashboard';
import ComparisonDashboard from './components/ComparisonDashboard';
import FinancialMarket from './components/FinancialMarket';
import './styles.css';

function Home() {
  const navigate = useNavigate();

  const handleAnalysisStart = (data) => {
    // Single URL analysis
    if (!Array.isArray(data)) {
      const jobId = data?.id;
      if (jobId) navigate('/analysis/' + jobId);
    } else {
      // Multiple URLs comparison
      navigate('/comparison', { state: { analyses: data } });
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 items-start justify-center">
      {/* Input panel */}
      <div className="flex-1 max-w-2xl w-full">
        <MultiURLInput onAnalysisStart={handleAnalysisStart} />
      </div>

      {/* Market sidebar */}
      <div className="w-full lg:w-80 shrink-0">
        <FinancialMarket />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">

        {/* Navigation */}
        <nav className="border-b border-white/10 bg-black/30 backdrop-blur-lg sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <span className="text-xl">🏦</span>
              <span className="font-bold text-lg bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
                FinSentiment AI
              </span>
              <span className="text-gray-500 text-xs hidden sm:block">v3.0 Multi-Bank</span>
            </a>
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400">
                🤖 Groq Free
              </span>
              <span className="px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400">
                📊 Multi-Compare
              </span>
              <span className="px-2 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-400">
                📈 Strategy AI
              </span>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/"             element={<Home />} />
            <Route path="/analysis/:id" element={<AnalysisDashboard />} />
            <Route path="/comparison"   element={<ComparisonDashboard />} />
          </Routes>
        </main>

        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: '#1e293b', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' },
          }}
        />
      </div>
    </Router>
  );
}
