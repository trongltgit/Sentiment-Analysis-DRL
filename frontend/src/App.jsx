import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import URLInput from './components/URLInput';
import AnalysisDashboard from './components/AnalysisDashboard';
import './styles.css';

function App() {
  const [currentAnalysis, setCurrentAnalysis] = useState(null);

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
        <nav className="border-b border-white/10 bg-black/20 backdrop-blur-lg">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-400">
              🤖 AI Sentiment Analysis DRL
            </h1>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route 
              path="/" 
              element={
                <URLInput 
                  onAnalysisStart={setCurrentAnalysis} 
                />
              } 
            />
            <Route 
              path="/analysis/:id" 
              element={
                <AnalysisDashboard 
                  analysisId={currentAnalysis?.analysis_id} 
                />
              } 
            />
          </Routes>
        </main>

        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e293b',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.1)'
            }
          }}
        />
      </div>
    </Router>
  );
}

export default App;