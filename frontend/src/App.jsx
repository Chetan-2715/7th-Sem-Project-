import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import AuditInput from './components/AuditInput';
import ProgressBar from './components/ProgressBar';
import HealthScoreGauge from './components/HealthScoreGauge';
import MetricCards from './components/MetricCards';
import DependencyFlow from './components/DependencyFlow';
import FindingsTable from './components/FindingsTable';

export default function App() {
  const [isAuditing, setIsAuditing] = useState(false);
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
    const isRaw = Boolean(rawCode);
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
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_rag', enableRag);
    formData.append('enable_ml', enableMl);

    const isZip = file.name.toLowerCase().endsWith('.zip');
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

  // Export JSON Report
  const handleExportJson = () => {
    if (!report) return;
    const jsonStr = JSON.stringify(report, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-report-${report.audit_id || 'result'}.json`;
    a.click();
    URL.revokeObjectURL(url);
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
                <MetricCards report={report} onExportJson={handleExportJson} />
              </div>
            </section>

            {/* Interactive React Flow Dependency Call-Graph */}
            <DependencyFlow graph={report.dependency_graph} findings={report.findings || []} />

            {/* Filterable Findings & Diff Reviewer */}
            <FindingsTable findings={report.findings || []} />
          </main>
        )}

        {/* Footer */}
        <footer className="text-center text-xs text-gray-500 py-6 border-t border-gray-800">
          Codebase Architecture &amp; Risk Auditor • 7th Semester Major Project (Academic Year 2026–2027) • Built with React, React Flow, FastAPI, CodeBERT, FAISS &amp; LangGraph
        </footer>
      </div>
    </div>
  );
}
