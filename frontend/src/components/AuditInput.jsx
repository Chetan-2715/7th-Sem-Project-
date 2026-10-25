import React, { useState, useRef } from 'react';
import {
  Github,
  UploadCloud,
  Code2,
  Play,
  Loader2,
  FileCode,
  X,
  FileCheck,
  CheckCircle2
} from 'lucide-react';

export default function AuditInput({ onStartAudit, onUploadFile, isAuditing }) {
  const [activeTab, setActiveTab] = useState('github'); // 'github' | 'upload' | 'raw'
  const [repoUrl, setRepoUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [rawCode, setRawCode] = useState('');
  const [filename, setFilename] = useState('snippet.py');
  const [filenameCustomized, setFilenameCustomized] = useState(false);
  const [detectedLang, setDetectedLang] = useState('Python');
  const fileInputRef = useRef(null);

  const handleRawCodeChange = (e) => {
    const code = e.target.value;
    setRawCode(code);

    if (!filenameCustomized && code.trim().length > 0) {
      if (
        /\b(function|const|let|var)\s+[a-zA-Z0-9_]+/.test(code) ||
        /\b(document\.|window\.|console\.log|\.innerHTML|\.textContent)/.test(code) ||
        /=>\s*\{?/.test(code)
      ) {
        setFilename('snippet.js');
        setDetectedLang('JavaScript');
      } else if (
        /#include\s*[<"]|\bint\s+main\s*\(|\bprintf\s*\(|\bstd::|\bmalloc\s*\(/.test(code)
      ) {
        setFilename('snippet.cpp');
        setDetectedLang('C / C++');
      } else if (
        /\bpublic\s+class\s+[a-zA-Z0-9_]+|\bSystem\.out\.print/.test(code)
      ) {
        setFilename('snippet.java');
        setDetectedLang('Java');
      } else if (
        /^\s*(def|import|from|class)\s+[a-zA-Z0-9_]+/m.test(code) ||
        /\belif\b|\bprint\s*\(/.test(code)
      ) {
        setFilename('snippet.py');
        setDetectedLang('Python');
      }
    }
  };

  // Tab 1: Submit GitHub Link
  const handleGithubSubmit = (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      alert('Please enter a public GitHub repository URL!');
      return;
    }
    onStartAudit({ repoUrl: repoUrl.trim(), enableRag: true, enableMl: true });
  };

  // Tab 2: Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleUploadSubmit = () => {
    if (!selectedFile) {
      alert('Please select or drop a file to audit!');
      return;
    }
    onUploadFile(selectedFile, { enableRag: true, enableMl: true });
  };

  // Tab 3: Submit Raw Code
  const handleRawCodeSubmit = () => {
    if (!rawCode.trim()) {
      alert('Please paste code into the box to audit!');
      return;
    }
    onStartAudit({
      rawCode: rawCode,
      filename: filename.trim() || 'snippet.py',
      enableRag: true,
      enableMl: true
    });
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <section className="bg-[#161B22] border border-[#30363D] rounded-xl p-6 shadow-sm no-print">
      {/* Top Full-Width Segmented Tab Bar: Git | ZIP | Code */}
      <div className="grid grid-cols-3 p-1.5 bg-[#090D13] border border-gray-800 rounded-xl mb-6 shadow-inner">
        {/* Tab 1: Git */}
        <button
          type="button"
          onClick={() => setActiveTab('github')}
          className={`relative flex items-center justify-center gap-2.5 py-2.5 rounded-lg text-sm font-bold tracking-wide transition-all duration-300 ease-out select-none ${
            activeTab === 'github'
              ? 'bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-600/30 border border-blue-400/40 scale-[1.01]'
              : 'text-gray-400 hover:text-gray-200 hover:bg-[#161B22]/70 border border-transparent'
          }`}
        >
          <Github className={`w-4 h-4 transition-transform duration-300 ${activeTab === 'github' ? 'scale-110 text-white' : 'text-gray-400'}`} />
          <span>Git</span>
        </button>

        {/* Tab 2: ZIP */}
        <button
          type="button"
          onClick={() => setActiveTab('upload')}
          className={`relative flex items-center justify-center gap-2.5 py-2.5 rounded-lg text-sm font-bold tracking-wide transition-all duration-300 ease-out select-none ${
            activeTab === 'upload'
              ? 'bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-600/30 border border-blue-400/40 scale-[1.01]'
              : 'text-gray-400 hover:text-gray-200 hover:bg-[#161B22]/70 border border-transparent'
          }`}
        >
          <UploadCloud className={`w-4 h-4 transition-transform duration-300 ${activeTab === 'upload' ? 'scale-110 text-white' : 'text-gray-400'}`} />
          <span>ZIP</span>
        </button>

        {/* Tab 3: Code */}
        <button
          type="button"
          onClick={() => setActiveTab('raw')}
          className={`relative flex items-center justify-center gap-2.5 py-2.5 rounded-lg text-sm font-bold tracking-wide transition-all duration-300 ease-out select-none ${
            activeTab === 'raw'
              ? 'bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-600/30 border border-blue-400/40 scale-[1.01]'
              : 'text-gray-400 hover:text-gray-200 hover:bg-[#161B22]/70 border border-transparent'
          }`}
        >
          <Code2 className={`w-4 h-4 transition-transform duration-300 ${activeTab === 'raw' ? 'scale-110 text-white' : 'text-gray-400'}`} />
          <span>Code</span>
        </button>
      </div>

      {/* Tab 1: GitHub Repository Link */}
      {activeTab === 'github' && (
        <form onSubmit={handleGithubSubmit} className="space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div className="md:col-span-9">
              <label className="block text-xs font-medium text-gray-400 mb-1.5">
                Public GitHub Repository URL
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-gray-500">
                  <Github className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/project.git"
                  className="w-full bg-[#090D13] border border-gray-700 rounded-md pl-10 pr-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition font-mono"
                />
              </div>
            </div>

            <div className="md:col-span-3 flex items-end">
              <button
                type="submit"
                disabled={isAuditing}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-70 text-white font-semibold py-2.5 px-4 rounded-md text-sm transition flex items-center justify-center gap-2 shadow-md shadow-blue-600/20 active:scale-95"
              >
                {isAuditing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Auditing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    Start Audit
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Tab 2: Drag and Drop Box for ZIP or Single Code File */}
      {activeTab === 'upload' && (
        <div className="space-y-4 animate-fade-in">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-blue-500 bg-blue-950/20 shadow-inner'
                : 'border-gray-700 hover:border-gray-500 bg-[#090D13]/60 hover:bg-[#090D13]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,.py,.js,.jsx,.ts,.tsx,.c,.cpp,.h,.hpp,.java,.go,.rs,.php,.sql,.sh,.html,.json,.yaml,.yml,.txt"
              onChange={handleFileInputChange}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-full bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-3">
                <UploadCloud className="w-6 h-6 animate-pulse" />
              </div>
              <p className="text-sm font-semibold text-gray-200">
                Drag and drop your ZIP archive or code file here
              </p>
              <p className="text-xs text-gray-400 mt-1">
                or <span className="text-blue-400 underline font-medium">browse from your computer</span>
              </p>
              <p className="text-[11px] text-gray-500 mt-3 font-mono">
                Supports .zip archives or individual source files (.py, .js, .ts, .c, .cpp, .java, .go, .rs, .php, etc.)
              </p>
            </div>
          </div>

          {/* Selected File Card */}
          {selectedFile && (
            <div className="flex items-center justify-between p-3.5 bg-[#090D13] border border-gray-800 rounded-md">
              <div className="flex items-center gap-3">
                <FileCode className="w-5 h-5 text-yellow-400" />
                <div>
                  <div className="text-xs font-mono font-semibold text-gray-200">
                    {selectedFile.name}
                  </div>
                  <div className="text-[11px] text-gray-500 font-mono">
                    {formatFileSize(selectedFile.size)}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                  className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-gray-800 transition"
                  title="Remove file"
                >
                  <X className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={handleUploadSubmit}
                  disabled={isAuditing}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-70 text-white font-semibold py-1.5 px-4 rounded text-xs transition flex items-center gap-1.5 shadow-sm active:scale-95"
                >
                  {isAuditing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Auditing...
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-white" />
                      Audit Uploaded File
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Raw Code Paste Box */}
      {activeTab === 'raw' && (
        <div className="space-y-3 animate-fade-in">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
            <label className="text-xs font-medium text-gray-400">
              Paste Raw Code Snippet (Formatting &amp; indentation preserved)
            </label>
            <div className="flex items-center gap-2 text-xs">
              {rawCode.trim().length > 0 && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950/70 text-blue-300 border border-blue-700/50 font-mono">
                  {detectedLang}
                </span>
              )}
              <span className="text-gray-500 font-mono">Filename:</span>
              <input
                type="text"
                value={filename}
                onChange={(e) => {
                  setFilename(e.target.value);
                  setFilenameCustomized(true);
                }}
                placeholder="snippet.py"
                className="bg-[#090D13] border border-gray-700 rounded px-2.5 py-1 text-xs text-gray-200 font-mono focus:outline-none focus:border-blue-500 w-32"
              />
            </div>
          </div>

          <div className="relative border border-gray-700 rounded-md bg-[#090D13] focus-within:border-blue-500 transition">
            <textarea
              value={rawCode}
              onChange={handleRawCodeChange}
              placeholder={`# Paste your source code here directly\n# Indentation, whitespace, and tabs are preserved\n\ndef user_login(username, password):\n    query = f"SELECT * FROM users WHERE user = '{username}' AND pass = '{password}'"\n    cursor.execute(query)\n    return cursor.fetchone()`}
              rows={9}
              spellCheck="false"
              autoCapitalize="off"
              autoCorrect="off"
              className="w-full bg-transparent p-4 text-xs text-gray-100 font-mono leading-relaxed focus:outline-none resize-y whitespace-pre"
              style={{ tabSize: 4 }}
            />
          </div>

          <div className="flex justify-between items-center pt-1">
            <span className="text-[11px] text-gray-500 font-mono">
              {rawCode ? `${rawCode.split('\n').length} lines • ${rawCode.length} characters` : '0 lines'}
            </span>

            <button
              type="button"
              onClick={handleRawCodeSubmit}
              disabled={isAuditing}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-70 text-white font-semibold py-2 px-5 rounded-md text-xs transition flex items-center gap-2 shadow-md shadow-blue-600/20 active:scale-95"
            >
              {isAuditing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Auditing Code...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  Audit Raw Code
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
