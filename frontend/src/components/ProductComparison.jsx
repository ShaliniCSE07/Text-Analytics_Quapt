import React, { useEffect, useState } from 'react';
import { getByProduct } from '../api/client';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LabelList, ResponsiveContainer
} from 'recharts';

export default function ProductComparison() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getByProduct()
      .then(setData)
      .catch(() => setError('Failed to load product data.'))
      .finally(() => setLoading(false));
  }, []);

  const TotalLabel = (props) => {
    const { x, y, width, height, value } = props;
    return (
      <text x={x + width + 6} y={y + height / 2 + 4} fill="#94A0B8" fontSize={11} fontFamily="JetBrains Mono">
        {value}
      </text>
    );
  };

  return (
    <div className="bg-surface rounded-lg border border-gray-800/80 p-6 flex flex-col shadow-sm font-body">
      <h2 className="font-display font-bold text-textPrimary text-xl mb-4">Sentiment by Product</h2>

      {loading && (
        <div className="flex-1 flex items-center justify-center min-h-[220px]">
          <div className="w-8 h-8 border-4 border-amber border-t-transparent rounded-full animate-spin opacity-40" />
        </div>
      )}

      {error && (
        <div className="flex-1 flex items-center justify-center text-textMuted text-sm">{error}</div>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-textMuted text-sm">No product data available.</div>
      )}

      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 8, right: 60, bottom: 4, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#262F40" horizontal={false} />
            <XAxis type="number" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#94A0B8' }} allowDecimals={false} />
            <YAxis dataKey="product" type="category" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#F1F3F6' }} width={90} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1A2130',
                borderColor: '#334155',
                color: '#F1F3F6',
                borderRadius: 8,
                fontFamily: 'Inter',
                fontSize: 13
              }}
            />
            <Legend wrapperStyle={{ fontFamily: 'Inter', fontSize: 13, color: '#94A0B8' }} />
            <Bar dataKey="Positive" stackId="a" fill="#34D399" />
            <Bar dataKey="Neutral" stackId="a" fill="#94A3B8" />
            <Bar dataKey="Negative" stackId="a" fill="#F87171" radius={[0, 4, 4, 0]}>
              <LabelList dataKey="total" content={<TotalLabel />} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
