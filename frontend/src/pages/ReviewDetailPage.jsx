import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { getReviewDetail } from '../api/client';
import CorrectionModal from '../components/CorrectionModal';
import { ArrowLeft } from 'lucide-react';

export default function ReviewDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const result = await getReviewDetail(id);
      setData(result);
    } catch (err) {
      console.error(err);
      setError('Failed to load review details. It may not exist.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

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

  const getEmotionBadgeStyle = (emotion) => {
    switch (emotion?.toLowerCase()) {
      case 'delight':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'frustration':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'anger':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'disappointment':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40';
      case 'anxiety':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      case 'confusion':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'uncertain':
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-textMuted animate-pulse font-body">Loading review details...</div>;
  }

  if (error || !data) {
    return (
      <div className="font-body space-y-4">
        <Link to="/reviews" className="inline-flex items-center text-sm text-amber hover:text-amber/80 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Reviews
        </Link>
        <div className="bg-surface p-6 rounded-lg text-negative border-l-4 border-negative">
          {error || 'Review not found.'}
        </div>
      </div>
    );
  }

  const { review, correction_history } = data;
  const emotionScores = review.Emotion_Scores_Dict || {};

  return (
    <div className="space-y-6 font-body text-textPrimary">
      <div>
        <Link to="/reviews" className="inline-flex items-center text-sm text-textMuted hover:text-textPrimary transition-colors mb-4 font-medium">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Reviews
        </Link>
        <PageHeader
          title="Review Detail"
          subtitle={`Platform ID: ${id}`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Review Info & Emotion Analysis */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-surface rounded-lg shadow-sm border border-gray-800/80 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="font-bold text-lg text-textPrimary">{review.Platform}</span>
                <span className="text-textMuted text-sm px-2 py-1 bg-bg rounded-md border border-gray-800 font-mono">
                  {review.Product}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRatingBadgeStyle(review.Rating)}`}>
                  {review.Rating || 'None'}
                </span>
                {review.Emotion && (
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getEmotionBadgeStyle(review.Emotion)}`}>
                    {review.Emotion}
                  </span>
                )}
              </div>
            </div>
            
            <div className="bg-bg p-5 rounded-lg border-l-4 border-amber italic text-lg leading-relaxed text-textPrimary mb-6">
              "{review.Review}"
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-xs font-mono text-textMuted">Tags</div>
                <div className="flex flex-wrap gap-2">
                  {review.Tags ? review.Tags.split('|').map((t, i) => (
                    <span key={i} className="bg-bg text-textPrimary px-2.5 py-1 rounded-md text-sm border border-gray-800 font-medium">
                      {t.trim()}
                    </span>
                  )) : <span className="text-gray-600 text-sm italic">No tags</span>}
                </div>
              </div>
              
              <div className="space-y-1 text-right">
                <div className="text-xs font-mono text-textMuted">Sentiment Confidence</div>
                <div className="text-lg font-mono font-bold text-amber">{review.Confidence || 0}%</div>
              </div>
            </div>
          </div>

          {/* Emotion Analysis Breakdown Card */}
          <div className="bg-surface rounded-lg shadow-sm border border-gray-800/80 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div>
                <h3 className="font-display font-bold text-base text-textPrimary">Emotion Classification</h3>
                <p className="text-xs text-textMuted">RoBERTa GoEmotions mapped to 6 business categories (ICXBee)</p>
              </div>
              <div className="text-right">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getEmotionBadgeStyle(review.Emotion)}`}>
                  {review.Emotion || 'Uncertain'}
                </span>
                <span className="ml-2 font-mono text-xs text-amber font-semibold">
                  {review.Emotion_Confidence ? `${review.Emotion_Confidence}%` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Mapped Score Bars */}
            <div className="space-y-2.5 pt-2">
              <div className="text-xs font-mono text-textMuted uppercase tracking-wider">Mapped Category Scores</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { name: 'Delight', color: 'bg-emerald-500', barText: 'text-emerald-400' },
                  { name: 'Frustration', color: 'bg-amber-500', barText: 'text-amber-400' },
                  { name: 'Disappointment', color: 'bg-indigo-500', barText: 'text-indigo-400' },
                  { name: 'Anxiety', color: 'bg-purple-500', barText: 'text-purple-400' },
                  { name: 'Confusion', color: 'bg-yellow-500', barText: 'text-yellow-400' },
                  { name: 'Anger', color: 'bg-red-500', barText: 'text-red-400' },
                ].map((emo) => {
                  const score = emotionScores[emo.name] ?? 0;
                  const pct = Math.round(score * 100);
                  const isPrimary = review.Emotion === emo.name;
                  return (
                    <div key={emo.name} className={`p-2.5 rounded-lg bg-bg border ${isPrimary ? 'border-gray-700 ring-1 ring-amber/30' : 'border-gray-800/70'}`}>
                      <div className="flex justify-between items-center text-xs mb-1.5">
                        <span className={`font-semibold ${isPrimary ? emo.barText : 'text-textPrimary'}`}>
                          {emo.name} {isPrimary && '★'}
                        </span>
                        <span className="font-mono text-textMuted">{pct}%</span>
                      </div>
                      <div className="w-full bg-gray-900 h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${emo.color} transition-all duration-500 rounded-full`}
                          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Explainability & Model Info */}
            <div className="mt-4 p-3 bg-bg/60 rounded-md border border-gray-800 text-xs text-textMuted space-y-1">
              <div className="flex justify-between font-mono text-[11px] text-gray-500">
                <span>Model: {review.Emotion_Model || 'SamLowe/roberta-base-go_emotions'}</span>
                <span>Rule: Max Source Score per Category</span>
              </div>
              <p className="italic text-gray-400 leading-relaxed pt-1">
                Notice: Model-generated scores represent statistical lexical associations detected in the text, not certified human emotional states.
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowCorrectionModal(true)}
            className="w-full sm:w-auto px-6 py-2.5 text-sm font-bold bg-amber text-bg rounded-lg hover:bg-amber/90 transition-colors shadow-sm"
          >
            Correct this review
          </button>
        </div>

        {/* Right Column: Correction History */}
        <div className="space-y-6">
          <div className="bg-surface rounded-lg shadow-sm border border-gray-800/80 p-6 h-full">
            <h3 className="font-display font-bold text-lg text-textPrimary mb-4 pb-2 border-b border-gray-800">
              Correction History
            </h3>
            
            {!correction_history || correction_history.length === 0 ? (
              <div className="text-center p-6 bg-bg/50 rounded-lg border border-gray-800 text-textMuted text-sm">
                No corrections made yet
              </div>
            ) : (
              <div className="space-y-4">
                {correction_history.map((corr, idx) => (
                  <div key={idx} className="relative pl-4 border-l-2 border-gray-800 pb-2 last:pb-0">
                    <div className="absolute w-2.5 h-2.5 bg-amber rounded-full -left-[5px] top-1.5 ring-4 ring-surface"></div>
                    <div className="text-xs text-textMuted mb-1 font-mono">
                      {corr.Corrected_At}
                    </div>
                    <div className="bg-bg p-3 rounded-lg border border-gray-800/80 shadow-sm space-y-1.5">
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-semibold text-textPrimary">{corr.Corrected_By}</span>
                      </div>
                      <div className="text-sm text-textPrimary">
                        <span className="text-textMuted mr-1">Rating:</span> 
                        <span className="font-medium text-amber">{corr.Corrected_Rating || 'Unchanged'}</span>
                      </div>
                      <div className="text-sm text-textPrimary">
                        <span className="text-textMuted mr-1">Tags:</span> 
                        <span className="font-medium text-amber">{corr.Corrected_Tags || 'Unchanged'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {showCorrectionModal && (
        <CorrectionModal
          review={review}
          onClose={() => setShowCorrectionModal(false)}
          onCorrectionSaved={() => fetchDetail()}
        />
      )}
    </div>
  );
}
