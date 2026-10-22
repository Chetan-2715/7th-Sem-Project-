import React from 'react';
import { ShieldCheck, Zap, Server } from 'lucide-react';

export default function Header({ onLoadDemo, isOnline = true }) {
  return (
    <header className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 text-xl shadow-lg shadow-blue-500/10">
          <ShieldCheck className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Codebase Architecture &amp; Risk Auditor
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-900/60 text-blue-300 border border-blue-700/60 font-mono">
              React Flow • v1.0
            </span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Autonomous Neuro-Symbolic Code Review • CodeBERT 125M • Local FAISS Vector RAG • NetworkX Call Graph • LangGraph
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 self-end md:self-center">
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-950/60 text-green-400 border border-green-800/80">
          <span className="w-2 h-2 mr-2 bg-green-400 rounded-full animate-pulse"></span>
          Backend Engine Ready
        </span>
        <button
          onClick={onLoadDemo}
          className="no-print bg-[#21262D] hover:bg-gray-700 text-gray-200 text-xs font-semibold py-1.5 px-3 rounded border border-gray-700 transition flex items-center gap-1.5 shadow-sm active:scale-95"
        >
          <Zap className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
          Load Demo Sample
        </button>
      </div>
    </header>
  );
}
