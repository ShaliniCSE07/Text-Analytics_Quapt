import React, { useEffect, useState } from 'react';
import { getKeywords } from '../api/client';

export default function KeywordPanel() {
  const [keywords, setKeywords] = useState({ overall: [], positive: [], negative: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getKeywords()
      .then((data) => {
        setKeywords(data || { overall: [], positive: [], negative: [] });
      })
      .catch(() => {
        setError('Failed to load keywords.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const getMinMaxScores = (list = []) => {
    if (!list || list.length === 0) return { min: 0, max: 0 };
    const scores = list.map((item) => item.score);
    return {
      min: Math.min(...scores),
      max: Math.max(...scores),
    };
  };

  const renderTagGroup = (title, items, colorTheme) => {
    const { min, max } = getMinMaxScores(items);

    const themeStyles = {
      overall: {
        bg: 'bg-bg',
        text: 'text-textPrimary',
        border: 'border-gray-700/80',
        hover: 'hover:bg-gray-800',
      },
      positive: {
        bg: 'bg-positive/15',
        text: 'text-positive',
        border: 'border-positive/30',
        hover: 'hover:bg-positive/25',
      },
      negative: {
        bg: 'bg-negative/15',
        text: 'text-negative',
        border: 'border-negative/30',
        hover: 'hover:bg-negative/25',
      },
    };

    const style = themeStyles[colorTheme] || themeStyles.overall;

    return (
      <div className="flex flex-col bg-bg/50 p-4 rounded-lg border border-gray-800/80">
        <h3 className="font-display font-semibold text-textPrimary text-base mb-3 border-b border-gray-800 pb-2">
          {title}
        </h3>

        {(!items || items.length === 0) ? (
          <div className="text-textMuted text-xs font-body italic py-4">No keywords found.</div>
        ) : (
          <div className="flex flex-wrap gap-2 items-center">
            {items.map((item, idx) => {
              let fontSize = '0.85rem';
              let fontWeight = 400;

              if (max > min) {
                const ratio = (item.score - min) / (max - min);
                fontSize = `${(0.75 + ratio * 0.45).toFixed(2)}rem`;
                fontWeight = ratio > 0.65 ? 700 : ratio > 0.35 ? 600 : ratio > 0.15 ? 500 : 400;
              }

              return (
                <span
                  key={`${item.word}-${idx}`}
                  style={{ fontSize, fontWeight }}
                  className={`font-body inline-flex items-center px-2.5 py-1 rounded-full border transition-all duration-150 ${style.bg} ${style.text} ${style.border} ${style.hover}`}
                  title={`Score: ${item.score}`}
                >
                  {item.word}
                </span>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-surface rounded-lg border border-gray-800/80 p-6 flex flex-col shadow-sm font-body">
      <h2 className="font-display font-bold text-textPrimary text-xl mb-4">Common Themes</h2>

      {loading && (
        <div className="flex items-center justify-center min-h-[160px]">
          <div className="w-8 h-8 border-4 border-amber border-t-transparent rounded-full animate-spin opacity-40" />
        </div>
      )}

      {error && (
        <div className="flex items-center justify-center text-textMuted text-sm min-h-[100px]">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {renderTagGroup('Overall', keywords.overall, 'overall')}
          {renderTagGroup("What's Working", keywords.positive, 'positive')}
          {renderTagGroup("What's Not", keywords.negative, 'negative')}
        </div>
      )}
    </div>
  );
}
