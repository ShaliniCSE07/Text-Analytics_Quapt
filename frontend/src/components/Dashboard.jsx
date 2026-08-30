import React, { useEffect, useState } from 'react';
import { getSummary } from '../api/client';
import PageHeader from './PageHeader';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSummary()
      .then(data => {
        setSummary(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load dashboard data. Please try again later.');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse space-y-6 font-body">
        <PageHeader title="Dashboard" subtitle="Overview of overall sentiment metrics" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-surface rounded-lg"></div>
          ))}
        </div>
        <div className="h-32 bg-surface rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="font-body">
        <PageHeader title="Dashboard" subtitle="Overview of overall sentiment metrics" />
        <div className="text-negative bg-surface p-6 rounded-lg border-l-4 border-negative">
          {error}
        </div>
      </div>
    );
  }

  const { total_reviews, rating_breakdown, uncategorised_count } = summary;

  const posCount = rating_breakdown['Positive'] || 0;
  const negCount = rating_breakdown['Negative'] || 0;
  const neuCount = rating_breakdown['Neutral'] || 0;

  const totalRated = posCount + negCount + neuCount;
  const posPct = totalRated ? (posCount / totalRated) * 100 : 0;
  const negPct = totalRated ? (negCount / totalRated) * 100 : 0;
  const neuPct = totalRated ? (neuCount / totalRated) * 100 : 0;

  return (
    <div className="space-y-8 font-body">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Dashboard"
          subtitle="Overview of total feedback, sentiment breakdowns, and distribution"
        />
        <span className="text-sm font-mono text-textMuted bg-surface px-3 py-1.5 rounded-md border border-gray-800">
          {total_reviews} total reviews
        </span>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-surface p-6 rounded-lg shadow-sm border-l-4 border-positive border-y border-r border-gray-800/60">
          <div className="text-4xl font-mono font-bold text-positive">{posCount}</div>
          <div className="text-sm text-textMuted mt-2 font-medium">Positive</div>
        </div>

        <div className="bg-surface p-6 rounded-lg shadow-sm border-l-4 border-negative border-y border-r border-gray-800/60">
          <div className="text-4xl font-mono font-bold text-negative">{negCount}</div>
          <div className="text-sm text-textMuted mt-2 font-medium">Negative</div>
        </div>

        <div className="bg-surface p-6 rounded-lg shadow-sm border-l-4 border-neutral border-y border-r border-gray-800/60">
          <div className="text-4xl font-mono font-bold text-neutral">{neuCount}</div>
          <div className="text-sm text-textMuted mt-2 font-medium">Neutral</div>
        </div>

        <div className="bg-surface p-6 rounded-lg shadow-sm border-l-4 border-amber border-y border-r border-gray-800/60">
          <div className="text-4xl font-mono font-bold text-amber">{uncategorised_count}</div>
          <div className="text-sm text-textMuted mt-2 font-medium">Uncategorised</div>
        </div>
      </div>

      {/* Stacked Sentiment Bar */}
      <div className="bg-surface p-6 rounded-lg shadow-sm border border-gray-800/60">
        <h2 className="text-lg font-bold font-display text-textPrimary mb-4">Overall Sentiment</h2>
        <div className="h-6 flex rounded-full overflow-hidden bg-bg p-0.5 border border-gray-800">
          <div
            style={{ width: `${posPct}%` }}
            className="bg-positive transition-all duration-500 rounded-l-full"
            title={`Positive: ${posPct.toFixed(1)}%`}
          ></div>
          <div
            style={{ width: `${neuPct}%` }}
            className="bg-neutral transition-all duration-500"
            title={`Neutral: ${neuPct.toFixed(1)}%`}
          ></div>
          <div
            style={{ width: `${negPct}%` }}
            className="bg-negative transition-all duration-500 rounded-r-full"
            title={`Negative: ${negPct.toFixed(1)}%`}
          ></div>
        </div>
        <div className="flex flex-wrap gap-6 mt-4 text-sm font-medium">
          <div className="flex items-center text-textPrimary">
            <span className="w-3 h-3 bg-positive rounded-full mr-2"></span>
            Positive ({posPct.toFixed(1)}%)
          </div>
          <div className="flex items-center text-textPrimary">
            <span className="w-3 h-3 bg-neutral rounded-full mr-2"></span>
            Neutral ({neuPct.toFixed(1)}%)
          </div>
          <div className="flex items-center text-textPrimary">
            <span className="w-3 h-3 bg-negative rounded-full mr-2"></span>
            Negative ({negPct.toFixed(1)}%)
          </div>
        </div>
      </div>
    </div>
  );
}
