import React, { useState, useMemo, useRef } from 'react';
import {
  Copy,
  Check,
  X,
  ShieldCheck,
  Columns,
  AlignJustify,
  Zap,
  ChevronDown,
  ChevronUp,
  Target,
  Sparkles
} from 'lucide-react';

/**
 * Computes Longest Common Subsequence line diff between old and new code.
 */
function computeDiff(oldCode = '', newCode = '', baseLine = 1) {
  const oldLines = oldCode ? oldCode.split('\n') : [];
  const newLines = newCode ? newCode.split('\n') : [];

  const m = oldLines.length;
  const n = newLines.length;
  const dp = Array.from({ length: m + 1 }, () => new Int32Array(n + 1));

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (oldLines[i] === newLines[j]) {
        dp[i + 1][j + 1] = dp[i][j] + 1;
      } else {
        dp[i + 1][j + 1] = Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
  }

  const rawDiff = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      rawDiff.unshift({
        type: 'unchanged',
        oldLine: oldLines[i - 1],
        newLine: newLines[j - 1],
        oldIndex: i - 1,
        newIndex: j - 1,
      });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      rawDiff.unshift({
        type: 'added',
        newLine: newLines[j - 1],
        newIndex: j - 1,
      });
      j--;
    } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
      rawDiff.unshift({
        type: 'deleted',
        oldLine: oldLines[i - 1],
        oldIndex: i - 1,
      });
      i--;
    }
  }

  // Construct paired side-by-side rows
  const rows = [];
  let k = 0;
  let delCount = 0;
  let addCount = 0;
  let firstChangedIndex = -1;

  while (k < rawDiff.length) {
    const item = rawDiff[k];
    if (item.type === 'unchanged') {
      rows.push({
        type: 'unchanged',
        left: { text: item.oldLine, lineNum: baseLine + item.oldIndex, type: 'unchanged' },
        right: { text: item.newLine, lineNum: item.newIndex + 1, type: 'unchanged' },
      });
      k++;
    } else {
      if (firstChangedIndex === -1) {
        firstChangedIndex = rows.length;
      }
      const delGroup = [];
      const addGroup = [];
      while (k < rawDiff.length && rawDiff[k].type !== 'unchanged') {
        if (rawDiff[k].type === 'deleted') {
          delGroup.push(rawDiff[k]);
          delCount++;
        } else if (rawDiff[k].type === 'added') {
          addGroup.push(rawDiff[k]);
          addCount++;
        }
        k++;
      }

      // Isolate top-level added comments from actual replacement code to avoid misaligned token diffs
      const isComment = (str) => /^\s*(?:#|\/\/|\/\*|\*)/.test(str || '');
      const cleanAdds = [];
      for (const a of addGroup) {
        if (isComment(a.newLine) && !delGroup.some((d) => isComment(d.oldLine))) {
          rows.push({
            type: 'added',
            left: null,
            right: { text: a.newLine, lineNum: 1 + a.newIndex, type: 'added' },
          });
        } else {
          cleanAdds.push(a);
        }
      }

      const maxLen = Math.max(delGroup.length, cleanAdds.length);
      for (let idx = 0; idx < maxLen; idx++) {
        const d = delGroup[idx];
        const a = cleanAdds[idx];
        rows.push({
          type: d && a ? 'modified' : d ? 'deleted' : 'added',
          left: d ? { text: d.oldLine, lineNum: baseLine + d.oldIndex, type: 'deleted' } : null,
          right: a ? { text: a.newLine, lineNum: 1 + a.newIndex, type: 'added' } : null,
        });
      }
    }
  }

  return { rows, rawDiff, delCount, addCount, firstChangedIndex };
}

/**
 * Extracts common prefix and suffix to isolate changed tokens in modified lines.
 */
function renderInlineDiff(str1, str2, isLeft) {
  if (str1 === undefined || str1 === null) return null;
  if (!str2) {
    return <span className={isLeft ? 'text-rose-200' : 'text-emerald-200'}>{str1}</span>;
  }

  let start = 0;
  while (start < str1.length && start < str2.length && str1[start] === str2[start]) {
    start++;
  }
  let end1 = str1.length - 1;
  let end2 = str2.length - 1;
  while (end1 >= start && end2 >= start && str1[end1] === str2[end2]) {
    end1--;
    end2--;
  }

  const prefix = str1.slice(0, start);
  const diffPart = isLeft ? str1.slice(start, end1 + 1) : str2.slice(start, end2 + 1);
  const suffix = isLeft ? str1.slice(end1 + 1) : str2.slice(end2 + 1);

  return (
    <>
      <span className="text-gray-300">{prefix}</span>
      {diffPart && (
        <mark
          className={`font-semibold px-1 py-0.5 rounded shadow-sm inline-block ${
            isLeft
              ? 'bg-rose-900/90 text-rose-100 ring-1 ring-rose-500/70 border border-rose-600/50'
              : 'bg-emerald-800/90 text-emerald-100 ring-1 ring-emerald-400/70 border border-emerald-500/50'
          }`}
        >
          {diffPart}
        </mark>
      )}
      <span className="text-gray-300">{suffix}</span>
    </>
  );
}

export default function DiffViewer({
  vulnerableCode = '',
  fixCode = '',
  id = '',
  lineStart = 1,
}) {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('split'); // 'split' | 'unified'
  const [focusChanges, setFocusChanges] = useState(false); // only show changed hunks
  const diffContainerRef = useRef(null);

  const { rows, rawDiff, delCount, addCount, firstChangedIndex } = useMemo(
    () => computeDiff(vulnerableCode, fixCode, lineStart || 1),
    [vulnerableCode, fixCode, lineStart]
  );

  const handleCopy = () => {
    if (!fixCode) return;
    navigator.clipboard.writeText(fixCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const jumpToFirstChange = () => {
    if (!diffContainerRef.current) return;
    const targetEl = diffContainerRef.current.querySelector('[data-first-change="true"]');
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Build display blocks when focusChanges is toggled
  const displayRows = useMemo(() => {
    if (!focusChanges) {
      return rows.map((r, i) => ({ ...r, originalIndex: i }));
    }

    const context = 2;
    const inFocus = new Array(rows.length).fill(false);
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].type !== 'unchanged') {
        const start = Math.max(0, i - context);
        const end = Math.min(rows.length - 1, i + context);
        for (let j = start; j <= end; j++) {
          inFocus[j] = true;
        }
      }
    }

    // Filter to focused rows with fold markers
    const result = [];
    let idx = 0;
    while (idx < rows.length) {
      if (inFocus[idx]) {
        result.push({ ...rows[idx], originalIndex: idx, isFold: false });
        idx++;
      } else {
        let count = 0;
        const start = idx;
        while (idx < rows.length && !inFocus[idx]) {
          count++;
          idx++;
        }
        result.push({ isFold: true, count, startIndex: start });
      }
    }
    return result;
  }, [rows, focusChanges]);

  const hasChanges = delCount > 0 || addCount > 0;
  const unchangedCount = rows.filter((r) => r.type === 'unchanged').length;
  const hasFoldableLines = unchangedCount >= 4;
  const canScrollToChange = firstChangedIndex > 3 || rows.length > 8;

  return (
    <div className="mt-3 border border-[#30363D] rounded-xl overflow-hidden bg-[#0D1117] shadow-lg">
      {/* Top Action Bar */}
      <div className="bg-[#161B22] px-4 py-2 border-b border-[#30363D] flex flex-wrap items-center justify-between gap-2 text-xs">
        {/* Left: Change statistics and Quick Jump */}
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Code Diff Analysis:
          </span>

          {hasChanges ? (
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              {delCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-800/80 font-bold">
                  -{delCount} {delCount === 1 ? 'line' : 'lines'}
                </span>
              )}
              {addCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 font-bold">
                  +{addCount} {addCount === 1 ? 'line' : 'lines'}
                </span>
              )}

              {firstChangedIndex !== -1 && canScrollToChange && (
                <button
                  onClick={jumpToFirstChange}
                  title="Auto-scroll down to the first modified line"
                  className="ml-1 px-2 py-0.5 rounded bg-blue-950/70 hover:bg-blue-900 text-blue-300 border border-blue-800/60 transition flex items-center gap-1 text-[11px]"
                >
                  <Target className="w-3 h-3 text-blue-400" />
                  Jump to Change
                </button>
              )}
            </div>
          ) : (
            <span className="text-gray-500 font-mono text-[11px]">No differences detected</span>
          )}
        </div>

        {/* Right: View Mode & Copy Controls */}
        <div className="flex items-center gap-2">
          {/* Focus Mode (Changes only vs All lines) - Only displayed when there are surrounding unchanged lines to fold */}
          {hasFoldableLines && (
            <button
              onClick={() => setFocusChanges(!focusChanges)}
              className={`px-2 py-1 rounded text-[11px] font-mono transition flex items-center gap-1 border ${
                focusChanges
                  ? 'bg-amber-950/70 text-amber-300 border-amber-800/80 font-bold'
                  : 'bg-[#21262D] text-gray-300 hover:text-white border-gray-700'
              }`}
              title={
                focusChanges
                  ? 'Folded unchanged lines; click to show full code'
                  : 'Collapse unchanged lines and isolate diffs'
              }
            >
              <Zap
                className={`w-3 h-3 ${focusChanges ? 'text-amber-400 fill-amber-400' : 'text-gray-400'}`}
              />
              {focusChanges ? 'Focus: Changes Only' : 'Show All Lines'}
            </button>
          )}

          {/* View Mode Toggle (Split vs Unified) */}
          <div className="flex items-center bg-[#090D13] p-0.5 rounded border border-gray-700 text-[11px]">
            <button
              onClick={() => setViewMode('split')}
              className={`px-2 py-0.5 rounded transition flex items-center gap-1 ${
                viewMode === 'split'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
              title="Side-by-Side Split View"
            >
              <Columns className="w-3 h-3" />
              Split
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`px-2 py-0.5 rounded transition flex items-center gap-1 ${
                viewMode === 'unified'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
              title="Single Unified Stream"
            >
              <AlignJustify className="w-3 h-3" />
              Unified
            </button>
          </div>

          {/* Copy Replacement Button */}
          <button
            onClick={handleCopy}
            className="text-[11px] px-2.5 py-1 rounded bg-emerald-950/70 hover:bg-emerald-900 text-emerald-200 border border-emerald-800/70 transition flex items-center gap-1.5 active:scale-95 font-semibold"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-300" />
                Copied Patch!
              </>
            ) : (
              <>
                <Copy className="w-3 h-3 text-emerald-400" />
                Copy Replacement
              </>
            )}
          </button>
        </div>
      </div>

      {/* Diff Workspace Container: Side-by-side comparison with zero horizontal scroll */}
      <div
        ref={diffContainerRef}
        className="max-h-[500px] overflow-y-auto select-text overflow-x-hidden"
      >
        {viewMode === 'split' ? (
          /* ========================================================= */
          /* SIDE-BY-SIDE SPLIT VIEW (TABLE-FIXED, FULL WRAP, NO SCROLL) */
          /* ========================================================= */
          <div className="w-full">
            <table className="w-full table-fixed border-collapse font-mono text-xs">
              <colgroup>
                <col className="w-12" />
                <col className="w-[calc(50%-3rem)]" />
                <col className="w-12" />
                <col className="w-[calc(50%-3rem)]" />
              </colgroup>
              <thead className="sticky top-0 z-10 bg-[#090D13] border-b border-[#30363D] text-[11px]">
                <tr>
                  <th colSpan="2" className="w-1/2 px-3 py-1.5 text-left text-rose-300 font-semibold bg-rose-950/30 border-r border-[#30363D]">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <X className="w-3.5 h-3.5 text-rose-400" />
                        Original Vulnerable Code
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 uppercase font-bold">
                        Risk Detected
                      </span>
                    </div>
                  </th>
                  <th colSpan="2" className="w-1/2 px-3 py-1.5 text-left text-emerald-300 font-semibold bg-emerald-950/30">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        Grounded Replacement Patch
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 uppercase font-bold">
                        Secure Fix
                      </span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-900/60 bg-[#090D13]">
                {displayRows.map((row, idx) => {
                  if (row.isFold) {
                    return (
                      <tr key={`fold-${row.startIndex}`}>
                        <td
                          colSpan="4"
                          onClick={() => setFocusChanges(false)}
                          className="px-4 py-1.5 bg-[#161B22]/80 hover:bg-[#21262D] cursor-pointer text-center text-gray-500 hover:text-gray-300 text-[11px] font-mono transition border-y border-[#30363D]"
                        >
                          ⋯┄⋯ @@ {row.count} unchanged lines hidden (click to expand) @@ ⋯┄⋯
                        </td>
                      </tr>
                    );
                  }

                  const isFirstChange = row.originalIndex === firstChangedIndex;
                  const isLeftChanged = row.type === 'deleted' || row.type === 'modified';
                  const isRightChanged = row.type === 'added' || row.type === 'modified';

                  return (
                    <tr
                      key={`row-${row.originalIndex ?? idx}`}
                      data-first-change={isFirstChange ? 'true' : undefined}
                      className="group hover:bg-white/[0.02]"
                    >
                      {/* Left Gutter */}
                      <td
                        className={`w-12 shrink-0 px-1.5 py-1 select-none text-right font-mono text-[11px] border-r border-gray-800/60 bg-[#0D1117]/60 align-top ${
                          isLeftChanged ? 'border-l-4 border-l-rose-500' : ''
                        }`}
                      >
                        {row.left ? (
                          <div className="flex items-center justify-end gap-1">
                            <span className={isLeftChanged ? 'text-rose-400 font-bold' : 'text-gray-600'}>
                              {row.left.lineNum}
                            </span>
                            <span
                              className={`w-3 text-center font-bold text-xs ${
                                isLeftChanged ? 'text-rose-400' : 'text-transparent'
                              }`}
                            >
                              -
                            </span>
                          </div>
                        ) : (
                          <span className="text-gray-800">•</span>
                        )}
                      </td>

                      {/* Left Code Text */}
                      <td
                        className={`px-3 py-1 border-r border-[#30363D] align-top font-mono text-xs leading-relaxed whitespace-pre-wrap break-words break-all ${
                          isLeftChanged ? 'bg-rose-950/40 text-rose-200 font-medium' : 'text-gray-400'
                        }`}
                      >
                        {row.left ? (
                          row.type === 'modified' && row.right ? (
                            renderInlineDiff(row.left.text, row.right.text, true)
                          ) : (
                            <span className={isLeftChanged ? 'text-rose-200' : 'text-gray-400'}>
                              {row.left.text}
                            </span>
                          )
                        ) : (
                          <span className="text-gray-800 select-none italic text-[11px]"> </span>
                        )}
                      </td>

                      {/* Right Gutter */}
                      <td
                        className={`w-12 shrink-0 px-1.5 py-1 select-none text-right font-mono text-[11px] border-r border-gray-800/60 bg-[#0D1117]/60 align-top ${
                          isRightChanged ? 'border-l-4 border-l-emerald-500' : ''
                        }`}
                      >
                        {row.right ? (
                          <div className="flex items-center justify-end gap-1">
                            <span className={isRightChanged ? 'text-emerald-400 font-bold' : 'text-gray-600'}>
                              {row.right.lineNum}
                            </span>
                            <span
                              className={`w-3 text-center font-bold text-xs ${
                                isRightChanged ? 'text-emerald-400' : 'text-transparent'
                              }`}
                            >
                              +
                            </span>
                          </div>
                        ) : (
                          <span className="text-gray-800">•</span>
                        )}
                      </td>

                      {/* Right Code Text */}
                      <td
                        className={`px-3 py-1 align-top font-mono text-xs leading-relaxed whitespace-pre-wrap break-words break-all ${
                          isRightChanged ? 'bg-emerald-950/40 text-emerald-200 font-medium' : 'text-gray-400'
                        }`}
                      >
                        {row.right ? (
                          row.type === 'modified' && row.left ? (
                            renderInlineDiff(row.left.text, row.right.text, false)
                          ) : (
                            <span className={isRightChanged ? 'text-emerald-200' : 'text-gray-400'}>
                              {row.right.text}
                            </span>
                          )
                        ) : (
                          <span className="text-gray-800 select-none italic text-[11px]"> </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          /* ========================================================= */
          /* UNIFIED GIT DIFF VIEW (TABLE-FIXED, FULL WRAP)           */
          /* ========================================================= */
          <div className="w-full">
            <table className="w-full table-fixed border-collapse font-mono text-xs bg-[#090D13]">
              <colgroup>
                <col className="w-12" />
                <col className="w-12" />
                <col className="w-6" />
                <col className="w-[calc(100%-7.5rem)]" />
              </colgroup>
              <tbody className="divide-y divide-gray-900/60">
                {rawDiff.map((item, idx) => {
                  const isFirst =
                    item.type !== 'unchanged' &&
                    rawDiff.findIndex((x) => x.type !== 'unchanged') === idx;

                  if (item.type === 'unchanged') {
                    return (
                      <tr key={`uni-${idx}`} className="hover:bg-white/[0.02] text-gray-400 leading-relaxed">
                        <td className="w-12 px-1 py-1 text-right text-gray-600 border-r border-gray-800/60 select-none text-[11px] align-top">
                          {(lineStart || 1) + item.oldIndex}
                        </td>
                        <td className="w-12 px-1 py-1 text-right text-gray-600 border-r border-gray-800/60 select-none text-[11px] align-top">
                          {item.newIndex + 1}
                        </td>
                        <td className="w-6 text-center text-gray-600 select-none align-top"> </td>
                        <td className="px-3 py-1 align-top font-mono whitespace-pre-wrap break-words break-all">
                          {item.oldLine}
                        </td>
                      </tr>
                    );
                  }

                  if (item.type === 'deleted') {
                    return (
                      <tr
                        key={`uni-${idx}`}
                        data-first-change={isFirst ? 'true' : undefined}
                        className="bg-rose-950/40 border-l-4 border-rose-500 text-rose-200 font-medium leading-relaxed"
                      >
                        <td className="w-12 px-1 py-1 text-right text-rose-400/80 border-r border-rose-900/60 select-none text-[11px] font-bold align-top">
                          {(lineStart || 1) + item.oldIndex}
                        </td>
                        <td className="w-12 px-1 py-1 text-right text-gray-700 border-r border-rose-900/60 select-none text-[11px] align-top">
                          -
                        </td>
                        <td className="w-6 text-center text-rose-400 font-bold select-none align-top">
                          -
                        </td>
                        <td className="px-3 py-1 align-top font-mono font-bold whitespace-pre-wrap break-words break-all">
                          {item.oldLine}
                        </td>
                      </tr>
                    );
                  }

                  if (item.type === 'added') {
                    return (
                      <tr
                        key={`uni-${idx}`}
                        data-first-change={isFirst ? 'true' : undefined}
                        className="bg-emerald-950/40 border-l-4 border-emerald-500 text-emerald-200 font-medium leading-relaxed"
                      >
                        <td className="w-12 px-1 py-1 text-right text-gray-700 border-r border-emerald-900/60 select-none text-[11px] align-top">
                          +
                        </td>
                        <td className="w-12 px-1 py-1 text-right text-emerald-400/80 border-r border-emerald-900/60 select-none text-[11px] font-bold align-top">
                          {item.newIndex + 1}
                        </td>
                        <td className="w-6 text-center text-emerald-400 font-bold select-none align-top">
                          +
                        </td>
                        <td className="px-3 py-1 align-top font-mono font-bold whitespace-pre-wrap break-words break-all">
                          {item.newLine}
                        </td>
                      </tr>
                    );
                  }

                  return null;
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer Info Legend */}
      <div className="bg-[#161B22] px-4 py-2 border-t border-[#30363D] flex items-center justify-between text-[11px] text-gray-500 font-mono">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/80 inline-block" />
            <span className="text-gray-300 font-medium">Vulnerable / Replaced Line</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/80 inline-block" />
            <span className="text-gray-300 font-medium">Grounded Fix</span>
          </span>
        </div>
        <div className="text-gray-500 text-[10px]">
          Side-by-side synchronized view
        </div>
      </div>
    </div>
  );
}
