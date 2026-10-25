import React, { useMemo, useState, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import {
  Folder,
  FolderOpen,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  Check,
  Copy,
  Search,
  X,
  ArrowLeft,
  ChevronRight,
  Layers,
  Network,
  Maximize2,
  ExternalLink,
  Code
} from 'lucide-react';

// Helper to determine folder from a file path
function extractFolderPath(filePath) {
  if (!filePath) return '(root)';
  const normalized = filePath.replace(/\\/g, '/').replace(/^\/+/, '');
  const parts = normalized.split('/');
  if (parts.length <= 1) return '(root)';
  return parts.slice(0, -1).join('/');
}

// Helper to get file basename
function extractFileName(filePath) {
  if (!filePath) return 'unknown';
  const normalized = filePath.replace(/\\/g, '/');
  const parts = normalized.split('/');
  return parts[parts.length - 1] || 'unknown';
}

export default function DependencyFlow({ graph, findings = [] }) {
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [folderSearch, setFolderSearch] = useState('');
  const [fileSearch, setFileSearch] = useState('');
  const [functionSearch, setFunctionSearch] = useState('');
  const [viewMode, setViewMode] = useState('folders'); // 'folders' | 'detailed'
  const [copiedId, setCopiedId] = useState(null);

  // Close popup with ESC key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (selectedFile) {
          setSelectedFile(null);
        } else if (selectedFolder) {
          setSelectedFolder(null);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedFolder, selectedFile]);

  // Copy helper
  const handleCopyCode = (id, code) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // -------------------------------------------------------------
  // Process raw graph nodes and findings into Hierarchical Folder Structure
  // -------------------------------------------------------------
  const folderHierarchy = useMemo(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) {
      return { folders: {}, folderList: [], edges: [] };
    }

    const folders = {};
    const fileToFolder = {};
    const nodeToFolder = {};

    // 1. Group nodes by Folder and File
    graph.nodes.forEach((node) => {
      const fp = node.file_path || node.id.split(':')[0] || '';
      const folderPath = extractFolderPath(fp);
      const filename = extractFileName(fp);

      nodeToFolder[node.id] = folderPath;
      if (fp) fileToFolder[fp] = folderPath;

      if (!folders[folderPath]) {
        folders[folderPath] = {
          id: folderPath,
          path: folderPath,
          files: {},
          functions: [],
          findings: [],
          maxSeverity: 'LOW',
          riskScore: 0.0,
          incomingCallsCount: 0,
          outgoingCallsCount: 0,
          connectedFrom: new Set(),
          connectedTo: new Set(),
        };
      }

      if (fp) {
        if (!folders[folderPath].files[fp]) {
          folders[folderPath].files[fp] = {
            path: fp,
            filename: filename,
            functions: [],
            findings: [],
            riskScore: 0.0,
            maxSeverity: 'LOW',
          };
        }
      }

      if (node.type === 'function') {
        folders[folderPath].functions.push(node);
        if (fp && folders[folderPath].files[fp]) {
          folders[folderPath].files[fp].functions.push(node);
        }
      }

      // Track max risk
      if (node.risk_score && node.risk_score > folders[folderPath].riskScore) {
        folders[folderPath].riskScore = node.risk_score;
      }
    });

    // 2. Associate Findings with Folders and Files
    findings.forEach((finding) => {
      const fp = finding.file_path || '';
      const folderPath = extractFolderPath(fp);

      if (folders[folderPath]) {
        folders[folderPath].findings.push(finding);

        // Update severity priority
        const sev = (finding.severity || '').toUpperCase();
        if (sev === 'CRITICAL') {
          folders[folderPath].maxSeverity = 'CRITICAL';
        } else if (sev === 'HIGH' && folders[folderPath].maxSeverity !== 'CRITICAL') {
          folders[folderPath].maxSeverity = 'HIGH';
        } else if (sev === 'MEDIUM' && !['CRITICAL', 'HIGH'].includes(folders[folderPath].maxSeverity)) {
          folders[folderPath].maxSeverity = 'MEDIUM';
        }

        if (folders[folderPath].files[fp]) {
          folders[folderPath].files[fp].findings.push(finding);
          if (sev === 'CRITICAL') {
            folders[folderPath].files[fp].maxSeverity = 'CRITICAL';
          } else if (sev === 'HIGH' && folders[folderPath].files[fp].maxSeverity !== 'CRITICAL') {
            folders[folderPath].files[fp].maxSeverity = 'HIGH';
          } else if (sev === 'MEDIUM' && !['CRITICAL', 'HIGH'].includes(folders[folderPath].files[fp].maxSeverity)) {
            folders[folderPath].files[fp].maxSeverity = 'MEDIUM';
          }
        }
      }
    });

    // 3. Aggregate inter-folder dependencies from edges
    const folderEdgesMap = {};

    (graph.edges || []).forEach((edge) => {
      const srcFolder = nodeToFolder[edge.source];
      const tgtFolder = nodeToFolder[edge.target];

      if (srcFolder && tgtFolder && srcFolder !== tgtFolder) {
        folders[srcFolder].connectedTo.add(tgtFolder);
        folders[tgtFolder].connectedFrom.add(srcFolder);

        const edgeKey = `${srcFolder}->${tgtFolder}`;
        if (!folderEdgesMap[edgeKey]) {
          folderEdgesMap[edgeKey] = {
            source: srcFolder,
            target: tgtFolder,
            count: 0,
            callTypes: new Set(),
          };
        }
        folderEdgesMap[edgeKey].count += 1;
        folderEdgesMap[edgeKey].callTypes.add(edge.call_type || 'call');
      }
    });

    const folderList = Object.values(folders);
    const folderEdges = Object.values(folderEdgesMap);

    return { folders, folderList, edges: folderEdges };
  }, [graph, findings]);

  // -------------------------------------------------------------
  // Build React Flow Nodes & Edges based on selected view mode
  // -------------------------------------------------------------
  const { flowNodes, flowEdges } = useMemo(() => {
    if (viewMode === 'detailed') {
      // Return full microscopic function graph if user toggles to detailed mode
      if (!graph || !graph.nodes) return { flowNodes: [], flowEdges: [] };

      const nodes = graph.nodes.map((n, idx) => {
        const isFile = n.type === 'file';
        const col = idx % 4;
        const row = Math.floor(idx / 4);
        const sev = (n.severity || '').toUpperCase();

        let border = '#30363D';
        let bg = '#161B22';
        if (sev === 'CRITICAL' || sev === 'HIGH') {
          border = '#F85149';
          bg = '#2A0D0E';
        } else if (sev === 'MEDIUM') {
          border = '#D29922';
          bg = '#261C08';
        }

        return {
          id: n.id,
          position: { x: 50 + col * 260, y: 50 + row * 140 },
          data: {
            label: (
              <div className="text-left text-xs">
                <div className="flex items-center gap-1.5 font-bold truncate">
                  {isFile ? <FileCode className="w-3.5 h-3.5 text-blue-400" /> : <Code className="w-3.5 h-3.5 text-emerald-400" />}
                  <span className="truncate">{n.label || n.id}</span>
                </div>
                <div className="text-[10px] text-gray-400 mt-1 flex justify-between">
                  <span>{n.type}</span>
                  <span className="font-mono text-yellow-400">{(n.risk_score || 0).toFixed(2)}</span>
                </div>
              </div>
            ),
            raw: n,
          },
          style: {
            background: bg,
            color: '#E6EDF3',
            border: `1.5px solid ${border}`,
            borderRadius: '6px',
            padding: '8px 12px',
            width: 220,
          },
        };
      });

      const edges = (graph.edges || []).map((e, idx) => ({
        id: `detail-edge-${idx}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        style: { stroke: e.call_type === 'import' ? '#8B949E' : '#58A6FF', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12 },
      }));

      return { flowNodes: nodes, flowEdges: edges };
    }

    // Default: CLEAN ARCHITECTURAL FOLDERS VIEW
    const { folderList, edges } = folderHierarchy;
    if (!folderList || folderList.length === 0) return { flowNodes: [], flowEdges: [] };

    // Layout folder nodes in an organized, spacious grid
    const COLS = Math.min(3, Math.max(2, Math.ceil(Math.sqrt(folderList.length))));
    const nodes = folderList.map((folder, index) => {
      const col = index % COLS;
      const row = Math.floor(index / COLS);
      const x = 60 + col * 320;
      const y = 50 + row * 210;

      const fileCount = Object.keys(folder.files).length;
      const funcCount = folder.functions.length;
      const findCount = folder.findings.length;
      const sev = folder.maxSeverity;

      let border = '#30363D';
      let glow = 'none';
      let badgeBg = 'bg-emerald-950/70 text-emerald-400 border-emerald-800';
      let statusText = 'Clean';

      if (findCount > 0) {
        if (sev === 'CRITICAL' || sev === 'HIGH') {
          border = '#F85149';
          glow = '0 0 16px rgba(248, 81, 73, 0.25)';
          badgeBg = 'bg-rose-950/80 text-rose-300 border-rose-800';
          statusText = `${findCount} ${findCount === 1 ? 'Risk' : 'Risks'} (${sev})`;
        } else {
          border = '#D29922';
          glow = '0 0 14px rgba(210, 153, 34, 0.25)';
          badgeBg = 'bg-amber-950/80 text-amber-300 border-amber-800';
          statusText = `${findCount} Risks (Med)`;
        }
      }

      return {
        id: folder.id,
        position: { x, y },
        data: {
          folderData: folder,
          label: (
            <div className="text-left font-sans select-none cursor-pointer p-1">
              {/* Folder Title Header */}
              <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b border-[#30363D]">
                <div className="flex items-center gap-2 overflow-hidden">
                  <div className="p-1.5 rounded-md bg-[#21262D] text-amber-400 shrink-0">
                    <Folder className="w-4 h-4 fill-amber-400/20" />
                  </div>
                  <span className="font-bold text-xs text-gray-100 truncate font-mono">
                    {folder.path === '(root)' ? '📁 (root)' : `📁 ${folder.path}`}
                  </span>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border shrink-0 font-semibold ${badgeBg}`}>
                  {statusText}
                </span>
              </div>

              {/* Stats Counters */}
              <div className="grid grid-cols-2 gap-1.5 text-[11px] mb-2.5">
                <div className="bg-[#0D1117] px-2 py-1 rounded border border-[#30363D]/60 flex items-center justify-between">
                  <span className="text-gray-400">Files:</span>
                  <span className="font-mono font-semibold text-blue-300">{fileCount}</span>
                </div>
                <div className="bg-[#0D1117] px-2 py-1 rounded border border-[#30363D]/60 flex items-center justify-between">
                  <span className="text-gray-400">Funcs:</span>
                  <span className="font-mono font-semibold text-purple-300">{funcCount}</span>
                </div>
              </div>

              {/* Click to inspect prompt */}
              <div className="flex items-center justify-between text-[10px] text-cyan-400 font-medium group-hover:underline pt-0.5">
                <span>Click to inspect files</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </div>
          ),
        },
        style: {
          background: '#161B22',
          color: '#E6EDF3',
          border: `1.5px solid ${border}`,
          borderRadius: '10px',
          padding: '12px 14px',
          width: 270,
          boxShadow: glow !== 'none' ? glow : '0 6px 16px rgba(0,0,0,0.4)',
          transition: 'all 0.2s ease-in-out',
        },
      };
    });

    const flowEdgesList = edges.map((e, idx) => ({
      id: `folder-edge-${idx}-${e.source}->${e.target}`,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: true,
      style: {
        stroke: '#58A6FF',
        strokeWidth: Math.min(4, 1.5 + Math.log2(e.count + 1)),
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#58A6FF',
        width: 14,
        height: 14,
      },
      label: `${e.count} ${e.count === 1 ? 'call' : 'calls'}`,
      labelStyle: { fill: '#8B949E', fontSize: 10, fontFamily: 'monospace', fontWeight: 600 },
      labelBgStyle: { fill: '#0D1117', fillOpacity: 0.9, rx: 4, ry: 4 },
    }));

    return { flowNodes: nodes, flowEdges: flowEdgesList };
  }, [folderHierarchy, viewMode, graph]);

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  useEffect(() => {
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  // Handle clicking on a folder node in the map
  const onNodeClick = useCallback((event, node) => {
    if (viewMode === 'folders' && node.data?.folderData) {
      setSelectedFolder(node.data.folderData);
      setSelectedFile(null);
      setFileSearch('');
      setFunctionSearch('');
    }
  }, [viewMode]);

  // Filtered files in currently selected folder
  const filteredFiles = useMemo(() => {
    if (!selectedFolder) return [];
    const filesArray = Object.values(selectedFolder.files);
    if (!fileSearch.trim()) return filesArray;
    const q = fileSearch.toLowerCase();
    return filesArray.filter((f) => f.filename.toLowerCase().includes(q) || f.path.toLowerCase().includes(q));
  }, [selectedFolder, fileSearch]);

  // Filtered functions in currently selected file
  const filteredFunctions = useMemo(() => {
    if (!selectedFile) return [];
    const funcs = selectedFile.functions || [];
    if (!functionSearch.trim()) return funcs;
    const q = functionSearch.toLowerCase();
    return funcs.filter((fn) => (fn.label || fn.id || '').toLowerCase().includes(q));
  }, [selectedFile, functionSearch]);

  // Quick jump helper for global folder search
  const matchingFolders = useMemo(() => {
    if (!folderSearch.trim()) return [];
    const q = folderSearch.toLowerCase();
    return folderHierarchy.folderList.filter((f) => f.path.toLowerCase().includes(q));
  }, [folderHierarchy, folderSearch]);

  return (
    <section className="bg-[#161B22] border border-[#30363D] rounded-xl p-5 md:p-6 shadow-md relative">
      {/* Header Bar with View Controls & Search */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-4">
        <div>
          <h2 className="text-base font-bold text-gray-100 flex items-center gap-2.5">
            <Network className="w-5 h-5 text-blue-400" />
            Architectural Component &amp; Dependency Map
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {viewMode === 'folders'
              ? 'Showing high-level modular directories. Click any folder to inspect its internal files & functions.'
              : 'Detailed microscopic view showing all extracted file and function nodes.'}
          </p>
        </div>

        {/* View Mode Toggle and Search Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search folders..."
              value={folderSearch}
              onChange={(e) => setFolderSearch(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg bg-[#0D1117] border border-[#30363D] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 w-44 sm:w-52"
            />
            {/* Quick search dropdown */}
            {matchingFolders.length > 0 && (
              <div className="absolute right-0 top-full mt-1.5 w-64 bg-[#161B22] border border-[#30363D] rounded-lg shadow-2xl z-40 max-h-48 overflow-y-auto p-1">
                {matchingFolders.map((fld) => (
                  <button
                    key={fld.id}
                    onClick={() => {
                      setSelectedFolder(fld);
                      setSelectedFile(null);
                      setFolderSearch('');
                    }}
                    className="w-full text-left px-2.5 py-1.5 text-xs text-gray-300 hover:bg-[#21262D] rounded flex items-center justify-between"
                  >
                    <span className="font-mono truncate">📁 {fld.path}</span>
                    <span className="text-[10px] text-gray-500">{Object.keys(fld.files).length} files</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* View Mode Switcher */}
          <div className="flex items-center rounded-lg bg-[#0D1117] p-0.5 border border-[#30363D] text-xs">
            <button
              onClick={() => setViewMode('folders')}
              className={`px-3 py-1 rounded-md transition font-medium flex items-center gap-1.5 ${
                viewMode === 'folders' ? 'bg-[#21262D] text-blue-400 shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Folder className="w-3.5 h-3.5" />
              Folders Architecture
            </button>
            <button
              onClick={() => setViewMode('detailed')}
              className={`px-3 py-1 rounded-md transition font-medium flex items-center gap-1.5 ${
                viewMode === 'detailed' ? 'bg-[#21262D] text-blue-400 shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Micro-Graph
            </button>
          </div>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="h-[520px] w-full rounded-xl border border-[#30363D] overflow-hidden bg-[#090D13] relative">
        {nodes.length > 0 ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <MiniMap
              nodeColor={(n) => {
                const fld = n.data?.folderData;
                if (fld && fld.findings && fld.findings.length > 0) {
                  return fld.maxSeverity === 'CRITICAL' || fld.maxSeverity === 'HIGH' ? '#F85149' : '#D29922';
                }
                return '#238636';
              }}
              maskColor="rgba(13, 17, 23, 0.75)"
            />
            <Controls />
            <Background color="#30363D" gap={18} size={1} />
          </ReactFlow>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-gray-500 font-mono">
            No architectural dependency nodes available.
          </div>
        )}

        {/* Legend Overlay at bottom left of canvas */}
        <div className="absolute bottom-3 left-3 bg-[#161B22]/90 backdrop-blur border border-[#30363D] rounded-lg px-3 py-2 text-[11px] text-gray-300 flex items-center gap-3.5 pointer-events-none z-10 shadow-lg">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Critical / High Risk
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Medium Risk
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Secure
          </span>
          <span className="flex items-center gap-1.5 text-gray-400">
            <span className="w-3.5 h-0.5 bg-blue-400 inline-block"></span> Calls / Imports
          </span>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* POPUP MODAL: Interactive Folder & File Drilldown Screen */}
      {/* ------------------------------------------------------------- */}
      {selectedFolder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#161B22] border border-[#30363D] rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Navigation Bar / Breadcrumbs */}
            <div className="px-5 py-4 border-b border-[#30363D] bg-[#0D1117] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2 text-xs font-mono overflow-x-auto py-1">
                <button
                  onClick={() => {
                    setSelectedFolder(null);
                    setSelectedFile(null);
                  }}
                  className="text-gray-400 hover:text-blue-400 transition flex items-center gap-1 shrink-0"
                >
                  <Network className="w-3.5 h-3.5" />
                  <span>Map</span>
                </button>
                <ChevronRight className="w-3 h-3 text-gray-600 shrink-0" />
                <button
                  onClick={() => setSelectedFile(null)}
                  className={`flex items-center gap-1 shrink-0 ${
                    !selectedFile ? 'text-amber-400 font-bold' : 'text-gray-400 hover:text-amber-300'
                  }`}
                >
                  <Folder className="w-3.5 h-3.5" />
                  <span>{selectedFolder.path === '(root)' ? 'root' : selectedFolder.path}</span>
                </button>
                {selectedFile && (
                  <>
                    <ChevronRight className="w-3 h-3 text-gray-600 shrink-0" />
                    <span className="text-blue-400 font-bold flex items-center gap-1 shrink-0">
                      <FileCode className="w-3.5 h-3.5" />
                      <span>{selectedFile.filename}</span>
                    </span>
                  </>
                )}
              </div>

              {/* Close button */}
              <button
                onClick={() => {
                  setSelectedFolder(null);
                  setSelectedFile(null);
                }}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-[#21262D] transition shrink-0 ml-2"
                title="Close (ESC)"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {!selectedFile ? (
                /* ---------------- LEVEL 1: FOLDER FILES VIEW ---------------- */
                <div className="space-y-4">
                  {/* Folder Overview Banner */}
                  <div className="bg-[#0D1117] p-4 rounded-xl border border-[#30363D] flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Folder className="w-5 h-5 text-amber-400" />
                        <h3 className="text-base font-bold text-gray-100 font-mono">
                          {selectedFolder.path === '(root)' ? '📁 Root Directory' : `📁 ${selectedFolder.path}`}
                        </h3>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        Select a file below to view its extracted functions, line boundaries, and security findings.
                      </p>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2.5 py-1 rounded-md bg-[#21262D] text-xs font-mono text-blue-300 border border-[#30363D]">
                        {Object.keys(selectedFolder.files).length} Files
                      </span>
                      <span className="px-2.5 py-1 rounded-md bg-[#21262D] text-xs font-mono text-purple-300 border border-[#30363D]">
                        {selectedFolder.functions.length} Functions
                      </span>
                      {selectedFolder.findings.length > 0 ? (
                        <span className="px-2.5 py-1 rounded-md bg-rose-950/80 text-rose-300 border border-rose-800 text-xs font-mono font-semibold flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          {selectedFolder.findings.length} Vulnerabilities
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-800 text-xs font-mono font-semibold flex items-center gap-1">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          All Clean
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Connected Folders Info */}
                  {(selectedFolder.connectedTo.size > 0 || selectedFolder.connectedFrom.size > 0) && (
                    <div className="bg-[#0D1117]/60 p-3 rounded-lg border border-[#30363D]/60 text-xs flex flex-wrap gap-x-6 gap-y-2 text-gray-400">
                      {selectedFolder.connectedTo.size > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-gray-500 font-medium">Calls into:</span>
                          {Array.from(selectedFolder.connectedTo).map((target) => (
                            <span key={target} className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[#21262D] text-blue-300">
                              {target}
                            </span>
                          ))}
                        </div>
                      )}
                      {selectedFolder.connectedFrom.size > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-gray-500 font-medium">Called by:</span>
                          {Array.from(selectedFolder.connectedFrom).map((source) => (
                            <span key={source} className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[#21262D] text-gray-300">
                              {source}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Search Files in Folder */}
                  <div className="relative">
                    <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder={`Filter ${Object.keys(selectedFolder.files).length} files in this folder...`}
                      value={fileSearch}
                      onChange={(e) => setFileSearch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 text-xs rounded-xl bg-[#0D1117] border border-[#30363D] text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  {/* Files Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {filteredFiles.map((file) => {
                      const hasVuln = file.findings && file.findings.length > 0;
                      return (
                        <div
                          key={file.path}
                          onClick={() => {
                            setSelectedFile(file);
                            setFunctionSearch('');
                          }}
                          className={`p-3.5 rounded-xl border transition cursor-pointer flex flex-col justify-between gap-3 ${
                            hasVuln
                              ? 'bg-[#2A0D0E]/40 border-rose-900/60 hover:border-rose-500 hover:bg-[#2A0D0E]/60'
                              : 'bg-[#0D1117] border-[#30363D] hover:border-blue-500 hover:bg-[#21262D]'
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between gap-2 mb-1.5">
                              <div className="flex items-center gap-2 overflow-hidden">
                                <FileCode className={`w-4 h-4 shrink-0 ${hasVuln ? 'text-rose-400' : 'text-blue-400'}`} />
                                <span className="font-mono font-bold text-xs text-gray-100 truncate">
                                  {file.filename}
                                </span>
                              </div>
                              {hasVuln ? (
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold bg-rose-950 text-rose-300 border border-rose-800 shrink-0">
                                  {file.findings.length} {file.findings.length === 1 ? 'Finding' : 'Findings'}
                                </span>
                              ) : (
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-900 shrink-0">
                                  Clean
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-gray-500 font-mono truncate">{file.path}</div>
                          </div>

                          <div className="flex items-center justify-between text-[11px] pt-2 border-t border-[#30363D]/40">
                            <span className="text-gray-400 font-mono">
                              {file.functions.length} {file.functions.length === 1 ? 'function' : 'functions'}
                            </span>
                            <span className="text-cyan-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition">
                              Inspect Functions <ChevronRight className="w-3.5 h-3.5" />
                            </span>
                          </div>
                        </div>
                      );
                    })}

                    {filteredFiles.length === 0 && (
                      <div className="col-span-2 py-10 text-center text-xs text-gray-500 font-mono">
                        No files matching "{fileSearch}"
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                /* ---------------- LEVEL 2: FILE FUNCTIONS & DETAILS VIEW ---------------- */
                <div className="space-y-4">
                  {/* Back Button & File Banner */}
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-[#30363D]">
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="px-3 py-1.5 rounded-lg bg-[#21262D] text-xs font-medium text-gray-300 hover:text-white hover:bg-[#30363D] transition flex items-center gap-1.5"
                    >
                      <ArrowLeft className="w-3.5 h-3.5" />
                      Back to Files in {selectedFolder.path}
                    </button>

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-gray-400 font-medium">{selectedFile.path}</span>
                      {selectedFile.findings.length > 0 && (
                        <span className="px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 text-[10px] font-mono font-bold">
                          {selectedFile.findings.length} Vulnerabilities
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Search Functions in File */}
                  <div className="relative">
                    <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder={`Search ${selectedFile.functions.length} functions in ${selectedFile.filename}...`}
                      value={functionSearch}
                      onChange={(e) => setFunctionSearch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 text-xs rounded-xl bg-[#0D1117] border border-[#30363D] text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  {/* Functions List */}
                  <div className="space-y-3">
                    {filteredFunctions.map((fn, idx) => {
                      const funcId = fn.id;
                      const fnName = fn.label ? fn.label.replace('()', '') : fn.id.split(':').pop();

                      // Check if any finding belongs to this function
                      const relatedFindings = (selectedFile.findings || []).filter(
                        (f) =>
                          f.function_name === fnName ||
                          (f.line_start && fn.data?.raw?.line_start && f.line_start >= fn.data.raw.line_start && f.line_start <= fn.data.raw.line_end)
                      );

                      const hasRisk = relatedFindings.length > 0 || (fn.risk_score || 0) > 0.4;
                      const sev = relatedFindings[0]?.severity || fn.severity || (hasRisk ? 'HIGH' : 'LOW');

                      return (
                        <div
                          key={funcId || idx}
                          className={`p-4 rounded-xl border transition ${
                            hasRisk
                              ? 'bg-[#2A0D0E]/30 border-rose-900/60'
                              : 'bg-[#0D1117] border-[#30363D]'
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                            <div className="flex items-center gap-2">
                              <Code className={`w-4 h-4 ${hasRisk ? 'text-rose-400' : 'text-purple-400'}`} />
                              <span className="font-mono font-bold text-sm text-gray-100">{fn.label || fn.id}</span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span
                                className={`text-[10px] font-mono px-2 py-0.5 rounded-full border font-bold ${
                                  hasRisk
                                    ? 'bg-rose-950 text-rose-300 border-rose-800'
                                    : 'bg-emerald-950/60 text-emerald-400 border-emerald-900'
                                }`}
                              >
                                {sev} Risk ({fn.risk_score ? fn.risk_score.toFixed(2) : '0.00'})
                              </span>
                            </div>
                          </div>

                          {/* Function Vulnerability Finding Detail */}
                          {relatedFindings.length > 0 && (
                            <div className="mt-3 space-y-3">
                              {relatedFindings.map((finding) => (
                                <div
                                  key={finding.id}
                                  className="bg-[#161B22] border border-rose-900/80 rounded-lg p-3 text-xs space-y-2"
                                >
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-2 font-semibold text-rose-300">
                                      <AlertOctagon className="w-4 h-4 shrink-0 text-rose-400" />
                                      <span>
                                        {finding.category} ({finding.cwe_id})
                                      </span>
                                    </div>
                                    <span className="font-mono text-[10px] text-gray-400">
                                      L{finding.line_start}-L{finding.line_end}
                                    </span>
                                  </div>

                                  <p className="text-gray-300 text-[11px] leading-relaxed">
                                    {finding.description}
                                  </p>

                                  {/* Code Diffs inside function view */}
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                                    {/* Vulnerable Code */}
                                    <div className="bg-[#090D13] p-2.5 rounded border border-rose-950 overflow-x-auto">
                                      <div className="text-[10px] text-rose-400 font-bold mb-1">Original Vulnerable Snippet:</div>
                                      <pre className="text-rose-200/90 whitespace-pre-wrap">{finding.vulnerable_code}</pre>
                                    </div>

                                    {/* Recommended Fix */}
                                    <div className="bg-[#090D13] p-2.5 rounded border border-emerald-950 overflow-x-auto relative group">
                                      <div className="flex justify-between items-center mb-1">
                                        <div className="text-[10px] text-emerald-400 font-bold">Recommended Secure Patch:</div>
                                        <button
                                          onClick={() => handleCopyCode(finding.id, finding.fix_code)}
                                          className="text-[10px] text-gray-400 hover:text-white flex items-center gap-1 bg-[#21262D] px-1.5 py-0.5 rounded"
                                        >
                                          {copiedId === finding.id ? (
                                            <>
                                              <Check className="w-3 h-3 text-emerald-400" /> Copied
                                            </>
                                          ) : (
                                            <>
                                              <Copy className="w-3 h-3" /> Copy
                                            </>
                                          )}
                                        </button>
                                      </div>
                                      <pre className="text-emerald-200/90 whitespace-pre-wrap">{finding.fix_code}</pre>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {relatedFindings.length === 0 && (
                            <div className="text-[11px] text-gray-400 flex items-center gap-1.5 mt-1 font-mono">
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                              <span>No security vulnerabilities detected in this function unit.</span>
                            </div>
                          )}
                        </div>
                      );
                    })}

                    {filteredFunctions.length === 0 && (
                      <div className="p-8 text-center text-xs text-gray-500 font-mono bg-[#0D1117] rounded-xl border border-[#30363D]">
                        {selectedFile.functions.length === 0
                          ? 'This file has no standalone function definitions (module-level script or configuration).'
                          : `No functions matching "${functionSearch}"`}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
