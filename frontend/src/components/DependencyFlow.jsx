import React, { useMemo, useState, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import { Network, FileCode, CheckCircle, AlertTriangle, Skull, Maximize2 } from 'lucide-react';

export default function DependencyFlow({ graph }) {
  const [selectedNode, setSelectedNode] = useState(null);

  // Transform backend graph nodes and edges to React Flow format with automatic layout
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) {
      return { initialNodes: [], initialEdges: [] };
    }

    const files = graph.nodes.filter((n) => n.type === 'file');
    const functions = graph.nodes.filter((n) => n.type !== 'file');

    const nodes = [];
    const nodePositions = {};

    // Position files in columns on the left / top
    files.forEach((file, index) => {
      const x = 50 + (index % 3) * 280;
      const y = 50 + Math.floor(index / 3) * 160;
      nodePositions[file.id] = { x, y };

      nodes.push({
        id: file.id,
        data: {
          label: (
            <div className="flex items-center gap-2 text-xs">
              <FileCode className="w-3.5 h-3.5 text-blue-400 shrink-0" />
              <span className="font-mono truncate">{file.label || file.id}</span>
            </div>
          ),
          raw: file,
        },
        position: { x, y },
        style: {
          background: '#161B22',
          color: '#E6EDF3',
          border: '1px solid #30363D',
          borderRadius: '8px',
          padding: '10px 14px',
          width: 220,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        },
      });
    });

    // Position functions relative to their files or in rows below
    functions.forEach((fn, index) => {
      const x = 100 + (index % 4) * 250;
      const y = 300 + Math.floor(index / 4) * 140;
      nodePositions[fn.id] = { x, y };

      const sev = (fn.severity || fn.risk || '').toUpperCase();
      let border = '#238636';
      let bg = '#0A1E11';
      let badgeColor = 'text-green-400 bg-green-950';

      if (sev === 'CRITICAL' || sev === 'HIGH' || (fn.risk_score || 0) >= 0.7) {
        border = '#F85149';
        bg = '#2A0D0E';
        badgeColor = 'text-red-400 bg-red-950';
      } else if (sev === 'MEDIUM' || (fn.risk_score || 0) >= 0.4) {
        border = '#D29922';
        bg = '#261C08';
        badgeColor = 'text-yellow-400 bg-yellow-950';
      }

      nodes.push({
        id: fn.id,
        data: {
          label: (
            <div className="text-left">
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="font-mono font-bold text-xs truncate text-gray-100">
                  {fn.label || fn.id}
                </span>
                <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${badgeColor}`}>
                  {sev || 'LOW'}
                </span>
              </div>
              <div className="text-[10px] text-gray-400 truncate">
                Risk: {(fn.risk_score || 0).toFixed(2)}
              </div>
            </div>
          ),
          raw: fn,
        },
        position: { x, y },
        style: {
          background: bg,
          color: '#E6EDF3',
          border: `1.5px solid ${border}`,
          borderRadius: '6px',
          padding: '8px 12px',
          width: 200,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        },
      });
    });

    // Edges
    const edges = (graph.edges || []).map((e, idx) => {
      const isImport = e.call_type === 'import';
      return {
        id: `e-${idx}-${e.source}->${e.target}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: !isImport,
        style: {
          stroke: isImport ? '#8B949E' : '#58A6FF',
          strokeWidth: isImport ? 1.5 : 2,
          strokeDasharray: isImport ? '4,4' : undefined,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isImport ? '#8B949E' : '#58A6FF',
          width: 14,
          height: 14,
        },
        label: isImport ? 'imports' : 'calls',
        labelStyle: { fill: '#8B949E', fontSize: 10, fontFamily: 'monospace' },
        labelBgStyle: { fill: '#0D1117', fillOpacity: 0.8 },
      };
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [graph]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state if graph changes
  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node.data?.raw || null);
  }, []);

  return (
    <section className="bg-[#161B22] border border-[#30363D] rounded-lg p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
        <div>
          <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-400" />
            Interactive Architectural Dependency Graph (React Flow)
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Rendered via NetworkX graph pipeline. Drag, zoom, and click nodes to explore invocation paths &amp; blast radius.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-xs no-print flex-wrap">
          <span className="flex items-center gap-1.5 text-gray-300">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> High Risk Function
          </span>
          <span className="flex items-center gap-1.5 text-gray-300">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span> Medium Risk
          </span>
          <span className="flex items-center gap-1.5 text-gray-300">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500"></span> Benign Function
          </span>
          <span className="flex items-center gap-1.5 text-gray-300">
            <span className="w-2.5 h-2.5 rounded bg-gray-600"></span> Source File
          </span>
        </div>
      </div>

      {/* React Flow Canvas Container */}
      <div className="h-[480px] w-full rounded-md border border-[#30363D] overflow-hidden bg-[#090D13]">
        {nodes.length > 0 ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            attributionPosition="bottom-right"
          >
            <MiniMap
              nodeColor={(n) => {
                const sev = (n.data?.raw?.severity || n.data?.raw?.risk || '').toUpperCase();
                if (sev === 'CRITICAL' || sev === 'HIGH') return '#F85149';
                if (sev === 'MEDIUM') return '#D29922';
                return '#238636';
              }}
              maskColor="rgba(13, 17, 23, 0.7)"
            />
            <Controls />
            <Background color="#30363D" gap={16} size={1} />
          </ReactFlow>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-gray-500 font-mono">
            No dependency graph nodes extracted.
          </div>
        )}
      </div>

      {/* Selected Node Inspector Bar */}
      <div className="mt-3 p-3 bg-[#090D13] border border-gray-800 rounded text-xs text-gray-400 flex flex-wrap justify-between items-center gap-2">
        {selectedNode ? (
          <div className="flex items-center gap-2 flex-wrap">
            <strong className="text-gray-300">Selected Node:</strong>
            <code className="text-blue-400 font-mono px-1.5 py-0.5 rounded bg-gray-900 border border-gray-800">
              {selectedNode.id}
            </code>
            <span className="text-gray-500">({selectedNode.type || 'function'})</span>
            <span>•</span>
            <span>Risk Score: <strong className="text-yellow-400 font-mono">{(selectedNode.risk_score || 0).toFixed(2)}</strong></span>
            <span>•</span>
            <span>Severity: <strong className="text-orange-400">{selectedNode.severity || selectedNode.risk || 'Low'}</strong></span>
          </div>
        ) : (
          <span className="text-gray-500 italic">
            Click on any graph node above to inspect its details, file path, and blast radius.
          </span>
        )}
      </div>
    </section>
  );
}
