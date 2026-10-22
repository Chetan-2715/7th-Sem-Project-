import React from 'react';
import { CheckCircle2, AlertTriangle, Skull } from 'lucide-react';

export default function HealthScoreGauge({ score = 100 }) {
  const normalizedScore = Math.max(0, Math.min(100, Math.round(score)));
  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ~314.159
  const offset = circumference - (normalizedScore / 100) * circumference;

  let strokeColor = '#3FB950'; // Green
  let verdictText = 'Low Risk • Production Ready';
  let verdictClass = 'bg-green-950 text-green-400 border-green-800';
  let Icon = CheckCircle2;

  if (normalizedScore < 60) {
    strokeColor = '#F85149'; // Red
    verdictText = 'High Risk • Critical Flaws';
    verdictClass = 'bg-red-950 text-red-400 border-red-800';
    Icon = Skull;
  } else if (normalizedScore < 80) {
    strokeColor = '#D29922'; // Yellow/Amber
    verdictText = 'Moderate Risk • Patch Needed';
    verdictClass = 'bg-yellow-950 text-yellow-400 border-yellow-800';
    Icon = AlertTriangle;
  }

  return (
    <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-6 flex flex-col items-center justify-center text-center shadow-sm">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
        Security Health Score
      </div>

      <div className="relative w-36 h-36 flex items-center justify-center">
        <svg className="w-36 h-36" viewBox="0 0 120 120">
          <circle
            className="gauge-circle-bg"
            cx="60"
            cy="60"
            r={radius}
          />
          <circle
            className="gauge-circle-progress"
            cx="60"
            cy="60"
            r={radius}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            stroke={strokeColor}
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-4xl font-black text-white font-mono tracking-tight">
            {normalizedScore}
          </span>
          <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">
            out of 100
          </span>
        </div>
      </div>

      <div className={`text-xs font-semibold mt-3 px-3 py-1 rounded-full border flex items-center gap-1.5 ${verdictClass}`}>
        <Icon className="w-3.5 h-3.5" />
        {verdictText}
      </div>
    </div>
  );
}
