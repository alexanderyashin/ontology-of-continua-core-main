from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
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


def normalize_build_transcript(value: str) -> str:
    value = re.sub(r"\(\d+(?:\.\d+)?s\)", "(<elapsed>)", value or "")
    value = re.sub(r".*toolchain.*(?:already up-to-date|not updated|updated).*", "<toolchain provisioning outside canonical transcript>", value, flags=re.IGNORECASE)
    return value.replace(str(ROOT), "<REPO_ROOT>")


def canonical_lean_observation(value: str) -> dict[str, str | None]:
    version = re.search(r"Lean \(version\s+([^,\s]+)", value or "")
    commit = re.search(r"commit\s+([0-9a-fA-F]+)", value or "")
    return {
        "version": version.group(1) if version else None,
        "commit": commit.group(1).lower() if commit else None,
    }


def canonical_lake_observation(value: str) -> dict[str, str | None]:
    lake = re.search(r"Lake version\s+([^\s]+)", value or "")
    lean = re.search(r"Lean version\s+([^)]+)\)", value or "")
    return {
        "lake_version": lake.group(1) if lake else None,
        "lean_version": lean.group(1).strip() if lean else None,
    }


def release_critical_source_refs() -> list[str]:
    return [
        "lakefile.lean",
        "lean-toolchain",
        "formal/lean/OC133V12.lean",
        "tools/materialize_oc_core_1_3_3_v12_closure.py",
        "tools/templates/OC133V12_hardened.lean",
        "tools/templates/run_finite_model_checks_hardened.py",
        "proofs/finite_model_checks/run_finite_model_checks.py",
        "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "data/OC133_GLOBAL_MINIMALITY_WITNESSES.json",
        "data/k_level_irreducibility_matrix.json",
        "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_3.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
        "validation/run_all.py",
        "validation/numeric_predictions/run_numeric_prediction_replay.py",
        "tools/verify_oc133_reproducible_temp_tree.py",
        "simulations/adversarial/run_all.py",
        "simulations/run_all.py",
        "simulations/expected_simulations.yml",
        "release_machine/oc133.py",
        "release_machine/oc133_v12.py",
        "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
        "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json",
    ]


def source_manifest() -> list[dict[str, str]]:
    rows = []
    refs = set(release_critical_source_refs())
    for pattern in [
        "validation/*/replay.py",
        "validation/*/VALIDATION_PACKET.json",
        "validation/_raw/*",
        "simulations/*/run_simulation.py",
        "simulations/*/simulation_contract.json",
    ]:
        refs.update(path.relative_to(ROOT).as_posix() for path in ROOT.glob(pattern) if path.is_file())
    for ref in sorted(refs):
        path = ROOT / ref
        if path.exists() and path.is_file():
            rows.append({"ref": ref, "sha256": sha256_file(path)})
    return rows


def generated_artifact_manifest() -> list[dict[str, str]]:
    rows = []
    generated_refs = [
        (
            "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
            "python tools/materialize_oc_core_1_3_3_v12_closure.py",
            "deterministic_numeric_replay_qa_input",
        ),
    ]
    for ref, producer, role in generated_refs:
        path = ROOT / ref
        if path.exists() and path.is_file():
            rows.append(
                {
                    "ref": ref,
                    "sha256": sha256_file(path),
                    "producer_command": producer,
                    "artifact_role": role,
                }
            )
    return rows


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rel_json(ref: str) -> dict[str, Any]:
    path = (ROOT / ref).resolve()
    if ROOT.resolve() not in path.parents and path != ROOT.resolve():
        raise ValueError(f"ref escapes repo root: {ref}")
    return read_json(path)


def run_live_lake_build() -> dict[str, Any]:
    try:
        with tempfile.TemporaryDirectory(prefix="oc133_finite_lean_clean_") as tmp:
            clean_root = Path(tmp)
            for row in source_manifest():
                src = ROOT / row["ref"]
                dst = clean_root / row["ref"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            preexisting_lake = (clean_root / ".lake").exists()
            toolchain = (ROOT / "lean-toolchain").read_text(encoding="utf-8").strip()
            lean_version = subprocess.run(
                ["elan", "run", toolchain, "lean", "--version"],
                cwd=clean_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
            lake_version = subprocess.run(
                ["elan", "run", toolchain, "lake", "--version"],
                cwd=clean_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
            completed = subprocess.run(
                ["elan", "run", toolchain, "lake", "build", "OC133V12"],
                cwd=clean_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=600,
            )
            post_build_lake = (clean_root / ".lake").exists()
    except Exception as exc:
        return {
            "execution_status": "EXECUTION_FAILED",
            "returncode": -1,
            "clean_returncode": -1,
            "stdout_tail": "",
            "stderr_tail": str(exc)[-2000:],
            "preexisting_lake_cache_detected": True,
            "post_build_lake_cache_created": False,
        }
    zero_job_cached = "0 jobs" in (completed.stdout or "")
    returncode = 0 if completed.returncode == 0 and lean_version.returncode == 0 and lake_version.returncode == 0 and not zero_job_cached and not preexisting_lake and post_build_lake else 2
    return {
        "execution_status": "EXECUTED_ISOLATED_CLEAN_BUILD" if returncode == 0 else "CLEAN_BUILD_FAILED_OR_CACHED",
        "returncode": returncode,
        "clean_returncode": 0,
        "build_returncode": completed.returncode,
        "zero_job_cached_build_detected": zero_job_cached,
        "clean_stdout_tail": "isolated temporary checkout created without .lake",
        "clean_stderr_tail": "",
        "stdout_tail": normalize_build_transcript(completed.stdout[-2000:]),
        "stderr_tail": normalize_build_transcript(completed.stderr[-2000:]),
        "preexisting_lake_cache_detected": preexisting_lake,
        "post_build_lake_cache_created": post_build_lake,
        "build_transcript_sha256": hashlib.sha256(normalize_build_transcript((completed.stdout or "") + "\n" + (completed.stderr or "")).encode("utf-8")).hexdigest(),
        "lean_version_observed": (lean_version.stdout + lean_version.stderr).strip(),
        "lake_version_observed": (lake_version.stdout + lake_version.stderr).strip(),
        "lean_version_canonical": canonical_lean_observation((lean_version.stdout + lean_version.stderr).strip()),
        "lake_version_canonical": canonical_lake_observation((lake_version.stdout + lake_version.stderr).strip()),
    }


def declared_symbols(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"^\s*(?:theorem|def|structure|inductive)\s+([A-Za-z0-9_'.]+)", text, flags=re.MULTILINE))


def theorem_reference_audit(inputs: dict[str, Any], lean_cert: dict[str, Any]) -> dict[str, Any]:
    lean_symbols = declared_symbols(ROOT / "formal" / "lean" / "OC133V12.lean")
    runner_symbols = declared_symbols(Path(__file__))
    refs = set()
    for row in inputs.get("rows", []):
        for key in ("lean_ref", "counterexample_lean_ref"):
            value = row.get(key)
            if value:
                refs.add(str(value))
    for item in lean_cert.get("theorem_refs", []) or []:
        if isinstance(item, dict) and item.get("name"):
            refs.add(f"formal/lean/OC133V12.lean::{item['name']}")
    missing = []
    bound = []
    for ref in sorted(refs):
        if "::" not in ref:
            if (ROOT / ref).exists():
                bound.append(ref)
            else:
                missing.append({"ref": ref, "reason": "ARTIFACT_REF_NOT_FOUND"})
            continue
        path_ref, symbol = ref.split("::", 1)
        if path_ref == "formal/lean/OC133V12.lean":
            ok = symbol in lean_symbols
        elif path_ref == "proofs/finite_model_checks/run_finite_model_checks.py":
            ok = symbol in runner_symbols
        else:
            ok = (ROOT / path_ref).exists()
        if ok:
            bound.append(ref)
        else:
            missing.append({"ref": ref, "reason": "SYMBOL_NOT_FOUND_IN_CURRENT_SOURCE"})
    return {
        "theorem_ref_total": len(refs),
        "theorem_ref_bound_total": len(bound),
        "theorem_ref_missing_total": len(missing),
        "theorem_refs": sorted(bound),
        "theorem_ref_missing": missing,
    }


def atlas_external_binding_audit(inputs: dict[str, Any], atlas: dict[str, Any], lean_cert: dict[str, Any]) -> dict[str, Any]:
    finite_by_id = {row.get("case_id"): row for row in inputs.get("rows", [])}
    theorem_names = {
        row.get("name")
        for row in lean_cert.get("theorem_refs", [])
        if isinstance(row, dict) and row.get("present") is True
    }
    failures: list[dict[str, str]] = []
    if "release_atlas_manifest_has_total_finite_case_coverage" not in theorem_names:
        failures.append({"ref": "formal/lean/OC133V12.lean", "reason": "ATLAS_LEAN_THEOREM_NOT_CERTIFIED"})
    transition_ids = set()
    for row in atlas.get("rows", []):
        transition_id = str(row.get("transition_id", ""))
        transition_ids.add(transition_id)
        if row.get("lean_theorem_ref") != "formal/lean/OC133V12.lean::release_atlas_manifest_has_total_finite_case_coverage":
            failures.append({"ref": transition_id, "reason": "ATLAS_ROW_NOT_BOUND_TO_EXPECTED_LEAN_THEOREM"})
        if not str(row.get("lean_constructor", "")).startswith("AdjacentK."):
            failures.append({"ref": transition_id, "reason": "ATLAS_ROW_MISSING_ADJACENTK_CONSTRUCTOR"})
        retained_id = row.get("retained_finite_case_id")
        demotion_id = row.get("demotion_finite_case_id")
        retained = finite_by_id.get(retained_id)
        demotion = finite_by_id.get(demotion_id)
        if not retained:
            failures.append({"ref": str(retained_id), "reason": "RETAINED_FINITE_CASE_MISSING"})
        else:
            retained_model = retained.get("model", {})
            retained_transitions = retained_model.get("transitions", [])
            retained_transition_id = (
                retained_model.get("transition_id")
                or (retained_transitions[0].get("transition_id") if retained_transitions else None)
            )
            if retained.get("case_type") != "adjacent_k_transition_witness":
                failures.append({"ref": str(retained_id), "reason": "RETAINED_CASE_WRONG_TYPE"})
            if retained.get("expected_reduction_verdict") != "FAILS_WITH_WITNESS":
                failures.append({"ref": str(retained_id), "reason": "RETAINED_CASE_WRONG_EXPECTED_VERDICT"})
            if retained_transition_id != transition_id:
                failures.append({"ref": str(retained_id), "reason": "RETAINED_CASE_TRANSITION_ID_MISMATCH"})
        if not demotion:
            failures.append({"ref": str(demotion_id), "reason": "DEMOTION_FINITE_CASE_MISSING"})
        else:
            demotion_model = demotion.get("model", {})
            demotion_transitions = demotion_model.get("transitions", [])
            demotion_transition_id = (
                demotion_model.get("transition_id")
                or (demotion_transitions[0].get("transition_id") if demotion_transitions else None)
            )
            if demotion.get("case_type") != "adjacent_k_transition_witness":
                failures.append({"ref": str(demotion_id), "reason": "DEMOTION_CASE_WRONG_TYPE"})
            if demotion.get("expected_reduction_verdict") != "DEMOTABLE_WITH_LOST_WITNESS":
                failures.append({"ref": str(demotion_id), "reason": "DEMOTION_CASE_WRONG_EXPECTED_VERDICT"})
            if demotion_transition_id != transition_id:
                failures.append({"ref": str(demotion_id), "reason": "DEMOTION_CASE_TRANSITION_ID_MISMATCH"})
    finite_transition_ids = set()
    for row in inputs.get("rows", []):
        if row.get("case_type") != "adjacent_k_transition_witness":
            continue
        model = row.get("model", {})
        if model.get("transition_id"):
            finite_transition_ids.add(model.get("transition_id"))
            continue
        transitions = model.get("transitions", [])
        if transitions:
            finite_transition_ids.add(transitions[0].get("transition_id"))
    missing_from_atlas = sorted(tid for tid in finite_transition_ids if tid and tid not in transition_ids)
    for transition_id in missing_from_atlas:
        failures.append({"ref": str(transition_id), "reason": "FINITE_TRANSITION_NOT_DECLARED_IN_ATLAS"})
    return {
        "state": "PASS" if not failures else "FAIL",
        "atlas_transition_total": len(atlas.get("rows", [])),
        "finite_transition_total": len(finite_transition_ids),
        "failure_total": len(failures),
        "failures": failures[:50],
        "binding_policy": "External K-level JSON rows must name retained/demotion finite case IDs and the certified Lean atlas theorem.",
    }


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


def obstruction_active(obstructions: dict[str, Any]) -> bool:
    return any(
        bool(obstructions.get(name))
        for name in ("flow_blocked", "coherence_broken", "identity_split", "embedding_failure")
    )


def unique_nonempty_values(*values: Any) -> bool:
    if any(value in {None, ""} for value in values):
        return False
    return len(set(values)) == len(values)


def hypothetical_owner_approved_control(model: dict[str, Any]) -> str:
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
    requested_channels_ok = bool(requested) and all(
        channel in channel_fields and model.get(channel_fields[channel]) is True
        for channel in requested
    )
    global_lock_open = model.get("global_no_send_lock") is False
    common_gates_open = (
        model.get("publish_allowed") is True
        and model.get("journal_submissions_allowed") is True
    )
    if publish_requested and owner_approved and global_lock_open and common_gates_open and requested_channels_ok:
        return "ALLOW_AFTER_OWNER_APPROVAL"
    if publish_requested:
        return "REJECT_PUBLIC_ACTION"
    return "NO_ACTION"


def endpoint_bound_identity(model: dict[str, Any]) -> bool:
    source = model.get("source_token")
    target = model.get("target_token")
    return (
        model.get("morphism_class") == "identity"
        and model.get("identity_invariant_preserved") is True
        and model.get("residue_token") in {None, ""}
        and source not in {None, ""}
        and target not in {None, ""}
        and source == target
        and model.get("lifecycle_identity_invariant") is True
    )


def morphism_shape_valid(model: dict[str, Any]) -> bool:
    source = model.get("source_token")
    target = model.get("target_token")
    residue = model.get("residue_token")
    if source in {None, ""} or target in {None, ""}:
        return False
    mclass = model.get("morphism_class")
    if mclass == "identity":
        return residue in {None, ""} and source == target
    if mclass == "residue":
        return residue not in {None, "", source} and source == target
    if mclass == "rebirth":
        return residue not in {None, "", source, target} and source != target
    return False


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
            tokens_separated = unique_nonempty_values(
                model.get("identity_token"),
                model.get("residue_id"),
                model.get("rebirth_target_id"),
            )
            ok = (
                model.get("death") is True
                and model.get("live") is False
                and model.get("residue_id") not in {None, "", model.get("identity_token")}
                and model.get("rebirth_source_residue_id") == model.get("residue_id")
                and model.get("rebirth_target_id") not in {None, ""}
                and tokens_separated
                and model.get("residue_morphism_class") == "residue"
                and model.get("residue_morphism_source_id") == model.get("identity_token")
                and model.get("residue_morphism_residue_id") == model.get("residue_id")
                and model.get("residue_morphism_target_id") == model.get("identity_token")
                and model.get("morphism_class") == "rebirth"
                and model.get("morphism_source_id") == model.get("identity_token")
                and model.get("morphism_residue_id") == model.get("residue_id")
                and model.get("morphism_target_id") == model.get("rebirth_target_id")
                and model.get("identity_invariant_preserved") is False
                and model.get("claimed_identity_continuation") is False
            )
        elif theorem_id == "T133-K-ZERO":
            ok = (
                model.get("live_support") is True
                and model.get("admissible_nonempty") is True
                and model.get("cycle_witness") is True
                and model.get("claimed_k") == 0
                and zero_cause_active(model.get("zero_causes", {}))
                and not obstruction_active(model.get("obstructions", {}))
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
            if update_kind == "hybrid_guard_reset":
                guard = bool(model.get("guard"))
                expected_next = model.get("reset_target") if guard else model.get("step_target")
                no_smooth_flow_leak = (
                    not chart_declared
                    and model.get("flow_one_target") in {None, ""}
                    and model.get("smooth_step_target") in {None, ""}
                )
                shared_state_ok = model.get("smooth_state_type") == model.get("hybrid_state_type")
                reset_typed_ok = (
                    model.get("reset_source_mode") == model.get("current_mode")
                    and model.get("reset_target_mode") == model.get("target_mode")
                    and model.get("reset_codomain") == model.get("hybrid_state_type")
                    and model.get("post_reset_admissible") is True
                    and model.get("mode_invariant_preserved") is True
                )
                ok = (
                    model.get("actual_next") == expected_next
                    and model.get("derivative_requested") is False
                    and no_smooth_flow_leak
                    and shared_state_ok
                    and reset_typed_ok
                )
            elif update_kind == "proof_rewrite":
                ok = (
                    model.get("carrier_kind") in {"proof", "rewrite"}
                    and model.get("typed_update_relation") is True
                    and model.get("source_type") == model.get("target_type")
                    and model.get("derivative_requested") is False
                    and not chart_declared
                    and model.get("actual_next") == model.get("step_target")
                )
            elif update_kind == "smooth_chart":
                ok = (
                    chart_declared
                    and model.get("smooth_state_type") == model.get("source_type") == model.get("target_type")
                    and model.get("derivative_requested") is True
                    and model.get("flow_one_target") not in {None, ""}
                    and model.get("smooth_step_target") == model.get("flow_one_target")
                    and model.get("actual_next") == model.get("smooth_step_target")
                    and model.get("local_law_declared") is True
                    and model.get("chart_domain_contains_state") is True
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
            should_be_identity = endpoint_bound_identity(model)
            ok = morphism_shape_valid(model) and model.get("claimed_identity_continuation") is should_be_identity
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
        manifest_ref = str(model.get("manifest_ref"))
        approval_ref = str(model.get("approval_ref"))
        manifest_path = ROOT / manifest_ref
        approval_path = ROOT / approval_ref
        manifest = read_rel_json(manifest_ref)
        approval = read_rel_json(approval_ref)
        digest_bound = (
            model.get("manifest_sha256") == sha256_file(manifest_path)
            and model.get("approval_sha256") == sha256_file(approval_path)
        )
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
        any_common_lock = (
            manifest.get("global_no_send_lock") is True
            or manifest.get("owner_approved") is not True
            or manifest.get("publish_allowed") is not True
            or manifest.get("journal_submissions_allowed") is not True
        )
        channel_fields = {
            "github_release": "github_release_allowed",
            "zenodo_deposit": "zenodo_deposit_allowed",
            "software_heritage_deposit": "software_heritage_deposit_allowed",
            "journal_submission": "journal_submission_allowed",
            "doi_minting": "doi_minting_allowed",
        }
        requested = model.get("requested_channels", [])
        requested_channel_locked = any(
            channel not in channel_fields or manifest.get(channel_fields[channel]) is not True
            for channel in requested
        )
        approval_locked = (
            approval.get("decision") == "PENDING"
            and approval.get("owner_approved") is False
            and approval.get("owner_approval_required") is True
            and approval.get("no_send") is True
            and approval.get("publish_allowed") is False
            and approval.get("journal_submissions_allowed") is False
            and approval.get("journal_submission_allowed") is False
            and approval.get("github_release_allowed") is False
            and approval.get("zenodo_deposit_allowed") is False
            and approval.get("software_heritage_deposit_allowed") is False
            and approval.get("doi_minting_allowed") is False
        )
        if digest_bound and publish_requested and (approval_locked or all_locked or any_common_lock or requested_channel_locked):
            return "REJECT_PUBLIC_ACTION"
        return "NO_ACTION"
    if case_type == "no_send_hypothetical_control":
        return hypothetical_owner_approved_control(model)
    return "UNKNOWN"


def evaluate(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if any(key.startswith("observed_") for key in row):
        out["input_schema_violation"] = "input rows must not contain observed_* verdict fields"
        out["passed"] = False
        return out
    obs = observed(row)
    if row.get("theorem_id") == "OC133-NOSEND-001":
        model = row.get("model", {})
        if model.get("manifest_ref"):
            out["publish_manifest_ref"] = model.get("manifest_ref")
            out["publish_manifest_sha256"] = sha256_file(ROOT / str(model.get("manifest_ref")))
            out["expected_publish_manifest_sha256"] = model.get("manifest_sha256")
        if model.get("approval_ref"):
            out["owner_release_approval_ref"] = model.get("approval_ref")
            out["owner_release_approval_sha256"] = sha256_file(ROOT / str(model.get("approval_ref")))
            out["expected_owner_release_approval_sha256"] = model.get("approval_sha256")
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
    atlas_payload = json.loads(ATLAS.read_text(encoding="utf-8"))
    rows = [evaluate(row) for row in inputs["rows"]]
    failures = [row for row in rows if not row.get("passed")]
    lean_cert = read_json(LEAN_CERT) if LEAN_CERT.exists() else {}
    ref_audit = theorem_reference_audit(inputs, lean_cert)
    atlas_audit = atlas_external_binding_audit(inputs, atlas_payload, lean_cert)
    lean_source = ROOT / "formal" / "lean" / "OC133V12.lean"
    current_lean_sha256 = sha256_file(lean_source) if lean_source.exists() else None
    cert_lean_sha256_matches = lean_cert.get("lean_source_sha256") == current_lean_sha256
    live_lean_build = run_live_lake_build()
    current_source_manifest = source_manifest()
    current_source_manifest_sha256 = hashlib.sha256(json.dumps(current_source_manifest, sort_keys=True).encode("utf-8")).hexdigest()
    current_generated_artifact_manifest = generated_artifact_manifest()
    current_generated_artifact_manifest_sha256 = hashlib.sha256(json.dumps(current_generated_artifact_manifest, sort_keys=True).encode("utf-8")).hexdigest()
    cert_manifest_hashes = {row.get("ref"): row.get("sha256") for row in lean_cert.get("clean_source_manifest", []) if isinstance(row, dict)}
    current_manifest_hashes = {row.get("ref"): row.get("sha256") for row in current_source_manifest}
    cert_generated_hashes = {row.get("ref"): row.get("sha256") for row in lean_cert.get("generated_artifact_manifest", []) if isinstance(row, dict)}
    current_generated_hashes = {row.get("ref"): row.get("sha256") for row in current_generated_artifact_manifest}
    shared_manifest_mismatches = [
        ref for ref, digest in current_manifest_hashes.items()
        if cert_manifest_hashes.get(ref) != digest
    ]
    generated_manifest_mismatches = [
        ref for ref, digest in current_generated_hashes.items()
        if cert_generated_hashes.get(ref) != digest
    ]
    lean_cert_ok = (
        lean_cert.get("returncode") == 0
        and lean_cert.get("theorem_ref_missing_total") == 0
        and lean_cert.get("theorem_ref_present_total", 0) >= 10
        and ref_audit["theorem_ref_missing_total"] == 0
        and ref_audit["theorem_ref_bound_total"] >= 10
        and atlas_audit["failure_total"] == 0
        and cert_lean_sha256_matches
        and lean_cert.get("cache_free_build_required") is True
        and lean_cert.get("zero_job_cached_build_detected") is False
        and lean_cert.get("isolated_clean_checkout_build") is True
        and lean_cert.get("preexisting_lake_cache_detected") is False
        and lean_cert.get("post_build_lake_cache_created") is True
        and bool(lean_cert.get("build_transcript_sha256"))
        and lean_cert.get("clean_source_manifest_sha256") == current_source_manifest_sha256
        and lean_cert.get("generated_artifact_manifest_sha256") == current_generated_artifact_manifest_sha256
        and not shared_manifest_mismatches
        and not generated_manifest_mismatches
        and lean_cert.get("build_transcript_sha256") == live_lean_build.get("build_transcript_sha256")
        and lean_cert.get("lean_version_canonical") == live_lean_build.get("lean_version_canonical")
        and lean_cert.get("lake_version_canonical") == live_lean_build.get("lake_version_canonical")
    )
    certificate_binding_failures = []
    if not lean_cert_ok:
        certificate_binding_failures.append("LEAN_CERTIFICATE_NOT_CLEAN_OR_NOT_BOUND_TO_CURRENT_SOURCE")
    if live_lean_build.get("returncode") != 0:
        certificate_binding_failures.append("LIVE_LAKE_BUILD_FAILED_DURING_FINITE_MODEL_RUN")
    if ref_audit["theorem_ref_missing_total"] != 0:
        certificate_binding_failures.append("FINITE_ROW_THEOREM_REFS_NOT_BOUND_TO_CURRENT_SOURCE")
    if shared_manifest_mismatches:
        certificate_binding_failures.append("LEAN_CERTIFICATE_SOURCE_MANIFEST_HASH_MISMATCH")
    if generated_manifest_mismatches or lean_cert.get("generated_artifact_manifest_sha256") != current_generated_artifact_manifest_sha256:
        certificate_binding_failures.append("LEAN_CERTIFICATE_GENERATED_ARTIFACT_MANIFEST_HASH_MISMATCH")
    if atlas_audit["failure_total"] != 0:
        certificate_binding_failures.append("LEAN_ATLAS_EXTERNAL_JSON_BINDING_FAILED")
    if lean_cert.get("build_transcript_sha256") != live_lean_build.get("build_transcript_sha256"):
        certificate_binding_failures.append("LEAN_CERTIFICATE_BUILD_TRANSCRIPT_HASH_MISMATCH")
    if lean_cert.get("lean_version_canonical") != live_lean_build.get("lean_version_canonical") or lean_cert.get("lake_version_canonical") != live_lean_build.get("lake_version_canonical"):
        certificate_binding_failures.append("LEAN_CERTIFICATE_TOOLCHAIN_VERSION_MISMATCH")
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
        "lean_source_ref": "formal/lean/OC133V12.lean",
        "current_lean_source_sha256": current_lean_sha256,
        "certificate_lean_source_sha256": lean_cert.get("lean_source_sha256"),
        "cert_lean_sha256_matches_current_source": cert_lean_sha256_matches,
        "lean_build_returncode": lean_cert.get("returncode"),
        "lean_build_execution_status": lean_cert.get("execution_status"),
        "lean_cache_free_build_required": lean_cert.get("cache_free_build_required"),
        "lean_zero_job_cached_build_detected": lean_cert.get("zero_job_cached_build_detected"),
        "live_lean_build_returncode": live_lean_build.get("returncode"),
        "live_lean_build_execution_status": live_lean_build.get("execution_status"),
        "live_lean_build_clean_returncode": live_lean_build.get("clean_returncode"),
        "live_lean_build_zero_job_cached_build_detected": live_lean_build.get("zero_job_cached_build_detected"),
        "live_lean_preexisting_lake_cache_detected": live_lean_build.get("preexisting_lake_cache_detected"),
        "live_lean_post_build_lake_cache_created": live_lean_build.get("post_build_lake_cache_created"),
        "live_lean_build_transcript_sha256": live_lean_build.get("build_transcript_sha256"),
        "live_lean_version_observed": live_lean_build.get("lean_version_observed"),
        "live_lake_version_observed": live_lean_build.get("lake_version_observed"),
        "live_lean_version_canonical": live_lean_build.get("lean_version_canonical"),
        "live_lake_version_canonical": live_lean_build.get("lake_version_canonical"),
        "certificate_lean_version_canonical": lean_cert.get("lean_version_canonical"),
        "certificate_lake_version_canonical": lean_cert.get("lake_version_canonical"),
        "live_lean_clean_source_manifest_sha256": current_source_manifest_sha256,
        "certificate_clean_source_manifest_sha256": lean_cert.get("clean_source_manifest_sha256"),
        "generated_artifact_manifest_sha256": current_generated_artifact_manifest_sha256,
        "certificate_generated_artifact_manifest_sha256": lean_cert.get("generated_artifact_manifest_sha256"),
        "source_manifest_mismatch_total": len(shared_manifest_mismatches),
        "source_manifest_mismatches": shared_manifest_mismatches[:20],
        "generated_artifact_manifest_mismatch_total": len(generated_manifest_mismatches),
        "generated_artifact_manifest_mismatches": generated_manifest_mismatches[:20],
        "atlas_external_binding_audit": atlas_audit,
        "live_lean_build_stdout_tail": live_lean_build.get("stdout_tail"),
        "live_lean_build_stderr_tail": live_lean_build.get("stderr_tail"),
        "lean_theorem_ref_present_total": lean_cert.get("theorem_ref_present_total", 0),
        "lean_theorem_ref_missing_total": lean_cert.get("theorem_ref_missing_total", 999),
        "finite_row_theorem_ref_total": ref_audit["theorem_ref_total"],
        "finite_row_theorem_ref_bound_total": ref_audit["theorem_ref_bound_total"],
        "finite_row_theorem_ref_missing_total": ref_audit["theorem_ref_missing_total"],
        "finite_row_theorem_refs": ref_audit["theorem_refs"],
        "finite_row_theorem_ref_missing": ref_audit["theorem_ref_missing"],
        "certificate_binding_failure_total": len(certificate_binding_failures),
        "certificate_binding_failures": certificate_binding_failures,
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
        "semantic_failure_total": len(failures),
        "failure_total": len(failures) + len(certificate_binding_failures),
        "machine_checked_subset_total": lean_cert.get("theorem_ref_present_total", 0) if lean_cert_ok else 0,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures and not certificate_binding_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
