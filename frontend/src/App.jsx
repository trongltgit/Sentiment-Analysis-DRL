// File: frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import URLInput from './components/URLInput';
import AnalysisDashboard from './components/AnalysisDashboard';
import './styles.css';

// Wrapper để dùng useNavigate bên trong Router
function Home() {
  const navigate = useNavigate();

  const handleAnalysisStart = (data) => {
    // ✅ data.id là job_id trả về từ POST /api/v1/analyze
    const jobId = data?.id;
    if (jobId) {
      navigate(`/analysis/${jobId}`);
    } else {
      console.error('❌ Không nhận được job id từ server:', data);
    }
  };

  return <URLInput onAnalysisStart={handleAnalysisStart} />;
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
        {/* Navbar */}
        <nav className="border-b border-white/10 bg-black/20 backdrop-blur-lg sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="/" className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-400">
              🤖 AI Sentiment Analysis DRL
            </a>
          </div>
        </nav>

        {/* Nội dung */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/"               element={<Home />} />
            <Route path="/analysis/:id"   element={<AnalysisDashboard />} />
          </Routes>
        </main>

        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e293b',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.1)',
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
