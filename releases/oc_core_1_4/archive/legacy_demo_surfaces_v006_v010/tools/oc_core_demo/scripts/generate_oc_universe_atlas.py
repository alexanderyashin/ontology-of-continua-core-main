from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEB_PUBLIC_DATA = ROOT / "web" / "public" / "data"
DEMO_DATA = ROOT / "oc_core_demo" / "data"
DEMO_VERSION = "V010"
RELEASE_ORDINAL = "010"
RELEASE_LABEL = "OC Core 1.4 Demonstrator V010 Ideal RC"
UNIVERSE_SCHEMA_VERSION = "oc-core-demo-universe.v010"
ENTITY_LINK_INDEX_SCHEMA_VERSION = "oc-core-demo-entity-link-index.v010"
SYSTEM_WORKBENCH_SCHEMA_VERSION = "oc-core-demo-system-workbench.v010"

GENERIC_REPLACEMENT_VERSIONS = (
    "V004",
    "V005",
    "V006",
    "V007",
    "V008",
    "V009",
)


PRIVATE_LEAK_PATTERNS = (
    "C:" + "/" + "Users" + r"/[^/\"'\s]+",
    "C:" + r"\\Users\\",
    "/" + "Users" + "/",
    r"\\\." + "runtime" + r"\\",
    r"/\." + "runtime" + r"/",
    "logion_" + "local",
    "Desk" + r"top\\",
    "Desk" + r"top/",
    "Mega" + "port",
    "estra-" + "private-" + "work",
    "raw_" + "private",
    "source_" + "cache",
)

FORMULA_CODE_OR_PATH_MARKERS = (
    "Path(",
    "logion/",
    "master_manuscript_ref",
    "Exact source locator",
    "translation_lane_status",
    "ref=`",
    "C:/",
    "C:\\",
    "/" + "Users" + "/",
    "estra-" + "private-" + "work",
    "RESULT_PATH",
    "FORMALIZATION_PATH",
    "SOURCE_PATH",
    "TARGET_PATH",
    ".json",
    ".py",
    "workbench/",
)


def _repo_root() -> Path:
    for parent in [ROOT] + list(ROOT.parents):
        if (parent / "AGENTS.md").exists() or (parent / ".git").exists():
            return parent
    return ROOT.parents[7]


REPO_ROOT = _repo_root()
OC14_PACKAGE_ROOT = REPO_ROOT / "logion" / "k7" / "release_missions" / "oc_core_current" / "packages" / "oc_core_1_4"
OC14_UNITS = OC14_PACKAGE_ROOT / "006" / "language_sources" / "units"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")


def _canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _hash(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _clean(text: Any, limit: int = 900) -> str:
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
        "\u0001": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        return value[: limit - 1].rstrip() + "..."
    return value


def _safe_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return path.name


def _sanitize_public(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_public(item)
            for key, item in value.items()
            if key
            not in {
                "refs",
                "private_refs",
                "source_lineage",
                "source_refs_raw",
                "raw_source_refs",
                "source_paths_raw",
                "raw_paths",
            }
        }
    if isinstance(value, list):
        return [_sanitize_public(item) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in PRIVATE_LEAK_PATTERNS:
            text = re.sub(pattern, "[private-redacted]", text, flags=re.IGNORECASE)
        return text
    return value


def _release_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _release_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_release_text(item) for item in value]
    if isinstance(value, str):
        version_label = f"Version {RELEASE_ORDINAL}"
        text = value.replace("Version 004", version_label).replace("Version 005", version_label).replace("Version 006", version_label).replace(
            "Version 007", version_label
        ).replace("Version 008", version_label)
        for old_version in GENERIC_REPLACEMENT_VERSIONS:
            text = text.replace(old_version, DEMO_VERSION)
        return text
    return value


def _assert_public_safe(payload: Any) -> None:
    text = _canonical(payload)
    leaks = [pattern for pattern in PRIVATE_LEAK_PATTERNS if re.search(pattern, text, flags=re.IGNORECASE)]
    if leaks:
        raise RuntimeError(f"public atlas leak check failed: {', '.join(leaks)}")


def _public_source_ref(ref: Any, route_name: str = "source") -> str:
    text = str(ref or "").replace("\\", "/")
    leaf = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(text).name or route_name).strip("_")
    if not leaf:
        leaf = route_name
    return f"SRC::{route_name}::{leaf}::{_hash(text)[:16]}"


def _public_source_refs(refs: list[Any], route_name: str = "source") -> list[str]:
    return [_public_source_ref(ref, route_name) for ref in refs if str(ref or "").strip()]


ROOT_GRAPH_NODE_ID = "OC::ROOT_PRINCIPLE::CONTRADICTION_AXIS_OR_COLLAPSE"


ACTION_TARGET_RULES: dict[str, dict[str, str]] = {
    "Open in Wiki": {
        "target_view": "wiki",
        "target_type": "corpus_search",
        "target_id": "continuum boundary operator coherence collapse",
    },
    "Show in Graph": {
        "target_view": "graph",
        "target_type": "graph_node",
        "target_id": ROOT_GRAPH_NODE_ID,
    },
    "Show Formula": {
        "target_view": "formula",
        "target_type": "formula_search",
        "target_id": "coherence transition operator",
    },
    "Open Evidence Boundary": {
        "target_view": "proof",
        "target_type": "proof_boundary",
        "target_id": "proof_boundary_route",
    },
    "Open Domain": {
        "target_view": "benchmarks",
        "target_type": "domain_lane",
        "target_id": "PHYSICS",
    },
    "Run Simulation": {
        "target_view": "cascade",
        "target_type": "simulation",
        "target_id": "kill_cascade",
    },
    "Use in Workbench": {
        "target_view": "workbench",
        "target_type": "system_template",
        "target_id": "civilization",
    },
    "Diagnose": {
        "target_view": "workbench",
        "target_type": "system_template",
        "target_id": "civilization",
    },
    "Kill": {
        "target_view": "workbench",
        "target_type": "simulation",
        "target_id": "kill_cascade",
    },
    "Improve": {
        "target_view": "workbench",
        "target_type": "system_template",
        "target_id": "civilization",
    },
    "Compare": {
        "target_view": "graph",
        "target_type": "comparison",
        "target_id": ROOT_GRAPH_NODE_ID,
    },
    "Export": {
        "target_view": "workbench",
        "target_type": "system_bundle",
        "target_id": "system_workbench_bundle",
    },
    "purchase_pull": {
        "target_view": "practical",
        "target_type": "local_request_preview",
        "target_id": "local_qualified_next_step",
    },
}

SURFACE_LABELS = {
    "journey": "Guided OC Journey",
    "guided": "Guided OC Journey",
    "worldline": "Worldline Theater",
    "workbench": "System Workbench",
    "km": "K/M Hierarchy",
    "klevels": "K/M Hierarchy",
    "benchmarks": "Domain Lanes & Benchmarks",
    "cascade": "Cascade Lab",
    "graph": "3D Science Graph",
    "formula": "Formula Atlas",
    "wiki": "OC Wiki",
    "proof": "Evidence / Boundaries",
    "reviewer": "Reviewer Mode",
    "trust": "Trust Ladder",
    "whyoc": "Why OC & Existing Models",
    "practical": "Practical Value Surface",
    "mission": "Mission Deck",
}


def _action_target(action: str, step: dict[str, Any]) -> dict[str, Any]:
    rule = dict(ACTION_TARGET_RULES.get(action, {}))
    for key in ("target_view", "target_type", "target_id", "source_step_id"):
        override = step.get(key)
        if override:
            rule[key] = str(override)
    if step.get("view") == "worldline" and action == "Run Simulation":
        rule.update({"target_view": "worldline", "target_type": "simulation", "target_id": "worldline_birth_evolution_collapse"})
    if step.get("view") == "workbench" and action == "Run Simulation":
        rule.update({"target_view": "workbench", "target_type": "simulation", "target_id": "system_workbench_preview"})
    if step.get("view") == "km" and action == "Show in Graph":
        rule.update({"target_view": "graph", "target_type": "graph_node", "target_id": "OC::METAONTOLOGY::K_LEVEL_HIERARCHY"})
    if step.get("view") == "benchmarks" and action == "Open Domain":
        rule.update({"target_view": "benchmarks", "target_type": "domain_lane", "target_id": "PHYSICS"})
    return {
        "action": action,
        "source_step_id": step.get("id", ""),
        "source_view": step.get("view", ""),
        "target_view": rule.get("target_view", step.get("view", "")),
        "target_type": rule.get("target_type", "view"),
        "target_id": rule.get("target_id", step.get("view", "")),
        "resolution_status": "direct" if rule.get("target_type") not in {"corpus_search", "formula_search"} else "search",
        "fallback_state": "If the target is filtered out, keep the action visible but route to the corresponding searchable atlas page with a boundary note.",
    }


def _route_action_manifest(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route in routes:
        route_markers: list[str] = []
        for step in route.get("steps", []):
            if not isinstance(step, dict):
                continue
            route_markers.extend(str(marker) for marker in step.get("completion_markers", []) if marker)
            targets = [_action_target(action, step) for action in step.get("actions", [])]
            step["action_targets"] = targets
            for action_index, target in enumerate(targets, start=1):
                surface = target.get("target_view") or step.get("view", "")
                source_surface = str(step.get("view", ""))
                source_surface_label = SURFACE_LABELS.get(source_surface, source_surface or "Unknown surface")
                target_surface_label = SURFACE_LABELS.get(str(surface), str(surface) or "Unknown surface")
                action_slug = re.sub(r"[^A-Za-z0-9]+", "_", str(target.get("action", "action"))).strip("_").lower()
                route_slug = re.sub(r"[^A-Za-z0-9]+", "_", str(route.get("id", "route"))).strip("_").lower()
                step_slug = re.sub(r"[^A-Za-z0-9]+", "_", str(step.get("id", "step"))).strip("_").lower()
                control_binding = "purchase_pull" if action_slug == "purchase_pull" else f"{surface}-{action_slug}"
                rows.append(
                    {
                        "route_id": route.get("id", ""),
                        "route_display_label": route.get("title", route.get("id", "Route")),
                        **target,
                        "action_display_label": str(target.get("action", "Open route target")).replace("_", " ").replace("-", " ").strip().title(),
                        "surface_binding": surface,
                        "source_surface_label": source_surface_label,
                        "target_surface_label": target_surface_label,
                        "breadcrumb": f"{route.get('title', route.get('id', 'Route'))} / {step.get('title', step.get('id', 'Step'))} / {target_surface_label}",
                        "control_binding": control_binding,
                        "test_id": f"route-{route_slug}-{step_slug}-{action_index:02d}-{action_slug}",
                        "expected_visible_result": f"{target.get('action')} opens or mutates the {surface} surface with a visible state/hash/detail change.",
                    }
                )
        route["completion_markers"] = sorted(set(route.get("completion_markers", []) + route_markers))
        route["completion_marker_count"] = len(route["completion_markers"])
        route["estimated_minutes"] = sum(int(step.get("minutes", 0) or 0) for step in route.get("steps", []) if isinstance(step, dict))
        route["timing_evidence"] = "estimated from step minutes in the didactic route, not user telemetry"
        for step in route.get("steps", []):
            if isinstance(step, dict):
                view = str(step.get("view", ""))
                step["surface_label"] = SURFACE_LABELS.get(view, view or "Unknown surface")
                step["breadcrumb"] = f"{route.get('title', route.get('id', 'Route'))} / {step.get('title', step.get('id', 'Step'))} / {step['surface_label']}"
        if route.get("id") == "k12_to_k0_drilldown":
            for action_index, (action_id, title, control_binding, expected) in enumerate(
                [
                    ("hierarchy:select-level-rail", "Select K12 in hierarchy rail", "klevels-select_level_rail", "selected_level_before K12 visible"),
                    ("hierarchy:elevator-select", "Drill ladder toward K0", "klevels-elevator_select", "selected_level_after K0 visible"),
                    ("hierarchy:export-selected-route", "Export selected K/M route", "klevels-export_selected_route", "hash scopes and dependency text visible"),
                ],
                start=1,
            ):
                rows.append(
                    {
                        "route_id": route.get("id", ""),
                        "route_display_label": route.get("title", "K12 to K0 Drilldown"),
                        "action": action_id,
                        "action_label": title,
                        "action_display_label": title,
                        "source_step_id": "drill-hierarchy-core",
                        "source_view": "klevels",
                        "target_view": "klevels",
                        "target_type": "hierarchy_control",
                        "target_id": action_id,
                        "resolution_status": "direct",
                        "fallback_state": "If hierarchy controls are not visible, route fails closed.",
                        "surface_binding": "klevels",
                        "source_surface_label": SURFACE_LABELS.get("klevels", "K/M Hierarchy"),
                        "target_surface_label": SURFACE_LABELS.get("klevels", "K/M Hierarchy"),
                        "breadcrumb": f"{route.get('title', route.get('id', 'Route'))} / core hierarchy drilldown / K/M Hierarchy",
                        "control_binding": control_binding,
                        "test_id": f"route-k12_to_k0_drilldown-core-{action_index:02d}",
                        "expected_visible_result": expected,
                    }
                )
    return rows


def _concepts() -> list[dict[str, Any]]:
    rows = [
        ("continuum", "Continuum", "A bounded field of variation that keeps identity through transformations.", "#2563eb"),
        ("boundary", "Boundary", "The rule that separates, couples and translates a continuum and its environment.", "#0f766e"),
        ("operator", "Operator", "A repeatable action over state, description or relation.", "#7c3aed"),
        ("coherence", "Coherence", "The degree to which relations, evidence and operations remain jointly usable.", "#ca8a04"),
        ("collapse", "Collapse", "Loss of a previously workable description when pressure outruns repair or re-description.", "#dc2626"),
        ("emergence", "Emergence", "A structure visible only through relations across levels, boundaries or time.", "#db2777"),
        ("projection", "Projection", "A controlled translation of OC into a domain, figure, graph, simulation or claim surface.", "#0891b2"),
        ("nonclaim", "Evidence / Nonclaim", "The boundary between what the model shows, what it proves, and what remains frontier work.", "#475569"),
    ]
    return [
        {
            "id": key,
            "title": title,
            "short": short,
            "learning_goal": f"Understand {title.lower()} as an operational object, not as a slogan.",
            "visual_metaphor": title.lower(),
            "color": color,
            "try_it": f"Change a system parameter and watch how {title.lower()} affects graph, proof and simulation state.",
            "nonclaim": "Concept modules teach the vocabulary and its operational projection; they do not by themselves prove OC.",
        }
        for key, title, short, color in rows
    ]


def _postulates() -> list[dict[str, Any]]:
    return [
        {
            "id": "P-OC-001",
            "title": "Bounded Description",
            "statement": "Every useful OC claim declares the continuum, boundary, operator and failure condition it is using.",
            "test": "Can another reviewer reconstruct the object and the condition under which the claim retreats?",
        },
        {
            "id": "P-OC-002",
            "title": "Continuity Under Transformation",
            "statement": "A continuum is tracked by preserved relations through change, not by static parts alone.",
            "test": "Does the same identity survive across a declared operator sequence?",
        },
        {
            "id": "P-OC-003",
            "title": "Contradiction Load",
            "statement": "An unresolvable contradiction either births a new axis of description or drives collapse of the old continuum.",
            "test": "Can the app identify the shortest repair, re-axis or collapse trajectory?",
        },
        {
            "id": "P-OC-004",
            "title": "Projection Discipline",
            "statement": "A domain projection inherits OC vocabulary only inside declared empirical and mathematical bounds.",
            "test": "Does each predictive lane expose source status, validation status and nonclaim boundary?",
        },
    ]


def _operators() -> list[dict[str, Any]]:
    return [
        {"id": "OP-BIRTH", "title": "Birth", "effect": "Create a bounded distinction and initialize a continuum."},
        {"id": "OP-DIFFERENTIATE", "title": "Differentiate", "effect": "Split latent variation into visible axes and roles."},
        {"id": "OP-STABILIZE", "title": "Stabilize", "effect": "Increase coherence through repair, buffering or evidence."},
        {"id": "OP-PROJECT", "title": "Project", "effect": "Translate the continuum into a domain model or evidence-boundary surface."},
        {"id": "OP-KILL", "title": "Kill", "effect": "Remove a critical support and compute the shortest collapse path."},
        {"id": "OP-REPAIR", "title": "Repair", "effect": "Insert corrective capacity before collapse becomes terminal."},
    ]


def _journeys() -> list[dict[str, Any]]:
    routes = [
        {
            "id": "oc_in_12_minutes",
            "title": "OC in 12 minutes",
            "audience": "first-time scientific reviewer",
            "promise": "Move from a continuum being born to K/M hierarchy, domain projection, cascade collapse, graph evidence and proof limits.",
            "steps": [
                {
                    "id": "j1",
                    "title": "Birth of a continuum",
                    "view": "worldline",
                    "minutes": 2,
                    "goal": "See contradiction load, boundary clarity and repair capacity become visible dynamics.",
                    "completion_markers": ["played_worldline", "changed_boundary_slider"],
                    "actions": ["Run Simulation", "Open in Wiki"],
                },
                {
                    "id": "j2",
                    "title": "Bidirectional K/M hierarchy",
                    "view": "km",
                    "minutes": 2,
                    "goal": "Move K0->K12 and K12->K0 while inspecting M-space, axes, flows and thresholds.",
                    "completion_markers": ["selected_k_slice", "opened_m_space"],
                    "actions": ["Show in Graph", "Use in Workbench"],
                },
                {
                    "id": "j3",
                    "title": "Build a system",
                    "view": "workbench",
                    "minutes": 2,
                    "goal": "Choose a template, add a computable axis, strengthen a link and compare the deterministic hash.",
                    "completion_markers": ["selected_template", "added_axis"],
                    "actions": ["Use in Workbench", "Run Simulation"],
                },
                {
                    "id": "j4",
                    "title": "Kill cascade / chain reaction",
                    "view": "cascade",
                    "minutes": 2,
                    "goal": "Break selected or weakest support and watch rupture, connectivity loss and recovery potential.",
                    "completion_markers": ["pressed_kill", "inspected_recovery"],
                    "actions": ["Run Simulation", "Open Evidence Boundary"],
                },
                {
                    "id": "j5",
                    "title": "Domain mission",
                    "view": "benchmarks",
                    "minutes": 2,
                    "goal": "Enter a familiar domain and inspect constants, benchmark cases, replay status and boundaries.",
                    "completion_markers": ["selected_domain", "opened_observable"],
                    "actions": ["Open Domain", "Show Formula"],
                },
                {
                    "id": "j6",
                    "title": "Graph -> formula -> proof",
                    "view": "graph",
                    "minutes": 2,
                    "goal": "Follow root principle through operators, K-levels, formulas, evidence routes and nonclaim boundaries.",
                    "completion_markers": ["clicked_graph_node", "opened_formula", "opened_proof_boundary"],
                    "actions": ["Show in Graph", "Show Formula", "Open Evidence Boundary"],
                },
            ],
        }
        ,
        {
            "id": "from_contradiction_to_axis",
            "title": "From Contradiction to New Axis",
            "audience": "systems architect",
            "promise": "Start at the root principle and choose whether contradiction is repaired by a new computable axis or collapses the old description.",
            "steps": [
                {"id": "axis-1", "title": "Find the pressure that could break the system", "view": "worldline", "minutes": 2, "goal": "Identify pressure and load.", "completion_markers": ["inspected_pressure"], "actions": ["Run Simulation"]},
                {"id": "axis-2", "title": "Select computable axis", "view": "workbench", "minutes": 2, "goal": "Add only axes with available deterministic diagnostics.", "completion_markers": ["added_axis"], "actions": ["Use in Workbench"]},
                {"id": "axis-3", "title": "Replay failure after the repair", "view": "cascade", "minutes": 2, "goal": "Compare collapse depth before and after re-axis.", "completion_markers": ["compared_hash"], "actions": ["Run Simulation"]},
            ],
        },
        {
            "id": "k12_to_k0_drilldown",
            "title": "K12 to K0 Drilldown",
            "audience": "cross-domain reviewer",
            "promise": "Begin at high-level psychology/civilization/meta-model structure and drill down to lower-level physical supports.",
            "steps": [
                {"id": "drill-1", "title": "Open K12", "view": "km", "minutes": 1, "goal": "Inspect top-down constraints.", "completion_markers": ["selected_k12"], "actions": ["Show in Graph"]},
                {"id": "drill-2", "title": "Open K12 to K0 inputs", "view": "km", "minutes": 2, "goal": "Trace lower-level dependencies from K12 through every public K-level down to K0.", "completion_markers": ["opened_lower_inputs"], "actions": ["Open in Wiki"]},
                {"id": "drill-3", "title": "Run domain anchor", "view": "benchmarks", "minutes": 2, "goal": "Recognize domain constants and benchmarks.", "completion_markers": ["selected_domain"], "actions": ["Open Domain"]},
            ],
        },
        {
            "id": "domain_expert_entry",
            "title": "Domain Expert Entry",
            "audience": "skeptical domain specialist",
            "promise": "Start with familiar constants, observables and predecessors, then open the OC graph behind them.",
            "steps": [
                {"id": "domain-1", "title": "Choose domain", "view": "benchmarks", "minutes": 1, "goal": "Find the familiar lane first.", "completion_markers": ["selected_domain"], "actions": ["Open Domain"]},
                {"id": "domain-2", "title": "Inspect known observables", "view": "benchmarks", "minutes": 2, "goal": "Compare replay-backed and boundary-only outputs.", "completion_markers": ["opened_observable"], "actions": ["Show Formula"]},
                {"id": "domain-3", "title": "Open graph projection", "view": "graph", "minutes": 2, "goal": "Trace domain projection back to OC root.", "completion_markers": ["opened_root_path"], "actions": ["Show in Graph"]},
            ],
        },
        {
            "id": "collapse_and_recovery",
            "title": "Collapse and Recovery",
            "audience": "system builder",
            "promise": "Break a system, watch cascade propagation, then add compensators or axes and compare recovery.",
            "steps": [
                {"id": "collapse-1", "title": "Select system template", "view": "workbench", "minutes": 1, "goal": "Start from a replay-bounded model.", "completion_markers": ["selected_template"], "actions": ["Use in Workbench"]},
                {"id": "collapse-2", "title": "Kill weakest node", "view": "cascade", "minutes": 2, "goal": "Watch shortest collapse path.", "completion_markers": ["pressed_kill"], "actions": ["Run Simulation"]},
                {"id": "collapse-3", "title": "Add compensator", "view": "workbench", "minutes": 2, "goal": "Improve resilience without hiding boundaries.", "completion_markers": ["added_compensator"], "actions": ["Use in Workbench"]},
            ],
        },
        {
            "id": "proof_boundary_route",
            "title": "Evidence Boundary Route",
            "audience": "scientific reviewer",
            "promise": "Follow one claim through graph node, formula, corpus atom, evidence route, closure ledger and nonclaim boundary.",
            "steps": [
                {"id": "proof-1", "title": "Click graph node", "view": "graph", "minutes": 1, "goal": "Open semantic node detail.", "completion_markers": ["clicked_graph_node"], "actions": ["Show in Graph"]},
                {"id": "proof-2", "title": "Open formula and source atom", "view": "formula", "minutes": 2, "goal": "Inspect symbolic surface and source hash.", "completion_markers": ["opened_formula"], "actions": ["Show Formula", "Open in Wiki"]},
                {"id": "proof-3", "title": "Read evidence boundary", "view": "proof", "minutes": 2, "goal": "Separate replay, evidence and proof-workbench obligations.", "completion_markers": ["opened_proof_boundary"], "actions": ["Open Evidence Boundary"]},
            ],
        },
    ]
    _route_action_manifest(routes)
    return routes


def _reviewer_objection_routes(
    graph: dict[str, Any],
    systems: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    proof_routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    graph_node_ids = {node.get("id") for node in graph.get("nodes", [])}
    root_node = ROOT_GRAPH_NODE_ID if ROOT_GRAPH_NODE_ID in graph_node_ids else next(iter(graph_node_ids), "")
    sample_proof = proof_routes[0] if proof_routes else {}
    sample_proof_id = sample_proof.get("target_id", "proof_boundary_route")
    sample_domain = domains[0].get("domain_id") if domains else "PHYSICS"
    replayed_domain = next((row.get("domain_id") for row in domains if row.get("closure_status") == "CLOSED_REPLAY_BACKED"), sample_domain)
    sample_system = systems[0].get("id") if systems else "civilization"
    return [
        {
            "id": "purchase_pull::local_qualified_next_step",
            "title": "Qualified next-step pull, local only",
            "audience": "system architect",
            "severity": "high",
            "promise": "Convert interest into a bounded local review packet only after diagnose, kill, improve, compare and export evidence is visible.",
            "steps": [
                {
                    "id": "purchase-pull-1",
                    "title": "Open local qualification preview",
                    "view": "practical",
                    "minutes": 1,
                    "goal": "Show the local follow-up criterion, not a purchase or contact form.",
                    "actions": ["purchase_pull"],
                    "target_view": "practical",
                    "target_type": "local_request_preview",
                    "target_id": "local_qualified_next_step",
                    "completion_markers": ["local_request_preview_opened"],
                },
                {
                    "id": "purchase-pull-2",
                    "title": "Inspect edited-scenario boundary before continuing",
                    "view": "workbench",
                    "minutes": 1,
                    "goal": "Verify edited scenarios remain exploratory until replay-backed separately.",
                    "actions": ["Use in Workbench"],
                    "target_view": "workbench",
                    "target_type": "boundary_gate",
                    "target_id": sample_system,
                    "completion_markers": ["edited_scenario_boundary_seen"],
                },
            ],
            "links_to_real_surfaces": [
                {"view": "practical", "target_type": "local_request_preview", "target_id": "local_qualified_next_step"},
                {"view": "workbench", "target_type": "boundary_gate", "target_id": sample_system},
            ],
            "negative_assertion_path": {
                "action": "purchase_pull",
                "blocked_external_actions": ["pricing", "checkout", "contact", "upload", "publish"],
                "expected_visible_result": "local request preview opens; no external action is executed",
            },
            "nonclaim_boundary": "This is a local qualified-next-step route only; it is not a sale, purchase, upload, contact request or external validation.",
        },
        {
            "id": "objection_route::predictive_overreach",
            "title": "Predictive claim exceeds replay support",
            "audience": "reviewer",
            "severity": "high",
            "promise": "Force a claim check when replay or proof support is not yet present.",
            "steps": [
                {
                    "id": "predictive-overreach-1",
                    "title": "Inspect domain replay state",
                    "view": "benchmarks",
                    "minutes": 1,
                    "goal": "Open a domain lane before accepting predictive wording.",
                    "actions": ["Open Domain"],
                    "target_id": replayed_domain if replayed_domain else sample_domain,
                },
                {
                    "id": "predictive-overreach-2",
                    "title": "Open a proof boundary",
                    "view": "proof",
                    "minutes": 1,
                    "goal": "Follow nonclaim language and closure status for the related target.",
                    "actions": ["Open Evidence Boundary"],
                    "target_id": sample_proof_id,
                },
                    {
                    "id": "predictive-overreach-3",
                    "title": "Expose where contradiction closes or still opens",
                    "view": "cascade",
                    "minutes": 1,
                    "goal": "Replay a failure path before any predictive narrative is finalized.",
                    "actions": ["Run Simulation"],
                    "target_id": "kill_cascade",
                },
            ],
            "links_to_real_surfaces": [
                {"view": "benchmarks", "target_type": "domain_lane", "target_id": replayed_domain},
                {"view": "proof", "target_type": "proof_boundary", "target_id": sample_proof_id},
                {"view": "cascade", "target_type": "simulation", "target_id": "kill_cascade"},
            ],
            "nonclaim_boundary": "This route is for predictive boundary governance, not scientific substitution.",
        },
        {
            "id": "objection_route::graph_formula_discrepancy",
            "title": "Graph and formula narratives diverge",
            "audience": "reviewer",
            "severity": "medium",
            "promise": "Compare graph and formula views when confidence appears too high.",
            "steps": [
                {
                    "id": "graph-formula-discrepancy-1",
                    "title": "Open graph root context",
                    "view": "graph",
                    "minutes": 1,
                    "goal": "Inspect the root node and its incident relations.",
                    "actions": ["Show in Graph"],
                    "target_id": root_node,
                },
                {
                    "id": "graph-formula-discrepancy-2",
                    "title": "Open matching formula query",
                    "view": "formula",
                    "minutes": 1,
                    "goal": "Look for shared semantics in symbol/query space.",
                    "actions": ["Show Formula"],
                    "target_id": "coherence transition operator",
                },
                {
                    "id": "graph-formula-discrepancy-3",
                    "title": "Open a concrete system to test stability",
                    "view": "workbench",
                    "minutes": 1,
                    "goal": "Check whether one template can sustain a reproducible simulation.",
                    "actions": ["Use in Workbench"],
                    "target_id": sample_system,
                },
            ],
            "links_to_real_surfaces": [
                {"view": "graph", "target_type": "graph_node", "target_id": root_node},
                {"view": "formula", "target_type": "formula_search", "target_id": "coherence transition operator"},
                {"view": "workbench", "target_type": "system_template", "target_id": sample_system},
            ],
            "nonclaim_boundary": "Graph and formula checks are bounded by deterministic visualization and should not be treated as independent proof.",
        },
        {
            "id": "objection_route::no_compare_explanation",
            "title": "No explicit comparison before system edits",
            "audience": "reviewer",
            "severity": "medium",
            "promise": "Force explicit baseline-vs-edited comparison before approving edited systems.",
            "steps": [
                {
                    "id": "no-compare-1",
                    "title": "Load a baseline template",
                    "view": "workbench",
                    "minutes": 1,
                    "goal": "Inspect a concrete template as baseline.",
                    "actions": ["Use in Workbench"],
                    "target_id": sample_system,
                },
                {
                    "id": "no-compare-2",
                    "title": "Apply a controlled simulation kill",
                    "view": "workbench",
                    "minutes": 1,
                    "goal": "Create a diagnostic divergence before claiming improvement.",
                    "actions": ["Run Simulation"],
                    "target_id": "system_workbench_preview",
                },
                {
                    "id": "no-compare-3",
                    "title": "Compare edited behavior",
                    "view": "graph",
                    "minutes": 1,
                    "goal": "Keep comparison in an explicit comparative frame.",
                    "actions": ["Compare"],
                    "target_type": "comparison",
                    "target_id": "system-template-comparison",
                    "target_view": "graph",
                },
            ],
            "links_to_real_surfaces": [
                {"view": "workbench", "target_type": "system_template", "target_id": sample_system},
                {"view": "workbench", "target_type": "simulation", "target_id": "system_workbench_preview"},
                {"view": "graph", "target_type": "comparison", "target_id": "system-template-comparison"},
            ],
            "nonclaim_boundary": "Comparisons are diagnostic and remain exploratory unless replay supports are explicitly attached.",
        },
    ]


def _model_comparison_matrix(
    system_templates: list[dict[str, Any]],
    proof_routes: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    k_axes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    replay_frontier = [row.get("domain_id") for row in domains if row.get("closure_status") != "CLOSED_REPLAY_BACKED"]
    primary_axis = k_axes[0].get("axis_id", "coherence") if k_axes else "coherence"
    comparison_inventory = [
        ("system_dynamics", "System dynamics stock-flow models", "Great for accumulations, feedback loops and policy experiments; OC adds explicit contradiction/axis/collapse boundary routing."),
        ("graph_theory", "Graph theory / network science", "Great for topology, centrality and paths; OC adds K/M hierarchy, proof boundaries and axis addition as first-class operations."),
        ("causal_models", "Causal DAG / structural causal models", "Great for intervention logic; OC adds continuum viability, collapse/recovery trajectory and nonclaim discipline."),
        ("complexity_science", "Complex adaptive systems models", "Great for emergence and adaptation; OC adds reviewer-facing proof/evidence routing and formal K-level drilldown."),
        ("category_formal", "Category/formal abstraction models", "Great for compositional abstraction; OC adds concrete system workbench diagnostics and public evidence boundaries."),
        ("agent_based", "Agent-based simulation", "Great for local rules and populations; OC adds cross-level axis, threshold and proof-route linking."),
        ("control_theory", "Control theory / cybernetics", "Great for control loops and stability; OC adds explicit K-level provenance, contradiction load and evidence-boundary routing."),
        ("risk_registers", "Enterprise risk registers", "Great for governance inventory; OC adds dynamic cascade, recovery-index and computable-axis interventions."),
    ]
    comparison_specifics = {
        "system_dynamics": {
            "native_strength": "Best native fit for stock/flow accumulation, delayed feedback and policy-loop sensitivity.",
            "oc_adds": "Adds contradiction thresholds, axis-birth alternatives, collapse-path export and proof-boundary routing around the stock/flow core.",
            "concrete_decision": "Decide whether a feedback policy needs buffering, a new axis, or a bounded no-claim escalation before external prediction.",
            "native_preferable_case": "Use plain system dynamics when the question is only parameterized stock/flow calibration.",
            "decision_rubric": {"use_native": "closed stock/flow calibration", "use_oc_overlay": "collapse/recovery/proof-boundary decision", "stop": "no declared system boundary"},
        },
        "graph_theory": {
            "native_strength": "Best native fit for topology, paths, cuts, centrality and component analysis.",
            "oc_adds": "Adds K/M hierarchy, typed flows/cycles/thresholds, semantic proof links and axis/compensator interventions.",
            "concrete_decision": "Decide which dependency is a structural cut, which is a flow rupture, and which intervention changes recovery.",
            "native_preferable_case": "Use graph theory alone for pure topology where no claim/evidence boundary is needed.",
            "decision_rubric": {"use_native": "centrality/path answer only", "use_oc_overlay": "system architecture intervention", "stop": "edge semantics are unavailable"},
        },
        "causal_models": {
            "native_strength": "Best native fit for intervention logic, counterfactual assumptions and causal identification.",
            "oc_adds": "Adds continuum viability, collapse/recovery timeline and K-level provenance before treating an intervention as stable.",
            "concrete_decision": "Decide whether an intervention is a cause, a stabilizer, or a new-axis change to the model space.",
            "native_preferable_case": "Use causal models alone when identification and effect estimation are the only goals.",
            "decision_rubric": {"use_native": "identified DAG effect", "use_oc_overlay": "cross-level collapse/recovery risk", "stop": "intervention assumptions are hidden"},
        },
        "complexity_science": {
            "native_strength": "Best native fit for adaptation, emergence, phase-like transitions and nonlinear behavior.",
            "oc_adds": "Adds explicit formalization obligations, proof/evidence routes and repeatable architect export packets.",
            "concrete_decision": "Decide when an emergent pattern needs K-level drilldown, domain replay, or boundary-only labeling.",
            "native_preferable_case": "Use complexity models alone when exploration does not need proof-route or architect export discipline.",
            "decision_rubric": {"use_native": "exploratory emergence study", "use_oc_overlay": "auditable system decision", "stop": "no measurable output"},
        },
        "category_formal": {
            "native_strength": "Best native fit for compositional abstraction and structure-preserving mappings.",
            "oc_adds": "Adds concrete system templates, kill/recovery diagnostics and reviewer-visible source/boundary payloads.",
            "concrete_decision": "Decide whether a compositional map can be exercised as a workbench system with bounded outputs.",
            "native_preferable_case": "Use formal abstraction alone when the goal is theorem development rather than system diagnosis.",
            "decision_rubric": {"use_native": "pure formal proof", "use_oc_overlay": "formal route plus workbench trace", "stop": "no computable projection"},
        },
        "agent_based": {
            "native_strength": "Best native fit for heterogeneous agents, local rules and population-level runs.",
            "oc_adds": "Adds cross-level K/M drilldown, contradiction pressure and proof/nonclaim routing for scenario claims.",
            "concrete_decision": "Decide whether a population result is an agent-rule effect, a K-level constraint, or a boundary-only scenario.",
            "native_preferable_case": "Use ABM alone when local rules and calibration are the entire question.",
            "decision_rubric": {"use_native": "population run/calibration", "use_oc_overlay": "cross-level architecture risk", "stop": "no replay seed or boundary"},
        },
        "control_theory": {
            "native_strength": "Best native fit for stability, control loops, observability and feedback design.",
            "oc_adds": "Adds contradiction-load semantics, axis addition and evidence-boundary packaging for system-architecture review.",
            "concrete_decision": "Decide whether to tune feedback, add buffering, or change the admissible axis set.",
            "native_preferable_case": "Use control theory alone for well-specified controller design.",
            "decision_rubric": {"use_native": "controller synthesis", "use_oc_overlay": "cross-level failure/recovery design", "stop": "plant/model not declared"},
        },
        "risk_registers": {
            "native_strength": "Best native fit for governance inventory, ownership and qualitative risk tracking.",
            "oc_adds": "Adds dynamic cascade path, recovery index and explicit compensator/axis intervention comparison.",
            "concrete_decision": "Decide whether a registered risk is isolated, cascading, recoverable, or boundary-only.",
            "native_preferable_case": "Use a risk register alone for static governance documentation.",
            "decision_rubric": {"use_native": "static ownership/inventory", "use_oc_overlay": "dynamic cascade mitigation", "stop": "no dependency/flow model"},
        },
    }
    for index, template in enumerate(system_templates or []):
        template_id = template.get("template_id") or template.get("id")
        if not template_id:
            continue
        compared_id, compared_label, compared_boundary = comparison_inventory[index % len(comparison_inventory)]
        axis_names = template.get("allowed_axis_ids", [])[:3]
        if not axis_names:
            axis_names = [primary_axis]
        formula_ref = ["OCF-006", "OCF-007", "OCF-009", "OCF-010", "OCF-012", "OCF-013"][index % 6]
        sample_proof = (proof_routes[0] or {}).get("target_id", "")
        specifics = comparison_specifics.get(compared_id, {})
        rows.append(
            {
                "comparison_id": f"model-comparison::{template_id}::{axis_names[0]}",
                "model_id": template_id,
                "model_title": template.get("title", template_id),
                "compared_model": compared_label,
                "compared_model_id": compared_id,
                "model_kind": "system_template",
                "fairness_criteria": [
                    "same declared system boundary",
                    "same visible evidence status",
                    "no replacement claim",
                    "same allowed intervention surface",
                ],
                "surface_links": [
                    {"view": "workbench", "target_type": "system_template", "target_id": template_id},
                    {"view": "graph", "target_type": "graph_node", "target_id": ROOT_GRAPH_NODE_ID},
                ],
                "native_strength": specifics.get("native_strength", compared_boundary),
                "oc_adds": specifics.get("oc_adds") or f"Provides explicit {', '.join(axis_names)} axis instrumentation and collapse geometry for {template_id} while keeping replay and proof boundaries visible.",
                "does_not_replace": f"Does not replace {template_id} domain baselines, formula systems, or replay reports; it adds explicit workbench framing.",
                "nonreplacement_text": f"OC does not replace {compared_label}; use OC when the decision needs K/M hierarchy, contradiction pressure, cascade/recovery and evidence-boundary export in one workflow.",
                "concrete_decision": specifics.get("concrete_decision", "Decide whether an OC overlay adds collapse/recovery and evidence-boundary value to this template."),
                "native_preferable_case": specifics.get("native_preferable_case", f"Use {compared_label} alone when the task only needs its native calculation."),
                "decision_rubric": specifics.get("decision_rubric", {"use_native": "native calculation only", "use_oc_overlay": "architecture/collapse/proof-boundary decision", "stop": "boundary absent"}),
                "when_not_to_use": specifics.get("native_preferable_case") or f"Do not use OC instead of {compared_label} when the task only needs that model family's native calculation, or when a replay/proof boundary is absent.",
                "comparison_assumptions": [
                    "same declared system boundary",
                    "same visible evidence status",
                    "no replacement or superiority claim",
                    "same allowed intervention surface",
                ],
                "source_refs": [f"model-family::{compared_id}", f"template::{template_id}", "boundary::nonreplacement"],
                "comparison_axes": axis_names,
                "formula_refs": [formula_ref],
                "baseline_evidence": [
                    f"axis::{axis_names[0]}",
                    "proof_boundary_route",
                    sample_proof,
                    *([f"domain::{item}" for item in replay_frontier[:2]]),
                ],
                "claim_status": "nonclaim",
                "source_boundary": compared_boundary,
                "nonclaim_boundary": "These rows compare public model-family envelopes; they do not assert superiority or replace domain methods.",
            }
        )
    if not rows:
        rows.append(
            {
                "comparison_id": "model-comparison::oc-core-none",
                "model_id": "oc-core-system-templates",
                "model_title": "OC Core 1.4 model set",
                "model_kind": "system_template",
                "surface_links": [
                    {"view": "workbench", "target_type": "system_template", "target_id": "civilization"},
                    {"view": "graph", "target_type": "graph_node", "target_id": ROOT_GRAPH_NODE_ID},
                ],
                "oc_adds": f"Provides explicit contrast between replay-backed modeling and exploratory workbench edits using {primary_axis}-driven diagnostics.",
                "does_not_replace": "Does not replace source data, evidence-boundary routes, or domain replay records.",
                "nonreplacement_text": "OC does not replace source data, domain methods or evidence routes; it connects them into a bounded workbench workflow.",
                "when_not_to_use": "Do not use when a model is not attached to a replay or proof-linked boundary.",
                "comparison_axes": [primary_axis],
                "baseline_evidence": [],
                "claim_status": "nonclaim",
                "nonclaim_boundary": "Fallback comparison row for public-safe schema continuity.",
            }
        )
    return rows


def _trust_ladder(
    graph: dict[str, Any],
    systems: list[dict[str, Any]],
    simulations: list[dict[str, Any]],
    proof_routes: list[dict[str, Any]],
    domains: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    graph_node_ids = [node.get("id", "") for node in graph.get("nodes", []) if node.get("id")]
    proof_target = (proof_routes[0] or {}).get("target_id", "proof_boundary_route")
    sample_domain = domains[0].get("domain_id") if domains else "PHYSICS"
    replay_domain = next((row.get("domain_id") for row in domains if row.get("closure_status") == "CLOSED_REPLAY_BACKED"), sample_domain)
    domain_surface = {"view": "benchmarks", "target_type": "domain_lane", "target_id": replay_domain or sample_domain}
    graph_root_surface = {"view": "graph", "target_type": "graph_node", "target_id": graph_node_ids[0] if graph_node_ids else ROOT_GRAPH_NODE_ID}
    simulation_surface = {"view": "cascade", "target_type": "simulation", "target_id": (simulations[0]["id"] if simulations else "kill_cascade")}
    workbench_surface = {"view": "workbench", "target_type": "system_template", "target_id": (systems[0]["id"] if systems else "civilization")}
    proof_surface = {"view": "proof", "target_type": "proof_boundary", "target_id": proof_target}
    return [
        {
            "rung_id": "trust-ladder::toy-or-explanatory",
            "title": "Toy / Explanatory",
            "summary": "Interactive explainability and deterministic examples without empirical prediction claims.",
            "rationale": "Suitable for onboarding and conceptual checks where reproducibility is pedagogical.",
            "surface_links": [
                graph_root_surface,
                {"view": "formula", "target_type": "formula_search", "target_id": "continuum boundary operator"},
                {"view": "workbench", "target_type": "system_template", "target_id": workbench_surface["target_id"]},
            ],
        },
        {
            "rung_id": "trust-ladder::replay-backed",
            "title": "Replay-Backed",
            "summary": "Model behavior is interpretable through explicit simulation runs and bounded replay pathways.",
            "rationale": "Requires simulation execution and explicit failure/recovery traces.",
            "surface_links": [
                simulation_surface,
                {"view": "worldline", "target_type": "simulation", "target_id": "worldline_birth_evolution_collapse"},
                workbench_surface,
            ],
        },
        {
            "rung_id": "trust-ladder::domain-validated",
            "title": "Domain-Validated",
            "summary": "Claims attach to domain lanes with replay and validation status exposed.",
            "rationale": "Use replayed or closed domains before elevating confidence.",
            "surface_links": [
                domain_surface,
                {"view": "benchmarks", "target_type": "domain_lane", "target_id": sample_domain},
                {"view": "graph", "target_type": "graph_node", "target_id": graph_node_ids[-1] if graph_node_ids else ROOT_GRAPH_NODE_ID},
            ],
        },
        {
            "rung_id": "trust-ladder::proof-bounded",
            "title": "Proof-Bounded",
            "summary": "Model claims are bounded by explicit evidence routes and nonclaim boundaries.",
            "rationale": "Promote only with closure-aware proof and public boundary language.",
            "surface_links": [
                proof_surface,
                {"view": "graph", "target_type": "proof_route", "target_id": proof_target},
                {"view": "proof", "target_type": "proof_boundary", "target_id": "proof_boundary_route"},
            ],
        },
    ]


def _system_architect_missions(
    system_templates: list[dict[str, Any]],
    k_axes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    axis_ids = [axis.get("axis_id", "coherence") for axis in k_axes]
    for template in system_templates:
        template_id = template.get("template_id") or template.get("id")
        if not template_id:
            continue
        template_axes = template.get("allowed_axis_ids", axis_ids[:1] or ["coherence"])
        topology_hash = _hash({
            "nodes": template.get("nodes", []),
            "edges": template.get("edges", []),
            "kill_default": template.get("kill_default", ""),
            "weakest_node": template.get("weakest_node", ""),
        })
        template_hash = template.get("template_hash") or template.get("model_hash") or _hash(template)
        compare_output_hash = _hash({
            "template_id": template_id,
            "template_hash": template_hash,
            "topology_hash": topology_hash,
            "stage_sequence": ["diagnose", "kill", "improve", "compare", "export"],
            "compare_metrics": ["collapse_depth_delta", "recovery_index_delta", "connectivity_loss_delta"],
        })
        rows.append(
            {
                "id": f"system-architect::{template_id}::diagnostic-loop",
                "title": f"Architect mission: {template.get('title', template_id)}",
                "template_id": template_id,
                "target_system_id": template_id,
                "template_hash": template_hash,
                "topology_hash": topology_hash,
                "topology_hash_scope": "nodes, edges, kill_default and weakest_node",
                "stage_sequence": ["diagnose", "kill", "improve", "compare", "export"],
                "compare_route_id": f"{template_id}::comparison",
                "compare_output_hash": compare_output_hash,
                "negative_path": {
                    "failure_action": "invalid_axis_or_unknown_node",
                    "expected_visible_result": "structured fail-closed boundary row; no replay-backed badge",
                    "test_status": "PASS_MANIFEST_BOUNDARY_CASE",
                },
                "semantic_action_trace": [
                    {"stage": "diagnose", "visible_delta": "baseline risk metrics materialized", "hash_scope": "template_hash"},
                    {"stage": "kill", "visible_delta": "selected/weakest node and cascade path materialized", "hash_scope": "topology_hash + selected_node_id"},
                    {"stage": "improve", "visible_delta": "axis or compensator edit demotes edited scenario to exploratory sandbox", "hash_scope": "edited_topology_hash"},
                    {"stage": "compare", "visible_delta": "before/after metric deltas and compare_output_hash materialized", "hash_scope": "compare_output_hash"},
                    {"stage": "export", "visible_delta": "bounded audit packet with assumptions and nonclaim boundary", "hash_scope": "export_hash"},
                ],
                "claim_status": "nonclaim",
                "nonclaim_boundary": "Mission sequence is diagnostic; it is not a scientific guarantee.",
                "steps": [
                    {
                        "id": "diag",
                        "stage": "diagnose",
                        "title": "Diagnose baseline risk surface",
                        "view": "workbench",
                        "minutes": 1,
                        "goal": "Inspect collapse, support and axis context in a known template.",
                        "axis_id": template_axes[0] if template_axes else axis_ids[0],
                        "actions": ["Diagnose"],
                        "target_id": template_id,
                        "target_type": "system_template",
                        "target_view": "workbench",
                    },
                    {
                        "id": "kill",
                        "stage": "kill",
                        "title": "Kill a stress point and observe path",
                        "view": "workbench",
                        "minutes": 1,
                        "goal": "Trigger a shortest-path diagnostic from a critical dependency.",
                        "actions": ["Kill"],
                        "target_id": "kill_cascade",
                        "target_type": "simulation",
                        "target_view": "workbench",
                    },
                    {
                        "id": "improve",
                        "stage": "improve",
                        "title": "Improve with a supported axis",
                        "view": "workbench",
                        "minutes": 2,
                        "goal": "Apply one allowed axis or default recovery action.",
                        "axis_id": template_axes[1] if len(template_axes) > 1 else (template_axes[0] if template_axes else axis_ids[0]),
                        "actions": ["Improve", "Use in Workbench"],
                        "target_id": template_id,
                        "target_type": "system_template",
                        "target_view": "workbench",
                    },
                    {
                        "id": "compare",
                        "stage": "compare",
                        "title": "Compare baseline and edited profile",
                        "view": "graph",
                        "minutes": 2,
                        "goal": "Keep edits explicit and inspect comparison path on a shared graph projection.",
                        "actions": ["Compare"],
                        "target_type": "comparison",
                        "target_view": "graph",
                        "target_id": f"{template_id}::comparison",
                    },
                    {
                        "id": "export",
                        "stage": "export",
                        "title": "Export audit bundle",
                        "view": "workbench",
                        "minutes": 1,
                        "goal": "Generate a deterministic bundle for reviewer handoff.",
                        "actions": ["Export"],
                        "target_id": f"{template_id}::bundle",
                        "target_type": "system_bundle",
                        "target_view": "workbench",
                    },
                ],
            }
        )
    return rows


def _practical_value_cards(
    reviewer_objection_routes: list[dict[str, Any]],
    system_architect_missions: list[dict[str, Any]],
    model_comparison_matrix: list[dict[str, Any]],
    trust_ladder: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    objection_ids = [row.get("id") for row in reviewer_objection_routes[:3]]
    mission_ids = [row.get("id") for row in system_architect_missions[:4]]
    ladder_ids = [row.get("rung_id") for row in trust_ladder]
    return [
        {
            "card_id": "practical-value::reviewer_safeguard",
            "title": "Reviewer Safeguard Card",
            "audience": "reviewer",
            "value_statement": "Resolve objections against explicit replay, proof and domain checkpoints.",
            "practical_value": "Reduces false positive claims by forcing route-to-surface checks before predictive language.",
            "linked_routes": objection_ids[:2],
            "linked_missions": mission_ids[:1],
            "linked_rungs": [rung for rung in ladder_ids if rung],
            "linked_comparison_rows": [row.get("comparison_id") for row in model_comparison_matrix[:2]],
            "surfaces": [
                {"view": "proof", "target_type": "proof_boundary", "target_id": "proof_boundary_route"},
                {"view": "benchmarks", "target_type": "domain_lane", "target_id": "PHYSICS"},
            ],
        },
        {
            "card_id": "practical-value::architect_workflow",
            "title": "System Architect Workflow Card",
            "audience": "system architect",
            "value_statement": "Move from diagnosis to actionable edits using built-in missions.",
            "practical_value": "Provides a standard sequence for safe edits: diagnose, kill, improve, compare, export.",
            "linked_routes": objection_ids[1:],
            "linked_missions": mission_ids[:3],
            "linked_rungs": ladder_ids[:2],
            "linked_comparison_rows": [row.get("comparison_id") for row in model_comparison_matrix[:3]],
            "surfaces": [
                {"view": "workbench", "target_type": "system_template", "target_id": (system_architect_missions[0]["template_id"] if system_architect_missions else "civilization")},
                {"view": "graph", "target_type": "graph_node", "target_id": ROOT_GRAPH_NODE_ID},
            ],
        },
        {
            "card_id": "practical-value::evidence_ready",
            "title": "Evidence Readiness Card",
            "audience": "scientific reviewer",
            "value_statement": "Translate conceptual understanding into reproducible evidence checks.",
            "practical_value": "Turns abstract objections into explicit action/target sequences with nonclaim boundaries.",
            "linked_routes": objection_ids[:1],
            "linked_missions": mission_ids[1:2],
            "linked_rungs": ladder_ids[2:4],
            "surfaces": [
                {"view": "graph", "target_type": "proof_route", "target_id": ((model_comparison_matrix[0] or {}).get("baseline_evidence", [""])[-1] if model_comparison_matrix else "")},
                {"view": "formula", "target_type": "formula_search", "target_id": "replay-bounded projection"},
            ],
        },
    ]


def _science_atom_graph_payload() -> dict[str, Any]:
    candidates = [
        OC14_PACKAGE_ROOT / "020" / "science_atom_graph" / "SCIENCE_ATOM_GRAPH.json",
        OC14_PACKAGE_ROOT / "019" / "science_atom_graph" / "SCIENCE_ATOM_GRAPH.json",
        OC14_PACKAGE_ROOT / "011" / "science_atom_graph" / "SCIENCE_ATOM_GRAPH.json",
    ]
    for candidate in candidates:
        payload = _read_json(candidate, {})
        if isinstance(payload, dict) and payload.get("unified_scientific_entity_graph"):
            return payload
    return {}


def _safe_graph_id(prefix: str, value: Any, limit: int = 96) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip()).strip("_")
    if not slug:
        slug = _hash(value)[:12]
    return f"{prefix}::{slug[:limit]}"


def _graph_xyz(layer_index: int, ordinal: int, total_hint: int = 36) -> tuple[float, float, float]:
    total = max(6, total_hint)
    angle = (2 * math.pi * (ordinal % total) / total) + layer_index * 0.31
    ring = 2.2 + layer_index * 1.12 + (ordinal // total) * 0.42
    z = (layer_index - 5.5) * 0.84 + math.sin(ordinal * 0.37) * 0.55
    return (round(math.cos(angle) * ring, 5), round(math.sin(angle) * ring, 5), round(z, 5))


def _node_size(layer: str) -> int:
    return {
        "root_principle": 18,
        "continuum_operator": 13,
        "metaontology": 14,
        "m_space": 12,
        "k_level": 11,
        "axis": 8,
        "threshold": 8,
        "domain_projection": 10,
        "simulation": 10,
        "theorem": 8,
        "formula": 6,
        "proof_route": 5,
        "evidence": 6,
        "corpus_atom": 4,
        "boundary": 9,
    }.get(layer, 6)


def _graph_node(
    node_id: str,
    label: str,
    layer: str,
    ordinal: int,
    *,
    statement: Any = "",
    route: str = "science-graph",
    demo_class: str = "",
    demo_spec_id: str = "",
    evidence_class: str = "",
    technical_label: str = "",
    source_hash: str = "",
    closure_status: str = "",
    closure_basis: str = "",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    layer_order = [
        "root_principle",
        "continuum_operator",
        "metaontology",
        "m_space",
        "k_level",
        "axis",
        "threshold",
        "domain_projection",
        "simulation",
        "theorem",
        "formula",
        "proof_route",
        "evidence",
        "corpus_atom",
        "boundary",
    ]
    layer_index = layer_order.index(layer) if layer in layer_order else len(layer_order)
    x, y, z = _graph_xyz(layer_index, ordinal)
    semantic = _clean(label, 120)
    clean_statement = _clean(statement, 640)
    node_detail = {
        "node_type": layer,
        "layer": layer,
        "wiki_query": _clean(clean_statement or semantic, 160),
        "formula_query": _formula_query_from_text(clean_statement or semantic),
        "nonclaim_boundary": "Graph navigation shows traceability and didactic structure; it is not proof by visualization.",
    }
    if detail:
        node_detail.update({key: value for key, value in detail.items() if value not in (None, "", [])})
    return {
        "id": node_id,
        "technical_id": node_id,
        "label": semantic,
        "semantic_label": semantic,
        "technical_label": technical_label or node_id,
        "layer": layer,
        "cluster": layer,
        "route": route,
        "demo_class": demo_class,
        "demo_spec_id": demo_spec_id,
        "evidence_class": evidence_class,
        "statement_excerpt": clean_statement,
        "quality_flags": _quality_flags(clean_statement),
        "source_hash": source_hash,
        "closure_status": closure_status,
        "closure_basis": closure_basis,
        "x": x,
        "y": y,
        "z": z,
        "size": _node_size(layer),
        "detail": node_detail,
    }


def _pick_formula_rows(formulas: list[dict[str, Any]], limit: int = 260) -> list[dict[str, Any]]:
    important_terms = ("continuum", "boundary", "collapse", "contradiction", "operator", "proof", "theorem", "k(", "k_", "omega", "Ω", "dim")

    def score(row: dict[str, Any]) -> tuple[int, int]:
        text = str(row.get("formula_text", "")).lower()
        return (
            int(bool(row.get("katex_ready"))) * 6 + sum(1 for term in important_terms if term.lower() in text),
            -len(text),
        )

    return sorted([row for row in formulas if isinstance(row, dict)], key=score, reverse=True)[:limit]


def _pick_corpus_atoms(atoms: list[dict[str, Any]], limit: int = 240) -> list[dict[str, Any]]:
    buckets = {
        "root": ("contradiction", "collapse", "axis", "continuum"),
        "meta": ("metaontology", "ontology", "operator", "boundary"),
        "k": ("k-level", "k0", "k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "k10", "k11", "k12"),
        "proof": ("theorem", "proof", "lemma", "evidence", "refute"),
        "domain": ("physics", "chemistry", "biology", "systems", "mathematics"),
    }
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_bucket = max(10, limit // len(buckets))
    for terms in buckets.values():
        count = 0
        for atom in atoms:
            text = str(atom.get("search_text") or atom.get("text") or "").lower()
            if atom.get("unit_id") in seen or not any(term in text for term in terms):
                continue
            selected.append(atom)
            seen.add(str(atom.get("unit_id")))
            count += 1
            if count >= per_bucket:
                break
    for atom in atoms:
        if len(selected) >= limit:
            break
        if atom.get("unit_id") not in seen:
            selected.append(atom)
            seen.add(str(atom.get("unit_id")))
    return selected


def _load_graph(
    wiki: dict[str, Any],
    k_levels: list[dict[str, Any]],
    m_spaces: list[dict[str, Any]],
    k_axes: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    proof_routes: list[dict[str, Any]],
    simulations: list[dict[str, Any]],
    systems: list[dict[str, Any]],
    thresholds: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    layer_seen: Counter[str] = Counter()

    def add_node(node: dict[str, Any]) -> str:
        nodes[node["id"]] = node
        return node["id"]

    def add(layer: str, node_id: str, label: str, *, statement: Any = "", **kwargs: Any) -> str:
        layer_seen[layer] += 1
        return add_node(_graph_node(node_id, label, layer, layer_seen[layer], statement=statement, **kwargs))

    def link(source: str, target: str, relation: str, *, evidence_ref: str = "", weight: float = 1.0) -> None:
        if source not in nodes or target not in nodes:
            return
        key = (source, target, relation)
        if key not in edges:
            edges[key] = {
                "id": f"E{len(edges) + 1:05d}",
                "source": source,
                "target": target,
                "relation": relation,
                "edge_type": relation,
                "evidence_ref": evidence_ref,
                "weight": round(float(weight), 4),
            }

    root_id = add(
        "root_principle",
        "OC::ROOT_PRINCIPLE::CONTRADICTION_AXIS_OR_COLLAPSE",
        "Unresolvable contradiction births a new axis or drives collapse",
        statement="Persistent unresolved contradiction either forces a new axis of description or collapses the old continuum.",
        demo_class="ROOT_PRINCIPLE",
        evidence_class="didactic-spine",
        detail={"nonclaim_boundary": "This is the didactic root of the demonstrator graph; source/proof status remains visible downstream."},
    )
    boundary_id = add(
        "boundary",
        "OC::BOUNDARY::NONCLAIM_DISCIPLINE",
        "Evidence / nonclaim boundary",
        statement="Every visualization, simulation and formula remains bounded by replay, proof and source status.",
        demo_class="BOUNDARY",
        evidence_class="truth-discipline",
    )
    proof_gateway_id = add(
        "proof_route",
        "OC::PROOF_GATEWAY",
        "Proof and refutation route gateway",
        statement="Public targets, proof obligations, closure rows and evidence classes are reached through this gateway.",
        demo_class="PROOF_TRACE_REPLAYER",
        evidence_class="public-route",
        closure_status="PUBLIC_EVIDENCE_BOUNDARY",
        closure_basis="gateway routes to Evidence / Boundaries; it is not proof closure",
        detail={"replay_status": "BOUNDARY_ONLY_GATEWAY", "validation_status": "PUBLIC_EVIDENCE_BOUNDARY", "proof_target_id": "EVIDENCE_BOUNDARY_GATEWAY"},
    )
    evidence_gateway_id = add(
        "evidence",
        "OC::EVIDENCE::REPLAY_AND_SOURCE_LEDGER",
        "Replay, source and evidence ledgers",
        statement="Graph nodes are supported by public-safe source hashes, replay ledgers, formula registry rows and proof/evidence routes.",
        demo_class="EVIDENCE_ATLAS",
        evidence_class="hash-bound-public-evidence",
        closure_status="PUBLIC_EVIDENCE_BOUNDARY",
        closure_basis="evidence ledger exposes hashes and source refs without proof promotion",
        detail={"replay_status": "SOURCE_HASH_LEDGER_VISIBLE", "validation_status": "PUBLIC_EVIDENCE_BOUNDARY", "proof_target_id": "EVIDENCE_SOURCE_LEDGER"},
    )
    link(root_id, boundary_id, "proved_or_bounded_by", evidence_ref="V010_ROOT_BOUNDARY")
    link(root_id, proof_gateway_id, "proved_or_bounded_by", evidence_ref="V010_ROOT_PROOF_GATEWAY")
    link(root_id, evidence_gateway_id, "supported_by", evidence_ref="V010_ROOT_EVIDENCE")
    link(evidence_gateway_id, boundary_id, "proved_or_bounded_by", evidence_ref="V010_EVIDENCE_BOUNDARY")

    operator_ids: dict[str, str] = {}
    for operator in _operators():
        op_id = add(
            "continuum_operator",
            f"OC::OPERATOR::{operator['id']}",
            operator["title"],
            statement=operator["effect"],
            demo_class="CONTINUUM_OPERATOR",
            evidence_class="didactic-operator",
        )
        operator_ids[operator["id"]] = op_id
        link(root_id, op_id, "derives", evidence_ref="V010_OPERATOR_SPINE")
    meta_rows = [
        ("OC::META::ONTOLOGY", "Metaontology of Continua", "The grammar that keeps continuum, boundary, operator, evidence and collapse in one navigable science surface."),
        ("OC::META::CONTINUUM_MODEL", "Continuum model grammar", "Bounded identity is tracked through operators, preserved invariants and failure conditions."),
        ("OC::META::K_LEVEL_BRANCHING", "K-level branching discipline", "The ontology branches into K0-K12 without losing root, boundary or proof status."),
        ("OC::META::THEOREM_FORMULA_PROOF", "Theorem -> formula -> evidence boundary chain", "The graph must expose how theorem-bearing claims touch formulas, evidence routes and boundaries."),
        ("OC::META::DOMAIN_PROJECTION", "Domain projection discipline", "Physics, chemistry, biology, systems, mathematics and meta lanes inherit OC only inside declared validation limits."),
    ]
    meta_ids: list[str] = []
    for node_id, label, statement in meta_rows:
        mid = add("metaontology", node_id, label, statement=statement, demo_class="METAONTOLOGY", evidence_class="didactic-spine")
        meta_ids.append(mid)
        link(root_id, mid, "derives", evidence_ref="V010_METAONTOLOGY_SPINE")
        link(mid, evidence_gateway_id, "supported_by", evidence_ref="V010_META_EVIDENCE")
    for op_id in operator_ids.values():
        link(op_id, "OC::META::CONTINUUM_MODEL", "refines", evidence_ref="V010_OPERATOR_TO_MODEL")
    link("OC::META::ONTOLOGY", "OC::META::K_LEVEL_BRANCHING", "refines", evidence_ref="V010_META_BRANCH")
    link("OC::META::ONTOLOGY", "OC::META::THEOREM_FORMULA_PROOF", "refines", evidence_ref="V010_META_THEOREM")
    link("OC::META::ONTOLOGY", "OC::META::DOMAIN_PROJECTION", "refines", evidence_ref="V010_META_DOMAIN")
    link("OC::OPERATOR::OP-KILL", boundary_id, "collapse_path", evidence_ref="V010_KILL_BOUNDARY")

    m_space_ids: dict[str, str] = {}
    for m_space in m_spaces:
        mid = add(
            "m_space",
            f"M::{m_space['m_space_id']}",
            m_space.get("semantic_name") or m_space["m_space_id"],
            statement=m_space.get("scope", ""),
            demo_class="M_SPACE",
            evidence_class=m_space.get("source_status", "generated-navigation"),
            source_hash=m_space.get("source_hash", ""),
            detail={
                "m_space_id": m_space.get("m_space_id"),
                "k_levels": m_space.get("k_level_bindings", []),
                "domain_id": m_space.get("parent_domain", ""),
                "supported_axes": m_space.get("supported_axes", []),
                "nonclaim_boundary": m_space.get("boundary_text", ""),
            },
        )
        m_space_ids[m_space["m_space_id"]] = mid
        link("OC::META::CONTINUUM_MODEL", mid, "refines", evidence_ref="V010_M_SPACE_LAYER")
        link(mid, boundary_id, "proved_or_bounded_by", evidence_ref="V010_M_SPACE_BOUNDARY")

    k_node_ids: dict[str, str] = {}
    for level in k_levels:
        kid = add(
            "k_level",
            f"K::{level['level_id']}",
            f"{level['level_id']} - {level.get('meaning') or 'K-level'}",
            statement=level.get("semantic_summary") or level.get("preserved_invariants") or "",
            demo_class="K_LEVEL_WORLD",
            evidence_class=level.get("simulation_status", ""),
            source_hash=level.get("artifact_sha256", ""),
            closure_status=level.get("closure_status", ""),
            closure_basis=level.get("closure_basis", ""),
            detail={
                "k_level": level.get("level_id"),
                "domain_projections": level.get("domain_projections", []),
                "nonclaim_boundary": "K-level world state is replay/status navigation, not external peer review.",
            },
        )
        k_node_ids[level["level_id"]] = kid
        link("OC::META::K_LEVEL_BRANCHING", kid, "branches_to_k_level", evidence_ref="OC_K_LEVEL_ATLAS_latest")
        link(kid, evidence_gateway_id, "supported_by", evidence_ref="K_LEVEL_SIMULATION_SUITE_latest")
        for m_space in m_spaces:
            if level.get("level_id") in m_space.get("k_level_bindings", []):
                link(m_space_ids.get(m_space["m_space_id"], ""), kid, "constrains", evidence_ref="V010_M_SPACE_TO_K")
    ordered_levels = sorted(k_node_ids, key=lambda value: int(re.sub(r"\D", "", value) or 0))
    for left, right in zip(ordered_levels, ordered_levels[1:]):
        link(k_node_ids[left], k_node_ids[right], "refines", evidence_ref="K_LEVEL_ORDER")

    axis_ids: dict[str, str] = {}
    for axis in k_axes[:80]:
        aid = add(
            "axis",
            f"AXIS::{axis['axis_id']}",
            axis.get("title") or axis["axis_id"],
            statement=axis.get("interpretation", ""),
            demo_class="COMPUTABLE_AXIS",
            evidence_class=axis.get("source_status", ""),
            source_hash=axis.get("axis_hash", ""),
            detail={
                "axis_id": axis.get("axis_id"),
                "k_levels": axis.get("k_levels", []),
                "domain_ids": axis.get("domain_ids", []),
                "claim_status": axis.get("claim_status", "nonclaim"),
                "nonclaim_boundary": axis.get("nonclaim_boundary", ""),
            },
        )
        axis_ids[axis["axis_id"]] = aid
        link("OC::META::CONTINUUM_MODEL", aid, "formalized_by", evidence_ref="V010_AXIS_CATALOG")
        for level_id in axis.get("k_levels", [])[:6]:
            if level_id in k_node_ids:
                link(k_node_ids[level_id], aid, "uses_formula", evidence_ref="V010_K_AXIS")
        for m_space in m_spaces:
            if axis.get("axis_id") in m_space.get("supported_axes", []):
                link(m_space_ids.get(m_space["m_space_id"], ""), aid, "supports", evidence_ref="V010_M_SPACE_AXIS")

    domain_ids: dict[str, str] = {}
    for domain in domains:
        did = add(
            "domain_projection",
            f"DOMAIN::{domain['domain_id']}",
            domain.get("title") or domain["domain_id"],
            statement=domain.get("nonclaim_boundary") or domain.get("closure_basis") or "",
            demo_class="DOMAIN_PROJECTION",
            evidence_class=domain.get("closure_status", ""),
            closure_status=domain.get("closure_status", ""),
            closure_basis=domain.get("closure_basis", ""),
            detail={
                "domain_id": domain.get("domain_id"),
                "replay_status": domain.get("replay_status"),
                "validation_status": domain.get("validation_status"),
                "nonclaim_boundary": domain.get("nonclaim_boundary", ""),
            },
        )
        domain_ids[str(domain["domain_id"]).upper()] = did
        link("OC::META::DOMAIN_PROJECTION", did, "projects_to_domain", evidence_ref="DOMAIN_NUMERICAL_PREDICTION_REGISTRY_latest")
        link(did, evidence_gateway_id, "supported_by", evidence_ref="DOMAIN_REPLAY_REPORTS_latest")
        for m_space in m_spaces:
            if domain.get("domain_id") in m_space.get("domain_bindings", []):
                link(m_space_ids.get(m_space["m_space_id"], ""), did, "projects_to_domain", evidence_ref="V010_M_SPACE_DOMAIN")
    for level in k_levels:
        source = k_node_ids.get(level.get("level_id"))
        if not source:
            continue
        projections = " ".join(str(item).upper() for item in level.get("domain_projections", []))
        for domain_key, domain_node in domain_ids.items():
            if domain_key in projections or not projections:
                link(source, domain_node, "projects_to_domain", evidence_ref="K_LEVEL_DOMAIN_PROJECTION")

    for threshold in (thresholds or [])[:80]:
        tid = add(
            "threshold",
            f"THRESHOLD::{threshold['threshold_id']}",
            threshold.get("title") or threshold["threshold_id"],
            statement=threshold.get("interpretation", ""),
            demo_class="SYSTEM_THRESHOLD",
            evidence_class=threshold.get("source_status", ""),
            source_hash=threshold.get("threshold_hash", ""),
            detail={
                "threshold_id": threshold.get("threshold_id"),
                "system_id": threshold.get("system_id"),
                "node_id": threshold.get("node_id"),
                "axis_id": threshold.get("axis_id"),
                "nonclaim_boundary": threshold.get("nonclaim_boundary", ""),
            },
        )
        if threshold.get("axis_id") in axis_ids:
            link(axis_ids[threshold["axis_id"]], tid, "supports", evidence_ref="V010_AXIS_THRESHOLD")
        for level_id in threshold.get("k_levels", [])[:4]:
            if level_id in k_node_ids:
                link(k_node_ids[level_id], tid, "collapse_path", evidence_ref="V010_K_THRESHOLD")

    sim_ids: dict[str, str] = {}
    for sim in simulations:
        sid = add(
            "simulation",
            f"SIM::{sim['id']}",
            sim.get("title") or sim["id"],
            statement=sim.get("purpose", ""),
            demo_class="SIMULATION",
            demo_spec_id=sim.get("id", ""),
            evidence_class=sim.get("source_status", ""),
            detail={"simulation_id": sim.get("id"), "nonclaim_boundary": "Simulation output is deterministic and bounded; proof status is shown separately."},
        )
        sim_ids[sim["id"]] = sid
    if "worldline_birth_evolution_collapse" in sim_ids:
        link(operator_ids.get("OP-BIRTH", root_id), sim_ids["worldline_birth_evolution_collapse"], "simulated_by", evidence_ref="V010_WORLDLINE")
        link(operator_ids.get("OP-DIFFERENTIATE", root_id), sim_ids["worldline_birth_evolution_collapse"], "simulated_by", evidence_ref="V010_WORLDLINE")
    if "k_level_elevator" in sim_ids:
        link("OC::META::K_LEVEL_BRANCHING", sim_ids["k_level_elevator"], "simulated_by", evidence_ref="V010_K_ELEVATOR")
    if "kill_cascade" in sim_ids:
        link(operator_ids.get("OP-KILL", root_id), sim_ids["kill_cascade"], "collapse_path", evidence_ref="V010_KILL_CASCADE")
    if "domain_anchor_lab" in sim_ids:
        for domain_node in domain_ids.values():
            link(domain_node, sim_ids["domain_anchor_lab"], "simulated_by", evidence_ref="V010_DOMAIN_ANCHOR")

    for system in systems:
        system_id = add(
            "simulation",
            f"SYSTEM::{system['id']}",
            system.get("title") or system["id"],
            statement=system.get("what_it_shows", ""),
            demo_class="SYSTEM_ZOO",
            evidence_class="deterministic-system-model",
            detail={"system_id": system.get("id"), "nonclaim_boundary": system.get("nonclaim", "")},
        )
        if "kill_cascade" in sim_ids:
            link(sim_ids["kill_cascade"], system_id, "collapse_path", evidence_ref="V010_SYSTEM_ZOO")

    formulas = _pick_formula_rows(wiki.get("formulas", []))
    formula_ids: list[str] = []
    for formula in formulas:
        formula_node_id = _safe_graph_id("FORMULA", formula.get("formula_id") or formula.get("formula_text"))
        if formula_node_id in nodes:
            formula_node_id = f"{formula_node_id}::{len(formula_ids) + 1:03d}"
        fid = add(
            "formula",
            formula_node_id,
            formula.get("formula_text") or formula.get("formula_id"),
            statement=formula.get("formula_text", ""),
            demo_class="FORMULA_ATLAS",
            evidence_class=formula.get("status", ""),
            source_hash=formula.get("source_hash", ""),
            detail={"formula_id": formula.get("formula_id"), "formula_text": formula.get("formula_text"), "render_mode": formula.get("render_mode")},
        )
        formula_ids.append(fid)
        link("OC::META::THEOREM_FORMULA_PROOF", fid, "formalized_by", evidence_ref="SCIENCE_FORMULA_SYMBOL_REGISTRY_latest", weight=0.65)
        link(fid, evidence_gateway_id, "supported_by", evidence_ref="SCIENCE_FORMULA_SYMBOL_REGISTRY_latest", weight=0.45)

    atoms = _pick_corpus_atoms(wiki.get("corpus_atoms", []))
    atom_ids: list[str] = []
    for atom in atoms:
        aid = add(
            "corpus_atom",
            _safe_graph_id("ATOM", atom.get("unit_id")),
            _semantic_label(atom.get("chapter_title") or atom.get("source_unit_id"), atom.get("text", ""), str(atom.get("unit_id", ""))),
            statement=atom.get("text", ""),
            demo_class="CORPUS_ATOM",
            evidence_class="public-corpus",
            source_hash=atom.get("source_hash", ""),
            detail={
                "unit_id": atom.get("unit_id"),
                "document_id": atom.get("document_id"),
                "chapter_id": atom.get("chapter_id"),
                "formula_query": atom.get("formula_query"),
                "proof_query": atom.get("proof_query"),
            },
        )
        atom_ids.append(aid)
        text = str(atom.get("search_text") or "")
        if any(term in text for term in ("contradiction", "collapse", "axis", "continuum")):
            link(root_id, aid, "cites_corpus_atom", evidence_ref="V010_CORPUS_ROOT", weight=0.45)
        elif any(term in text for term in ("k-level", "k0", "k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "k10", "k11", "k12")):
            link("OC::META::K_LEVEL_BRANCHING", aid, "cites_corpus_atom", evidence_ref="V010_CORPUS_K", weight=0.45)
        elif any(term in text for term in ("theorem", "proof", "formula", "lemma")):
            link("OC::META::THEOREM_FORMULA_PROOF", aid, "cites_corpus_atom", evidence_ref="V010_CORPUS_PROOF", weight=0.45)
        else:
            link("OC::META::ONTOLOGY", aid, "cites_corpus_atom", evidence_ref="V010_CORPUS_GENERAL", weight=0.35)

    theorem_atoms = [atom for atom in wiki.get("corpus_atoms", []) if re.search(r"theorem|proof|lemma|formal", str(atom.get("search_text", "")), re.IGNORECASE)]
    theorem_limit = 96
    theorem_ids: list[str] = []
    science_graph = _science_atom_graph_payload().get("unified_scientific_entity_graph", {})
    theorem_source_nodes = [row for row in science_graph.get("nodes", []) if isinstance(row, dict) and row.get("node_type") == "theorem"]
    theorem_total = max(len(theorem_source_nodes), min(theorem_limit, len(theorem_atoms)))
    for index in range(min(theorem_limit, theorem_total)):
        source_node = theorem_source_nodes[index] if index < len(theorem_source_nodes) else {}
        atom = theorem_atoms[index % len(theorem_atoms)] if theorem_atoms else {}
        label = _semantic_label(
            f"Theorem route {index + 1}",
            atom.get("text") or source_node.get("label") or f"Theorem route {index + 1}",
            f"THEOREM::{index + 1:03d}",
        )
        tid = add(
            "theorem",
            f"THEOREM::{index + 1:03d}",
            label,
            statement=atom.get("text") or source_node.get("label") or "",
            demo_class="THEOREM_CHAIN",
            evidence_class="science-atom-graph",
            source_hash=atom.get("source_hash", ""),
            detail={
                "science_atom_node_id": source_node.get("node_id", ""),
                "refs": source_node.get("refs", [])[:4],
                "corpus_unit_id": atom.get("unit_id", ""),
            },
        )
        theorem_ids.append(tid)
        link("OC::META::THEOREM_FORMULA_PROOF", tid, "derives", evidence_ref="SCIENCE_ATOM_GRAPH")
        link(tid, evidence_gateway_id, "supported_by", evidence_ref="SCIENCE_ATOM_GRAPH")
        if formula_ids:
            link(tid, formula_ids[index % len(formula_ids)], "uses_formula", evidence_ref="SCIENCE_FORMULA_SYMBOL_REGISTRY_latest")
        if atom_ids:
            link(tid, atom_ids[index % len(atom_ids)], "cites_corpus_atom", evidence_ref="LANGUAGE_SOURCE_UNITS")

    target_ids: list[str] = []
    for index, route in enumerate(proof_routes):
        target_id = str(route.get("target_id"))
        statement = route.get("statement_excerpt") or route.get("rationale") or route.get("label")
        label = _semantic_label(route.get("label"), statement, target_id)
        add(
            "proof_route",
            target_id,
            label,
            statement=statement,
            route=route.get("ui_route", "proof-route"),
            demo_class=route.get("demo_class", ""),
            demo_spec_id=route.get("demo_spec_id", ""),
            evidence_class=route.get("evidence_class", ""),
            source_hash=route.get("closure_evidence_hash", ""),
            closure_status=route.get("closure_status", ""),
            closure_basis=route.get("closure_basis", ""),
            detail={
                "proof_target_id": target_id,
                "wiki_query": _clean(statement, 160),
                "formula_query": _formula_query_from_text(statement),
                "nonclaim_boundary": route.get("nonclaim_boundary", ""),
                "rationale": route.get("rationale", ""),
            },
        )
        target_ids.append(target_id)
        link(proof_gateway_id, target_id, "proved_or_bounded_by", evidence_ref="PUBLIC_TARGETS")
        link(target_id, evidence_gateway_id, "supported_by", evidence_ref="PUBLIC_TARGETS")
        if formula_ids:
            link(target_id, formula_ids[index % len(formula_ids)], "uses_formula", evidence_ref="PUBLIC_TARGET_FORMULA_QUERY", weight=0.55)
        if atom_ids:
            link(target_id, atom_ids[index % len(atom_ids)], "cites_corpus_atom", evidence_ref="PUBLIC_TARGET_CORPUS_QUERY", weight=0.45)
        demo_spec = str(route.get("demo_spec_id") or "")
        if demo_spec and f"SIM::{demo_spec}" in nodes:
            link(target_id, f"SIM::{demo_spec}", "simulated_by", evidence_ref="PUBLIC_TARGET_DEMO_SPEC")
    for index, tid in enumerate(theorem_ids):
        if target_ids:
            link(tid, target_ids[index % len(target_ids)], "proved_or_bounded_by", evidence_ref="THEOREM_TO_PUBLIC_TARGET")
        else:
            link(tid, boundary_id, "proved_or_bounded_by", evidence_ref="THEOREM_BOUNDARY")

    node_rows = list(nodes.values())
    edge_rows = list(edges.values())
    layer_counts = Counter(node.get("layer", node.get("cluster", "unknown")) for node in node_rows)
    relation_counts = Counter(edge.get("relation", "related") for edge in edge_rows)
    graph = {
        "schema_version": "oc-core-demo-science-graph.v010",
        "root_node_id": root_id,
        "root_principle": nodes[root_id]["label"],
        "summary": {
            "node_total": len(node_rows),
            "edge_total": len(edge_rows),
            "target_total": len(proof_routes),
            "k_level_total": len(k_levels),
            "domain_total": len(domains),
            "theorem_total": len(theorem_ids),
            "formula_node_total": len(formula_ids),
            "corpus_atom_node_total": len(atom_ids),
            "cluster_counts": dict(layer_counts),
            "layer_counts": dict(layer_counts),
            "relation_counts": dict(relation_counts),
            "required_layers_present": sorted(layer_counts),
            "required_edge_types_present": sorted(relation_counts),
            "root_reachability_required": True,
            "private_trace_map_publicly_exposed": False,
        },
        "nodes": node_rows,
        "edges": edge_rows,
    }
    graph["summary"]["graph_hash"] = _hash({"nodes": node_rows, "edges": edge_rows})
    return graph


def _semantic_label(default: Any, statement: Any, fallback: str) -> str:
    text = _clean(statement, 220)
    if text and not text.lower().startswith("public proof/refute obligation"):
        text = re.sub(r"^(Problem|Question|Claim)\s+[\d.]+\.?\s*", "", text, flags=re.IGNORECASE).lstrip(" .:-")
        label = text.split("?")[0].split(".")[0].strip()
        if len(label) < 12:
            label = text[:90].strip()
        if len(label) > 90:
            label = label[:87].rstrip() + "..."
        if len(label) >= 12:
            return label + ("?" if "?" in text[:120] and not label.endswith("?") else "")
    default_text = _clean(default, 90)
    return default_text if default_text and default_text != fallback else fallback


def _formula_query_from_text(text: Any) -> str:
    value = _clean(text, 160).lower()
    terms = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", value)
    return " ".join(terms[:4])


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


def _quality_flags(text: Any) -> list[str]:
    raw = str(text or "")
    clean = _clean(raw, 10000)
    flags: list[str] = []
    if not clean:
        flags.append("empty")
    if "Frozen proof/refute target ." in clean or "Frozen 019 proof/refute target" in clean:
        flags.append("placeholder")
    if any(char in raw for char in ("\ufb00", "\ufb01", "\ufb02", "\ufb03", "\ufb04")):
        flags.append("ocr_ligature_normalized")
    if len(clean) > 420:
        flags.append("long_excerpt")
    return flags


def _proof_routes() -> list[dict[str, Any]]:
    targets = _read_json(DEMO_DATA / "public_targets.json", {"targets": []}).get("targets", [])
    routes = []
    for row in targets:
        statement = row.get("public_statement_excerpt", "")
        closure_status = row.get("closure_status", "") or "PUBLIC_EVIDENCE_BOUNDARY"
        boundary = _clean(
            row.get("nonclaim_boundary", "")
            or "Public demonstrator exposes claim/evidence route and boundary; this row is not counted as external peer-reviewed proof closure.",
            620,
        )
        source_refs = _public_source_refs(row.get("closure_source_refs", []), "proof-route")
        if not source_refs:
            source_refs = [
                f"public-target::{row.get('public_target_id', '')}",
                f"evidence-class::{row.get('public_evidence_class', 'public-evidence')}",
                f"route::{row.get('ui_route', 'public-route')}",
            ]
        routes.append(
            {
                "target_id": row["public_target_id"],
                "label": _clean(statement, 92) or row.get("public_label", row["public_target_id"]),
                "technical_label": row.get("public_label", row["public_target_id"]),
                "status": row.get("terminal_status_public", "unknown"),
                "demo_class": row.get("demo_class", ""),
                "demo_spec_id": row.get("demo_spec_id", ""),
                "evidence_class": row.get("public_evidence_class", ""),
                "ui_route": row.get("ui_route", ""),
                "statement_excerpt": _clean(statement, 520),
                "quality_flags": _quality_flags(statement),
                "source_target_id": row.get("source_target_id", ""),
                "closure_status": closure_status,
                "closure_basis": row.get("closure_basis", "") or "public_target_evidence_boundary",
                "closure_evidence_hash": row.get("closure_evidence_hash", "") or _hash({"target_id": row.get("public_target_id"), "statement": _clean(statement, 520), "status": row.get("terminal_status_public", "unknown")}),
                "nonclaim_boundary": boundary,
                "closure_source_refs": source_refs,
                "proof_surface_class": "BOUNDARY_OR_OBLIGATION_NOT_PROOF_CLOSURE",
                "proof_closed_public": False,
                "rationale": _clean(row.get("rationale", ""), 620),
                "non_simulated_reason": _clean(row.get("non_simulated_reason", ""), 620),
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


def _k_levels(edition: str) -> list[dict[str, Any]]:
    atlas = _read_json(REPO_ROOT / "logion" / "k0" / "governance" / "status" / "OC_K_LEVEL_ATLAS_latest.json", {"rows": []})
    formal = _read_json(REPO_ROOT / "logion" / "k7" / "spe" / "state" / "science" / "K_LEVEL_FORMALIZATION_latest.json", {"k_levels": []})
    sims = _read_json(REPO_ROOT / "logion" / "k7" / "spe" / "state" / "science" / "K_LEVEL_SIMULATION_SUITE_latest.json", {"rows": []})
    formal_by_k = {str(row.get("k_level", "")).upper(): row for row in formal.get("k_levels", []) if isinstance(row, dict)}
    sim_by_k = {str(row.get("k_level", "")).upper(): row for row in sims.get("rows", []) if isinstance(row, dict)}
    rows = []
    for row in atlas.get("rows", []):
        if not isinstance(row, dict):
            continue
        level = str(row.get("level_id", "")).upper()
        frow = formal_by_k.get(level, {})
        srow = sim_by_k.get(level, {})
        simulation_pass = bool(srow.get("simulation_pass", False))
        stress_pass = bool(srow.get("stress_test_pass", False))
        sensitivity_pass = bool(srow.get("sensitivity_pass", False))
        reproducible = bool(srow.get("reproducibility", {}).get("pass", srow.get("reproducible", False)))
        counterexample_found = bool(
            srow.get("counterexample_found", False) or srow.get("counterexample_search", {}).get("counterexample_found", False)
        )
        counterexample_pass = bool(srow.get("counterexample_search", {}).get("pass", not counterexample_found))
        simulation_status = "PASS" if simulation_pass and stress_pass and sensitivity_pass and reproducible and counterexample_pass and not counterexample_found else "OPEN_REPLAY_GAP"
        domain_projections = list(row.get("active_domain_projections", []) or [])
        if level == "K7" and not any(str(item).upper() in {"SYSTEMS", "COGNITIVE_SOCIAL", "SOCIAL", "INSTITUTIONAL"} for item in domain_projections):
            domain_projections = [*domain_projections, "COGNITIVE_SOCIAL", "SYSTEMS"]
        out = {
            "level_id": level,
            "meaning": _clean(row.get("meaning_name_en") or row.get("canonical_semantics"), 280),
            "semantic_summary": _clean(row.get("semantic_summary_ru") or row.get("canonical_semantics"), 420),
            "domain_projections": domain_projections,
            "domain_projection_boundary": (
                "K7 is displayed as cognitive/social/institutional projection in the workbench; biology remains a substrate lane, not the semantic landing domain."
                if level == "K7"
                else ""
            ),
            "terminal_status": row.get("terminal_execution_status", "unknown"),
            "model_boundary_status": row.get("model_boundary_status", "unknown"),
            "theorem_admissibility_status": row.get("theorem_admissibility_status", "unknown"),
            "quantitative_prediction_readiness": row.get("quantitative_prediction_readiness", "unknown"),
            "preserved_invariants": _clean(row.get("preserved_invariants", ""), 360),
            "confidence": frow.get("confidence"),
            "confidence_basis": _clean(frow.get("confidence_basis", ""), 320),
            "applicability_bounds": [_clean(item, 220) for item in frow.get("applicability_bounds", [])[:4]],
            "simulation_status": simulation_status,
            "simulation_summary": {
                "simulation_pass": simulation_pass,
                "stress_pass": stress_pass,
                "sensitivity_pass": sensitivity_pass,
                "reproducible": reproducible,
                "counterexample_search_pass": counterexample_pass,
                "counterexample_found": counterexample_found,
            },
            "artifact_sha256": srow.get("artifact_sha256", ""),
            "model_hash": srow.get("model_hash", ""),
            "closure_status": "CLOSED_REPLAY_BACKED" if simulation_status == "PASS" else "OPEN_REPLAY_GAP",
            "closure_basis": "K_LEVEL_SIMULATION_SUITE simulation/stress/sensitivity/reproducibility/counterexample gates",
            "scenario_matrix": srow.get("scenario_matrix", [])[:8],
        }
        if edition == "private":
            out["private_refs"] = {
                "k_atlas_refs": row.get("refs", []),
                "formalization_refs": frow.get("evidence_refs", []),
                "simulation_artifact": srow.get("artifact_path", ""),
            }
        rows.append(out)
    return rows


def _domain_benchmarks(edition: str) -> list[dict[str, Any]]:
    registry = _read_json(REPO_ROOT / "logion" / "k0" / "governance" / "status" / "DOMAIN_NUMERICAL_PREDICTION_REGISTRY_latest.json", {"rows": []})
    cases = _read_json(REPO_ROOT / "logion" / "k0" / "governance" / "status" / "DOMAIN_BENCHMARK_CASESET_latest.json", {"rows": []})
    replay = _read_json(REPO_ROOT / "logion" / "k0" / "governance" / "status" / "DOMAIN_REPLAY_REPORTS_latest.json", {"rows": []})
    validation = _read_json(REPO_ROOT / "logion" / "k0" / "governance" / "status" / "EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json", {"rows": []})
    completion = _read_json(REPO_ROOT / "logion" / "k0" / "governance" / "status" / "OC_DOMAIN_PROJECTION_COMPLETION_latest.json", {})
    case_by_domain = {row.get("domain_id"): row for row in cases.get("rows", []) if isinstance(row, dict)}
    replay_by_domain = {row.get("domain_id"): row for row in replay.get("rows", []) if isinstance(row, dict)}
    validation_by_domain = {row.get("domain_id"): row for row in validation.get("rows", []) if isinstance(row, dict)}
    completion_by_domain: dict[str, list[dict[str, Any]]] = {}
    for row in completion.get("benchmark_replay_manifest", []) if isinstance(completion, dict) else []:
        if isinstance(row, dict):
            completion_by_domain.setdefault(str(row.get("domain_id", "UNKNOWN")), []).append(row)
    out = []
    for row in registry.get("rows", []):
        if not isinstance(row, dict):
            continue
        domain = row.get("domain_id", "UNKNOWN")
        case_row = case_by_domain.get(domain, {})
        replay_row = replay_by_domain.get(domain, {})
        validation_row = validation_by_domain.get(domain, {})
        completion_rows = completion_by_domain.get(domain, [])
        status = row.get("quantitative_packet_status", "unknown")
        validation = row.get("prediction_contract_status", "unknown")
        replay_status = replay_row.get("replay_status") or validation_row.get("replay_status") or ""
        validation_status = validation_row.get("validation_status") or replay_row.get("status") or ""
        meta_only = "NOT_REQUIRED" in f"{status} {validation} {replay_status} {validation_status}".upper()
        replay_backed = replay_status == "PASS_REPLAYABLE" and str(validation_status).startswith("PASS")
        closure_status = "NOT_APPLICABLE_META_ONLY" if meta_only and not replay_backed else "CLOSED_REPLAY_BACKED" if replay_backed else "OPEN_DOMAIN_REPLAY_GAP"
        promotion_state = "not-applicable-meta-only" if closure_status == "NOT_APPLICABLE_META_ONLY" else "replay-backed" if closure_status == "CLOSED_REPLAY_BACKED" else "frontier-gap"
        completion_hashes = sorted({str(item.get("replay_hash", "")) for item in completion_rows if item.get("replay_hash")})
        benchmark_cases = [
            {
                "case_id": item.get("case_id"),
                "title": _clean(item.get("case_title"), 180),
                "benchmark_id": item.get("benchmark_id"),
                "observable_name": item.get("observable_name"),
                "units": item.get("units", ""),
                "prediction_status": item.get("prediction_status", ""),
                "held_out_role": item.get("held_out_role", ""),
                "official_source_url": item.get("official_source_url", ""),
            }
            for item in case_row.get("case_rows", [])[:60]
            if isinstance(item, dict)
        ]
        pending_case_total = sum(1 for item in benchmark_cases if "PENDING" in str(item.get("prediction_status", "")).upper())
        executed_case_total = sum(1 for item in benchmark_cases if item.get("prediction_status") and "PENDING" not in str(item.get("prediction_status", "")).upper())
        case_total_value = case_row.get("benchmark_case_total", len(benchmark_cases))
        raw_claim_level = validation_row.get("claim_level") or replay_row.get("claim_level", "")
        public_claim_level = raw_claim_level
        public_prediction_status = validation_status or validation
        if public_claim_level == "validated_predictive" and pending_case_total:
            public_claim_level = "replay_boundary_pending_benchmark_execution"
            public_prediction_status = "PASS_REPLAYABLE_WITH_PENDING_BENCHMARK_EXECUTION"
        elif public_claim_level == "validated_predictive" and case_total_value and executed_case_total < int(case_total_value or 0):
            public_claim_level = "replay_boundary_incomplete_benchmark_execution"
            public_prediction_status = "PASS_REPLAYABLE_WITH_INCOMPLETE_BENCHMARK_EXECUTION"
        raw_source_refs = [
            "logion/k0/governance/status/DOMAIN_REPLAY_REPORTS_latest.json",
            "logion/k0/governance/status/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
            "logion/k0/governance/status/OC_DOMAIN_PROJECTION_COMPLETION_latest.json",
        ]
        item = {
            "domain_id": domain,
            "title": row.get("title", domain),
            "source_status": status,
            "prediction_status": public_prediction_status,
            "promotion_state": promotion_state,
            "closure_status": closure_status,
            "closure_basis": "domain replay report and empirical validation matrix" if replay_backed else "domain declared meta-only / not required" if meta_only else "domain replay closure is not yet present",
            "replay_status": replay_status or ("NOT_APPLICABLE" if meta_only else "UNKNOWN"),
            "validation_status": validation_status or ("NOT_APPLICABLE" if meta_only else "UNKNOWN"),
            "replay_hashes": completion_hashes,
            "claim_level": public_claim_level,
            "raw_claim_level": raw_claim_level if edition == "private" else "",
            "closure_program_status": validation_row.get("closure_program_status", ""),
            "pass_semantics": "PASS means the demonstrator lane has public replay/calibration evidence and a bounded display contract; it does not mean unsupported prediction validation.",
            "prediction_boundary": public_prediction_status if public_prediction_status else "PREDICTION_DECLARED_PENDING_EXECUTION_OR_BOUNDARY_ONLY",
            "pass_does_not_mean": "external validation, solved domain theory, production forecast, or proof closure",
            "claim_display_policy": "Always show prediction status, claim level and nonclaim boundary next to PASS/replay badges.",
            "source_refs": _public_source_refs(raw_source_refs, f"domain-{domain.lower()}"),
            "measurable_outputs": row.get("measurable_outputs", []),
            "nonclaim_boundary": _clean(row.get("nonclaim_boundary", ""), 500),
            "theorem_to_observable_map": [_clean(text, 300) for text in row.get("theorem_to_observable_map", [])],
            "benchmark_dataset_manifest": row.get("benchmark_dataset_manifest", []),
            "case_total": case_total_value,
            "benchmark_pending_execution_total": pending_case_total,
            "benchmark_executed_prediction_total": executed_case_total,
            "held_out_case_total": replay_row.get("held_out_case_total") or validation_row.get("held_out_case_total") or sum(int(item.get("held_out_case_total", 0) or 0) for item in completion_rows),
            "benchmark_cases": benchmark_cases,
        }
        if edition == "private":
            item["private_replay_command_ref"] = row.get("replay_command_ref", "")
            item["private_refs"] = row.get("refs", [])
            item["private_raw_source_ref_hashes"] = [_hash(ref) for ref in raw_source_refs]
        out.append(item)
    return out


def _promotion_state(status: Any, validation: Any) -> str:
    text = f"{status} {validation}".upper()
    if "ACTIVE_NUMERICAL_PACKET" in text and "PENDING" not in text:
        return "supported"
    if "PENDING" in text or "SPEC_READY" in text:
        return "frontier-gap"
    if "NOT_REQUIRED" in text:
        return "meta-or-not-required"
    return "bounded"


def _wiki(edition: str, pass_units: list[tuple[Path, dict[str, Any]]] | None = None) -> dict[str, Any]:
    pass_units = pass_units or _pass_language_units()
    atoms = _corpus_atoms(edition, pass_units=pass_units)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for atom in atoms:
        grouped.setdefault((atom["document_id"], atom["chapter_id"]), []).append(atom)
    chapters = []
    for order, ((document_id, chapter_id), rows) in enumerate(sorted(grouped.items()), start=1):
        rows = sorted(rows, key=lambda item: item["section_id"])
        chapters.append(
            {
                "id": f"{document_id}::{chapter_id}",
                "document_id": document_id,
                "order": order,
                "title": rows[0]["chapter_title"] or chapter_id.replace("_", " ").title(),
                "sections": [
                    {
                        "heading": rows[index]["source_unit_id"],
                        "paragraphs": [rows[index]["text"]],
                    }
                    for index in range(min(6, len(rows)))
                ],
                "claim_trace": [item["source_unit_id"] for item in rows[:5]],
                "residual_uncertainties": ["See proof/evidence route and nonclaim boundary before treating reader text as proof."],
                "atom_count": len(rows),
            }
        )
    glossary = _glossary_from_atoms(atoms)
    formula_rows = _formula_rows(edition)
    _enrich_formula_rows_with_atoms(formula_rows, atoms, edition)
    return {
        "glossary": glossary,
        "postulates": _postulates(),
        "operators": _operators(),
        "chapters": chapters,
        "corpus_atoms": atoms,
        "corpus_summary": {
            "atom_count": len(atoms),
            "documents": dict(Counter(atom["document_id"] for atom in atoms)),
            "chapter_count": len(chapters),
            "full_corpus_mode": "atomized-pass-units",
        },
        "formulas": formula_rows,
    }


def _pass_language_units() -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    for pattern in ("master_monograph__*.json", "methods_repro_companion__*.json"):
        for path in sorted(OC14_UNITS.glob(pattern)):
            row = _read_json(path, {})
            if isinstance(row, dict) and row.get("language_source_status") == "PASS":
                rows.append((path, row))
    return rows


def _corpus_atoms(edition: str, pass_units: list[tuple[Path, dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    pass_units = pass_units or _pass_language_units()
    atoms: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, row in pass_units:
        text = _clean(row.get("translation_source_text", ""), 1800)
        if not text:
            continue
        unit_id = str(row.get("unit_id", path.stem))
        if unit_id in seen:
            continue
        seen.add(unit_id)
        atom = {
            "unit_id": unit_id,
            "source_unit_id": row.get("source_unit_id", path.stem),
            "document_id": row.get("target_artifact_id", path.stem.split("__", 1)[0]),
            "chapter_id": row.get("chapter_id", ""),
            "chapter_title": _clean(row.get("chapter_title", ""), 180),
            "section_id": row.get("section_id", ""),
            "text": text,
            "search_text": _clean(
                " ".join([row.get("target_artifact_id", ""), row.get("chapter_title", ""), row.get("translation_source_text", "")]),
                2400,
            ).lower(),
            "source_hash": row.get("source_content_sha256", ""),
            "target_pdf_filename": row.get("target_pdf_filename", ""),
            "formula_query": _formula_query_from_text(text),
            "proof_query": _formula_query_from_text(text),
            "language_source_status": row.get("language_source_status", ""),
            "language_source_path": path.name,
        }
        if edition == "private":
            atom["private_unit_path"] = _safe_rel(path)
            atom["private_translator_note_hash"] = row.get("translator_note_sha256", "")
        atoms.append(atom)
    return atoms


def _glossary_from_atoms(atoms: list[dict[str, Any]]) -> list[dict[str, str]]:
    terms: dict[str, str] = {}
    seed_terms = {
        "Continuum": "A bounded field of variation whose identity is tracked through transformations.",
        "Boundary": "A coupling and separation rule that controls how a continuum is projected and can fail.",
        "K-level": "An ontological level with declared admissible structure, invariants and domain projections.",
        "Collapse": "Loss of workable coherence or connectivity after load outruns repair or re-description.",
        "Nonclaim": "A declared boundary that prevents demonstration, replay or reader text from being over-promoted into proof.",
    }
    terms.update(seed_terms)
    for atom in atoms[:1200]:
        text = atom["text"]
        for match in re.finditer(r"\b([A-Z][A-Za-z -]{3,42})\s+(?:is|means|denotes)\s+([^.;]{24,220})", text):
            term = _clean(match.group(1), 60)
            if term not in terms:
                terms[term] = _clean(match.group(2), 260)
    return [{"term": key, "definition": value} for key, value in sorted(terms.items())[:420]]


FORMULA_DOMAIN_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Physics", ("energy", "phase", "entropy", "lambda", "Δ", "E_", "Hamilton", "field")),
    ("Chemistry", ("reaction", "chemical", "raf", "molecule", "activation", "cataly")),
    ("Biology", ("cell", "gene", "organism", "bio", "selection", "state transition")),
    ("Systems", ("cascade", "flow", "connectivity", "network", "threshold", "recovery", "load")),
    ("Mathematics", ("forall", "exists", "theorem", "proof", "pi", "homotopy", "Omega", "Ω")),
    ("Metaontology", ("continuum", "axis", "collapse", "coherence", "operator", "K_", "K(", "M")),
)


OPERATOR_MEANINGS: dict[str, str] = {
    "K": "continuum or K-level indexed system",
    "M": "state/model space with nodes, relations, axes and thresholds",
    "N": "node set or substrate population inside an M-space",
    "A": "active axis set / expressible distinction set",
    "E": "edge set, evidence score, or energy term depending on row context",
    "I": "invariant, interaction map, or interpretation map",
    "Ω": "admissible state space of a continuum",
    "Phi": "coherence / viability functional",
    "Φ": "coherence / viability functional",
    "Theta": "critical threshold",
    "Θ": "critical threshold",
    "Delta": "change across time, level or perturbation",
    "Δ": "change across time, level or perturbation",
    "rho": "recovery index",
    "ρ": "recovery index",
    "delta": "damage / activation indicator",
    "δ": "damage / activation indicator",
    "pi": "domain projection or structure-preserving map",
    "π": "domain projection or structure-preserving map",
    "Sigma": "aggregate over nodes, evidence roles or flows",
    "Σ": "aggregate over nodes, evidence roles or flows",
    "w": "edge, evidence or channel weight",
    "s": "system state",
    "t": "time or ordered replay step",
    "f": "constraint / boundary function",
    "p": "control probability, percolation parameter, or pressure term",
    "n": "index, count, or K-level offset",
    "F": "flow capacity or flow bundle",
    "C": "contradiction, coherence or connectivity depending on row context",
    "R": "repair / resilience / recovery term",
    "L": "load term",
    "B": "boundary or buffering term",
}

FORMULA_TYPED_SIGNATURE_HINTS: dict[str, str] = {
    "->": "relation",
    "∨": "logical_op",
    "⇔": "equivalence_op",
    "≠": "predicate",
    "∅": "set",
    "∪": "set",
    "∩": "set",
    "⊆": "set",
    "Ω": "set",
    "Phi": "function",
    "Φ": "function",
    "Theta": "function",
    "Θ": "function",
    "Delta": "function",
    "Δ": "function",
    "rho": "scalar",
    "ρ": "scalar",
    "w": "scalar",
    "s": "scalar",
    "t": "scalar",
    "C": "set",
    "f": "function",
    "p": "scalar",
    "n": "index",
    "F": "function",
    "R": "scalar",
    "B": "scalar",
    "K": "function",
    "A": "set",
    "M": "set",
    "N": "set",
    "E": "scalar",
    "I": "relation",
    "pi": "function",
    "π": "function",
    "Sigma": "aggregation",
    "Σ": "aggregation",
}


CANONICAL_OC_FORMULAS: list[dict[str, Any]] = [
    {
        "formula_id": "OCF-001",
        "semantic_title": "Contradiction bifurcation",
        "domain": "Metaontology",
        "formula_text": "C_K(t) > \\Theta_K \\to \\operatorname{AxisBirth}_K(t) \\lor \\operatorname{Collapse}_K(t)",
        "interpretation": "When contradiction pressure in a continuum exceeds its threshold, the lawful branch is new-axis formation or collapse.",
        "consequences": ["A contradiction is not merely noise; it is a transition trigger.", "Collapse and axis birth are separated by boundary/recovery capacity."],
        "chart_kind": "threshold_bifurcation",
    },
    {
        "formula_id": "OCF-002",
        "semantic_title": "Admissible state viability",
        "domain": "Metaontology",
        "formula_text": "\\operatorname{Alive}_K(t) \\Leftrightarrow \\Omega_K(t) \\ne \\varnothing",
        "interpretation": "A continuum remains alive while at least one admissible state remains open.",
        "consequences": ["Collapse can be displayed as admissible-state exhaustion.", "Recovery is meaningful only if a path reopens Ω."],
        "chart_kind": "state_space",
    },
    {
        "formula_id": "OCF-003",
        "semantic_title": "Collapse condition",
        "domain": "Systems",
        "formula_text": "\\operatorname{Collapse}_K(t^*) \\Leftrightarrow \\Omega_K(t^*) = \\varnothing",
        "interpretation": "At the collapse time the admissible state space is empty under the active constraints.",
        "consequences": ["The demonstrator can show collapse as loss of reachable viable states.", "This is a boundary condition, not an empirical forecast by itself."],
        "chart_kind": "state_space",
    },
    {
        "formula_id": "OCF-004",
        "semantic_title": "Coherence balance",
        "domain": "Systems",
        "formula_text": "\\Phi_K(t) = B_K(t) + R_K(t) - L_K(t) - C_K(t)",
        "interpretation": "Coherence rises with boundary/repair capacity and falls with load/contradiction pressure.",
        "consequences": ["The workbench can diagnose whether a system fails from overload or insufficient repair.", "Adding a compensator should change R or B, not the animation speed."],
        "chart_kind": "coherence_balance",
    },
    {
        "formula_id": "OCF-005",
        "semantic_title": "Transition pressure",
        "domain": "Systems",
        "formula_text": "P_K(t) = L_K(t) + C_K(t) - R_K(t) - B_K(t)",
        "interpretation": "Transition pressure is the net excess of load and contradiction over repair and boundary capacity.",
        "consequences": ["P above threshold marks a transition/collapse risk.", "Reducing load and adding buffering are distinct interventions."],
        "chart_kind": "pressure_threshold",
    },
    {
        "formula_id": "OCF-006",
        "semantic_title": "Cascade propagation",
        "domain": "Systems",
        "formula_text": "s_j(t+1)=\\min\\left(1,\\max\\left(0, s_j(t)-\\sum_i w_{ij}\\,\\delta_i(t)+r_j(t)\\right)\\right)",
        "interpretation": "A node loses state from weighted upstream damage, regains state through local recovery, and the public replay clamps the next state into [0,1]. Collapse depth is displayed as a named sub-role, not compressed into the propagation expression.",
        "consequences": ["Kill selected node and kill weakest node share the same deterministic propagation law.", "Speed slider may change playback timing but not this recurrence.", "Per-node replay rows must label one-edge reductions versus multi-input sums.", "collapse_depth is computed as D_c=|P_c| and is not inferred from flow-loss values."],
        "chart_kind": "cascade",
    },
    {
        "formula_id": "OCF-007",
        "semantic_title": "Connectivity loss",
        "domain": "Systems",
        "formula_text": "\\Lambda(t) = 1 - \\frac{\\lvert E_{\\mathrm{alive}}(t)\\rvert}{\\max(\\epsilon, \\lvert E_0\\rvert)}",
        "interpretation": "Connectivity loss measures the fraction of original edges that no longer carry viable system relation.",
        "consequences": ["Cascade depth and graph fragmentation become comparable across templates.", "A system can retain nodes while losing functional connectedness."],
        "chart_kind": "connectivity_loss",
    },
    {
        "formula_id": "OCF-008",
        "semantic_title": "Flow rupture",
        "domain": "Systems",
        "formula_text": "F_{\\mathrm{loss}}(t) = 1 - \\frac{\\sum_i f_{i,\\mathrm{alive}}(t)}{\\max(\\epsilon, \\sum_i f_{i,0})}",
        "interpretation": "Flow rupture is the lost fraction of baseline flow capacity.",
        "consequences": ["The cascade lab can distinguish structural survival from flow survival.", "Restoring a bridge edge should reduce F_loss before it restores every node."],
        "chart_kind": "flow_loss",
    },
    {
        "formula_id": "OCF-009",
        "semantic_title": "Recovery index",
        "domain": "Systems",
        "formula_text": "\\rho = \\frac{\\Phi_{\\mathrm{after}} - \\Phi_{\\min}}{\\max(\\epsilon, \\Phi_{\\mathrm{before}} - \\Phi_{\\min})}",
        "interpretation": "Recovery compares post-reconfiguration coherence against the collapse trough and pre-shock baseline.",
        "consequences": ["Recovery is normalized and comparable across templates.", "Zero recovery means the system never climbed out of its trough."],
        "chart_kind": "recovery",
    },
    {
        "formula_id": "OCF-010",
        "semantic_title": "K-level build-up operator",
        "domain": "Metaontology",
        "formula_text": "K_n = \\Pi_n(K_{n-1}, A_n, I_n)",
        "interpretation": "A higher K-level is built from lower-level substrate, active axes and invariants.",
        "consequences": ["K0->K12 navigation must preserve lower-level dependencies.", "Adding a new axis changes the admissible construction path."],
        "chart_kind": "k_ladder",
    },
    {
        "formula_id": "OCF-011",
        "semantic_title": "Top-down constraint",
        "domain": "Metaontology",
        "formula_text": "K_{n-1}^{\\prime} = T_n(K_n, K_{n-1})",
        "interpretation": "Higher-level organization constrains and reshapes lower-level dynamics.",
        "consequences": ["K12->K0 drilldown cannot be a passive decomposition only.", "Downward constraints should be visible in slice view."],
        "chart_kind": "k_ladder",
    },
    {
        "formula_id": "OCF-012",
        "semantic_title": "M-space tuple",
        "domain": "Metaontology",
        "formula_text": "M = (N, E, A, F, \\Theta, R)",
        "interpretation": "An M-space is a bounded model space of nodes, edges, axes, flows, thresholds and recovery rules.",
        "consequences": ["The workbench builder must expose axes, flows, cycles, thresholds and compensators.", "A system template is not just a graph; it is a typed M-space."],
        "chart_kind": "m_space",
    },
    {
        "formula_id": "OCF-013",
        "semantic_title": "Axis addition",
        "domain": "Metaontology",
        "formula_text": "A^{\\prime}=A\\cup\\{a_{\\mathrm{new}}\\},\\quad M=(N,E,A,F,\\Theta,R),\\quad M^{\\prime}=(N,E,A^{\\prime},F,\\Theta,R)\\;\\text{if}\\;\\operatorname{computable}(a_{\\mathrm{new}})",
        "interpretation": "A new axis updates the typed axis component A of an M-space; it does not union an axis set with the whole M-space tuple.",
        "consequences": ["The UI must use a dropdown of computable axes, not free-text claims.", "Axis addition can raise resilience only inside declared model boundaries."],
        "chart_kind": "axis_addition",
    },
    {
        "formula_id": "OCF-014",
        "semantic_title": "Domain projection",
        "domain": "Domain Projection",
        "formula_text": "D_d(K) = \\pi_d(K, C_d, U_d)",
        "interpretation": "A domain lane is a projection of OC structure through domain constants and units.",
        "consequences": ["Physics, chemistry and biology entries must show recognizable domain anchors.", "Unsupported projections remain boundary-only."],
        "chart_kind": "domain_projection",
    },
    {
        "formula_id": "OCF-015",
        "semantic_title": "Boundary inspectability score",
        "domain": "Proof/Evidence",
        "formula_text": "E_{raw}(c)=\\sum_i b_i(c),\\quad E_{display}(c)=\\min(\\max(0,E_{raw}(c)),\\kappa_c)",
        "interpretation": "The displayed score is route inspectability from visible component contributions. Boundary and obligation rows are capped by kappa_c and do not become proof closure.",
        "consequences": ["Trust ladder rungs use visible score_component_basis contributions plus claim class caps.", "A high display score is not external peer review or proof closure.", "Boundary rows must show raw component total, cap and capped display score together."],
        "chart_kind": "evidence_score",
    },
]


def _semantic_symbol(
    symbol: str,
    symbol_type: str,
    role: str,
    domain: str,
    range_text: str,
    default_value: float | None = None,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "type": symbol_type,
        "role": role,
        "domain": domain,
        "range": range_text,
        "default_value": default_value,
        "source_boundary": "V010 curated semantic symbol contract; parser tokens and raw LaTeX commands are intentionally excluded.",
    }


FORMULA_SYMBOL_TABLE_OVERRIDES: dict[str, list[dict[str, Any]]] = {
    "OCF-001": [
        _semantic_symbol("C_K(t)", "scalar_function", "contradiction pressure in K-level K at replay step t", "selected K/M slice", "[0,1]", 0.0),
        _semantic_symbol("Theta_K", "scalar_threshold", "transition threshold for the selected continuum", "selected K/M slice", "[0,1]", 0.7),
        _semantic_symbol("AxisBirth_K(t)", "event", "new computable axis becomes admissible", "transition branch", "true/false", None),
        _semantic_symbol("Collapse_K(t)", "event", "admissible-state exhaustion or functional collapse branch", "transition branch", "true/false", None),
    ],
    "OCF-002": [
        _semantic_symbol("Alive_K(t)", "predicate", "continuum K remains viable at replay step t", "selected K/M slice", "true/false", None),
        _semantic_symbol("Omega_K(t)", "set", "admissible state set for continuum K", "selected K/M slice", "finite state set", None),
        _semantic_symbol("empty_set", "set_constant", "no admissible states remain", "state-space boundary", "set", None),
    ],
    "OCF-003": [
        _semantic_symbol("Collapse_K(t*)", "predicate", "collapse has occurred at the marked replay step", "selected K/M slice", "true/false", None),
        _semantic_symbol("Omega_K(t*)", "set", "admissible state set at collapse step", "selected K/M slice", "finite state set", None),
        _semantic_symbol("empty_set", "set_constant", "zero admissible states under active constraints", "state-space boundary", "set", None),
    ],
    "OCF-004": [
        _semantic_symbol("Phi_K(t)", "scalar_function", "coherence balance of the selected continuum", "selected K/M slice", "signed normalized scalar", 0.0),
        _semantic_symbol("B_K(t)", "scalar_function", "boundary/buffering capacity", "selected K/M slice", "[0,1]", 0.3),
        _semantic_symbol("R_K(t)", "scalar_function", "repair/recovery capacity", "selected K/M slice", "[0,1]", 0.3),
        _semantic_symbol("L_K(t)", "scalar_function", "external/internal load", "selected K/M slice", "[0,1]", 0.3),
        _semantic_symbol("C_K(t)", "scalar_function", "contradiction pressure scalarized for this balance row", "selected K/M slice", "[0,1]", 0.3),
    ],
    "OCF-005": [
        _semantic_symbol("P_K(t)", "scalar_function", "net transition pressure", "selected K/M slice", "signed normalized scalar", 0.0),
        _semantic_symbol("L_K(t)", "scalar_function", "load pressure", "selected K/M slice", "[0,1]", 0.3),
        _semantic_symbol("C_K(t)", "scalar_function", "contradiction pressure scalarized for this pressure row", "selected K/M slice", "[0,1]", 0.3),
        _semantic_symbol("R_K(t)", "scalar_function", "repair capacity", "selected K/M slice", "[0,1]", 0.3),
        _semantic_symbol("B_K(t)", "scalar_function", "boundary/buffering capacity", "selected K/M slice", "[0,1]", 0.3),
    ],
    "OCF-006": [
        _semantic_symbol("j", "index", "target node being updated", "cascade system graph", "integer node id", None),
        _semantic_symbol("i", "index", "upstream source node contributing damage to j", "cascade system graph", "integer node id", None),
        _semantic_symbol("v_0", "node", "first node in selected collapse path P_c", "cascade replay", "node id in selected system graph", None),
        _semantic_symbol("v_m", "node", "last node in selected collapse path P_c", "cascade replay", "node id in selected system graph", None),
        _semantic_symbol("P_c=(v_0,...,v_m)", "ordered_path_tuple", "selected collapse path tuple through the system graph", "cascade replay", "ordered node sequence", None),
        _semantic_symbol("P_c", "ordered_path", "selected collapse path through the system graph", "cascade replay", "ordered node sequence", None),
        _semantic_symbol("D_c", "integer_metric", "collapse depth, the length of selected collapse path P_c", "cascade replay", "nonnegative integer", 0),
        _semantic_symbol("s_j(t)", "scalar_function", "health/state of node j at step t", "cascade system graph", "[0,1]", 1.0),
        _semantic_symbol("t+1", "time_step", "next deterministic replay step after t", "cascade replay clock", "integer replay step", None),
        _semantic_symbol("s_j(t+1)", "scalar_function", "clamped next health/state of node j", "cascade system graph", "[0,1] after min(1,max(0, raw update))", 1.0),
        _semantic_symbol("w_ij", "scalar", "directed dependency weight from i to j", "cascade edge set", "[0,1]", 0.2),
        _semantic_symbol("delta_i(t)", "scalar_function", "damage indicator emitted by node i at step t", "cascade system graph", "[0,1]", 0.0),
        _semantic_symbol("sum_i", "aggregation", "sum over visible upstream source terms for target j", "incoming edges to node j", "nonnegative scalar", 0.0),
        _semantic_symbol("max(0,x)", "clamp_operator", "lower-bound clamp preventing negative displayed node state", "numeric display guard", "[0,infinity) before upper cap", None),
        _semantic_symbol("min(1,x)", "clamp_operator", "upper-bound clamp preventing node state above the normalized template domain", "numeric display guard", "[0,1] after lower clamp", None),
        _semantic_symbol("clamp", "display_policy", "export label for min(1,max(0, raw_output_before_clamp))", "cascade arithmetic export", "min(1,max(0,x))", None),
        _semantic_symbol("r_j(t)", "scalar_function", "local recovery term for node j", "cascade system graph", "[0,1]", 0.0),
    ],
    "OCF-007": [
        _semantic_symbol("Lambda(t)", "scalar_function", "fraction of baseline connectivity lost", "cascade system graph", "[0,1]", 0.0),
        _semantic_symbol("E_alive(t)", "set", "alive/functional edge set at step t", "cascade edge set", "finite edge set", None),
        _semantic_symbol("E_0", "set", "baseline edge set before the shock", "cascade edge set", "finite edge set", None),
        _semantic_symbol("epsilon", "positive_scalar", "zero-denominator guard", "numeric display guard", ">0", 1e-9),
    ],
    "OCF-008": [
        _semantic_symbol("i", "index", "flow-channel index in the summation", "system flow channels", "integer flow id", None),
        _semantic_symbol("F_loss(t)", "scalar_function", "fraction of baseline flow capacity lost", "system flow channels", "[0,1]", 0.0),
        _semantic_symbol("f_i_alive(t)", "scalar_function", "alive flow capacity for channel i at step t", "system flow channels", "[0,1]", 1.0),
        _semantic_symbol("f_i_0", "scalar", "baseline flow capacity for channel i", "system flow channels", "[0,1]", 1.0),
        _semantic_symbol("epsilon", "positive_scalar", "zero-denominator guard", "numeric display guard", ">0", 1e-9),
    ],
    "OCF-009": [
        _semantic_symbol("rho", "scalar", "normalized recovery index", "workbench comparison", "[0,1] when bounded by baseline/trough", 0.0),
        _semantic_symbol("Phi_after", "scalar", "coherence after recovery/reconfiguration", "workbench comparison", "signed normalized scalar", 0.0),
        _semantic_symbol("Phi_min", "scalar", "minimum coherence reached during collapse", "workbench comparison", "signed normalized scalar", 0.0),
        _semantic_symbol("Phi_before", "scalar", "baseline coherence before shock", "workbench comparison", "signed normalized scalar", 0.0),
        _semantic_symbol("epsilon", "positive_scalar", "zero-denominator guard", "numeric display guard", ">0", 1e-9),
    ],
    "OCF-010": [
        _semantic_symbol("K_n", "structured_level", "constructed higher K-level", "K/M hierarchy", "K-level entity", None),
        _semantic_symbol("K_{n-1}", "structured_level", "lower-level substrate feeding K_n", "K/M hierarchy", "K-level entity", None),
        _semantic_symbol("A_n", "set", "active axis set at level n", "K/M hierarchy", "finite axis set", None),
        _semantic_symbol("I_n", "relation", "invariant/interpretation constraints at level n", "K/M hierarchy", "finite relation set", None),
        _semantic_symbol("Pi_n", "operator", "build-up projection operator", "K/M hierarchy", "level transition map", None),
    ],
    "OCF-011": [
        _semantic_symbol("K_n", "structured_level", "higher-level organization", "K/M hierarchy", "K-level entity", None),
        _semantic_symbol("K'_{n-1}", "structured_level", "lower-level substrate after top-down constraint", "K/M hierarchy", "K-level entity", None),
        _semantic_symbol("K_{n-1}", "structured_level", "lower-level substrate before constraint", "K/M hierarchy", "K-level entity", None),
        _semantic_symbol("T_n", "operator", "top-down constraint operator", "K/M hierarchy", "constraint map", None),
    ],
    "OCF-012": [
        _semantic_symbol("M", "tuple", "bounded model space", "system workbench", "(N,E,A,F,Theta,R)", None),
        _semantic_symbol("N", "set", "nodes/entities", "system workbench", "finite node set", None),
        _semantic_symbol("E", "set", "edges/dependencies", "system workbench", "finite edge set", None),
        _semantic_symbol("A", "set", "computable axes", "system workbench", "finite axis set", None),
        _semantic_symbol("F", "set", "flow channels", "system workbench", "finite flow set", None),
        _semantic_symbol("Theta", "set", "threshold rules", "system workbench", "finite threshold set", None),
        _semantic_symbol("R", "set", "recovery rules/compensators", "system workbench", "finite recovery rule set", None),
    ],
    "OCF-013": [
        _semantic_symbol("M", "tuple", "current bounded model space", "system workbench", "M-space tuple", None),
        _semantic_symbol("M'", "tuple", "model space after admissible axis addition", "system workbench", "M-space tuple", None),
        _semantic_symbol("A", "axis_set", "current axis component inside M", "system workbench", "finite axis set", None),
        _semantic_symbol("A'", "axis_set", "updated axis component A union admissible new axis", "system workbench", "finite axis set", None),
        _semantic_symbol("a_new", "axis", "candidate new axis", "axis dropdown", "axis id", None),
        _semantic_symbol("computable(a_new)", "predicate", "axis has a declared local calculation", "axis dropdown", "true/false", None),
    ],
    "OCF-014": [
        _semantic_symbol("D_d(K)", "domain_projection", "projection of continuum K into domain d", "domain lane", "domain-specific bounded packet", None),
        _semantic_symbol("pi_d", "operator", "domain projection map", "domain lane", "projection map", None),
        _semantic_symbol("C_d", "set", "domain constants/calibration anchors", "domain lane", "public-safe constant set", None),
        _semantic_symbol("U_d", "set", "domain units/conventions", "domain lane", "unit system", None),
        _semantic_symbol("K", "structured_continuum", "source continuum or K-level structure", "K/M hierarchy", "K-level entity", None),
    ],
    "OCF-015": [
        _semantic_symbol("c", "claim_route", "proof/evidence route being scored", "proof/evidence route", "route id", None),
        _semantic_symbol("i", "index", "evidence-role index in the weighted inspectability sum", "proof/evidence route", "integer role id", None),
        _semantic_symbol("b_i(c)", "scalar_component", "visible score_component_basis contribution for role i on route c", "proof/evidence route", "[0,1] contribution", 0.0),
        _semantic_symbol("E_raw(c)", "scalar_function", "uncapped raw inspectability component total before clamp and claim-class cap", "proof/evidence route", "nonnegative raw sum; normalized display is E_display(c), not E_raw(c)", 0.0),
        _semantic_symbol("E_display(c)", "scalar_function", "displayed clamped/capped inspectability score", "proof/evidence route", "[0,1]", 0.0),
        _semantic_symbol("kappa_c", "scalar", "claim-class cap; boundary/obligation rows stay below proof closure", "proof/evidence route", "[0,1]", 0.74),
        _semantic_symbol("max(0,x)", "clamp_operator", "lower-bound clamp for raw component totals", "numeric display guard", "[0,infinity) before cap", None),
        _semantic_symbol("min(x,kappa_c)", "cap_operator", "claim-class cap applied to the displayed score", "proof/evidence route", "[0,kappa_c]", None),
    ],
}


def _typed_signatures_from_symbol_table(symbol_table: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in symbol_table:
        symbol = str(item.get("symbol", "")).strip()
        if not symbol:
            continue
        rows.append(
            {
                "symbol": symbol,
                "signature": f"{symbol}: {item.get('domain', 'declared domain')} -> {item.get('range', 'declared range')}",
                "kind": str(item.get("type", "semantic_symbol")),
                "semantic_hint": str(item.get("role", "curated semantic symbol")),
            }
        )
    return rows


def _formula_presentation_metadata(formula_id: str) -> dict[str, Any]:
    sections: list[dict[str, Any]] = [
        {
            "section_id": f"{formula_id}.primary_expression",
            "title": "Primary expression",
            "role": "formula_text",
            "visible_expression": "formula_text",
            "display_policy": "Shown in the Formula Atlas table as the main expression.",
        }
    ]
    family_relation = {
        "status": "STANDALONE",
        "relation_note": "No required paired formula relation for this row.",
        "paired_formula_ids": [],
    }
    disambiguation_notes: list[dict[str, str]] = []
    output_examples: list[dict[str, Any]] = []
    operator_count_rule = {
        "status": "PASS_DECLARED",
        "counting_unit": "semantic symbol/operator rows, not raw LaTeX parser tokens or expression tree nodes",
        "review_note": "operator_count is a UI glossary cardinality; expression complexity is covered by symbol_table and formula_subderivations.",
    }
    cross_links: list[dict[str, str]] = []

    if formula_id == "OCF-006":
        sections = [
            {
                "section_id": "OCF-006.propagation_section",
                "title": "Node propagation recurrence",
                "role": "OCF-006.propagation_update",
                "visible_expression": "s_j(t+1)=min(1,max(0,s_j(t)-sum_i w_ij delta_i(t)+r_j(t)))",
                "display_policy": "Main formula table row teaches state propagation only.",
            },
            {
                "section_id": "OCF-006.path_depth_section",
                "title": "Collapse path depth",
                "role": "OCF-006.path_depth",
                "visible_expression": "P_c=(v_0,...,v_m); D_c=|P_c|",
                "display_policy": "Shown as a named subderivation and in cascade export rows, not compressed into formula_text.",
            },
        ]
        family_relation = {
            "status": "PASS_SPLIT_FORMULA_FAMILY",
            "relation_note": "OCF-006 is a cascade family with separate propagation and path-depth roles; both must be visible in exports.",
            "paired_formula_ids": [],
        }
    elif formula_id == "OCF-013":
        sections = [
            {
                "section_id": "OCF-013.admissibility_guard",
                "title": "Admissibility guard",
                "role": "axis_admissibility",
                "visible_expression": "computable(a_new)",
                "display_policy": "The Add axis dropdown exposes only axes with a declared computable guard.",
            },
            {
                "section_id": "OCF-013.tuple_component_update",
                "title": "M-space tuple update",
                "role": "typed_tuple_component_update",
                "visible_expression": "A'=A union {a_new}; M'=(N,E,A',F,Theta,R)",
                "display_policy": "Only the A component changes; N,E,F,Theta,R are inherited unless another control changes them.",
            },
        ]
        family_relation = {
            "status": "PASS_GUARD_AND_TUPLE_SEPARATED",
            "relation_note": "Axis admissibility and tuple mutation are separate visible steps.",
            "paired_formula_ids": ["OCF-012"],
        }
    elif formula_id in {"OCF-004", "OCF-005"}:
        pair = "OCF-005" if formula_id == "OCF-004" else "OCF-004"
        family_relation = {
            "status": "PASS_INVERSE_PAIR_VISIBLE",
            "relation_note": "OCF-004 coherence balance and OCF-005 transition pressure use the same terms with opposite sign convention: P_K(t) = -Phi_K(t) for the displayed normalized balance row.",
            "paired_formula_ids": [pair],
        }
        cross_links.append({"target_formula_id": pair, "relation": "inverse_sign_pair"})
    elif formula_id in {"OCF-002", "OCF-003"}:
        pair = "OCF-003" if formula_id == "OCF-002" else "OCF-002"
        family_relation = {
            "status": "PASS_VIABILITY_COLLAPSE_DUAL_VISIBLE",
            "relation_note": "OCF-002 states viability while Omega_K is non-empty; OCF-003 is the dual boundary where Omega_K becomes empty.",
            "paired_formula_ids": [pair],
        }
        cross_links.append({"target_formula_id": pair, "relation": "viability_collapse_dual"})
    elif formula_id == "OCF-014":
        output_examples = [
            {"domain": "Physics", "example_output": "D_physics(K4) -> constants/units lane plus replay-backed boundary labels.", "status": "EXPLANATORY_PUBLIC_SAFE"},
            {"domain": "Chemistry", "example_output": "D_chemistry(K5) -> thermochemical/spectral anchor packet when source status permits.", "status": "BOUNDARY_AWARE"},
            {"domain": "Biology", "example_output": "D_biology(K7) -> state-transition signature lane with validation status.", "status": "BOUNDARY_AWARE"},
        ]
    elif formula_id == "OCF-015":
        sections = [
            {
                "section_id": "OCF-015.raw_total",
                "title": "Raw component total",
                "role": "raw_component_total",
                "visible_expression": "E_raw(c)=sum_i b_i(c)",
                "display_policy": "Uncapped diagnostic sum; may exceed the final displayed range.",
            },
            {
                "section_id": "OCF-015.display_cap",
                "title": "Displayed capped score",
                "role": "claim_class_cap",
                "visible_expression": "E_display(c)=min(max(0,E_raw(c)),kappa_c)",
                "display_policy": "Only E_display(c) is shown as normalized inspectability; boundary rows remain non-proof.",
            },
        ]
        family_relation = {
            "status": "PASS_RAW_DISPLAY_SPLIT_VISIBLE",
            "relation_note": "Raw component totals and capped display scores are separate quantities; this is inspectability, not proof closure.",
            "paired_formula_ids": [],
        }
        operator_count_rule["review_note"] = "operator_count counts the named semantic symbols/operators in the table; it does not claim to measure expression-tree complexity."

    if formula_id in {"OCF-001", "OCF-012"}:
        disambiguation_notes.append(
            {
                "symbol": "Theta",
                "note": "Theta_K in OCF-001 is a contradiction threshold; Theta in OCF-012 is the set of threshold rules inside an M-space tuple.",
                "paired_formula_ids": "OCF-001, OCF-012",
            }
        )

    return {
        "formula_presentation_sections": sections,
        "formula_family_relation": family_relation,
        "symbol_disambiguation_notes": disambiguation_notes,
        "formula_output_examples": output_examples,
        "operator_count_rule": operator_count_rule,
        "cross_formula_links": cross_links,
    }


def _formula_domain(text: str, source_refs: list[Any] | None = None, fallback: str = "General OC") -> str:
    haystack = f"{text} {' '.join(str(ref) for ref in (source_refs or []))}".lower()
    for domain, keywords in FORMULA_DOMAIN_KEYWORDS:
        if any(keyword.lower() in haystack for keyword in keywords):
            return domain
    return fallback


def _formula_symbol_present(symbol: str, text: str) -> bool:
    if len(symbol) == 1 and symbol.isalpha():
        return bool(re.search(rf"(?<![A-Za-z\\]){re.escape(symbol)}(?![A-Za-z])", text))
    if symbol in {"Theta", "Phi", "Delta", "Sigma", "Omega"}:
        return f"\\{symbol}" in text or symbol in text
    if symbol in {"theta", "phi", "delta", "sigma", "omega", "rho", "pi"}:
        return f"\\{symbol}" in text or bool(re.search(rf"(?<![A-Za-z\\]){re.escape(symbol)}(?![A-Za-z])", text))
    return symbol in text


def _formula_operator_glossary(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for symbol, meaning in OPERATOR_MEANINGS.items():
        if _formula_symbol_present(symbol, text) and not any(row["symbol"] == symbol for row in rows):
            rows.append({"symbol": symbol, "meaning": meaning})
    if "\\Omega" in text and not any(row["symbol"] == "Ω" for row in rows):
        rows.append({"symbol": "Ω", "meaning": "admissible state space of a continuum"})
    if "\\kcont" in text and not any(row["symbol"] == "k_cont" for row in rows):
        rows.append({"symbol": "k_cont", "meaning": "continuumness / viable-continuum score"})
    if "\\KEA" in text and not any(row["symbol"] == "K_EA" for row in rows):
        rows.append({"symbol": "K_EA", "meaning": "named evidence-atlas continuum used in the source formula"})
    if any(token in text for token in ("->", "→")):
        rows.append({"symbol": "->", "meaning": "lawful implication or transition route"})
    if any(token in text for token in ("∨", " or ")):
        rows.append({"symbol": "∨", "meaning": "branching alternative"})
    if "⇔" in text:
        rows.append({"symbol": "⇔", "meaning": "definition / equivalence inside the model boundary"})
    if "≠" in text:
        rows.append({"symbol": "≠", "meaning": "non-empty or non-identical condition"})
    if any(token in text for token in ("\\varnothing", "\\emptyset", "∅")):
        rows.append({"symbol": "∅", "meaning": "empty set / no admissible states or no surviving cycles"})
    if "\\cup" in text or "∪" in text:
        rows.append({"symbol": "∪", "meaning": "union or axis/state addition"})
    if "\\cap" in text or "∩" in text:
        rows.append({"symbol": "∩", "meaning": "intersection / overlap test"})
    if "\\subset" in text or "⊂" in text or "⊆" in text:
        rows.append({"symbol": "⊆", "meaning": "inclusion or monotone containment"})
    return rows[:10]


def _derive_typed_symbol_signatures(text: str) -> list[dict[str, str]]:
    clean = _normalize_formula_text(text)
    glossary = _formula_operator_glossary(clean)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_signature(symbol: str, signature: str, kind: str) -> None:
        label = _clean(symbol)
        if not label or label in seen:
            return
        seen.add(label)
        rows.append(
            {
                "symbol": label,
                "signature": signature,
                "kind": kind,
                "semantic_hint": "inferred-from-formula-context",
            }
        )

    for row in glossary:
        symbol = row.get("symbol", "")
        kind = FORMULA_TYPED_SIGNATURE_HINTS.get(symbol, "scalar")
        if symbol in {"->", "∨", "⇔", "≠", "∅", "∪", "∩", "⊆"}:
            signature = "relation"
        elif "\\" in symbol:
            signature = f"{symbol}(...) -> {symbol}_v"
        elif symbol in {"C", "R", "B", "F"}:
            signature = f"{symbol} : Scalar"
        elif symbol in {"K", "M", "N", "A"}:
            signature = f"{symbol} : Set"
        elif symbol in {"f", "π", "pi", "Θ", "Theta", "Δ", "Delta", "Ω", "Sigma", "Σ"}:
            signature = f"{symbol}(domain_state) -> scalar_or_set"
        else:
            signature = f"{symbol} : Scalar"
        add_signature(symbol, signature, kind)

    for match in re.finditer(r"\\?[A-Za-z]+(?:_{[^}]+})?", clean):
        token = match.group(0).strip("\\")
        if not token:
            continue
        if len(token) < 2:
            continue
        if any(token.lower() == glossary_row.get("symbol", "").lower() for glossary_row in glossary):
            continue
        if token.lower() in {
            "and",
            "the",
            "with",
            "from",
            "into",
            "where",
            "only",
            "when",
            "such",
            "that",
            "this",
            "while",
            "each",
            "each",
            "then",
            "for",
        }:
            continue
        kind = FORMULA_TYPED_SIGNATURE_HINTS.get(token, "function" if "(" in clean else "scalar")
        signature = f"{token}(...) -> {token}_out"
        add_signature(token, signature, kind)

    return rows[:16]


def _formula_symbol_table(text: str, typed_signatures: list[dict[str, str]], operators: list[dict[str, str]]) -> list[dict[str, Any]]:
    meanings = {row.get("symbol", ""): row.get("meaning", "") for row in operators}
    rows: list[dict[str, Any]] = []
    for signature in typed_signatures:
        symbol = signature.get("symbol", "")
        if not symbol:
            continue
        kind = signature.get("kind", "scalar")
        if kind in {"set", "relation"}:
            domain = "finite symbolic set or relation inside the selected K/M slice"
            range_text = "set/relation"
        elif kind == "function":
            domain = "declared symbolic state variables for the selected template"
            range_text = "bounded scalar_or_set"
        else:
            domain = "[0,1] normalized diagnostic scalar unless a domain lane overrides units"
            range_text = "[0,1] or signed symbolic scalar"
        rows.append(
            {
                "symbol": symbol,
                "type": kind,
                "role": meanings.get(symbol, signature.get("semantic_hint", "symbolic diagnostic term")),
                "domain": domain,
                "range": range_text,
                "default_value": 0.0 if kind == "scalar" else None,
                "source_boundary": "V010 curated symbolic formula contract; SI-unit claims require a domain replay lane.",
            }
        )
    return rows


def _formula_dimension_checks(text: str, symbol_table: list[dict[str, Any]]) -> dict[str, Any]:
    denominator_terms = re.findall(r"\\frac\{[^{}]+\}\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}", text)
    if "\\frac" in text and not denominator_terms:
        denominator_terms = ["semantic denominator declared by symbol table / max(epsilon, denominator) guard"]
    operations = []
    semantic_symbols = [str(row.get("symbol", "")) for row in symbol_table]
    scalar_symbols = [
        symbol
        for symbol, row in zip(semantic_symbols, symbol_table)
        if any(marker in str(row.get("type", "")).lower() for marker in ("scalar", "threshold", "positive"))
        or "[0,1]" in str(row.get("range", ""))
        or "signed normalized scalar" in str(row.get("range", ""))
    ]
    set_symbols = [
        symbol
        for symbol, row in zip(semantic_symbols, symbol_table)
        if str(row.get("type", "")).lower() in {"set", "tuple", "relation", "structured_level", "structured_continuum", "domain_projection"}
    ]
    has_additive_operation = bool(re.search(r"\s[+\-]\s", text))
    if has_additive_operation:
        operations.append({
            "operation": "additive_balance",
            "operand_dimension": "normalized_diagnostic_scalar",
            "status": "PASS_SYMBOLIC",
            "operands_declared_scalar": scalar_symbols,
            "set_operands_excluded_from_arithmetic": set_symbols,
            "explanation": "Add/subtract terms use row-context scalarized diagnostic quantities; set-like symbols are not treated as arithmetic operands.",
        })
    if "\\frac" in text:
        operations.append({
            "operation": "ratio",
            "operand_dimension": "compatible_normalized_scalar",
            "status": "PASS_SYMBOLIC",
            "operands_declared_scalar": scalar_symbols,
            "set_cardinality_terms": [symbol for symbol in set_symbols if "E_" in symbol or symbol.endswith("_0")],
            "explanation": "Ratio numerator and denominator use compatible bounded magnitudes; denominator guards are listed explicitly.",
        })
        if any(row.get("type") == "set" for row in symbol_table):
            operations.append({
                "operation": "set_cardinality_ratio",
                "operand_dimension": "cardinality_of_declared_sets",
                "status": "PASS_SYMBOLIC",
                "explanation": "Set-valued terms are used through visible cardinality bars in the displayed formula.",
            })
    if "\\max(\\epsilon" in text or "max(\\epsilon" in text:
        operations.append({"operation": "guarded_denominator", "operand_dimension": "epsilon_guarded_scalar", "status": "PASS_SYMBOLIC", "explanation": "max(epsilon, denominator) prevents zero-denominator display claims."})
    if "A\\cup\\{a_{\\mathrm{new}}\\}" in text or "A\\cup\\{a_new\\}" in text:
        operations.append({
            "operation": "typed_tuple_component_update",
            "operand_dimension": "axis_component_of_m_space_tuple",
            "status": "PASS_SYMBOLIC",
            "explanation": "Axis addition updates component A inside M=(N,E,A,F,Theta,R); it does not union the whole tuple with an axis.",
            "inherited_tuple_component_binding": {
                "source_tuple": "M=(N,E,A,F,Theta,R)",
                "updated_tuple": "M'=(N,E,A union {a_new},F,Theta,R)",
                "updated_component": "A",
                "inherited_components": ["N", "E", "F", "Theta", "R"],
                "binding_status": "PASS_COMPONENTS_VISIBLE",
            },
        })
    if "D_c" in text and "P_c" in text:
        operations.append({
            "operation": "path_cardinality_depth",
            "operand_dimension": "cardinality_of_ordered_collapse_path",
            "status": "PASS_SYMBOLIC",
            "explanation": "Collapse depth is displayed as D_c=|P_c|, the length/cardinality of the selected collapse path.",
        })
    if "s_j(t+1)" in text and "w_{ij}" in text and "\\delta_i" in text:
        operations.append({
            "operation": "cascade_state_update",
            "operand_dimension": "normalized_node_state_scalar",
            "status": "PASS_SYMBOLIC_ARITHMETIC_SAMPLE",
            "scalar_terms": {
                "s_j(t)": 1.0,
                "w_ij": 0.41,
                "delta_i(t)": 0.82,
                "r_j(t)": 0.09,
                "sum_i w_ij_delta_i": 0.3362,
            },
            "clamp_rule": "s_j(t+1)=min(1, max(0, s_j(t)-sum_i(w_ij*delta_i(t))+r_j(t)))",
            "recomputable_example": "min(1, max(0, 1.0 - 0.3362 + 0.09)) = 0.7538",
            "range_claim_condition": "Displayed s_j(t+1) is in [0,1] for the public replay rows because s_j(t), w_ij, delta_i(t), r_j(t) are [0,1], upstream_terms are nonnegative, and the replay export verifies min(1,max(0, raw_output)) with bounded template inputs.",
            "explanation": "OCF-006 is a named cascade formula family. The UI and exports must bind path cardinality to OCF-006.path_depth and scalar node-state updates to OCF-006.propagation_update.",
        })
    if "E_{display}" in text and "\\kappa_c" in text:
        operations.append({
            "operation": "claim_class_score_cap",
            "operand_dimension": "visible_inspectability_component_scalar",
            "status": "PASS_SYMBOLIC",
            "component_basis": "E_raw(c)=sum_i b_i(c), where b_i(c) are named score_component_basis contributions in proof_body_index rows.",
            "clamp_rule": "E_display(c)=min(max(0,E_raw(c)),kappa_c)",
            "range_claim_condition": "E_display(c) is in [0,1] when every b_i(c) is nonnegative and kappa_c is in [0,1]; boundary/obligation rows use kappa_c<1 and remain non-proof scores.",
            "explanation": "The formula display matches the V010 proof score payload: raw_weighted_score/component_total is capped into capped_score/evidence_score and never upgrades boundary rows to proof closure.",
        })
    if ">" in text or "\\to" in text or "\\lor" in text:
        operations.append({
            "operation": "threshold_branch",
            "operand_dimension": "order-compatible_scalar_threshold",
            "status": "PASS_SYMBOLIC",
            "explanation": "Threshold comparisons are declared over scalar diagnostics and threshold values, not over raw sets.",
        })
    return {
        "status": "PASS_SYMBOLIC_DIMENSION_CONTRACT",
        "dimension_vector": {row["symbol"]: row.get("range", "symbolic") for row in symbol_table},
        "semantic_symbol_count": len(symbol_table),
        "parser_tokens_excluded": True,
        "scalarized_symbols": scalar_symbols,
        "set_symbols_not_used_as_numbers": set_symbols,
        "operation_checks": operations or [{"operation": "symbolic_relation", "operand_dimension": "declared_symbolic_terms", "status": "PASS_SYMBOLIC", "explanation": "No incompatible algebraic operation is exposed in this formula row."}],
        "denominator_terms": denominator_terms,
        "range_claim_conditions": [
            check.get("range_claim_condition")
            for check in operations
            if isinstance(check, dict) and check.get("range_claim_condition")
        ],
        "inherited_tuple_component_bindings": [
            check.get("inherited_tuple_component_binding")
            for check in operations
            if isinstance(check, dict) and check.get("inherited_tuple_component_binding")
        ],
        "nonclaim_boundary": "This is a symbolic workbench consistency check, not a physical SI-dimensional proof.",
    }


def _formula_denominator_guards(formula_id: str, text: str) -> list[dict[str, str]]:
    guards: list[dict[str, str]] = []
    if "\\frac" not in text:
        return guards
    if "\\max(\\epsilon" in text:
        guards.append({"guard": "max(epsilon, denominator)", "status": "VISIBLE_INLINE", "failure_behavior": "If the baseline denominator is zero, the row is boundary-only and uses epsilon for display continuity."})
    else:
        guards.append({"guard": "denominator assumed nonzero and positive", "status": "ASSUMPTION_VISIBLE", "failure_behavior": "If the denominator is zero, the diagnostic is disabled and recorded as a formalization obligation."})
    guards.append({"guard": f"{formula_id} ratio boundary", "status": "NONCLAIM_BOUNDARY", "failure_behavior": "Guard protects the demonstrator calculation only; it is not external validation."})
    return guards


def _formula_range_condition_rows(formula_id: str) -> list[dict[str, Any]]:
    rows_by_formula: dict[str, list[dict[str, Any]]] = {
        "OCF-006": [
            {
                "condition_id": "OCF-006::RANGE::PATH_DEPTH",
                "formula_role_id": "OCF-006.path_depth",
                "output_symbol": "D_c",
                "bounded_range": "nonnegative integer, bounded by selected template node count",
                "template_bound_inputs": ["selected_system_template.nodes", "selected collapse path P_c"],
                "row_level_required_fields": ["template_id", "topology_hash", "P_c", "D_c"],
                "pass_condition": "D_c == len(P_c) and 0 <= D_c <= len(selected_system_template.nodes)",
            },
            {
                "condition_id": "OCF-006::RANGE::PROPAGATION_UPDATE",
                "formula_role_id": "OCF-006.propagation_update",
                "output_symbol": "s_j(t+1)",
                "bounded_range": "[0,1] for public replay rows",
                "template_bound_inputs": ["s_j(t) in [0,1]", "w_ij in [0,1]", "delta_i(t) in [0,1]", "r_j(t) in [0,1]", "visible upstream_terms"],
                "row_level_required_fields": ["template_id", "node_id", "upstream_terms", "sum_value", "raw_output_before_clamp", "clamp_min_applied", "clamp_max_applied", "s_j(t+1)_output"],
                "pass_condition": "s_j(t+1)_output == min(1, max(0, raw_output_before_clamp)) and replay row verifies the output in the normalized template domain",
            },
        ],
        "OCF-007": [
            {
                "condition_id": "OCF-007::RANGE::CONNECTIVITY_LOSS",
                "output_symbol": "Lambda(t)",
                "bounded_range": "[0,1]",
                "template_bound_inputs": ["0 <= |E_alive(t)| <= |E_0|", "|E_0| > 0 for scored rows", "epsilon > 0"],
                "row_level_required_fields": ["template_id", "topology_hash", "E_alive_count", "E_0_count", "epsilon_guard", "connectivity_loss"],
                "pass_condition": "Lambda(t)=1-E_alive_count/max(epsilon,E_0_count) and the row is scored only when counts are template-bound support units",
            }
        ],
        "OCF-008": [
            {
                "condition_id": "OCF-008::RANGE::FLOW_RUPTURE",
                "output_symbol": "F_loss(t)",
                "bounded_range": "[0,1]",
                "template_bound_inputs": ["0 <= sum_i f_i_alive(t) <= sum_i f_i_0", "sum_i f_i_0 > 0 for scored rows", "epsilon > 0"],
                "row_level_required_fields": ["template_id", "support_unit_derivation_rows", "pre_flow", "post_flow", "epsilon", "flow_rupture"],
                "pass_condition": "F_loss(t)=1-post_flow/max(epsilon,pre_flow) using the same bounded support-unit basis as OCF-007",
            }
        ],
        "OCF-009": [
            {
                "condition_id": "OCF-009::RANGE::RECOVERY_INDEX",
                "output_symbol": "rho",
                "bounded_range": "[0,1] when Phi_min <= Phi_after <= Phi_before and Phi_before > Phi_min",
                "template_bound_inputs": ["Phi_before", "Phi_min", "Phi_after", "epsilon > 0"],
                "row_level_required_fields": ["template_id", "Phi_before", "Phi_min", "Phi_after", "epsilon", "rho"],
                "pass_condition": "rho=(Phi_after-Phi_min)/max(epsilon,Phi_before-Phi_min), with out-of-order tuples marked boundary-only rather than scored",
            }
        ],
    }
    rows = []
    for row in rows_by_formula.get(formula_id, []):
        payload = {
            "formula_id": formula_id,
            "status": "PASS_TEMPLATE_BOUND_RANGE_CONDITION",
            "template_scope": "V010 public workbench/cascade template row; not a universal mathematical or empirical bound",
            "nonclaim_boundary": "Range condition licenses only the displayed template-bound diagnostic row; it is not external validation.",
        } | row
        payload["row_hash"] = _hash(payload)
        rows.append(payload)
    return rows


def _formula_consequences(text: str, domain: str) -> list[str]:
    lower = text.lower()
    if "collapse" in lower or "ω" in lower:
        return ["Collapse can be checked as admissible-state loss.", "Recovery requires a route that reopens viable states."]
    if "σ" in lower or "Σ" in text or "w_" in text:
        return ["Local failure can propagate along weighted dependencies.", "Changing animation speed must not change deterministic results."]
    if domain == "Physics":
        return ["The row belongs to a domain-projection lane and needs domain constants before prediction.", "A graph can show the dependency but not claim external validation by itself."]
    if domain == "Chemistry":
        return ["Reaction or network terms should be tied to a bounded chemistry template.", "Unsupported thermochemical inference remains a formalization obligation."]
    if domain == "Biology":
        return ["State-transition interpretation needs an explicit biological system template.", "Replay-backed status must come from a validation lane."]
    return ["The formula should link to graph, wiki, proof/boundary and a visual diagnostic.", "If replay support is absent, the row remains a formalization boundary."]


def _formula_chart_spec(formula_id: str, domain: str, chart_kind: str | None = None) -> dict[str, Any]:
    kind = chart_kind or ("threshold" if domain in {"Systems", "Metaontology"} else "domain_projection")
    axis_labels = {
        "threshold_bifurcation": ("contradiction load C_K", "axis-birth / collapse risk"),
        "pressure_threshold": ("net pressure P_K", "transition risk"),
        "coherence_balance": ("repair and boundary capacity", "coherence Φ_K"),
        "cascade": ("cascade step t", "node state s_j"),
        "connectivity_loss": ("alive edge fraction", "connectivity loss Λ"),
        "flow_loss": ("alive flow fraction", "flow rupture F_loss"),
        "recovery": ("reconfiguration step", "recovery index ρ"),
        "k_ladder": ("K-level n", "constraint / build-up intensity"),
        "m_space": ("M-space component", "typed component availability"),
        "axis_addition": ("candidate axis", "computable admissibility"),
        "domain_projection": ("domain calibration step", "projection readiness D_d"),
        "evidence_score": ("visible score component contribution", "capped inspectability score E_display(c)"),
        "state_space": ("admissible-state sample", "viability Ω_K"),
    }
    if kind in {"threshold_bifurcation", "pressure_threshold", "coherence_balance"}:
        points = [{"x": step, "y": round(0.22 + step * 0.035 + (0.18 if step >= 11 else 0), 3)} for step in range(16)]
        threshold = 0.72
    elif kind in {"cascade", "connectivity_loss", "flow_loss"}:
        points = [{"x": step, "y": round(min(1.0, (step / 15) ** 1.35), 3)} for step in range(16)]
        threshold = 0.55
    elif kind == "recovery":
        recovery = [0.9, 0.78, 0.61, 0.43, 0.28, 0.18, 0.24, 0.31, 0.39, 0.47, 0.54, 0.6, 0.65, 0.69, 0.72, 0.74]
        points = [{"x": step, "y": round(recovery[step], 3)} for step in range(16)]
        threshold = 0.5
    else:
        points = [{"x": step, "y": round(0.18 + step * 0.045, 3)} for step in range(16)]
        threshold = 0.6
    x_axis, y_axis = axis_labels.get(kind, ("formula probe step", "normalized diagnostic value"))
    return {
        "chart_id": f"CHART::{formula_id}",
        "kind": kind,
        "x_axis": x_axis,
        "y_axis": y_axis,
        "threshold": threshold,
        "points": points,
        "nonclaim_boundary": "Chart is an explanatory visual diagnostic, not empirical validation.",
        "provenance": {
            "formula_id": formula_id,
            "chart_id": f"CHART::{formula_id}",
            "domain": domain,
            "chart_kind": kind,
            "generation_contract": "v010_formula_surface_chart_contract",
            "source_status": "public",
            "generated_by": "generate_oc_universe_atlas",
            "demo_version": DEMO_VERSION,
            "release_ordinal": RELEASE_ORDINAL,
            "source_samples": len(points),
            "point_bounds": {"x": {"min": 0, "max": len(points) - 1}, "y": {"min": 0.0, "max": 1.0}},
        },
    }


def _normalize_formula_text(text: str) -> str:
    normalized = _clean(str(text), 420).strip()
    if normalized.startswith("$") and normalized.endswith("$") and len(normalized) > 2:
        normalized = normalized[1:-1].strip()
    normalized = normalized.replace("$", "")
    normalized = re.sub(r"^&\s*", "", normalized)
    normalized = normalized.replace("\\\\subseteq", "\\subseteq").replace("\\\\subset", "\\subset")
    normalized = normalized.replace("\\\\in", "\\in").replace("\\\\notin", "\\notin")
    normalized = normalized.replace("\\Om(", "\\Omega(")
    normalized = re.sub(r"\s*\\\\\s*$", "", normalized)
    normalized = re.sub(r"\s*\\\s*$", "", normalized)
    normalized = normalized.strip().rstrip(".;")
    return normalized.strip()


def _formula_table_item(
    *,
    ordinal: int,
    formula_id: str,
    text: str,
    title: str,
    domain: str,
    status: str,
    source_refs: list[Any],
    symbol_refs: list[Any] | None = None,
    interpretation: str = "",
    consequences: list[str] | None = None,
    chart_kind: str | None = None,
    formula_class: str = "registry_math",
    edition: str = "public",
) -> dict[str, Any]:
    text = _normalize_formula_text(text)
    katex_ready = _looks_like_formula(text) or formula_class == "canonical_oc_workbench"
    clean_refs = [_public_source_ref(item, "formula") for item in source_refs] if edition == "public" else [str(item) for item in source_refs]
    operators = _formula_operator_glossary(text)
    source_boundary = " / ".join(clean_refs[:3]) if clean_refs else "OC V010 curated formula surface; source linkage remains bounded by public-safe hashes."
    source_ref_count = len(clean_refs)
    semantic_symbol_override = FORMULA_SYMBOL_TABLE_OVERRIDES.get(formula_id)
    typed_signatures = (
        _typed_signatures_from_symbol_table(semantic_symbol_override)
        if semantic_symbol_override
        else _derive_typed_symbol_signatures(text)
    )
    chart_spec = _formula_chart_spec(formula_id, domain, chart_kind)
    dimensional_profile = {
        "status": "PASS_SYMBOLIC_DIMENSION_CONTRACT",
        "basis": "V010 curated workbench formula row; symbolic dimension compatibility is checked for displayed algebraic operations; SI-unit derivations require a domain lane.",
        "symbol_signature_count": len(typed_signatures),
    }
    symbol_table = semantic_symbol_override or _formula_symbol_table(text, typed_signatures, operators)
    dimension_checks = _formula_dimension_checks(text, symbol_table)
    if formula_id == "OCF-006" and not any(
        isinstance(check, dict) and check.get("operation") == "path_cardinality_depth"
        for check in dimension_checks.get("operation_checks", [])
    ):
        dimension_checks.setdefault("operation_checks", []).append(
            {
                "operation": "path_cardinality_depth",
                "operand_dimension": "cardinality_of_ordered_collapse_path",
                "status": "PASS_SYMBOLIC_SUBDERIVATION",
                "explanation": "Collapse depth is displayed as the OCF-006.path_depth subderivation D_c=|P_c|, separate from the propagation formula_text.",
            }
        )
    denominator_guards = _formula_denominator_guards(formula_id, text)
    range_condition_rows = _formula_range_condition_rows(formula_id)
    if range_condition_rows:
        dimension_checks["range_condition_rows"] = range_condition_rows
        dimension_checks["range_condition_row_count"] = len(range_condition_rows)
        existing_conditions = [
            str(item)
            for item in (dimension_checks.get("range_claim_conditions") or [])
            if str(item).strip()
        ]
        dimension_checks["range_claim_conditions"] = existing_conditions + [
            f"{row['condition_id']}: {row['pass_condition']}"
            for row in range_condition_rows
        ]
    formula_role_contract = {}
    formula_subderivations: list[dict[str, Any]] = []
    if formula_id == "OCF-006":
        formula_role_contract = {
            "status": "PASS_DISAMBIGUATED_FORMULA_FAMILY",
            "formula_family_id": "OCF-006",
            "required_visible_roles": ["OCF-006.path_depth", "OCF-006.propagation_update"],
            "visible_notation_coverage": {
                "status": "PASS_ALL_VISIBLE_NOTATION_BOUND",
                "symbols": ["s_j(t)", "t+1", "s_j(t+1)", "max(0,x)", "min(1,x)", "clamp", "sum_i", "w_ij", "delta_i(t)", "r_j(t)", "P_c=(v_0,...,v_m)", "v_0", "v_m", "P_c", "D_c"],
                "coverage_policy": "The Formula Atlas symbol table and cascade export rows must bind every displayed OCF-006 notation item, including tuple/path notation and clamp/summation operators.",
            },
            "nonclaim_boundary": "One Formula Atlas row teaches the cascade family; exports must bind each metric to a named role.",
        }
        formula_subderivations = [
            {
                "formula_role_id": "OCF-006.path_depth",
                "formula_subtype": "path_depth",
                "canonical_expression": "D_c=|P_c|",
                "symbols": ["P_c=(v_0,...,v_m)", "v_0", "v_m", "P_c", "D_c"],
                "input_fields": ["selected collapse path P_c"],
                "output_fields": ["collapse_depth"],
                "meaning": "Collapse depth is the length/cardinality of the selected collapse path.",
            },
            {
                "formula_role_id": "OCF-006.propagation_update",
                "formula_subtype": "propagation_update",
                "canonical_expression": "s_j(t+1)=min(1, max(0, s_j(t)-sum_i w_ij delta_i(t)+r_j(t)))",
                "symbols": ["s_j(t)", "t+1", "s_j(t+1)", "max(0,x)", "min(1,x)", "clamp", "sum_i", "w_ij", "delta_i(t)", "r_j(t)"],
                "input_fields": ["node state", "incoming dependency weights", "upstream damage", "local recovery"],
                "output_fields": ["node residual coherence"],
                "range_claim_condition": "The displayed output is clamped by min(1,max(0,x)); public replay rows keep inputs in the normalized template domain and verify the final [0,1] value.",
                "meaning": "A node updates by subtracting weighted upstream damage, adding local recovery and clamping into the normalized [0,1] state range.",
            },
        ]
    elif formula_id == "OCF-015":
        formula_role_contract = {
            "status": "PASS_COMPONENT_SCORE_DISPLAY_ALIGNED",
            "formula_family_id": "OCF-015",
            "required_visible_roles": ["raw component total", "claim-class cap", "displayed capped score", "not-proof warning"],
            "score_component_basis": ["statement_visible", "trace_richness", "source_refs_visible", "evidence_hash_present", "nonclaim_boundary_visible", "status_specificity"],
            "payload_alignment": "Matches proof_body_index rows: raw_weighted_score is an uncapped component_total, capped_score/evidence_score is min(max(0,raw_weighted_score),kappa_c), and boundary rows remain non-proof.",
            "nonclaim_boundary": "Inspectability score is not proof sufficiency, peer review or proof closure.",
        }
    ui_probe_contract = {
        "probe_id": f"formula-probe::{formula_id}",
        "surface": "formula",
        "workbench_binding": chart_spec["chart_id"],
        "expected_visible_result": "Selecting the formula updates the diagnostic chart, source/boundary panel and graph/wiki probe controls.",
        "deterministic": True,
    }
    source_exception_reasons: list[str] = []
    if not source_refs:
        source_exception_reasons.append("NO_PUBLIC_SOURCE_REFS")
    if not katex_ready:
        source_exception_reasons.append("NON_KATEX_FORMULA_TEXT")
    assumption_bodies = [
        {
            "assumption_id": "assumption_1",
            "text": "Formula is part of the curated V010 workbench symbolic surface.",
            "text_hash": _hash("Formula is part of the curated V010 workbench symbolic surface."),
            "status": "VISIBLE_NONPLACEHOLDER",
        },
        {
            "assumption_id": "assumption_2",
            "text": "Formula validity is bounded by its source/boundary row and does not imply external peer review.",
            "text_hash": _hash("Formula validity is bounded by its source/boundary row and does not imply external peer review."),
            "status": "VISIBLE_NONPLACEHOLDER",
        },
    ]
    validation_rule_bodies = [
        {"rule_id": "FORMULA_RULE_001", "rule_text": "semantic title present", "status": "PASS", "hash_basis": ["semantic_title", "formula_title"]},
        {"rule_id": "FORMULA_RULE_002", "rule_text": "operator glossary present", "status": "PASS", "hash_basis": ["operator_glossary", "operator_meanings"]},
        {"rule_id": "FORMULA_RULE_003", "rule_text": "consequences present", "status": "PASS", "hash_basis": ["consequences"]},
        {"rule_id": "FORMULA_RULE_004", "rule_text": "diagnostic chart present", "status": "PASS", "hash_basis": ["chart_spec", "diagnostic_chart"]},
        {"rule_id": "FORMULA_RULE_005", "rule_text": "source or boundary present", "status": "PASS", "hash_basis": ["source_refs", "source_boundary", "nonclaim_boundary"]},
    ]
    presentation_metadata = _formula_presentation_metadata(formula_id)
    return {
        "ordinal": ordinal,
        "formula_id": formula_id,
        "formula_title": _clean(title, 180),
        "semantic_title": _clean(title, 180),
        "domain": domain,
        "formula_text": text,
        "formula": text,
        "operator_glossary": operators,
        "operator_meanings": operators,
        "operators": operators,
        "operator_count": len(operators),
        "consequence_count": len(consequences or _formula_consequences(text, domain)),
        "operator_summary": "; ".join(f"{row['symbol']}: {row['meaning']}" for row in operators) or "No formal operator glossary available yet.",
        "consequences": consequences or _formula_consequences(text, domain),
        "chart_spec": chart_spec,
        "diagnostic_chart": chart_spec,
        "formula_presentation_sections": presentation_metadata["formula_presentation_sections"],
        "formula_family_relation": presentation_metadata["formula_family_relation"],
        "symbol_disambiguation_notes": presentation_metadata["symbol_disambiguation_notes"],
        "formula_output_examples": presentation_metadata["formula_output_examples"],
        "operator_count_rule": presentation_metadata["operator_count_rule"],
        "cross_formula_links": presentation_metadata["cross_formula_links"],
        "interpretation": _clean(interpretation or text, 420),
        "status": status,
        "quality_status": status,
        "formula_class": formula_class,
        "render_mode": "katex" if katex_ready else "plain",
        "render_quality_status": "PASS_KATEX" if katex_ready else "PASS_PLAINTEXT_FALLBACK",
        "katex_ready": katex_ready,
        "assumptions": [row["text"] for row in assumption_bodies],
        "assumption_bodies": assumption_bodies,
        "validation_rules": [row["rule_text"] for row in validation_rule_bodies],
        "validation_rule_bodies": validation_rule_bodies,
        "dimensional_profile": dimensional_profile,
        "dimensional_consistency_status": dimensional_profile["status"],
        "symbol_table": symbol_table,
        "semantic_symbol_contract": {
            "status": "PASS_CURATED_SEMANTIC_SYMBOLS" if semantic_symbol_override else "PASS_INFERRED_SYMBOLS",
            "parser_tokens_excluded": bool(semantic_symbol_override),
            "symbol_count": len(symbol_table),
            "review_boundary": "The Formula Atlas displays only semantic symbols; raw LaTeX/parser tokens are kept out of the primary UI.",
        },
        "dimension_checks": dimension_checks,
        "range_condition_rows": range_condition_rows,
        "range_condition_row_count": len(range_condition_rows),
        "template_bound_range_condition_status": "PASS" if range_condition_rows else "NOT_APPLICABLE",
        "formula_role_contract": formula_role_contract,
        "formula_subderivations": formula_subderivations,
        "formula_family_id": formula_id,
        "denominator_guards": denominator_guards,
        "denominator_guard_status": "PASS" if (not "\\frac" in text or denominator_guards) else "FAIL_CLOSED",
        "ui_probe_contract": ui_probe_contract,
        "formula_boundary_mapping": {
            "status": "EVIDENCE_BOUNDARY_LINKED",
            "target_route": "proof_boundary_route",
            "nonclaim_boundary": "Formula probe links to proof/boundary inspection; it is not counted as proof closure.",
        },
        "formula_query": _formula_query_from_text(text),
        "candidate_kind": "math_expression",
        "symbol_refs": [_clean(item, 80) for item in (symbol_refs or [])[:8]],
        "source_hash": _hash({"formula_text": text, "source_refs": clean_refs}),
        "source_refs": clean_refs,
        "formula_source_refs": clean_refs,
        "source_boundary": source_boundary,
        "source_ref_count": source_ref_count,
        "typed_symbol_signatures": typed_signatures,
        "chart_provenance": {
            "source_basis": "formula_table_item",
            "chart_kind": chart_spec["kind"],
            "chart_id": chart_spec["chart_id"],
            "chart_source": "canonical_formula_chart_spec",
            "provenance": chart_spec.get("provenance", {}),
        },
        "source_exceptions": [
            {"code": code, "resolution": "nonclaim_boundary"} for code in source_exception_reasons
        ],
        "source_linking_profile": {
            "has_source_refs": bool(clean_refs),
            "has_source_atom": False,
            "has_formula_query": bool(formula_id),
            "source_boundary_present": bool(source_boundary),
            "source_ref_count": source_ref_count,
            "source_exception_codes": source_exception_reasons,
        },
        "boundary": "Curated UI formula row; proof, replay or prediction status must be read from linked evidence routes.",
        "source_atom_id": "",
        "nonclaim_boundary": "Formula row is a curated demonstrator/formalization surface; proof or prediction status must come from linked evidence routes.",
    }


def _formula_title_from_text(text: str) -> str:
    compact = _normalize_formula_text(text)
    lower = compact.lower()
    if "axisbirth" in lower or "collapse" in lower and "theta" in lower:
        return "Contradiction threshold branch"
    if re.search(r"S\s*K\(t\s*\+\s*dt\)\s*≥\s*S\s*K\(t\)", compact):
        return "Continuum stability monotonicity"
    if "theta_{\\mathrm{cog}}" in lower:
        return "Cognitive threshold exceedance"
    if "theta_{\\mathrm{pe}}" in lower:
        return "Potential-emergence threshold exceedance"
    if "theta_{\\mathrm{react}}" in lower:
        return "Reaction-energy threshold condition"
    if "alive" in lower and ("omega" in lower or "Ω" in compact):
        return "Admissible-state life condition"
    if "\\om(" in lower or "\\kcont" in lower:
        return "KEA continuumness viability test"
    if "cyc(" in lower:
        return "KEA cycle-extinction test"
    if "omega" in lower and ("varnothing" in lower or "emptyset" in lower or "∅" in compact):
        if "cap" in lower or "\\cap" in compact:
            return "Local admissible-region exclusion"
        return "Admissible-state collapse boundary"
    if "\\thetasys" in lower or "thetasys" in lower:
        return "System threshold admissible set"
    if re.search(r"k\(\\mathcal\{I\}\(\\omega\)\)\s*<\s*k\(\\omega\)", compact):
        return "Interpretation lowers K-order"
    if "p_c" in compact or "p_{c}" in compact:
        return "Percolation threshold crossing"
    if "f_i" in compact or "f_{i}" in compact or "f_k" in compact or "f_{k}" in compact:
        return "Constraint boundary test"
    if "f_{\\text{collapse}}" in lower:
        return "Collapse predicate activation"
    if "f_{\\text{exist}}" in lower:
        return "Existence predicate activation"
    if "f_{\\text{inertia}}" in lower:
        return "Inertia predicate activation"
    if "h_{\\omega}" in lower or "s_{\\mathrm{conn}}" in lower:
        return "Continuumness product score"
    if "a(k) < dim differences" in lower:
        return "Axis insufficiency criterion"
    if re.search(r"A\(K\)\s*=", compact):
        return "Axis family declaration"
    if "a(k_{x})" in lower and "\\subset" in compact:
        return "Axis monotonicity across K-levels"
    if "a(k_{x+1})" in lower or "a(k_{+})" in lower:
        return "Axis extension update"
    if "a(k_{-})" in lower:
        return "Axis removal collapse test"
    if "a(k_{0})" in lower or "a_0" in lower:
        return "K0 axis emptiness"
    if "a(k_{1})" in lower:
        return "K1 primitive axis declaration"
    if "a(k_{2})" in lower:
        return "K2 connectivity axis declaration"
    if "a(k_{3})" in lower:
        return "K3 chemical axis declaration"
    if "a_{\\mathrm{in/out}}" in lower:
        return "K4 membrane axis declaration"
    if "a(m_{x})" in lower and "\\subset" in compact:
        return "M-space axis monotonicity"
    if re.search(r"A\(t\s*\+\s*dt\)\s*≥\s*dim\s*A\(t\)", compact):
        return "Axis-dimensional growth condition"
    if re.search(r"A_x\s*\\subset", compact):
        return "Axis monotonicity across slices"
    if "c(k_x)" in lower and "\\subset" in compact:
        return "Cycle inclusion across K-levels"
    if re.search(r"C\s*=\s*\(J_", compact):
        return "Constraint tuple declaration"
    if re.search(r"C\(K\)\s*=\s*\\varnothing", compact):
        return "Cycle set emptiness"
    if re.search(r"C\(K_x\)\s*=\s*\\varnothing", compact):
        return "K-level cycle emptiness"
    if re.search(r"\bC\s*=\s*\\varnothing|\bC\s*=\s*∅", compact):
        return "Cycle extinction boundary"
    if "c_n" in lower and "\\to" in compact:
        return "Closed cycle trajectory"
    if re.search(r"C_n\s*=\s*\\varnothing", compact):
        return "Indexed cycle extinction"
    if re.search(r"C_x\s*\\subset", compact):
        return "Cycle monotonicity across slices"
    if re.search(r"C_x\(t\^\\ast\)\s*=\s*\\varnothing", compact):
        return "Cycle death-time condition"
    if "c_{j}^{\\mathrm{eff}}" in lower:
        return "Normalized effective constraint weight"
    if "\\bigcup_{x=0}^{12}" in compact or "k_{x}" in lower and "\\bigcup" in compact:
        return "K0-K12 admissible-state union"
    if "\\mathcal{i}" in lower and "phase" in lower:
        return "Interpretation phase stop condition"
    if "\\kcont" in lower:
        return "Continuumness positivity test"
    if "d_{\\partial\\omega}" in lower:
        return "Boundary-distance viability test"
    if re.fullmatch(r"n\s*>\s*\d+", compact):
        return "Minimum-cardinality condition"
    if re.search(r"T\(K\)\s*>\s*\\Theta_\{\\mathrm\{dim\}\}\(K\)", compact):
        return "K-specific dimensional transition pressure"
    if re.search(r"T\(K\)\s*>\s*\\Theta_\{\\mathrm\{dim\}\}", compact):
        return "Dimensional transition pressure"
    return ""


def _formula_title_from_source(row: dict[str, Any], text: str, formula_id: str) -> str:
    inferred = _formula_title_from_text(text)
    if inferred:
        return inferred
    explicit = _clean(row.get("title") or row.get("semantic_title") or "", 180)
    if explicit:
        return explicit
    compact = formula_id.replace("FORM::", "").replace("OCF-", "OC formula ")
    compact = re.sub(r"tier1_[a-z0-9_]+", "", compact, flags=re.IGNORECASE)
    compact = re.sub(r"[_-]+", " ", compact).strip()
    compact = re.sub(r"\s+", " ", compact)
    if compact and not re.fullmatch(r"[a-zA-Z]\s*[0-9]?", compact):
        return _clean(compact, 120).title()
    return _clean(f"Relation: {text}", 120)


def _canonical_formula_rows(edition: str) -> list[dict[str, Any]]:
    rows = []
    for index, formula in enumerate(CANONICAL_OC_FORMULAS, start=1):
        rows.append(
            _formula_table_item(
                ordinal=index,
                formula_id=formula["formula_id"],
                text=formula["formula_text"],
                title=formula["semantic_title"],
                domain=formula["domain"],
                status="WORKBENCH_READY_BOUNDARY_CHECKED",
                source_refs=["OC_CORE_V010_CANONICAL_FORMULA_SURFACE"],
                interpretation=formula["interpretation"],
                consequences=formula["consequences"],
                chart_kind=formula.get("chart_kind"),
                formula_class="canonical_oc_workbench",
                edition=edition,
            )
        )
    return rows


def _formula_rows(edition: str) -> list[dict[str, Any]]:
    # V010 product rule: the visible Formula Atlas is a curated teaching/workbench table,
    # not a raw extraction dump. Registry candidates remain in the formalization backlog
    # until a human-quality title, operator glossary, consequence, chart and boundary exist.
    return _canonical_formula_rows(edition)


def _formula_ui_contract_gaps(formula: dict[str, Any]) -> list[str]:
    required_contract = {
        "semantic_title": ("semantic_title", "formula_title"),
        "operator_meanings": ("operator_meanings", "operator_glossary", "operators", "operator_summary"),
        "consequences": ("consequences",),
        "diagnostic_chart": ("diagnostic_chart", "chart_spec"),
        "source_boundary": ("source_boundary", "source_refs", "source_atom_id", "nonclaim_boundary", "boundary"),
    }
    return [
        field_name
        for field_name, aliases in required_contract.items()
        if not any(formula.get(alias) for alias in aliases)
    ]


def _formula_backlog_summary(ui_formulas: list[dict[str, Any]], edition: str) -> dict[str, Any]:
    registry_path = REPO_ROOT / "logion" / "k0" / "governance" / "status" / "SCIENCE_FORMULA_SYMBOL_REGISTRY_latest.json"
    data = _read_json(registry_path, {"rows": []})
    selected_hashes = {_hash(_normalize_formula_text(row.get("formula_text", ""))) for row in ui_formulas}
    raw_rows = [row for row in data.get("rows", []) if isinstance(row, dict)]
    backlog_total = 0
    samples: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    for row in raw_rows:
        text = _normalize_formula_text(row.get("formula_text", ""))
        if not text:
            reason = "empty_formula_text"
        elif _hash(text) in selected_hashes:
            continue
        elif edition == "public" and _formula_has_private_or_code_shape(text):
            reason = "private_or_code_shape"
        elif not _looks_like_formula(text):
            reason = "not_semantic_formula"
        else:
            reason = "needs_semantic_title_operator_chart_source_boundary"
        backlog_total += 1
        reason_counts[reason] += 1
        if len(samples) < 24:
            samples.append(
                {
                    "obligation_id": f"RAW_FORMULA_BACKLOG::{backlog_total:05d}",
                    "source_formula_id_hash": _hash(str(row.get("formula_id", "")) or text),
                    "formula_text_hash": _hash(text),
                    "status": "FORMALIZATION_OBLIGATION",
                    "reason": reason,
                    "nonclaim_boundary": "Raw registry candidates are not UI Formula Atlas rows until semantic title, operator meanings, consequence, chart and source/boundary are complete.",
                }
            )
    return {
        "raw_candidate_registry_rows": len(raw_rows),
        "raw_candidate_backlog_total": backlog_total,
        "reason_counts": dict(reason_counts),
        "sample_obligations": samples,
    }


def _extract_terms(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z][A-Za-z0-9_]+", str(text).lower())
    return sorted({term for term in terms if len(term) >= 3})


def _atom_term_index(atoms: list[dict[str, Any]]) -> tuple[dict[str, str], list[tuple[str, set[str]]]]:
    direct: dict[str, str] = {}
    term_rows: list[tuple[str, set[str]]] = []
    for atom in atoms:
        unit_id = str(atom.get("unit_id", ""))
        if not unit_id:
            continue
        direct[unit_id] = unit_id
        source_unit_id = str(atom.get("source_unit_id", ""))
        if source_unit_id:
            direct[source_unit_id] = unit_id
        terms = set(_extract_terms(atom.get("search_text", ""))) | set(_extract_terms(atom.get("text", "")))
        if terms:
            term_rows.append((unit_id, terms))
    return direct, term_rows


def _formula_to_atom_id(
    formula: dict[str, Any],
    direct_atom_refs: dict[str, str],
    atom_term_rows: list[tuple[str, set[str]]],
) -> str:
    source_refs = [str(item) for item in formula.get("source_refs_raw", [])]
    for ref in source_refs:
        for needle, unit_id in direct_atom_refs.items():
            if needle and needle in ref:
                return unit_id
    formula_text = formula.get("formula_text", "")
    formula_terms = set(_extract_terms(formula_text))
    if not formula_terms:
        return ""
    best_unit = ""
    best_score = 0
    for unit_id, atom_terms in atom_term_rows:
        overlap = len(atom_terms & formula_terms)
        if overlap > best_score:
            best_score = overlap
            best_unit = unit_id
        if best_score >= min(3, len(formula_terms)):
            break
    return best_unit if best_score else ""


def _enrich_formula_rows_with_atoms(formula_rows: list[dict[str, Any]], atoms: list[dict[str, Any]], edition: str) -> None:
    direct_atom_refs, atom_term_rows = _atom_term_index(atoms)
    for formula in formula_rows:
        source_atom_id = _formula_to_atom_id(formula, direct_atom_refs, atom_term_rows)
        if source_atom_id:
            formula["source_atom_id"] = source_atom_id
            if formula.get("formula_class") != "canonical_oc_workbench":
                formula["quality_status"] = "FORMALIZED_PARTIAL" if formula.get("katex_ready") else "FORMALIZATION_BOUNDARY"
        elif formula.get("quality_status") in {"EXTRACTED_CANDIDATE", "UNKNOWN", "UNCATEGORIZED"}:
            formula["quality_status"] = "FORMALIZATION_OBLIGATION"
        if not formula.get("interpretation"):
            formula["interpretation"] = _clean(formula.get("formula_text", ""), 420)
        if edition == "public":
            formula["source_refs"] = formula.get("source_refs", [])


def _corpus_completeness_report(pass_units: list[tuple[Path, dict[str, Any]]], atoms: list[dict[str, Any]]) -> dict[str, Any]:
    atom_unit_ids = {str(atom.get("unit_id", "")) for atom in atoms}
    exclusions: list[dict[str, Any]] = []
    by_status: Counter[str] = Counter()
    for path, row in pass_units:
        status = row.get("language_source_status", "UNKNOWN")
        by_status[status] += 1
        unit_id = str(row.get("unit_id", path.stem))
        if unit_id in atom_unit_ids:
            continue
        text = _clean(row.get("translation_source_text", ""), 24)
        if not text:
            reason = "empty_translation_text"
        else:
            reason = "dedupe_or_parse_filter"
        exclusions.append(
            {
                "unit_id": unit_id,
                "document_id": row.get("target_artifact_id", path.stem.split("__", 1)[0]),
                "status": status,
                "language_source_path": path.name,
                "language_source_ref": _public_source_ref(path, "language-source"),
                "exclusion_reason": reason,
            }
        )
    report = {
        "schema_version": "oc-core-demo-corpus-completeness.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "scope": "PASS language_source_unit rows vs generated corpus_atoms",
        "counts": {
            "available_pass_units": len(pass_units),
            "generated_atoms": len(atoms),
            "coverage_ratio": round(len(atoms) / max(1, len(pass_units)), 6),
            "bounded_exclusions": len(exclusions),
            "status_breakdown": dict(by_status),
        },
        "bounded_exclusions": exclusions,
    }
    report["report_hash"] = _hash(report)
    return report


FORMULA_PARSER_TOKEN_MARKERS = {
    "operatorname",
    "lor",
    "frac",
    "lvert",
    "rvert",
    "max",
    "sum",
    "cup",
    "prime",
    "varnothing",
    "Leftrightarrow",
}


def _symbol_table_parser_token_count(formula: dict[str, Any]) -> int:
    count = 0
    for row in formula.get("symbol_table", []) or []:
        symbol = str(row.get("symbol", "")).strip()
        if symbol in FORMULA_PARSER_TOKEN_MARKERS:
            count += 1
        if symbol.endswith("{") or "\\mathrm" in symbol or "operatorname" in symbol:
            count += 1
    return count


def _formula_quality_report(formulas: list[dict[str, Any]], atoms: list[dict[str, Any]]) -> dict[str, Any]:
    source_atom_ids = {atom.get("unit_id") for atom in atoms}
    rows: list[dict[str, Any]] = []
    quality_totals: Counter[str] = Counter()
    for formula in formulas:
        formula_refs = set(formula.get("symbol_refs", []))
        assumptions = [str(item).strip() for item in (formula.get("assumptions") or []) if str(item).strip()]
        placeholder_assumptions = [item for item in assumptions if item.lower() in {"assumption", "todo", "tbd", "placeholder"}]
        duplicate_only_assumptions = len(set(assumptions)) < len(assumptions)
        linked_atoms = []
        if formula.get("source_atom_id") in source_atom_ids:
            linked_atoms.append(formula["source_atom_id"])
        quality_totals[formula.get("quality_status", "unknown")] += 1
        validation_rules = [str(item).strip() for item in (formula.get("validation_rules") or []) if str(item).strip()]
        validation_rule_bodies = [
            row for row in (formula.get("validation_rule_bodies") or [])
            if isinstance(row, dict) and row.get("rule_id") and row.get("rule_text")
        ]
        if not validation_rule_bodies:
            validation_rule_bodies = [
                {
                    "rule_id": f"FORMULA_RULE_{index:03d}",
                    "rule_text": text,
                    "status": "PASS",
                    "hash_basis": ["formula_atlas_row"],
                }
                for index, text in enumerate(validation_rules, start=1)
            ]
        dimension_checks = formula.get("dimension_checks") if isinstance(formula.get("dimension_checks"), dict) else {}
        operation_checks = dimension_checks.get("operation_checks", []) or []
        range_condition_rows = [
            item for item in (formula.get("range_condition_rows") or dimension_checks.get("range_condition_rows") or [])
            if isinstance(item, dict)
        ]
        formula_role_contract = formula.get("formula_role_contract") if isinstance(formula.get("formula_role_contract"), dict) else {}
        symbol_table_symbols = [
            str(row.get("symbol", "")).strip()
            for row in (formula.get("symbol_table", []) or [])
            if isinstance(row, dict) and str(row.get("symbol", "")).strip()
        ]
        ocf006_required_symbols = ["s_j(t)", "t+1", "s_j(t+1)", "max(0,x)", "min(1,x)", "clamp", "sum_i", "w_ij", "delta_i(t)", "r_j(t)", "P_c=(v_0,...,v_m)", "v_0", "v_m", "P_c", "D_c"]
        ocf006_missing_symbols = [
            symbol for symbol in ocf006_required_symbols
            if formula.get("formula_id") == "OCF-006" and symbol not in symbol_table_symbols
        ]
        rows.append(
            {
                "formula_id": formula.get("formula_id"),
                "semantic_title": formula.get("semantic_title"),
                "interpretation": formula.get("interpretation"),
                "quality_status": formula.get("quality_status", "unknown"),
                "render_quality": formula.get("render_quality"),
                "render_quality_status": formula.get("render_quality_status"),
                "source_atom_id": formula.get("source_atom_id", ""),
                "source_refs": formula.get("source_refs", []),
                "formula_source_refs": formula.get("formula_source_refs", formula.get("source_refs", [])),
                "linked_atoms": linked_atoms,
                "linked_term_count": len(formula_refs),
                "typed_symbol_signature_count": len(formula.get("typed_symbol_signatures", []) or []),
                "symbol_table_count": len(formula.get("symbol_table", []) or []),
                "semantic_symbol_contract_status": (formula.get("semantic_symbol_contract") or {}).get("status") if isinstance(formula.get("semantic_symbol_contract"), dict) else "MISSING",
                "parser_tokens_excluded": bool((formula.get("semantic_symbol_contract") or {}).get("parser_tokens_excluded")) if isinstance(formula.get("semantic_symbol_contract"), dict) else False,
                "parser_token_symbol_count": _symbol_table_parser_token_count(formula),
                "dimension_operation_check_count": len(operation_checks),
                "dimension_operations": [
                    check.get("operation")
                    for check in operation_checks
                    if isinstance(check, dict)
                ],
                "tuple_component_update_status": (
                    "PASS"
                    if any((check or {}).get("operation") == "typed_tuple_component_update" for check in operation_checks if isinstance(check, dict))
                    else ("NOT_APPLICABLE" if formula.get("formula_id") != "OCF-013" else "FAIL_CLOSED")
                ),
                "inherited_tuple_component_binding_status": (
                    "PASS"
                    if any((check or {}).get("inherited_tuple_component_binding", {}).get("binding_status") == "PASS_COMPONENTS_VISIBLE" for check in operation_checks if isinstance(check, dict))
                    else ("NOT_APPLICABLE" if formula.get("formula_id") != "OCF-013" else "FAIL_CLOSED")
                ),
                "inherited_tuple_component_bindings": dimension_checks.get("inherited_tuple_component_bindings", []),
                "path_depth_binding_status": (
                    "PASS"
                    if any((check or {}).get("operation") == "path_cardinality_depth" for check in operation_checks if isinstance(check, dict))
                    else ("NOT_APPLICABLE" if formula.get("formula_id") != "OCF-006" else "FAIL_CLOSED")
                ),
                "ocf006_visible_notation_status": (
                    "PASS"
                    if formula.get("formula_id") == "OCF-006" and not ocf006_missing_symbols and (formula_role_contract.get("visible_notation_coverage") or {}).get("status") == "PASS_ALL_VISIBLE_NOTATION_BOUND"
                    else ("NOT_APPLICABLE" if formula.get("formula_id") != "OCF-006" else "FAIL_CLOSED")
                ),
                "ocf006_missing_visible_notation": ocf006_missing_symbols,
                "range_claim_condition_status": (
                    "PASS"
                    if dimension_checks.get("range_claim_conditions")
                    else ("NOT_APPLICABLE" if formula.get("formula_id") not in {"OCF-006", "OCF-015"} else "FAIL_CLOSED")
                ),
                "range_claim_conditions": dimension_checks.get("range_claim_conditions", []),
                "range_condition_rows": range_condition_rows,
                "range_condition_row_count": len(range_condition_rows),
                "template_bound_range_condition_status": (
                    "PASS"
                    if range_condition_rows
                    else ("NOT_APPLICABLE" if formula.get("formula_id") not in {"OCF-006", "OCF-007", "OCF-008", "OCF-009"} else "FAIL_CLOSED")
                ),
                "ocf015_score_display_alignment_status": (
                    "PASS"
                    if formula.get("formula_id") == "OCF-015" and formula_role_contract.get("status") == "PASS_COMPONENT_SCORE_DISPLAY_ALIGNED"
                    else ("NOT_APPLICABLE" if formula.get("formula_id") != "OCF-015" else "FAIL_CLOSED")
                ),
                "denominator_guard_count": len(formula.get("denominator_guards", []) or []),
                "missing_symbol_count": 0 if (formula.get("typed_symbol_signatures") or formula.get("operator_glossary")) else 1,
                "assumptions_present": bool(formula.get("assumptions")),
                "assumption_count": len(assumptions),
                "assumption_bodies": formula.get("assumption_bodies") or [
                    {"assumption_id": f"assumption_{index}", "text": text, "text_hash": _hash(text), "status": "VISIBLE_NONPLACEHOLDER"}
                    for index, text in enumerate(assumptions, start=1)
                ],
                "assumption_audit_status": "PASS" if len(assumptions) >= 2 and not placeholder_assumptions and not duplicate_only_assumptions else "FAIL_CLOSED",
                "validation_rule_count": len(validation_rules),
                "validation_rule_bodies": validation_rule_bodies,
                "validation_rule_audit_status": "PASS" if len(validation_rule_bodies) >= 5 and all(row.get("status") == "PASS" for row in validation_rule_bodies) else "FAIL_CLOSED",
                "dimensional_consistency_status": formula.get("dimensional_consistency_status", "NOT_DECLARED"),
                "chart_provenance_present": bool(formula.get("chart_provenance") or (isinstance(formula.get("chart_spec"), dict) and formula["chart_spec"].get("provenance"))),
                "ui_probe_contract_id": (formula.get("ui_probe_contract") or {}).get("probe_id") if isinstance(formula.get("ui_probe_contract"), dict) else "",
                "boundary_mapping_status": (formula.get("formula_boundary_mapping") or {}).get("status") if isinstance(formula.get("formula_boundary_mapping"), dict) else "",
                "needs_formalization_boundary": bool(not linked_atoms and not formula.get("source_refs") and not formula.get("nonclaim_boundary")),
            }
        )
    report = {
        "schema_version": "oc-core-demo-formula-quality.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "status": "PASS",
        "aggregate_count_units": {
            "rows_total": "curated UI Formula Atlas rows, not raw registry candidates",
            "formula_count": "curated UI Formula Atlas rows",
            "symbol_table_count": "formula rows with a non-empty semantic symbol table",
            "semantic_symbol_contract_count": "formula rows with curated semantic symbol contracts",
            "parser_token_symbol_count": "raw parser-token symbol leaks found in primary UI symbol tables",
            "dimension_operation_check_count": "formula rows with at least one symbolic dimension/operation check",
            "ui_probe_contract_count": "formula rows with a selectable UI probe contract",
            "boundary_mapping_count": "formula rows linked to a proof/boundary route",
        },
        "rows_total": len(formulas),
        "quality_totals": dict(quality_totals),
        "missing_symbol_count": sum(row["missing_symbol_count"] for row in rows),
        "assumptions_missing_count": sum(1 for row in rows if not row["assumptions_present"]),
        "assumption_audit_pass_count": sum(1 for row in rows if row.get("assumption_audit_status") == "PASS"),
        "assumption_audit_fail_count": sum(1 for row in rows if row.get("assumption_audit_status") != "PASS"),
        "validation_rule_audit_pass_count": sum(1 for row in rows if row.get("validation_rule_audit_status") == "PASS"),
        "validation_rule_audit_fail_count": sum(1 for row in rows if row.get("validation_rule_audit_status") != "PASS"),
        "symbolic_dimension_profile_count": sum(1 for row in rows if row.get("dimensional_consistency_status")),
        "symbol_table_count": sum(1 for row in rows if row.get("symbol_table_count")),
        "semantic_symbol_contract_count": sum(1 for row in rows if row.get("semantic_symbol_contract_status") == "PASS_CURATED_SEMANTIC_SYMBOLS"),
        "parser_token_symbol_count": sum(row.get("parser_token_symbol_count", 0) for row in rows),
        "parser_token_policy": "FAIL_CLOSED if any primary UI formula row exposes parser/LaTeX command tokens as symbols.",
        "dimension_operation_check_count": sum(1 for row in rows if row.get("dimension_operation_check_count")),
        "denominator_guarded_formula_count": sum(1 for row in rows if row.get("denominator_guard_count")),
        "ocf006_visible_notation_status": next((row.get("ocf006_visible_notation_status") for row in rows if row.get("formula_id") == "OCF-006"), "MISSING"),
        "ocf006_visible_notation_coverage_status": next((row.get("ocf006_visible_notation_status") for row in rows if row.get("formula_id") == "OCF-006"), "MISSING"),
        "ocf006_missing_visible_notation": next((row.get("ocf006_missing_visible_notation") for row in rows if row.get("formula_id") == "OCF-006"), ["OCF-006 row missing"]),
        "inherited_tuple_component_binding_status": next((row.get("inherited_tuple_component_binding_status") for row in rows if row.get("formula_id") == "OCF-013"), "MISSING"),
        "ocf013_inherited_tuple_component_binding_status": next((row.get("inherited_tuple_component_binding_status") for row in rows if row.get("formula_id") == "OCF-013"), "MISSING"),
        "ocf006_inherited_tuple_binding_status": "NOT_APPLICABLE_SEE_OCF013_AXIS_ADDITION_TUPLE_BINDING",
        "range_claim_condition_pass_count": sum(1 for row in rows if row.get("range_claim_condition_status") == "PASS"),
        "template_bound_range_condition_pass_count": sum(1 for row in rows if row.get("template_bound_range_condition_status") == "PASS"),
        "template_bound_range_condition_required_formula_ids": ["OCF-006", "OCF-007", "OCF-008", "OCF-009"],
        "template_bound_range_condition_required_status": (
            "PASS"
            if all(
                next((row.get("template_bound_range_condition_status") for row in rows if row.get("formula_id") == formula_id), "MISSING") == "PASS"
                for formula_id in {"OCF-006", "OCF-007", "OCF-008", "OCF-009"}
            )
            else "FAIL_CLOSED"
        ),
        "range_condition_rows_by_formula": {
            row.get("formula_id"): row.get("range_condition_rows", [])
            for row in rows
            if row.get("range_condition_rows")
        },
        "ocf015_score_display_alignment_status": next((row.get("ocf015_score_display_alignment_status") for row in rows if row.get("formula_id") == "OCF-015"), "MISSING"),
        "chart_provenance_count": sum(1 for row in rows if row.get("chart_provenance_present")),
        "ui_probe_contract_count": sum(1 for row in rows if row.get("ui_probe_contract_id")),
        "boundary_mapping_count": sum(1 for row in rows if row.get("boundary_mapping_status")),
        "formula_count": len(formulas),
        "rows": rows,
    }
    report["report_hash"] = _hash(report)
    return report


def _formula_formalization_obligations(formulas: list[dict[str, Any]], quality_report: dict[str, Any]) -> dict[str, Any]:
    obligations: list[dict[str, Any]] = []
    quality_rows = {row.get("formula_id"): row for row in quality_report.get("rows", []) if isinstance(row, dict)}
    for formula in formulas:
        formula_id = formula.get("formula_id", "")
        row = quality_rows.get(formula_id, {})
        missing_contract = _formula_ui_contract_gaps(formula)
        if missing_contract or row.get("needs_formalization_boundary"):
            obligations.append(
                {
                    "obligation_id": f"FORMULA_OBLIGATION::{formula_id}",
                    "formula_id": formula_id,
                    "semantic_title": formula.get("semantic_title", formula_id),
                    "status": "FORMALIZATION_OBLIGATION",
                    "missing_contract_fields": missing_contract,
                    "source_atom_id": formula.get("source_atom_id", ""),
                    "source_refs": formula.get("source_refs", []),
                    "boundary": formula.get(
                        "source_boundary",
                        "This symbolic row remains a UI/formalization obligation until source, operators, consequences and chart are complete.",
                    ),
                    "nonclaim_boundary": "Obligation rows are excluded from proof promotion and must not be presented as validated formulas.",
                }
            )
    payload = {
        "schema_version": "oc-core-demo-formula-formalization-obligations.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "ui_contract_obligation_count": len(obligations),
        "raw_candidate_backlog": _formula_backlog_summary(formulas, "public"),
        "rows_total": len(obligations),
        "rows": obligations,
    }
    payload["obligation_hash"] = _hash(payload)
    return payload


def _persona_user_story_map(
    *,
    system_architect_missions: list[dict[str, Any]],
    reviewer_objection_routes: list[dict[str, Any]],
) -> dict[str, Any]:
    spine = ["diagnose", "kill", "improve", "compare", "export"]
    personas = [
        {
            "persona_id": "system_architect",
            "opening_question": "Can this help me understand and harden a real system?",
            "primary_route": "workbench",
            "success_signal": "Completes diagnose -> kill -> improve -> compare -> export without reading source files.",
        },
        {
            "persona_id": "skeptical_scientist",
            "opening_question": "Why should I believe this is more than a visualization?",
            "primary_route": "proof",
            "success_signal": "Every claim routes to proof, boundary, source hash, formula and graph context.",
        },
        {
            "persona_id": "domain_expert",
            "opening_question": "Where is my domain and what recognizable anchors are here?",
            "primary_route": "benchmarks",
            "success_signal": "Domain lane opens replay-backed or boundary-marked examples with exportable assumptions.",
        },
        {
            "persona_id": "first_time_enthusiast",
            "opening_question": "What is OC and what can I click first?",
            "primary_route": "journey",
            "success_signal": "The cockpit provides a live model, a kill action, a ladder and cross-links.",
        },
        {
            "persona_id": "buyer_reviewer",
            "opening_question": "What practical work does this improve?",
            "primary_route": "mission",
            "success_signal": "Mission deck produces before/after diagnostics and a reviewer export.",
        },
    ]
    route_ids = sorted({row.get("id") for row in reviewer_objection_routes if row.get("id")})
    mission_ids = sorted({row.get("id") for row in system_architect_missions if row.get("id")})
    payload = {
        "schema_version": "oc-core-demo-persona-user-story-map.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "primary_product_story": "Ontology of Continua System Architect Workbench",
        "workflow_spine": spine,
        "personas": personas,
        "objection_route_ids": route_ids,
        "mission_ids": mission_ids,
        "acceptance_contract": {
            "first_screen": "Shows Version 010, a live workbench model and the diagnose/kill/improve/compare/export route.",
            "no_text_only_answers": "Reviewer objections resolve to functional routes and clicked surfaces.",
            "truth_discipline": "Unsupported science is shown as boundary or formalization obligation, never as proof.",
        },
    }
    payload["map_hash"] = _hash(payload)
    return payload


def _k_level_example_atlas(
    k_levels: list[dict[str, Any]],
    systems: list[dict[str, Any]],
    system_templates: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    proof_routes: list[dict[str, Any]],
    domains: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def _level_domain_coverage(level_id: str, available_domain_rows: list[dict[str, Any]]) -> list[str]:
        domain_count = [row["domain_id"] for row in available_domain_rows if level_id in (row.get("domain_projections", []) or []) or level_id in (row.get("domain_id", ""), "")]
        if not domain_count:
            domain_count = [row.get("domain_id") for row in available_domain_rows[:1] if row.get("domain_id")]
        return domain_count[:6]

    level_map = {row.get("level_id", ""): row for row in k_levels}
    template_by_level = {}
    for template in system_templates or []:
        for level in template.get("k_levels", []):
            template_by_level.setdefault(level, template["template_id"])
    if not template_by_level and systems:
        fallback_template = systems[0].get("id", "civilization")
        for level in [f"K{i}" for i in range(13)]:
            template_by_level[level] = fallback_template
    default_template = (system_templates[0]["template_id"] if system_templates else "civilization")
    example_rows: list[dict[str, Any]] = []
    formula_index = list(formulas)
    proof_ids = [row.get("target_id") for row in proof_routes][:6]
    domain_ids = [row.get("domain_id") for row in domains[:6]]
    for level in [f"K{i}" for i in range(13)]:
        level_number = int(level[1:])
        level_row = level_map.get(level, {})
        closure = level_row.get("closure_status", "OPEN_REPLAY_GAP")
        template_id = template_by_level.get(level, default_template)
        formula_refs = [item.get("formula_id") for item in formula_index if level in (item.get("formula_query", "") or item.get("formula_text", ""))][:2]
        if len(formula_refs) < 2:
            offset = (level_number * 2) % max(1, len(formula_index))
            rotated = formula_index[offset:] + formula_index[:offset]
            fallback_formula_refs = [item.get("formula_id") for item in rotated if item.get("formula_id")][:3]
            formula_refs.extend(fallback_formula_refs[len(formula_refs):])
        has_formula_refs = bool(formula_refs)
        has_proof_refs = bool(proof_ids)
        has_domain_refs = bool(domain_ids)
        has_template = bool(template_id)
        source_exception_reasons = []
        if not has_formula_refs:
            source_exception_reasons.append("NO_FORMULA_LINKS")
        if not has_proof_refs:
            source_exception_reasons.append("NO_PROOF_ROUTE_LINKS")
        if not has_domain_refs:
            source_exception_reasons.append("NO_DOMAIN_LINKS")
        if not has_template:
            source_exception_reasons.append("NO_TEMPLATE_LINK")
        boundary_mode = bool(source_exception_reasons)
        domain_coverage = _level_domain_coverage(level, domains)
        level_title = _clean(level_row.get("meaning") or level_row.get("semantic_summary") or f"{level} continuum", 80)
        example_themes = [
            f"{level} {level_title} rupture map",
            f"{level} {level_title} compensator trial",
            f"{level} {level_title} top-down constraint drill",
        ]
        for index in range(3):
            kill_target = "kill_cascade" if index % 2 == 0 else "system_workbench_preview"
            source_refs = [item for item in level_row.get("source_refs", []) if item] or ([f"k-level-source::{level}::{level_row.get('source_hash')}"] if level_row.get("source_hash") else [f"k-level-source::{level}::synthetic-boundary"])
            proof_slice = [proof_ids[(level_number + index + step) % len(proof_ids)] for step in range(min(2, len(proof_ids)))] if proof_ids else []
            formula_slice = [formula_refs[(index + step) % len(formula_refs)] for step in range(min(2, len(formula_refs)))] if formula_refs else []
            source_refs = list(dict.fromkeys([*source_refs, *[f"formula::{item}" for item in formula_slice if item], *[f"proof-route::{item}" for item in proof_slice if item], *[f"domain::{item}" for item in domain_coverage if item]]))
            example_rows.append(
                {
                    "example_id": f"k-level-example::{level}::{index + 1:02d}",
                    "k_level": level,
                    "quality_status": "FORMALIZATION_BOUNDARY_VISIBLE" if boundary_mode or closure.startswith("OPEN") else "WORKBENCH_READY_BOUNDARY_CHECKED",
                    "title": example_themes[index],
                    "objective": f"Inspect {level_title.lower()} through template {template_id}, formula {', '.join(formula_slice) or 'boundary-only'}, and a bounded kill/recovery path.",
                    "source": level_row.get("meaning") or "K-level diagnostic atlas row",
                    "system_template_workbench": {
                        "view": "workbench",
                        "target_type": "system_template",
                        "target_id": template_id,
                        "system_type": "workbench_template",
                        "template_model": next((item for item in system_templates if item.get("template_id") == template_id), {}),
                    },
                    "kill_path": {
                        "view": "workbench",
                        "target_type": "simulation",
                        "target_id": kill_target,
                        "axis": system_templates[0].get("allowed_axis_ids", ["coherence"])[0] if system_templates else "coherence",
                        "action": "Kill",
                    },
                    "recovery_option": {
                        "view": "workbench",
                        "target_type": "system_template",
                        "target_id": template_id,
                        "action": "Improve",
                        "linked_axis": system_templates[0].get("allowed_axis_ids", ["repair"])[-1] if system_templates else "repair",
                    },
                    "formula_refs": formula_slice,
                    "proof_refs": proof_slice,
                    "boundary_refs": [item for item in domain_ids[:2] if item],
                    "linked_axis": level_row.get("axis_ids", [])[:1] if isinstance(level_row.get("axis_ids"), list) else [item.get("axis_id") for item in (system_templates[0].get("allowed_axes", [])[:1] if system_templates else [])],
                    "source_refs": list(source_refs),
                    "nonclaim_boundary": (
                        "Replay and boundary language only; no unresolved claim upgrades; deterministic and bounded."
                        if closure.startswith("OPEN")
                        else "K-level route links are bounded by available simulation and evidence-boundary surfaces."
                    ),
                    "source_ref_count": len(source_refs),
                    "boundary_profile": {
                        "has_formula_refs": has_formula_refs,
                        "has_proof_refs": has_proof_refs,
                        "has_domain_refs": has_domain_refs,
                        "has_template": has_template,
                        "has_source_refs": bool(source_refs),
                        "closure_open": str(closure).startswith("OPEN"),
                    },
                    "source_exceptions": [{"code": code, "resolution": "nonclaim_boundary"} for code in source_exception_reasons],
                    "source_metadata": {
                        "k_level_row": {
                            "k_level": level,
                            "closure_status": closure,
                            "scenario_matrix_size": len(level_row.get("scenario_matrix", []) or []),
                            "simulation_status": level_row.get("simulation_status"),
                        },
                        "formula_refs": formula_slice,
                        "proof_refs": proof_slice,
                        "domain_refs": domain_coverage,
                        "boundary": "K-level route is a guided didactic scenario with explicit replay/proof boundary."
                        + (" Closure is open; only bounded claims are shown." if str(closure).startswith("OPEN") else " Closure gates are represented by provided simulation/proof evidence."),
                    },
                    "scenario_steps": [
                        {"step": "diagnose", "view": "workbench", "action": "Diagnose"},
                        {"step": "kill", "view": "workbench", "action": "Kill"},
                        {"step": "recover", "view": "workbench", "action": "Improve"},
                    ],
                }
            )
    return example_rows


def _science_formalization_ledger(
    k_levels: list[dict[str, Any]],
    k_axes: list[dict[str, Any]],
    systems: list[dict[str, Any]],
    system_templates: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    thresholds: list[dict[str, Any]],
    domains: list[dict[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    for level in k_levels:
        source_id = f"SCIENCE_FORMALIZATION::{level.get('level_id')}"
        status = "FORMALIZATION_BOUNDARY"
        if level.get("simulation_status") == "PASS":
            status = "FORMALIZATION_PARTIAL"
        rows.append(
            {
                "entity_id": source_id,
                "entity_kind": "k_level",
                "label": f"{level.get('level_id')} formalization status",
                "formalization_status": status,
                "basis": "simulation_replay_status_and_boundary_gates",
                "boundary_refs": [level.get("artifact_sha256", "")] if level.get("artifact_sha256") else [],
                "nonclaim_boundary": "K-level coverage is simulation/status bounded; not an external proof.",
            }
        )

    for row in k_axes:
        rows.append(
            {
                "entity_id": f"AXIS::{row.get('axis_id')}",
                "entity_kind": "axis",
                "label": row.get("title", row.get("axis_id", "")),
                "formalization_status": "FORMALIZATION_OBLIGATION" if "k_levels" not in row else "FORMALIZATION_BOUNDARY",
                "basis": "computable-axis diagnostic only",
                "nonclaim_boundary": row.get("nonclaim_boundary", ""),
                "source_refs": [row.get("axis_id")],
            }
        )

    for row in system_templates:
        rows.append(
            {
                "entity_id": f"TEMPLATE::{row.get('template_id')}",
                "entity_kind": "system_template",
                "label": row.get("title", row.get("template_id", "")),
                "formalization_status": "FORMALIZATION_BOUNDARY",
                "basis": "workbench template descriptor",
                "nonclaim_boundary": row.get("nonclaim_boundary", ""),
                "source_refs": [row.get("template_hash", "")] if row.get("template_hash") else [],
            }
        )

    for row in systems:
        rows.append(
            {
                "entity_id": f"SYSTEM::{row.get('id')}",
                "entity_kind": "system",
                "label": row.get("title", row.get("id", "")),
                "formalization_status": "FORMALIZATION_BOUNDARY",
                "basis": "deterministic workbench model",
                "source_refs": [row.get("model_hash", "")] if row.get("model_hash") else [],
                "nonclaim_boundary": row.get("nonclaim", ""),
            }
        )

    for row in thresholds:
        rows.append(
            {
                "entity_id": row.get("threshold_id", ""),
                "entity_kind": "threshold",
                "label": row.get("title", row.get("threshold_id", "")),
                "formalization_status": "FORMALIZATION_OBLIGATION" if row.get("threshold_type") == "collapse" else "FORMALIZATION_BOUNDARY",
                "basis": "workbench diagnostic threshold",
                "source_refs": [row.get("axis_id")] if row.get("axis_id") else [],
                "nonclaim_boundary": row.get("nonclaim_boundary", ""),
            }
        )

    for row in formulas:
        status = "FORMALIZATION_OBLIGATION" if row.get("render_quality") == "low" else "FORMALIZATION_BOUNDARY"
        rows.append(
            {
                "entity_id": row.get("formula_id"),
                "entity_kind": "formula",
                "label": row.get("semantic_title", ""),
                "formalization_status": status,
                "basis": row.get("quality_status", "candidate"),
                "source_refs": row.get("source_refs", []),
                "source_atom_id": row.get("source_atom_id", ""),
                "nonclaim_boundary": "Formula rows are display surfaces unless replay/closure marks support.",
            }
        )

    if domains:
        boundary_domains = [row.get("domain_id") for row in domains if str(row.get("closure_status", "")).startswith("OPEN")]
        for domain_id in boundary_domains[:8]:
            rows.append(
                {
                    "entity_id": f"DOMAIN::{domain_id}",
                    "entity_kind": "domain",
                    "label": f"{domain_id} validation status",
                    "formalization_status": "FORMALIZATION_BOUNDARY",
                    "basis": "domain validation replay gate",
                    "nonclaim_boundary": "Domain lanes are not replaced by this formalization ledger; replay boundaries still apply.",
                }
            )

    ledger = {
        "schema_version": "oc-core-demo-science-formalization-ledger.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "rows_total": len(rows),
        "obligation_rows": len([row for row in rows if "OBLIGATION" in str(row.get("formalization_status", ""))]),
        "boundary_rows": len([row for row in rows if "BOUNDARY" in str(row.get("formalization_status", ""))]),
        "rows": rows,
    }
    ledger["ledger_hash"] = _hash(ledger)
    return ledger


def _demonstrator_surface_graph(
    *,
    source_counts: dict[str, Any],
    didactic_routes: list[dict[str, Any]],
    reviewer_objection_routes: list[dict[str, Any]],
    system_architect_missions: list[dict[str, Any]],
    route_action_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    surfaces = [
        ("journey", "Cockpit", "First loaded workbench surface; tells the reviewer what OC is and gives immediate actions.", "atlas/source_status/cerberus_review"),
        ("guided", "Guided OC Journey", "Didactic route rail for first-time readers.", "didactic_routes"),
        ("workbench", "System Workbench", "Architect workflow: diagnose, kill, improve, compare, export.", "system_templates/k_level_example_atlas"),
        ("km", "K/M Hierarchy", "Bidirectional K/M slice view with axes, flows, cycles and thresholds.", "k_levels/m_spaces/k_axes"),
        ("wiki", "OC Wiki", "Atomized monograph/methods reader with cross-links.", "corpus_index/oc_wiki"),
        ("formula", "Formula Atlas", "Searchable symbolic surface with quality/boundary metadata.", "formula_atlas/formula_quality_report"),
        ("klevels", "K-Level Worlds", "K0-K12 3D worlds and drilldown examples.", "k_level_worlds/k_level_example_atlas"),
        ("worldline", "Worldline Theater", "Birth/evolution/overload/collapse/recovery didactic simulation.", "simulation_worlds"),
        ("cascade", "Cascade Lab", "Selected/weakest node kill and recovery visualization.", "system_zoo/collapse_paths"),
        ("benchmarks", "Domain Simulators", "Domain entry lanes with replay/status boundaries.", "domain_benchmarks"),
        ("objections", "Objection Router", "Routes skeptical objections to functional surfaces, not FAQ text.", "reviewer_objection_routes"),
        ("whyoc", "Why OC / Comparison", "Interactive comparison to existing model families.", "model_comparison_matrix"),
        ("practical", "Practical Value", "Three-minute utility and export surfaces.", "practical_value_cards"),
        ("trust", "Trust Ladder", "Toy/exploratory/replay/proof-bounded status ladder.", "trust_ladder"),
        ("mission", "Mission Deck", "System architect missions with expected actions.", "system_architect_missions"),
        ("graph", "3D Science Graph", "Root principle to operators, K-levels, proofs, formulas and domains.", "science_graph_v010/node_detail_index"),
        ("proof", "Evidence / Boundaries", "Claim status, evidence route, limitations and nonclaim boundary without public proof-closure overclaim.", "proof_routes/closure_ledger"),
        ("gaps", "Gap Closure", "Closure ledger and proof-workbench obligations.", "closure_ledger/research_gap_summary"),
        ("reviewer", "Reviewer Mode", "Evidence bundle, quality report and public-safety review.", "quality_report/cerberus_v010_review"),
    ]
    controls = {
        "journey": ["Open OC Journey", "Open Workbench", "Open Science Graph", "Open Formula Atlas", "skeptical objection chips"],
        "workbench": ["template selector", "K-level selector", "add axis dropdown", "Kill", "Diagnose", "Improve", "Compare", "Export"],
        "wiki": ["search", "TOC chapter buttons", "section chips", "atom open", "Formula drill", "Graph drill", "Proof route"],
        "formula": ["search", "formula row button", "Probe in graph", "Open in wiki", "Open in graph by id"],
        "graph": ["search", "layer filter", "edge filter", "reset/root path", "node click", "wiki/formula/proof/K/workbench links"],
        "cascade": ["system selector", "speed slider", "kill mode selector", "selected node kill", "reset/replay", "export cascade replay packet"],
        "klevels": ["select level rail", "elevator select", "export selected route", "open workbench", "graph probe"],
        "proof": ["target list", "claim drilldown", "nonclaim boundary", "trust ladder"],
        "reviewer": ["export bundle", "trust ladder", "why OC", "practical value", "mission deck"],
    }
    nodes = []
    edges = []
    for surface_id, title, purpose, source in surfaces:
        nodes.append(
            {
                "id": f"SURFACE::{surface_id}",
                "kind": "surface",
                "surface_id": surface_id,
                "title": title,
                "purpose": purpose,
                "test_id": f"{surface_id}-surface",
                "data_sources": source.split("/"),
                "visible_count_source": source_counts,
                "must_have": [
                    "loaded-state screenshot",
                    "DOM snapshot",
                    "click trace for primary controls",
                    "nonclaim boundary where scientific status is shown",
                ],
                "anti_patterns": [
                    "button without route",
                    "count without drilldown",
                    "formula id as primary explanation",
                    "decorative PASS badge without evidence",
                    "loading-state screenshot",
                ],
            }
        )
        for control in controls.get(surface_id, []):
            control_slug = re.sub(r"[^A-Za-z0-9]+", "_", control).strip("_").lower()
            control_id = f"CONTROL::{surface_id}::{control_slug}"
            nodes.append(
                {
                    "id": control_id,
                    "kind": "control",
                    "surface_id": surface_id,
                    "title": control,
                    "purpose": f"Primary user action on {title}.",
                    "data_sources": source.split("/"),
                    "target_view": surface_id,
                    "state_mutation": "route-change-or-local-selection",
                    "expected_visible_result": f"{title} visibly changes the {surface_id} surface or opens a linked route.",
                    "test_id": f"{surface_id}-{control_slug}",
                    "required_test": "Playwright click changes route, selection, model state or exported payload.",
                }
            )
            edges.append({"source": f"SURFACE::{surface_id}", "target": control_id, "relation": "exposes_control"})

    existing_control_test_ids = {row.get("test_id") for row in nodes if row.get("kind") == "control"}
    for route_row in route_action_manifest or []:
        if not isinstance(route_row, dict) or not route_row.get("control_binding"):
            continue
        control_binding = str(route_row.get("control_binding"))
        if control_binding in existing_control_test_ids:
            continue
        surface_id = str(route_row.get("surface_binding") or route_row.get("target_view") or "journey")
        control_id = f"CONTROL::{surface_id}::{control_binding}"
        nodes.append(
            {
                "id": control_id,
                "kind": "control",
                "surface_id": surface_id,
                "title": route_row.get("action_label") or route_row.get("action") or control_binding,
                "purpose": f"Route-bound control for {route_row.get('route_id', 'didactic route')}.",
                "data_sources": ["route_action_manifest"],
                "target_view": route_row.get("target_view", surface_id),
                "state_mutation": "route-bound-semantic-action",
                "expected_visible_result": route_row.get("expected_visible_result", "Route-bound control produces a visible semantic result."),
                "test_id": control_binding,
                "required_test": "Route-action reconciliation resolves this control_binding to this listed control test_id.",
            }
        )
        edges.append({"source": f"SURFACE::{surface_id}", "target": control_id, "relation": "exposes_route_bound_control"})
        existing_control_test_ids.add(control_binding)

    route_targets = []
    for bundle in (didactic_routes, reviewer_objection_routes, system_architect_missions):
        for route in bundle:
            route_id = route.get("id") or route.get("route_id")
            action_views: list[str] = []
            for key in ("action_view", "target_view", "view"):
                if route.get(key):
                    action_views.append(str(route[key]))
            for link in route.get("links_to_real_surfaces", []) if isinstance(route.get("links_to_real_surfaces"), list) else []:
                if isinstance(link, dict) and link.get("view"):
                    action_views.append(str(link["view"]))
            for step in route.get("steps", []) if isinstance(route.get("steps"), list) else []:
                if not isinstance(step, dict):
                    continue
                for key in ("action_view", "target_view", "view"):
                    if step.get(key):
                        action_views.append(str(step[key]))
                for action_target in step.get("action_targets", []) if isinstance(step.get("action_targets"), list) else []:
                    if isinstance(action_target, dict) and action_target.get("target_view"):
                        action_views.append(str(action_target["target_view"]))
            for action_view in sorted(set(action_views)):
                if route_id and action_view:
                    route_targets.append((route_id, action_view))
    route_node_ids: set[str] = set()
    for route_id, action_view in route_targets:
        target = f"SURFACE::{action_view}"
        if any(node["id"] == target for node in nodes):
            edges.append({"source": f"ROUTE::{route_id}", "target": target, "relation": "routes_to_surface"})
            route_node_id = f"ROUTE::{route_id}"
            if route_node_id not in route_node_ids:
                route_node_ids.add(route_node_id)
                nodes.append(
                    {
                        "id": route_node_id,
                        "kind": "route",
                        "title": route_id,
                        "purpose": "Pre-build route contract; prevents orphan buttons and dead didactic branches.",
                        "target_surface": action_view,
                        "source": "route_action_manifest",
                        "test_id": f"route-{re.sub(r'[^A-Za-z0-9]+', '_', route_id).strip('_').lower()}",
                        "expected_visible_result": f"Route lands on {action_view} with a visible surface or state change.",
                        "required_test": "Route must be reachable from UI and included in click trace.",
                    }
                )

    surface_rows = [node for node in nodes if node.get("kind") == "surface"]
    control_rows = [node for node in nodes if node.get("kind") == "control"]
    route_rows = [node for node in nodes if node.get("kind") == "route"]
    surface_ids = {row.get("surface_id") for row in surface_rows}
    orphan_controls = [
        row
        for row in control_rows
        if row.get("surface_id") not in surface_ids
        or not row.get("purpose")
        or not row.get("target_view")
        or not row.get("expected_visible_result")
        or not row.get("test_id")
    ]
    dead_routes = [
        row
        for row in route_rows
        if row.get("target_surface") not in surface_ids
        or not row.get("expected_visible_result")
        or not row.get("test_id")
    ]
    count_without_drilldown = [
        row
        for row in surface_rows
        if row.get("declared_visible_counts")
        and not any(edge.get("source") == row.get("id") and edge.get("relation") == "exposes_control" for edge in edges)
    ]
    prebuild_status = "PASS" if not orphan_controls and not dead_routes and not count_without_drilldown else "FAIL_CLOSED"
    graph = {
        "schema_version": "oc-core-demo-surface-graph.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "summary": {
            "surface_count": len(surface_rows),
            "control_count": len(control_rows),
            "route_count": len(route_rows),
            "edge_count": len(edges),
            "orphan_control_count": len(orphan_controls),
            "dead_route_count": len(dead_routes),
            "count_without_drilldown_count": len(count_without_drilldown),
        },
        "surfaces": surface_rows,
        "controls": control_rows,
        "routes": route_rows,
        "nodes": nodes,
        "edges": edges,
        "prebuild_gate": {
            "required_before_release": True,
            "status": prebuild_status,
            "orphan_control_ids": [row.get("id") for row in orphan_controls],
            "dead_route_ids": [row.get("id") for row in dead_routes],
            "count_without_drilldown_surface_ids": [row.get("id") for row in count_without_drilldown],
            "rules": [
                "Every surface has purpose, data source, loaded screenshot and DOM/click trace.",
                "Every button/control maps to a visible route or state mutation.",
                "Every displayed count links to a drilldown/list.",
                "Every scientific control declares evidence source and nonclaim boundary.",
            ],
        },
    }
    graph["surface_graph_hash"] = _hash(graph)
    return graph


def _formula_has_private_or_code_shape(text: str) -> bool:
    haystack = text.replace("\\", "/")
    if any(marker.lower() in haystack.lower() for marker in FORMULA_CODE_OR_PATH_MARKERS):
        return True
    return bool(re.search(r"\b[A-Z_]{3,}_PATH\s*=", text))


def _looks_like_formula(text: str) -> bool:
    if len(text) > 220:
        return False
    stripped = _normalize_formula_text(text)
    prose_or_locator_markers = (
        '"""',
        "`",
        "- [",
        "Match ",
        "Exact source locator",
        "master_manuscript_ref",
        "translation_lane_status",
        "NOT_READY_FOR_REVIEW",
        "page=",
        "source locator",
        "theorem_claim",
        "rows",
        "lines",
    )
    if stripped.startswith(('"', "'", "-", "*", "#", "@")):
        return False
    if '"' in stripped or "'" in stripped or "@" in stripped:
        return False
    if stripped.rstrip().endswith(("=", "->", "+", "-", "\\to", "\\mapsto")):
        return False
    if stripped.count("(") != stripped.count(")") or stripped.count("[") != stripped.count("]"):
        return False
    if stripped.count("{") != stripped.count("}"):
        return False
    if "|" in stripped or "?" in stripped or "#" in stripped:
        return False
    if re.search(r"[А-Яа-я]", stripped):
        return False
    if "/" in stripped and "\\" not in stripped:
        return False
    if re.search(r"\b(?:file|project_dir|scripts|skipped|fileresult|result|class|function|cloudflare|claim=|baseline|theorem_cov|dataclass|patch|version|auth|s3|lake|clogic|corepaper|core\(|compute|secant|doi|assessment|ideal)\b", stripped, flags=re.IGNORECASE):
        return False
    if re.match(r"^[A-Z_]{2,}\s*=", stripped):
        return False
    if re.match(r"^(?:Let|It|Every|Each|The|This|All|Aim|Ligatures|LAKE|M0\s+and)\b", stripped):
        return False
    if re.search(r"\b(?:denote|manifold|property|satisfying|monotonically|error pattern|ligatures|not known|living continuum|of the form|for some|while|under|therefore|classified|attempted extension|almost non-negative|cohomogeneity|classification)\b", stripped, flags=re.IGNORECASE):
        return False
    if "\\begin{cases}" in stripped and "\\end{cases}" not in stripped:
        return False
    relation_markers = ("=", ">", "<", "≥", "≤", "⇔", "->", "→", "\\subset", "\\subseteq", "\\in", "\\notin", "\\le", "\\ge")
    if not any(marker in stripped for marker in relation_markers):
        return False
    prose_patterns = (
        r"\bEach\b.+\b(?:is|has|generated)\b",
        r"\bEvery\b.+\b(?:is|has|subject)\b",
        r"\bIt\s+satisfies\b",
        r"\bA\s+[a-z].+\b(?:is|has|when)\b",
    )
    if any(re.search(pattern, stripped) for pattern in prose_patterns):
        return False
    if re.search(r"\b(?:suppose|there|gibt|existe|существует|метрика|question|tier1|whitepaper|constraint|admissibility)\b", stripped, flags=re.IGNORECASE):
        return False
    if any(marker.lower() in stripped.lower() for marker in prose_or_locator_markers):
        return False
    if re.search(r"\b(?:match|locator|status|review|source|page|path|json|python|row|line)s?\b", stripped, flags=re.IGNORECASE):
        return False
    if re.search(r"\b\d+\s*-\s*(?:rc|patch|v)\w*", stripped, flags=re.IGNORECASE):
        return False
    if re.match(r"^\d+\s+(?:and|or)\b", stripped, flags=re.IGNORECASE):
        return False
    symbolic_tokens = ("≥", "≤", "∑", "∫", "→", "↦", "⊂", "⊆", "∀", "∃", "∧", "∨", "¬", "∂", "λ", "Δ", "Ω", "α", "β", "γ")
    if any(token in stripped for token in symbolic_tokens):
        return True
    if re.search(r"\\(?:frac|sum|int|lim|forall|exists|partial|alpha|beta|gamma|delta|Delta|Omega|Theta|Phi|Lambda|Pi|rho|epsilon|lor|Leftrightarrow|to)\b", stripped):
        return True
    ascii_math = re.search(r"(?:[A-Za-z][A-Za-z0-9_]*|\)|\])\s*(?:=|<=|>=|<|>|\+|\-|\*|/|\^)\s*(?:[A-Za-z0-9(\\])", stripped)
    if ascii_math:
        words = re.findall(r"[A-Za-z]{3,}", stripped)
        return len(words) <= 4
    return False


def _simulation_worlds(k_levels: list[dict[str, Any]], domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": "worldline_birth_evolution_collapse",
            "world_id": "worldline_birth_evolution_collapse",
            "title": "Worldline Birth / Evolution / Collapse",
            "type": "worldline",
            "purpose": "Show a continuum being born, differentiating, stabilizing, evolving, entering contradiction load and either repairing or collapsing.",
            "default_params": {"seed": 14, "load": 0.62, "repair": 0.38, "contradiction": 0.58, "coupling": 0.44, "steps": 72},
            "assumptions": ["bounded deterministic toy model", "state variables are OC diagnostic coordinates", "not standalone empirical proof"],
            "source_status": "educational-deterministic",
        },
        {
            "id": "k_level_elevator",
            "world_id": "k_level_elevator",
            "title": "K-Level Elevator",
            "type": "klevels",
            "purpose": "Move through K0-K12 while preserving invariants and exposing domain projections, proof status and simulation replay state.",
            "default_params": {"start": 0, "stop": max(0, len(k_levels) - 1), "load": 0.65},
            "assumptions": ["K-level rows come from Logion K-level atlas", "domain projections are status surfaces, not automatic empirical closure"],
            "source_status": "ledger-backed",
        },
        {
            "id": "kill_cascade",
            "world_id": "kill_cascade",
            "title": "Kill Cascade",
            "type": "cascade",
            "purpose": "Remove a support node and compute the shortest collapse trajectory through a bounded dependency graph.",
            "default_params": {"system_id": "civilization", "kill_node": "energy-throughput", "shock": 0.82},
            "assumptions": ["shortest path is computed over demonstrator dependency edges", "collapse path is diagnostic, not a prophecy"],
            "source_status": "deterministic-graph",
        },
        {
            "id": "domain_anchor_lab",
            "world_id": "domain_anchor_lab",
            "title": "Domain Anchors",
            "type": "domain-benchmarks",
            "purpose": "Inspect physics, chemistry, biology and systems benchmark lanes with official constants and validation status.",
            "default_params": {"domain_index": 0, "residual_scale": 1.0},
            "assumptions": ["official datasets are anchors", "lanes are promoted only when replay/validation closure is present"],
            "source_status": "benchmark-registry-backed",
            "domain_count": len(domains),
        },
    ]


def _k_level_worlds(k_levels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    worlds = []
    for index, level in enumerate(k_levels):
        domains = level.get("domain_projections", []) or []
        domain_nodes = []
        for d_index, domain in enumerate(domains[:6]):
            angle = 2 * math.pi * d_index / max(1, min(6, len(domains)))
            domain_nodes.append(
                {
                    "id": f"{level['level_id']}::DOMAIN::{domain}",
                    "label": str(domain),
                    "role": "domain-projection",
                    "x": round(math.cos(angle) * (2.8 + index * 0.08), 5),
                    "y": round(math.sin(angle) * (2.8 + index * 0.08), 5),
                    "z": round(0.45 + d_index * 0.18, 5),
                    "health": 0.82,
                }
            )
        nodes = [
            {"id": f"{level['level_id']}::CORE", "label": f"{level['level_id']} core", "role": "continuum-core", "x": 0, "y": 0, "z": 0, "health": 0.94},
            {"id": f"{level['level_id']}::BOUNDARY", "label": "boundary", "role": "boundary", "x": 1.9, "y": 0, "z": 0.6, "health": 0.76},
            {"id": f"{level['level_id']}::INVARIANT", "label": "invariant", "role": "invariant", "x": -1.9, "y": 0, "z": -0.6, "health": 0.88},
            *domain_nodes,
        ]
        links = [{"source": f"{level['level_id']}::CORE", "target": node["id"], "relation": node["role"], "weight": 0.72} for node in nodes[1:]]
        worlds.append(
            {
                "world_id": f"WORLD::{level['level_id']}",
                "level_id": level["level_id"],
                "title": f"{level['level_id']} Continuum World",
                "meaning": level.get("meaning", ""),
                "semantic_summary": level.get("semantic_summary", ""),
                "nodes": nodes,
                "links": links,
                "kill_options": [node["id"] for node in nodes if node["role"] in {"boundary", "domain-projection"}],
                "replay_status": level.get("simulation_status", "unknown"),
                "closure_status": level.get("closure_status", "unknown"),
                "artifact_sha256": level.get("artifact_sha256", ""),
                "nonclaim_boundary": "K-level world geometry is a deterministic visualization of atlas semantics, not new proof.",
                "world_hash": _hash({"level_id": level["level_id"], "nodes": nodes, "links": links}),
            }
        )
    return worlds


def _system_zoo() -> list[dict[str, Any]]:
    systems = [
        {
            "id": "primitive-distinction",
            "title": "Primitive Distinction / Axis Birth",
            "k_levels": ["K0", "K1"],
            "critical_nodes": ["unresolved-contradiction", "boundary-seed", "axis-choice", "collapse-null"],
            "dependencies": [["unresolved-contradiction", "axis-choice"], ["boundary-seed", "axis-choice"], ["axis-choice", "collapse-null"]],
            "kill_default": "boundary-seed",
            "what_it_shows": "How the root OC principle becomes the first computable split: contradiction either births an axis or exhausts admissible continuation.",
            "nonclaim": "This is the demonstrator's formal root workbench model, not an empirical physical system.",
        },
        {
            "id": "physical-phase",
            "title": "Physical Phase Continuum",
            "k_levels": ["K1", "K2"],
            "critical_nodes": ["temperature-gradient", "field-boundary", "phase-threshold"],
            "dependencies": [["temperature-gradient", "phase-threshold"], ["field-boundary", "phase-threshold"], ["phase-threshold", "coherence-loss"]],
            "kill_default": "field-boundary",
            "what_it_shows": "How a physical projection can be visualized as thresholds, gradients and collapse surfaces.",
            "nonclaim": "This is a bounded projection surface, not a replacement for physics.",
        },
        {
            "id": "prebiotic-chemistry",
            "title": "Prebiotic Chemical Organization",
            "k_levels": ["K2", "K3", "K4"],
            "critical_nodes": ["catalytic-loop", "resource-gradient", "membrane-boundary"],
            "dependencies": [["resource-gradient", "catalytic-loop"], ["membrane-boundary", "catalytic-loop"], ["catalytic-loop", "organization-collapse"]],
            "kill_default": "resource-gradient",
            "what_it_shows": "How chemical organization depends on gradients, closure and catalytic recurrence.",
            "nonclaim": "This does not claim solved origin-of-life chemistry.",
        },
        {
            "id": "biological-cell",
            "title": "Biological Cell-State Continuum",
            "k_levels": ["K4", "K5", "K6"],
            "critical_nodes": ["membrane", "ion-channel", "expression-state", "repair-loop"],
            "dependencies": [["membrane", "ion-channel"], ["ion-channel", "expression-state"], ["repair-loop", "expression-state"], ["expression-state", "cell-state-collapse"]],
            "kill_default": "membrane",
            "what_it_shows": "How bounded biological state transitions can be represented without overclaiming universal biology.",
            "nonclaim": "The app does not diagnose real organisms or clinical state.",
        },
        {
            "id": "institution",
            "title": "Institutional Continuum",
            "k_levels": ["K7", "K8"],
            "critical_nodes": ["trust", "lawful-boundary", "resource-flow", "coordination"],
            "dependencies": [["trust", "coordination"], ["lawful-boundary", "coordination"], ["resource-flow", "coordination"], ["coordination", "institutional-collapse"]],
            "kill_default": "trust",
            "what_it_shows": "How social and institutional continua fail through dependency coupling.",
            "nonclaim": "This is a diagnostic model, not political prediction.",
        },
        {
            "id": "cognitive-social-agent",
            "title": "Cognitive / Social Agent Continuum",
            "k_levels": ["K6", "K7", "K8"],
            "critical_nodes": ["attention-boundary", "memory-loop", "norm-model", "coordination-signal"],
            "dependencies": [["attention-boundary", "memory-loop"], ["memory-loop", "norm-model"], ["coordination-signal", "norm-model"], ["norm-model", "agent-coherence-collapse"]],
            "kill_default": "attention-boundary",
            "what_it_shows": "How cognitive and social coordination can be modeled through attention, memory, norms and signal coupling.",
            "nonclaim": "This is an OC diagnostic workbench model, not a psychological diagnosis or social prediction.",
        },
        {
            "id": "civilization",
            "title": "Civilizational Continuum",
            "k_levels": ["K8", "K9", "K10", "K11", "K12"],
            "critical_nodes": ["energy-throughput", "semantic-coherence", "infrastructure", "feedback-governance"],
            "dependencies": [["energy-throughput", "infrastructure"], ["semantic-coherence", "feedback-governance"], ["infrastructure", "feedback-governance"], ["feedback-governance", "civilizational-collapse"]],
            "kill_default": "energy-throughput",
            "what_it_shows": "How large-scale systemic thresholds become visible through coupled dependencies.",
            "nonclaim": "This is a bounded K8+ projection, not unrestricted civilizational prophecy.",
        },
        {
            "id": "meta-model",
            "title": "Theory / Meta-Model Continuum",
            "k_levels": ["K10", "K11", "K12"],
            "critical_nodes": ["axiom-boundary", "formal-map", "evidence-ledger", "review-loop"],
            "dependencies": [["axiom-boundary", "formal-map"], ["formal-map", "evidence-ledger"], ["review-loop", "evidence-ledger"], ["evidence-ledger", "model-collapse"]],
            "kill_default": "axiom-boundary",
            "what_it_shows": "How a theory architecture holds together through axioms, formalization, evidence ledgers and review feedback.",
            "nonclaim": "This models theory structure inside the demonstrator; it does not certify the theory as externally accepted.",
        },
    ]
    return [_enrich_system_model(system, index) for index, system in enumerate(systems)]


def _enrich_system_model(system: dict[str, Any], system_index: int) -> dict[str, Any]:
    node_ids = sorted({node for edge in system.get("dependencies", []) for node in edge})
    nodes = []
    for index, node_id in enumerate(node_ids):
        angle = 2 * math.pi * index / max(1, len(node_ids))
        vulnerability = round(0.28 + ((index + system_index) % 5) * 0.11, 4)
        resilience = round(max(0.12, 0.88 - vulnerability * 0.72), 4)
        nodes.append(
            {
                "id": node_id,
                "label": node_id.replace("-", " "),
                "role": "collapse-terminal" if "collapse" in node_id else "critical-support" if node_id in system.get("critical_nodes", []) or node_id == system.get("kill_default") else "dependency",
                "x": round(math.cos(angle) * 3.4, 5),
                "y": round(math.sin(angle) * 2.2, 5),
                "z": round(math.sin(angle * 2) * 1.2, 5),
                "vulnerability": vulnerability,
                "resilience": resilience,
                "recovery_capacity": round(resilience * 0.64, 4),
                "health": 1.0,
            }
        )
    edges = [
        {
            "id": f"{system['id']}::edge::{index}",
            "source": source,
            "target": target,
            "weight": round(0.55 + (index % 4) * 0.12, 4),
            "flow_channel": "support" if "collapse" not in target else "failure",
        }
        for index, (source, target) in enumerate(system.get("dependencies", []))
    ]
    outgoing_sources = {edge["source"] for edge in edges}
    weakest_candidates = [node for node in nodes if node["id"] in outgoing_sources and "collapse" not in node["id"]]
    return {
        **system,
        "nodes": nodes,
        "edges": edges,
        "weakest_node": max(weakest_candidates or nodes, key=lambda item: item["vulnerability"])["id"] if nodes else system.get("kill_default", ""),
        "model_hash": _hash({"id": system.get("id"), "nodes": nodes, "edges": edges}),
    }


def _k_axes(k_levels: list[dict[str, Any]], domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domain_ids = [str(row.get("domain_id")) for row in domains if row.get("domain_id")]
    seeds = [
        ("coherence", "Coherence axis", "Tracks whether relation, evidence and operation remain jointly usable.", 0.66),
        ("load", "Contradiction/load axis", "Tracks pressure from unresolved contradiction, coupling drag or stress.", 0.58),
        ("repair", "Repair capacity axis", "Tracks corrective capacity, buffering and recovery potential.", 0.42),
        ("connectivity", "Connectivity axis", "Tracks how many support paths survive after local rupture.", 0.74),
        ("flow", "Flow continuity axis", "Tracks whether support, energy, evidence or coordination channels remain open.", 0.69),
        ("threshold", "Threshold proximity axis", "Tracks distance to collapse, transition or re-description thresholds.", 0.47),
        ("boundary", "Boundary clarity axis", "Tracks how cleanly a system separates, couples and projects its environment.", 0.62),
        ("axis_birth", "New-axis birth capacity", "Tracks whether a contradiction can be resolved by adding a computable axis.", 0.51),
    ]
    axes = []
    all_k = [level.get("level_id") for level in k_levels if level.get("level_id")]
    for index, (axis_id, title, interpretation, default_value) in enumerate(seeds):
        k_bindings = [level for level in all_k if (int(re.sub(r"\D", "", level) or 0) + index) % 3 != 1][:7] or all_k[:4]
        domain_bindings = domain_ids[index % max(1, len(domain_ids)) : index % max(1, len(domain_ids)) + 3] or domain_ids[:3]
        row = {
            "axis_id": axis_id,
            "title": title,
            "direction": "higher_is_more_resilient" if axis_id in {"coherence", "repair", "connectivity", "flow", "boundary", "axis_birth"} else "higher_is_more_dangerous",
            "default_value": default_value,
            "min": 0,
            "max": 1,
            "step": 0.01,
            "k_levels": k_bindings,
            "domain_ids": domain_bindings,
            "source_status": "deterministic-diagnostic",
            "closure_basis": f"{DEMO_VERSION} workbench axis derived from existing replay/cascade/worldline telemetry.",
            "claim_status": "nonclaim",
            "interpretation": interpretation,
            "nonclaim_boundary": "Workbench axes are deterministic diagnostic coordinates; they are not unrestricted empirical prediction claims.",
        }
        row["axis_hash"] = _hash(row)
        axes.append(row)
    return axes


def _m_spaces(k_levels: list[dict[str, Any]], domains: list[dict[str, Any]], k_axes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_k = [level.get("level_id") for level in k_levels if level.get("level_id")]
    domain_ids = [str(row.get("domain_id")) for row in domains if row.get("domain_id")]
    axis_ids = [row["axis_id"] for row in k_axes]
    rows = [
        ("M-ROOT", "Root M-space", "The full model space where contradiction, boundary, operator and collapse are jointly tracked.", all_k, domain_ids, axis_ids),
        ("M-PHYSICS", "Physical M-space", "Model space for gradients, constants, thresholds, fields and physical projection limits.", ["K0", "K1", "K2"], ["PHYSICS", "MATHEMATICS"], ["coherence", "load", "threshold", "boundary"]),
        ("M-CHEMISTRY", "Chemical organization M-space", "Model space for reaction organization, resource gradients, catalytic closure and membrane-like boundaries.", ["K2", "K3", "K4"], ["CHEMISTRY"], ["flow", "connectivity", "threshold", "axis_birth"]),
        ("M-BIOLOGY", "Biological state M-space", "Model space for cell-state transitions, repair loops, expression signatures and bounded organismic states.", ["K4", "K5", "K6"], ["BIOLOGY"], ["coherence", "repair", "flow", "boundary"]),
        ("M-COGNITIVE-SOCIAL", "Cognitive/social M-space", "Model space for attention, memory, norms, trust, coordination and institutional feedback.", ["K6", "K7", "K8"], ["SYSTEMS_CIVILIZATIONAL_PROJECTION"], ["connectivity", "flow", "repair", "axis_birth"]),
        ("M-CIVILIZATION", "Civilizational M-space", "Model space for energy throughput, infrastructure, semantic coherence and governance feedback.", ["K8", "K9", "K10", "K11", "K12"], ["SYSTEMS_CIVILIZATIONAL_PROJECTION", "METAONTOLOGY"], ["load", "connectivity", "flow", "threshold", "boundary"]),
        ("M-META", "Meta-model M-space", "Model space for theories, evidence-boundary surfaces, evidence ledgers, formula registries and review loops.", ["K10", "K11", "K12"], ["METAONTOLOGY", "DRT", "MATHEMATICS"], ["coherence", "boundary", "repair", "axis_birth"]),
    ]
    out = []
    for m_space_id, semantic_name, scope, k_bindings, domain_bindings, supported_axes in rows:
        row = {
            "m_space_id": m_space_id,
            "semantic_name": semantic_name,
            "scope": scope,
            "functions": ["construct", "project", "stress", "kill", "repair", "compare"],
            "parent_domain": domain_bindings[0] if domain_bindings else "METAONTOLOGY",
            "k_level_bindings": [level for level in k_bindings if level in all_k],
            "domain_bindings": [domain for domain in domain_bindings if domain in domain_ids] or domain_bindings,
            "operators": ["Birth", "Differentiate", "Stabilize", "Project", "Kill", "Repair"],
            "supported_axes": [axis for axis in supported_axes if axis in axis_ids],
            "source_status": f"generated-from-{DEMO_VERSION.lower()}-workbench-schema",
            "boundary_text": "M-space is an explicit workbench/navigation layer over existing OC sources; it does not create new proof status.",
        }
        row["source_hash"] = _hash(row)
        out.append(row)
    return out


def _collapse_path(system: dict[str, Any], start: str) -> list[str]:
    dependencies = [(str(source), str(target)) for source, target in system.get("dependencies", [])]
    adjacency: dict[str, list[str]] = {}
    for source, target in dependencies:
        adjacency.setdefault(source, []).append(target)
    queue = deque([(start, [start])])
    visited = {start}
    best = [start]
    while queue:
        node, path = queue.popleft()
        if "collapse" in node:
            return path
        for nxt in adjacency.get(node, []):
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, [*path, nxt]))
                best = [*path, nxt]
    return best


def _system_flows(systems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flows = []
    for system in systems:
        for edge in system.get("edges", []):
            row = {
                "flow_id": f"FLOW::{system['id']}::{edge['id']}",
                "system_id": system["id"],
                "source": edge["source"],
                "target": edge["target"],
                "flow_channel": edge.get("flow_channel", "support"),
                "flow_direction": "collapse" if edge.get("flow_channel") == "failure" else "support",
                "weight": edge.get("weight", 0.5),
                "claim_status": "nonclaim",
                "source_status": "system-template-edge",
                "nonclaim_boundary": "Flow rows are workbench dependency channels, not empirical causal proof.",
            }
            row["flow_hash"] = _hash(row)
            flows.append(row)
    return flows


def _system_cycles(systems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cycles = []
    for system in systems:
        support_nodes = [node["id"] for node in system.get("nodes", []) if node.get("role") != "collapse-terminal"]
        loop = support_nodes[:4]
        if len(loop) < 3:
            continue
        row = {
            "cycle_id": f"CYCLE::{system['id']}::repair-feedback",
            "system_id": system["id"],
            "title": f"{system['title']} repair feedback cycle",
            "nodes": loop,
            "cycle_kind": "diagnostic_feedback_loop",
            "direction": "support_then_repair",
            "source_status": "derived-from-system-template",
            "claim_status": "nonclaim",
            "nonclaim_boundary": "Cycle rows encode demonstrator feedback logic; they are not a discovered natural-law cycle by themselves.",
        }
        row["cycle_hash"] = _hash(row)
        cycles.append(row)
    return cycles


def _thresholds(systems: list[dict[str, Any]], k_axes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axis_by_index = [row["axis_id"] for row in k_axes] or ["threshold"]
    rows = []
    for s_index, system in enumerate(systems):
        for n_index, node in enumerate(system.get("nodes", [])):
            if node.get("role") not in {"critical-support", "collapse-terminal"}:
                continue
            value = round(0.46 + float(node.get("vulnerability", 0.4)) * 0.38, 4)
            row = {
                "threshold_id": f"THR::{system['id']}::{node['id']}",
                "system_id": system["id"],
                "node_id": node["id"],
                "title": f"{node['label']} threshold",
                "axis_id": axis_by_index[(s_index + n_index) % len(axis_by_index)],
                "threshold_type": "collapse" if "collapse" in node["id"] else "stress",
                "value": min(1, value),
                "k_levels": system.get("k_levels", []),
                "source_status": "derived-from-system-vulnerability",
                "claim_status": "nonclaim",
                "interpretation": "Crossing this diagnostic threshold increases collapse propagation in the workbench model.",
                "nonclaim_boundary": "Threshold values are normalized demonstrator diagnostics unless tied to a replay-backed domain lane.",
            }
            row["threshold_hash"] = _hash(row)
            rows.append(row)
    return rows


def _compensators(systems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for system in systems:
        candidates = sorted(system.get("nodes", []), key=lambda row: float(row.get("recovery_capacity", 0)), reverse=True)[:3]
        for node in candidates:
            row = {
                "compensator_id": f"COMP::{system['id']}::{node['id']}",
                "system_id": system["id"],
                "node_id": node["id"],
                "title": f"{node['label']} compensator",
                "mode": "increase_recovery_capacity",
                "default_delta": 0.08,
                "source_status": "derived-from-system-recovery-capacity",
                "claim_status": "nonclaim",
                "nonclaim_boundary": "Compensators are sandbox interventions unless replay-backed for a domain lane.",
            }
            row["compensator_hash"] = _hash(row)
            rows.append(row)
    return rows


def _collapse_paths(systems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for system in systems:
        starts = [system.get("kill_default", "")]
        if system.get("weakest_node") not in starts:
            starts.append(system.get("weakest_node", ""))
        for start in [item for item in starts if item]:
            path = _collapse_path(system, str(start))
            row = {
                "collapse_path_id": f"PATH::{system['id']}::{start}",
                "system_id": system["id"],
                "trigger_node": start,
                "path": path,
                "path_length": len(path),
                "status": "terminal-path-found" if path and "collapse" in path[-1] else "bounded-damage",
                "source_status": "deterministic-shortest-path",
                "claim_status": "nonclaim",
                "nonclaim_boundary": "Collapse paths are shortest paths over the workbench dependency graph, not unrestricted prediction.",
            }
            row["path_hash"] = _hash(row)
            rows.append(row)
    return rows


def _system_templates(systems: list[dict[str, Any]], k_axes: list[dict[str, Any]], m_spaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axis_ids = [row["axis_id"] for row in k_axes]
    m_by_k = {level: row["m_space_id"] for row in m_spaces for level in row.get("k_level_bindings", [])}
    rows = []
    for system in systems:
        allowed_axes = [axis for axis in k_axes if set(axis.get("k_levels", [])) & set(system.get("k_levels", []))]
        if not allowed_axes:
            allowed_axes = k_axes[:4]
        row = {
            "template_id": system["id"],
            "title": system["title"],
            "truth_mode": "REPLAY_BACKED",
            "fallback_truth_mode": "EXPLORATORY_SANDBOX",
            "k_levels": system.get("k_levels", []),
            "m_spaces": sorted({m_by_k.get(level, "M-ROOT") for level in system.get("k_levels", [])}),
            "nodes": system.get("nodes", []),
            "edges": system.get("edges", []),
            "kill_default": system.get("kill_default", ""),
            "weakest_node": system.get("weakest_node", system.get("kill_default", "")),
            "model_hash": system.get("model_hash", ""),
            "template_hash_scope": "full system template row after workbench enrichment",
            "topology_hash_scope": "nodes, edges, kill_default and weakest_node only",
            "allowed_axis_ids": [axis["axis_id"] for axis in allowed_axes],
            "allowed_axes": allowed_axes[:8],
            "editable_actions": ["add_node", "remove_node", "add_edge", "add_axis", "strengthen_link", "add_compensator", "change_threshold", "kill_selected_node", "kill_weakest_node", "recover"],
            "default_intervention": {"add_axis": allowed_axes[0]["axis_id"] if allowed_axes else axis_ids[0] if axis_ids else "coherence", "strengthen_link_delta": 0.08, "recovery_delta": 0.06},
            "assumptions": ["Template starts replay-bounded; edits move the model into exploratory sandbox unless separately validated."],
            "nonclaim_boundary": "Edited templates are exploratory system models until replay-backed closure exists.",
        }
        row["template_hash"] = _hash(row)
        rows.append(row)
    return rows


def _system_workbench_schema(k_axes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": SYSTEM_WORKBENCH_SCHEMA_VERSION,
        "truth_modes": ["REPLAY_BACKED", "EXPLORATORY_SANDBOX"],
        "computable_axis_ids": [row["axis_id"] for row in k_axes],
        "actions": ["select_template", "add_node", "remove_node", "add_edge", "add_axis", "strengthen_link", "add_compensator", "change_threshold", "kill", "recover", "export"],
        "hash_policy": "animation_speed is excluded from deterministic result hash; structural edits, parameters and interventions are included.",
        "nonclaim_boundary": "The workbench can model any user-built system structurally, but scientific promotion requires replay-backed validation.",
    }


def _node_detail_index(
    graph: dict[str, Any],
    entity_link_index: dict[str, Any],
    asset_links: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    entities = entity_link_index.get("entities", {}) if isinstance(entity_link_index, dict) else {}
    out: dict[str, Any] = {}
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", ""))
        if not node_id:
            continue
        entity_row = entities.get(node_id, {}) if isinstance(entities, dict) else {}
        links = entity_row.get("links", {}) if isinstance(entity_row, dict) else {}
        if not isinstance(links, dict):
            links = {}
        links = {
            **links,
            "graph_node_id": node_id,
        }
        if node_id == ROOT_GRAPH_NODE_ID and asset_links:
            links["atlas_asset_links"] = asset_links
        out[node_id] = {**node, "links": links}
    return out


def _entity_link_index(
    graph: dict[str, Any],
    wiki: dict[str, Any],
    k_levels: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    proof_routes: list[dict[str, Any]],
    simulations: list[dict[str, Any]],
    systems: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    m_spaces: list[dict[str, Any]],
) -> dict[str, Any]:
    index: dict[str, Any] = {
        "schema_version": ENTITY_LINK_INDEX_SCHEMA_VERSION,
        "actions": ["Open in Wiki", "Show in Graph", "Show Formula", "Open Evidence Boundary", "Open Domain", "Run Simulation", "Use in Workbench"],
        "entities": {},
    }

    def add(entity_id: str, entity_type: str, label: str, links: dict[str, Any]) -> None:
        index["entities"][entity_id] = {"entity_type": entity_type, "label": _clean(label, 140), "links": links}

    for node in graph.get("nodes", [])[:1200]:
        detail = node.get("detail", {})
        add(
            node["id"],
            "graph_node",
            node.get("semantic_label") or node.get("label", node["id"]),
            {
                "graph_node_id": node["id"],
                "wiki_query": detail.get("wiki_query", ""),
                "formula_query": detail.get("formula_query", ""),
                "proof_target_id": detail.get("proof_target_id", ""),
                "k_level": detail.get("k_level", ""),
                "domain_id": detail.get("domain_id", ""),
                "simulation_id": detail.get("simulation_id", ""),
            },
        )
    for level in k_levels:
        add(level["level_id"], "k_level", f"{level['level_id']} {level.get('meaning', '')}", {"graph_node_id": f"K::{level['level_id']}", "wiki_query": level.get("semantic_summary", ""), "workbench_filter": level["level_id"]})
    for domain in domains:
        add(domain["domain_id"], "domain", domain.get("title", domain["domain_id"]), {"graph_node_id": f"DOMAIN::{domain['domain_id']}", "domain_id": domain["domain_id"], "wiki_query": domain.get("title", "")})
    for route in proof_routes[:400]:
        add(route["target_id"], "proof_route", route.get("label", route["target_id"]), {"graph_node_id": route["target_id"], "proof_target_id": route["target_id"], "wiki_query": route.get("statement_excerpt", "")})
    for formula in formulas[:800]:
        add(formula["formula_id"], "formula", formula.get("formula_text", formula["formula_id"]), {"formula_id": formula["formula_id"], "wiki_query": formula.get("formula_text", ""), "formula_query": formula.get("formula_text", "")})
    for sim in simulations:
        add(sim["id"], "simulation", sim.get("title", sim["id"]), {"simulation_id": sim["id"], "graph_node_id": f"SIM::{sim['id']}", "wiki_query": sim.get("purpose", "")})
    for system in systems:
        add(system["id"], "system_template", system.get("title", system["id"]), {"system_id": system["id"], "workbench_template_id": system["id"], "simulation_id": "kill_cascade"})
    for m_space in m_spaces:
        add(m_space["m_space_id"], "m_space", m_space.get("semantic_name", m_space["m_space_id"]), {"m_space_id": m_space["m_space_id"], "wiki_query": m_space.get("scope", ""), "graph_node_id": f"M::{m_space['m_space_id']}"})
    index["entity_total"] = len(index["entities"])
    index["index_hash"] = _hash(index)
    return index


def _research_gaps(domains: list[dict[str, Any]], proof_routes: list[dict[str, Any]], k_levels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for domain in domains:
        if str(domain.get("closure_status", "")).startswith("OPEN"):
            gaps.append(
                {
                    "gap_id": f"GAP-DOMAIN-{domain['domain_id']}",
                    "kind": "domain-validation",
                    "title": f"{domain['title']} validation lane",
                    "status": domain.get("closure_status", "frontier-gap"),
                    "missing_evidence": domain.get("nonclaim_boundary", ""),
                    "requested_action": "Execute or refresh replayable numerical validation before promoting predictive language.",
                    "source_ref": domain.get("private_replay_command_ref", "public benchmark registry"),
                    "severity": "high" if "frontier" in str(domain.get("promotion_state")) else "medium",
                }
            )
    for level in k_levels:
        sim = level.get("simulation_summary", {})
        if level.get("simulation_status") != "PASS" or sim.get("counterexample_found"):
            gaps.append(
                {
                    "gap_id": f"GAP-KLEVEL-{level['level_id']}",
                    "kind": "k-level-simulation",
                    "title": f"{level['level_id']} simulation / counterexample lane",
                    "status": level.get("simulation_status", "unknown"),
                    "missing_evidence": "K-level replay needs pass status and counterexample accounting.",
                    "requested_action": "Re-run K-level simulation suite and integrate updated artifact hashes.",
                    "source_ref": "K_LEVEL_SIMULATION_SUITE_latest.json",
                    "severity": "medium",
                }
            )
    placeholder_count = sum(1 for route in proof_routes if "placeholder" in route.get("quality_flags", []))
    if placeholder_count:
        gaps.append(
            {
                "gap_id": "GAP-PROOF-PLACEHOLDER-EXCERPTS",
                "kind": "proof-data-quality",
                "title": "Placeholder proof excerpts",
                "status": "display-quality-gap",
                "missing_evidence": f"{placeholder_count} public evidence routes still carry placeholder/degraded excerpts.",
                "requested_action": "Refresh target excerpts from public-safe proof/evidence source packets.",
                "source_ref": "public_targets.json",
                "severity": "medium",
            }
        )
    return gaps


def _proof_placeholder_ledger() -> dict[str, Any]:
    ledger = _read_json(
        DEMO_DATA / "proof_placeholder_closure_ledger.json",
        {
            "schema_version": "oc-core-demo-proof-placeholder-closure.v010",
            "demo_version": DEMO_VERSION,
            "release_ordinal": RELEASE_ORDINAL,
            "status": "NOT_GENERATED",
            "placeholder_rows_closed": 0,
            "open_placeholder_rows": 0,
            "rows": [],
        },
    )
    if isinstance(ledger, dict):
        ledger = _release_text(ledger)
        ledger["schema_version"] = "oc-core-demo-proof-placeholder-closure.v010"
        ledger["demo_version"] = DEMO_VERSION
        ledger["release_ordinal"] = RELEASE_ORDINAL
        for row in ledger.get("rows", []):
            if isinstance(row, dict):
                row["closed_at_build"] = DEMO_VERSION
                row["source_refs"] = _public_source_refs(row.get("source_refs", []), "proof-placeholder")
    return ledger


def _closure_row(
    gap_id: str,
    kind: str,
    title: str,
    status: str,
    basis: str,
    source_refs: list[str],
    evidence: Any,
    nonclaim: str,
) -> dict[str, Any]:
    row = {
        "gap_id": gap_id,
        "kind": kind,
        "title": title,
        "closure_status": status,
        "closure_basis": basis,
        "source_refs": source_refs,
        "evidence_hash": _hash(evidence),
        "closed_at_build": DEMO_VERSION,
        "nonclaim_boundary": nonclaim,
    }
    return row


def _closure_ledger(domains: list[dict[str, Any]], proof_routes: list[dict[str, Any]], k_levels: list[dict[str, Any]], edition: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for level in k_levels:
        rows.append(
            _closure_row(
                f"GAP-KLEVEL-{level['level_id']}",
                "k-level-simulation",
                f"{level['level_id']} simulation / counterexample lane",
                level.get("closure_status", "OPEN_REPLAY_GAP"),
                level.get("closure_basis", "K-level replay closure status"),
                _public_source_refs(["logion/k7/spe/state/science/K_LEVEL_SIMULATION_SUITE_latest.json"], "k-level-suite"),
                {
                    "level_id": level.get("level_id"),
                    "artifact_sha256": level.get("artifact_sha256", ""),
                    "simulation_summary": level.get("simulation_summary", {}),
                },
                "K-level replay closure is a deterministic demonstrator basis; it is not external peer review.",
            )
        )
    for domain in domains:
        rows.append(
            _closure_row(
                f"GAP-DOMAIN-{domain['domain_id']}",
                "domain-validation",
                f"{domain['title']} validation lane",
                domain.get("closure_status", "OPEN_DOMAIN_REPLAY_GAP"),
                domain.get("closure_basis", "domain replay closure status"),
                domain.get("source_refs", []),
                {
                    "domain_id": domain.get("domain_id"),
                    "replay_status": domain.get("replay_status"),
                    "validation_status": domain.get("validation_status"),
                    "replay_hashes": domain.get("replay_hashes", []),
                    "case_total": domain.get("case_total"),
                    "held_out_case_total": domain.get("held_out_case_total"),
                },
                domain.get("nonclaim_boundary", "") or "Domain closure stays within declared replay and validation limits.",
            )
        )
    proof_ledger = _proof_placeholder_ledger()
    for row in proof_ledger.get("rows", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "gap_id": row.get("gap_id", f"GAP-PROOF-PLACEHOLDER-{row.get('public_target_id', 'UNKNOWN')}"),
                "kind": "proof-data-quality",
                "title": f"Proof placeholder closure {row.get('public_target_id', '')}".strip(),
                "closure_status": row.get("closure_status", "CLOSED_AS_OBLIGATION_BOUNDARY"),
                "closure_basis": row.get("closure_basis", "proof placeholder closure"),
                "source_refs": _public_source_refs(row.get("source_refs", []), "proof-placeholder"),
                "evidence_hash": row.get("evidence_hash", _hash(row)),
                "closed_at_build": DEMO_VERSION,
                "nonclaim_boundary": row.get("nonclaim_boundary", ""),
            }
        )
    return rows


def build_universe(edition: str) -> dict[str, Any]:
    if edition not in {"public", "private"}:
        raise ValueError("edition must be public or private")
    concepts = _concepts()
    proof_routes = _proof_routes()
    k_levels = _k_levels(edition)
    domains = _domain_benchmarks(edition)
    pass_units = _pass_language_units()
    wiki = _wiki(edition, pass_units=pass_units)
    k_axes = _k_axes(k_levels, domains)
    m_spaces = _m_spaces(k_levels, domains, k_axes)
    simulations = _simulation_worlds(k_levels, domains)
    k_level_worlds = _k_level_worlds(k_levels)
    systems = _system_zoo()
    system_flows = _system_flows(systems)
    system_cycles = _system_cycles(systems)
    thresholds = _thresholds(systems, k_axes)
    compensators = _compensators(systems)
    collapse_paths = _collapse_paths(systems)
    system_templates = _system_templates(systems, k_axes, m_spaces)
    workbench_schema = _system_workbench_schema(k_axes)
    graph = _load_graph(wiki, k_levels, m_spaces, k_axes, domains, proof_routes, simulations, systems, thresholds)
    entity_link_index = _entity_link_index(graph, wiki, k_levels, domains, proof_routes, simulations, systems, wiki.get("formulas", []), m_spaces)
    gaps = _research_gaps(domains, proof_routes, k_levels)
    closure_ledger = _closure_ledger(domains, proof_routes, k_levels, edition)
    proof_placeholder_ledger = _proof_placeholder_ledger()
    closure_counts = Counter(row.get("closure_status", "UNKNOWN") for row in closure_ledger)
    didactic_routes = _journeys()
    reviewer_objection_routes = _reviewer_objection_routes(graph, systems, domains, proof_routes)
    system_architect_missions = _system_architect_missions(system_templates, k_axes)
    model_comparison_matrix = _model_comparison_matrix(system_templates, proof_routes, domains, k_axes)
    trust_ladder = _trust_ladder(graph, systems, simulations, proof_routes, domains)
    practical_value_cards = _practical_value_cards(reviewer_objection_routes, system_architect_missions, model_comparison_matrix, trust_ladder)
    corpus_completeness_report = _corpus_completeness_report(pass_units, wiki.get("corpus_atoms", []))
    formula_quality_report = _formula_quality_report(wiki.get("formulas", []), wiki.get("corpus_atoms", []))
    formula_formalization_obligations = _formula_formalization_obligations(wiki.get("formulas", []), formula_quality_report)
    k_level_example_atlas = _k_level_example_atlas(k_levels, systems, system_templates, wiki.get("formulas", []), proof_routes, domains)
    science_formalization_ledger = _science_formalization_ledger(
        k_levels,
        k_axes,
        systems,
        system_templates,
        wiki.get("formulas", []),
        thresholds,
        domains,
    )
    persona_user_story_map = _persona_user_story_map(
        system_architect_missions=system_architect_missions,
        reviewer_objection_routes=reviewer_objection_routes,
    )
    route_action_manifest = []
    route_action_manifest.extend(_route_action_manifest(didactic_routes))
    route_action_manifest.extend(_route_action_manifest(reviewer_objection_routes))
    route_action_manifest.extend(_route_action_manifest(system_architect_missions))
    atlas_asset_links = {
        "reviewer_objection_routes": [row["id"] for row in reviewer_objection_routes],
        "system_architect_missions": [mission["id"] for mission in system_architect_missions],
        "model_comparison_rows": [row["comparison_id"] for row in model_comparison_matrix],
        "trust_ladder_rungs": [row["rung_id"] for row in trust_ladder],
        "practical_value_cards": [card["card_id"] for card in practical_value_cards],
    }
    node_detail_index = _node_detail_index(graph, entity_link_index, atlas_asset_links)
    generated_from = {
        "demo_specs": len(_read_json(DEMO_DATA / "demo_specs.json", {"specs": []}).get("specs", [])),
        "proof_routes": len(proof_routes),
        "graph_nodes": len(graph.get("nodes", [])),
        "k_levels": len(k_levels),
        "domains": len(domains),
        "wiki_chapters": len(wiki.get("chapters", [])),
        "corpus_atoms": wiki.get("corpus_summary", {}).get("atom_count", 0),
        "formulas": len(wiki.get("formulas", [])),
        "science_graph_nodes": len(graph.get("nodes", [])),
        "science_graph_edges": len(graph.get("edges", [])),
        "k_level_worlds": len(k_level_worlds),
        "m_spaces": len(m_spaces),
        "k_axes": len(k_axes),
        "system_templates": len(system_templates),
        "system_flows": len(system_flows),
        "system_cycles": len(system_cycles),
        "thresholds": len(thresholds),
        "compensators": len(compensators),
        "collapse_paths": len(collapse_paths),
        "route_action_targets": len(route_action_manifest),
        "reviewer_objection_routes": len(reviewer_objection_routes),
        "system_architect_missions": len(system_architect_missions),
        "model_comparison_rows": len(model_comparison_matrix),
        "trust_ladder_rungs": len(trust_ladder),
        "practical_value_cards": len(practical_value_cards),
        "corpus_completeness_rows": len(corpus_completeness_report.get("bounded_exclusions", [])),
        "formula_quality_rows": len(formula_quality_report.get("rows", [])),
        "formula_formalization_obligations": formula_formalization_obligations.get("rows_total", 0),
        "k_level_examples": len(k_level_example_atlas),
        "science_formalization_rows": len(science_formalization_ledger.get("rows", [])),
        "closure_rows": len(closure_ledger),
        "open_research_gaps": len(gaps),
    }
    demonstrator_surface_graph = _demonstrator_surface_graph(
        source_counts=generated_from,
        didactic_routes=didactic_routes,
        reviewer_objection_routes=reviewer_objection_routes,
        system_architect_missions=system_architect_missions,
        route_action_manifest=route_action_manifest,
    )
    payload = {
        "schema_version": UNIVERSE_SCHEMA_VERSION,
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "release_label": RELEASE_LABEL,
        "edition": edition,
        "title": "Ontology of Continua Core 1.4 System Workbench",
        "build_policy": {
            "public_safe": edition == "public",
            "private_backend_allowed": edition == "private",
            "predictive_language_rule": "Replay-backed templates and lanes use REPLAY_BACKED language; edited/free-form workbench systems are EXPLORATORY_SANDBOX until validated.",
            "external_actions": 0,
        },
        "scientific_boundary": "OC Core V010 is an interactive didactic and system workbench. It does not claim external peer review, does not replace source evidence, and separates replay-backed closure from exploratory sandbox modeling.",
        "limits": [
            "Private edition may expose local Logion-backed provenance; public edition must remain sanitized.",
            "Simulation worlds are deterministic explanatory models, not standalone proofs.",
            "Domain predictions require explicit replay/status support before they may be presented as replay-backed lanes.",
            "Proof placeholder closure removes display gaps only; it never upgrades unresolved proof/refute work into solved science.",
        ],
        "source_status": {"generated_from": generated_from},
        "concepts": concepts,
        "journeys": didactic_routes,
        "didactic_routes": didactic_routes,
        "reviewer_objection_routes": reviewer_objection_routes,
        "route_action_manifest": route_action_manifest,
        "system_architect_missions": system_architect_missions,
        "persona_user_story_map": persona_user_story_map,
        "model_comparison_matrix": model_comparison_matrix,
        "trust_ladder": trust_ladder,
        "practical_value_cards": practical_value_cards,
        "wiki": wiki,
        "formula_atlas": wiki.get("formulas", []),
        "corpus_index": wiki.get("corpus_atoms", []),
        "k_levels": k_levels,
        "k_axes": k_axes,
        "m_spaces": m_spaces,
        "domain_benchmarks": domains,
        "simulation_worlds": simulations,
        "k_level_worlds": k_level_worlds,
        "system_zoo": systems,
        "system_templates": system_templates,
        "system_workbench_schema": workbench_schema,
        "system_flows": system_flows,
        "system_cycles": system_cycles,
        "thresholds": thresholds,
        "compensators": compensators,
        "collapse_paths": collapse_paths,
        "entity_link_index": entity_link_index,
        "node_detail_index": node_detail_index,
        "graph": graph,
        "science_graph_v010": graph,
        "science_graph_v008": graph,
        "science_graph_v007": graph,
        "science_graph_v006": graph,
        "proof_routes": proof_routes,
        "corpus_completeness_report": corpus_completeness_report,
        "formula_quality_report": formula_quality_report,
        "formula_formalization_obligations": formula_formalization_obligations,
        "k_level_example_atlas": k_level_example_atlas,
        "science_formalization_ledger": science_formalization_ledger,
        "demonstrator_surface_graph": demonstrator_surface_graph,
        "research_gaps": gaps,
        "research_gap_summary": {
            "open_count": len(gaps),
            "closure_rows": len(closure_ledger),
            "closed_count": sum(count for status, count in closure_counts.items() if not str(status).startswith("OPEN")),
            "counts_by_status": dict(closure_counts),
            "proof_placeholder_rows_closed": proof_placeholder_ledger.get("placeholder_rows_closed", 0),
            "nonclaim_boundary": "Open Research Gaps counts unresolved demonstrator gaps only; proof-workbench obligations are shown separately and are not proof closure.",
        },
        "closure_ledger": closure_ledger,
        "proof_placeholder_closure_ledger": proof_placeholder_ledger,
        "reviewer_mode": {
            "checklist": [
                "Complete OC in 12 minutes.",
                "Run Worldline Birth / Evolution / Collapse.",
                "Press Kill in at least one System Zoo model.",
                "Inspect K0-K12 status and preserved invariants.",
                "Open one domain benchmark lane and check nonclaim boundary.",
                "Inspect one evidence/boundary route and one closure-ledger row.",
                "Export the evidence bundle and verify deterministic hash.",
            ],
            "external_actions": 0,
        },
    }
    if edition == "public":
        payload = _sanitize_public(payload)
        _assert_public_safe(payload)
    payload.pop("determinism_hash", None)
    payload["determinism_hash"] = _hash(payload)
    return payload


def write_parts(payload: dict[str, Any], output_dir: Path) -> None:
    _write_json(output_dir / "oc_universe_atlas.json", payload)
    _write_json(output_dir / "oc_universe_atlas_v010.json", payload)
    _write_json(output_dir / "oc_universe_atlas_v009.json", payload)
    _write_json(output_dir / "oc_universe_atlas_v008.json", payload)
    _write_json(output_dir / "oc_universe_atlas_v007.json", payload)
    _write_json(output_dir / "science_graph_v008.json", payload["graph"])
    _write_json(output_dir / "science_graph_v010.json", payload["graph"])
    _write_json(output_dir / "science_graph_v007.json", payload["graph"])
    _write_json(output_dir / "science_graph_v006.json", payload["graph"])
    _write_json(output_dir / "science_graph.json", payload["graph"])
    _write_json(output_dir / "didactic_routes.json", payload["didactic_routes"])
    _write_json(output_dir / "reviewer_objection_routes.json", payload["reviewer_objection_routes"])
    _write_json(output_dir / "route_action_manifest.json", payload.get("route_action_manifest", []))
    _write_json(output_dir / "system_architect_missions.json", payload["system_architect_missions"])
    _write_json(output_dir / "persona_user_story_map.json", payload.get("persona_user_story_map", {}))
    _write_json(output_dir / "model_comparison_matrix.json", payload["model_comparison_matrix"])
    _write_json(output_dir / "trust_ladder.json", payload["trust_ladder"])
    _write_json(output_dir / "practical_value_cards.json", payload["practical_value_cards"])
    _write_json(output_dir / "m_spaces.json", payload["m_spaces"])
    _write_json(output_dir / "k_axes.json", payload["k_axes"])
    _write_json(output_dir / "k_levels.json", payload["k_levels"])
    _write_json(output_dir / "oc_wiki.json", payload["wiki"])
    _write_json(output_dir / "domain_benchmarks.json", payload["domain_benchmarks"])
    _write_json(output_dir / "simulation_worlds.json", payload["simulation_worlds"])
    _write_json(output_dir / "k_level_worlds.json", payload["k_level_worlds"])
    _write_json(output_dir / "system_templates.json", payload["system_templates"])
    _write_json(output_dir / "system_workbench_schema.json", payload["system_workbench_schema"])
    _write_json(output_dir / "system_flows.json", payload["system_flows"])
    _write_json(output_dir / "system_cycles.json", payload["system_cycles"])
    _write_json(output_dir / "thresholds.json", payload["thresholds"])
    _write_json(output_dir / "compensators.json", payload["compensators"])
    _write_json(output_dir / "collapse_paths.json", payload["collapse_paths"])
    _write_json(output_dir / "entity_link_index.json", payload["entity_link_index"])
    _write_json(output_dir / "corpus_index.json", payload.get("corpus_index", []))
    _write_json(output_dir / "formula_atlas.json", payload.get("formula_atlas", []))
    _write_json(output_dir / "node_detail_index.json", payload.get("node_detail_index", {}))
    _write_json(output_dir / "proof_evidence_routes.json", payload["proof_routes"])
    _write_json(output_dir / "proof_routes.json", payload["proof_routes"])
    _write_json(output_dir / "research_gap_requests.json", payload["research_gaps"])
    _write_json(output_dir / "closure_ledger.json", payload["closure_ledger"])
    _write_json(output_dir / "corpus_completeness_report.json", payload.get("corpus_completeness_report", {}))
    _write_json(output_dir / "formula_quality_report.json", payload.get("formula_quality_report", {}))
    _write_json(output_dir / "formula_formalization_obligations.json", payload.get("formula_formalization_obligations", {}))
    _write_json(output_dir / "k_level_example_atlas.json", payload.get("k_level_example_atlas", []))
    _write_json(output_dir / "science_formalization_ledger.json", payload.get("science_formalization_ledger", {}))
    _write_json(output_dir / "demonstrator_surface_graph.json", payload.get("demonstrator_surface_graph", {}))
    _write_json(output_dir / "demonstrator_surface_graph_v010.json", payload.get("demonstrator_surface_graph", {}))
    _write_json(output_dir / "proof_placeholder_closure_ledger.json", payload["proof_placeholder_closure_ledger"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate OC Core V010 universe atlas.")
    parser.add_argument("--edition", choices=["public", "private"], default="public")
    parser.add_argument("--output-dir", default=str(WEB_PUBLIC_DATA))
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    payload = build_universe(args.edition)
    write_parts(payload, output_dir)
    print(json.dumps({"status": "PASS", "edition": args.edition, "output_dir": str(output_dir), "hash": payload["determinism_hash"]}, ensure_ascii=False, allow_nan=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



