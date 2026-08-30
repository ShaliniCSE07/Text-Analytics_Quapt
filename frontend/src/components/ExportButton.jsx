import React from 'react';
import * as XLSX from 'xlsx';

export default function ExportButton({ data, filename = 'reviews_export.xlsx' }) {
  const handleExport = () => {
    if (!data || data.length === 0) return;

    const exportData = data.map(item => ({
      Platform: item.Platform,
      Product: item.Product,
      Review: item.Review,
      Rating: item.Rating,
      Tags: item.Tags,
      Platform_Reference_Id: item.Platform_Reference_Id
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    
    const columnWidths = [
      { wch: 15 },
      { wch: 20 },
      { wch: 80 },
      { wch: 12 },
      { wch: 30 },
      { wch: 20 }
    ];
    worksheet['!cols'] = columnWidths;

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Reviews');

    XLSX.writeFile(workbook, filename);
  };

  return (
    <button
      onClick={handleExport}
      disabled={!data || data.length === 0}
      className="px-4 py-2 text-sm font-medium bg-bg text-textPrimary border border-gray-800 rounded-lg hover:border-amber hover:text-amber transition-colors disabled:opacity-50 flex items-center justify-center space-x-2 w-full md:w-auto h-[38px] font-mono"
      title="Export to Excel"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>Export Excel</span>
    </button>
  );
}
