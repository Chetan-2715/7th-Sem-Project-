import React from 'react';
import { Loader2, Terminal } from 'lucide-react';

export default function ProgressBar({ stage = 'Processing...', progress = 0, message = '' }) {
  return (
    <section className="bg-[#161B22] border border-[#30363D] rounded-lg p-6 shadow-sm no-print">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
          <span className="text-sm font-semibold text-blue-400">{stage}</span>
        </div>
        <span className="text-sm font-bold text-gray-200 font-mono">{progress}%</span>
      </div>

      <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden p-0.5 border border-gray-700/60">
        <div
          className="bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="text-xs text-gray-400 mt-2 flex items-center gap-1.5 font-mono">
        <Terminal className="w-3.5 h-3.5 text-gray-500" />
        {message || 'Connecting to background audit worker...'}
      </p>
    </section>
  );
}
