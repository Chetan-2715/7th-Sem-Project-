import React, { useMemo, useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  FileCode2,
  Cpu,
  Brain,
  Wrench,
  CheckCircle2,
  Terminal,
  Activity,
  Radio,
  Lock,
  Binary
} from 'lucide-react';

const AUDIT_STAGES = [
  {
    id: 1,
    name: 'Ingestion',
    label: 'Repo & Ingestion',
    desc: 'Unpacking files & modules',
    icon: FileCode2,
    threshold: 20
  },
  {
    id: 2,
    name: 'AST Parsing',
    label: 'AST & Call Graph',
    desc: 'Extracting function boundaries',
    icon: Binary,
    threshold: 40
  },
  {
    id: 3,
    name: 'CodeBERT Scan',
    label: 'CodeBERT Scan',
    desc: '768-dim semantic vectorization',
    icon: Cpu,
    threshold: 65
  },
  {
    id: 4,
    name: 'FAISS RAG',
    label: 'FAISS RAG Retrieval',
    desc: 'Vector grounding in CWE/OWASP',
    icon: Brain,
    threshold: 85
  },
  {
    id: 5,
    name: 'AI Remediation',
    label: 'AI Remediation',
    desc: 'Synthesizing verified fixes',
    icon: Wrench,
    threshold: 100
  }
];

export default function ProgressBar({
  stage = 'Initializing audit pipeline...',
  progress = 0,
  message = ''
}) {
  const [logHistory, setLogHistory] = useState([]);

  // Determine current active pipeline stage index (0-4)
  const activeStageIndex = useMemo(() => {
    for (let i = 0; i < AUDIT_STAGES.length; i++) {
      if (progress < AUDIT_STAGES[i].threshold) return i;
    }
    return AUDIT_STAGES.length - 1;
  }, [progress]);

  // Keep a streaming cyber telemetry log of stage updates
  useEffect(() => {
    if (!message && !stage) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now
      .getMinutes()
      .toString()
      .padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now
      .getMilliseconds()
      .toString()
      .slice(0, 2)}`;

    const newEntry = {
      time: timeStr,
      stage: stage || 'CORE',
      text: message || stage
    };

    setLogHistory((prev) => {
      // Don't add duplicate entries
      if (prev.length > 0 && prev[prev.length - 1].text === newEntry.text) {
        return prev;
      }
      return [...prev.slice(-4), newEntry];
    });
  }, [stage, message, progress]);

  return (
    <section className="bg-[#111722]/95 border border-[#30363D] rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden animate-fade-in no-print">
      {/* Background Cyber Grid Accent */}
      <div className="absolute inset-0 bg-[radial-gradient(#1f293d_1px,transparent_1px)] [background-size:16px_16px] opacity-40 pointer-events-none" />

      {/* Ambient Pulsing Glow Orbs */}
      <div className="absolute -top-24 -left-24 w-72 h-72 bg-blue-600/10 rounded-full blur-3xl pointer-events-none animate-pulse" />
      <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none animate-pulse" />

      {/* Top Header: Cyber Radar Scanner + Status & Digital Progress */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-[#21262D]">
        {/* Left: Animated Holographic Cyber Scanner Core */}
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16 shrink-0 flex items-center justify-center">
            {/* Outer Spinning Radar Ring with Tick Accents */}
            <div className="absolute inset-0 rounded-full border-2 border-dashed border-cyan-500/40 animate-[spin_8s_linear_infinite]" />

            {/* Inner Counter-Rotating Hex Ring */}
            <div className="absolute inset-1 rounded-full border border-blue-500/50 animate-[spin_4s_linear_infinite_reverse]" />

            {/* Radial Sweep Gradient (Laser Radar Beam) */}
            <div className="absolute inset-0 rounded-full bg-[conic-gradient(from_0deg,transparent_0deg,rgba(6,182,212,0.35)_300deg,transparent_360deg)] animate-[spin_3s_linear_infinite]" />

            {/* Center Core Shield Icon */}
            <div className="relative z-10 w-9 h-9 rounded-full bg-[#0D1117] border border-cyan-400/80 flex items-center justify-center shadow-lg shadow-cyan-500/30">
              <ShieldCheck className="w-5 h-5 text-cyan-400 animate-pulse" />
            </div>

            {/* Active Satellite Ping Dot */}
            <span className="absolute top-0 right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-md shadow-cyan-400 animate-ping" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-700/80 tracking-wider uppercase">
                <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                Live Audit Pipeline
              </span>
              <span className="text-[11px] text-gray-500 font-mono">
                Stage {activeStageIndex + 1} of 5
              </span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mt-1 flex items-center gap-2 tracking-tight">
              {stage}
            </h3>
            <p className="text-xs text-cyan-300/80 font-mono mt-0.5 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              {message || 'Scanning functions and computing security invariants...'}
            </p>
          </div>
        </div>

        {/* Right: Digital Percentage Readout */}
        <div className="flex items-center gap-4 self-end md:self-center">
          <div className="text-right">
            <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 block">
              Scan Progress
            </span>
            <div className="flex items-baseline justify-end gap-1 font-mono">
              <span className="text-3xl sm:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-300 drop-shadow">
                {progress}
              </span>
              <span className="text-sm font-bold text-cyan-400">%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Middle: 5-Stage Interactive Telemetry Pipeline Stepper */}
      <div className="relative z-10 py-6">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {AUDIT_STAGES.map((s, idx) => {
            const isCompleted = progress >= s.threshold;
            const isActive = idx === activeStageIndex;
            const StageIcon = s.icon;

            return (
              <div
                key={s.id}
                className={`p-3 rounded-xl border transition-all duration-300 flex flex-col justify-between ${
                  isActive
                    ? 'bg-cyan-950/40 border-cyan-500/80 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/40'
                    : isCompleted
                    ? 'bg-emerald-950/20 border-emerald-700/50 text-gray-300'
                    : 'bg-[#161B22]/60 border-gray-800/80 text-gray-500 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isActive
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/50'
                        : isCompleted
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-gray-800 text-gray-500 border border-gray-700'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <StageIcon className="w-4 h-4" />
                    )}
                  </div>
                  <span
                    className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isActive
                        ? 'bg-cyan-900/80 text-cyan-200'
                        : isCompleted
                        ? 'bg-emerald-900/60 text-emerald-300'
                        : 'bg-gray-800/80 text-gray-500'
                    }`}
                  >
                    0{s.id}
                  </span>
                </div>
                <div>
                  <h4
                    className={`text-xs font-bold leading-tight ${
                      isActive
                        ? 'text-cyan-200'
                        : isCompleted
                        ? 'text-gray-200'
                        : 'text-gray-500'
                    }`}
                  >
                    {s.label}
                  </h4>
                  <p className="text-[10px] text-gray-400/80 font-mono mt-0.5 truncate">
                    {s.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Cyber Shimmer Progress Track */}
      <div className="relative z-10">
        <div className="w-full bg-[#090D13] rounded-full h-3 p-0.5 border border-gray-700/70 overflow-hidden relative shadow-inner">
          {/* Animated Glowing Fill Bar */}
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-600 via-cyan-400 to-emerald-400 transition-all duration-500 relative"
            style={{ width: `${Math.max(progress, 3)}%` }}
          >
            {/* Shimmer Light Beam Effect */}
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/40 to-transparent animate-[pulse_1.5s_infinite]" />
            <div className="absolute right-0 top-0 bottom-0 w-2 bg-white rounded-full shadow-lg shadow-white" />
          </div>
        </div>
      </div>

      {/* Bottom: Streaming Terminal Telemetry Feed */}
      <div className="relative z-10 mt-5 bg-[#090D13]/90 border border-gray-800 rounded-xl p-3.5 font-mono text-xs shadow-inner">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-gray-800/80 text-[11px] text-gray-400">
          <span className="flex items-center gap-1.5 text-gray-300 font-semibold">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            Audit Engine Telemetry Feed
          </span>
          <span className="flex items-center gap-1 text-[10px] text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            PROCESSING
          </span>
        </div>

        <div className="space-y-1 max-h-24 overflow-hidden text-[11px]">
          {logHistory.length > 0 ? (
            logHistory.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 text-gray-300 animate-fade-in"
              >
                <span className="text-gray-500 select-none">[{item.time}]</span>
                <span className="text-cyan-400 font-semibold select-none">
                  [{item.stage.slice(0, 14)}]
                </span>
                <span className="text-gray-300 truncate">{item.text}</span>
              </div>
            ))
          ) : (
            <div className="flex items-center gap-2 text-gray-500 italic">
              <span>Connecting to background LangGraph orchestrator...</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
