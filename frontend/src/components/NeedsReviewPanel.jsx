import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getLowConfidence } from '../api/client';
import CorrectionModal from './CorrectionModal';
import PageHeader from './PageHeader';

export default function NeedsReviewPanel({ onCorrectionSaved, showPageHeader = false }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReview, setSelectedReview] = useState(null);

  const fetchLowConfidence = async () => {
    try {
      setLoading(true);
      const data = await getLowConfidence(60);
      setReviews(data || []);
    } catch (err) {
      console.error("Failed to load low confidence reviews:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLowConfidence();
  }, []);

  const handleCorrectionSaved = async () => {
    await fetchLowConfidence();
    if (onCorrectionSaved) {
      onCorrectionSaved();
    }
  };

  const getRatingBadgeStyle = (rating) => {
    switch (rating?.toLowerCase()) {
      case 'positive':
        return 'bg-positive/20 text-positive border-positive/30';
      case 'negative':
        return 'bg-negative/20 text-negative border-negative/30';
      case 'neutral':
      default:
        return 'bg-neutral/20 text-textPrimary border-neutral/30';
    }
  };

  return (
    <div className="space-y-6 font-body text-textPrimary">
      {showPageHeader && (
        <PageHeader
          title="Needs Review"
          subtitle="Low-confidence sentiment outputs requiring manual auditor intervention"
        />
      )}

      <div className="bg-surface p-6 rounded-lg shadow-sm border border-gray-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-gray-800 gap-2">
          <div>
            <h2 className="text-lg font-bold font-display text-textPrimary">Needs Review</h2>
            <p className="text-xs text-textMuted">Reviews where the model wasn't confident</p>
          </div>
          {!loading && (
            <span className="text-xs font-mono bg-bg px-2.5 py-1 rounded text-amber border border-gray-800 self-start sm:self-auto">
              {reviews.length} flagged
            </span>
          )}
        </div>

        {loading ? (
          <div className="py-8 text-center text-sm text-textMuted animate-pulse">
            Checking confidence scores...
          </div>
        ) : reviews.length === 0 ? (
          <div className="py-8 text-center text-sm text-textMuted bg-bg/50 rounded-lg border border-gray-800">
            No reviews currently need attention
          </div>
        ) : (
          <div className="space-y-3">
            {reviews.map((r) => {
              const conf = r.Confidence || 0;
              return (
                <div
                  key={r.Platform_Reference_Id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-lg bg-bg/50 hover:bg-bg/80 border border-gray-800/80 transition-colors gap-3"
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-xs font-mono text-textMuted font-semibold">
                        {r.Product || r.Platform_Reference_Id}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getRatingBadgeStyle(
                          r.Rating
                        )}`}
                      >
                        {r.Rating}
                      </span>
                    </div>
                    <p className="text-sm text-textPrimary truncate" title={r.Review}>
                      "{r.Review}"
                    </p>
                  </div>

                  <div className="flex items-center space-x-4 flex-shrink-0">
                    <div className="w-28 text-right">
                      <div className="flex justify-between items-center text-xs font-mono text-textMuted mb-1">
                        <span>Conf</span>
                        <span className="font-semibold text-textPrimary">{conf}%</span>
                      </div>
                      <div className="w-full bg-bg h-1.5 rounded-full overflow-hidden border border-gray-800">
                        <div
                          className={`h-full rounded-full ${
                            conf < 50 ? 'bg-amber' : 'bg-gray-500'
                          }`}
                          style={{ width: `${Math.max(conf, 5)}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Link
                        to={`/reviews/${r.Platform_Reference_Id}`}
                        className="px-3.5 py-1.5 text-xs font-semibold text-textPrimary border border-gray-700 bg-bg/50 rounded-lg hover:bg-gray-800 transition-all flex items-center justify-center"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => setSelectedReview(r)}
                        className="px-3.5 py-1.5 text-xs font-bold bg-amber text-bg rounded-lg hover:bg-amber/90 transition-colors"
                      >
                        Correct
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {selectedReview && (
          <CorrectionModal
            review={selectedReview}
            onClose={() => setSelectedReview(null)}
            onCorrectionSaved={handleCorrectionSaved}
          />
        )}
      </div>
    </div>
  );
}
