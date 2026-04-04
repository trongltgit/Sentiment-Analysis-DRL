import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  BrainCircuit
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AnalysisDashboard = () => {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(true);
  const [error, setError] = useState(null);

  // 🔴 SỬA: Dùng relative URL vì cùng domain
  const apiBase = '/api/v1';

  useEffect(() => {
    let interval;

    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(`${apiBase}/analysis/${id}`, {
          timeout: 30000 // 30s cho analysis lâu
        });

        setAnalysis(response.data);
        setError(null);

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setPolling(false);
        }
      } catch (err) {
        console.error("API Error:", err);
        setError("Không thể kết nối đến server phân tích.");
        toast.error("Lỗi kết nối backend");
        setPolling(false);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();

    if (polling) {
      interval = setInterval(fetchAnalysis, 4000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, polling]);

  // ... rest of component giữ nguyên
};

export default AnalysisDashboard;
