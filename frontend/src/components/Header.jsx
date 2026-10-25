import React from 'react';
import {
  ShieldCheck,
  GraduationCap,
  Cpu,
  Share2,
  Brain,
  Zap,
  CheckCircle2
} from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-[#161B22]/95 backdrop-blur-md border border-[#30363D] rounded-xl px-5 py-3.5 shadow-lg flex flex-col lg:flex-row items-center justify-between gap-4">
      {/* Left: Brand / Logo */}
      <div className="flex items-center gap-3 self-start lg:self-center">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600/30 to-cyan-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-md shadow-blue-500/10">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
        </div>
        <div>
          <h1 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2">
            Codebase Risk Auditor
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950/80 text-blue-300 border border-blue-800/80 font-mono font-medium">
              v1.0
            </span>
          </h1>
          <p className="text-[11px] text-gray-400 font-mono">
            Autonomous Vulnerability &amp; AST Analysis
          </p>
        </div>
      </div>

      {/* Middle: Integrated Project & Architecture Navigation Bar */}
      <nav className="flex flex-wrap items-center justify-center gap-2 px-3 py-1.5 rounded-xl bg-[#090D13]/80 border border-gray-800/80 shadow-inner">
        {/* Academic Project Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-950/60 border border-blue-800/50 text-[11px] font-semibold text-blue-200">
          <GraduationCap className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>7th Sem Major Project</span>
          <span className="text-blue-400/60 font-mono text-[10px]">(2026–2027)</span>
        </div>

        <span className="text-gray-700 hidden sm:inline">|</span>

        {/* Core AI & Architectural Stack Badges */}
        <div className="flex items-center gap-1.5 flex-wrap justify-center text-[11px] font-mono">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#161B22] text-gray-300 border border-gray-700/60 hover:border-cyan-500/50 hover:text-cyan-300 transition">
            <Share2 className="w-3 h-3 text-cyan-400" />
            React Flow
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#161B22] text-gray-300 border border-gray-700/60 hover:border-emerald-500/50 hover:text-emerald-300 transition">
            <Zap className="w-3 h-3 text-emerald-400" />
            FastAPI
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#161B22] text-gray-300 border border-gray-700/60 hover:border-purple-500/50 hover:text-purple-300 transition">
            <Cpu className="w-3 h-3 text-purple-400" />
            CodeBERT
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#161B22] text-gray-300 border border-gray-700/60 hover:border-indigo-500/50 hover:text-indigo-300 transition">
            <Brain className="w-3 h-3 text-indigo-400" />
            FAISS RAG
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#161B22] text-gray-300 border border-gray-700/60 hover:border-rose-500/50 hover:text-rose-300 transition">
            <CheckCircle2 className="w-3 h-3 text-rose-400" />
            LangGraph
          </span>
        </div>
      </nav>

      {/* Right: Live Engine Ready Status */}
      <div className="flex items-center gap-2 self-end lg:self-center">
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/80 shadow-sm">
          <span className="w-2 h-2 mr-2 bg-emerald-400 rounded-full animate-ping"></span>
          Engine Ready
        </span>
      </div>
    </header>
  );
}
