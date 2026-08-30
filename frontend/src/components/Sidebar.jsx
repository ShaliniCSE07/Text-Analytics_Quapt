import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquareText, TrendingUp, Sparkles, AlertCircle, Settings } from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Reviews', path: '/reviews', icon: MessageSquareText },
    { label: 'Trends', path: '/trends', icon: TrendingUp },
    { label: 'Insights', path: '/insights', icon: Sparkles },
    { label: 'Needs Review', path: '/needs-review', icon: AlertCircle },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 bg-bg border-r border-gray-800/80 flex flex-col z-30 font-body">
      {/* Brand Logo Header */}
      <div className="p-6 border-b border-gray-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-amber/20 border border-amber/40 flex items-center justify-center text-amber font-display font-bold text-lg">
            S
          </div>
          <div>
            <h1 className="font-display font-bold text-lg text-textPrimary leading-tight">
              Sentiment Analysis
            </h1>
            <p className="text-[10px] font-mono text-textMuted uppercase tracking-wider">Analytics Suite</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3.5 py-3 rounded-lg text-sm font-medium transition-all group ${
                  isActive
                    ? 'bg-surface text-amber border-l-4 border-amber font-semibold shadow-sm'
                    : 'text-textMuted hover:text-textPrimary hover:bg-surface/50 border-l-4 border-transparent'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={`w-5 h-5 transition-colors ${
                      isActive ? 'text-amber' : 'text-textMuted group-hover:text-textPrimary'
                    }`}
                  />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer info */}
      <div className="p-4 border-t border-gray-800/80 text-xs text-textMuted font-mono text-center">
        v2.0 • Active Engine
      </div>
    </aside>
  );
}
