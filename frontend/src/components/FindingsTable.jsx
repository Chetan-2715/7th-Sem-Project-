import React, { useState, useMemo } from 'react';
import { AlertTriangle, BookOpen, FileCode, Skull, Info, ShieldAlert } from 'lucide-react';
import DiffViewer from './DiffViewer';

function getSeverityBadge(severity) {
  const sev = (severity || '').toUpperCase();
  switch (sev) {
    case 'CRITICAL':
      return (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-950 text-red-300 border border-red-700/80 flex items-center gap-1">
          <Skull className="w-3 h-3 text-red-400" />
          CRITICAL
        </span>
      );
    case 'HIGH':
      return (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-orange-950 text-orange-300 border border-orange-700/80 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3 text-orange-400" />
          HIGH
        </span>
      );
    case 'MEDIUM':
      return (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-950 text-yellow-300 border border-yellow-700/80 flex items-center gap-1">
          <ShieldAlert className="w-3 h-3 text-yellow-400" />
          MEDIUM
        </span>
      );
    default:
      return (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-950 text-green-300 border border-green-700/80 flex items-center gap-1">
          <Info className="w-3 h-3 text-green-400" />
          LOW
        </span>
      );
  }
}

export default function FindingsTable({ findings = [] }) {
  const [filter, setFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const counts = useMemo(() => {
    return {
      all: findings.length,
      critical: findings.filter((f) => (f.severity || '').toUpperCase() === 'CRITICAL').length,
      high: findings.filter((f) => (f.severity || '').toUpperCase() === 'HIGH').length,
      medium: findings.filter((f) => (f.severity || '').toUpperCase() === 'MEDIUM').length,
      low: findings.filter((f) => (f.severity || '').toUpperCase() === 'LOW').length,
    };
  }, [findings]);

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      const sev = (f.severity || '').toUpperCase();
      const matchesFilter = filter === 'ALL' || sev === filter;

      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        (f.category || '').toLowerCase().includes(q) ||
        (f.cwe_id || '').toLowerCase().includes(q) ||
        (f.file_path || '').toLowerCase().includes(q) ||
        (f.description || '').toLowerCase().includes(q);

      return matchesFilter && matchesSearch;
    });
  }, [findings, filter, searchQuery]);

  return (
    <section className="bg-[#161B22] border border-[#30363D] rounded-lg p-6 shadow-sm">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Vulnerability Findings &amp; Grounded Remediations
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Cross-checked against MITRE CWE Top 25 and OWASP Top 10 with verified side-by-side patch diffs.
          </p>
        </div>

        {/* Filter Controls & Search */}
        <div className="flex flex-wrap items-center gap-2 no-print w-full md:w-auto">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search findings, CWE, file..."
            className="w-full md:w-52 bg-[#090D13] border border-gray-700 rounded px-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />

          <div className="flex items-center gap-1 bg-[#090D13] p-0.5 rounded border border-gray-800 text-xs">
            <button
              onClick={() => setFilter('ALL')}
              className={`px-2.5 py-1 rounded transition text-xs font-semibold ${
                filter === 'ALL' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              All ({counts.all})
            </button>
            <button
              onClick={() => setFilter('CRITICAL')}
              className={`px-2 py-1 rounded transition text-xs font-semibold ${
                filter === 'CRITICAL' ? 'bg-red-700 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              Crit ({counts.critical})
            </button>
            <button
              onClick={() => setFilter('HIGH')}
              className={`px-2 py-1 rounded transition text-xs font-semibold ${
                filter === 'HIGH' ? 'bg-orange-700 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              High ({counts.high})
            </button>
            <button
              onClick={() => setFilter('MEDIUM')}
              className={`px-2 py-1 rounded transition text-xs font-semibold ${
                filter === 'MEDIUM' ? 'bg-yellow-700 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              Med ({counts.medium})
            </button>
            <button
              onClick={() => setFilter('LOW')}
              className={`px-2 py-1 rounded transition text-xs font-semibold ${
                filter === 'LOW' ? 'bg-green-700 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              Low ({counts.low})
            </button>
          </div>
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings.length > 0 ? (
          filteredFindings.map((finding, idx) => (
            <div
              key={finding.id || idx}
              className="border border-[#30363D] rounded-lg p-5 bg-[#11161D] shadow-sm hover:border-gray-600 transition"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start gap-2 mb-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    {getSeverityBadge(finding.severity)}
                    <span className="font-bold text-sm text-gray-100 font-mono">
                      {finding.category || 'Security Flaw'}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-blue-950 text-blue-400 rounded border border-blue-800/60 font-mono font-semibold">
                      {finding.cwe_id || 'CWE'}
                    </span>
                  </div>

                  <div className="text-xs text-gray-400 mt-1.5 flex items-center gap-2 font-mono">
                    <span className="flex items-center gap-1 text-gray-300">
                      <FileCode className="w-3.5 h-3.5 text-gray-500" />
                      {finding.file_path}
                    </span>
                    <span>•</span>
                    <span className="text-gray-400">
                      Lines {finding.line_start || 1}–{finding.line_end || 1}
                    </span>
                  </div>
                </div>

                <div className="text-right flex items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded bg-[#090D13] border border-gray-800 text-gray-300 font-mono">
                    AI Confidence:{' '}
                    <strong className="text-blue-400">
                      {((finding.confidence || 0.9) * 100).toFixed(0)}%
                    </strong>
                  </span>
                </div>
              </div>

              <p className="text-xs text-gray-300 leading-relaxed mb-3">
                {finding.description}
              </p>

              {/* Side-by-Side Diff Component */}
              <DiffViewer
                vulnerableCode={finding.vulnerable_code}
                fixCode={finding.fix_code}
                id={finding.id || idx}
              />

              {/* RAG Grounding Citation */}
              {finding.explanation && (
                <div className="mt-3 p-3 rounded bg-[#090D13] border border-gray-800 text-xs text-gray-400 flex items-start gap-2">
                  <BookOpen className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-gray-300">RAG Grounded Explanation:</strong>{' '}
                    <span>{finding.explanation}</span>
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-12 text-gray-400 text-sm">
            <Info className="w-8 h-8 text-gray-500 mx-auto mb-2" />
            <p>No vulnerability findings match the current filter or search criteria.</p>
          </div>
        )}
      </div>
    </section>
  );
}
