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

  // Start GitHub Audit
  const handleStartAudit = async ({ repoUrl, enableRag, enableMl }) => {
    setTaskStatus({
      taskId: null,
      stage: 'Cloning repository & initializing pipeline...',
      progress: 5,
      message: `Target: ${repoUrl}`,
    });
    setIsAuditing(true);

    try {
      const res = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repoUrl,
          enable_rag: enableRag,
          enable_ml: enableMl,
        }),
      });

      if (!res.ok) throw new Error('Failed to initiate audit');
      const task = await res.json();
      startPolling(task.task_id);
    } catch (err) {
      setIsAuditing(false);
      alert(`Error starting audit: ${err.message}`);
    }
  };

  // Upload ZIP Audit
  const handleUploadZip = async (file, { enableRag, enableMl }) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_rag', enableRag);
    formData.append('enable_ml', enableMl);

    setTaskStatus({
      taskId: null,
      stage: 'Uploading and extracting ZIP archive...',
      progress: 10,
      message: `File: ${file.name}`,
    });
    setIsAuditing(true);

    try {
      const res = await fetch('/api/audit', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Failed to upload ZIP');
      const task = await res.json();
      startPolling(task.task_id);
    } catch (err) {
      setIsAuditing(false);
      alert(`Error uploading archive: ${err.message}`);
    }
  };

  // Load Offline Demo Sample
  const handleLoadDemo = async () => {
    setTaskStatus({
      taskId: 'sample-demo',
      stage: 'Loading verified sample audit report...',
      progress: 50,
      message: 'Retrieving grounded findings and call graph from backend...',
    });
    setIsAuditing(true);

    try {
      const res = await fetch('/api/sample-report');
      if (!res.ok) throw new Error('Failed to fetch sample report');
      const data = await res.json();

      setTimeout(() => {
        setIsAuditing(false);
        setReport(data);
      }, 400);
    } catch (err) {
      setIsAuditing(false);
      alert(`Error loading sample report: ${err.message}`);
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
        <Header onLoadDemo={handleLoadDemo} />

        {/* Audit Input Form */}
        <AuditInput
          onStartAudit={handleStartAudit}
          onUploadZip={handleUploadZip}
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
            <DependencyFlow graph={report.dependency_graph} />

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
