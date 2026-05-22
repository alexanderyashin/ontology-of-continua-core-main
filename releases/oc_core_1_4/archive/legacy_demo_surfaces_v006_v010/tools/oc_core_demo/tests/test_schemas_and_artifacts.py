from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import copy
from pathlib import Path

import pytest

from oc_core_demo.core import list_specs, run_spec, run_spec_safe


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
DIST = ROOT / "dist"


def _forgiving_schema(schema: dict) -> dict:
    payload = copy.deepcopy(schema)
    properties = payload.get("properties", {})
    for key in {"schema_version", "demo_version", "release_ordinal", "release_label"}:
        field = properties.get(key)
        if isinstance(field, dict):
            field.pop("const", None)
            if key == "release_label":
                field.pop("enum", None)
    return payload


def test_schema_files_are_valid_json() -> None:
    schema_files = sorted(SCHEMAS.glob("*.schema.json"))
    assert {path.name for path in schema_files} >= {
        "case_input.schema.json",
        "demo_input.schema.json",
        "demo_output.schema.json",
        "demo_spec.schema.json",
        "failure_output.schema.json",
        "graph_edge.schema.json",
        "graph_node.schema.json",
        "oc_atlas.schema.json",
        "oc_universe_atlas.schema.json",
    }
    for path in schema_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"].startswith("https://json-schema.org/")


def test_schemas_validate_representative_payloads() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    spec_schema = json.loads((SCHEMAS / "demo_spec.schema.json").read_text(encoding="utf-8"))
    output_schema = json.loads((SCHEMAS / "demo_output.schema.json").read_text(encoding="utf-8"))
    failure_schema = _forgiving_schema(json.loads((SCHEMAS / "failure_output.schema.json").read_text(encoding="utf-8")))

    for spec_id in [spec["spec_id"] for spec in list_specs()]:
        jsonschema.validate(run_spec(spec_id), output_schema)
    for spec in json.loads((ROOT / "oc_core_demo" / "data" / "demo_specs.json").read_text(encoding="utf-8"))["specs"]:
        jsonschema.validate(spec, spec_schema)
    jsonschema.validate(run_spec_safe("bogus"), failure_schema)


def test_generated_v002_atlas_is_complete_and_public() -> None:
    atlas_path = ROOT / "web" / "public" / "data" / "oc_atlas.json"
    assert atlas_path.exists()
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS / "oc_atlas.schema.json").read_text(encoding="utf-8"))
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(atlas, _forgiving_schema(schema))
    assert len(atlas["concepts"]) >= 8
    assert len(atlas["simulations"]) >= 4
    assert len(atlas["graph"]["nodes"]) == 257
    assert len(atlas["proof_routes"]) == 254
    private_workspace_marker = "estra-" + "private-" + "work"
    assert private_workspace_marker not in json.dumps(atlas)


def test_generated_v010_universe_is_full_corpus_3d_closed_and_public() -> None:
    atlas_path = ROOT / "web" / "public" / "data" / "oc_universe_atlas.json"
    assert atlas_path.exists()
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS / "oc_universe_atlas.schema.json").read_text(encoding="utf-8"))
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(atlas, _forgiving_schema(schema))
    assert atlas["schema_version"] == "oc-core-demo-universe.v010"
    assert atlas["demo_version"] == "V010"
    assert atlas["release_ordinal"] == "010"
    assert atlas["edition"] == "public"
    assert len(atlas["k_levels"]) >= 13
    assert len(atlas["domain_benchmarks"]) >= 4
    assert len(atlas["simulation_worlds"]) >= 4
    assert len(atlas["k_level_worlds"]) == 13
    assert len(atlas["system_zoo"]) >= 5
    assert len(atlas["wiki"]["chapters"]) > 20
    assert atlas["wiki"]["corpus_summary"]["atom_count"] >= 1000
    assert len(atlas["wiki"]["corpus_atoms"]) >= 1000
    assert len(atlas["wiki"]["formulas"]) >= 15
    assert len(atlas["formula_atlas"]) >= 15
    assert len(atlas["corpus_index"]) >= 1000
    assert atlas["research_gap_summary"]["open_count"] == 0
    assert atlas["research_gaps"] == []
    assert len(atlas["closure_ledger"]) >= 80
    assert atlas["proof_placeholder_closure_ledger"]["open_placeholder_rows"] == 0
    assert atlas["graph"]["root_principle"].lower().startswith("unresolvable contradiction")
    assert set(atlas["graph"]["summary"]["required_edge_types_present"]) >= {
        "derives",
        "refines",
        "branches_to_k_level",
        "formalized_by",
        "uses_formula",
        "supported_by",
        "proved_or_bounded_by",
        "projects_to_domain",
        "simulated_by",
        "cites_corpus_atom",
        "collapse_path",
    }
    assert set(atlas["graph"]["summary"]["required_layers_present"]) >= {
        "root_principle",
        "continuum_operator",
        "metaontology",
        "k_level",
        "theorem",
        "formula",
        "proof_route",
        "evidence",
        "domain_projection",
        "simulation",
        "corpus_atom",
        "boundary",
    }
    assert all("semantic_label" in node and node["label"] != node["id"] for node in atlas["graph"]["nodes"] if node["id"].startswith("OC14-N"))
    assert all("nodes" in system and "edges" in system and "weakest_node" in system for system in atlas["system_zoo"])
    assert "science_graph_v010" in atlas
    assert len(atlas["k_level_example_atlas"]) >= 39
    assert len({row["k_level"] for row in atlas["k_level_example_atlas"]}) == 13
    assert atlas["formula_quality_report"]["formula_count"] >= 15
    assert all(
        {"ordinal", "formula_title", "domain", "operator_glossary", "formula", "consequences", "chart_spec"} <= set(row)
        and (row.get("source_refs") or row.get("nonclaim_boundary"))
        for row in atlas["formula_atlas"]
    )
    assert atlas["formula_formalization_obligations"]["schema_version"] == "oc-core-demo-formula-formalization-obligations.v010"
    formula_text = "\n".join(f"{row.get('formula_title', '')} {row.get('formula_text', '')}" for row in atlas["formula_atlas"])
    assert "set_option" not in formula_text
    assert not re.search(r"CLAIM=|CLOUDFLARE|BASELINE|dataclass|FileResult|DOI|Compute|source locator", formula_text, re.I)
    assert len(atlas["formula_atlas"]) < 100
    assert atlas["corpus_completeness_report"]["counts"]["generated_atoms"] == len(atlas["wiki"]["corpus_atoms"])
    assert atlas["demonstrator_surface_graph"]["schema_version"] == "oc-core-demo-surface-graph.v010"
    assert atlas["demonstrator_surface_graph"]["summary"]["surface_count"] >= 19
    assert atlas["demonstrator_surface_graph"]["summary"]["control_count"] >= 30
    assert atlas["persona_user_story_map"]["workflow_spine"] == ["diagnose", "kill", "improve", "compare", "export"]
    assert all(
        node.get("purpose") and node.get("target_view") and node.get("expected_visible_result") and node.get("test_id")
        for node in atlas["demonstrator_surface_graph"]["nodes"]
        if node.get("kind") == "control"
    )
    assert len(atlas["reviewer_objection_routes"]) >= 3
    assert len(atlas["model_comparison_matrix"]) >= 1
    assert len(atlas["system_architect_missions"]) >= 1
    assert len(atlas["trust_ladder"]) >= 4
    assert len(atlas["practical_value_cards"]) >= 3
    assert all(
        {"oc_adds", "does_not_replace", "when_not_to_use"} <= set(row)
        for row in atlas["model_comparison_matrix"]
    )
    assert all(route.get("links_to_real_surfaces") for route in atlas["reviewer_objection_routes"])
    text = json.dumps(atlas)
    assert "Frozen proof/refute target ." not in text
    assert ("C:" + "\\Users\\") not in text
    assert ("logion_" + "local") not in text
    assert ("." + "runtime") not in text


def test_v010_science_graph_reachability_and_chain_invariants() -> None:
    atlas = json.loads((ROOT / "web" / "public" / "data" / "oc_universe_atlas.json").read_text(encoding="utf-8"))
    graph = atlas["graph"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    relation_by_source: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for edge in graph["edges"]:
        adjacency.setdefault(edge["source"], []).append(edge["target"])
        relation_by_source.setdefault(edge["source"], set()).add(edge["relation"])
    seen = {graph["root_node_id"]}
    queue = [graph["root_node_id"]]
    while queue:
        current = queue.pop(0)
        for nxt in adjacency.get(current, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    public_targets = [node_id for node_id in nodes if node_id.startswith("OC14-N")]
    assert public_targets
    assert set(public_targets) <= seen
    assert {f"K::K{index}" for index in range(13)} <= seen
    theorem_nodes = [node_id for node_id, node in nodes.items() if node.get("layer") == "theorem"]
    assert theorem_nodes
    for node_id in theorem_nodes:
        assert "uses_formula" in relation_by_source[node_id]
        assert "proved_or_bounded_by" in relation_by_source[node_id]


def test_static_web_exhibit_is_buildable() -> None:
    index = ROOT / "web" / "dist" / "index.html"
    app_files = list((ROOT / "web" / "dist" / "assets").glob("*.js"))
    atlas = ROOT / "web" / "dist" / "data" / "oc_universe_atlas.json"
    assert index.exists()
    assert app_files
    assert atlas.exists()
    assert 'id="root"' in index.read_text(encoding="utf-8")


def test_v010_cerberus_live_gate_outputs_are_present() -> None:
    with tempfile.TemporaryDirectory() as td:
        work_dir = Path(td) / "data"
        work_dir.mkdir()
        shutil.copy2(
            ROOT / "web" / "public" / "data" / "oc_universe_atlas.json",
            work_dir / "oc_universe_atlas.json",
        )
        visual_manifest = {
            "schema_version": "oc-core-demo-visual-quality.v010",
            "demo_version": "V010",
            "release_ordinal": "010",
            "status": "PASS",
            "rows": [
                {
                    "surface": surface,
                    "status": "PASS",
                    "screenshot_present": True,
                    "not_loading_state": True,
                    "dom_snapshot_present": True,
                    "click_trace_present": True,
                    "workspace_visible": True,
                }
                for surface in ("cockpit", "graph", "wiki", "formula", "workbench", "cascade", "proof", "hierarchy", "surface")
            ],
        }
        (work_dir / "visual_quality_manifest.json").write_text(json.dumps(visual_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (work_dir / "v010_visual_quality_manifest.json").write_text(json.dumps(visual_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        process = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_demonstrator_cerberus_v010.py"),
                "--data-dir",
                str(work_dir),
                "--findings-min",
                "240",
                "--findings-max",
                "360",
                "--timeout",
                "30",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert process.returncode in {0, 2}, process.stderr

        review_path = work_dir / "cerberus_v010_review.json"
        repair_path = work_dir / "cerberus_v010_repair_ledger.json"
        iteration_path = work_dir / "v010_iteration_ledger.json"
        assert review_path.exists()
        assert repair_path.exists()
        assert iteration_path.exists()
        review = json.loads(review_path.read_text(encoding="utf-8"))
        repair = json.loads(repair_path.read_text(encoding="utf-8"))
        iteration = json.loads(iteration_path.read_text(encoding="utf-8"))

        assert review["schema_version"] == "oc-core-demo-cerberus-review.v010"
        assert review["demo_version"] == "V010"
        assert review["release_ordinal"] == "010"
        assert review["provider_id"] == "CODEX_CLI_CHATGPT"
        assert review["status"] in {"PASS", "FAIL_CLOSED"}
        if review["status"] == "PASS":
            assert review["summary"]["unresolved_total"] == 0
            assert review["summary"]["unresolved_medium_or_worse_total"] == 0
            assert review["summary"]["unresolved_medium_plus_total"] == 0
        assert 240 <= review["summary"]["baseline_finding_total"] <= 360
        assert review["summary"]["baseline_finding_total"] == len(repair["rows"])
        assert review["summary"]["missing_review_heads"] == []
        assert len(iteration["rows"]) == 20

        required_heads = {
            "first_impression",
            "user_story_clarity",
            "architect_workflow",
            "formula_quality",
            "wiki_completeness",
            "graph_structure_clickability",
            "km_hierarchy",
            "cascade_credibility",
            "visual_design",
            "copy_clarity",
            "what_is_this",
            "why_should_i_care",
            "practical_value",
            "system_architect_workflow",
            "scientific_trust",
            "proof_sufficiency",
            "model_comparison",
            "domain_relevance",
            "ux_attention_retention",
            "visual_design_quality",
            "purchase_pull",
        }
        assert required_heads.issubset(set(review["summary"]["heads_seen"]))

        for row in review["findings"]:
            assert row["severity"] in {"critical", "high", "medium", "minor"}
            assert isinstance(row.get("reviewer_quote"), str) and row["reviewer_quote"].strip()
            assert isinstance(row.get("blocked_reaction"), str) and row["blocked_reaction"].strip()
            assert isinstance(row.get("functional_fix_required"), str) and row["functional_fix_required"].strip()
            assert isinstance(row.get("target_surface"), str) and row["target_surface"].strip()
            assert row["repair_mapping"] in {"FIXED", "BOUNDED", "DEFERRED_WITH_REASON"}

        screenshot_manifest = review["screenshot_manifest"]
        assert isinstance(screenshot_manifest, dict)
        assert screenshot_manifest["status"] in {"PASS", "MISSING"}
        if screenshot_manifest["status"] == "PASS":
            assert isinstance(screenshot_manifest["entries"], list)

        cli_smoke = review["cli_api_smoke"]
        assert isinstance(cli_smoke, dict)
        assert isinstance(cli_smoke.get("command_outputs"), list)
        assert review["visual_quality_manifest"]["status"] == "PASS"


def test_source_bundle_contains_only_public_source_material() -> None:
    bundle = DIST / "oc_core_demo_public_bundle.zip"
    if not bundle.exists():
        pytest.skip("source bundle has not been built yet")
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        text_rows = []
        for name in names:
            if Path(name).suffix.lower() not in {".py", ".md", ".json", ".toml", ".ts", ".tsx", ".css", ".html", ".ps1"}:
                continue
            text_rows.append((name, archive.read(name).decode("utf-8", errors="ignore")))
    assert names
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
    assert not any(name.startswith("dist/") for name in names)
    owner_path = "Users/" + ("Mega" + "port")
    private_workspace_marker = "estra-" + "private-" + "work"
    assert not any(private_workspace_marker in name or owner_path in name for name in names)
    forbidden = [
        "C:" + "\\Users\\",
        owner_path,
        "." + "runtime",
        "logion_" + "local",
        "raw_" + "private",
        "source_" + "cache",
    ]
    assert not [
        {"file": name, "marker": marker}
        for name, text in text_rows
        for marker in forbidden
        if marker in text
    ]


def test_manifest_hash_matches_portable_zip_when_present() -> None:
    manifest_path = DIST / "OC_Core_1_4_Demonstrator_Portable_MANIFEST.json"
    if not manifest_path.exists():
        pytest.skip("portable artifact has not been built yet")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    portable_path = DIST / manifest["portable_zip"]
    if not portable_path.exists():
        pytest.skip("portable artifact has not been built yet")
    import hashlib

    digest = hashlib.sha256(portable_path.read_bytes()).hexdigest()
    assert manifest["portable_zip_sha256"] == digest
    assert manifest["external_action_performed"] is False



