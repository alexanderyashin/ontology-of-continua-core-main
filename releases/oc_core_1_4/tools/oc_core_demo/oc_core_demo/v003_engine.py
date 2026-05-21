from __future__ import annotations

import hashlib
import json
import math
import subprocess
import time
import zipfile
from collections import deque
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "oc-core-demo-api.v010"
DEMO_VERSION = "V010"
RELEASE_ORDINAL = "010"
RELEASE_LABEL = "OC Core 1.4 Demonstrator V010 Ideal RC"
PACKAGE_ROOT = Path(__file__).resolve().parent


def canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_read_json(path: Path) -> tuple[Any | None, dict[str, Any]]:
    probe = {
        "path": str(path),
        "found": path.exists(),
        "status": "PASS",
        "error": "",
        "load_error": "",
    }
    try:
        return read_json(path), probe
    except FileNotFoundError:
        probe["status"] = "MISSING"
        probe["load_error"] = "ledger_file_not_found"
        return None, probe
    except Exception as exc:  # pragma: no cover - defensive.
        probe["status"] = "CORRUPT"
        probe["load_error"] = str(exc)
        return None, probe


def _coerce_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def resource_rows(
    universe: dict[str, Any],
    resource_key: str,
    *,
    fallback_file: str | None = None,
    fallback_key: str | None = None,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    direct = _coerce_rows(universe.get(resource_key))
    if direct:
        return direct
    if not fallback_file:
        return []
    candidate_base = base_dir or find_data_dir()
    loaded, _probe = _safe_read_json(candidate_base / fallback_file)
    if isinstance(loaded, list):
        return _coerce_rows(loaded)
    if isinstance(loaded, dict):
        source = loaded.get(fallback_key or resource_key)
        return _coerce_rows(source)
    return []


def find_by_id(rows: list[dict[str, Any]], lookup_id: str, *, id_fields: tuple[str, ...] = ("id",)) -> dict[str, Any] | None:
    for row in rows:
        for key in id_fields:
            if str(row.get(key, "")) == str(lookup_id):
                return row
    return None


def data_dir_candidates(base_dir: Path | None = None) -> list[Path]:
    roots = []
    if base_dir:
        roots.append(base_dir)
    roots.extend([PACKAGE_ROOT.parent, Path.cwd()])
    candidates: list[Path] = []
    for root in roots:
        candidates.extend(
            [
                root / "web_dist" / "data",
                root / "web" / "public" / "data",
                root / "web" / "dist" / "data",
                root / "data",
            ]
        )
    return candidates


def find_data_dir(base_dir: Path | None = None, *, edition: str | None = None) -> Path:
    for candidate in data_dir_candidates(base_dir):
        atlas_path = candidate / "oc_universe_atlas.json"
        if not atlas_path.exists():
            continue
        if edition is None:
            return candidate
        try:
            payload = read_json(atlas_path)
        except Exception:
            continue
        if payload.get("edition") == edition:
            return candidate
    suffix = f" for edition {edition}" if edition else ""
    raise FileNotFoundError(f"oc_universe_atlas.json not found in V010 data directories{suffix}")


def load_universe(base_dir: Path | None = None, *, edition: str | None = None) -> dict[str, Any]:
    return read_json(find_data_dir(base_dir, edition=edition) / "oc_universe_atlas.json")


def envelope(kind: str, edition: str, payload: dict[str, Any], *, status: str = "PASS", message: str = "") -> dict[str, Any]:
    out = {
        "schema_version": SCHEMA_VERSION,
        "demo_version": payload.get("demo_version", DEMO_VERSION),
        "release_ordinal": payload.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": payload.get("release_label", RELEASE_LABEL),
        "status": status,
        "kind": kind,
        "edition": edition,
        "payload": payload,
        "message": message,
        "scientific_boundary": "Predictive and simulation outputs are lawful only inside their stated source, replay and nonclaim boundaries.",
        "generated_at_unix": int(time.time()),
    }
    out["result_hash"] = stable_hash({key: value for key, value in out.items() if key not in {"result_hash", "generated_at_unix"}})
    return out


def _num(params: dict[str, Any], key: str, default: float, low: float, high: float) -> float:
    value = params.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{key} must be a finite number")
    number = float(value)
    if number < low or number > high:
        raise ValueError(f"{key} out of range")
    return number


def _int(params: dict[str, Any], key: str, default: int, low: int, high: int) -> int:
    value = params.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    if value < low or value > high:
        raise ValueError(f"{key} out of range")
    return value


def run_worldline(params: dict[str, Any]) -> dict[str, Any]:
    steps = _int(params, "steps", 72, 12, 240)
    load = _num(params, "load", 0.62, 0.0, 1.5)
    repair = _num(params, "repair", 0.38, 0.0, 1.0)
    contradiction = _num(params, "contradiction", 0.58, 0.0, 1.5)
    coupling = _num(params, "coupling", 0.44, 0.0, 1.0)
    coherence = _num(params, "initial_coherence", 0.18, 0.0, 1.0)
    complexity = _num(params, "initial_complexity", 0.08, 0.0, 1.0)
    boundary = _num(params, "boundary", 0.42, 0.0, 1.0)
    series = []
    events = []
    collapse_step: int | None = None
    for step in range(steps + 1):
        pressure = load * (0.34 + complexity) + contradiction * (1.0 - boundary)
        repair_force = repair * (1.0 - coherence) + boundary * 0.025
        coherence = max(0.0, min(1.0, coherence + repair_force * 0.09 - pressure * 0.045 - coupling * complexity * 0.018))
        complexity = max(0.0, min(1.25, complexity + coherence * 0.021 + boundary * 0.006 - contradiction * 0.007))
        phase = "birth" if step < steps * 0.18 else "differentiation" if step < steps * 0.42 else "evolution" if coherence > 0.34 else "collapse"
        if phase == "collapse" and collapse_step is None:
            collapse_step = step
            events.append({"step": step, "event": "collapse-threshold-crossed", "coherence": round(coherence, 6)})
        if step in {0, int(steps * 0.18), int(steps * 0.42), int(steps * 0.7), steps}:
            events.append({"step": step, "event": phase, "coherence": round(coherence, 6)})
        series.append(
            {
                "step": step,
                "coherence": round(coherence, 6),
                "complexity": round(complexity, 6),
                "pressure": round(pressure, 6),
                "phase": phase,
            }
        )
    final = series[-1]
    status = "collapsed" if final["coherence"] < 0.24 else "fragile" if final["coherence"] < 0.5 else "evolving"
    return {
        "simulation_id": "worldline_birth_evolution_collapse",
        "params": {
            "steps": steps,
            "load": load,
            "repair": repair,
            "contradiction": contradiction,
            "coupling": coupling,
            "boundary": boundary,
        },
        "series": series,
        "events": events,
        "collapse_step": collapse_step,
        "status": status,
        "final": final,
        "assumptions": ["bounded deterministic OC diagnostic model", "state is illustrative unless bound to a replay-backed lane"],
        "nonclaim": "This simulation demonstrates OC dynamics; it does not prove a physical, chemical, biological or civilizational prediction by itself.",
    }


def run_k_elevator(params: dict[str, Any], atlas: dict[str, Any]) -> dict[str, Any]:
    levels = atlas.get("k_levels", [])
    if not levels:
        raise ValueError("atlas has no k_levels")
    start = _int(params, "start", 0, 0, len(levels) - 1)
    stop = _int(params, "stop", len(levels) - 1, start, len(levels) - 1)
    load = _num(params, "load", 0.65, 0.0, 1.5)
    rows = []
    for index, level in enumerate(levels[start : stop + 1], start=start):
        confidence = level.get("confidence")
        base = float(confidence) if isinstance(confidence, (int, float)) else 0.62
        stress_penalty = max(0.0, load - 0.65) * 0.22
        replay_bonus = 0.08 if level.get("simulation_summary", {}).get("reproducible") else -0.04
        stability = max(0.0, min(1.0, base - stress_penalty + replay_bonus - index * 0.006))
        rows.append(
            {
                "index": index,
                "level_id": level.get("level_id"),
                "meaning": level.get("meaning"),
                "domain_projections": level.get("domain_projections", []),
                "terminal_status": level.get("terminal_status"),
                "stability": round(stability, 6),
                "status_band": "stable" if stability >= 0.72 else "review" if stability >= 0.45 else "frontier",
                "preserved_invariants": level.get("preserved_invariants", ""),
            }
        )
    return {
        "simulation_id": "k_level_elevator",
        "params": {"start": start, "stop": stop, "load": load},
        "rows": rows,
        "assumptions": ["K-level status is imported from Logion ledgers", "elevator stability is a display diagnostic, not new proof"],
    }


def _system_by_id(atlas: dict[str, Any], system_id: str) -> dict[str, Any]:
    for system in atlas.get("system_zoo", []):
        if system.get("id") == system_id:
            return system
    raise ValueError(f"unknown system_id: {system_id}")


def _weakest_node(system: dict[str, Any]) -> str:
    nodes = [node for node in system.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in system.get("edges", []) if isinstance(edge, dict)]
    outgoing = {str(edge.get("source")) for edge in edges}
    candidates = [node for node in nodes if str(node.get("id")) in outgoing and "collapse" not in str(node.get("id"))]
    if system.get("weakest_node") and any(str(node.get("id")) == str(system["weakest_node"]) for node in candidates):
        return str(system["weakest_node"])
    if candidates or nodes:
        return str(max(candidates or nodes, key=lambda item: float(item.get("vulnerability", 0.0))).get("id"))
    return str(system.get("kill_default", ""))


def kill_cascade(params: dict[str, Any], atlas: dict[str, Any]) -> dict[str, Any]:
    system_id = str(params.get("system_id") or "civilization")
    system = _system_by_id(atlas, system_id)
    mode = str(params.get("mode") or "selected")
    if mode not in {"selected", "weakest"}:
        raise ValueError("mode must be selected or weakest")
    requested_node = str(params.get("kill_node") or system.get("kill_default") or "")
    kill_node = _weakest_node(system) if mode == "weakest" else requested_node
    shock = _num(params, "shock", 0.82, 0.0, 1.0)
    dependencies = [(str(edge.get("source")), str(edge.get("target"))) for edge in system.get("edges", []) if isinstance(edge, dict)]
    if not dependencies:
        dependencies = [(str(a), str(b)) for a, b in system.get("dependencies", [])]
    adjacency: dict[str, list[str]] = {}
    for source, target in dependencies:
        adjacency.setdefault(source, []).append(target)
    terminal_nodes = [node for node in {b for _, b in dependencies} if "collapse" in node]
    queue = deque([(kill_node, [kill_node])])
    visited = {kill_node}
    path = [kill_node]
    while queue:
        node, current_path = queue.popleft()
        if node in terminal_nodes or "collapse" in node:
            path = current_path
            break
        for nxt in adjacency.get(node, []):
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, [*current_path, nxt]))
    else:
        path = [kill_node, *adjacency.get(kill_node, [])]
    events = []
    residual = 1.0
    node_by_id = {str(node.get("id")): node for node in system.get("nodes", []) if isinstance(node, dict)}
    for step, node in enumerate(path):
        node_info = node_by_id.get(node, {})
        vulnerability = float(node_info.get("vulnerability", 0.42))
        recovery = float(node_info.get("recovery_capacity", 0.22))
        residual = max(0.0, min(1.0, residual - shock * (0.13 + step * 0.045 + vulnerability * 0.09) + recovery * 0.018))
        connectivity = max(0.0, 1.0 - (step + 1) / max(1, len(dependencies) + 1))
        events.append(
            {
                "step": step,
                "node": node,
                "residual_coherence": round(residual, 6),
                "connectivity": round(connectivity, 6),
                "flow": round(max(0.0, residual - vulnerability * 0.18), 6),
                "recovery_potential": round(recovery, 6),
                "status": "hit" if step == 0 else "terminal-collapse" if "collapse" in node else "propagated",
            }
        )
    return {
        "simulation_id": "kill_cascade",
        "system_id": system_id,
        "system_title": system.get("title"),
        "kill_node": kill_node,
        "mode": mode,
        "shortest_collapse_path": path,
        "events": events,
        "recovery": [{"step": row["step"], "value": round(min(1.0, row["residual_coherence"] + row["recovery_potential"] * 0.28), 6), "label": row["node"]} for row in events],
        "affected_nodes": sorted(visited),
        "connectivity_loss": round(1.0 - (events[-1]["connectivity"] if events else 1.0), 6),
        "status": "terminal-path-found" if path and "collapse" in path[-1] else "bounded-damage",
        "assumptions": ["collapse path uses demonstrator dependency edges", "shortest path is diagnostic and local to this model"],
        "nonclaim": system.get("nonclaim", ""),
    }


def domain_anchor(params: dict[str, Any], atlas: dict[str, Any]) -> dict[str, Any]:
    domains = atlas.get("domain_benchmarks", [])
    if not domains:
        raise ValueError("atlas has no domain benchmarks")
    index = _int(params, "domain_index", 0, 0, len(domains) - 1)
    domain = domains[index]
    cases = domain.get("benchmark_cases", [])
    points = []
    for idx, case in enumerate(cases[:30]):
        held_out = "HELD_OUT" in str(case.get("held_out_role", "")).upper()
        base = 0.18 + (idx % 7) * 0.07 + (0.12 if held_out else 0.0)
        points.append(
            {
                "step": idx,
                "case_id": case.get("case_id"),
                "value": round(min(1.0, base), 6),
                "role": "held-out" if held_out else "calibration",
                "observable": case.get("observable_name", ""),
            }
        )
    return {
        "simulation_id": "domain_anchor_lab",
        "domain": domain,
        "series": points,
        "status": domain.get("promotion_state", "bounded"),
        "nonclaim": domain.get("nonclaim_boundary", ""),
    }


def corpus_search(atlas: dict[str, Any], query: str = "", limit: int = 25) -> dict[str, Any]:
    query = query.strip().lower()[:180]
    atoms = atlas.get("wiki", {}).get("corpus_atoms", [])
    rows = [row for row in atoms if isinstance(row, dict) and (not query or query in str(row.get("search_text", "")).lower())]
    rows = rows[: max(1, min(100, limit))]
    return {
        "query": query,
        "returned": len(rows),
        "corpus_summary": atlas.get("wiki", {}).get("corpus_summary", {}),
        "rows": rows,
        "result_hash": stable_hash({"query": query, "rows": rows}),
        "nonclaim": "Corpus search returns reader-text atoms and source hashes; it is navigation evidence, not proof by itself.",
    }


def formula_search(atlas: dict[str, Any], query: str = "", limit: int = 25) -> dict[str, Any]:
    query = query.strip().lower()[:180]
    formulas = atlas.get("formula_atlas", [])
    if not formulas:
        formulas = atlas.get("wiki", {}).get("formulas", [])
    rows = [row for row in formulas if isinstance(row, dict) and (not query or query in canonical(row).lower())]
    rows = rows[: max(1, min(100, limit))]
    return {
        "query": query,
        "returned": len(rows),
        "total_formulas": len([row for row in formulas if isinstance(row, dict)]),
        "rows": rows,
        "result_hash": stable_hash({"query": query, "rows": rows}),
        "nonclaim": "Formula rows are curated symbolic surfaces. Raw registry candidates stay in formalization obligations until title, operators, consequence, chart and source boundary are complete.",
    }


def quality_report(atlas: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    graph = atlas.get("science_graph_v010") or atlas.get("science_graph_v008") or atlas.get("science_graph_v007") or atlas.get("graph") or {}
    wiki = atlas.get("wiki") or {}
    corpus_summary = wiki.get("corpus_summary", {})
    formula_total = len(atlas.get("formula_atlas", []) or wiki.get("formulas", []))
    corpus_total = len(wiki.get("corpus_atoms", []))
    model_cells = len(atlas.get("model_comparison_matrix", []))
    mission_total = len(atlas.get("system_architect_missions", []))
    closure_total = len(atlas.get("closure_ledger", []))
    try:
        report_data_dir = find_data_dir()
    except Exception:
        report_data_dir = None
    cerberus_review: dict[str, Any] = {}
    cerberus_backlog: dict[str, Any] = {}
    if report_data_dir is not None:
        loaded_review, _ = _safe_read_json(report_data_dir / "cerberus_v010_review.json")
        loaded_backlog, _ = _safe_read_json(report_data_dir / "cerberus_v010_repair_backlog.json")
        if isinstance(loaded_review, dict):
            cerberus_review = loaded_review
        if isinstance(loaded_backlog, dict):
            cerberus_backlog = loaded_backlog
    cerberus_findings = [row for row in cerberus_review.get("findings", []) if isinstance(row, dict)]
    cerberus_unresolved = [
        row for row in cerberus_findings if row.get("repair_mapping") == "DEFERRED_WITH_REASON"
    ]
    cerberus_counts_by_surface: dict[str, int] = {}
    cerberus_counts_by_head: dict[str, int] = {}
    for row in cerberus_unresolved:
        surface = str(row.get("target_surface") or "unknown")
        head = str(row.get("head") or "unknown")
        cerberus_counts_by_surface[surface] = cerberus_counts_by_surface.get(surface, 0) + 1
        cerberus_counts_by_head[head] = cerberus_counts_by_head.get(head, 0) + 1
    unresolved = sum(
        1 for row in atlas.get("closure_ledger", []) if str(row.get("closure_status", "")).startswith("OPEN")
    ) if isinstance(atlas.get("closure_ledger", []), list) else 0
    incomplete = [
        key
        for key in ("proof_routes", "formula_atlas", "corpus_index", "m_spaces", "system_templates", "didactic_routes")
        if not atlas.get(key)
    ]
    payload = {
        "schema_version": "oc-core-demo-quality-report.v010",
        "demo_version": atlas.get("demo_version", DEMO_VERSION),
        "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": atlas.get("release_label", RELEASE_LABEL),
        "status": "FAIL" if (strict and incomplete) else "PASS",
        "corpus_total": corpus_total,
        "formula_total": formula_total,
        "graph_node_total": len(graph.get("nodes", [])),
        "graph_edge_total": len(graph.get("edges", [])),
        "proof_route_total": len(atlas.get("proof_routes", [])),
        "closure_open_total": unresolved,
        "surface_presence_ok": len(incomplete) == 0,
        "missing_surfaces": incomplete,
        "model_cells": model_cells,
        "mission_total": mission_total,
        "closure_total": closure_total,
        "cerberus_status": cerberus_review.get("status", "UNKNOWN" if not cerberus_review else ""),
        "cerberus_unresolved_total": int(cerberus_review.get("summary", {}).get("unresolved_total", len(cerberus_unresolved))) if cerberus_review else 0,
        "cerberus_unresolved_medium_plus_total": int(
            cerberus_review.get("summary", {}).get("unresolved_medium_plus_total", cerberus_review.get("summary", {}).get("unresolved_medium_or_worse_total", 0))
        ) if cerberus_review else 0,
        "cerberus_unresolved_by_surface": dict(sorted(cerberus_counts_by_surface.items())),
        "cerberus_unresolved_by_head": dict(sorted(cerberus_counts_by_head.items())),
        "cerberus_repair_backlog_hash": cerberus_backlog.get("backlog_hash", ""),
        "cerberus_repair_backlog_open_total": int(cerberus_backlog.get("summary", {}).get("open_total", 0)) if cerberus_backlog else 0,
        "target_coverage": {
            "didactic_routes": len(atlas.get("didactic_routes", [])),
            "reviewer_objections": len(atlas.get("reviewer_objection_routes", [])),
            "k_axes": len(atlas.get("k_axes", [])),
            "system_templates": len(atlas.get("system_templates", [])),
            "m_spaces": len(atlas.get("m_spaces", [])),
            "workbench_schema_rows": len(atlas.get("system_workbench_schema", {}).get("rows", [])),
        },
        "corpus_summary": corpus_summary,
        "result_hash": stable_hash({
            "release": atlas.get("release_ordinal"),
            "missing": incomplete,
            "open": unresolved,
            "cerberus_unresolved": cerberus_review.get("summary", {}).get("unresolved_total", 0) if cerberus_review else 0,
        }),
        "nonclaim": "Quality-report is a reviewer-facing metadata packet and does not encode scientific correctness.",
    }
    return payload


def corpus_completeness(atlas: dict[str, Any]) -> dict[str, Any]:
    graph = atlas.get("science_graph_v010") or atlas.get("science_graph_v008") or atlas.get("science_graph_v007") or atlas.get("graph") or {}
    wiki = atlas.get("wiki") or {}
    corpus = wiki.get("corpus_atoms", [])
    formulas = wiki.get("formulas", [])
    expected_layers = 12
    expected_nodes = graph.get("summary", {}).get("node_count", len(graph.get("nodes", [])))
    present_layers = set()
    for node in graph.get("nodes", []):
        layer = node.get("layer") or node.get("cluster")
        if layer:
            present_layers.add(layer)
    payload = {
        "schema_version": "oc-core-demo-corpus-completeness.v010",
        "demo_version": atlas.get("demo_version", DEMO_VERSION),
        "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": atlas.get("release_label", RELEASE_LABEL),
        "corpus_atom_total": len(corpus),
        "corpus_formula_total": len(formulas),
        "graph_node_total": len(graph.get("nodes", [])),
        "science_graph_node_layers": len(present_layers),
        "graph_edges": len(graph.get("edges", [])),
        "has_science_graph_v010": bool(atlas.get("science_graph_v010")),
        "node_layer_coverage": {
            "present": sorted(present_layers),
            "required_minimum": expected_layers,
            "meets_minimum": len(present_layers) >= expected_layers,
        },
        "missing_required_surfaces": [
            key
            for key in ("m_spaces", "system_templates", "k_axes", "k_levels", "wiki", "proof_routes")
            if not atlas.get(key)
        ],
        "completeness_scores": {
            "corpus": min(1.0, len(corpus) / max(1, 1000)),
            "formulas": min(1.0, len(formulas) / max(1, 1000)),
            "graphs": min(1.0, expected_nodes / max(1, 1200)),
        },
        "expected_nodes": expected_nodes,
        "result_hash": stable_hash({
            "layers": sorted(present_layers),
            "atoms": len(corpus),
            "formulas": len(formulas),
            "nodes": expected_nodes,
        }),
        "nonclaim": "Completeness metrics indicate surface completeness, not inferential truth claims.",
    }
    return payload


def formula_quality(atlas: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    wiki = atlas.get("wiki") or {}
    formulas = [row for row in atlas.get("formula_atlas", []) if isinstance(row, dict)]
    if not formulas:
        formulas = [row for row in wiki.get("formulas", []) if isinstance(row, dict)]

    def _formula_text(row: dict[str, Any]) -> str:
        return str(row.get("formula_text") or row.get("expression") or row.get("rendered_math") or "").strip()

    missing_latex = sum(1 for row in formulas if not _formula_text(row))
    missing_ids = sum(1 for row in formulas if not str(row.get("formula_id", "")).strip())
    weak_rows = [
        row
        for row in formulas
        if not _formula_text(row)
        or not str(row.get("semantic_title") or row.get("title") or "").strip()
        or not str(row.get("interpretation") or "").strip()
        or str(row.get("quality_status") or row.get("render_quality") or "").upper() in {"", "INVALID", "BROKEN"}
    ]
    table_contract_gaps = [
        row
        for row in formulas
        if not str(row.get("semantic_title") or row.get("formula_title") or "").strip()
        or not str(row.get("domain") or "").strip()
        or not (row.get("operator_meanings") or row.get("operator_glossary") or row.get("operators") or row.get("operator_summary"))
        or not row.get("consequences")
        or not (row.get("diagnostic_chart") or row.get("chart_spec"))
        or not (row.get("source_boundary") or row.get("source_refs") or row.get("source_atom_id") or row.get("nonclaim_boundary") or row.get("boundary"))
    ]
    missing_typed_signature = [
        row for row in formulas if not (row.get("typed_symbol_signatures") or row.get("symbol_signature") or row.get("operator_glossary"))
    ]
    missing_chart_provenance = [
        row for row in formulas
        if not (
            row.get("chart_provenance")
            or (isinstance(row.get("chart_spec"), dict) and row.get("chart_spec", {}).get("provenance"))
            or (isinstance(row.get("diagnostic_chart"), dict) and row.get("diagnostic_chart", {}).get("provenance"))
        )
    ]
    source_exception_rows = [
        row for row in formulas if row.get("source_exceptions") and not (row.get("source_boundary") or row.get("nonclaim_boundary"))
    ]
    strict_validation_rule_inventory = [
        {
            "formula_id": row.get("formula_id"),
            "semantic_title": row.get("semantic_title") or row.get("formula_title"),
            "assumption_bodies": row.get("assumption_bodies", []),
            "validation_rule_bodies": row.get("validation_rule_bodies", []),
            "rule_ids": [
                rule.get("rule_id")
                for rule in row.get("validation_rule_bodies", [])
                if isinstance(rule, dict) and rule.get("rule_id")
            ],
        }
        for row in formulas
    ]
    obligation_rows = atlas.get("formula_formalization_obligations", {}).get("rows", [])
    strict_pass = (
        len(table_contract_gaps) == 0
        and len(weak_rows) == 0
        and missing_latex == 0
        and missing_ids == 0
        and len(missing_typed_signature) == 0
        and len(missing_chart_provenance) == 0
        and len(source_exception_rows) == 0
    )
    payload = {
        "schema_version": "oc-core-demo-formula-quality.v010",
        "demo_version": atlas.get("demo_version", DEMO_VERSION),
        "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": atlas.get("release_label", RELEASE_LABEL),
        "formula_total": len(formulas),
        "missing_expression_count": missing_latex,
        "missing_formula_id_count": missing_ids,
        "render_gaps_count": len(weak_rows),
        "table_contract_gaps_count": len(table_contract_gaps),
        "missing_typed_symbol_signature_count": len(missing_typed_signature),
        "missing_chart_provenance_count": len(missing_chart_provenance),
        "unbounded_source_exception_count": len(source_exception_rows),
        "formalization_obligations_count": len(obligation_rows) if isinstance(obligation_rows, list) else 0,
        "strict_requested": strict,
        "strict_status": "PASS" if strict_pass else "FAIL_CLOSED",
        "quality_score": round(
            max(
                0.0,
                min(
                    1.0,
                    1.0
                    - 0.5 * (missing_latex / max(1, len(formulas)))
                    - 0.25 * (missing_ids / max(1, len(formulas)))
                    - 0.25 * (len(weak_rows) / max(1, len(formulas))),
                ),
            ),
            4,
        ),
        "sample_gaps": weak_rows[:24],
        "sample_table_contract_gaps": table_contract_gaps[:24],
        "sample_typed_signature_gaps": missing_typed_signature[:12],
        "sample_chart_provenance_gaps": missing_chart_provenance[:12],
        "sample": formulas[:30],
        "strict_validation_rule_inventory": strict_validation_rule_inventory,
        "strict_validation_rule_inventory_hash": stable_hash(strict_validation_rule_inventory),
        "result_hash": stable_hash({
            "total": len(formulas),
            "missing_expression_count": missing_latex,
            "missing_ids": missing_ids,
            "typed_signature_gaps": len(missing_typed_signature),
            "chart_provenance_gaps": len(missing_chart_provenance),
        }),
        "nonclaim": "Formula quality verifies the user-facing table contract; no mathematical validity claims are implied.",
    }
    return payload


def k_examples(atlas: dict[str, Any]) -> dict[str, Any]:
    k_levels = atlas.get("k_levels", [])
    k_worlds = atlas.get("k_level_worlds", [])
    axes = atlas.get("k_axes", [])
    axis_examples: list[dict[str, Any]] = []
    for axis in (axes if isinstance(axes, list) else []):
        axis_examples.append(
            {
                "axis_id": axis.get("axis_id", ""),
                "name": axis.get("name", ""),
                "summary": axis.get("summary", ""),
            }
        )
    world_examples = []
    for world in (k_worlds[:16] if isinstance(k_worlds, list) else []):
        if isinstance(world, dict):
            world_examples.append(
                {
                    "k_level": world.get("k_level"),
                    "status": world.get("terminal_status", ""),
                    "replays": world.get("simulation_summary", {}),
                }
            )
    levels = []
    for level in (k_levels if isinstance(k_levels, list) else []):
        if isinstance(level, dict):
            levels.append(
                {
                    "level_id": level.get("level_id"),
                    "meaning": level.get("meaning"),
                    "terminal_status": level.get("terminal_status"),
                    "invariant_count": len(level.get("preserved_invariants", []) or []),
                }
            )
    missing_projection = 13 - len(k_levels) if isinstance(k_levels, list) else 13
    return {
        "schema_version": "oc-core-demo-k-examples.v010",
        "demo_version": atlas.get("demo_version", DEMO_VERSION),
        "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": atlas.get("release_label", RELEASE_LABEL),
        "k_level_total": len(k_levels) if isinstance(k_levels, list) else 0,
        "axis_total": len(axes) if isinstance(axes, list) else 0,
        "k_m_hierarchy_depth": len(k_levels) if isinstance(k_levels, list) else 0,
        "high_signal_examples": levels[:32],
        "sample_k_levels": axis_examples[:32],
        "notable_examples": world_examples[:24],
        "completeness": {
            "missing_k_levels": max(0, missing_projection),
            "has_13_levels": len(k_levels) >= 13 if isinstance(k_levels, list) else False,
        },
        "result_hash": stable_hash({"levels": len(k_levels) if isinstance(k_levels, list) else 0, "axes": len(axes) if isinstance(axes, list) else 0}),
        "nonclaim": "K/M examples provide navigation scaffolding and bounded simulation context, not proof completion.",
    }


def node_detail(atlas: dict[str, Any], node_id: str) -> dict[str, Any]:
    graph_nodes = atlas.get("graph", {}).get("nodes", [])
    node = next((row for row in graph_nodes if isinstance(row, dict) and row.get("id") == node_id), None)
    if node is None:
        raise ValueError(f"unknown node_id: {node_id}")
    proof_id = node.get("detail", {}).get("proof_target_id") or node_id
    proof = next((row for row in atlas.get("proof_routes", []) if isinstance(row, dict) and row.get("target_id") == proof_id), None)
    formula_query = node.get("detail", {}).get("formula_query", "")
    corpus_query = node.get("detail", {}).get("wiki_query", "")
    return {
        "node": node,
        "proof_route": proof,
        "corpus_matches": corpus_search(atlas, corpus_query, 5)["rows"],
        "formula_matches": formula_search(atlas, formula_query, 5)["rows"],
        "result_hash": stable_hash({"node": node, "proof": proof}),
        "nonclaim": "Node detail links graph, corpus, formula and proof surfaces; clickability is not proof closure.",
    }


def science_graph(atlas: dict[str, Any], *, include_rows: bool = True) -> dict[str, Any]:
    graph = atlas.get("science_graph_v010") or atlas.get("science_graph_v008") or atlas.get("science_graph_v007") or atlas.get("science_graph_v006") or atlas.get("graph") or {}
    if not isinstance(graph, dict):
        graph = {}
    payload = {
        "schema_version": graph.get("schema_version", "oc-core-demo-science-graph.v010"),
        "root_node_id": graph.get("root_node_id", ""),
        "root_principle": graph.get("root_principle", ""),
        "summary": graph.get("summary", {}),
        "required_invariants": {
            "root_to_public_targets": True,
            "metaontology_to_k0_k12": True,
            "theorem_to_formula_to_proof_or_boundary": True,
            "domain_projection_visibility": True,
        },
        "nonclaim": "The science graph is a structured navigation and traceability surface; it is not proof by visualization.",
    }
    if include_rows:
        payload["nodes"] = graph.get("nodes", [])
        payload["edges"] = graph.get("edges", [])
    payload["result_hash"] = stable_hash(payload)
    return payload


def surface_graph(atlas: dict[str, Any], *, include_rows: bool = True) -> dict[str, Any]:
    graph = atlas.get("demonstrator_surface_graph")
    if not isinstance(graph, dict):
        graph = {}
    prebuild_gate = graph.get("prebuild_gate", {})
    graph_ready = bool(graph.get("nodes")) and (not isinstance(prebuild_gate, dict) or prebuild_gate.get("status", "PASS") == "PASS")
    payload = {
        "schema_version": graph.get("schema_version", "oc-core-demo-surface-graph.v010"),
        "demo_version": atlas.get("demo_version", DEMO_VERSION),
        "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": atlas.get("release_label", RELEASE_LABEL),
        "status": "PASS" if graph_ready else "FAIL_CLOSED",
        "summary": graph.get("summary", {}),
        "prebuild_gate": prebuild_gate,
        "surface_graph_hash": graph.get("surface_graph_hash", ""),
        "nonclaim": "The surface graph is a pre-build product contract for pages, controls, fields, sources and clickability. It is not scientific evidence.",
    }
    if include_rows:
        payload["surfaces"] = graph.get("surfaces", [])
        payload["controls"] = graph.get("controls", [])
        payload["routes"] = graph.get("routes", [])
        payload["nodes"] = graph.get("nodes", [])
        payload["edges"] = graph.get("edges", [])
    payload["result_hash"] = stable_hash(payload)
    return payload


def desktop_smoke() -> dict[str, Any]:
    shortcut = Path.home() / "Desktop" / "OC Core 1.4 Demonstrator.lnk"
    workspace_atlas_path = PACKAGE_ROOT.parent / "web" / "dist" / "data" / "oc_universe_atlas.json"
    probe: dict[str, Any] = {
        "schema_version": "oc-core-demo-desktop-smoke.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "shortcut_exists": shortcut.exists(),
        "shortcut_path_hash": stable_hash(str(shortcut)),
        "target_path_hash": "",
        "working_directory_hash": "",
        "target_exists": False,
        "working_directory_exists": False,
        "points_to_v010_runtime": False,
        "workspace_atlas_found": workspace_atlas_path.exists(),
        "workspace_atlas_path_hash": stable_hash(str(workspace_atlas_path)),
        "runtime_atlas_found": False,
        "runtime_freshness_manifest_found": False,
        "runtime_matches_workspace": False,
        "workspace_determinism_hash": "",
        "runtime_determinism_hash": "",
        "workspace_formula_count": 0,
        "runtime_formula_count": 0,
        "workspace_surface_graph_hash": "",
        "runtime_surface_graph_hash": "",
        "runtime_demo_version": "",
        "runtime_release_ordinal": "",
        "runtime_build_mtime": "",
        "target_mtime": "",
        "status": "FAIL_CLOSED",
        "nonclaim": "Desktop smoke verifies local shortcut routing and runtime freshness only; it is not a public artifact safety report.",
    }
    if not shortcut.exists():
        probe["message"] = "desktop shortcut not found"
        probe["result_hash"] = stable_hash(probe)
        return probe
    shortcut_literal = str(shortcut).replace("'", "''")
    command = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"
        + shortcut_literal
        + "'); [pscustomobject]@{TargetPath=$s.TargetPath;WorkingDirectory=$s.WorkingDirectory;IconLocation=$s.IconLocation} | ConvertTo-Json -Compress"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        probe["message"] = f"shortcut probe failed: {exc}"
        probe["result_hash"] = stable_hash(probe)
        return probe
    probe["probe_returncode"] = proc.returncode
    if proc.returncode != 0:
        probe["message"] = (proc.stderr or proc.stdout or "shortcut probe returned nonzero").strip()[:500]
        probe["result_hash"] = stable_hash(probe)
        return probe
    try:
        link = json.loads(proc.stdout)
    except Exception as exc:
        probe["message"] = f"shortcut probe returned invalid JSON: {exc}"
        probe["result_hash"] = stable_hash(probe)
        return probe
    target = Path(str(link.get("TargetPath", "")))
    workdir = Path(str(link.get("WorkingDirectory", ""))) if link.get("WorkingDirectory") else target.parent
    target_text = str(target)
    probe.update(
        {
            "target_path_hash": stable_hash(target_text),
            "working_directory_hash": stable_hash(str(workdir)),
            "target_basename": target.name,
            "working_directory_basename": workdir.name,
            "target_exists": target.exists(),
            "working_directory_exists": workdir.exists(),
            "icon_present": bool(link.get("IconLocation")),
            "points_to_v010_runtime": ("OC_Core_1_4_Demonstrator" in target_text and "oc_core_14_demonstrator_portable" in target_text),
        }
    )
    if target.exists():
        probe["target_mtime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(target.stat().st_mtime))

    runtime_data_candidates = [
        workdir / "_internal" / "web_dist" / "data",
        target.parent / "_internal" / "web_dist" / "data",
        workdir / "web_dist" / "data",
        target.parent / "web_dist" / "data",
    ]
    runtime_data_dir = next((candidate for candidate in runtime_data_candidates if (candidate / "oc_universe_atlas.json").exists()), None)
    runtime_atlas: dict[str, Any] = {}
    workspace_atlas: dict[str, Any] = {}
    if runtime_data_dir:
        runtime_atlas_path = runtime_data_dir / "oc_universe_atlas.json"
        probe["runtime_atlas_found"] = True
        probe["runtime_atlas_path_hash"] = stable_hash(str(runtime_atlas_path))
        probe["runtime_build_mtime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(runtime_atlas_path.stat().st_mtime))
        runtime_atlas = read_json(runtime_atlas_path, {})
        manifest_path = runtime_data_dir / "runtime_freshness_manifest.json"
        if manifest_path.exists():
            probe["runtime_freshness_manifest_found"] = True
            probe["runtime_freshness_manifest_hash"] = stable_hash(read_json(manifest_path, {}))
    if workspace_atlas_path.exists():
        workspace_atlas = read_json(workspace_atlas_path, {})

    runtime_surface = runtime_atlas.get("demonstrator_surface_graph", {}) if isinstance(runtime_atlas, dict) else {}
    workspace_surface = workspace_atlas.get("demonstrator_surface_graph", {}) if isinstance(workspace_atlas, dict) else {}
    probe.update(
        {
            "runtime_demo_version": runtime_atlas.get("demo_version", "") if isinstance(runtime_atlas, dict) else "",
            "runtime_release_ordinal": runtime_atlas.get("release_ordinal", "") if isinstance(runtime_atlas, dict) else "",
            "runtime_determinism_hash": runtime_atlas.get("determinism_hash", "") if isinstance(runtime_atlas, dict) else "",
            "workspace_determinism_hash": workspace_atlas.get("determinism_hash", "") if isinstance(workspace_atlas, dict) else "",
            "runtime_formula_count": len(runtime_atlas.get("formula_atlas", [])) if isinstance(runtime_atlas, dict) else 0,
            "workspace_formula_count": len(workspace_atlas.get("formula_atlas", [])) if isinstance(workspace_atlas, dict) else 0,
            "runtime_surface_graph_hash": runtime_surface.get("surface_graph_hash", "") if isinstance(runtime_surface, dict) else "",
            "workspace_surface_graph_hash": workspace_surface.get("surface_graph_hash", "") if isinstance(workspace_surface, dict) else "",
        }
    )
    freshness_checks = {
        "runtime_atlas_found": probe["runtime_atlas_found"],
        "workspace_atlas_found": probe["workspace_atlas_found"],
        "version_is_v010": probe["runtime_demo_version"] == DEMO_VERSION and probe["runtime_release_ordinal"] == RELEASE_ORDINAL,
        "atlas_hash_matches": bool(probe["runtime_determinism_hash"]) and probe["runtime_determinism_hash"] == probe["workspace_determinism_hash"],
        "formula_count_matches": probe["runtime_formula_count"] == probe["workspace_formula_count"] and probe["runtime_formula_count"] < 100,
        "surface_graph_hash_matches": bool(probe["runtime_surface_graph_hash"]) and probe["runtime_surface_graph_hash"] == probe["workspace_surface_graph_hash"],
    }
    probe["freshness_checks"] = freshness_checks
    probe["runtime_matches_workspace"] = all(freshness_checks.values())
    route_ok = probe["target_exists"] and probe["working_directory_exists"] and probe["points_to_v010_runtime"]
    probe["status"] = "PASS" if route_ok and probe["runtime_matches_workspace"] else "FAIL_CLOSED"
    if probe["status"] == "PASS":
        probe["message"] = "shortcut target resolved and runtime atlas matches workspace V010 build"
    elif route_ok:
        probe["message"] = "shortcut target exists but runtime is stale or does not match workspace V010 build"
    else:
        probe["message"] = "shortcut target missing or not pointed at V010 runtime"
    probe["result_hash"] = stable_hash(probe)
    return probe


def cerberus_summary(
    atlas: dict[str, Any],
    data_dir: Path | None = None,
    *,
    requested_version: str | None = None,
    require_strict_release_gate: bool = False,
) -> dict[str, Any]:
    data_dir = data_dir or find_data_dir()
    requested = (requested_version or DEMO_VERSION).upper()
    if requested in {"V008", "008"}:
        review_name = "cerberus_v008_review.json"
        repair_name = "cerberus_v008_repair_ledger.json"
        iteration_name = "v008_iteration_ledger.json"
        visual_name = "visual_quality_manifest.json"
    elif requested in {"V010", "010"}:
        review_name = "cerberus_v010_review.json"
        repair_name = "cerberus_v010_repair_ledger.json"
        iteration_name = "v010_iteration_ledger.json"
        visual_name = "v010_visual_quality_manifest.json"
    else:
        review_name = "demonstrator_cerberus_review.json"
        repair_name = "demonstrator_cerberus_repair_ledger.json"
        iteration_name = "v010_iteration_ledger.json"
        visual_name = "visual_quality_manifest.json"
    review, review_probe = _safe_read_json(data_dir / review_name)
    repair, repair_probe = _safe_read_json(data_dir / repair_name)
    iteration, iteration_probe = _safe_read_json(data_dir / iteration_name)
    visual, visual_probe = _safe_read_json(data_dir / visual_name)
    review = review if isinstance(review, dict) else {"status": "FAIL_CLOSED", "message": "review ledger missing or invalid", "finding_summary": {}}
    repair = repair if isinstance(repair, dict) else {"rows": []}
    iteration = iteration if isinstance(iteration, dict) else {}
    visual = visual if isinstance(visual, dict) else {}

    if not isinstance(review.get("release_ordinal"), str):
        review["release_ordinal"] = RELEASE_ORDINAL
    if not isinstance(review.get("demo_version"), str):
        review["demo_version"] = atlas.get("demo_version", DEMO_VERSION)
    if not isinstance(review.get("release_label"), str):
        review["release_label"] = atlas.get("release_label", RELEASE_LABEL)

    findings = [row for row in review.get("findings", []) if isinstance(row, dict)]
    unresolved_medium_plus_rows = [
        row
        for row in findings
        if row.get("severity") in {"critical", "high", "medium"} and row.get("repair_mapping") == "DEFERRED_WITH_REASON"
    ]
    unresolved_all_rows = [row for row in findings if row.get("repair_mapping") == "DEFERRED_WITH_REASON"]

    iteration_rows = iteration.get("rows") if isinstance(iteration, dict) else None
    if not isinstance(iteration_rows, list):
        iteration_rows = []

    provider_gate = {
        "provider_id": review.get("provider_id", "CODEX_CLI_CHATGPT"),
        "provider_available": bool(review.get("actual_live_llm_invocation")),
        "actual_live_llm_invocation": bool(review.get("actual_live_llm_invocation")),
        "status": "PASS"
        if bool(review.get("actual_live_llm_invocation")) and review.get("status") == "PASS"
        else "FAIL_CLOSED",
        "failure_reason": (
            "provider unavailable" if not bool(review.get("actual_live_llm_invocation")) else ""
        ).strip(),
    }
    review_loading = {
        "review_ledger": review_probe,
        "repair_ledger": repair_probe,
    }
    if review_loading["review_ledger"]["status"] != "PASS":
        provider_gate["status"] = "FAIL_CLOSED"
        provider_gate["failure_reason"] = "ledger load failure"

    visual_errors: list[str] = []
    if not isinstance(visual, dict):
        visual_errors.append("visual_quality_manifest_missing")
    elif visual.get("status") != "PASS":
        visual_errors.append("visual_quality_manifest_invalid")

    iteration_errors: list[str] = []
    if requested in {"V010", "010"} and len(iteration_rows) != 20:
        iteration_errors.append("iteration_ledger_entry_count_mismatch")

    status = "PASS"
    if provider_gate["status"] != "PASS":
        status = "FAIL_CLOSED"
    if review.get("status") != "PASS":
        status = "FAIL_CLOSED"
    if not isinstance(repair.get("rows"), list):
        status = "FAIL_CLOSED"
        repair["rows"] = []

    summary = review.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    unresolved_critical_high = summary.get("unresolved_critical_high_total", 0)
    unresolved_medium_plus = summary.get(
        "unresolved_medium_or_worse_total",
        summary.get("unresolved_medium_plus_total", 0),
    )
    if requested in {"V010", "010"}:
        unresolved_medium_plus = int(summary.get("unresolved_medium_or_worse_total", unresolved_medium_plus))
    unresolved_total = int(summary.get("unresolved_total", unresolved_medium_plus or len(unresolved_all_rows)) or 0)
    unresolved_medium_plus = int(unresolved_medium_plus or len(unresolved_medium_plus_rows))
    baseline_total = summary.get("baseline_finding_total", 0)
    repair_rows = repair.get("rows", [])
    repair_hash = repair.get("repair_hash") if isinstance(repair.get("repair_hash"), str) else stable_hash(repair)

    if requested in {"V008", "008"} and int(baseline_total or 0) < 240:
        status = "FAIL_CLOSED"
    if requested in {"V010", "010"}:
        if int(baseline_total or 0) < 240:
            status = "FAIL_CLOSED"
        if int(unresolved_total or unresolved_medium_plus or 0) != 0:
            status = "FAIL_CLOSED"
        if visual_errors or iteration_errors:
            status = "FAIL_CLOSED"
        if not bool(review.get("actual_live_llm_invocation", False)):
            status = "FAIL_CLOSED"
    if require_strict_release_gate and requested in {"V010", "010"}:
        if unresolved_total or unresolved_medium_plus:
            status = "FAIL_CLOSED"

    if int(unresolved_total or unresolved_medium_plus or 0) != 0:
        status = "FAIL_CLOSED"

    payload = {
        "status": status,
        "requested_version": requested,
        "demo_version": atlas.get("demo_version", DEMO_VERSION),
        "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
        "release_label": atlas.get("release_label", RELEASE_LABEL),
        "provider_id": review.get("provider_id", "CODEX_CLI_CHATGPT"),
        "actual_live_llm_invocation": bool(review.get("actual_live_llm_invocation", False)),
        "provider_gate": provider_gate,
        "review_ledger_loading": review_loading,
        "cerberus_iteration_ledger": iteration,
        "cerberus_iteration_probe": iteration_probe,
        "visual_quality_manifest": visual,
        "visual_quality_manifest_probe": visual_probe,
        "visual_quality_manifest_status": visual.get("status", "MISSING") if isinstance(visual, dict) else "MISSING",
        "visual_quality_validation_failures": sorted(set(visual_errors + iteration_errors)),
        "baseline_finding_total": int(summary.get("baseline_finding_total", baseline_total or 0)),
        "unresolved_total": int(unresolved_total),
        "unresolved_minor_total": int(summary.get("unresolved_minor_total", 0) or 0),
        "unresolved_critical_high_total": int(unresolved_critical_high),
        "unresolved_medium_plus_total": int(unresolved_medium_plus or 0),
        "unresolved_medium_or_worse_total": int(summary.get("unresolved_medium_or_worse_total", unresolved_medium_plus or 0)),
        "heads_present": summary.get("heads_present", []),
        "screenshots_manifest": review.get("screenshots_manifest", {}),
        "cli_smoke_summary": review.get("cli_smoke_summary", {}),
        "cli_api_smoke": review.get("cli_api_smoke", review.get("cli_smoke_summary", {})),
        "repair_row_total": len(repair_rows) if isinstance(repair_rows, list) else 0,
        "review_hash": review.get("review_hash", stable_hash(review)),
        "repair_hash": repair_hash,
        "review": review,
        "repair_ledger": repair,
        "nonclaim": "Cerberus is a live LLM adversarial review gate for demonstrator quality. It does not prove OC scientific claims.",
        "schema_version": SCHEMA_VERSION,
        "review_payload_status": review.get("status", "FAIL_CLOSED"),
        "provider_probe": review.get("provider_probe", {}),
        "nonclaim_mode": "review is bounded to public artifact quality and boundary assertions.",
    }
    payload["result_hash"] = stable_hash(payload)
    return payload


def predict(params: dict[str, Any], atlas: dict[str, Any]) -> dict[str, Any]:
    domain_id = str(params.get("domain_id") or "PHYSICS").upper()
    domains = [row for row in atlas.get("domain_benchmarks", []) if isinstance(row, dict)]
    domain = next((row for row in domains if str(row.get("domain_id", "")).upper() == domain_id), None)
    if domain is None:
        raise ValueError(f"unknown domain_id: {domain_id}")
    supported = domain.get("closure_status") == "CLOSED_REPLAY_BACKED"
    payload = domain_anchor({"domain_index": domains.index(domain)}, atlas)
    payload.update(
        {
            "kind": "predict",
            "domain_id": domain_id,
            "prediction_allowed": bool(supported),
            "proof_status": domain.get("closure_status", "UNKNOWN"),
            "source_status": domain.get("source_status", ""),
            "result_hash": stable_hash({"domain": domain_id, "series": payload.get("series", []), "allowed": supported}),
            "nonclaim": domain.get("nonclaim_boundary", "") or "Prediction lane remains bounded by replay and validation status.",
        }
    )
    if not supported:
        payload["status"] = "BOUNDARY_ONLY_UNSUPPORTED_PREDICTION"
        payload["series"] = []
    return payload


def run_simulation(simulation_id: str, params: dict[str, Any] | None = None, *, atlas: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params or {}
    atlas = atlas or {}
    if simulation_id == "worldline_birth_evolution_collapse":
        return run_worldline(params)
    if simulation_id == "k_level_elevator":
        return run_k_elevator(params, atlas)
    if simulation_id == "kill_cascade":
        return kill_cascade(params, atlas)
    if simulation_id == "domain_anchor_lab":
        return domain_anchor(params, atlas)
    raise ValueError(f"unknown simulation_id: {simulation_id}")


def closure_ledger_summary(atlas: dict[str, Any], subject: str = "") -> dict[str, Any]:
    ledger = atlas.get("closure_ledger", [])
    if not isinstance(ledger, list):
        ledger = []
    query = subject.strip().lower()
    rows = [row for row in ledger if isinstance(row, dict)]
    if query:
        rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("closure_status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    open_rows = [row for row in rows if str(row.get("closure_status", "")).startswith("OPEN")]
    return {
        "open_count": len(open_rows),
        "closed_count": len(rows) - len(open_rows),
        "total_count": len(rows),
        "counts_by_status": counts,
        "rows": rows,
        "summary_hash": stable_hash({"subject": subject, "rows": rows}),
        "nonclaim": "Closure ledger rows close demonstrator gaps only inside their stated source/replay/boundary basis.",
    }


def make_research_gap(params: dict[str, Any], atlas: dict[str, Any]) -> dict[str, Any]:
    subject = str(params.get("subject") or params.get("domain_id") or "OC_V010_REVIEW").strip()[:120]
    lane = str(params.get("lane") or "prediction-validation").strip()[:120]
    gaps = atlas.get("research_gaps", [])
    matching = [gap for gap in gaps if subject.lower() in json.dumps(gap, ensure_ascii=False).lower()]
    if not matching:
        matching = gaps[:3]
    closure = closure_ledger_summary(atlas, subject)
    if not gaps:
        return {
            "request_id": "RGC-" + stable_hash({"subject": subject, "lane": lane, "closure": closure.get("summary_hash")})[:12].upper(),
            "subject": subject,
            "lane": lane,
            "status": "NO_OPEN_RESEARCH_GAP",
            "open_count": 0,
            "matched_gaps": [],
            "matched_closures": closure.get("rows", [])[:12],
            "closure_summary": {key: value for key, value in closure.items() if key != "rows"},
            "requested_action": "No research-gap request was created; inspect the closure ledger and proof-workbench obligations instead.",
            "nonclaim": "No open demonstrator research gap is not a claim that every external theorem or proof/refute task is solved.",
        }
    request = {
        "request_id": "RG-" + stable_hash({"subject": subject, "lane": lane, "matches": matching})[:12].upper(),
        "subject": subject,
        "lane": lane,
        "status": "QUEUED_LOCAL_RESEARCH_GAP",
        "requested_action": "Route this gap to the Logion research corpus, execute lawful proof/replay work, then regenerate the demonstrator.",
        "matched_gaps": matching,
        "closure_summary": {key: value for key, value in closure.items() if key != "rows"},
        "nonclaim": "Creating a research-gap request is not evidence that the claim is solved.",
    }
    return request


def export_bundle(atlas: dict[str, Any], data_dir: Path) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("oc_universe_atlas.json", json.dumps(atlas, ensure_ascii=False, allow_nan=False, indent=2))
        for name in [
            "oc_universe_atlas_v008.json",
            "oc_universe_atlas_v010.json",
            "oc_universe_atlas_v007.json",
            "science_graph_v008.json",
            "science_graph_v010.json",
            "science_graph_v007.json",
            "science_graph_v006.json",
            "didactic_routes.json",
            "reviewer_objection_routes.json",
            "model_comparison_matrix.json",
            "system_architect_missions.json",
            "trust_ladder.json",
            "practical_value_cards.json",
            "cerberus_v008_review.json",
            "cerberus_v008_repair_ledger.json",
            "cerberus_v010_review.json",
            "cerberus_v010_repair_ledger.json",
            "cerberus_v010_repair_backlog.json",
            "v010_iteration_ledger.json",
            "visual_quality_manifest.json",
            "v010_visual_quality_manifest.json",
            "responsive_visual_quality_manifest.json",
            "click_trace_manifest.json",
            "semantic_click_trace_manifest.json",
            "workflow_trace_manifest.json",
            "cli_api_smoke.json",
            "screenshots_manifest.json",
            "screenshot_manifest.json",
            "demonstrator_surface_graph.json",
            "demonstrator_surface_graph_v010.json",
            "m_spaces.json",
            "k_axes.json",
            "k_levels.json",
            "oc_wiki.json",
            "domain_benchmarks.json",
            "simulation_worlds.json",
            "k_level_worlds.json",
            "system_templates.json",
            "system_workbench_schema.json",
            "system_flows.json",
            "system_cycles.json",
            "thresholds.json",
            "compensators.json",
            "collapse_paths.json",
            "entity_link_index.json",
            "corpus_index.json",
            "formula_atlas.json",
            "formula_quality_report.json",
            "formula_formalization_obligations.json",
            "node_detail_index.json",
            "proof_body_index.json",
            "proof_evidence_routes.json",
            "research_gap_requests.json",
            "closure_ledger.json",
            "proof_placeholder_closure_ledger.json",
            "model_comparison_claim_ledger.json",
            "practical_value_decision_summary.json",
            "corpus_completeness_report.json",
            "k_level_example_atlas.json",
            "science_formalization_ledger.json",
            "demonstrator_cerberus_review.json",
            "demonstrator_cerberus_repair_ledger.json",
        ]:
            path = data_dir / name
            if path.exists():
                archive.write(path, name)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "demo_version": atlas.get("demo_version", DEMO_VERSION),
            "release_ordinal": atlas.get("release_ordinal", RELEASE_ORDINAL),
            "release_label": atlas.get("release_label", RELEASE_LABEL),
            "edition": atlas.get("edition", "unknown"),
            "atlas_hash": atlas.get("determinism_hash", stable_hash(atlas)),
            "external_actions": 0,
        }
        archive.writestr("bundle_manifest.json", json.dumps(manifest, ensure_ascii=False, allow_nan=False, indent=2))
    return buffer.getvalue()


def verify_public_safety(path: Path) -> dict[str, Any]:
    leak_patterns = [
        "C:" + "/" + "Users" + r"/[^/\"'\s]+",
        "C:" + r"\\Users\\",
        "/" + "Users" + "/",
        r"\." + "runtime",
        "logion_" + "local",
        "raw_" + "private",
        "source_" + "cache",
        r"(?:^|[\\/])" + "Desk" + r"top[\\/]",
        "Mega" + "port",
        "estra-" + "private-" + "work",
    ]
    bad: list[dict[str, str]] = []
    if path.is_file():
        files = [path]
    else:
        files = [item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".json", ".html", ".js", ".css", ".md"}]
    for file in files:
        text = file.read_text(encoding="utf-8", errors="ignore")
        for pattern in leak_patterns:
            if __import__("re").search(pattern, text, flags=__import__("re").IGNORECASE):
                bad.append({"file": str(file), "pattern": pattern})
    return {"status": "PASS" if not bad else "FAIL_CLOSED", "checked_files": len(files), "leaks": bad}

