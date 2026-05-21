from __future__ import annotations

import json
import math

from oc_core_demo.core import (
    explain_spec_safe,
    list_specs,
    load_public_graph,
    run_spec,
    run_spec_safe,
)


def test_all_specs_run_with_defaults_and_strict_json() -> None:
    specs = list_specs()
    assert len(specs) == 10
    for spec in specs:
        payload = run_spec(spec["spec_id"])
        assert payload["schema_version"] == "oc-core-demo.v001"
        assert payload["status"] == "PASS"
        assert len(payload["result_hash"]) == 64
        json.dumps(payload, allow_nan=False)


def test_params_are_strict_and_hashes_are_stable() -> None:
    first = run_spec("transformation_risk_calculator", {"change_pressure": 0.7})
    second = run_spec("transformation_risk_calculator", {"change_pressure": 0.7})
    assert first["result_hash"] == second["result_hash"]

    extra = run_spec_safe("transformation_risk_calculator", {"change_pressure": 0.7, "unused": 1})
    assert extra["status"] == "FAIL_CLOSED"
    assert "unknown parameter" in extra["message"]


def test_non_finite_and_bool_values_fail_closed() -> None:
    non_finite = run_spec_safe("transformation_risk_calculator", {"change_pressure": math.nan})
    assert non_finite["status"] == "FAIL_CLOSED"
    assert "finite" in non_finite["message"]

    bool_integer = run_spec_safe("transition_pressure_lab", {"steps": True})
    assert bool_integer["status"] == "FAIL_CLOSED"
    assert "integer" in bool_integer["message"]


def test_graph_neighborhood_avoids_route_hub_explosion() -> None:
    payload = run_spec("graph_neighborhood", {"node": "OC14-N001", "radius": 2})
    result = payload["result"]
    assert result["summary"]["matched_node_total"] >= 3
    assert "OC::PROOF_GATEWAY" in result["summary"]["route_nodes_not_expanded"]
    assert result["summary"]["returned_node_total"] <= 80
    assert len(result["nodes"]) == result["summary"]["returned_node_total"]
    assert "proved_or_bounded_by" in result["relation_counts"] or "uses_formula" in result["relation_counts"]


def test_proof_replay_is_target_specific_and_bounded() -> None:
    payload = run_spec("proof_trace_replay", {"target": "OC14-N001"})
    result = payload["result"]
    assert result["public_target"]["public_target_id"] == "OC14-N001"
    assert result["public_target"]["evidence_class"] == "terminal-public-evidence"
    assert "not a proof engine" in result["nonclaim"]
    assert len(result["trace"]) >= 5


def test_proof_placeholder_targets_are_closed_as_boundaries() -> None:
    payload = run_spec("proof_trace_replay", {"target": "OC14-N152"})
    result = payload["result"]
    assert "Frozen proof/refute target ." not in result["statement_excerpt"]
    assert result["public_target"]["closure_status"] in {"CLOSED_SOURCE_REPAIRED", "CLOSED_AS_OBLIGATION_BOUNDARY"}
    assert "does not prove or refute" in result["nonclaim"]


def test_invalid_explain_is_structured_failure() -> None:
    payload = explain_spec_safe("bogus")
    assert payload["status"] == "FAIL_CLOSED"
    assert payload["spec_id"] == "bogus"
    assert "unknown spec_id" in payload["message"]


def test_graph_data_endpoints_are_valid() -> None:
    graph = load_public_graph()
    node_ids = {node["id"] for node in graph["nodes"]}
    assert graph["summary"]["target_total"] == 254
    for edge in graph["edges"]:
        source = edge.get("from", edge.get("source"))
        target = edge.get("to", edge.get("target"))
        assert source in node_ids
        assert target in node_ids
