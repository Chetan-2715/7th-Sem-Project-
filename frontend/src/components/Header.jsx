import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-[#161B22]/95 backdrop-blur-md border border-[#30363D] rounded-xl px-6 py-4 shadow-lg flex items-center justify-between">
      {/* Brand / Logo */}
      <div className="flex items-center gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600/30 to-cyan-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-md shadow-blue-500/10">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            Codebase Risk Auditor
          </h1>
          <p className="text-xs text-gray-400 font-mono">
            Autonomous Vulnerability &amp; AST Analysis
          </p>
        </div>
      </div>
    </header>
  );
}
