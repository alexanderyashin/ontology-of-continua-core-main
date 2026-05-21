from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "oc_core_demo", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def test_cli_examples_pass() -> None:
    commands = [
        ("list",),
        ("cases",),
        ("export",),
        ("run", "transformation_risk_calculator", "--params", "examples/transform_risk_params.json"),
        ("run", "coherence_debt_calculator", "--params", "examples/calculator_params.json"),
        ("run", "transition_pressure_lab", "--params", "examples/threshold_params.json"),
        ("analyze-case", "--params", "examples/case_params.json"),
        ("graph", "--node", "OC14-N001", "--radius", "2"),
        ("science-graph", "--summary-only"),
        ("explain", "case_diagnostic", "--json"),
        ("atlas", "--edition", "public"),
        ("simulate", "worldline_birth_evolution_collapse"),
        ("kill", "--system-id", "civilization"),
        ("kill", "--system-id", "civilization", "--mode", "weakest"),
        ("predict", "--domain-id", "PHYSICS"),
        ("corpus", "--query", "continuum", "--limit", "3"),
        ("formula", "--query", "K", "--limit", "3"),
        ("node-detail", "OC14-N001"),
        ("research-gaps",),
        ("closure-ledger",),
        ("m-space",),
        ("system-templates",),
        ("didactic-route",),
        ("reviewer-objections",),
        ("model-comparison",),
        ("architect-missions",),
        ("trust-ladder",),
        ("quality-report",),
        ("corpus-completeness",),
        ("formula-quality",),
        ("formula-quality", "--strict"),
        ("k-examples",),
        ("surface-graph", "--summary-only"),
        ("simulate-system", "civilization", "--kill-node", "CIV-005"),
        ("verify-public-safety", "web/public/data"),
        ("cerberus", "--version", "V010", "--zero-findings"),
        ("desktop-smoke",),
    ]
    for command in commands:
        proc = _run(*command)
        payload = json.loads(proc.stdout)
        if command[0] in {"cerberus", "desktop-smoke"}:
            assert proc.returncode in {0, 2}, proc.stderr
            assert payload["status"] in {"PASS", "FAIL_CLOSED"}
        else:
            assert proc.returncode == 0, proc.stderr
            assert payload["status"] == "PASS"


def test_v010_cli_outputs_have_boundaries_corpus_and_closure() -> None:
    proc = _run("simulate", "k_level_elevator")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "oc-core-demo-api.v010"
    assert payload["demo_version"] == "V010"
    assert payload["payload"]["simulation_id"] == "k_level_elevator"
    assert "scientific_boundary" in payload

    proc = _run("m-space", "M-ROOT")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "PASS"
    assert payload["payload"]["m_space_id"] == "M-ROOT"

    proc = _run("system-templates", "physical-phase")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "PASS"
    assert payload["payload"]["template_id"] == "physical-phase"

    proc = _run("didactic-route", "oc_in_12_minutes")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "PASS"
    assert payload["payload"]["route_id"] == "oc_in_12_minutes"

    proc = _run("reviewer-objections")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["count"] >= 3

    proc = _run("model-comparison")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["count"] >= 1
    assert all("oc_adds" in row and "does_not_replace" in row and "when_not_to_use" in row for row in payload["payload"]["rows"])

    proc = _run("architect-missions")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["count"] >= 1

    proc = _run("trust-ladder")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["count"] >= 4

    proc = _run("research-gaps", "--subject", "PHYSICS")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["status"] == "NO_OPEN_RESEARCH_GAP"
    assert payload["payload"]["open_count"] == 0

    proc = _run("closure-ledger", "--subject", "PHYSICS")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["open_count"] == 0
    assert payload["payload"]["closed_count"] >= 1

    proc = _run("corpus", "--query", "threshold", "--limit", "2")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["returned"] >= 1
    assert payload["payload"]["corpus_summary"]["atom_count"] >= 1000

    proc = _run("kill", "--system-id", "civilization", "--mode", "weakest")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["mode"] == "weakest"
    assert payload["payload"]["connectivity_loss"] > 0

    proc = _run("surface-graph", "--summary-only")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["payload"]["status"] == "PASS"
    assert payload["payload"]["summary"]["surface_count"] >= 19
    assert payload["payload"]["prebuild_gate"]["required_before_release"] is True


def test_cli_invalid_spec_fails_without_traceback() -> None:
    proc = _run("explain", "bogus")
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert payload["spec_id"] == "bogus"


def test_cli_bad_params_file_fails_closed() -> None:
    proc = _run("run", "case_diagnostic", "--params", "examples/missing.json")
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert "could not read params file" in payload["message"]


def test_v010_desktop_smoke_verifies_runtime_freshness() -> None:
    proc = _run("desktop-smoke")
    payload = json.loads(proc.stdout)

    assert payload["schema_version"] == "oc-core-demo-api.v010"
    assert payload["demo_version"] == "V010"
    assert payload["release_ordinal"] == "010"
    assert payload["kind"] == "desktop-smoke"
    assert payload["status"] in {"PASS", "FAIL_CLOSED"}
    probe = payload["payload"]

    assert probe["schema_version"] == "oc-core-demo-desktop-smoke.v010"
    assert probe["demo_version"] == "V010"
    assert probe["release_ordinal"] == "010"
    assert probe["shortcut_exists"] in (True, False)
    assert isinstance(probe["shortcut_path_hash"], str) and len(probe["shortcut_path_hash"]) == 64
    assert isinstance(probe["result_hash"], str) and len(probe["result_hash"]) == 64
    assert isinstance(probe.get("runtime_freshness_manifest_found"), bool)
    assert isinstance(probe.get("freshness_checks"), dict)
    assert isinstance(probe.get("workspace_determinism_hash"), str)
    assert isinstance(probe.get("runtime_determinism_hash"), str)
    assert probe["status"] in {"PASS", "FAIL_CLOSED"}
    assert isinstance(probe["target_exists"], bool)
    assert isinstance(probe["working_directory_exists"], bool)
    assert isinstance(probe["points_to_v010_runtime"], bool)
    assert isinstance(probe["result_hash"], str) and len(probe["result_hash"]) == 64

    if probe["shortcut_exists"]:
        assert probe["target_exists"] is True
        assert probe["working_directory_exists"] is True
        assert probe["points_to_v010_runtime"] is True
        assert probe["target_basename"] == "OC_Core_1_4_Demonstrator.exe"
        assert probe["working_directory_basename"] == "OC_Core_1_4_Demonstrator"
        assert "OC_Core_1_4_Demonstrator" in probe["target_basename"]
        assert isinstance(probe["target_path_hash"], str) and len(probe["target_path_hash"]) == 64
        assert isinstance(probe["working_directory_hash"], str) and len(probe["working_directory_hash"]) == 64
        assert isinstance(probe.get("icon_present"), bool)
        assert isinstance(probe.get("workspace_atlas_found"), bool)
        assert isinstance(probe.get("runtime_atlas_found"), bool)
        assert isinstance(probe.get("runtime_matches_workspace"), bool)
        assert isinstance(probe.get("workspace_formula_count"), int)
        assert isinstance(probe.get("runtime_formula_count"), int)
        assert set(probe["freshness_checks"]).issuperset(
            {
                "runtime_atlas_found",
                "workspace_atlas_found",
                "version_is_v010",
                "atlas_hash_matches",
                "formula_count_matches",
                "surface_graph_hash_matches",
            }
        )
        if probe["status"] == "PASS":
            assert probe["runtime_matches_workspace"] is True
            assert probe["workspace_determinism_hash"] == probe["runtime_determinism_hash"]
            assert probe["workspace_formula_count"] == probe["runtime_formula_count"]
            assert probe["freshness_checks"]["atlas_hash_matches"] is True
            assert probe["freshness_checks"]["formula_count_matches"] is True
            assert probe["freshness_checks"]["surface_graph_hash_matches"] is True
            assert probe["freshness_checks"]["version_is_v010"] is True
            assert probe["runtime_demo_version"] == "V010"
            assert probe["runtime_release_ordinal"] == "010"
            assert payload["status"] == "PASS"
        else:
            assert probe["runtime_matches_workspace"] is False
            assert "stale" in str(probe.get("message", "")) or "missing" in str(probe.get("message", ""))
            assert payload["status"] == "FAIL_CLOSED"
        if "message" in probe:
            assert str(probe["message"]).strip()
    else:
        assert probe["status"] == "FAIL_CLOSED"
        assert probe["message"] == "desktop shortcut not found"
        assert probe["points_to_v010_runtime"] is False


def test_v010_formula_quality_strict_contract() -> None:
    proc = _run("formula-quality", "--strict")
    payload = json.loads(proc.stdout)
    assert proc.returncode in {0, 2}, proc.stderr
    assert payload["schema_version"] == "oc-core-demo-api.v010"
    assert payload["demo_version"] == "V010"
    assert payload["release_ordinal"] == "010"
    assert payload["kind"] == "formula-quality"
    report = payload["payload"]

    assert report["schema_version"] == "oc-core-demo-formula-quality.v010"
    assert report["demo_version"] == "V010"
    assert report["strict_requested"] is True
    assert report["strict_status"] in {"PASS", "FAIL_CLOSED"}
    assert report["missing_expression_count"] == 0
    assert report["missing_formula_id_count"] == 0
    assert report["render_gaps_count"] == 0
    assert report["table_contract_gaps_count"] == 0
    assert report["missing_typed_symbol_signature_count"] == 0
    assert report["missing_chart_provenance_count"] == 0
    assert report["unbounded_source_exception_count"] == 0
    assert report["formula_total"] >= 15
    assert 0.0 <= report["quality_score"] <= 1.0
    assert len(report["sample"]) >= 10
    assert payload["status"] == ("PASS" if report["strict_status"] == "PASS" else "FAIL_CLOSED")
    atlas = json.loads((ROOT / "web/public/data/oc_universe_atlas.json").read_text(encoding="utf-8"))
    all_rows = atlas["formula_atlas"]
    assert report["formula_total"] == len(all_rows)

    for row in report["sample"]:
        assert row["ordinal"] >= 1
        assert isinstance(row.get("formula_id"), str) and row["formula_id"].strip()
        assert isinstance(row.get("formula_text"), str) and row["formula_text"].strip()
        assert isinstance(row.get("semantic_title"), str) and row["semantic_title"].strip()
        assert row["domain"].strip()
        assert isinstance(row.get("operator_glossary"), list) and row["operator_glossary"]
        assert isinstance(row.get("consequences"), list) and row["consequences"]
        assert isinstance(row.get("chart_spec"), dict)
        assert row["source_refs"] or row.get("source_atom_id") or row.get("nonclaim_boundary")
        assert isinstance(row.get("typed_symbol_signatures"), list) and row["typed_symbol_signatures"]
        assert isinstance(row.get("chart_provenance"), dict) and row["chart_provenance"]
        assert isinstance(row.get("source_ref_count", 0), int)
        assert isinstance(row.get("source_linking_profile"), dict)

    for row in all_rows:
        assert row["ordinal"] >= 1
        assert isinstance(row.get("formula_id"), str) and row["formula_id"].strip()
        assert isinstance(row.get("formula_text"), str) and row["formula_text"].strip()
        assert isinstance(row.get("semantic_title"), str) and row["semantic_title"].strip()
        assert isinstance(row.get("formula_title"), str) and row["formula_title"].strip()
        assert isinstance(row.get("domain"), str) and row["domain"].strip()
        assert isinstance(row.get("operator_glossary"), list) and row["operator_glossary"]
        assert isinstance(row.get("consequences"), list) and row["consequences"]
        assert isinstance(row.get("chart_spec"), dict) and row["chart_spec"]
        assert bool(row["source_refs"] or row.get("source_atom_id") or row.get("nonclaim_boundary"))
        assert isinstance(row.get("typed_symbol_signatures"), list) and row["typed_symbol_signatures"]
        assert isinstance(row.get("chart_provenance"), dict) and row["chart_provenance"]
        assert isinstance(row.get("source_ref_count", 0), int)
        assert row.get("source_ref_count", 0) >= 0
        assert isinstance(row.get("source_exceptions"), list)
        if row.get("source_exceptions"):
            assert row.get("source_boundary") or row.get("nonclaim_boundary")


def test_v010_surface_graph_contract_has_routable_controls_and_targets() -> None:
    proc = _run("surface-graph")
    payload = json.loads(proc.stdout)
    assert proc.returncode == 0, proc.stderr
    assert payload["schema_version"] == "oc-core-demo-api.v010"
    assert payload["demo_version"] == "V010"
    assert payload["release_ordinal"] == "010"
    assert payload["kind"] == "surface-graph"

    graph = payload["payload"]
    assert graph["schema_version"] == "oc-core-demo-surface-graph.v010"
    assert graph["demo_version"] == "V010"
    assert graph["release_ordinal"] == "010"
    assert graph["status"] == "PASS"
    summary = graph["summary"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert summary["surface_count"] == 19
    assert summary["surface_count"] == sum(1 for node in nodes if node.get("kind") == "surface")
    assert summary["control_count"] == sum(1 for node in nodes if node.get("kind") == "control")
    assert summary["route_count"] == sum(1 for node in nodes if node.get("kind") == "route")
    assert summary["edge_count"] == len(edges)

    prebuild_gate = graph["prebuild_gate"]
    assert prebuild_gate["required_before_release"] is True
    assert prebuild_gate["status"] == "PASS"
    assert prebuild_gate["orphan_control_ids"] == []
    assert prebuild_gate["dead_route_ids"] == []
    assert isinstance(prebuild_gate.get("count_without_drilldown_surface_ids"), list)
    assert "rules" in prebuild_gate and len(prebuild_gate["rules"]) >= 4
    required_surface_ids = {
        "journey",
        "guided",
        "workbench",
        "km",
        "wiki",
        "formula",
        "klevels",
        "worldline",
        "cascade",
        "benchmarks",
        "objections",
        "whyoc",
        "practical",
        "trust",
        "mission",
        "graph",
        "proof",
        "gaps",
        "reviewer",
    }
    rendered_surfaces = {node.get("surface_id") for node in nodes if node.get("kind") == "surface"}
    assert required_surface_ids <= rendered_surfaces
    node_ids = {node.get("id") for node in nodes}
    surface_targets = {node.get("id"): node.get("id") for node in nodes if node.get("kind") == "surface"}
    surface_targets.update(
        {
            str(node.get("id")).removeprefix("SURFACE::"): node.get("id")
            for node in nodes
            if isinstance(node.get("id"), str) and node.get("kind") == "surface"
        }
    )

    for node in nodes:
        assert node.get("kind") in {"surface", "control", "route"}
        assert isinstance(node.get("id"), str) and node["id"]
        assert isinstance(node.get("purpose"), str) and node["purpose"]
        assert isinstance(node.get("test_id"), str) and node["test_id"]
        if node["kind"] == "route":
            assert isinstance(node.get("source"), str) and node["source"]
            assert isinstance(node.get("target_surface"), str)
            assert node["target_surface"] in surface_targets
            assert isinstance(node.get("expected_visible_result"), str) and node["expected_visible_result"]
        if node["kind"] == "control":
            assert node.get("data_sources") and isinstance(node["data_sources"], list)
            assert node["target_view"] or node["target_surface"] or node.get("state_mutation")
            assert isinstance(node.get("expected_visible_result"), str) and node["expected_visible_result"]

    for edge in edges:
        assert edge.get("source") in node_ids
        assert edge.get("target") in node_ids


def test_v010_resource_lookup_is_fail_closed_on_missing_ids() -> None:
    proc = _run("m-space", "M-0000")
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert "unknown m_space_id" in payload["message"]

    proc = _run("system-templates", "template-does-not-exist")
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert "unknown template_id" in payload["message"]

    proc = _run("didactic-route", "route-does-not-exist")
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert "unknown route_id" in payload["message"]

    proc = _run("simulate-system", "not-a-system")
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert "unknown system/template id" in payload["message"]


