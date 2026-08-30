import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getReviews } from '../api/client';
import CorrectionModal from './CorrectionModal';
import ExportButton from './ExportButton';
import PageHeader from './PageHeader';

export default function ReviewsTable() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    rating: '',
    product: '',
    tag: ''
  });

  const [selectedReview, setSelectedReview] = useState(null);
  const [toastMessage, setToastMessage] = useState('');

  const fetchReviews = useCallback(async () => {
    setLoading(true);
    try {
      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '')
      );
      const data = await getReviews(activeFilters);
      setReviews(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleCorrectionSaved = async () => {
    setSelectedReview(null);
    setToastMessage('Correction saved successfully');
    setTimeout(() => setToastMessage(''), 3000);
    await fetchReviews();
  };

  const getRatingBadgeClass = (rating) => {
    switch(rating?.toLowerCase()) {
      case 'positive': return 'bg-positive/20 text-positive border border-positive/30';
      case 'negative': return 'bg-negative/20 text-negative border border-negative/30';
      case 'neutral':  return 'bg-neutral/20 text-textPrimary border border-neutral/30';
      default:         return 'bg-amber/20 text-amber border border-amber/30';
    }
  };

  return (
    <div className="space-y-6 font-body text-textPrimary">
      <PageHeader
        title="Customer Reviews"
        subtitle="Filter, inspect, export, and manually correct customer sentiment & tags"
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-surface text-amber border border-amber/40 px-4 py-2.5 rounded-lg shadow-xl z-50 transition-all font-mono text-sm">
          ✓ {toastMessage}
        </div>
      )}

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 bg-surface p-4 rounded-lg border border-gray-800/80 shadow-sm">
        <div className="flex-1">
          <label className="block text-xs font-medium text-textMuted mb-1 font-mono">Rating</label>
          <select
            name="rating"
            value={filters.rating}
            onChange={handleFilterChange}
            className="w-full bg-bg border border-gray-800 rounded p-2 text-sm text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
          >
            <option value="">All Ratings</option>
            <option value="Positive">Positive</option>
            <option value="Negative">Negative</option>
            <option value="Neutral">Neutral</option>
            <option value="language unsupported">Language Unsupported</option>
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-xs font-medium text-textMuted mb-1 font-mono">Product</label>
          <input
            name="product"
            type="text"
            value={filters.product}
            onChange={handleFilterChange}
            placeholder="Filter by product..."
            className="w-full bg-bg border border-gray-800 rounded p-2 text-sm text-textPrimary placeholder:text-gray-600 focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
          />
        </div>

        <div className="flex-1">
          <label className="block text-xs font-medium text-textMuted mb-1 font-mono font-mono">Tag</label>
          <select
            name="tag"
            value={filters.tag}
            onChange={handleFilterChange}
            className="w-full bg-bg border border-gray-800 rounded p-2 text-sm text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
          >
            <option value="">All Tags</option>
            <option value="Battery">Battery</option>
            <option value="Camera">Camera</option>
            <option value="Delivery">Delivery</option>
            <option value="Customer Support">Customer Support</option>
            <option value="Price">Price</option>
            <option value="Uncategorised">Uncategorised</option>
          </select>
        </div>

        <div className="flex-shrink-0 md:ml-auto">
          <ExportButton data={reviews} />
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-surface rounded-lg border border-gray-800/80 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-bg/60 border-b border-gray-800 text-xs font-semibold text-textMuted uppercase tracking-wider font-mono">
                <th className="p-4">Platform / ID</th>
                <th className="p-4">Product</th>
                <th className="p-4 w-1/3">Review</th>
                <th className="p-4">Rating</th>
                <th className="p-4">Tags</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {loading ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-textMuted animate-pulse">Loading reviews...</td>
                </tr>
              ) : reviews.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-12 text-center">
                    <div className="text-textMuted text-lg font-medium">No reviews match your filters.</div>
                    <p className="text-xs text-gray-500 mt-1 font-mono">Try adjusting the dropdowns or clearing search.</p>
                  </td>
                </tr>
              ) : (
                reviews.map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-800/60 hover:bg-bg/40 transition-colors bg-surface">
                    <td className="p-4 align-top">
                      <div className="font-semibold text-textPrimary">{row.Platform}</div>
                      <div className="text-xs text-textMuted font-mono mt-0.5">{row.Platform_Reference_Id}</div>
                    </td>
                    <td className="p-4 align-top font-medium text-textPrimary">{row.Product}</td>
                    <td className="p-4 align-top text-textPrimary/90 leading-relaxed">
                      {row.Review?.length > 90 ? `${row.Review.substring(0, 90)}...` : row.Review}
                    </td>
                    <td className="p-4 align-top">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold inline-block ${getRatingBadgeClass(row.Rating)}`}>
                        {row.Rating || 'None'}
                      </span>
                    </td>
                    <td className="p-4 align-top">
                      <div className="flex flex-wrap gap-1">
                        {row.Tags ? row.Tags.split('|').map((t, i) => (
                          <span key={i} className="bg-bg text-textMuted px-2 py-0.5 rounded text-xs border border-gray-800 font-mono">
                            {t.trim()}
                          </span>
                        )) : <span className="text-gray-600 text-xs italic">No tags</span>}
                      </div>
                    </td>
                    <td className="p-4 align-top text-right">
                      <div className="flex justify-end space-x-2">
                        <Link
                          to={`/reviews/${row.Platform_Reference_Id}`}
                          className="px-3 py-1.5 text-xs font-semibold text-textPrimary border border-gray-700 bg-bg/50 rounded-md hover:bg-gray-800 transition-all"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => setSelectedReview(row)}
                          className="text-xs font-semibold text-amber border border-amber/40 bg-amber/5 px-3 py-1.5 rounded-md hover:bg-amber hover:text-bg transition-all"
                        >
                          Correct
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedReview && (
        <CorrectionModal
          review={selectedReview}
          onClose={() => setSelectedReview(null)}
          onCorrectionSaved={handleCorrectionSaved}
        />
      )}
    </div>
  );
}
