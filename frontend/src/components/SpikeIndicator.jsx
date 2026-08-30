import React, { useEffect, useState } from 'react';
import { getSpikeCheck } from '../api/client';

export default function SpikeIndicator() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSpikeCheck = async () => {
      try {
        setLoading(true);
        const res = await getSpikeCheck();
        setData(res || []);
      } catch (err) {
        console.error("Failed to load spike check data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSpikeCheck();
  }, []);

  return (
    <div className="bg-surface p-6 rounded-lg shadow-sm border border-gray-800/80 font-body text-textPrimary">
      <div className="pb-4 mb-4 border-b border-gray-800">
        <h2 className="text-lg font-bold font-display text-textPrimary">Negative Trend Spikes</h2>
        <p className="text-xs text-textMuted">Detecting sudden spikes in negative sentiment by product</p>
      </div>

      {loading ? (
        <div className="py-6 text-center text-sm text-textMuted animate-pulse">
          Calculating trend changes...
        </div>
      ) : data.length === 0 ? (
        <div className="py-6 text-center text-sm text-textMuted bg-bg/50 rounded-lg border border-gray-800">
          Not enough historical data yet to detect trends
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {data.map((item) => {
            const isIncrease = item.change > 0;
            const isDecrease = item.change < 0;

            return (
              <div
                key={item.product}
                className={`p-4 rounded-lg bg-bg/50 border ${
                  item.is_spike
                    ? 'border-l-4 border-l-amber border-gray-800 bg-amber/5'
                    : 'border-gray-800/80'
                } flex flex-col justify-between space-y-3`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-sm text-textPrimary">{item.product}</h3>
                    {item.is_spike && (
                      <span className="inline-block mt-1 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber/20 text-amber border border-amber/40">
                        Needs attention
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-1 font-mono text-sm font-bold">
                    {isIncrease && (
                      <span className="text-negative flex items-center">
                        <svg className="w-4 h-4 mr-0.5 fill-current" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                        </svg>
                        +{item.change}%
                      </span>
                    )}
                    {isDecrease && (
                      <span className="text-positive flex items-center">
                        <svg className="w-4 h-4 mr-0.5 fill-current" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M12 13a1 1 0 100 2h5a1 1 0 001-1V9a1 1 0 10-2 0v2.586l-4.293-4.293a1 1 0 00-1.414 0L8 9.586 3.707 5.293a1 1 0 00-1.414 1.414l5 5a1 1 0 001.414 0L11 9.414 14.586 13H12z" clipRule="evenodd" />
                        </svg>
                        {item.change}%
                      </span>
                    )}
                    {!isIncrease && !isDecrease && (
                      <span className="text-textMuted">0%</span>
                    )}
                  </div>
                </div>

                <div className="text-xs font-mono text-textMuted bg-bg p-2 rounded-md border border-gray-800 flex justify-between">
                  <span>Older: {item.older_negative_pct}%</span>
                  <span>→</span>
                  <span>Newer: {item.newer_negative_pct}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
