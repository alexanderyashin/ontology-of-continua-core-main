import { useEffect, useMemo, useRef, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import type { GraphNode, ScienceGraph as ScienceGraphData } from "../types";
import { Canvas3D } from "./Canvas3D";

const COLORS: Record<string, string> = {
  structural: "#2563eb",
  "proof-only": "#7c3aed",
  simulatable: "#0f766e",
  "proof-browser": "#dc2626",
  calculator: "#ca8a04",
  root_principle: "#b91c1c",
  continuum_operator: "#2563eb",
  metaontology: "#7c3aed",
  m_space: "#0891b2",
  k_level: "#0f766e",
  axis: "#16a34a",
  threshold: "#ea580c",
  theorem: "#9333ea",
  formula: "#0ea5e9",
  proof_route: "#dc2626",
  evidence: "#64748b",
  domain_projection: "#ca8a04",
  simulation: "#db2777",
  corpus_atom: "#475569",
  boundary: "#111827"
};

function trustFromNode(node?: GraphNode | null): string {
  const status = node?.detail?.validation_status ?? node?.detail?.replay_status;
  return status ?? "frontier";
}

type ScienceGraphCrossLinks = {
  onOpenWiki?: (query: string) => void;
  onOpenFormula?: (query: string) => void;
  onOpenFormulaId?: (formulaId: string) => void;
  onOpenProofTarget?: (targetId: string) => void;
  onOpenKLevel?: (kLevel: string) => void;
  onOpenWorkbench?: (kLevel: string) => void;
};

export function ScienceGraph({
  graph,
  query,
  onQuery,
  onOpenWiki,
  onOpenFormula,
  onOpenFormulaId,
  onOpenProofTarget,
  onOpenKLevel,
  onOpenWorkbench
}: {
  graph: ScienceGraphData;
  query: string;
  onQuery: (value: string) => void;
} & ScienceGraphCrossLinks) {
  const sigmaContainerRef = useRef<HTMLDivElement | null>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const [layer, setLayer] = useState("all");
  const [relation, setRelation] = useState("all");
  const [selected, setSelected] = useState(graph.nodes[0]?.id ?? "");
  const [show2d, setShow2d] = useState(false);
  const selectedNode = graph.nodes.find((node) => node.id === selected) ?? graph.nodes[0];
  const rootPath = useMemo(() => {
    const root = graph.nodes.find((node) => node.layer === "root_principle")?.id ?? graph.nodes[0]?.id;
    if (!root || !selected) return [] as string[];
    const adjacency = new Map<string, string[]>();
    for (const edge of graph.edges) {
      adjacency.set(edge.source, [...(adjacency.get(edge.source) ?? []), edge.target]);
      adjacency.set(edge.target, [...(adjacency.get(edge.target) ?? []), edge.source]);
    }
    const queue: Array<{ id: string; path: string[] }> = [{ id: root, path: [root] }];
    const seen = new Set([root]);
    while (queue.length) {
      const current = queue.shift();
      if (!current) break;
      if (current.id === selected) return current.path;
      for (const next of adjacency.get(current.id) ?? []) {
        if (seen.has(next)) continue;
        seen.add(next);
        queue.push({ id: next, path: [...current.path, next] });
      }
    }
    return [] as string[];
  }, [graph.edges, graph.nodes, selected]);
  const layerCounts = graph.summary.layer_counts ?? graph.summary.cluster_counts;
  const selectedLabel = selectedNode?.semantic_label ?? selectedNode?.technical_label ?? selectedNode?.label;
  const semanticRootPath = rootPath.map((nodeId) => {
    const node = graph.nodes.find((nodeToMatch) => nodeToMatch.id === nodeId);
    return {
      id: node?.id ?? nodeId,
      label: node?.semantic_label ?? node?.technical_label ?? node?.label ?? nodeId
    };
  })
    .filter((entry) => entry.id);

  const filteredNodes = useMemo(() => {
    const lower = query.toLowerCase();
    return graph.nodes.filter((node) => {
      const nodeLayer = node.layer ?? node.cluster;
      return (layer === "all" || nodeLayer === layer) && (!lower || JSON.stringify(node).toLowerCase().includes(lower));
    });
  }, [layer, graph.nodes, query]);

  useEffect(() => {
    if (!query || filteredNodes.length === 0) return;
    if (!filteredNodes.some((node) => node.id === selected)) {
      setSelected(filteredNodes[0].id);
    }
  }, [filteredNodes, query, selected]);

  const filteredEdges = useMemo(() => {
    const allowed = new Set(filteredNodes.map((node) => node.id));
    return graph.edges.filter((edge) => allowed.has(edge.source) && allowed.has(edge.target) && (relation === "all" || edge.relation === relation));
  }, [filteredNodes, graph.edges, relation]);

  const selectedLinks = useMemo(() => {
    if (!selected) return [];
    return filteredEdges.filter((edge) => edge.source === selected || edge.target === selected).map((edge) => (edge.source === selected ? edge.target : edge.source)).slice(0, 16);
  }, [filteredEdges, selected]);

  useEffect(() => {
    if (!show2d || !sigmaContainerRef.current) return;
    const g = new Graph();
    const allowed = new Set(filteredNodes.map((node) => node.id));
    for (const node of filteredNodes) {
      g.addNode(node.id, {
        label: node.label,
        x: node.x,
        y: node.y,
        size: node.size,
        color: COLORS[node.layer ?? node.cluster] ?? "#64748b"
      });
    }
    for (const edge of filteredEdges) {
      if (allowed.has(edge.source) && allowed.has(edge.target) && !g.hasEdge(edge.id)) {
        g.addEdgeWithKey(edge.id, edge.source, edge.target, { label: edge.relation, color: edge.relation === "collapse_path" ? "#dc2626" : "#cbd5e1", size: edge.weight ?? 1 });
      }
    }
    sigmaRef.current?.kill();
    sigmaRef.current = new Sigma(g, sigmaContainerRef.current, { renderEdgeLabels: false, allowInvalidContainer: true });
    sigmaRef.current.on("clickNode", (event) => setSelected(event.node));
    return () => {
      sigmaRef.current?.kill();
      sigmaRef.current = null;
    };
  }, [show2d, filteredNodes, filteredEdges]);

  return (
    <section className="view-grid graph-view" data-testid="graph-surface">
      <aside className="rail">
        <h2>3D Science Graph</h2>
        <input className="search" value={query} onChange={(event) => onQuery(event.target.value)} placeholder="Search targets, claims, routes" />
        <select className="search" value={layer} onChange={(event) => setLayer(event.target.value)}>
          <option value="all">All layers</option>
          {Object.keys(layerCounts).map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <select className="search" value={relation} onChange={(event) => setRelation(event.target.value)}>
          <option value="all">All edge types</option>
          {Object.keys(graph.summary.relation_counts).map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <button className="command secondary-command" onClick={() => setShow2d((value) => !value)}>{show2d ? "Hide" : "Show"} Sigma 2D fallback</button>
        <button className="command secondary-command" onClick={() => setSelected(graph.nodes.find((node) => node.layer === "root_principle")?.id ?? graph.nodes[0]?.id ?? "")}>Root principle</button>
        <div className="legend">
          {Object.entries(layerCounts).map(([name, count]) => (
            <span key={name}><i style={{ background: COLORS[name] ?? "#64748b" }} />{name} {count}</span>
          ))}
        </div>
        <div className="note danger" data-testid="graph-theorem-proof-policy">
          <strong>Theorem node policy</strong><br />
          A theorem or formula node is a navigation object, not a closed proof. Proof closure lives only in Evidence / Boundaries and its proof-count policy.
        </div>
      </aside>
      <main className="panel big-panel graph-shell">
        <div className="section-header">
          <div>
            <p className="eyebrow">rooted corpus-first / rotatable / clickable</p>
            <h2>Science Graph</h2>
          <p>Start from the root principle and follow semantic labels through contradiction, operators, formulas, K-level links, evidence routes and domains.</p>
        </div>
        <div className="metric-stack"><strong>{filteredNodes.length}</strong><span>visible nodes</span></div>
        </div>
        <div className="graph-root-path">
          <p className="eyebrow">root path</p>
          {semanticRootPath.length > 0 ? (
            <div className="tag-row">
              {semanticRootPath.map((item, index) => (
                <button
                  className="action-chip"
                  key={item.id}
                  onClick={() => {
                    setSelected(item.id);
                    onQuery(item.label);
                  }}
                >
                  {index + 1}. {item.label}
                </button>
              ))}
            </div>
          ) : (
            <span>No full root path available for current selection.</span>
          )}
        </div>
        <div className="closure-summary" data-testid="graph-active-filter-readout">
          <span><strong>Layer</strong>{layer}</span>
          <span><strong>Edge</strong>{relation}</span>
          <span><strong>Query</strong>{query || "all"}</span>
          <span><strong>Visible edges</strong>{filteredEdges.length}</span>
          <span><strong>Selected</strong>{selectedLabel}</span>
        </div>
        <Canvas3D
          nodes={filteredNodes.map((node) => ({ ...node, z: node.z ?? 0, role: node.layer ?? node.cluster }))}
          links={filteredEdges}
          selected={selected}
          onSelect={setSelected}
          highlight={[...selectedLinks, ...rootPath]}
          testId="science-graph-3d-canvas"
        />
        {show2d && <div className="graph-canvas sigma-fallback" ref={sigmaContainerRef} data-testid="science-graph-canvas" />}
        <div className="detail-panel">
          <h3 data-testid="graph-selected-semantic-label">{selectedLabel}</h3>
          <p>{selectedNode?.statement_excerpt || "Route node for proof/evidence or simulation surface."}</p>
          <div className="tag-row">
            <span data-testid="graph-selected-node-id">{selectedNode?.id}</span>
            <span data-testid="graph-selected-technical-id">{selectedNode?.technical_id ?? selectedNode?.id}</span>
            <span data-testid="graph-selected-node-layer">{selectedNode?.layer ?? selectedNode?.cluster}</span>
            <span>{selectedNode?.demo_class || "route"}</span>
            <span>{selectedNode?.evidence_class || "public route"}</span>
          </div>
          <div className="action-chip-row" data-testid="graph-node-picks">
            {filteredNodes.slice(0, 6).map((node) => (
              <button
                key={node.id}
                className={`action-chip graph-node-pick ${node.id === selected ? "active" : ""}`}
                onClick={() => {
                  setSelected(node.id);
                  onQuery(node.semantic_label ?? node.label ?? node.id);
                }}
              >
                Select {node.semantic_label ?? node.label ?? node.id}
              </button>
            ))}
          </div>
          <div className="action-chip-row">
            {selectedNode?.detail?.wiki_query && <button className="action-chip" onClick={() => onOpenWiki?.(selectedNode.detail?.wiki_query || "")}>Inspect in wiki</button>}
            {selectedNode?.detail?.formula_query && <button className="action-chip" onClick={() => onOpenFormula?.(selectedNode.detail?.formula_query || "")}>Trace formula</button>}
            {selectedNode?.detail?.formula_id && <button className="action-chip" onClick={() => onOpenFormulaId?.(selectedNode.detail?.formula_id || "")}>Open formula id</button>}
            {selectedNode?.detail?.proof_target_id && <button className="action-chip" onClick={() => onOpenProofTarget?.(selectedNode?.detail?.proof_target_id ?? "")}>Open proof boundary</button>}
            {(selectedNode?.detail?.k_level || selectedNode?.detail?.k_level_id) && <button className="action-chip" onClick={() => onOpenKLevel?.((selectedNode?.detail?.k_level || selectedNode?.detail?.k_level_id) ?? "K0")}>Open K-level</button>}
            {(selectedNode?.detail?.k_level || selectedNode?.detail?.k_level_id || selectedNode?.layer === "k_level") && <button className="action-chip" onClick={() => onOpenWorkbench?.((selectedNode?.detail?.k_level || selectedNode?.detail?.k_level_id) || "K0")}>Open workbench</button>}
          </div>
          <div className="note-grid compact-notes">
            <div className="note"><strong>Proof target</strong><br />{selectedNode?.detail?.proof_target_id || "route hub / graph node"}</div>
            <div className="note" data-testid="graph-selected-outbound-index">
              <strong>Outbound link index</strong><br />
              wiki={selectedNode?.detail?.wiki_query ? "available" : "boundary"} / formulaQuery={selectedNode?.detail?.formula_query ? "available" : "boundary"} / formulaId={selectedNode?.detail?.formula_id ?? "boundary"} / proof={selectedNode?.detail?.proof_target_id ?? "boundary"} / k={selectedNode?.detail?.k_level || selectedNode?.detail?.k_level_id || (selectedNode?.layer === "k_level" ? selectedNode?.id : "boundary")}
            </div>
            <div className="note"><strong>Wiki query</strong><br />{selectedNode?.detail?.wiki_query || selectedNode?.label}</div>
            <div className="note" data-testid="graph-source-atom-context">
              <strong>Source atom context</strong><br />
              {selectedNode?.detail?.unit_id ?? selectedNode?.source_hash ?? selectedNode?.technical_id ?? "not a corpus atom"}
              <small>{selectedNode?.detail?.document_id ?? selectedNode?.detail?.chapter_id ?? "source context carried where the graph node has corpus provenance"}</small>
            </div>
            <div className="note" data-testid="graph-node-proof-closure-policy"><strong>Theorem vs proof closure</strong><br />closure_status: {selectedNode?.detail?.validation_status ?? selectedNode?.detail?.replay_status ?? "not proof-closed here"}<small>Open Evidence / Boundaries for proof-count policy; graph visualization does not close proofs.</small></div>
            <div className="note" data-testid="graph-selected-root-path"><strong>Root path</strong><br />{rootPath.map((nodeId) => graph.nodes.find((node) => node.id === nodeId)?.label ?? nodeId).slice(0, 8).join(" to ") || "not connected"}</div>
            <div className="note"><strong>Trust ladder</strong><br />{trustFromNode(selectedNode)}</div>
            <div className="note danger"><strong>Boundary</strong><br />{selectedNode?.detail?.nonclaim_boundary || "Node detail is navigation evidence, not proof by visualization."}</div>
          </div>
        </div>
      </main>
    </section>
  );
}
