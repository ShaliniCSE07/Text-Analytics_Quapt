import React, { useEffect, useState } from 'react';
import { getSummaryText, getByProduct } from '../api/client';

function Skeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-4 bg-gray-800 rounded w-full" />
      <div className="h-4 bg-gray-800 rounded w-5/6" />
      <div className="h-4 bg-gray-800 rounded w-4/6" />
      <div className="h-3 bg-gray-800/60 rounded w-24 mt-4" />
    </div>
  );
}

export default function SummaryPanel() {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getByProduct()
      .then(res => setProducts(res.map(p => p.product)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError('');
    setData(null);

    const filters = selectedProduct ? { product: selectedProduct } : {};
    getSummaryText(filters)
      .then(setData)
      .catch(() => setError('Summary unavailable'))
      .finally(() => setLoading(false));
  }, [selectedProduct]);

  return (
    <div className="bg-surface rounded-lg border-l-4 border-amber border-y border-r border-gray-800/80 p-6 shadow-sm font-body">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
        <h2 className="font-display font-bold text-textPrimary text-xl">AI Review Summary</h2>
        <select
          value={selectedProduct}
          onChange={e => setSelectedProduct(e.target.value)}
          className="bg-bg border border-gray-800 rounded-lg p-2 text-sm text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber w-full sm:w-48 font-mono"
        >
          <option value="">All Products</option>
          {products.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
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
          <p className="font-mono text-textMuted text-xs mt-4">
            Based on {data.based_on_reviews} reviews
          </p>
        </>
      )}
    </div>
  );
}
