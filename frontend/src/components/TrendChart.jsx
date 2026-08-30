import React, { useEffect, useState } from 'react';
import { getTrend } from '../api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export default function TrendChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getTrend()
      .then(setData)
      .catch(() => setError('Failed to load trend data.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-surface rounded-lg border border-gray-800/80 p-6 flex flex-col shadow-sm font-body">
      <h2 className="font-display font-bold text-textPrimary text-xl mb-4">Sentiment Over Time</h2>

      {loading && (
        <div className="flex-1 flex items-center justify-center min-h-[220px]">
          <div className="w-8 h-8 border-4 border-amber border-t-transparent rounded-full animate-spin opacity-40" />
        </div>
      )}

      {error && (
        <div className="flex-1 flex items-center justify-center text-textMuted text-sm">{error}</div>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-textMuted text-sm">No trend data available.</div>
      )}

      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#262F40" />
            <XAxis dataKey="month" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#94A0B8' }} />
            <YAxis tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#94A0B8' }} allowDecimals={false} />
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
            <Line type="monotone" dataKey="Positive" stroke="#34D399" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="Negative" stroke="#F87171" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="Neutral" stroke="#94A3B8" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
