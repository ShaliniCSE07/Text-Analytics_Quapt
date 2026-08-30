import React from 'react';
import PageHeader from '../components/PageHeader';
import TrendChart from '../components/TrendChart';
import ProductComparison from '../components/ProductComparison';
import SpikeIndicator from '../components/SpikeIndicator';

export default function TrendsPage() {
  return (
    <div className="space-y-6 font-body text-textPrimary">
      <PageHeader
        title="Trends & Volatility"
        subtitle="Monitor temporal sentiment trajectories, product comparisons, and spike alerts"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TrendChart />
        <ProductComparison />
      </div>

      <SpikeIndicator />
    </div>
  );
}
