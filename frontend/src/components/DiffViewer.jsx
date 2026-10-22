import React, { useState } from 'react';
import { Copy, Check, X, ShieldCheck } from 'lucide-react';

export default function DiffViewer({ vulnerableCode = '', fixCode = '', id = '' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!fixCode) return;
    navigator.clipboard.writeText(fixCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
      {/* Left: Original Vulnerable Code */}
      <div className="border border-red-900/50 rounded-md overflow-hidden bg-[#0A0505]">
        <div className="bg-red-950/40 px-3 py-1.5 border-b border-red-900/50 flex justify-between items-center text-xs text-red-300 font-semibold">
          <span className="flex items-center gap-1.5">
            <X className="w-3.5 h-3.5 text-red-400" />
            Original Vulnerable Code
          </span>
          <span className="text-[10px] uppercase font-mono text-red-400 bg-red-950 px-1.5 py-0.5 rounded border border-red-800">
            Risk Detected
          </span>
        </div>
        <pre className="p-3 text-xs text-red-200 font-mono overflow-x-auto whitespace-pre leading-relaxed">
          <code>{vulnerableCode || '// No snippet available'}</code>
        </pre>
      </div>

      {/* Right: Synthesized Grounded Fix */}
      <div className="border border-green-900/50 rounded-md overflow-hidden bg-[#050A06]">
        <div className="bg-green-950/40 px-3 py-1.5 border-b border-green-900/50 flex justify-between items-center text-xs text-green-300 font-semibold">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-green-400" />
            Grounded Replacement Patch
          </span>
          <button
            onClick={handleCopy}
            className="text-[11px] px-2 py-0.5 rounded bg-green-900/60 hover:bg-green-800 text-green-200 border border-green-700/60 transition flex items-center gap-1 active:scale-95"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-green-300" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                Copy Patch
              </>
            )}
          </button>
        </div>
        <pre className="p-3 text-xs text-green-200 font-mono overflow-x-auto whitespace-pre leading-relaxed">
          <code>{fixCode || '// No fix synthesized'}</code>
        </pre>
      </div>
    </div>
  );
}
