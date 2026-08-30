import React from 'react';
import PageHeader from '../components/PageHeader';
import SummaryPanel from '../components/SummaryPanel';
import KeywordPanel from '../components/KeywordPanel';

export default function InsightsPage() {
  return (
    <div className="space-y-6 font-body text-textPrimary">
      <PageHeader
        title="AI Insights & Themes"
        subtitle="Automated review summaries and comparative distinctive keyword extraction"
      />

      <SummaryPanel />
      <KeywordPanel />
    </div>
  );
}
