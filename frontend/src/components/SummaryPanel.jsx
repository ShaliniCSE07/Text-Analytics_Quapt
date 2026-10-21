import React, { useEffect, useState } from 'react';
import { getSummaryText, getByProduct } from '../api/client';

function Skeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-4 bg-gray-800 rounded w-full" />
      <div className="h-4 bg-gray-800 rounded w-5/6" />
      <div className="h-4 bg-gray-800 rounded w-4/6" />
      <div className="h-3 bg-gray-800/60 rounded w-32 mt-4" />
    </div>
  );
}

function SentimentMiniBar({ breakdown, total }) {
  if (!breakdown || !total) return null;
  const posPct  = total ? ((breakdown.Positive  || 0) / total) * 100 : 0;
  const negPct  = total ? ((breakdown.Negative  || 0) / total) * 100 : 0;
  const neuPct  = total ? ((breakdown.Neutral   || 0) / total) * 100 : 0;
  return (
    <div className="mt-5">
      <div className="flex justify-between text-xs font-mono text-textMuted mb-1">
        <span>Sentiment breakdown</span>
        <span>{total} reviews total</span>
      </div>
      <div className="h-2 flex rounded-full overflow-hidden bg-bg border border-gray-800">
        <div style={{ width: `${posPct}%` }} className="bg-positive transition-all duration-500" title={`Positive ${posPct.toFixed(1)}%`} />
        <div style={{ width: `${neuPct}%` }} className="bg-neutral  transition-all duration-500" title={`Neutral ${neuPct.toFixed(1)}%`} />
        <div style={{ width: `${negPct}%` }} className="bg-negative transition-all duration-500" title={`Negative ${negPct.toFixed(1)}%`} />
      </div>
      <div className="flex gap-4 mt-2 text-xs font-mono text-textMuted">
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-positive rounded-full inline-block" />{breakdown.Positive || 0} pos</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-neutral  rounded-full inline-block" />{breakdown.Neutral  || 0} neu</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-negative rounded-full inline-block" />{breakdown.Negative || 0} neg</span>
      </div>
    </div>
  );
}

const RATING_OPTIONS = ['', 'Positive', 'Negative', 'Neutral'];
const RATING_LABELS  = { '': 'All Sentiments', Positive: 'Positive Only', Negative: 'Negative Only', Neutral: 'Neutral Only' };

export default function SummaryPanel() {
  const [products, setProducts]               = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedRating, setSelectedRating]   = useState('');
  const [data, setData]                       = useState(null);
  const [loading, setLoading]                 = useState(true);
  const [error, setError]                     = useState('');

  useEffect(() => {
    getByProduct()
      .then(res => setProducts(res.map(p => p.product)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError('');
    setData(null);

    const filters = {};
    if (selectedProduct) filters.product = selectedProduct;
    if (selectedRating)  filters.rating  = selectedRating;

    getSummaryText(filters)
      .then(setData)
      .catch(() => setError('Summary unavailable'))
      .finally(() => setLoading(false));
  }, [selectedProduct, selectedRating]);

  return (
    <div className="bg-surface rounded-lg border-l-4 border-amber border-y border-r border-gray-800/80 p-6 shadow-sm font-body">
      {/* Header row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
        <h2 className="font-display font-bold text-textPrimary text-xl">AI Review Summary</h2>
        <div className="flex gap-2 flex-wrap">
          {/* Product filter */}
          <select
            id="summary-product-filter"
            value={selectedProduct}
            onChange={e => setSelectedProduct(e.target.value)}
            className="bg-bg border border-gray-800 rounded-lg p-2 text-sm text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber w-full sm:w-44 font-mono"
          >
            <option value="">All Products</option>
            {products.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          {/* Rating / sentiment filter */}
          <select
            id="summary-rating-filter"
            value={selectedRating}
            onChange={e => setSelectedRating(e.target.value)}
            className="bg-bg border border-gray-800 rounded-lg p-2 text-sm text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber w-full sm:w-40 font-mono"
          >
            {RATING_OPTIONS.map(r => (
              <option key={r} value={r}>{RATING_LABELS[r]}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <Skeleton />}

      {error && !loading && (
        <p className="text-textMuted text-sm italic">{error}</p>
      )}

      {!loading && !error && data && (
        <>
          <p className="text-textPrimary text-lg leading-relaxed italic">
            "{data.summary}"
          </p>

          {/* Context footer */}
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <span className="font-mono text-textMuted text-xs">
              Summary based on&nbsp;
              <strong className="text-textPrimary">
                {data.based_on_reviews}
              </strong>
              {selectedRating ? ` ${selectedRating.toLowerCase()}` : ''} reviews
              {data.total_reviews && data.total_reviews !== data.based_on_reviews
                ? ` (${data.total_reviews} total for product)`
                : ''}
            </span>
            {data.filter_applied && data.filter_applied !== 'All' && (
              <span className="font-mono text-xs px-2 py-0.5 rounded border border-amber/40 text-amber bg-amber/10">
                {data.filter_applied} filter active
              </span>
            )}
          </div>

          {/* Sentiment mini-bar (always shown from total reviews) */}
          <SentimentMiniBar
            breakdown={data.sentiment_breakdown}
            total={data.total_reviews}
          />
        </>
      )}
    </div>
  );
}
