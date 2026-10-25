import React, { useState, useEffect } from 'react';
import { Terminal, ShieldAlert } from 'lucide-react';

const AUDIT_STAGES = [
  'Code Ingestion',
  'AST Call Graph',
  'CodeBERT Scan',
  'FAISS RAG Search',
  'AI Remediation'
];

export default function ProgressBar({
  stage = 'Initializing audit pipeline...',
  progress = 0,
  message = ''
}) {
  const [currentStageIdx, setCurrentStageIdx] = useState(0);

  // Synchronized stage switcher:
  // Offsets stage change by 500ms (25% of 2s animation),
  // which is precisely when the laser cuts the text closed!
  useEffect(() => {
    const initialTimer = setTimeout(() => {
      setCurrentStageIdx((prev) => (prev + 1) % AUDIT_STAGES.length);

      const cycleInterval = setInterval(() => {
        setCurrentStageIdx((prev) => (prev + 1) % AUDIT_STAGES.length);
      }, 2000);

      return () => clearInterval(cycleInterval);
    }, 500);

    return () => clearTimeout(initialTimer);
  }, []);

  const displayedStage = AUDIT_STAGES[currentStageIdx];

  return (
    <section className="bg-[#111722]/95 border border-[#30363D] rounded-2xl p-8 sm:p-12 shadow-2xl relative overflow-hidden animate-fade-in no-print flex flex-col items-center justify-center">
      {/* Background Cyber Grid Accent */}
      <div className="absolute inset-0 bg-[radial-gradient(#1f293d_1px,transparent_1px)] [background-size:16px_16px] opacity-40 pointer-events-none" />

      {/* Ambient Pulsing Glow Orbs */}
      <div className="absolute -top-24 -left-24 w-72 h-72 bg-red-600/10 rounded-full blur-3xl pointer-events-none animate-pulse" />
      <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none animate-pulse" />

      {/* Main Centerpiece: Uiverse Laser Cut Stage Loader */}
      <div className="relative z-10 my-4 flex flex-col items-center justify-center min-h-[90px]">
        <div className="uiverse-loader text-center">
          <span>{displayedStage}</span>
        </div>
      </div>

      {/* Cyber Progress Track & Status */}
      <div className="relative z-10 w-full max-w-xl mt-6 space-y-3">
        {/* Progress Bar Track */}
        <div className="w-full bg-[#090D13] rounded-full h-3.5 p-0.5 border border-gray-700/80 overflow-hidden relative shadow-inner">
          <div
            className="h-full rounded-full bg-gradient-to-r from-red-500 via-rose-400 to-amber-300 transition-all duration-500 relative"
            style={{ width: `${Math.max(progress, 4)}%` }}
          >
            {/* Shimmer Light Beam Effect */}
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/40 to-transparent animate-[pulse_1.5s_infinite]" />
            <div className="absolute right-0 top-0 bottom-0 w-2.5 bg-white rounded-full shadow-lg shadow-white" />
          </div>
        </div>

        {/* Progress Metrics & Live Stage Message */}
        <div className="flex items-center justify-between text-xs font-mono text-gray-400 pt-1">
          <span className="flex items-center gap-1.5 text-gray-300 truncate max-w-[70%]">
            <Terminal className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            <span className="truncate">{message || stage || 'Auditing codebase architecture and vulnerabilities...'}</span>
          </span>
          <span className="text-sm font-bold text-rose-300 shrink-0">
            {progress}%
          </span>
        </div>
      </div>
    </section>
  );
}
