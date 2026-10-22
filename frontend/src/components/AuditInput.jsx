import React, { useState } from 'react';
import { Search, Play, FileArchive, Github, Loader2 } from 'lucide-react';

export default function AuditInput({ onStartAudit, onUploadZip, isAuditing }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [zipFileName, setZipFileName] = useState('');
  const [enableRag, setEnableRag] = useState(true);
  const [enableMl, setEnableMl] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      alert('Please enter a public GitHub repository URL or click Load Demo Sample!');
      return;
    }
    onStartAudit({ repoUrl: repoUrl.trim(), enableRag, enableMl });
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setZipFileName(file.name);
    onUploadZip(file, { enableRag, enableMl });
  };

  return (
    <section className="bg-[#161B22] border border-[#30363D] rounded-lg p-6 shadow-sm no-print">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
          <Search className="w-4 h-4 text-blue-400" />
          Initiate Repository Scan
        </h2>
        <span className="text-xs text-gray-400">Supports Public Git Repositories and Local .ZIP Archives</span>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-4">
        <div className="md:col-span-8">
          <label className="block text-xs font-medium text-gray-400 mb-1">Public GitHub Repository URL</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
              <Github className="w-4 h-4" />
            </span>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/octocat/Hello-World.git"
              className="w-full bg-[#090D13] border border-gray-700 rounded-md pl-10 pr-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition font-mono"
            />
          </div>
        </div>

        <div className="md:col-span-4 flex items-end">
          <button
            type="submit"
            disabled={isAuditing}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-70 text-white font-semibold py-2.5 px-4 rounded-md text-sm transition flex items-center justify-center gap-2 shadow-md shadow-blue-600/20 active:scale-95"
          >
            {isAuditing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Auditing Pipeline...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                Start Audit
              </>
            )}
          </button>
        </div>
      </form>

      {/* Upload ZIP Option & Options */}
      <div className="mt-4 pt-4 border-t border-gray-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer bg-[#21262D] hover:bg-gray-700 px-3 py-1.5 rounded border border-gray-700 text-gray-300 transition">
            <FileArchive className="w-4 h-4 text-yellow-400" />
            <span>Upload .ZIP Archive</span>
            <input type="file" accept=".zip" className="hidden" onChange={handleFileChange} />
          </label>
          <span className="text-gray-400 italic font-mono text-[11px]">
            {zipFileName || 'No file selected'}
          </span>
        </div>

        <div className="flex items-center gap-4 text-gray-400">
          <label className="flex items-center gap-1.5 cursor-pointer hover:text-gray-200 transition">
            <input
              type="checkbox"
              checked={enableRag}
              onChange={(e) => setEnableRag(e.target.checked)}
              className="rounded bg-gray-900 border-gray-700 text-blue-600 focus:ring-0"
            />
            <span>Ground via FAISS RAG</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer hover:text-gray-200 transition">
            <input
              type="checkbox"
              checked={enableMl}
              onChange={(e) => setEnableMl(e.target.checked)}
              className="rounded bg-gray-900 border-gray-700 text-blue-600 focus:ring-0"
            />
            <span>CodeBERT 125M Scanner</span>
          </label>
        </div>
      </div>
    </section>
  );
}
