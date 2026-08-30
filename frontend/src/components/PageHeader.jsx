import React from 'react';

export default function PageHeader({ title, subtitle }) {
  return (
    <div className="mb-6 pb-4 border-b border-gray-800/80 font-body">
      <h1 className="text-2xl font-bold font-display text-textPrimary inline-block relative pb-2">
        {title}
        <span className="absolute bottom-0 left-0 w-12 h-0.5 bg-amber rounded-full"></span>
      </h1>
      {subtitle && <p className="text-sm text-textMuted mt-1">{subtitle}</p>}
    </div>
  );
}
