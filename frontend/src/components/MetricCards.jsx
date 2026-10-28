import React from 'react';
import { Download, Printer, Code, Network, Clock, FileText } from 'lucide-react';

export default function MetricCards({ report, onExportJson, onDownloadReport }) {
  const summary = report?.summary || {};
  const totalFindings = report?.findings?.length || 0;
  const totalFiles = report?.total_files || 0;
  const totalFunctions = report?.total_functions || 0;
  const scannedAt = report?.scanned_at
    ? new Date(report.scanned_at).toLocaleString()
    : new Date().toLocaleTimeString();

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {/* Total Findings Card */}
      <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 flex flex-col justify-between shadow-sm">
        <div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Findings</div>
          <div className="text-3xl font-extrabold text-blue-400 mt-1 font-mono">{totalFindings}</div>
        </div>
        <div className="text-xs text-gray-400 mt-3 pt-3 border-t border-gray-800 flex flex-wrap gap-2">
          <span className="text-red-400 font-semibold">{summary.critical_count || 0} Crit</span> •
          <span className="text-orange-400 font-semibold">{summary.high_count || 0} High</span> •
          <span className="text-yellow-400 font-semibold">{summary.medium_count || 0} Med</span> •
          <span className="text-green-400 font-semibold">{summary.low_count || 0} Low</span>
        </div>
      </div>

      {/* Files Ingested Card */}
      <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 flex flex-col justify-between shadow-sm">
        <div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Files Ingested</div>
          <div className="text-3xl font-extrabold text-purple-400 mt-1 font-mono">{totalFiles}</div>
        </div>
        <div className="text-xs text-gray-400 mt-3 pt-3 border-t border-gray-800 flex items-center gap-1.5">
          <Code className="w-3.5 h-3.5 text-purple-400" />
          Multi-language AST Parsed
        </div>
      </div>

      {/* Functions Mapped Card */}
      <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 flex flex-col justify-between shadow-sm">
        <div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Functions Mapped</div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-1 font-mono">{totalFunctions}</div>
        </div>
        <div className="text-xs text-gray-400 mt-3 pt-3 border-t border-gray-800 flex items-center gap-1.5">
          <Network className="w-3.5 h-3.5 text-emerald-400" />
          NetworkX Nodes &amp; Edges
        </div>
      </div>

      {/* Quick Action Bar */}
      <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-4 sm:col-span-3 flex flex-wrap items-center justify-between gap-3 text-xs shadow-sm">
        <div className="flex items-center gap-2 text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          <span>Audit Scanned: <strong className="text-gray-200">{scannedAt}</strong></span>
        </div>

        <div className="flex items-center gap-2 no-print">
          <button
            onClick={onDownloadReport}
            className="bg-[#21262D] hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded border border-gray-700 flex items-center gap-1.5 transition active:scale-95"
            title="Download clean, ordered text report"
          >
            <FileText className="w-3.5 h-3.5 text-emerald-400" />
            Download Report
          </button>
          <button
            onClick={onExportJson}
            className="bg-[#21262D] hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded border border-gray-700 flex items-center gap-1.5 transition active:scale-95"
            title="Export clean, ordered JSON report"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            Export JSON
          </button>
          <button
            onClick={() => window.print()}
            className="bg-[#21262D] hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded border border-gray-700 flex items-center gap-1.5 transition active:scale-95"
          >
            <Printer className="w-3.5 h-3.5 text-gray-400" />
            Print / PDF
          </button>
        </div>
      </div>
    </div>
  );
}
