import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import ReviewsTable from './components/ReviewsTable';
import TrendsPage from './pages/TrendsPage';
import InsightsPage from './pages/InsightsPage';
import NeedsReviewPanel from './components/NeedsReviewPanel';
import SettingsPage from './pages/SettingsPage';
import ReviewDetailPage from './pages/ReviewDetailPage';
import EmotionsPage from './pages/EmotionsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-bg text-textPrimary flex font-body">
        {/* Persistent Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <main className="pl-64 flex-1 min-h-screen p-8 bg-bg overflow-x-hidden">
          <div className="max-w-6xl mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/emotions" element={<EmotionsPage />} />
              <Route path="/reviews" element={<ReviewsTable />} />
              <Route path="/trends" element={<TrendsPage />} />
              <Route path="/insights" element={<InsightsPage />} />
              <Route path="/needs-review" element={<NeedsReviewPanel showPageHeader={true} />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/reviews/:id" element={<ReviewDetailPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}
