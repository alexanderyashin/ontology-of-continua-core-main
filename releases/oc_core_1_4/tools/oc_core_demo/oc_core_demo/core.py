from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, deque
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import v003_engine


SCHEMA_VERSION = "oc-core-demo.v001"
DEMO_VERSION = "V010"
RELEASE_ORDINAL = "010"
RELEASE_LABEL = "OC Core 1.4 Demonstrator V010 Ideal RC"
PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PACKAGE_ROOT / "data"
DEFAULT_STRING_MAX_LENGTH = 4000
CASE_TEXT_MAX_LENGTH = 1600
GRAPH_NODE_CAP = 80
SERIES_EVENT_CAP = 12


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dumps(payload: Any, *, indent: int | None = 2) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=indent, sort_keys=False)


def _canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _hash(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _load_specs_cached() -> tuple[tuple[tuple[str, Any], ...], ...]:
    specs = _read_json(DATA_ROOT / "demo_specs.json")["specs"]
    return tuple(tuple(row.items()) for row in specs)


def _load_specs() -> list[dict[str, Any]]:
    return [dict(items) for items in _load_specs_cached()]


@lru_cache(maxsize=1)
def _load_cases_cached() -> tuple[tuple[tuple[str, Any], ...], ...]:
    cases = _read_json(DATA_ROOT / "case_examples.json")["cases"]
    return tuple(tuple(row.items()) for row in cases)


def _load_cases() -> list[dict[str, Any]]:
    return [dict(items) for items in _load_cases_cached()]


@lru_cache(maxsize=1)
def _load_targets_cached() -> tuple[tuple[tuple[str, Any], ...], ...]:
    targets = _read_json(DATA_ROOT / "public_targets.json")["targets"]
    return tuple(tuple(row.items()) for row in targets)


def _load_targets() -> list[dict[str, Any]]:
    return [dict(items) for items in _load_targets_cached()]


@lru_cache(maxsize=1)
def _public_graph_cached() -> str:
    for atlas_path in (
        PACKAGE_ROOT.parent / "web" / "public" / "data" / "oc_universe_atlas.json",
        PACKAGE_ROOT.parent / "web" / "dist" / "data" / "oc_universe_atlas.json",
    ):
        if atlas_path.exists():
            atlas = _read_json(atlas_path)
            graph = atlas.get("science_graph_v010") or atlas.get("science_graph_v008") or atlas.get("science_graph_v007") or atlas.get("science_graph_v006") or atlas.get("graph")
            if isinstance(graph, dict) and graph.get("nodes") and graph.get("edges"):
                return _canonical(graph)
    return _canonical(_read_json(DATA_ROOT / "interactive_graph.json"))


def load_public_graph() -> dict[str, Any]:
    return dict(json.loads(_public_graph_cached()))


def _normalize_text(text: Any, *, collapse: bool = True) -> str:
    value = str(text or "")
    replacements = {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    if collapse:
        value = re.sub(r"\s+", " ", value).strip()
    return value


def _truncate(text: Any, max_length: int = 320) -> str:
    value = _normalize_text(text)
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "..."


def _quality_flags(raw_text: Any) -> list[str]:
    raw = str(raw_text or "")
    normalized = _normalize_text(raw)
    flags: list[str] = []
    if not normalized:
        flags.append("empty_excerpt")
    if "Frozen proof/refute target ." in normalized or "Frozen 019 proof/refute target" in normalized:
        flags.append("placeholder_excerpt")
    if any(mark in raw for mark in ("\ufb00", "\ufb01", "\ufb02", "\ufb03", "\ufb04")):
        flags.append("ocr_ligature_normalized")
    if len(normalized) > 320:
        flags.append("long_excerpt_truncated_for_display")
    return flags


def _public_target_view(row: dict[str, Any], *, max_excerpt: int = 320) -> dict[str, Any]:
    raw_excerpt = row.get("public_statement_excerpt") or row.get("statement") or ""
    return {
        "public_target_id": row.get("public_target_id") or row.get("id"),
        "public_label": row.get("public_label") or row.get("label"),
        "public_status": row.get("terminal_status_public") or row.get("evidence_class") or "unknown",
        "demo_class": row.get("demo_class", ""),
        "demo_spec_id": row.get("demo_spec_id", ""),
        "evidence_class": row.get("public_evidence_class") or row.get("evidence_class", ""),
        "ui_route": row.get("ui_route") or row.get("route", ""),
        "statement_excerpt": _truncate(raw_excerpt, max_excerpt),
        "statement_quality_flags": _quality_flags(raw_excerpt),
        "source_target_id": row.get("source_target_id", ""),
        "closure_status": row.get("closure_status", ""),
        "closure_basis": row.get("closure_basis", ""),
        "closure_evidence_hash": row.get("closure_evidence_hash", ""),
        "nonclaim_boundary": row.get("nonclaim_boundary", ""),
    }


def list_specs() -> list[dict[str, Any]]:
    return [
        {
            "spec_id": row["spec_id"],
            "title": row["title"],
            "demo_class": row["demo_class"],
            "purpose": row["purpose"],
            "window_id": row["window_id"],
            "oc_concept": row["oc_concept"],
        }
        for row in _load_specs()
    ]


def list_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": row["case_id"],
            "title": row["title"],
            "case_text": _normalize_text(row["case_text"]),
            "params": dict(row["params"]),
        }
        for row in _load_cases()
    ]


def get_spec(spec_id: str) -> dict[str, Any]:
    for spec in _load_specs():
        if spec["spec_id"] == spec_id:
            return spec
    raise ValueError(f"unknown spec_id: {spec_id}")


def explain_spec(spec_id: str) -> dict[str, Any]:
    spec = get_spec(spec_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "status": "PASS",
        "spec": spec,
        "scientific_boundary": "Simulation and calculator output are bounded demonstrations. Proof status comes from the public evidence graph.",
        "result_contract": "Every run returns deterministic JSON with a reproducibility hash, evidence references and limits.",
    }


def _defaults(spec: dict[str, Any]) -> dict[str, Any]:
    return {key: block.get("default") for key, block in spec.get("parameters", {}).items()}


def _max_string_length(key: str, block: dict[str, Any]) -> int:
    if key == "case_text":
        return int(block.get("maxLength", CASE_TEXT_MAX_LENGTH))
    return int(block.get("maxLength", DEFAULT_STRING_MAX_LENGTH))


def _coerce_params(spec: dict[str, Any], params: dict[str, Any] | None) -> dict[str, Any]:
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ValueError("params must be a JSON object")

    blocks = spec.get("parameters", {})
    unknown = sorted(set(params) - set(blocks))
    if unknown:
        raise ValueError(f"unknown parameter(s): {', '.join(unknown)}")

    merged = _defaults(spec)
    merged.update(params)
    clean: dict[str, Any] = {}

    for key, block in blocks.items():
        value = merged.get(key)
        kind = block.get("type")
        if kind == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{key} must be an integer")
            if value < block.get("min", value) or value > block.get("max", value):
                raise ValueError(f"{key} out of range")
            clean[key] = value
        elif kind == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{key} must be numeric")
            number = float(value)
            if not math.isfinite(number):
                raise ValueError(f"{key} must be finite")
            if number < block.get("min", number) or number > block.get("max", number):
                raise ValueError(f"{key} out of range")
            clean[key] = round(number, 12)
        elif kind == "string":
            if not isinstance(value, str):
                raise ValueError(f"{key} must be a string")
            normalized = _normalize_text(value)
            limit = _max_string_length(key, block)
            if len(normalized) > limit:
                raise ValueError(f"{key} exceeds max length {limit}")
            clean[key] = normalized
        else:
            raise ValueError(f"{key} has unsupported parameter type: {kind}")
    return clean


def _band(value: float, low_label: str = "low", mid_label: str = "watch", high_label: str = "high") -> str:
    if not math.isfinite(value):
        raise ValueError("band value must be finite")
    if value < 0.34:
        return low_label
    if value < 0.67:
        return mid_label
    return high_label


@lru_cache(maxsize=1)
def _target_map_cached() -> str:
    return _canonical({row["public_target_id"]: row for row in _load_targets()})


def _target_map() -> dict[str, dict[str, Any]]:
    return dict(json.loads(_target_map_cached()))


def _graph_nodes_by_id() -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in load_public_graph().get("nodes", [])}


def _route_node_ids() -> set[str]:
    nodes_by_id = _graph_nodes_by_id()
    return {
        node_id
        for node_id, node in nodes_by_id.items()
        if not node_id.startswith("OC14-N") and node.get("layer", node.get("cluster")) in {"root_principle", "metaontology", "proof_route", "evidence"}
    }


def _graph_edges() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for edge in load_public_graph().get("edges", []):
        source = edge.get("from", edge.get("source"))
        target = edge.get("to", edge.get("target"))
        if source is None or target is None:
            continue
        rows.append({"from": str(source), "to": str(target), "relation": str(edge.get("relation", edge.get("edge_type", "related")))})
    return rows


def _graph_adjacency() -> dict[str, list[tuple[str, str]]]:
    nodes_by_id = _graph_nodes_by_id()
    adjacency: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in nodes_by_id}
    for edge in _graph_edges():
        left, right, relation = edge["from"], edge["to"], edge["relation"]
        adjacency.setdefault(left, []).append((right, relation))
        adjacency.setdefault(right, []).append((left, relation))
    for node_id in adjacency:
        adjacency[node_id] = sorted(adjacency[node_id])
    return adjacency


def _graph_node_view(row: dict[str, Any], *, max_excerpt: int = 260) -> dict[str, Any]:
    public_id = row.get("id", "")
    statement = row.get("statement", "") or row.get("statement_excerpt", "")
    return {
        "id": public_id,
        "label": row.get("label", public_id),
        "route": row.get("route", ""),
        "layer": row.get("layer", row.get("cluster", "")),
        "demo_class": row.get("demo_class", ""),
        "demo_spec_id": row.get("demo_spec_id", ""),
        "evidence_class": row.get("evidence_class", ""),
        "statement_excerpt": _truncate(statement, max_excerpt) if statement else "",
        "statement_quality_flags": _quality_flags(statement) if statement else [],
    }


def _case_diagnostic(params: dict[str, Any]) -> dict[str, Any]:
    pressure = float(params["change_pressure"])
    boundary_gap = 1.0 - float(params["boundary_clarity"])
    evidence_gap = 1.0 - float(params["evidence_quality"])
    coupling = float(params["dependency_coupling"])
    risk = min(1.0, 0.30 * pressure + 0.27 * boundary_gap + 0.23 * evidence_gap + 0.20 * coupling)
    contributors = {
        "change pressure": pressure,
        "boundary ambiguity": boundary_gap,
        "evidence gap": evidence_gap,
        "dependency coupling": coupling,
    }
    main = max(contributors, key=contributors.get)
    first_step = {
        "change pressure": "Stabilize transition scope before adding new commitments.",
        "boundary ambiguity": "Make ownership and interface boundaries explicit first.",
        "evidence gap": "Bind claims to evidence roles and nonclaims before release use.",
        "dependency coupling": "Map dependency neighborhood and isolate high-coupling links.",
    }[main]
    return {
        "case_excerpt": _truncate(params["case_text"], 320),
        "risk_score": round(risk, 6),
        "risk_band": _band(risk, "bounded", "attention", "high"),
        "dominant_oc_reading": main,
        "first_investigation_step": first_step,
        "practical_use": "Use this as a starting diagnosis, then inspect graph and evidence routes.",
    }


def _transition_pressure_lab(params: dict[str, Any]) -> dict[str, Any]:
    coherence = float(params["initial_coherence"])
    pressure = float(params["transition_pressure"])
    correction = float(params["corrective_capacity"])
    drag = float(params["coupling_drag"])
    series = []
    events = []
    for step in range(int(params["steps"]) + 1):
        series.append({"step": step, "coherence": round(coherence, 6)})
        stress = max(0.0, pressure - correction)
        coherence += 0.08 * correction * (1 - coherence) - 0.06 * stress - 0.035 * drag * coherence
        coherence = max(0.0, min(1.0, coherence))
        if coherence < 0.33:
            events.append({"step": step, "event": "coherence below watch floor"})
    return {
        "series": series,
        "events": events[:SERIES_EVENT_CAP],
        "final_coherence": series[-1]["coherence"],
        "final_band": _band(series[-1]["coherence"], "fragile", "recoverable", "stable"),
        "interpretation": "Correction must exceed pressure and drag to preserve coherence in this bounded scenario.",
        "plot": {"x": "step", "y": "coherence"},
    }


def _degradation_recovery_lab(params: dict[str, Any]) -> dict[str, Any]:
    health = float(params["initial_health"])
    intervention_step = int(params["intervention_step"])
    series = []
    for step in range(int(params["steps"]) + 1):
        series.append({"step": step, "health": round(health, 6)})
        repair = float(params["intervention_strength"]) if step >= intervention_step else 0.0
        health += repair * (1 - health) * 0.18 - float(params["degradation_rate"]) * (0.6 + health)
        health = max(0.0, min(1.0, health))
    final = series[-1]["health"]
    return {
        "series": series,
        "final_health": final,
        "outcome": _band(final, "continued degradation", "partial recovery", "recovered"),
        "interpretation": "Late or weak intervention leaves accumulated coherence debt visible.",
        "plot": {"x": "step", "y": "health"},
    }


def _dependency_propagation(params: dict[str, Any]) -> dict[str, Any]:
    adjacency = _graph_adjacency()
    route_nodes = _route_node_ids()
    seed = params["seed_node"]
    if seed not in adjacency:
        raise ValueError(f"unknown graph node: {seed}")
    active = {seed}
    history = [{"step": 0, "active_total": 1, "new_nodes": [seed]}]
    for step in range(1, int(params["steps"]) + 1):
        new_nodes = set(active)
        for node in sorted(active):
            if node in route_nodes and node != seed:
                continue
            new_nodes.update(neighbor for neighbor, _relation in adjacency.get(node, []))
        added = sorted(new_nodes - active)
        active = new_nodes
        history.append({"step": step, "active_total": len(active), "new_nodes": added[:30]})
    return {
        "seed_node": seed,
        "history": history,
        "route_nodes_are_terminal": True,
        "interpretation": "A local claim is not isolated; graph neighbors reveal evidence and consequence context without expanding through global route hubs.",
        "plot": {"x": "step", "y": "active_total"},
    }


def _weighted_score(params: dict[str, Any], weights: dict[str, float], inverse: set[str] | None = None) -> tuple[float, dict[str, float]]:
    inverse = inverse or set()
    components = {}
    total = 0.0
    for key, weight in weights.items():
        value = float(params[key])
        if key in inverse:
            value = 1.0 - value
        components[key] = round(value, 6)
        total += weight * value
    return round(max(0.0, min(1.0, total)), 6), components


def _coherence_debt_calculator(params: dict[str, Any]) -> dict[str, Any]:
    score, components = _weighted_score(
        params,
        {"boundary_ambiguity": 0.30, "coupling": 0.25, "exception_load": 0.25, "evidence_quality": 0.20},
        inverse={"evidence_quality"},
    )
    main = max(components, key=components.get)
    return {"score": score, "band": _band(score, "manageable", "watch", "high debt"), "main_contributor": main, "components": components}


def _transformation_risk_calculator(params: dict[str, Any]) -> dict[str, Any]:
    score, components = _weighted_score(
        params,
        {"change_pressure": 0.30, "readiness": 0.24, "dependency_coupling": 0.26, "evidence_maturity": 0.20},
        inverse={"readiness", "evidence_maturity"},
    )
    return {
        "risk_score": score,
        "risk_band": _band(score, "bounded", "requires attention", "high"),
        "intervention_priority": "evidence and boundary repair" if components["evidence_maturity"] > components["dependency_coupling"] else "dependency isolation",
        "components": components,
        "forbidden_overclaim": "This is not a sale-ready risk proof or client-specific guarantee.",
    }


def _evidence_sufficiency_calculator(params: dict[str, Any]) -> dict[str, Any]:
    score, components = _weighted_score(
        params,
        {"source_binding": 0.25, "dependency_closure": 0.25, "verification_strength": 0.30, "nonclaim_clarity": 0.20},
    )
    weakest = min(components, key=components.get)
    return {
        "sufficiency_score": score,
        "band": _band(score, "insufficient", "reviewable", "strong"),
        "weakest_evidence_role": weakest,
        "reviewer_note": "Use this to identify which evidence role needs explanation, not to claim external peer review.",
        "components": components,
    }


def _architecture_readiness_calculator(params: dict[str, Any]) -> dict[str, Any]:
    score, components = _weighted_score(
        params,
        {"boundary_clarity": 0.28, "dependency_visibility": 0.27, "observability": 0.22, "intervention_capacity": 0.23},
    )
    weakest = min(components, key=components.get)
    return {"readiness_score": score, "band": _band(score, "not ready", "inspectable", "ready for review"), "weakest_axis": weakest, "components": components}


def _graph_neighborhood(params: dict[str, Any]) -> dict[str, Any]:
    node = params["node"]
    radius = int(params["radius"])
    graph = load_public_graph()
    adjacency = _graph_adjacency()
    nodes_by_id = _graph_nodes_by_id()
    route_nodes = _route_node_ids()
    if node not in adjacency:
        raise ValueError(f"unknown graph node: {node}")

    seen = {node}
    queue = deque([(node, 0)])
    while queue:
        current, distance = queue.popleft()
        if distance >= radius:
            continue
        if current in route_nodes and current != node:
            continue
        for nxt, _relation in adjacency.get(current, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, distance + 1))

    sorted_seen = sorted(seen)
    omitted_count = max(0, len(sorted_seen) - GRAPH_NODE_CAP)
    capped_ids = sorted_seen[:GRAPH_NODE_CAP]
    if node not in capped_ids:
        capped_ids = [node] + capped_ids[: GRAPH_NODE_CAP - 1]
    capped = set(capped_ids)
    edge_rows = [
        edge
        for edge in _graph_edges()
        if edge["from"] in capped and edge["to"] in capped
    ]
    relation_counts = dict(Counter(edge["relation"] for edge in edge_rows))
    visible_degree = {key: 0 for key in capped_ids}
    for edge in edge_rows:
        visible_degree[edge["from"]] += 1
        visible_degree[edge["to"]] += 1

    return {
        "summary": {
            "center": node,
            "radius": radius,
            "matched_node_total": len(sorted_seen),
            "returned_node_total": len(capped_ids),
            "returned_edge_total": len(edge_rows),
            "relation_counts": relation_counts,
            "route_nodes_not_expanded": sorted(route_nodes & seen),
        },
        "center": node,
        "radius": radius,
        "nodes": [_graph_node_view(nodes_by_id.get(item, {"id": item, "label": item})) for item in capped_ids],
        "edges": edge_rows,
        "degree_centrality": visible_degree,
        "degree_scope": "returned subgraph only; global route hubs are not expanded",
        "relation_counts": relation_counts,
        "truncated": omitted_count > 0,
        "omitted_count": omitted_count,
        "warnings": [
            "Global route nodes are shown but not expanded, to avoid misleading hub explosion.",
            "Use the exported JSON for audit; UI tables intentionally cap large neighborhoods.",
        ],
        "why_it_matters": "The neighborhood shows which public evidence and demonstration routes touch the selected claim.",
        "graph_summary": graph.get("summary", {}),
    }


def _proof_trace_replay(params: dict[str, Any]) -> dict[str, Any]:
    target = params["target"]
    row = _target_map().get(target)
    if not row:
        raise ValueError(f"unknown target: {target}")
    view = _public_target_view(row)
    return {
        "target": target,
        "public_target": view,
        "statement_excerpt": view["statement_excerpt"],
        "statement_quality_flags": view["statement_quality_flags"],
        "trace": [
            {"stage": "statement", "status": "public statement excerpt available", "detail": view["statement_excerpt"]},
            {"stage": "evidence_class", "status": view["evidence_class"] or "unspecified"},
            {"stage": "demo_route", "status": view["ui_route"] or "unspecified"},
            {"stage": "demo_class", "status": view["demo_class"] or "unspecified"},
            {"stage": "public_verdict", "status": view["public_status"]},
            {"stage": "closure_status", "status": view.get("closure_status") or "not-applicable"},
            {"stage": "limit", "status": row.get("non_simulated_reason") or "simulation is illustrative, not proof"},
        ],
        "rationale": _normalize_text(row.get("rationale", "")),
        "non_simulated_reason": _normalize_text(row.get("non_simulated_reason", "")),
        "nonclaim": view.get("nonclaim_boundary") or "This replay is not a proof engine, not external peer review, and does not expose private work records.",
    }


RUNNERS = {
    "case_diagnostic": _case_diagnostic,
    "transition_pressure_lab": _transition_pressure_lab,
    "degradation_recovery_lab": _degradation_recovery_lab,
    "dependency_propagation": _dependency_propagation,
    "coherence_debt_calculator": _coherence_debt_calculator,
    "transformation_risk_calculator": _transformation_risk_calculator,
    "evidence_sufficiency_calculator": _evidence_sufficiency_calculator,
    "architecture_readiness_calculator": _architecture_readiness_calculator,
    "graph_neighborhood": _graph_neighborhood,
    "proof_trace_replay": _proof_trace_replay,
}


def run_spec(spec_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = get_spec(spec_id)
    if spec_id not in RUNNERS:
        raise ValueError(f"spec has no runner: {spec_id}")
    clean_params = _coerce_params(spec, params)
    body = RUNNERS[spec_id](clean_params)
    result = {
        "schema_version": SCHEMA_VERSION,
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "status": "PASS",
        "spec_id": spec_id,
        "title": spec["title"],
        "demo_class": spec["demo_class"],
        "oc_concept": spec["oc_concept"],
        "params": clean_params,
        "result": body,
        "evidence_refs": spec.get("evidence_refs", []),
        "limits": spec.get("limits", []),
        "scientific_boundary": "Demonstration output is practical and reproducible; proof status comes from the public release evidence.",
    }
    result["result_hash"] = _hash(result)
    return result


def analyze_case(case_payload: dict[str, Any]) -> dict[str, Any]:
    return run_spec("case_diagnostic", case_payload)


def export_release_context() -> dict[str, Any]:
    graph = load_public_graph()
    specs = list_specs()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "status": "PASS",
        "title": "OC Core 1.4 Demonstrator",
        "target_total": graph.get("summary", {}).get("target_total", 0),
        "graph_node_total": len(graph.get("nodes", [])),
        "graph_edge_total": len(graph.get("edges", [])),
        "spec_total": len(specs),
        "case_total": len(list_cases()),
        "windows": sorted({spec["window_id"] for spec in specs}),
        "external_actions": 0,
        "boundary": "Local public demonstrator only; no publication, outreach, sales or repository action.",
    }
    payload["result_hash"] = _hash(payload)
    return payload


def quality_report_payload() -> dict[str, Any]:
    atlas = v003_engine.load_universe()
    return v003_engine.quality_report(atlas)


def corpus_completeness_payload() -> dict[str, Any]:
    atlas = v003_engine.load_universe()
    return v003_engine.corpus_completeness(atlas)


def formula_quality_payload(*, strict: bool = False) -> dict[str, Any]:
    atlas = v003_engine.load_universe()
    return v003_engine.formula_quality(atlas, strict=strict)


def k_examples_payload() -> dict[str, Any]:
    atlas = v003_engine.load_universe()
    return v003_engine.k_examples(atlas)


def surface_graph_payload(*, include_rows: bool = True) -> dict[str, Any]:
    atlas = v003_engine.load_universe()
    return v003_engine.surface_graph(atlas, include_rows=include_rows)


def desktop_smoke_payload() -> dict[str, Any]:
    return v003_engine.desktop_smoke()


def _failure(spec_id: str | None, message: str) -> dict[str, Any]:
    failure = {
        "schema_version": SCHEMA_VERSION,
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "status": "FAIL_CLOSED",
        "spec_id": spec_id,
        "message": message,
        "scientific_boundary": "Invalid or unknown demonstrator requests fail closed and do not imply scientific evidence.",
    }
    failure["result_hash"] = _hash(failure)
    return failure


def run_spec_safe(spec_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return run_spec(spec_id, params)
    except Exception as exc:
        return _failure(spec_id, str(exc))


def explain_spec_safe(spec_id: str) -> dict[str, Any]:
    try:
        payload = explain_spec(spec_id)
        payload["result_hash"] = _hash(payload)
        return payload
    except Exception as exc:
        return _failure(spec_id, str(exc))


def _v007_rows(
    atlas: dict[str, Any],
    resource_key: str,
    *,
    fallback_file: str | None = None,
    fallback_key: str | None = None,
) -> list[dict[str, Any]]:
    if atlas:
        direct = atlas.get(resource_key)
        if isinstance(direct, list):
            return [row for row in direct if isinstance(row, dict)]
    if not fallback_file:
        return []
    return v003_engine.resource_rows(atlas, resource_key, fallback_file=fallback_file, fallback_key=fallback_key or resource_key)


def _v007_lookup(rows: list[dict[str, Any]], resource_id: str, *, id_fields: tuple[str, ...]) -> dict[str, Any] | None:
    for row in rows:
        for key in id_fields:
            if str(row.get(key, "")) == str(resource_id):
                return row
    return None


def _v007_payload(kind: str, atlas: dict[str, Any], body: dict[str, Any], *, status: str = "PASS") -> dict[str, Any]:
    return v003_engine.envelope(kind, str(atlas.get("edition", "unknown")), body, status=status)


def _read_params_file(path_value: str) -> dict[str, Any]:
    try:
        payload = _read_json(Path(path_value))
    except Exception as exc:
        raise ValueError(f"could not read params file: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("params file must contain a JSON object")
    return payload


def _print(payload: dict[str, Any]) -> int:
    print(_dumps(payload))
    return 0 if payload.get("status", "PASS") == "PASS" else 2


def _print_safe(payload_factory: Any, *, spec_id: str | None = None) -> int:
    try:
        return _print(payload_factory())
    except Exception as exc:
        return _print(_failure(spec_id, str(exc)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OC Core public science demonstrator")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("cases")
    run = sub.add_parser("run")
    run.add_argument("spec_id")
    run.add_argument("--params", default="")
    analyze = sub.add_parser("analyze-case")
    analyze.add_argument("--params", default="")
    graph = sub.add_parser("graph")
    graph.add_argument("--node", default="")
    graph.add_argument("--radius", type=int, default=1)
    science_graph = sub.add_parser("science-graph")
    science_graph.add_argument("--summary-only", action="store_true")
    explain = sub.add_parser("explain")
    explain.add_argument("spec_id")
    explain.add_argument("--json", action="store_true")
    sub.add_parser("export")
    atlas = sub.add_parser("atlas")
    atlas.add_argument("--edition", choices=["public", "private"], default="")
    simulate = sub.add_parser("simulate")
    simulate.add_argument("simulation_id")
    simulate.add_argument("--params", default="")
    m_space = sub.add_parser("m-space")
    m_space.add_argument("m_space_id", nargs="?", default="")
    m_space.add_argument("--query", default="")
    system_templates = sub.add_parser("system-templates")
    system_templates.add_argument("template_id", nargs="?", default="")
    system_templates.add_argument("--query", default="")
    didactic_route = sub.add_parser("didactic-route")
    didactic_route.add_argument("route_id", nargs="?", default="")
    didactic_route.add_argument("--query", default="")
    reviewer_objections = sub.add_parser("reviewer-objections")
    reviewer_objections.add_argument("route_id", nargs="?", default="")
    reviewer_objections.add_argument("--query", default="")
    model_comparison = sub.add_parser("model-comparison")
    model_comparison.add_argument("comparison_id", nargs="?", default="")
    model_comparison.add_argument("--query", default="")
    architect_missions = sub.add_parser("architect-missions")
    architect_missions.add_argument("mission_id", nargs="?", default="")
    architect_missions.add_argument("--query", default="")
    trust_ladder = sub.add_parser("trust-ladder")
    trust_ladder.add_argument("rung_id", nargs="?", default="")
    trust_ladder.add_argument("--query", default="")
    simulate_system = sub.add_parser("simulate-system")
    simulate_system.add_argument("system_id")
    simulate_system.add_argument("--template-id", default="")
    simulate_system.add_argument("--mode", choices=["selected", "weakest"], default="selected")
    simulate_system.add_argument("--kill-node", default="")
    simulate_system.add_argument("--shock", type=float, default=0.82)
    simulate_system.add_argument("--params", default="")
    kill = sub.add_parser("kill")
    kill.add_argument("--system-id", default="civilization")
    kill.add_argument("--kill-node", default="")
    kill.add_argument("--shock", type=float, default=0.82)
    kill.add_argument("--mode", choices=["selected", "weakest"], default="selected")
    predict = sub.add_parser("predict")
    predict.add_argument("--domain-id", default="PHYSICS")
    corpus = sub.add_parser("corpus")
    corpus.add_argument("--query", default="")
    corpus.add_argument("--limit", type=int, default=25)
    formula = sub.add_parser("formula")
    formula.add_argument("--query", default="")
    formula.add_argument("--limit", type=int, default=25)
    node = sub.add_parser("node-detail")
    node.add_argument("node_id")
    gap = sub.add_parser("research-gaps")
    gap.add_argument("--subject", default="")
    gap.add_argument("--lane", default="prediction-validation")
    closure = sub.add_parser("closure-ledger")
    closure.add_argument("--subject", default="")
    quality = sub.add_parser("quality-report")
    quality.add_argument("--version", default=DEMO_VERSION)
    corpus_completeness = sub.add_parser("corpus-completeness")
    formula_quality = sub.add_parser("formula-quality")
    formula_quality.add_argument("--strict", action="store_true")
    formula_quality.add_argument("--version", default=DEMO_VERSION)
    k_examples = sub.add_parser("k-examples")
    k_examples.add_argument("--limit", type=int, default=20)
    surface_graph = sub.add_parser("surface-graph")
    surface_graph.add_argument("--summary-only", action="store_true")
    surface_graph.add_argument("--version", default=DEMO_VERSION)
    verify = sub.add_parser("verify-public-safety")
    verify.add_argument("path", nargs="?", default="")
    cerberus = sub.add_parser("cerberus")
    cerberus.add_argument("--version", default=DEMO_VERSION)
    cerberus.add_argument("--no-mercy", action="store_true")
    cerberus.add_argument("--zero-findings", action="store_true")
    sub.add_parser("desktop-smoke")
    sub.add_parser("build-private")
    args = parser.parse_args(argv)

    if args.cmd == "list":
        return _print_safe(lambda: {"schema_version": SCHEMA_VERSION, "status": "PASS", "specs": list_specs()})
    if args.cmd == "cases":
        return _print_safe(lambda: {"schema_version": SCHEMA_VERSION, "status": "PASS", "cases": list_cases()})
    if args.cmd == "run":
        try:
            params = _read_params_file(args.params) if args.params else {}
        except Exception as exc:
            return _print(_failure(args.spec_id, str(exc)))
        return _print(run_spec_safe(args.spec_id, params))
    if args.cmd == "analyze-case":
        try:
            params = _read_params_file(args.params) if args.params else {}
        except Exception as exc:
            return _print(_failure("case_diagnostic", str(exc)))
        return _print(run_spec_safe("case_diagnostic", params))
    if args.cmd == "graph":
        if args.node:
            return _print(run_spec_safe("graph_neighborhood", {"node": args.node, "radius": args.radius}))
        return _print_safe(
            lambda: {
                "schema_version": SCHEMA_VERSION,
                "status": "PASS",
                "summary": load_public_graph().get("summary", {}),
                "node_total": len(load_public_graph().get("nodes", [])),
                "edge_total": len(load_public_graph().get("edges", [])),
            }
        )
    if args.cmd == "science-graph":
        def _science_graph_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.science_graph(universe, include_rows=not args.summary_only)
            return v003_engine.envelope("science-graph", str(universe.get("edition", "unknown")), body)

        return _print_safe(_science_graph_payload)
    if args.cmd == "explain":
        return _print(explain_spec_safe(args.spec_id))
    if args.cmd == "export":
        return _print_safe(export_release_context)
    if args.cmd == "atlas":
        def _atlas_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe(edition=args.edition or None)
            if args.edition and universe.get("edition") != args.edition:
                raise ValueError(f"loaded atlas edition is {universe.get('edition')}, not {args.edition}")
            return v003_engine.envelope("atlas", str(universe.get("edition", "unknown")), universe)

        return _print_safe(_atlas_payload)
    if args.cmd == "simulate":
        try:
            params = _read_params_file(args.params) if args.params else {}
        except Exception as exc:
            return _print(_failure(args.simulation_id, str(exc)))

        def _simulate_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.run_simulation(args.simulation_id, params, atlas=universe)
            return v003_engine.envelope("simulation", str(universe.get("edition", "unknown")), body)

        return _print_safe(_simulate_payload, spec_id=args.simulation_id)
    if args.cmd == "m-space":
        def _m_space_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(
                atlas,
                "m_spaces",
                fallback_file="m_spaces.json",
            )
            if args.query and not args.m_space_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.m_space_id:
                row = _v007_lookup(rows, args.m_space_id, id_fields=("m_space_id", "id", "template_id"))
                if row is None:
                    raise ValueError(f"unknown m_space_id: {args.m_space_id}")
                return _v007_payload("m-space", atlas, {"m_space_id": args.m_space_id, "m_space": row})
            return _v007_payload("m-space", atlas, {"m_spaces": rows, "count": len(rows), "query": args.query})

        return _print_safe(_m_space_payload, spec_id="m-space")
    if args.cmd == "system-templates":
        def _templates_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(
                atlas,
                "system_templates",
                fallback_file="system_templates.json",
            )
            if args.query and not args.template_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.template_id:
                row = _v007_lookup(
                    rows,
                    args.template_id,
                    id_fields=("template_id", "id", "system_id"),
                )
                if row is None:
                    raise ValueError(f"unknown template_id: {args.template_id}")
                return _v007_payload("system-template", atlas, {"template_id": args.template_id, "template": row})
            return _v007_payload("system-template-list", atlas, {"templates": rows, "count": len(rows), "query": args.query})

        return _print_safe(_templates_payload, spec_id="system-template")
    if args.cmd == "didactic-route":
        def _route_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(atlas, "didactic_routes", fallback_file="didactic_routes.json", fallback_key="didactic_routes")
            if not rows:
                rows = _v007_rows(atlas, "journeys", fallback_file="didactic_routes.json", fallback_key="journeys")
            if args.query and not args.route_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.route_id:
                row = _v007_lookup(rows, args.route_id, id_fields=("route_id", "id", "name"))
                if row is None:
                    raise ValueError(f"unknown route_id: {args.route_id}")
                return _v007_payload("didactic-route", atlas, {"route_id": args.route_id, "route": row})
            return _v007_payload("didactic-route-list", atlas, {"routes": rows, "count": len(rows), "query": args.query})

        return _print_safe(_route_payload, spec_id="didactic-route")
    if args.cmd == "reviewer-objections":
        def _objection_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(
                atlas,
                "reviewer_objection_routes",
                fallback_file="reviewer_objection_routes.json",
                fallback_key="reviewer_objection_routes",
            )
            if args.query and not args.route_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.route_id:
                row = _v007_lookup(rows, args.route_id, id_fields=("id", "route_id", "objection_id"))
                if row is None:
                    raise ValueError(f"unknown reviewer objection route: {args.route_id}")
                return _v007_payload("reviewer-objection", atlas, {"route_id": args.route_id, "route": row})
            return _v007_payload(
                "reviewer-objection-list",
                atlas,
                {"routes": rows, "count": len(rows), "query": args.query},
            )

        return _print_safe(_objection_payload, spec_id="reviewer-objections")
    if args.cmd == "model-comparison":
        def _model_comparison_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(
                atlas,
                "model_comparison_matrix",
                fallback_file="model_comparison_matrix.json",
                fallback_key="model_comparison_matrix",
            )
            if args.query and not args.comparison_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.comparison_id:
                row = _v007_lookup(rows, args.comparison_id, id_fields=("comparison_id", "id", "model_id"))
                if row is None:
                    raise ValueError(f"unknown comparison_id: {args.comparison_id}")
                return _v007_payload("model-comparison", atlas, {"comparison_id": args.comparison_id, "comparison": row})
            return _v007_payload(
                "model-comparison-list",
                atlas,
                {"rows": rows, "count": len(rows), "query": args.query},
            )

        return _print_safe(_model_comparison_payload, spec_id="model-comparison")
    if args.cmd == "architect-missions":
        def _architect_mission_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(
                atlas,
                "system_architect_missions",
                fallback_file="system_architect_missions.json",
                fallback_key="system_architect_missions",
            )
            if args.query and not args.mission_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.mission_id:
                row = _v007_lookup(rows, args.mission_id, id_fields=("id", "mission_id", "template_id"))
                if row is None:
                    raise ValueError(f"unknown mission_id: {args.mission_id}")
                return _v007_payload("architect-mission", atlas, {"mission_id": args.mission_id, "mission": row})
            return _v007_payload(
                "architect-mission-list",
                atlas,
                {"missions": rows, "count": len(rows), "query": args.query},
            )

        return _print_safe(_architect_mission_payload, spec_id="architect-missions")
    if args.cmd == "trust-ladder":
        def _trust_ladder_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            rows = _v007_rows(
                atlas,
                "trust_ladder",
                fallback_file="trust_ladder.json",
                fallback_key="trust_ladder",
            )
            if args.query and not args.rung_id:
                query = args.query.lower()
                rows = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
            if args.rung_id:
                row = _v007_lookup(rows, args.rung_id, id_fields=("rung_id", "id"))
                if row is None:
                    raise ValueError(f"unknown trust ladder rung: {args.rung_id}")
                return _v007_payload("trust-ladder", atlas, {"rung_id": args.rung_id, "rung": row})
            return _v007_payload(
                "trust-ladder-list",
                atlas,
                {"rungs": rows, "count": len(rows), "query": args.query},
            )

        return _print_safe(_trust_ladder_payload, spec_id="trust-ladder")
    if args.cmd == "simulate-system":
        try:
            params = _read_params_file(args.params) if args.params else {}
        except Exception as exc:
            return _print(_failure("simulate-system", str(exc)))
        system_id = args.system_id or args.template_id
        if not system_id:
            return _print(_failure("simulate-system", "system_id is required"))

        def _simulate_system_payload() -> dict[str, Any]:
            atlas = v003_engine.load_universe()
            templates = _v007_rows(atlas, "system_templates", fallback_file="system_templates.json")
            systems = _v007_rows(atlas, "system_zoo", fallback_file="system_zoo.json")
            selected = _v007_lookup(templates, system_id, id_fields=("template_id", "system_id"))
            if selected is None:
                selected = _v007_lookup(systems, system_id, id_fields=("id", "system_id"))
            if selected is None:
                raise ValueError(f"unknown system/template id: {system_id}")
            body = dict(params)
            body.setdefault("system_id", system_id)
            body.setdefault("mode", args.mode)
            body.setdefault("shock", args.shock)
            if args.kill_node:
                body["kill_node"] = args.kill_node
            simulation = v003_engine.kill_cascade(body, atlas)
            return _v007_payload(
                "simulate-system",
                atlas,
                {
                    "system_id": system_id,
                    "template_id": selected.get("template_id", selected.get("id", "")),
                    "template": selected,
                    "simulation": simulation,
                },
            )

        return _print_safe(_simulate_system_payload, spec_id=system_id)
    if args.cmd == "kill":
        def _kill_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            params = {"system_id": args.system_id, "shock": args.shock, "mode": args.mode}
            if args.kill_node:
                params["kill_node"] = args.kill_node
            body = v003_engine.kill_cascade(params, universe)
            return v003_engine.envelope("kill-cascade", str(universe.get("edition", "unknown")), body)

        return _print_safe(_kill_payload, spec_id="kill_cascade")
    if args.cmd == "predict":
        def _predict_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.predict({"domain_id": args.domain_id}, universe)
            return v003_engine.envelope("predict", str(universe.get("edition", "unknown")), body)

        return _print_safe(_predict_payload, spec_id="predict")
    if args.cmd == "corpus":
        def _corpus_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.corpus_search(universe, args.query, args.limit)
            return v003_engine.envelope("corpus", str(universe.get("edition", "unknown")), body)

        return _print_safe(_corpus_payload, spec_id="corpus")
    if args.cmd == "formula":
        def _formula_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.formula_search(universe, args.query, args.limit)
            return v003_engine.envelope("formula", str(universe.get("edition", "unknown")), body)

        return _print_safe(_formula_payload, spec_id="formula")
    if args.cmd == "node-detail":
        def _node_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.node_detail(universe, args.node_id)
            return v003_engine.envelope("node-detail", str(universe.get("edition", "unknown")), body)

        return _print_safe(_node_payload, spec_id=args.node_id)
    if args.cmd == "research-gaps":
        def _gap_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            if args.subject:
                body = v003_engine.make_research_gap({"subject": args.subject, "lane": args.lane}, universe)
            else:
                summary = v003_engine.closure_ledger_summary(universe)
                body = {
                    "open_count": len(universe.get("research_gaps", [])),
                    "gaps": universe.get("research_gaps", []),
                    "closure_summary": {key: value for key, value in summary.items() if key != "rows"},
                }
            return v003_engine.envelope("research-gaps", str(universe.get("edition", "unknown")), body)

        return _print_safe(_gap_payload)
    if args.cmd == "closure-ledger":
        def _closure_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            body = v003_engine.closure_ledger_summary(universe, args.subject)
            return v003_engine.envelope("closure-ledger", str(universe.get("edition", "unknown")), body)

        return _print_safe(_closure_payload)
    if args.cmd == "quality-report":
        def _quality_payload() -> dict[str, Any]:
            payload = quality_report_payload()
            return v003_engine.envelope("quality-report", "public", payload)

        return _print_safe(_quality_payload, spec_id="quality-report")
    if args.cmd == "corpus-completeness":
        def _corpus_payload() -> dict[str, Any]:
            payload = corpus_completeness_payload()
            return v003_engine.envelope("corpus-completeness", "public", payload)

        return _print_safe(_corpus_payload, spec_id="corpus-completeness")
    if args.cmd == "formula-quality":
        def _formula_payload() -> dict[str, Any]:
            payload = formula_quality_payload(strict=args.strict)
            status = "PASS"
            if args.strict and payload.get("strict_status") != "PASS":
                status = "FAIL_CLOSED"
            return v003_engine.envelope("formula-quality", "public", payload, status=status)

        return _print_safe(_formula_payload, spec_id="formula-quality")
    if args.cmd == "k-examples":
        def _k_examples_payload() -> dict[str, Any]:
            payload = k_examples_payload()
            if args.limit > 0:
                for section in ("sample_k_levels", "high_signal_examples", "notable_examples"):
                    rows = payload.get(section)
                    if isinstance(rows, list):
                        payload[section] = rows[: args.limit]
            return v003_engine.envelope("k-examples", "public", payload)

        return _print_safe(_k_examples_payload, spec_id="k-examples")
    if args.cmd == "surface-graph":
        def _surface_graph_payload() -> dict[str, Any]:
            payload = surface_graph_payload(include_rows=not args.summary_only)
            status = "PASS" if payload.get("status") == "PASS" else "FAIL_CLOSED"
            return v003_engine.envelope("surface-graph", "public", payload, status=status)

        return _print_safe(_surface_graph_payload, spec_id="surface-graph")
    if args.cmd == "verify-public-safety":
        target = Path(args.path) if args.path else Path.cwd() / "web" / "public" / "data"
        def _verify_payload() -> dict[str, Any]:
            body = v003_engine.verify_public_safety(target)
            return v003_engine.envelope("verify-public-safety", "public", body, status=body["status"])

        return _print_safe(_verify_payload)
    if args.cmd == "cerberus":
        def _cerberus_payload() -> dict[str, Any]:
            universe = v003_engine.load_universe()
            data_dir = v003_engine.find_data_dir()
            body = v003_engine.cerberus_summary(
                universe,
                data_dir,
                requested_version=args.version,
                require_strict_release_gate=args.no_mercy or args.zero_findings,
            )
            status = "PASS" if body.get("status") == "PASS" else "FAIL_CLOSED"
            return v003_engine.envelope("cerberus", str(universe.get("edition", "unknown")), body, status=status)

        return _print_safe(_cerberus_payload)
    if args.cmd == "desktop-smoke":
        def _desktop_payload() -> dict[str, Any]:
            body = desktop_smoke_payload()
            return v003_engine.envelope("desktop-smoke", "private", body, status=body.get("status", "FAIL_CLOSED"))

        return _print_safe(_desktop_payload, spec_id="desktop-smoke")
    if args.cmd == "build-private":
        return _print(
            _failure(
                "build-private",
                "Use scripts/build_public_artifacts.py --edition private --deploy-desktop; CLI exposes the command name for reviewer discoverability but does not rebuild artifacts in-process.",
            )
        )
    return _print(_failure(None, f"unknown command: {args.cmd}"))

