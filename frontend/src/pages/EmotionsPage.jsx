import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import {
  getEmotionsSummary,
  getEmotionsTrend,
  getEmotions,
  analyzeEmotions
} from '../api/client';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import {
  Smile, Frown, AlertTriangle, HelpCircle, Flame, Eye,
  RefreshCw, ChevronLeft, ChevronRight, Info, SlidersHorizontal, Sparkles
} from 'lucide-react';

const EMOTION_CONFIG = {
  Delight: {
    label: 'Delight',
    color: '#10B981', // Emerald
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/40',
    textColor: 'text-emerald-400',
    icon: Smile,
    description: 'Joy, admiration, gratitude, approval, excitement'
  },
  Frustration: {
    label: 'Frustration',
    color: '#F97316', // Orange
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/40',
    textColor: 'text-orange-400',
    icon: Flame,
    description: 'Annoyance, disapproval'
  },
  Disappointment: {
    label: 'Disappointment',
    color: '#6366F1', // Indigo
    bgColor: 'bg-indigo-500/10',
    borderColor: 'border-indigo-500/40',
    textColor: 'text-indigo-400',
    icon: Frown,
    description: 'Disappointment, sadness, remorse'
  },
  Anxiety: {
    label: 'Anxiety',
    color: '#A855F7', // Purple
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/40',
    textColor: 'text-purple-400',
    icon: AlertTriangle,
    description: 'Nervousness, fear'
  },
  Confusion: {
    label: 'Confusion',
    color: '#EAB308', // Amber/Yellow
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/40',
    textColor: 'text-yellow-400',
    icon: HelpCircle,
    description: 'Unclear policy clauses, unexplained steps'
  },
  Anger: {
    label: 'Anger',
    color: '#EF4444', // Red
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/40',
    textColor: 'text-red-400',
    icon: Flame,
    description: 'Anger, disgust'
  },
  Uncertain: {
    label: 'Uncertain',
    color: '#94A3B8', // Slate
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/40',
    textColor: 'text-slate-400',
    icon: Info,
    description: 'No category met the 35% confidence threshold'
  }
};

export default function EmotionsPage() {
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [reviewsData, setReviewsData] = useState({ total: 0, reviews: [] });
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [toastMessage, setToastMessage] = useState('');

  // Filtering & Pagination State
  const [selectedEmotionFilter, setSelectedEmotionFilter] = useState('');
  const [productFilter, setProductFilter] = useState('');
  const [minConfidenceFilter, setMinConfidenceFilter] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Selected review for Explainability drawer/modal
  const [inspectedReview, setInspectedReview] = useState(null);

  // Active trend series toggles (all enabled by default)
  const [visibleTrendSeries, setVisibleTrendSeries] = useState({
    Delight: true,
    Frustration: true,
    Disappointment: true,
    Anxiety: true,
    Confusion: true,
    Anger: true,
    Uncertain: false
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  const fetchOverviewData = useCallback(async () => {
    try {
      const [sumRes, trendRes] = await Promise.all([
        getEmotionsSummary(),
        getEmotionsTrend()
      ]);
      setSummary(sumRes);
      setTrendData(trendRes);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch emotion analytics data.');
    }
  }, []);

  const fetchReviewsList = useCallback(async () => {
    setTableLoading(true);
    try {
      const params = {
        limit: pageSize,
        offset: (page - 1) * pageSize
      };
      if (selectedEmotionFilter) params.emotion = selectedEmotionFilter;
      if (productFilter) params.product = productFilter;
      if (minConfidenceFilter > 0) params.min_confidence = minConfidenceFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const data = await getEmotions(params);
      setReviewsData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setTableLoading(false);
    }
  }, [page, selectedEmotionFilter, productFilter, minConfidenceFilter, searchQuery]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchOverviewData(), fetchReviewsList()]).finally(() => {
      setLoading(false);
    });
  }, [fetchOverviewData, fetchReviewsList]);

  const handleRunAnalysis = async (force = false) => {
    setAnalyzing(true);
    try {
      const res = await analyzeEmotions(force);
      showToast(`Processed ${res.total_processed} reviews (${res.analyzed} analyzed, ${res.skipped_unsupported} skipped unsupported).`);
      await Promise.all([fetchOverviewData(), fetchReviewsList()]);
    } catch (err) {
      console.error(err);
      showToast('Error running emotion analysis.');
    } finally {
      setAnalyzing(false);
    }
  };

  const toggleTrendSeries = (key) => {
    setVisibleTrendSeries(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Distribution chart data prepared from summary
  const distributionData = useMemo(() => {
    if (!summary || !summary.emotion_counts) return [];
    return Object.entries(summary.emotion_counts).map(([name, count]) => ({
      name,
      count,
      percentage: summary.emotion_percentages[name] || 0,
      fill: EMOTION_CONFIG[name]?.color || '#94A3B8'
    }));
  }, [summary]);

  const getEmotionBadge = (emotion) => {
    const cfg = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.Uncertain;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg.bgColor} ${cfg.textColor} ${cfg.borderColor}`}>
        {emotion || 'Uncertain'}
      </span>
    );
  };

  const getSentimentBadge = (rating) => {
    switch (rating?.toLowerCase()) {
      case 'positive':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-positive/20 text-positive border border-positive/30">Pos</span>;
      case 'negative':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-negative/20 text-negative border border-negative/30">Neg</span>;
      case 'neutral':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-neutral/20 text-textPrimary border border-neutral/30">Neu</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs text-textMuted bg-gray-800">N/A</span>;
    }
  };

  const totalPages = Math.ceil((reviewsData.total || 0) / pageSize);

  if (loading) {
    return (
      <div className="space-y-6 font-body text-textPrimary animate-pulse">
        <PageHeader title="Emotions" subtitle="Loading customer emotion analytics suite..." />
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {[...Array(7)].map((_, i) => (
            <div key={i} className="h-28 bg-surface rounded-lg"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-72 bg-surface rounded-lg"></div>
          <div className="h-72 bg-surface rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 font-body text-textPrimary">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-surface text-amber border border-amber/40 px-4 py-2.5 rounded-lg shadow-xl z-50 transition-all font-mono text-sm">
          ✓ {toastMessage}
        </div>
      )}

      {/* Page Header with Action Button */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <PageHeader
            title="Emotions"
            subtitle="Business-specific affective classification mapped from RoBERTa GoEmotions (ICXBee)"
          />
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleRunAnalysis(false)}
            disabled={analyzing}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-amber text-bg font-bold text-xs rounded-lg hover:bg-amber/90 transition-all disabled:opacity-50 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
            <span>{analyzing ? 'Analyzing Reviews...' : 'Run Emotion Analysis'}</span>
          </button>
        </div>
      </div>

      {/* Denominator Explanation Banner */}
      {summary && (
        <div className="bg-surface/80 border border-gray-800 rounded-lg p-4 flex items-start space-x-3 text-xs leading-relaxed">
          <Info className="w-4 h-4 text-amber shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-textPrimary">Statistical Methodology & Analysis Baseline</div>
            <p className="text-textMuted">
              {summary.denominator_description} Unsupported languages ({summary.unsupported_reviews}) and unanalyzed reviews are tracked separately to avoid skewing category ratios. Model outputs represent lexical pattern correlations from RoBERTa GoEmotions rather than definitive psychological diagnoses.
            </p>
          </div>
        </div>
      )}

      {/* A. Emotion Summary Cards (6 Business Emotions + Uncertain) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3.5">
        {[
          'Delight',
          'Frustration',
          'Disappointment',
          'Anxiety',
          'Confusion',
          'Anger',
          'Uncertain'
        ].map((emoKey) => {
          const cfg = EMOTION_CONFIG[emoKey];
          const Icon = cfg.icon;
          const isUncertain = emoKey === 'Uncertain';
          const count = isUncertain
            ? (summary?.uncertain_count || 0)
            : (summary?.emotion_counts?.[emoKey] || 0);
          const percentage = isUncertain
            ? (summary?.uncertain_percentage || 0)
            : (summary?.emotion_percentages?.[emoKey] || 0);

          return (
            <div
              key={emoKey}
              onClick={() => {
                setSelectedEmotionFilter(prev => prev === emoKey ? '' : emoKey);
                setPage(1);
              }}
              className={`p-4 rounded-lg bg-surface border transition-all cursor-pointer group hover:scale-[1.02] ${
                selectedEmotionFilter === emoKey
                  ? `${cfg.borderColor} ring-2 ring-amber/40 shadow-md`
                  : 'border-gray-800/80 hover:border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs font-semibold ${cfg.textColor} truncate`} title={cfg.label}>
                  {cfg.label}
                </span>
                <Icon className={`w-4 h-4 ${cfg.textColor} opacity-80 group-hover:opacity-100`} />
              </div>
              <div className="text-2xl font-mono font-bold text-textPrimary leading-none mb-1">
                {count}
              </div>
              <div className="text-xs font-mono text-textMuted flex items-center justify-between">
                <span>{percentage.toFixed(1)}%</span>
                <span className="text-[10px] text-gray-500 truncate max-w-[70px]">{isUncertain ? 'Uncertain' : 'Share'}</span>
              </div>
              {/* Mini progress bar */}
              <div className="w-full bg-gray-900 h-1 rounded-full mt-2 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, percentage)}%`, backgroundColor: cfg.color }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* B. Emotion Distribution & C. Emotion Trends (2-Column Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* B. Emotion Distribution Chart */}
        <div className="bg-surface rounded-lg border border-gray-800/80 p-6 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-display font-bold text-textPrimary text-lg">Emotion Distribution</h2>
              <p className="text-xs text-textMuted">Proportional volume across 6 business categories</p>
            </div>
          </div>

          {distributionData.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-textMuted text-xs min-h-[240px]">
              No emotion distribution data available yet.
            </div>
          ) : (
            <div className="w-full h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributionData} margin={{ top: 10, right: 10, bottom: 20, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262F40" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontFamily: 'Inter', fontSize: 11, fill: '#94A0B8' }}
                    interval={0}
                  />
                  <YAxis
                    tick={{ fontFamily: 'Inter', fontSize: 11, fill: '#94A0B8' }}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1A2130',
                      borderColor: '#334155',
                      color: '#F1F3F6',
                      borderRadius: 8,
                      fontFamily: 'Inter',
                      fontSize: 12
                    }}
                    formatter={(val, name, props) => [`${val} reviews (${props.payload.percentage.toFixed(1)}%)`, 'Count']}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* C. Emotion Trends Chart */}
        <div className="bg-surface rounded-lg border border-gray-800/80 p-6 flex flex-col shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div>
              <h2 className="font-display font-bold text-textPrimary text-lg">Emotion Trends Over Time</h2>
              <p className="text-xs text-textMuted">Monthly trajectory of customer emotions</p>
            </div>
            {/* Toggle series buttons */}
            <div className="flex flex-wrap gap-1.5">
              {Object.keys(visibleTrendSeries).map((emo) => {
                const active = visibleTrendSeries[emo];
                const cfg = EMOTION_CONFIG[emo];
                return (
                  <button
                    key={emo}
                    onClick={() => toggleTrendSeries(emo)}
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-all ${
                      active
                        ? `${cfg.borderColor} ${cfg.textColor} ${cfg.bgColor}`
                        : 'border-gray-800 text-gray-500 bg-bg/50 line-through'
                    }`}
                  >
                    {emo}
                  </button>
                );
              })}
            </div>
          </div>

          {trendData.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-textMuted text-xs min-h-[240px]">
              No trend data available.
            </div>
          ) : (
            <div className="w-full h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 16, bottom: 20, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262F40" />
                  <XAxis dataKey="month" tick={{ fontFamily: 'Inter', fontSize: 11, fill: '#94A0B8' }} />
                  <YAxis tick={{ fontFamily: 'Inter', fontSize: 11, fill: '#94A0B8' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1A2130',
                      borderColor: '#334155',
                      color: '#F1F3F6',
                      borderRadius: 8,
                      fontFamily: 'Inter',
                      fontSize: 12
                    }}
                  />
                  <Legend wrapperStyle={{ fontFamily: 'Inter', fontSize: 11, color: '#94A0B8' }} />
                  {Object.keys(visibleTrendSeries).map((emo) => {
                    if (!visibleTrendSeries[emo]) return null;
                    return (
                      <Line
                        key={emo}
                        type="monotone"
                        dataKey={emo}
                        stroke={EMOTION_CONFIG[emo]?.color || '#94A3B8'}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* D. Review-Level Emotion Analysis Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="font-display font-bold text-textPrimary text-xl">Review-Level Emotion Analysis</h2>
            <p className="text-xs text-textMuted">Explore analyzed customer statements, mapped confidence scores, and model cues</p>
          </div>
          <span className="text-xs font-mono text-textMuted bg-surface px-3 py-1.5 rounded-md border border-gray-800 self-start sm:self-auto">
            {reviewsData.total} reviews found
          </span>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-surface p-4 rounded-lg border border-gray-800/80 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Emotion Filter */}
          <div>
            <label className="block text-[11px] font-mono text-textMuted mb-1">Emotion Filter</label>
            <select
              value={selectedEmotionFilter}
              onChange={(e) => {
                setSelectedEmotionFilter(e.target.value);
                setPage(1);
              }}
              className="w-full bg-bg border border-gray-800 rounded p-2 text-xs text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
            >
              <option value="">All Emotions</option>
              <option value="Delight">Delight</option>
              <option value="Frustration">Frustration</option>
              <option value="Disappointment">Disappointment</option>
              <option value="Anxiety">Anxiety</option>
              <option value="Confusion">Confusion</option>
              <option value="Anger">Anger</option>
              <option value="Uncertain">Uncertain / No clear emotion</option>
              <option value="language unsupported">Language Unsupported</option>
            </select>
          </div>

          {/* Product Filter */}
          <div>
            <label className="block text-[11px] font-mono text-textMuted mb-1">Product</label>
            <input
              type="text"
              value={productFilter}
              onChange={(e) => {
                setProductFilter(e.target.value);
                setPage(1);
              }}
              placeholder="e.g. Acme Health Shield..."
              className="w-full bg-bg border border-gray-800 rounded p-2 text-xs text-textPrimary placeholder:text-gray-600 focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
            />
          </div>

          {/* Search Query */}
          <div>
            <label className="block text-[11px] font-mono text-textMuted mb-1">Search Text</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search keyword in review..."
              className="w-full bg-bg border border-gray-800 rounded p-2 text-xs text-textPrimary placeholder:text-gray-600 focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
            />
          </div>

          {/* Min Confidence */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[11px] font-mono text-textMuted">Min Confidence</label>
              <span className="text-[11px] font-mono text-amber">{minConfidenceFilter}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={minConfidenceFilter}
              onChange={(e) => {
                setMinConfidenceFilter(Number(e.target.value));
                setPage(1);
              }}
              className="w-full accent-amber cursor-pointer mt-1"
            />
          </div>
        </div>

        {/* Table Container */}
        <div className="bg-surface rounded-lg border border-gray-800/80 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-bg/60 border-b border-gray-800 text-[11px] font-semibold text-textMuted uppercase tracking-wider font-mono">
                  <th className="p-3.5">ID / Platform</th>
                  <th className="p-3.5">Product</th>
                  <th className="p-3.5 w-2/5">Customer Review</th>
                  <th className="p-3.5">Primary Emotion</th>
                  <th className="p-3.5 text-center">Confidence</th>
                  <th className="p-3.5 text-center">Sentiment</th>
                  <th className="p-3.5 text-right">Explainability</th>
                </tr>
              </thead>
              <tbody className="text-xs divide-y divide-gray-800/60">
                {tableLoading ? (
                  <tr>
                    <td colSpan="7" className="p-8 text-center text-textMuted animate-pulse">
                      Loading matching reviews...
                    </td>
                  </tr>
                ) : reviewsData.reviews.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="p-12 text-center text-textMuted">
                      No customer reviews match the selected emotion and filters.
                    </td>
                  </tr>
                ) : (
                  reviewsData.reviews.map((row) => (
                    <tr key={row.Platform_Reference_Id} className="hover:bg-bg/40 transition-colors">
                      <td className="p-3.5 align-top">
                        <div className="font-semibold text-textPrimary">{row.Platform}</div>
                        <div className="text-[10px] font-mono text-textMuted">{row.Platform_Reference_Id}</div>
                        {row.Month_Year && (
                          <div className="text-[10px] font-mono text-gray-500 mt-0.5">{row.Month_Year}</div>
                        )}
                      </td>
                      <td className="p-3.5 align-top font-medium text-textPrimary max-w-[120px] truncate" title={row.Product}>
                        {row.Product}
                      </td>
                      <td className="p-3.5 align-top leading-relaxed text-textPrimary/90">
                        {row.Review}
                      </td>
                      <td className="p-3.5 align-top">
                        {getEmotionBadge(row.Emotion)}
                      </td>
                      <td className="p-3.5 align-top text-center font-mono font-bold text-amber">
                        {row.Emotion_Confidence ? `${row.Emotion_Confidence}%` : '—'}
                      </td>
                      <td className="p-3.5 align-top text-center">
                        {getSentimentBadge(row.Rating)}
                      </td>
                      <td className="p-3.5 align-top text-right space-x-1.5 whitespace-nowrap">
                        <button
                          onClick={() => setInspectedReview(row)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-amber border border-amber/40 bg-amber/5 rounded hover:bg-amber hover:text-bg transition-all"
                        >
                          Scores
                        </button>
                        <Link
                          to={`/reviews/${row.Platform_Reference_Id}`}
                          className="px-2.5 py-1 text-[11px] font-semibold text-textPrimary border border-gray-700 bg-bg/50 rounded hover:bg-gray-800 transition-all"
                        >
                          Detail
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="p-4 bg-bg/40 border-t border-gray-800 flex items-center justify-between text-xs">
              <span className="font-mono text-textMuted">
                Page {page} of {totalPages} ({reviewsData.total} items)
              </span>
              <div className="flex items-center space-x-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  className="px-2.5 py-1 rounded border border-gray-800 bg-surface disabled:opacity-40 hover:bg-gray-800 text-textPrimary transition-all flex items-center space-x-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Prev</span>
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 rounded border border-gray-800 bg-surface disabled:opacity-40 hover:bg-gray-800 text-textPrimary transition-all flex items-center space-x-1"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* E. Explainability Modal / Drawer */}
      {inspectedReview && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-gray-800 rounded-xl max-w-xl w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div className="flex items-center space-x-2.5">
                <Sparkles className="w-5 h-5 text-amber" />
                <div>
                  <h3 className="font-display font-bold text-base text-textPrimary">
                    Emotion Model Explainability
                  </h3>
                  <p className="text-xs text-textMuted font-mono">
                    ID: {inspectedReview.Platform_Reference_Id} • {inspectedReview.Product}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setInspectedReview(null)}
                className="text-textMuted hover:text-textPrimary text-sm font-mono px-2 py-1 rounded bg-bg border border-gray-800"
              >
                ✕
              </button>
            </div>

            {/* Review quote */}
            <div className="bg-bg p-3.5 rounded-lg border-l-4 border-amber italic text-sm text-textPrimary/90">
              "{inspectedReview.Review}"
            </div>

            {/* Classification summary */}
            <div className="flex items-center justify-between text-xs bg-bg/60 p-3 rounded-lg border border-gray-800 font-mono">
              <div>
                <span className="text-textMuted mr-2">Assigned Primary:</span>
                <span className="font-bold text-textPrimary">{inspectedReview.Emotion || 'Uncertain'}</span>
              </div>
              <div>
                <span className="text-textMuted mr-2">Confidence:</span>
                <span className="font-bold text-amber">{inspectedReview.Emotion_Confidence || 0}%</span>
              </div>
            </div>

            {/* 6 Category Mapped Scores */}
            <div className="space-y-2">
              <div className="text-xs font-mono text-textMuted uppercase tracking-wider">
                Category Scores (Max Source Rule)
              </div>
              <div className="space-y-2">
                {[
                  'Delight',
                  'Frustration',
                  'Disappointment',
                  'Anxiety',
                  'Confusion',
                  'Anger'
                ].map((emo) => {
                  const score = inspectedReview.Emotion_Scores_Dict?.[emo] ?? 0;
                  const pct = Math.round(score * 100);
                  const isPrimary = inspectedReview.Emotion === emo;
                  const cfg = EMOTION_CONFIG[emo];

                  return (
                    <div key={emo} className="text-xs space-y-1">
                      <div className="flex justify-between items-center">
                        <span className={`font-medium ${isPrimary ? `${cfg.textColor} font-bold` : 'text-textPrimary'}`}>
                          {emo} {isPrimary && '★'}
                        </span>
                        <span className="font-mono text-textMuted">{pct}% (raw: {score.toFixed(3)})</span>
                      </div>
                      <div className="w-full bg-bg h-2 rounded-full overflow-hidden border border-gray-800">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${Math.min(100, pct)}%`,
                            backgroundColor: cfg.color
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Cautionary Note */}
            <div className="p-3 bg-amber/5 border border-amber/20 rounded-lg text-xs text-amber/90 leading-relaxed space-y-1">
              <div className="font-semibold flex items-center space-x-1">
                <Info className="w-3.5 h-3.5" />
                <span>Notice on Machine Predictions</span>
              </div>
              <p className="text-[11px] text-textMuted">
                Model scores are derived from lexical matching in pretrained RoBERTa GoEmotions representations. They reflect statistical textual features and must not be treated as ground-truth customer mental states.
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setInspectedReview(null)}
                className="px-4 py-2 bg-gray-800 text-textPrimary text-xs font-semibold rounded-lg hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
