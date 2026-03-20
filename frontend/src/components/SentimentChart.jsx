import React from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip,
  Legend
} from 'recharts';

const SentimentChart = ({ distribution }) => {
  const data = [
    { name: 'Tích cực', value: distribution.positive || 0, color: '#10b981' },
    { name: 'Trung lập', value: distribution.neutral || 0, color: '#6b7280' },
    { name: 'Tiêu cực', value: distribution.negative || 0, color: '#ef4444' }
  ].filter(d => d.value > 0);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-white/10 p-3 rounded-lg shadow-xl">
          <p className="text-white font-semibold">{payload[0].name}</p>
          <p className="text-cyan-400">{payload[0].value} bình luận</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
      <h3 className="text-lg font-semibold mb-4">Phân bố cảm xúc</h3>
            <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              iconType="circle"
              formatter={(value) => (
                <span className="text-gray-300 text-sm">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        {data.map((item, idx) => (
          <div key={idx} className="bg-black/20 rounded-lg p-3">
            <div 
              className="text-2xl font-bold mb-1"
              style={{ color: item.color }}
            >
              {item.value}
            </div>
            <div className="text-xs text-gray-400">{item.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SentimentChart;