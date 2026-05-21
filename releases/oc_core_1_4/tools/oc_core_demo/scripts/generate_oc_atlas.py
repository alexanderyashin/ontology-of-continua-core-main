from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "oc_core_demo" / "data"
WEB_DATA = ROOT / "web" / "public" / "data"
DEMO_VERSION = "V010"
RELEASE_ORDINAL = "010"
RELEASE_LABEL = "OC Core 1.4 Demonstrator V010 Ideal RC"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")


def _clean(text: Any, limit: int = 420) -> str:
    value = str(text or "")
    replacements = {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        return value[: limit - 1].rstrip() + "..."
    return value


def _quality_flags(text: Any) -> list[str]:
    raw = str(text or "")
    clean = _clean(raw, 10000)
    flags: list[str] = []
    if not clean:
        flags.append("empty")
    if "Frozen proof/refute target ." in clean:
        flags.append("placeholder")
    if any(char in raw for char in ("\ufb00", "\ufb01", "\ufb02")):
        flags.append("ocr_ligature_normalized")
    if len(clean) > 420:
        flags.append("long_excerpt")
    return flags


def _concepts() -> list[dict[str, Any]]:
    rows = [
        ("continuum", "Continuum", "A bounded ongoing system whose identity is carried through relations and transformations.", "continuity under change", "#2563eb"),
        ("boundary", "Boundary", "The rule that separates what belongs to a continuum from its environment and interfaces.", "membership and interface", "#0f766e"),
        ("operator", "Operator", "A transformation acting on a continuum, changing state while preserving or breaking structure.", "action over state", "#7c3aed"),
        ("coherence", "Coherence", "The degree to which relations, evidence and operations still hold together.", "stability of relations", "#ca8a04"),
        ("collapse", "Collapse", "A transition where coherence debt overwhelms correction and the prior description fails.", "failure of continuity", "#dc2626"),
        ("emergence", "Emergence", "A pattern that becomes visible only through relations across levels or boundaries.", "new visible structure", "#db2777"),
        ("projection", "Projection", "A controlled view of a continuum into a domain, graph, simulation or claim surface.", "bounded translation", "#0891b2"),
        ("evidence_nonclaim", "Evidence / Nonclaim", "The rule that separates what the demo shows from what the science does not claim.", "trust boundary", "#475569"),
    ]
    return [
        {
            "id": row[0],
            "title": row[1],
            "short": row[2],
            "learning_goal": f"Understand {row[1].lower()} as {row[3]}.",
            "visual_metaphor": row[3],
            "color": row[4],
            "try_it": f"Change a parameter and watch how {row[1].lower()} moves in graph, simulation and evidence views.",
            "nonclaim": "This module teaches OC vocabulary; it is not an independent proof of the theory.",
        }
        for row in rows
    ]


def _journeys() -> list[dict[str, Any]]:
    return [
        {
            "id": "oc_in_12_minutes",
            "title": "OC in 12 minutes",
            "audience": "first-time reviewer",
            "promise": "Move from vocabulary to simulation, graph and proof boundary without reading source code.",
            "steps": [
                {"id": "j1", "title": "See the continuum", "concept": "continuum", "minutes": 2},
                {"id": "j2", "title": "Draw the boundary", "concept": "boundary", "minutes": 2},
                {"id": "j3", "title": "Run an operator", "concept": "operator", "minutes": 2},
                {"id": "j4", "title": "Watch coherence move", "concept": "coherence", "simulation": "transition_pressure_lab", "minutes": 2},
                {"id": "j5", "title": "Inspect the science graph", "view": "science_graph", "minutes": 2},
                {"id": "j6", "title": "Replay proof limits", "view": "proof_evidence", "minutes": 2},
            ],
        }
    ]


def _simulation_modules(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flagship = {
        "transition_pressure_lab": {"visual": "phase-flow", "concept": "coherence", "module_title": "Transition Pressure"},
        "degradation_recovery_lab": {"visual": "repair-curve", "concept": "collapse", "module_title": "Degradation / Recovery"},
        "dependency_propagation": {"visual": "network-wave", "concept": "projection", "module_title": "Dependency Propagation"},
        "evidence_sufficiency_calculator": {"visual": "evidence-radar", "concept": "evidence_nonclaim", "module_title": "Evidence Sufficiency"},
    }
    modules = []
    for spec in specs:
        if spec["spec_id"] not in flagship:
            continue
        meta = flagship[spec["spec_id"]]
        modules.append(
            {
                "id": spec["spec_id"],
                "title": meta["module_title"],
                "source_title": spec["title"],
                "concept": meta["concept"],
                "visual_type": meta["visual"],
                "purpose": spec["purpose"],
                "output_interpretation": spec.get("output_interpretation", ""),
                "parameters": spec.get("parameters", {}),
                "limits": spec.get("limits", []),
                "evidence_refs": spec.get("evidence_refs", []),
            }
        )
    return modules


def _cluster_for_node(node: dict[str, Any]) -> str:
    route = node.get("route") or "route"
    demo = node.get("demo_class") or "unknown"
    if route != "science-graph":
        return route
    if demo in {"SIMULATION", "PARAMETER_SANDBOX"}:
        return "simulatable"
    if demo in {"PROOF_TRACE_REPLAYER", "NOT_SIMULATABLE_PROOF_ONLY"}:
        return "proof-only"
    if demo == "CALCULATOR":
        return "calculator"
    return "structural"


def _graph(raw_graph: dict[str, Any]) -> dict[str, Any]:
    nodes = raw_graph.get("nodes", [])
    edges = raw_graph.get("edges", [])
    clusters = Counter(_cluster_for_node(node) for node in nodes)
    cluster_order = sorted(clusters)
    cluster_angles = {cluster: (2 * math.pi * index / max(1, len(cluster_order))) for index, cluster in enumerate(cluster_order)}
    cluster_seen: Counter[str] = Counter()
    enriched_nodes = []
    for node in nodes:
        cluster = _cluster_for_node(node)
        cluster_seen[cluster] += 1
        angle = cluster_angles[cluster] + cluster_seen[cluster] * 0.19
        radius = 5 + (cluster_seen[cluster] % 19) * 0.17
        statement = node.get("statement", "")
        enriched_nodes.append(
            {
                "id": node["id"],
                "label": node.get("label", node["id"]),
                "route": node.get("route", ""),
                "demo_class": node.get("demo_class", ""),
                "demo_spec_id": node.get("demo_spec_id", ""),
                "evidence_class": node.get("evidence_class", ""),
                "statement_excerpt": _clean(statement),
                "quality_flags": _quality_flags(statement),
                "cluster": cluster,
                "x": round(math.cos(angle) * radius + cluster_order.index(cluster) * 0.5, 5),
                "y": round(math.sin(angle) * radius, 5),
                "size": 12 if not node["id"].startswith("OC14-N") else 5,
            }
        )
    return {
        "summary": {
            **raw_graph.get("summary", {}),
            "cluster_counts": dict(clusters),
            "relation_counts": dict(Counter(edge.get("relation", "related") for edge in edges)),
        },
        "nodes": enriched_nodes,
        "edges": [
            {"id": f"e{index:04d}", "source": edge["from"], "target": edge["to"], "relation": edge.get("relation", "related")}
            for index, edge in enumerate(edges)
        ],
    }


def _proof_routes(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes = []
    for row in targets:
        statement = row.get("public_statement_excerpt", "")
        routes.append(
            {
                "target_id": row["public_target_id"],
                "label": row.get("public_label", row["public_target_id"]),
                "status": row.get("terminal_status_public", "unknown"),
                "demo_class": row.get("demo_class", ""),
                "demo_spec_id": row.get("demo_spec_id", ""),
                "evidence_class": row.get("public_evidence_class", ""),
                "ui_route": row.get("ui_route", ""),
                "statement_excerpt": _clean(statement),
                "quality_flags": _quality_flags(statement),
                "rationale": _clean(row.get("rationale", ""), 520),
                "non_simulated_reason": _clean(row.get("non_simulated_reason", ""), 520),
                "trace": [
                    "public statement",
                    row.get("public_evidence_class", "public evidence"),
                    row.get("ui_route", "public route"),
                    row.get("terminal_status_public", "status"),
                    "explicit nonclaim boundary",
                ],
            }
        )
    return routes


def build_atlas() -> dict[str, Any]:
    specs = _read_json(DATA / "demo_specs.json")["specs"]
    raw_graph = _read_json(DATA / "interactive_graph.json")
    targets = _read_json(DATA / "public_targets.json")["targets"]
    concepts = _concepts()
    return {
        "schema_version": "oc-core-demo-atlas.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "title": "Ontology of Continua Core 1.4 System Workbench",
        "generated_from": {
            "spec_total": len(specs),
            "target_total": len(targets),
            "graph_nodes": len(raw_graph.get("nodes", [])),
            "graph_edges": len(raw_graph.get("edges", [])),
        },
        "concepts": concepts,
        "journeys": _journeys(),
        "simulations": _simulation_modules(specs),
        "graph": _graph(raw_graph),
        "proof_routes": _proof_routes(targets),
        "glossary": [
            {"term": concept["title"], "definition": concept["short"], "concept_id": concept["id"]}
            for concept in concepts
        ],
        "evidence_roles": [
            {"id": "source_binding", "title": "Source Binding", "definition": "Statement is attached to public evidence context."},
            {"id": "dependency_closure", "title": "Dependency Closure", "definition": "The graph route identifies consequences and limits."},
            {"id": "verification_strength", "title": "Verification Strength", "definition": "The route explains how strong the public support is."},
            {"id": "nonclaim_clarity", "title": "Nonclaim Clarity", "definition": "The app says what is not proven or not externally reviewed."},
        ],
        "reviewer_mode": {
            "checklist": [
                "Complete OC in 12 minutes",
                "Run one simulation and export JSON",
                "Inspect one graph route",
                "Replay one proof/evidence target",
                "Read the nonclaim boundary",
            ],
            "external_actions": 0,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate V010 compatibility OC atlas assets.")
    parser.add_argument("--out", default=str(WEB_DATA), help="Output directory for generated JSON assets.")
    args = parser.parse_args(argv)
    out = Path(args.out)
    atlas = build_atlas()
    _write_json(out / "oc_atlas.json", atlas)
    _write_json(out / "concept_modules.json", atlas["concepts"])
    _write_json(out / "science_graph.json", atlas["graph"])
    _write_json(out / "sim_specs.json", atlas["simulations"])
    _write_json(out / "proof_routes.json", atlas["proof_routes"])
    print(json.dumps({"status": "PASS", "out": str(out), "targets": len(atlas["proof_routes"]), "nodes": len(atlas["graph"]["nodes"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

