import type { Atlas, DomainBenchmark, KLevel, SystemModel } from "./types";

export type SeriesPoint = { step: number; value: number; label?: string };
export type WorldlinePoint = { step: number; coherence: number; complexity: number; pressure: number; phase: string };
export type SimulationResult = {
  series: SeriesPoint[];
  score: number;
  band: string;
  components: Record<string, number>;
  interpretation: string;
};

function clamp(value: number, low = 0, high = 1) {
  return Math.max(low, Math.min(high, value));
}

export function worldline(params: Record<string, number>) {
  const steps = Math.round(params.steps ?? 72);
  const load = params.load ?? 0.62;
  const repair = params.repair ?? 0.38;
  const contradiction = params.contradiction ?? 0.58;
  const coupling = params.coupling ?? 0.44;
  const boundary = params.boundary ?? 0.42;
  let coherence = params.initial_coherence ?? 0.18;
  let complexity = params.initial_complexity ?? 0.08;
  const series: WorldlinePoint[] = [];
  const events: Array<{ step: number; event: string; coherence: number }> = [];
  let collapseStep: number | null = null;
  for (let step = 0; step <= steps; step += 1) {
    const pressure = load * (0.34 + complexity) + contradiction * (1 - boundary);
    const repairForce = repair * (1 - coherence) + boundary * 0.025;
    coherence = clamp(coherence + repairForce * 0.09 - pressure * 0.045 - coupling * complexity * 0.018);
    complexity = clamp(complexity + coherence * 0.021 + boundary * 0.006 - contradiction * 0.007, 0, 1.25);
    const phase = step < steps * 0.18 ? "birth" : step < steps * 0.42 ? "differentiation" : coherence > 0.34 ? "evolution" : "collapse";
    if (phase === "collapse" && collapseStep === null) {
      collapseStep = step;
      events.push({ step, event: "collapse-threshold-crossed", coherence: Number(coherence.toFixed(6)) });
    }
    if ([0, Math.floor(steps * 0.18), Math.floor(steps * 0.42), Math.floor(steps * 0.7), steps].includes(step)) {
      events.push({ step, event: phase, coherence: Number(coherence.toFixed(6)) });
    }
    series.push({ step, coherence: Number(coherence.toFixed(6)), complexity: Number(complexity.toFixed(6)), pressure: Number(pressure.toFixed(6)), phase });
  }
  const final = series[series.length - 1];
  return {
    series,
    events,
    collapseStep,
    score: final.coherence,
    band: final.coherence < 0.24 ? "collapsed" : final.coherence < 0.5 ? "fragile" : "evolving",
    interpretation: "A continuum survives when repair and boundary clarity outrun contradiction load and coupling drag."
  };
}

export function kElevator(levels: KLevel[], load = 0.65) {
  return levels.map((level, index) => {
    const confidence = typeof level.confidence === "number" ? level.confidence : 0.62;
    const replayBonus = level.simulation_summary?.reproducible ? 0.08 : -0.04;
    const stressPenalty = Math.max(0, load - 0.65) * 0.22;
    const stability = clamp(confidence - stressPenalty + replayBonus - index * 0.006);
    return { ...level, index, stability, band: stability >= 0.72 ? "stable" : stability >= 0.45 ? "review" : "frontier" };
  });
}

export function weakestNode(system: SystemModel) {
  const nodes = system.nodes ?? [];
  const dependencies = system.edges?.map((edge) => [edge.source, edge.target] as [string, string]) ?? system.dependencies;
  const outgoing = new Set(dependencies.map(([source]) => source));
  const candidates = nodes.filter((node) => outgoing.has(node.id) && !node.id.includes("collapse"));
  if (system.weakest_node && candidates.some((node) => node.id === system.weakest_node)) return system.weakest_node;
  if (candidates.length || nodes.length) return [...(candidates.length ? candidates : nodes)].sort((a, b) => b.vulnerability - a.vulnerability)[0].id;
  return system.kill_default;
}

export function killCascade(system: SystemModel, killNode = system.kill_default, shock = 0.82, mode: "selected" | "weakest" = "selected") {
  const trigger = mode === "weakest" ? weakestNode(system) : killNode;
  const dependencies = system.edges?.map((edge) => [edge.source, edge.target] as [string, string]) ?? system.dependencies;
  const adjacency = new Map<string, string[]>();
  for (const [source, target] of dependencies) {
    adjacency.set(source, [...(adjacency.get(source) ?? []), target]);
  }
  const terminal = new Set(dependencies.map(([, target]) => target).filter((node) => node.includes("collapse")));
  const queue: Array<{ node: string; path: string[] }> = [{ node: trigger, path: [trigger] }];
  const visited = new Set([trigger]);
  let path = [trigger];
  while (queue.length) {
    const current = queue.shift()!;
    if (terminal.has(current.node) || current.node.includes("collapse")) {
      path = current.path;
      break;
    }
    for (const next of adjacency.get(current.node) ?? []) {
      if (!visited.has(next)) {
        visited.add(next);
        queue.push({ node: next, path: [...current.path, next] });
      }
    }
  }
  let residual = 1;
  const nodeInfo = new Map((system.nodes ?? []).map((node) => [node.id, node]));
  const events = path.map((node, step) => {
    const vulnerability = nodeInfo.get(node)?.vulnerability ?? 0.42;
    const recovery = nodeInfo.get(node)?.recovery_capacity ?? 0.22;
    residual = clamp(residual - shock * (0.13 + step * 0.045 + vulnerability * 0.09) + recovery * 0.018);
    return {
      step,
      node,
      residual_coherence: Number(residual.toFixed(6)),
      connectivity: Number(Math.max(0, 1 - (step + 1) / Math.max(1, dependencies.length + 1)).toFixed(6)),
      flow: Number(Math.max(0, residual - vulnerability * 0.18).toFixed(6)),
      recovery_potential: Number(recovery.toFixed(6)),
      status: step === 0 ? "hit" : terminal.has(node) ? "terminal-collapse" : "propagated"
    };
  });
  const recovery = events.map((event) => ({
    step: event.step,
    value: Number(clamp(event.residual_coherence + event.recovery_potential * 0.28).toFixed(6)),
    label: event.node
  }));
  return {
    trigger,
    mode,
    path,
    events,
    recovery,
    affected_nodes: [...visited].sort(),
    connectivity_loss: Number((1 - (events.at(-1)?.connectivity ?? 1)).toFixed(6)),
    status: path[path.length - 1]?.includes("collapse") ? "terminal-path-found" : "bounded-damage"
  };
}

export function domainSeries(domain: DomainBenchmark) {
  return domain.benchmark_cases.slice(0, 30).map((row, index) => {
    const heldOut = String(row.held_out_role ?? "").includes("HELD_OUT");
    return {
      step: index,
      value: Math.min(1, 0.18 + (index % 7) * 0.07 + (heldOut ? 0.12 : 0)),
      label: String(row.case_id ?? row.observable_name ?? index)
    };
  });
}

export async function apiSimulation(simulationId: string, params: Record<string, number | string>) {
  const response = await fetch("/api/sim/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ simulation_id: simulationId, params })
  });
  if (!response.ok) throw new Error(`API simulation failed: ${response.status}`);
  return response.json();
}

export function runLegacySimulation(id: string, params: Record<string, number>): SimulationResult {
  const w = worldline(params);
  return {
    series: w.series.map((point) => ({ step: point.step, value: point.coherence, label: point.phase })),
    score: w.score,
    band: w.band,
    components: { load: params.load ?? 0.62, repair: params.repair ?? 0.38 },
    interpretation: w.interpretation
  };
}

export const runSimulation = runLegacySimulation;

export function transitionPressure(params: Record<string, number>): SimulationResult {
  const result = worldline({
    load: params.transition_pressure ?? 0.64,
    repair: params.corrective_capacity ?? 0.38,
    coupling: params.coupling_drag ?? 0.44,
    initial_coherence: params.initial_coherence ?? 0.52,
    steps: params.steps ?? 30,
    contradiction: Math.max(0, (params.transition_pressure ?? 0.64) - (params.corrective_capacity ?? 0.38))
  });
  return {
    series: result.series.map((point) => ({ step: point.step, value: point.coherence, label: point.phase })),
    score: result.score,
    band: result.band === "evolving" ? "stable" : result.band === "fragile" ? "recoverable" : "fragile",
    components: {
      pressure: params.transition_pressure ?? 0.64,
      correction: params.corrective_capacity ?? 0.38,
      drag: params.coupling_drag ?? 0.44
    },
    interpretation: result.interpretation
  };
}

export function evidenceSufficiency(params: Record<string, number>): SimulationResult {
  const components = {
    source_binding: params.source_binding ?? 0.82,
    dependency_closure: params.dependency_closure ?? 0.76,
    verification_strength: params.verification_strength ?? 0.7,
    nonclaim_clarity: params.nonclaim_clarity ?? 0.68
  };
  const score =
    components.source_binding * 0.25 +
    components.dependency_closure * 0.25 +
    components.verification_strength * 0.3 +
    components.nonclaim_clarity * 0.2;
  return {
    series: Object.entries(components).map(([label, value], step) => ({ step, label, value })),
    score: Number(score.toFixed(6)),
    band: score < 0.34 ? "insufficient" : score < 0.67 ? "reviewable" : "strong",
    components,
    interpretation: "Evidence sufficiency is a role balance, not a claim of external peer review."
  };
}

export function atlasCounts(atlas: Atlas) {
  return {
    kLevels: atlas.k_levels?.length ?? 0,
    domains: atlas.domain_benchmarks?.length ?? 0,
    gaps: atlas.research_gaps?.length ?? 0,
    openGaps: atlas.research_gap_summary?.open_count ?? atlas.research_gaps?.length ?? 0,
    closureRows: atlas.research_gap_summary?.closure_rows ?? atlas.closure_ledger?.length ?? 0,
    chapters: atlas.wiki?.chapters.length ?? 0,
    corpusAtoms: atlas.wiki?.corpus_summary?.atom_count ?? atlas.wiki?.corpus_atoms?.length ?? 0,
    formulas: atlas.formula_atlas?.length ?? 0,
    kWorlds: atlas.k_level_worlds?.length ?? 0,
    simulationLanes: atlas.simulation_worlds?.length ?? 0
  };
}
