import React, { useState, useEffect, useRef } from 'react';
import { jsPDF } from 'jspdf';
import Header from './components/Header';
import AuditInput from './components/AuditInput';
import ProgressBar from './components/ProgressBar';
import HealthScoreGauge from './components/HealthScoreGauge';
import MetricCards from './components/MetricCards';
import DependencyFlow from './components/DependencyFlow';
import FindingsTable from './components/FindingsTable';

export default function App() {
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditMode, setAuditMode] = useState('repo'); // 'repo' | 'zip' | 'file' | 'raw'
  const [taskStatus, setTaskStatus] = useState({
    taskId: null,
    stage: 'Initializing...',
    progress: 0,
    message: '',
  });
  const [report, setReport] = useState(null);
  const pollIntervalRef = useRef(null);

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Poll Audit Task Status
  const startPolling = (taskId) => {
    setIsAuditing(true);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${taskId}`);
        if (!res.ok) throw new Error(`Status check returned ${res.status}`);
        const task = await res.json();

        setTaskStatus({
          taskId,
          stage: task.current_stage || 'Processing...',
          progress: task.progress || 0,
          message: task.message || '',
        });

        if (task.status === 'COMPLETED') {
          clearInterval(pollIntervalRef.current);
          setIsAuditing(false);
          setReport(task.result);
        } else if (task.status === 'FAILED') {
          clearInterval(pollIntervalRef.current);
          setIsAuditing(false);
          alert(`Audit Failed: ${task.message}`);
        }
      } catch (err) {
        clearInterval(pollIntervalRef.current);
        setIsAuditing(false);
        console.error('Task status polling error:', err);
      }
    }, 1000);
  };

  // Start GitHub or Raw Code Audit
  const handleStartAudit = async ({ repoUrl, rawCode, filename, enableRag, enableMl }) => {
    // Clear old scan results immediately for a fresh screen
    setReport(null);
    const isRaw = Boolean(rawCode);
    setAuditMode(isRaw ? 'raw' : 'repo');
    setTaskStatus({
      taskId: null,
      stage: isRaw ? 'Parsing raw code snippet...' : 'Cloning repository & initializing pipeline...',
      progress: 5,
      message: isRaw ? `Auditing raw code (${filename || 'snippet.py'})` : `Target: ${repoUrl}`,
    });
    setIsAuditing(true);

    try {
      const payload = isRaw
        ? { raw_code: rawCode, filename: filename || 'snippet.py', enable_rag: enableRag, enable_ml: enableMl }
        : { repo_url: repoUrl, enable_rag: enableRag, enable_ml: enableMl };

      const res = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Failed to initiate audit');
      const task = await res.json();
      startPolling(task.task_id);
    } catch (err) {
      setIsAuditing(false);
      alert(`Error starting audit: ${err.message}`);
    }
  };

  // Upload ZIP or Single Code File
  const handleUploadFile = async (file, { enableRag, enableMl }) => {
    // Clear old scan results immediately for a fresh screen
    setReport(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_rag', enableRag);
    formData.append('enable_ml', enableMl);

    const isZip = file.name.toLowerCase().endsWith('.zip');
    setAuditMode(isZip ? 'zip' : 'file');
    setTaskStatus({
      taskId: null,
      stage: isZip ? 'Uploading & extracting ZIP archive...' : 'Uploading & ingesting source file...',
      progress: 10,
      message: `File: ${file.name}`,
    });
    setIsAuditing(true);

    try {
      const res = await fetch('/api/audit', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Failed to upload file');
      const task = await res.json();
      startPolling(task.task_id);
    } catch (err) {
      setIsAuditing(false);
      alert(`Error uploading file: ${err.message}`);
    }
  };

  // Helper to extract cleanly ordered vulnerability findings (sorted by file_path, then line_start)
  // Stripped of heavy AST graphs and rationale bloat, while preserving actionable replacement code.
  const getOrderedReportFindings = (findings = []) => {
    return [...findings]
      .sort((a, b) => {
        const fileA = (a.file_path || '').toLowerCase();
        const fileB = (b.file_path || '').toLowerCase();
        if (fileA !== fileB) {
          return fileA.localeCompare(fileB);
        }
        return (a.line_start || 0) - (b.line_start || 0);
      })
      .map((f) => {
        const lineStart = f.line_start ?? 1;
        const lineEnd = f.line_end ?? lineStart;
        const lineRange = lineStart === lineEnd ? `Line ${lineStart}` : `Lines ${lineStart}-${lineEnd}`;
        const funcName = f.function_name && f.function_name.trim() ? f.function_name : 'Global / Module Scope';
        const vulnName = f.cwe_id 
          ? `${f.category || 'Vulnerability'} (${f.cwe_id})` 
          : (f.category || 'Vulnerability');

        return {
          file_path: f.file_path || 'unknown',
          function: funcName,
          line_range: lineRange,
          vulnerability: vulnName,
          severity: f.severity || 'Medium',
          replacement_code: f.fix_code || f.replacement_code || '',
        };
      });
  };

  // Download Clean, Ordered Text Report (.txt)
  const handleDownloadReport = () => {
    if (!report) return;
    const ordered = getOrderedReportFindings(report.findings || []);
    const repoTitle = report.repo_name || 'Codebase';
    const timestamp = report.scanned_at
      ? new Date(report.scanned_at).toLocaleString()
      : new Date().toLocaleString();

    let content = `================================================================================\n`;
    content += `CODEBASE VULNERABILITY AUDIT REPORT\n`;
    content += `================================================================================\n`;
    content += `Target Project : ${repoTitle}\n`;
    content += `Scanned At     : ${timestamp}\n`;
    content += `Total Findings : ${ordered.length}\n`;
    content += `Health Score   : ${report.health_score ?? 0}/100\n`;
    content += `================================================================================\n\n`;
    content += `ORDERED VULNERABILITY FINDINGS:\n`;
    content += `--------------------------------------------------------------------------------\n`;

    if (ordered.length === 0) {
      content += `No vulnerabilities detected. Codebase is clean.\n`;
    } else {
      ordered.forEach((item, idx) => {
        content += `\n[${idx + 1}] File Path     : ${item.file_path}\n`;
        content += `    Function      : ${item.function}\n`;
        content += `    Line Range    : ${item.line_range}\n`;
        content += `    Vulnerability : ${item.vulnerability}\n`;
        content += `    Severity      : ${item.severity}\n`;
        if (item.replacement_code && item.replacement_code.trim()) {
          content += `    Replacement Code:\n`;
          content += `    --------------------------------------------------\n`;
          item.replacement_code.trim().replace(/\t/g, '    ').split('\n').forEach((line) => {
            content += `    ${line}\n`;
          });
          content += `    --------------------------------------------------\n`;
        } else {
          content += `    Replacement Code: [None provided]\n`;
        }
      });
    }

    content += `\n--------------------------------------------------------------------------------\n`;
    content += `================================================================================\n`;
    content += `END OF REPORT\n`;
    content += `================================================================================\n`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vulnerability-report-${report.repo_name || 'audit'}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export Clean, Ordered JSON Report (.json)
  const handleExportJson = () => {
    if (!report) return;
    const ordered = getOrderedReportFindings(report.findings || []);

    const exportData = {
      project: report.repo_name || 'Codebase Audit',
      audit_id: report.audit_id || 'result',
      scanned_at: report.scanned_at || new Date().toISOString(),
      health_score: report.health_score ?? null,
      total_findings: ordered.length,
      findings: ordered,
    };

    const jsonStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vulnerability-report-${report.repo_name || 'audit'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Download Clean, Ordered PDF Report (.pdf) formatted like the text report
  const handleDownloadPdf = () => {
    if (!report) return;
    const ordered = getOrderedReportFindings(report.findings || []);
    const repoTitle = report.repo_name || 'Codebase';
    const timestamp = report.scanned_at
      ? new Date(report.scanned_at).toLocaleString()
      : new Date().toLocaleString();

    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    const pageWidth = 210;
    const pageHeight = 297;
    const margin = 14;
    const contentWidth = pageWidth - margin * 2;
    let y = margin;

    const checkPageBreak = (neededHeight) => {
      if (y + neededHeight > pageHeight - margin - 10) {
        doc.addPage();
        y = margin + 2;
        return true;
      }
      return false;
    };

    // 1. Header Banner
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(20, 24, 33);
    doc.text('CODEBASE VULNERABILITY AUDIT REPORT', margin, y + 4);
    y += 10;

    doc.setDrawColor(200, 205, 215);
    doc.setLineWidth(0.5);
    doc.line(margin, y, margin + contentWidth, y);
    y += 5;

    // 2. Metadata Block
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(70, 80, 95);

    const leftMeta = [
      `Target Project : ${repoTitle}`,
      `Scanned At     : ${timestamp}`,
    ];
    const rightMeta = [
      `Total Findings : ${ordered.length}`,
      `Health Score   : ${report.health_score ?? 0}/100`,
    ];

    leftMeta.forEach((line, i) => {
      doc.text(line, margin, y + i * 4.5);
    });
    rightMeta.forEach((line, i) => {
      doc.text(line, margin + 110, y + i * 4.5);
    });
    y += 12;

    doc.line(margin, y, margin + contentWidth, y);
    y += 8;

    // 3. Findings Section Header
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59);
    doc.text('ORDERED VULNERABILITY FINDINGS & REPLACEMENT CODE', margin, y);
    y += 6;

    if (ordered.length === 0) {
      doc.setFont('helvetica', 'italic');
      doc.setFontSize(9.5);
      doc.setTextColor(22, 101, 52);
      doc.text('No vulnerabilities detected. Codebase is clean.', margin, y + 4);
      y += 12;
    } else {
      ordered.forEach((item, idx) => {
        checkPageBreak(32);

        // Finding Card Header
        doc.setFillColor(245, 247, 250);
        doc.setDrawColor(220, 226, 235);
        doc.rect(margin, y, contentWidth, 7, 'FD');

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9.5);
        doc.setTextColor(15, 23, 42);
        const title = `[${idx + 1}] ${item.vulnerability}`;
        const maxTitleWidth = contentWidth - 35;
        const displayTitle = doc.getTextWidth(title) > maxTitleWidth
          ? title.substring(0, Math.floor(title.length * (maxTitleWidth / doc.getTextWidth(title)))) + '...'
          : title;
        doc.text(displayTitle, margin + 3, y + 4.8);

        // Severity Badge
        const sev = (item.severity || 'Medium').toUpperCase();
        if (sev === 'CRITICAL') doc.setTextColor(185, 28, 28);
        else if (sev === 'HIGH') doc.setTextColor(194, 65, 12);
        else if (sev === 'MEDIUM') doc.setTextColor(161, 98, 7);
        else doc.setTextColor(21, 128, 61);
        doc.text(`[${sev}]`, margin + contentWidth - 25, y + 4.8);
        y += 10;

        // Metadata Details
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor(51, 65, 85);

        doc.text(`File Path   : ${item.file_path}`, margin + 2, y);
        y += 4;
        doc.text(`Function    : ${item.function}`, margin + 2, y);
        y += 4;
        doc.text(`Line Range  : ${item.line_range}`, margin + 2, y);
        y += 5;

        // Replacement Code Block
        const code = item.replacement_code;
        if (code && code.trim()) {
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(8);
          doc.setTextColor(71, 85, 105);
          doc.text('Replacement Code Patch:', margin + 2, y);
          y += 3.5;

          const rawLines = code.trim().replace(/\t/g, '    ').split('\n');
          const formattedLines = [];
          rawLines.forEach((l) => {
            const wrapped = doc.splitTextToSize(l, contentWidth - 8);
            formattedLines.push(...wrapped);
          });

          const lineHeight = 3.6;
          let currentLineIdx = 0;
          while (currentLineIdx < formattedLines.length) {
            checkPageBreak(12);

            const availableHeight = pageHeight - margin - 15 - y;
            const linesCanFit = Math.max(2, Math.floor((availableHeight - 4) / lineHeight));
            const chunk = formattedLines.slice(currentLineIdx, currentLineIdx + linesCanFit);
            const chunkHeight = chunk.length * lineHeight + 4;

            doc.setFillColor(248, 250, 252);
            doc.setDrawColor(226, 232, 240);
            doc.rect(margin, y, contentWidth, chunkHeight, 'FD');

            doc.setFont('courier', 'normal');
            doc.setFontSize(7.5);
            doc.setTextColor(30, 41, 59);

            chunk.forEach((cl, ci) => {
              doc.text(cl, margin + 4, y + 3.5 + ci * lineHeight);
            });

            y += chunkHeight + 4;
            currentLineIdx += chunk.length;
          }
        } else {
          doc.setFont('helvetica', 'italic');
          doc.setFontSize(8);
          doc.setTextColor(148, 163, 184);
          doc.text('Replacement Code: [None provided]', margin + 2, y);
          y += 5;
        }

        y += 3;
        doc.setDrawColor(235, 238, 243);
        doc.line(margin, y, margin + contentWidth, y);
        y += 5;
      });
    }

    // Footer on all pages
    const totalPages = doc.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
      doc.setPage(p);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(148, 163, 184);
      doc.text(
        'Codebase Architecture & Risk Auditor • Confidential Audit Report',
        margin,
        pageHeight - 8
      );
      doc.text(
        `Page ${p} of ${totalPages}`,
        pageWidth - margin - 18,
        pageHeight - 8
      );
    }

    doc.save(`vulnerability-report-${report.repo_name || 'audit'}.pdf`);
  };

  return (
    <div className="min-h-screen bg-[#0D1117] text-[#E6EDF3] p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Header */}
        <Header />

        {/* Audit Input Form with Interactive Navigation Tabs */}
        <AuditInput
          onStartAudit={handleStartAudit}
          onUploadFile={handleUploadFile}
          isAuditing={isAuditing}
        />

        {/* Real-time Progress Bar */}
        {isAuditing && (
          <ProgressBar
            stage={taskStatus.stage}
            progress={taskStatus.progress}
            message={taskStatus.message}
          />
        )}

        {/* Report Dashboard */}
        {report && (
          <main className="space-y-6 animate-fade-in">
            {/* Top Metrics Grid */}
            <section className="grid grid-cols-1 md:grid-cols-12 gap-4">
              <div className="md:col-span-4">
                <HealthScoreGauge score={report.health_score} />
              </div>
              <div className="md:col-span-8">
                <MetricCards
                  report={report}
                  onExportJson={handleExportJson}
                  onDownloadReport={handleDownloadReport}
                  onDownloadPdf={handleDownloadPdf}
                />
              </div>
            </section>

            {/* Interactive React Flow Dependency Call-Graph (Excluded for Raw Code Snippets) */}
            {auditMode !== 'raw' &&
              report.repo_name !== 'Raw Code Snippet' &&
              report.repo_name !== 'raw-snippet' &&
              report.dependency_graph?.nodes?.length > 1 && (
                <DependencyFlow graph={report.dependency_graph} findings={report.findings || []} />
            )}

            {/* Filterable Findings & Diff Reviewer */}
            <FindingsTable findings={report.findings || []} />
          </main>
        )}

        {/* Clean Minimal Footer */}
        <footer className="text-center text-xs text-gray-600 py-4 font-mono">
          Codebase Architecture &amp; Risk Auditor • Active Security Session
        </footer>
      </div>
    </div>
  );
}
