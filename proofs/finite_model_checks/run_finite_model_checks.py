from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"
OUTPUT = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
ATLAS = ROOT / "data" / "k_level_irreducibility_matrix.json"
LEAN_CERT = ROOT / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json"

FORBIDDEN_MODEL_KEYS = {
    "observed_verdict",
    "observed_drop_verdict",
    "observed_keep_verdict",
    "observed_reduction_verdict",
    "failure_equivalence_checked",
    "hybrid_guard_reset_checked",
    "semantic_evaluator",
    "oracle_attestation",
    "witness_retained",
    "added_axis_observable",
    "demotion_allowed",
    "upper_axis_value",
    "reduced_axis_value",
    "keep_present",
    "drop_present",
    "changed_fields",
}

COMPONENT_FIELDS = {
    "carrier": "carrier_witness",
    "realization": "realization_interprets",
    "lawful_possibility": "lawful_transition_only",
    "liveness": "live_support_witness",
    "residue": "residue_separated",
    "morphisms": "morphism_invariant_checked",
    "boundaries": "boundary_rejects_bad_state",
    "operators": "typed_operator_update",
    "cycles": "cycle_or_maintenance",
    "dimension": "dimension_axes_separated",
    "k": "k_zero_cause_declared",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rel_json(ref: str) -> dict[str, Any]:
    path = (ROOT / ref).resolve()
    if ROOT.resolve() not in path.parents and path != ROOT.resolve():
        raise ValueError(f"ref escapes repo root: {ref}")
    return read_json(path)


def has_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_MODEL_KEYS or has_forbidden_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(has_forbidden_key(child) for child in value)
    return False


def atlas_rows() -> dict[str, dict[str, Any]]:
    payload = json.loads(ATLAS.read_text(encoding="utf-8"))
    rows = {}
    for row in payload.get("rows", []):
        rows[row["transition_id"]] = {
            "from_k": row["from_k"],
            "to_k": row["to_k"],
            "added_axis": row["added_axis"],
            "witness_pair": row["adjacent_transition_witness"],
            "reduction_failure_criterion": row["reduction_failure_criterion"],
            "lawful_demotion_criterion": row["lawful_demotion_criterion"],
        }
    return rows


def cycle_or_maintenance(model: dict[str, Any]) -> bool:
    cycle = model.get("cycle_mode")
    maintenance = model.get("maintenance", {})
    return cycle not in {None, "", "none"} or (
        maintenance.get("obligation_checked") is True and maintenance.get("support_available") is True
    )


def zero_cause_active(causes: dict[str, Any]) -> bool:
    return any(bool(causes.get(name)) for name in ("flow", "coherence", "identity", "embedding"))


def semantic_tuple_verdict(model: dict[str, Any]) -> str:
    return "PASS" if all(bool(model.get(field)) for field in COMPONENT_FIELDS.values()) else "FAIL"


def semantic_delta_fields(keep: dict[str, Any], drop: dict[str, Any]) -> list[str]:
    return sorted(field for field in COMPONENT_FIELDS.values() if bool(keep.get(field)) != bool(drop.get(field)))


def component_case_valid(case: dict[str, Any]) -> bool:
    target = str(case.get("target_component"))
    target_field = COMPONENT_FIELDS.get(target)
    if not target_field:
        return False
    keep = case.get("keep", {})
    drop = case.get("drop", {})
    return (
        semantic_tuple_verdict(keep) == "PASS"
        and semantic_tuple_verdict(drop) == "FAIL"
        and semantic_delta_fields(keep, drop) == [target_field]
        and target in str(case.get("drop_reason", ""))
    )


def klevel_schema_valid(model: dict[str, Any]) -> bool:
    expected = atlas_rows().get(str(model.get("transition_id")))
    if not expected:
        return False
    return all(model.get(key) == value for key, value in expected.items())


def klevel_reduction_verdict(model: dict[str, Any]) -> str:
    if not klevel_schema_valid(model):
        return "REDUCTION_UNCHECKED"
    upper = model.get("upper_model", {})
    reduced = model.get("reduced_model", {})
    upper_active = (
        upper.get("axis_observed") is True
        and upper.get("retained_witness") == model.get("witness_pair")
        and upper.get("verdict_changes") is True
    )
    reduced_active = (
        reduced.get("axis_observed") is True
        or reduced.get("retained_witness") == model.get("witness_pair")
        or reduced.get("verdict_changes") is True
    )
    if upper_active and not reduced_active:
        return "FAILS_WITH_WITNESS"
    if (
        not upper_active
        and not reduced_active
        and model.get("demotion_observation") == "witness unobservable under declared equivalence"
    ):
        return "DEMOTABLE_WITH_LOST_WITNESS"
    return "REDUCTION_UNCHECKED"


def observed(row: dict[str, Any]) -> str:
    if has_forbidden_key(row.get("model", {})):
        return "REJECT_FLAG_ORACLE_INPUT"
    model = row.get("model", {})
    theorem_id = row.get("theorem_id")
    case_type = row.get("case_type")
    if case_type == "theorem_case":
        if theorem_id == "T133-K0-RES":
            same_cell = model.get("rho_cell_a") == model.get("rho_cell_b")
            raw_separated = model.get("raw_separated") is True and float(model.get("raw_distance", 0.0)) > 0.0
            same_cell_not_distinguished = model.get("resolution_distinguished") is False
            cross_cell_distinguished = (
                model.get("cross_rho_cell_a") != model.get("cross_rho_cell_b")
                and model.get("cross_resolution_distinguished") is True
            )
            ok = same_cell and raw_separated and same_cell_not_distinguished and cross_cell_distinguished
        elif theorem_id == "T133-OMEGA-STATUS":
            ok = (
                model.get("death") is True
                and model.get("live") is False
                and model.get("residue_id") not in {None, "", model.get("identity_token")}
                and model.get("rebirth_source_residue_id") == model.get("residue_id")
                and model.get("rebirth_target_id") not in {None, ""}
                and model.get("morphism_class") == "rebirth"
                and model.get("morphism_source_id") == model.get("residue_id")
                and model.get("morphism_target_id") == model.get("rebirth_target_id")
                and model.get("identity_invariant_preserved") is False
                and model.get("claimed_identity_continuation") is False
            )
        elif theorem_id == "T133-K-ZERO":
            ok = (
                model.get("admissible_nonempty") is True
                and model.get("cycle_witness") is True
                and model.get("claimed_k") == 0
                and zero_cause_active(model.get("zero_causes", {}))
            )
        elif theorem_id == "T133-BOUNDARY":
            if model.get("metric_measure_declared") is True:
                metric_failure = float(model.get("state_value")) > float(model.get("threshold"))
            else:
                metric_failure = None
            ok = model.get("boundary_kind") == "classifier" and (
                metric_failure is None or metric_failure == bool(model.get("classifier_failure"))
            )
        elif theorem_id == "T133-HYBRID":
            update_kind = model.get("update_kind", "hybrid_guard_reset")
            chart_declared = model.get("smooth_chart_id") not in {None, ""}
            derivative_ok = not bool(model.get("derivative_requested")) or chart_declared
            if update_kind == "hybrid_guard_reset":
                guard = bool(model.get("guard"))
                expected_next = model.get("reset_target") if guard else model.get("step_target")
                smooth_step_ok = model.get("smooth_step_target") in {None, model.get("flow_one_target")}
                shared_state_ok = model.get("smooth_state_type") == model.get("hybrid_state_type")
                reset_typed_ok = (
                    model.get("reset_source_mode") == model.get("current_mode")
                    and model.get("reset_target_mode") == model.get("target_mode")
                    and model.get("reset_codomain") == model.get("hybrid_state_type")
                    and model.get("post_reset_admissible") is True
                    and model.get("mode_invariant_preserved") is True
                )
                ok = model.get("actual_next") == expected_next and derivative_ok and smooth_step_ok and shared_state_ok and reset_typed_ok
            elif update_kind == "proof_rewrite":
                ok = (
                    model.get("carrier_kind") in {"proof", "rewrite"}
                    and model.get("typed_update_relation") is True
                    and model.get("source_type") == model.get("target_type")
                    and model.get("derivative_requested") is False
                    and not chart_declared
                    and model.get("actual_next") == model.get("step_target")
                )
            else:
                ok = False
        elif theorem_id == "T133-DIM":
            hist = model.get("historical", [])
            eff = model.get("effective", [])
            ok = (
                len(hist) >= 3
                and len(eff) >= 3
                and all(hist[idx] <= hist[idx + 1] for idx in range(len(hist) - 1))
                and any(eff[idx + 1] < eff[idx] for idx in range(len(eff) - 1))
            )
        elif theorem_id == "T133-CYCLE":
            ok = bool(model.get("live")) and cycle_or_maintenance(model)
        elif theorem_id == "T133-ID":
            should_be_identity = (
                model.get("morphism_class") == "identity"
                and model.get("identity_invariant_preserved") is True
            )
            ok = model.get("claimed_identity_continuation") is should_be_identity
        elif theorem_id == "T133-MIN":
            cases = model.get("component_cases", [])
            ok = (
                len(cases) == len(COMPONENT_FIELDS)
                and {case.get("target_component") for case in cases} == set(COMPONENT_FIELDS)
                and all(component_case_valid(case) for case in cases)
            )
        elif theorem_id == "T133-KLEVEL":
            transitions = model.get("transitions", [])
            expected_ids = set(atlas_rows())
            ok = (
                len(transitions) == len(expected_ids)
                and {transition.get("transition_id") for transition in transitions} == expected_ids
                and all(
                    klevel_reduction_verdict(transition) == "FAILS_WITH_WITNESS"
                    and klevel_reduction_verdict(transition.get("demotion_case", {})) == "DEMOTABLE_WITH_LOST_WITNESS"
                    for transition in transitions
                )
            )
        else:
            ok = False
        return "ACCEPT" if ok else "REJECT"
    if case_type == "component_keep_drop_witness":
        return semantic_tuple_verdict(model.get("drop", {}))
    if case_type == "adjacent_k_transition_witness":
        return klevel_reduction_verdict(model)
    if case_type == "mutation_control":
        return observed(dict(model.get("mutated_row", {})))
    if case_type == "no_send_state_machine":
        manifest = read_rel_json(str(model.get("manifest_ref")))
        approval = read_rel_json(str(model.get("approval_ref")))
        publish_requested = model.get("publish_requested") is True
        locked_fields = [
            "publish_allowed",
            "journal_submissions_allowed",
            "journal_submission_allowed",
            "github_release_allowed",
            "zenodo_deposit_allowed",
            "software_heritage_deposit_allowed",
            "doi_minting_allowed",
        ]
        all_locked = all(manifest.get(field) is False for field in locked_fields)
        approval_locked = (
            approval.get("decision") == "PENDING"
            and approval.get("owner_approved") is False
            and approval.get("publish_allowed") is False
            and approval.get("journal_submissions_allowed") is False
        )
        if publish_requested and manifest.get("global_no_send_lock") is True and approval_locked and all_locked:
            return "REJECT_PUBLIC_ACTION"
        return "NO_ACTION"
    if case_type == "no_send_hypothetical_control":
        owner_approved = model.get("owner_approved") is True
        publish_requested = model.get("publish_requested") is True
        channel_fields = {
            "github_release": "github_release_allowed",
            "zenodo_deposit": "zenodo_deposit_allowed",
            "software_heritage_deposit": "software_heritage_deposit_allowed",
            "journal_submission": "journal_submission_allowed",
            "doi_minting": "doi_minting_allowed",
        }
        requested = model.get("requested_channels", [])
        requested_channels_ok = bool(requested) and all(channel in channel_fields and model.get(channel_fields[channel]) is True for channel in requested)
        global_lock_open = model.get("global_no_send_lock") is False
        common_gates_open = (
            model.get("publish_allowed") is True
            and model.get("journal_submissions_allowed") is True
        )
        if publish_requested and owner_approved and global_lock_open and common_gates_open and requested_channels_ok:
            return "ALLOW_AFTER_OWNER_APPROVAL"
        return "NO_ACTION"
    return "UNKNOWN"


def evaluate(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if any(key.startswith("observed_") for key in row):
        out["input_schema_violation"] = "input rows must not contain observed_* verdict fields"
        out["passed"] = False
        return out
    obs = observed(row)
    if row.get("case_type") == "component_keep_drop_witness":
        out["observed_keep_verdict"] = semantic_tuple_verdict(row.get("model", {}).get("keep", {}))
        out["observed_drop_verdict"] = obs
        out["passed"] = out["observed_keep_verdict"] == row.get("expected_keep_verdict") and obs == row.get("expected_drop_verdict")
    elif row.get("case_type") == "adjacent_k_transition_witness":
        out["observed_reduction_verdict"] = obs
        out["passed"] = obs == row.get("expected_reduction_verdict")
    else:
        out["observed_verdict"] = obs
        out["passed"] = obs == row.get("expected_verdict")
    return out


def main() -> int:
    inputs = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = [evaluate(row) for row in inputs["rows"]]
    failures = [row for row in rows if not row.get("passed")]
    lean_cert = read_json(LEAN_CERT) if LEAN_CERT.exists() else {}
    lean_cert_ok = (
        lean_cert.get("returncode") == 0
        and lean_cert.get("theorem_ref_missing_total") == 0
        and lean_cert.get("theorem_ref_present_total", 0) >= 10
    )
    payload = {
        "schema_id": "OC133_FINITE_MODEL_CHECKS_v12_ATLAS_SEMANTIC_EXECUTED",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "runner": "proofs/finite_model_checks/run_finite_model_checks.py",
        "runner_sha256": sha256_file(Path(__file__)),
        "input_ref": "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "input_sha256": sha256_file(INPUT),
        "atlas_ref": "data/k_level_irreducibility_matrix.json",
        "atlas_sha256": sha256_file(ATLAS),
        "lean_build_certificate_ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "lean_build_certificate_sha256": sha256_file(LEAN_CERT) if LEAN_CERT.exists() else None,
        "lean_build_returncode": lean_cert.get("returncode"),
        "lean_theorem_ref_present_total": lean_cert.get("theorem_ref_present_total", 0),
        "lean_theorem_ref_missing_total": lean_cert.get("theorem_ref_missing_total", 999),
        "command": "python proofs/finite_model_checks/run_finite_model_checks.py",
        "semantic_evaluator": True,
        "input_observed_field_total": sum(1 for row in inputs["rows"] for key in row if key.startswith("observed_")),
        "flag_oracle_key_total": sum(1 for row in inputs["rows"] if row.get("case_type") != "mutation_control" and has_forbidden_key(row.get("model", {}))),
        "flag_oracle_mutation_total": sum(1 for row in inputs["rows"] if row.get("case_type") == "mutation_control" and has_forbidden_key(row.get("model", {}))),
        "case_total": len(rows),
        "positive_case_total": sum(1 for row in rows if row.get("case_type") == "theorem_case" and row.get("expected_verdict") == "ACCEPT"),
        "negative_case_total": sum(1 for row in rows if row.get("case_type") == "theorem_case" and row.get("expected_verdict") == "REJECT"),
        "component_witness_total": sum(1 for row in rows if row.get("case_type") == "component_keep_drop_witness"),
        "k_transition_witness_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness" and row.get("expected_reduction_verdict") == "FAILS_WITH_WITNESS"),
        "k_transition_negative_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness" and row.get("expected_reduction_verdict") == "DEMOTABLE_WITH_LOST_WITNESS"),
        "mutation_control_total": sum(1 for row in rows if row.get("case_type") == "mutation_control"),
        "no_send_state_machine_total": sum(1 for row in rows if row.get("case_type") in {"no_send_state_machine", "no_send_hypothetical_control"}),
        "failure_total": len(failures),
        "machine_checked_subset_total": lean_cert.get("theorem_ref_present_total", 0) if lean_cert_ok else 0,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
