"""
parser_engine/graph_builder.py
NetworkX-based architectural call-graph builder, cross-file import/invocation resolver,
and blast-radius vulnerability propagation analyzer.
Conforms strictly to backend/schemas.py data contracts.
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple

import networkx as nx

from parser_engine.ast_slicer import ASTSlicer, FunctionSlice, FileSliceResult

try:
    from backend.schemas import DependencyGraph, GraphNode, GraphEdge, SeverityLevel
except ImportError:
    # Graceful fallback if imported in standalone environment
    DependencyGraph = None
    GraphNode = None
    GraphEdge = None
    SeverityLevel = None


@dataclass
class BlastRadiusResult:
    """Represents the vulnerability blast radius analysis for a target function or file."""
    target_id: str
    target_label: str
    target_risk_score: float
    target_severity: Optional[str]
    affected_nodes: List[str]
    affected_count: int
    total_functions: int
    blast_radius_score: float
    direct_callers: List[str]
    entrypoint_callers: List[str]
    depth_map: Dict[str, int]
    call_chains: List[List[str]]
    blast_risk_level: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_label": self.target_label,
            "target_risk_score": self.target_risk_score,
            "target_severity": self.target_severity,
            "affected_nodes": self.affected_nodes,
            "affected_count": self.affected_count,
            "total_functions": self.total_functions,
            "blast_radius_score": self.blast_radius_score,
            "direct_callers": self.direct_callers,
            "entrypoint_callers": self.entrypoint_callers,
            "depth_map": self.depth_map,
            "call_chains": self.call_chains,
            "blast_risk_level": self.blast_risk_level,
        }


class GraphBuilder:
    """
    Constructs and analyzes directed architectural dependency graphs using NetworkX.
    Maps file containment, module imports, and cross-file function invocations.
    """

    def __init__(self, include_file_nodes: bool = True):
        self.graph: nx.DiGraph = nx.DiGraph()
        self.include_file_nodes = include_file_nodes
        self.slicer = ASTSlicer()

        # Internal index registries for cross-file resolution
        self.file_functions: Dict[str, List[FunctionSlice]] = {}
        self.file_imports: Dict[str, List[Dict[str, Any]]] = {}
        self.file_classes: Dict[str, List[Dict[str, Any]]] = {}
        self.function_registry: Dict[str, FunctionSlice] = {}  # node_id -> slice
        self.simple_name_to_nodes: Dict[str, List[str]] = {}   # func_name -> [node_id, ...]

    def add_file(self, file_path: str, content: Optional[str] = None) -> FileSliceResult:
        """
        Parses a single file, registers its functions, imports, and file nodes.
        """
        norm_path = file_path.replace("\\", "/")
        result = self.slicer.parse_file_detailed(norm_path, content=content)

        self.file_functions[norm_path] = result.functions
        self.file_imports[norm_path] = result.imports
        self.file_classes[norm_path] = result.classes

        # 1. Add file node
        if self.include_file_nodes:
            filename = os.path.basename(norm_path)
            self.graph.add_node(
                norm_path,
                id=norm_path,
                label=filename,
                type="file",
                file_path=norm_path,
                risk_score=0.0,
                severity=None,
                risk="Low",
            )

        # 2. Add function nodes
        for fn in result.functions:
            node_id = fn.node_id
            self.function_registry[node_id] = fn
            self.simple_name_to_nodes.setdefault(fn.name, []).append(node_id)

            label = f"{fn.name}()"
            if fn.class_name:
                label = f"{fn.class_name}.{fn.name}()"

            self.graph.add_node(
                node_id,
                id=node_id,
                label=label,
                type="function",
                file_path=norm_path,
                risk_score=0.0,
                severity=None,
                risk="Low",
                line_start=fn.line_start,
                line_end=fn.line_end,
                line_range=fn.line_range,
                boundary=fn.boundary,
                cyclomatic_complexity=fn.cyclomatic_complexity,
                signature=fn.signature,
                arg_count=fn.arg_count,
            )

            # Edge from file to function (containment)
            if self.include_file_nodes:
                self.graph.add_edge(
                    norm_path,
                    node_id,
                    call_type="call",
                    relationship="contains",
                )

        return result

    def build_from_raw_files(self, raw_files: List[Dict[str, Any]]) -> "GraphBuilder":
        """
        Builds the entire dependency graph from raw file objects
        (compatible with agent/state.py `raw_files` format).
        """
        for item in raw_files:
            rel_path = item.get("rel_path") or item.get("filename", "unknown.py")
            content = item.get("content", "")
            self.add_file(rel_path, content=content)

        self._resolve_dependencies()
        return self

    def build_from_directory(
        self,
        root_dir: str,
        extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
    ) -> "GraphBuilder":
        """
        Recursively scans a directory, parses all files, and resolves cross-file links.
        """
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".c", ".cpp"]
        if exclude_dirs is None:
            exclude_dirs = [".git", "venv", ".venv", "env", "node_modules", "__pycache__", "checkpoints", "dist", "build"]

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                    self.add_file(rel_path)

        self._resolve_dependencies()
        return self

    def _resolve_dependencies(self) -> None:
        """
        Performs multi-pass dependency resolution:
        1. Module/File imports
        2. Cross-file and intra-file function calls
        3. Class inheritance hierarchy
        """
        # Pass 1: Resolve imports between files/modules
        for file_path, imports in self.file_imports.items():
            for imp in imports:
                mod_name = imp.get("module", "")
                imported_name = imp.get("name", "")

                # Target file candidates
                target_file = self._resolve_import_to_file(file_path, mod_name)
                if target_file and target_file in self.graph:
                    self.graph.add_edge(
                        file_path,
                        target_file,
                        call_type="import",
                        relationship="imports",
                    )
                elif mod_name:
                    # External or top-level module node
                    if not self.graph.has_node(mod_name):
                        self.graph.add_node(
                            mod_name,
                            id=mod_name,
                            label=mod_name,
                            type="module",
                            file_path=mod_name,
                            risk_score=0.0,
                            severity=None,
                            risk="Low",
                        )
                    self.graph.add_edge(
                        file_path,
                        mod_name,
                        call_type="import",
                        relationship="imports",
                    )

        # Pass 2: Resolve function call invocations
        for caller_node_id, caller_slice in self.function_registry.items():
            caller_file = caller_slice.file_path
            caller_imports = self.file_imports.get(caller_file, [])

            for call_name in caller_slice.calls:
                target_node_id = self._resolve_function_call(caller_file, caller_imports, call_name)
                if target_node_id and target_node_id in self.graph:
                    # Prevent redundant self-loops unless desired
                    if target_node_id != caller_node_id or len(caller_slice.calls) == 1:
                        self.graph.add_edge(
                            caller_node_id,
                            target_node_id,
                            call_type="call",
                            relationship="calls",
                        )

        # Pass 3: Resolve class inheritances
        for file_path, classes in self.file_classes.items():
            for cls in classes:
                cls_name = cls.get("name")
                for base in cls.get("bases", []):
                    # Check if base class exists as node
                    base_candidates = [
                        nid for nid in self.graph.nodes
                        if nid.endswith(f":{base}") or nid.endswith(f".{base}")
                    ]
                    if base_candidates:
                        cls_node_id = f"{file_path}:{cls_name}"
                        if not self.graph.has_node(cls_node_id):
                            self.graph.add_node(
                                cls_node_id,
                                id=cls_node_id,
                                label=f"class {cls_name}",
                                type="class",
                                file_path=file_path,
                                risk_score=0.0,
                                severity=None,
                                risk="Low",
                            )
                        self.graph.add_edge(
                            cls_node_id,
                            base_candidates[0],
                            call_type="import",
                            relationship="inherits",
                        )

    def _resolve_import_to_file(self, current_file: str, module_name: str) -> Optional[str]:
        """Maps a Python module import string to a registered file path in the graph."""
        if not module_name:
            return None

        # Convert dot-separated module path to possible file relative path
        mod_rel = module_name.replace(".", "/")
        candidates = [
            f"{mod_rel}.py",
            f"{mod_rel}/__init__.py",
            f"{os.path.basename(mod_rel)}.py",
        ]

        # Directory relative to current file
        current_dir = os.path.dirname(current_file)
        if current_dir:
            candidates.append(f"{current_dir}/{mod_rel}.py")

        for cand in candidates:
            if cand in self.file_functions or cand in self.graph:
                return cand

        # Match by filename
        for registered in self.file_functions.keys():
            if registered.endswith(f"/{mod_rel}.py") or registered == f"{mod_rel}.py":
                return registered

        return None

    def _resolve_function_call(
        self,
        current_file: str,
        imports: List[Dict[str, Any]],
        call_name: str,
    ) -> Optional[str]:
        """
        Resolves a call name (e.g., 'hash_password', 'utils.hash_password')
        to a specific node_id in the graph.
        """
        # Case 1: Intra-file local call (same file)
        local_id = f"{current_file}:{call_name}"
        if local_id in self.function_registry:
            return local_id

        # Also check if it's a method on a class in the same file
        for nid in self.function_registry:
            if nid.startswith(f"{current_file}:") and nid.endswith(f".{call_name}"):
                return nid

        # Case 2: Directly imported function name (e.g. `from utils import hash_password`)
        for imp in imports:
            imp_name = imp.get("name")
            imp_alias = imp.get("alias") or imp_name
            if imp_alias == call_name or imp_name == call_name:
                target_file = self._resolve_import_to_file(current_file, imp.get("module", ""))
                if target_file:
                    target_id = f"{target_file}:{imp_name}"
                    if target_id in self.function_registry:
                        return target_id
                # Check globally if imp_name is registered
                global_matches = self.simple_name_to_nodes.get(imp_name, [])
                if global_matches:
                    return global_matches[0]

        # Case 3: Module-qualified call (e.g. `utils.hash_password(...)`)
        if "." in call_name:
            mod_prefix, fn_suffix = call_name.rsplit(".", 1)
            # Find which module mod_prefix refers to
            for imp in imports:
                alias = imp.get("alias") or imp.get("name")
                if alias == mod_prefix:
                    target_file = self._resolve_import_to_file(current_file, imp.get("module") or imp.get("name"))
                    if target_file:
                        target_id = f"{target_file}:{fn_suffix}"
                        if target_id in self.function_registry:
                            return target_id

            # Also check if mod_prefix matches a known file basename
            for target_file in self.file_functions:
                base = os.path.splitext(os.path.basename(target_file))[0]
                if base == mod_prefix:
                    target_id = f"{target_file}:{fn_suffix}"
                    if target_id in self.function_registry:
                        return target_id

        # Case 4: Unique global match across repository
        matches = self.simple_name_to_nodes.get(call_name, [])
        if len(matches) == 1:
            return matches[0]

        return None

    def calculate_blast_radius(self, target_node_id: str, calls_only: bool = True) -> BlastRadiusResult:
        """
        Computes the vulnerability blast radius for a target function or file.
        Identifies all upstream callers and dependents that would be compromised
        if the target component contains a vulnerability.

        Args:
            target_node_id: Node ID (e.g. 'db.py:execute_query').
            calls_only: If True, only follows function call edges.

        Returns:
            BlastRadiusResult containing affected nodes, propagation chains, and impact score.
        """
        # Normalize target ID
        norm_target = target_node_id.replace("\\", "/")
        if norm_target not in self.graph:
            # Try fuzzy match by suffix (e.g. 'execute_query' or 'auth.py:login')
            candidates = [n for n in self.graph.nodes if n.endswith(norm_target)]
            if candidates:
                norm_target = candidates[0]
            else:
                return BlastRadiusResult(
                    target_id=target_node_id,
                    target_label=target_node_id,
                    target_risk_score=0.0,
                    target_severity=None,
                    affected_nodes=[],
                    affected_count=0,
                    total_functions=0,
                    blast_radius_score=0.0,
                    direct_callers=[],
                    entrypoint_callers=[],
                    depth_map={},
                    call_chains=[],
                    blast_risk_level="Low",
                )

        target_data = self.graph.nodes[norm_target]

        # Extract relevant directed subgraph (call edges)
        sub_g = nx.DiGraph()
        for u, v, data in self.graph.edges(data=True):
            rel = data.get("relationship", "")
            call_type = data.get("call_type", "")
            if calls_only:
                if rel == "calls" or call_type == "call":
                    # Exclude file->function containment edges if both nodes are in graph
                    if self.graph.nodes[u].get("type") == "file" and self.graph.nodes[v].get("type") == "function":
                        continue
                    sub_g.add_edge(u, v, **data)
            else:
                sub_g.add_edge(u, v, **data)

        # All upstream ancestors that can reach target_node_id
        if norm_target in sub_g:
            affected_ancestors = nx.ancestors(sub_g, norm_target)
            direct_predecessors = list(sub_g.predecessors(norm_target))
        else:
            affected_ancestors = set()
            direct_predecessors = []

        # Reversed graph to compute shortest distance (depth) from callers to target
        rev_g = sub_g.reverse(copy=True)
        depth_map: Dict[str, int] = {}
        if norm_target in rev_g:
            try:
                depth_map = nx.single_source_shortest_path_length(rev_g, norm_target)
                depth_map.pop(norm_target, None)
            except Exception:
                pass

        # Call chains: find paths from top-level callers (in-degree 0 in ancestors) to target
        entrypoint_callers: List[str] = []
        call_chains: List[List[str]] = []
        for caller in affected_ancestors:
            if sub_g.in_degree(caller) == 0:
                entrypoint_callers.append(caller)
                try:
                    paths = list(nx.all_simple_paths(sub_g, source=caller, target=norm_target, cutoff=8))
                    call_chains.extend(paths[:3])  # Top 3 paths per entrypoint
                except Exception:
                    pass

        # If no entrypoints identified, use direct predecessors
        if not entrypoint_callers and direct_predecessors:
            entrypoint_callers = direct_predecessors

        # Metrics
        function_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "function"
        ]
        total_functions = max(1, len(function_nodes))
        affected_count = len(affected_ancestors)
        blast_score = round(affected_count / total_functions, 4)

        # Determine overall blast risk level
        target_risk = target_data.get("risk_score", 0.0)
        if affected_count >= 5 or blast_score >= 0.4 or target_risk >= 0.8:
            blast_risk_level = "Critical"
        elif affected_count >= 2 or blast_score >= 0.2 or target_risk >= 0.6:
            blast_risk_level = "High"
        elif affected_count >= 1 or blast_score > 0.0:
            blast_risk_level = "Medium"
        else:
            blast_risk_level = "Low"

        return BlastRadiusResult(
            target_id=norm_target,
            target_label=target_data.get("label", norm_target),
            target_risk_score=target_risk,
            target_severity=target_data.get("severity"),
            affected_nodes=sorted(list(affected_ancestors)),
            affected_count=affected_count,
            total_functions=total_functions,
            blast_radius_score=blast_score,
            direct_callers=direct_predecessors,
            entrypoint_callers=entrypoint_callers,
            depth_map=depth_map,
            call_chains=call_chains,
            blast_risk_level=blast_risk_level,
        )

    def update_node_risk(
        self,
        node_id: str,
        risk_score: float,
        severity: Optional[str] = None,
    ) -> None:
        """Updates risk score and severity for a specific graph node."""
        norm_id = node_id.replace("\\", "/")
        if norm_id in self.graph:
            self.graph.nodes[norm_id]["risk_score"] = float(risk_score)
            self.graph.nodes[norm_id]["severity"] = severity
            self.graph.nodes[norm_id]["risk"] = severity or "Low"

    def get_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculates in-degree, out-degree, and betweenness centralities."""
        return {
            "in_degree": nx.in_degree_centrality(self.graph),
            "out_degree": nx.out_degree_centrality(self.graph),
            "betweenness": nx.betweenness_centrality(self.graph),
        }

    def detect_cycles(self) -> List[List[str]]:
        """Identifies circular dependencies and recursive call loops."""
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def to_dict(self) -> Dict[str, Any]:
        """
        Exports graph representation matching the Pydantic schema in backend/schemas.py:
        {
          "nodes": [
            {"id": "file.py:func", "label": "func()", "type": "function", "file_path": "file.py", "risk": "Medium"}
          ],
          "edges": [
            {"source": "main.py:entry", "target": "file.py:func", "call_type": "call", "relationship": "calls"}
          ]
        }
        """
        nodes_out = []
        for n, d in self.graph.nodes(data=True):
            sev = d.get("severity")
            risk_label = sev if sev else ("Low" if d.get("risk_score", 0.0) == 0.0 else "Medium")
            nodes_out.append({
                "id": str(n),
                "label": str(d.get("label", n)),
                "type": str(d.get("type", "function")),
                "file_path": str(d.get("file_path", "")).replace("\\", "/"),
                "risk_score": float(d.get("risk_score", 0.0)),
                "severity": sev,
                "risk": risk_label,
            })

        edges_out = []
        for u, v, d in self.graph.edges(data=True):
            call_type = d.get("call_type", "call")
            rel = d.get("relationship", "calls" if call_type == "call" else "imports")
            edges_out.append({
                "source": str(u),
                "target": str(v),
                "call_type": str(call_type),
                "relationship": str(rel),
            })

        return {
            "nodes": nodes_out,
            "edges": edges_out,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes the dependency graph to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_pydantic(self) -> Any:
        """
        Exports a validated Pydantic DependencyGraph instance.
        """
        if DependencyGraph is None or GraphNode is None or GraphEdge is None:
            raise RuntimeError("backend.schemas is unavailable in current environment")

        data = self.to_dict()
        nodes = []
        for n in data["nodes"]:
            sev = None
            if n.get("severity") and SeverityLevel:
                try:
                    sev = SeverityLevel(n["severity"])
                except Exception:
                    sev = None
            nodes.append(GraphNode(
                id=n["id"],
                label=n["label"],
                type=n["type"],
                file_path=n["file_path"],
                risk_score=n["risk_score"],
                severity=sev,
            ))

        edges = [
            GraphEdge(
                source=e["source"],
                target=e["target"],
                call_type=e["call_type"],
            )
            for e in data["edges"]
        ]

        return DependencyGraph(nodes=nodes, edges=edges)
