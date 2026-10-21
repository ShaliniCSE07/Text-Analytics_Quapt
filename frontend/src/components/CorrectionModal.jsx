import React, { useState, useEffect } from 'react';
import { submitCorrection, getTopics } from '../api/client';

export default function CorrectionModal({ review, onClose, onCorrectionSaved }) {
  const [rating, setRating] = useState(review.Rating || '');
  const [tags, setTags] = useState(() => {
    if (!review.Tags) return [];
    return review.Tags.split('|').map(t => t.trim()).filter(Boolean);
  });
  const [correctedBy, setCorrectedBy] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [tagOptions, setTagOptions] = useState([]);

  useEffect(() => {
    getTopics()
      .then((data) => {
        if (data && typeof data === 'object') {
          const names = Object.keys(data);
          if (!names.includes('Uncategorised')) names.push('Uncategorised');
          setTagOptions(names);
        }
      })
      .catch((err) => {
        console.error(err);
        setTagOptions(['Uncategorised']);
      });
  }, []);

  const handleTagToggle = (tag) => {
    setTags(prev => 
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await submitCorrection({
        Platform_Reference_Id: review.Platform_Reference_Id,
        Corrected_Rating: rating,
        Corrected_Tags: tags.join('|'),
        Corrected_By: correctedBy
      });
      await onCorrectionSaved();
      onClose();
    } catch (err) {
      console.error(err);
      setError('Failed to save correction. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-xl shadow-2xl w-full max-w-lg overflow-hidden font-body flex flex-col max-h-[90vh] border border-gray-800 text-textPrimary">
        <div className="p-6 border-b border-gray-800 flex-shrink-0">
          <h2 className="text-xl font-display font-bold text-textPrimary">Correct Review</h2>
          <p className="text-sm text-textMuted mt-1">Platform ID: <span className="font-mono text-amber">{review.Platform_Reference_Id}</span></p>
        </div>
        
        <div className="p-6 overflow-y-auto bg-bg/40 space-y-5">
          <div className="bg-bg p-4 rounded-lg text-sm text-textPrimary italic border-l-4 border-amber">
            "{review.Review}"
          </div>

          {error && (
            <div className="text-xs text-negative bg-negative/10 border border-negative/30 p-3 rounded">
              {error}
            </div>
          )}

          <form id="correction-form" onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-textPrimary mb-1">Corrected Rating</label>
              <select 
                value={rating} 
                onChange={(e) => setRating(e.target.value)}
                className="w-full bg-bg border border-gray-800 rounded-lg p-2.5 text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber"
                required
              >
                <option value="">Select a rating...</option>
                <option value="Positive">Positive</option>
                <option value="Negative">Negative</option>
                <option value="Neutral">Neutral</option>
                <option value="language unsupported">language unsupported</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-textPrimary mb-2">Corrected Tags</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-1 bg-bg/20 rounded border border-gray-800">
                {tagOptions.map(tag => (
                  <label key={tag} title={tag} className="flex items-center space-x-2 text-xs text-textPrimary cursor-pointer bg-bg/60 p-2 rounded border border-gray-800/80 hover:border-gray-700">
                    <input 
                      type="checkbox" 
                      checked={tags.includes(tag)}
                      onChange={() => handleTagToggle(tag)}
                      className="rounded border-gray-700 bg-bg text-amber focus:ring-amber"
                    />
                    <span className="truncate">{tag}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-textPrimary mb-1">Corrected By</label>
              <input 
                type="text" 
                value={correctedBy}
                onChange={(e) => setCorrectedBy(e.target.value)}
                className="w-full bg-bg border border-gray-800 rounded-lg p-2.5 text-textPrimary focus:outline-none focus:border-amber focus:ring-1 focus:ring-amber placeholder:text-gray-600"
                placeholder="Your name"
                required
              />
            </div>
          </form>
        </div>

        <div className="p-4 border-t border-gray-800 flex justify-end space-x-3 bg-bg/80 flex-shrink-0">
          <button 
            type="button" 
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-textMuted hover:text-textPrimary transition-colors"
            disabled={submitting}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            form="correction-form"
            className="px-4 py-2 text-sm font-bold bg-amber text-bg rounded-lg hover:bg-amber/90 transition-all disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? 'Saving...' : 'Save correction'}
          </button>
        </div>
      </div>
    </div>
  );
}
