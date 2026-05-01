from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/FormalScience"
BLOCKER_ID = "CERBERUS-K-OC133-MATHEMATICS-EMPIRICAL-CLASS-MISMATCH-001"

EVIDENCE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
FORMAL_EVIDENCE_SCHEMA_ID = "OC133_FORMAL_SUPPORT_EVIDENCE_v1"
EXECUTION_REPORT_SCHEMA_ID = "OC133_MATHEMATICS_FORMAL_EVIDENCE_EXECUTION_REPORT_v3"
PROTOCOL_PACKET_SCHEMA_ID = "OC133_MATHEMATICS_FORMAL_EVIDENCE_PROTOCOL_PACKET_v3"

EXECUTOR_REL = "validation/heldout/domain_evidence/mathematics_evidence_executor.py"
OUTPUT_ROOT_REL = "validation/heldout/grand_science/mathematics"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
DEFAULT_SNAPSHOT_REF = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"
THEOREM_REGISTRY_REL = "proofs/THEOREM_REGISTRY_1_3_3.json"

DOMAIN = "mathematics"
MINIMUM_N = 20
HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
BYTE_HASH_POLICY = "sha256 over artifact bytes"
OBJECT_HASH_POLICY = "sha256 over sorted canonical JSON"
COMPARATOR_PREDICTION = "ACCEPT"


@dataclass(frozen=True)
class CaseEvidence:
    case_id: str
    theorem_id: str
    case_type: str
    lean_ref: str
    semantic_evaluator_ref: str | None
    predicted_verdict: str
    observed_verdict: str
    comparator_prediction: str
    model_residual: int
    comparator_residual: int
    input_model_sha256: str
    output_model_sha256: str
    negative_control_id: str | None
    negative_control_rejected: bool
    validation_failures: list[str]

    @property
    def valid(self) -> bool:
        return not self.validation_failures


@dataclass(frozen=True)
class MathematicsEvidence:
    snapshot_ref: str
    input_ref: str
    snapshot_payload: dict[str, Any]
    input_payload: dict[str, Any]
    snapshot_sha256: str
    snapshot_byte_sha256: str
    snapshot_byte_count: int
    snapshot_canonical_sha256: str
    input_sha256: str
    input_canonical_sha256: str
    input_byte_count: int
    cases: list[CaseEvidence]
    corpus_failures: list[str]
    source_separation: dict[str, Any]

    @property
    def eligible_n(self) -> int:
        return len([row for row in self.cases if row.valid])

    @property
    def model_residual(self) -> float:
        return float(sum(row.model_residual for row in self.cases if row.valid))

    @property
    def comparator_residual(self) -> float:
        return float(sum(row.comparator_residual for row in self.cases if row.valid))

    @property
    def superiority_margin(self) -> float:
        return self.comparator_residual - self.model_residual

    @property
    def negative_control_total(self) -> int:
        return len([row for row in self.cases if row.valid and row.predicted_verdict != COMPARATOR_PREDICTION])

    @property
    def negative_control_rejected_total(self) -> int:
        return len([row for row in self.cases if row.valid and row.negative_control_rejected])

    @property
    def valid_under_executor(self) -> bool:
        return (
            not self.corpus_failures
            and self.eligible_n >= MINIMUM_N
            and self.model_residual == 0.0
            and self.comparator_residual > self.model_residual
            and self.negative_control_total > 0
            and self.negative_control_total == self.negative_control_rejected_total
            and self.source_separation.get("pre_target_lock") is True
            and self.source_separation.get("target_hidden_until_scoring") is True
        )


@dataclass(frozen=True)
class DomainCandidate:
    domain: str
    pack_ref: str
    pack: dict[str, Any]
    report_row: dict[str, Any]


def repo_root() -> Path:
    return ROOT


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def lf_normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_lf_normalized_text(path: Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def default_requirements() -> dict[str, Any]:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "minimum_per_domain_n": MINIMUM_N,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": ["prospective", "target_blind"],
    }


def load_requirements(root: Path) -> dict[str, Any]:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return default_requirements()
    payload = read_json(path)
    return payload if isinstance(payload, dict) else default_requirements()


def minimum_n(root: Path) -> int:
    value = load_requirements(root).get("minimum_per_domain_n", MINIMUM_N)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else MINIMUM_N


def rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("rows", [])
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def has_observed_target_field(row: dict[str, Any]) -> bool:
    forbidden = {
        "observed_verdict",
        "observed_drop_verdict",
        "observed_keep_verdict",
        "observed_reduction_verdict",
        "passed",
    }
    if any(key in row for key in forbidden):
        return True
    model = row.get("model")
    return isinstance(model, dict) and any(key in model for key in forbidden)


def verdict_residual(predicted: str, observed: str) -> int:
    return 0 if predicted == observed else 1


def input_by_case_id(input_payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    failures: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows(input_payload):
        case_id = str(row.get("case_id") or "").strip()
        if not case_id:
            failures.append("INPUT_ROW_WITHOUT_CASE_ID")
            continue
        if case_id in indexed:
            failures.append(f"INPUT_CASE_ID_DUPLICATE::{case_id}")
            continue
        indexed[case_id] = row
        if has_observed_target_field(row):
            failures.append(f"TARGET_LEAKAGE_IN_INPUT_ROW::{case_id}")
    if int(input_payload.get("observed_field_total", 0) or 0) != 0:
        failures.append("INPUT_OBSERVED_FIELD_TOTAL_NONZERO")
    if int(input_payload.get("flag_oracle_key_total", 0) or 0) != 0:
        failures.append("INPUT_FLAG_ORACLE_KEY_TOTAL_NONZERO")
    return indexed, ordered_unique(failures)


def build_case_evidence(output_row: dict[str, Any], input_row: dict[str, Any] | None) -> CaseEvidence:
    case_id = str(output_row.get("case_id") or "").strip()
    theorem_id = str(output_row.get("theorem_id") or "").strip()
    case_type = str(output_row.get("case_type") or "").strip()
    expected = str((input_row or output_row).get("expected_verdict") or "").strip()
    observed = str(output_row.get("observed_verdict") or "").strip()
    input_model = (input_row or {}).get("model")
    output_model = output_row.get("model")
    input_model_sha256 = sha256_object(input_model)
    output_model_sha256 = sha256_object(output_model)
    lean_ref = str((input_row or {}).get("lean_ref") or "").strip()
    output_lean_ref = str(output_row.get("lean_theorem_ref") or "").strip()
    semantic_evaluator_ref = output_row.get("semantic_evaluator_ref")
    comparator_residual = verdict_residual(COMPARATOR_PREDICTION, observed)
    model_residual = verdict_residual(expected, observed)
    failures: list[str] = []

    if not case_id:
        failures.append("CASE_ID_MISSING")
    if input_row is None:
        failures.append("INPUT_ROW_MISSING")
    if case_type != "theorem_case":
        failures.append("CASE_TYPE_NOT_THEOREM_CASE")
    if not theorem_id:
        failures.append("THEOREM_ID_MISSING")
    if not isinstance(input_model, dict) or not input_model:
        failures.append("INPUT_MODEL_FACTS_MISSING")
    if not isinstance(output_model, dict) or not output_model:
        failures.append("OUTPUT_MODEL_FACTS_MISSING")
    if input_model_sha256 != output_model_sha256:
        failures.append("INPUT_OUTPUT_MODEL_HASH_MISMATCH")
    if expected not in {"ACCEPT", "REJECT"}:
        failures.append("EXPECTED_VERDICT_INVALID")
    if observed not in {"ACCEPT", "REJECT"}:
        failures.append("OBSERVED_VERDICT_INVALID")
    if str(output_row.get("expected_verdict") or "").strip() != expected:
        failures.append("OUTPUT_EXPECTED_VERDICT_NOT_INPUT_BOUND")
    if output_row.get("passed") is not (expected == observed):
        failures.append("PASSED_FLAG_NOT_DERIVED_FROM_EXPECTED_OBSERVED")
    if not lean_ref or not output_lean_ref or lean_ref != output_lean_ref:
        failures.append("LEAN_REF_BINDING_MISMATCH")

    negative_control_rejected = expected != COMPARATOR_PREDICTION and comparator_residual > model_residual
    return CaseEvidence(
        case_id=case_id,
        theorem_id=theorem_id,
        case_type=case_type,
        lean_ref=output_lean_ref or lean_ref,
        semantic_evaluator_ref=str(semantic_evaluator_ref) if semantic_evaluator_ref else None,
        predicted_verdict=expected,
        observed_verdict=observed,
        comparator_prediction=COMPARATOR_PREDICTION,
        model_residual=model_residual,
        comparator_residual=comparator_residual,
        input_model_sha256=input_model_sha256,
        output_model_sha256=output_model_sha256,
        negative_control_id=str(output_row.get("negative_control_id") or "").strip() or None,
        negative_control_rejected=negative_control_rejected,
        validation_failures=ordered_unique(failures),
    )


def source_separation(
    snapshot_ref: str,
    input_ref: str,
    input_payload: dict[str, Any],
    input_sha256_bound: bool,
    no_input_leakage: bool,
) -> dict[str, Any]:
    return {
        "mode": "target_blind",
        "pre_target_lock": input_sha256_bound,
        "target_hidden_until_scoring": no_input_leakage,
        "training_sources": [
            f"{input_ref}::rows(case_id,case_type,expected_verdict,model,lean_ref)",
            f"{input_ref}::sha256={sha256_object(input_payload)}",
        ],
        "target_sources": [
            f"{snapshot_ref}::rows(case_id,observed_verdict,passed,lean_theorem_ref)",
            f"{snapshot_ref}::lean_build_certificate_ref",
        ],
    }


def load_mathematics_evidence(root: Path, snapshot_ref: str = DEFAULT_SNAPSHOT_REF) -> MathematicsEvidence:
    snapshot_path = resolve_under_root(root, snapshot_ref)
    snapshot_payload = read_json(snapshot_path)
    if not isinstance(snapshot_payload, dict):
        raise ValueError("mathematics proof corpus snapshot must be a JSON object")
    input_ref = str(snapshot_payload.get("input_ref") or "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json")
    input_path = resolve_under_root(root, input_ref)
    input_payload = read_json(input_path)
    if not isinstance(input_payload, dict):
        raise ValueError("mathematics finite-model input must be a JSON object")

    bound_input_sha = str(snapshot_payload.get("input_sha256") or "")
    actual_input_sha = sha256_file(input_path)
    input_hash_bound = bool(bound_input_sha) and bound_input_sha == actual_input_sha
    indexed_input, input_failures = input_by_case_id(input_payload)
    corpus_failures: list[str] = list(input_failures)
    if not input_hash_bound:
        corpus_failures.append("SNAPSHOT_INPUT_SHA256_MISMATCH")
    if snapshot_payload.get("lean_build_returncode") != 0 or snapshot_payload.get("live_lean_build_returncode") != 0:
        corpus_failures.append("LEAN_BUILD_NOT_CLEAN")
    if snapshot_payload.get("cert_lean_sha256_matches_current_source") is not True:
        corpus_failures.append("LEAN_CERTIFICATE_SOURCE_BINDING_MISMATCH")
    if int(snapshot_payload.get("failure_total", 0) or 0) != 0:
        corpus_failures.append("FINITE_MODEL_FAILURE_TOTAL_NONZERO")

    case_rows = [
        build_case_evidence(row, indexed_input.get(str(row.get("case_id") or "").strip()))
        for row in rows(snapshot_payload)
        if row.get("case_type") == "theorem_case"
    ]
    duplicate_case_ids = [
        case_id
        for case_id in sorted({row.case_id for row in case_rows if row.case_id})
        if len([row for row in case_rows if row.case_id == case_id]) > 1
    ]
    corpus_failures.extend(f"SNAPSHOT_CASE_ID_DUPLICATE::{case_id}" for case_id in duplicate_case_ids)
    no_input_leakage = not any(failure.startswith("TARGET_LEAKAGE_IN_INPUT_ROW") for failure in input_failures)

    return MathematicsEvidence(
        snapshot_ref=snapshot_ref,
        input_ref=input_ref,
        snapshot_payload=snapshot_payload,
        input_payload=input_payload,
        snapshot_sha256=sha256_lf_normalized_text(snapshot_path),
        snapshot_byte_sha256=sha256_file(snapshot_path),
        snapshot_byte_count=len(snapshot_path.read_bytes()),
        snapshot_canonical_sha256=sha256_object(snapshot_payload),
        input_sha256=actual_input_sha,
        input_canonical_sha256=sha256_object(input_payload),
        input_byte_count=len(input_path.read_bytes()),
        cases=case_rows,
        corpus_failures=ordered_unique(corpus_failures),
        source_separation=source_separation(snapshot_ref, input_ref, input_payload, input_hash_bound, no_input_leakage),
    )


def case_rows_for_report(evidence: MathematicsEvidence) -> list[dict[str, Any]]:
    return [
        {
            "case_id": row.case_id,
            "theorem_id": row.theorem_id,
            "case_type": row.case_type,
            "lean_ref": row.lean_ref,
            "semantic_evaluator_ref": row.semantic_evaluator_ref,
            "predicted_verdict_from_input": row.predicted_verdict,
            "observed_verdict_from_executable_snapshot": row.observed_verdict,
            "comparator_prediction": row.comparator_prediction,
            "model_residual": row.model_residual,
            "comparator_residual": row.comparator_residual,
            "input_model_sha256": row.input_model_sha256,
            "output_model_sha256": row.output_model_sha256,
            "negative_control_id": row.negative_control_id,
            "negative_control_rejected": row.negative_control_rejected,
            "valid_under_executor": row.valid,
            "validation_failures": row.validation_failures,
        }
        for row in evidence.cases
    ]


def validate_negative_controls(evidence: MathematicsEvidence) -> list[str]:
    failures: list[str] = []
    if evidence.negative_control_total == 0:
        failures.append("NEGATIVE_CONTROL_ROWS_MISSING")
    if evidence.negative_control_total != evidence.negative_control_rejected_total:
        failures.append(
            f"NEGATIVE_CONTROL_ROWS_NOT_REJECTED::{evidence.negative_control_rejected_total}/{evidence.negative_control_total}"
        )
    if evidence.comparator_residual <= evidence.model_residual:
        failures.append("COMPARATOR_NOT_WORSE_THAN_MODEL")
    return ordered_unique(failures)


def executor_blockers(evidence: MathematicsEvidence, min_n: int, gate_failures: list[str]) -> list[str]:
    blockers: list[str] = []
    blockers.extend(evidence.corpus_failures)
    blockers.extend(
        f"CASE_VALIDATION::{row.case_id}::{failure}"
        for row in evidence.cases
        for failure in row.validation_failures
    )
    blockers.extend(validate_negative_controls(evidence))
    if evidence.eligible_n < min_n:
        blockers.append(f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{evidence.eligible_n}/{min_n}")
    if evidence.model_residual != 0.0:
        blockers.append(f"MODEL_RESIDUAL_NONZERO::{evidence.model_residual}")
    if evidence.source_separation.get("pre_target_lock") is not True:
        blockers.append("PRE_TARGET_LOCK_FAILED")
    if evidence.source_separation.get("target_hidden_until_scoring") is not True:
        blockers.append("TARGET_LEAKAGE_FAILED")
    blockers.extend(f"GRAND_GATE::{failure}" for failure in gate_failures)
    return ordered_unique(blockers)


def source_assessment(evidence: MathematicsEvidence) -> dict[str, Any]:
    valid_case_total = evidence.eligible_n
    theorem_ids = ordered_unique([row.theorem_id for row in evidence.cases if row.valid and row.theorem_id])
    return {
        "source_kind": "executable_finite_model_proof_corpus",
        "support_route": "formal",
        "formal_support_source": True,
        "grand_empirical_source": False,
        "empirical_support_allowed": False,
        "scope_statement": "machine-checkable mathematics-domain finite/proof evidence; rows support formal claims only and are not empirical grand-science observations",
        "candidate_n_policy": "N counts valid theorem_case executions joined from raw finite-model input rows to executed observed verdict rows by case_id for the formal route only",
        "case_total": len(evidence.cases),
        "valid_case_total": valid_case_total,
        "unique_theorem_id_total": len(theorem_ids),
        "negative_control_total": evidence.negative_control_total,
        "negative_control_rejected_total": evidence.negative_control_rejected_total,
        "lean_theorem_ref_total": int(evidence.snapshot_payload.get("lean_theorem_ref_total", 0) or 0),
        "lean_build_returncode": evidence.snapshot_payload.get("lean_build_returncode"),
        "live_lean_build_returncode": evidence.snapshot_payload.get("live_lean_build_returncode"),
        "lean_source_ref": evidence.snapshot_payload.get("lean_source_ref"),
        "current_lean_source_sha256": evidence.snapshot_payload.get("current_lean_source_sha256"),
        "certificate_lean_source_sha256": evidence.snapshot_payload.get("certificate_lean_source_sha256"),
    }


def theorem_registry_rows(root: Path) -> dict[str, dict[str, Any]]:
    path = root / THEOREM_REGISTRY_REL
    if not path.exists():
        return {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {}
    return {
        str(row.get("theorem_id")): row
        for row in rows(payload)
        if row.get("theorem_id")
    }


def refs_exist_under_root(root: Path, refs: list[str]) -> bool:
    for ref in refs:
        try:
            path = resolve_under_root(root, ref)
        except ValueError:
            return False
        if not path.exists():
            return False
    return True


def formal_support_audit(root: Path, evidence: MathematicsEvidence, min_n: int) -> dict[str, Any]:
    theorem_rows = theorem_registry_rows(root)
    valid_cases = [row for row in evidence.cases if row.valid]
    by_theorem: dict[str, list[CaseEvidence]] = {}
    for row in valid_cases:
        by_theorem.setdefault(row.theorem_id, []).append(row)

    snapshot_lean_refs = set(string for string in evidence.snapshot_payload.get("lean_theorem_refs", []) if isinstance(string, str))
    obligation_rows: list[dict[str, Any]] = []
    failures: list[str] = []
    if not theorem_rows:
        failures.append("FORMAL_THEOREM_REGISTRY_MISSING")
    if evidence.eligible_n < min_n:
        failures.append(f"FORMAL_FINITE_CASE_N_BELOW_MINIMUM::{evidence.eligible_n}/{min_n}")
    failures.extend(evidence.corpus_failures)
    failures.extend(
        f"FORMAL_CASE_VALIDATION::{row.case_id}::{failure}"
        for row in evidence.cases
        for failure in row.validation_failures
    )
    failures.extend(validate_negative_controls(evidence))
    if evidence.model_residual != 0.0:
        failures.append(f"FORMAL_MODEL_RESIDUAL_NONZERO::{evidence.model_residual}")

    for theorem_id in ordered_unique([row.theorem_id for row in valid_cases if row.theorem_id]):
        theorem_row = theorem_rows.get(theorem_id, {})
        theorem_cases = by_theorem.get(theorem_id, [])
        proof_sheet_ref = str(theorem_row.get("proof_sheet_ref") or "").strip()
        primary_lean_ref = str(theorem_row.get("lean_ref") or "").strip()
        finite_case_ids = ordered_unique([row.case_id for row in theorem_cases if row.case_id])
        finite_verdicts = {row.predicted_verdict for row in theorem_cases}
        case_lean_refs = ordered_unique([row.lean_ref for row in theorem_cases if row.lean_ref])
        public_claim_boundary = str(theorem_row.get("public_claim_boundary") or "").strip()
        theorem_failures: list[str] = []

        if not theorem_row:
            theorem_failures.append(f"FORMAL_THEOREM_ID_UNKNOWN::{theorem_id}")
        if not proof_sheet_ref:
            theorem_failures.append(f"FORMAL_PROOF_SHEET_REF_MISSING::{theorem_id}")
        elif not refs_exist_under_root(root, [proof_sheet_ref]):
            theorem_failures.append(f"FORMAL_PROOF_SHEET_REF_NOT_FOUND::{theorem_id}::{proof_sheet_ref}")
        if not primary_lean_ref:
            theorem_failures.append(f"FORMAL_PRIMARY_LEAN_REF_MISSING::{theorem_id}")
        elif primary_lean_ref not in snapshot_lean_refs and primary_lean_ref not in case_lean_refs:
            theorem_failures.append(f"FORMAL_PRIMARY_LEAN_REF_NOT_BOUND::{theorem_id}::{primary_lean_ref}")
        missing_case_lean_refs = [ref for ref in case_lean_refs if snapshot_lean_refs and ref not in snapshot_lean_refs]
        if not case_lean_refs or missing_case_lean_refs:
            theorem_failures.append(f"FORMAL_CASE_LEAN_REFS_NOT_BOUND::{theorem_id}")
        if "ACCEPT" not in finite_verdicts:
            theorem_failures.append(f"FORMAL_FINITE_POSITIVE_CASE_MISSING::{theorem_id}")
        if "REJECT" not in finite_verdicts:
            theorem_failures.append(f"FORMAL_FINITE_NEGATIVE_CASE_MISSING::{theorem_id}")
        if not public_claim_boundary:
            theorem_failures.append(f"FORMAL_PUBLIC_CLAIM_BOUNDARY_MISSING::{theorem_id}")

        failures.extend(theorem_failures)
        obligation_rows.append(
            {
                "theorem_id": theorem_id,
                "proof_sheet_ref": proof_sheet_ref or None,
                "proof_sheet_ref_exists": bool(proof_sheet_ref) and refs_exist_under_root(root, [proof_sheet_ref]),
                "primary_lean_ref": primary_lean_ref or None,
                "case_lean_refs": case_lean_refs,
                "finite_case_ids": finite_case_ids,
                "finite_positive_case_ids": [row.case_id for row in theorem_cases if row.predicted_verdict == "ACCEPT"],
                "finite_negative_case_ids": [row.case_id for row in theorem_cases if row.predicted_verdict == "REJECT"],
                "public_claim_boundary": public_claim_boundary or None,
                "formal_obligation_passed": not theorem_failures,
                "formal_obligation_failures": theorem_failures,
            }
        )

    if not obligation_rows:
        failures.append("FORMAL_THEOREM_OBLIGATIONS_MISSING")

    proof_sheet_refs = ordered_unique([str(row.get("proof_sheet_ref")) for row in obligation_rows if row.get("proof_sheet_ref")])
    lean_refs = ordered_unique(
        [
            ref
            for row in obligation_rows
            for ref in [row.get("primary_lean_ref"), *row.get("case_lean_refs", [])]
            if isinstance(ref, str) and ref
        ]
    )
    finite_case_ids = ordered_unique(
        [case_id for row in obligation_rows for case_id in row.get("finite_case_ids", []) if isinstance(case_id, str)]
    )
    failures = ordered_unique(failures)
    return {
        "support_route": "formal",
        "formal_support_allowed": not failures,
        "support_verdict": "FORMAL_SUPPORT_ACCEPTED" if not failures else "FORMAL_SUPPORT_BLOCKED",
        "failure_total": len(failures),
        "failures": failures,
        "theorem_ids": ordered_unique([row["theorem_id"] for row in obligation_rows]),
        "proof_sheet_refs": proof_sheet_refs,
        "lean_refs": lean_refs,
        "finite_case_ids": finite_case_ids,
        "formal_obligations": obligation_rows,
    }


def build_candidate_pack(evidence: MathematicsEvidence, min_n: int, formal_audit: dict[str, Any]) -> dict[str, Any]:
    support_allowed = formal_audit.get("formal_support_allowed") is True and evidence.eligible_n >= min_n
    return {
        "schema_id": FORMAL_EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-FORMAL-MATHEMATICS-FINITE-PROOF-CORPUS-V3",
        "domain": DOMAIN,
        "support_route": "formal",
        "evidence_class": "formal_finite_proof_corpus",
        "claim_support_scope": "formal_claims_only",
        "empirical_support_allowed": False,
        "formal_support_allowed": support_allowed,
        "formal_support_verdict": "FORMAL_SUPPORT_ACCEPTED" if support_allowed else "FORMAL_SUPPORT_BLOCKED",
        "grand_toe_support_allowed": False,
        "grand_empirical_support_allowed": False,
        "route_separation_policy": "Mathematics finite/proof rows support formal claims through theorem/proof/Lean/finite obligations only; they are never counted as empirical grand-science evidence.",
        "source_separation": evidence.source_separation,
        "n": evidence.eligible_n,
        "theorem_ids": formal_audit["theorem_ids"],
        "proof_sheet_refs": formal_audit["proof_sheet_refs"],
        "lean_refs": formal_audit["lean_refs"],
        "finite_case_ids": formal_audit["finite_case_ids"],
        "formal_obligations": formal_audit["formal_obligations"],
        "formal_falsifiers": [
            "Any theorem ID is absent from the theorem registry.",
            "Any proof sheet ref, Lean ref, finite positive case, finite negative case, or public claim boundary is missing.",
            "Any counted finite row fails replay, target-leakage, model-hash, Lean-binding, or expected/observed verdict checks.",
        ],
        "formal_audit_failures": formal_audit["failures"],
    }


def tampered_snapshot_payload(evidence: MathematicsEvidence) -> dict[str, Any]:
    mutated = json.loads(json.dumps(evidence.snapshot_payload))
    for row in mutated.get("rows", []):
        if isinstance(row, dict) and row.get("case_type") == "theorem_case":
            row["observed_verdict"] = "REJECT" if row.get("observed_verdict") == "ACCEPT" else "ACCEPT"
            break
    return mutated


def run_tamper_tests(evidence: MathematicsEvidence) -> list[dict[str, Any]]:
    mutated_snapshot = tampered_snapshot_payload(evidence)
    mutated_case = None
    indexed_input, _failures = input_by_case_id(evidence.input_payload)
    for row in rows(mutated_snapshot):
        if row.get("case_type") == "theorem_case":
            mutated_case = build_case_evidence(row, indexed_input.get(str(row.get("case_id") or "").strip()))
            break
    accept_all_control_fails = "COMPARATOR_NOT_WORSE_THAN_MODEL" in validate_negative_controls(
        MathematicsEvidence(
            snapshot_ref=evidence.snapshot_ref,
            input_ref=evidence.input_ref,
            snapshot_payload=evidence.snapshot_payload,
            input_payload=evidence.input_payload,
            snapshot_sha256=evidence.snapshot_sha256,
            snapshot_byte_sha256=evidence.snapshot_byte_sha256,
            snapshot_byte_count=evidence.snapshot_byte_count,
            snapshot_canonical_sha256=evidence.snapshot_canonical_sha256,
            input_sha256=evidence.input_sha256,
            input_canonical_sha256=evidence.input_canonical_sha256,
            input_byte_count=evidence.input_byte_count,
            cases=[
                CaseEvidence(
                    case_id=row.case_id,
                    theorem_id=row.theorem_id,
                    case_type=row.case_type,
                    lean_ref=row.lean_ref,
                    semantic_evaluator_ref=row.semantic_evaluator_ref,
                    predicted_verdict=row.predicted_verdict,
                    observed_verdict=row.observed_verdict,
                    comparator_prediction=row.predicted_verdict,
                    model_residual=row.model_residual,
                    comparator_residual=row.model_residual,
                    input_model_sha256=row.input_model_sha256,
                    output_model_sha256=row.output_model_sha256,
                    negative_control_id=row.negative_control_id,
                    negative_control_rejected=False,
                    validation_failures=row.validation_failures,
                )
                for row in evidence.cases
            ],
            corpus_failures=evidence.corpus_failures,
            source_separation=evidence.source_separation,
        )
    )
    return [
        {
            "test_id": "mathematics-finite-row-tamper-hash-changes",
            "description": "mutating an executed theorem_case observed_verdict must change the canonical snapshot hash",
            "passed": sha256_object(mutated_snapshot) != evidence.snapshot_canonical_sha256,
        },
        {
            "test_id": "mathematics-finite-row-tamper-replay-detected",
            "description": "mutating an executed theorem_case observed_verdict must invalidate the derived passed flag/residual binding",
            "passed": mutated_case is not None and bool(mutated_case.validation_failures),
            "mutated_case_failures": mutated_case.validation_failures if mutated_case else ["MUTATED_CASE_MISSING"],
        },
        {
            "test_id": "mathematics-target-leakage-input-scan",
            "description": "finite-model input rows must contain no observed target fields",
            "passed": evidence.source_separation.get("target_hidden_until_scoring") is True,
        },
        {
            "test_id": "mathematics-accept-all-negative-control-rejected",
            "description": "the accept-all comparator must be worse than executable row-level replay",
            "passed": not validate_negative_controls(evidence),
            "model_residual": evidence.model_residual,
            "comparator_residual": evidence.comparator_residual,
        },
        {
            "test_id": "mathematics-negative-control-mutation-rejected",
            "description": "replacing the comparator by the model prediction must fail negative-control validation",
            "passed": accept_all_control_fails,
            "expected_rejection": "COMPARATOR_NOT_WORSE_THAN_MODEL",
        },
    ]


def build_domain_candidate(
    root: Path,
    snapshot_ref: str = DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> DomainCandidate:
    min_n = minimum_n(root)
    requirements = load_requirements(root)
    evidence = load_mathematics_evidence(root, snapshot_ref)
    tamper_tests = run_tamper_tests(evidence)
    tamper_failures = [f"TAMPER_TEST_FAILED::{row['test_id']}" for row in tamper_tests if row.get("passed") is not True]
    formal_audit = formal_support_audit(root, evidence, min_n)
    if tamper_failures:
        formal_audit = {
            **formal_audit,
            "formal_support_allowed": False,
            "support_verdict": "FORMAL_SUPPORT_BLOCKED",
            "failures": ordered_unique([*formal_audit["failures"], *tamper_failures]),
        }
        formal_audit["failure_total"] = len(formal_audit["failures"])
    pack = build_candidate_pack(evidence, min_n, formal_audit)
    gate_failures = grand_factory.pack_failure_reasons(pack, requirements)
    blockers = executor_blockers(evidence, min_n, [])
    formal_blockers = formal_audit["failures"]
    pack_ref = f"{output_root_rel}/mathematics_candidate_evidence_pack.json"
    valid_under_executor = not blockers and not formal_blockers
    report_row = {
        "domain": DOMAIN,
        "status": "FORMAL_SUPPORT_ACCEPTED" if valid_under_executor else "BLOCKED_PENDING_MATHEMATICS_FORMAL_EVIDENCE_REPAIR",
        "candidate_pack_ref": pack_ref,
        "candidate_pack_sha256": sha256_object(pack),
        "candidate_pack_hash_policy": OBJECT_HASH_POLICY,
        "snapshot_ref": evidence.snapshot_ref,
        "snapshot_sha256": evidence.snapshot_sha256,
        "snapshot_sha256_policy": HASH_POLICY,
        "snapshot_byte_sha256": evidence.snapshot_byte_sha256,
        "snapshot_byte_sha256_policy": BYTE_HASH_POLICY,
        "snapshot_byte_count": evidence.snapshot_byte_count,
        "snapshot_canonical_sha256": evidence.snapshot_canonical_sha256,
        "snapshot_canonical_hash_policy": OBJECT_HASH_POLICY,
        "input_ref": evidence.input_ref,
        "input_sha256": evidence.input_sha256,
        "input_canonical_sha256": evidence.input_canonical_sha256,
        "input_byte_count": evidence.input_byte_count,
        "target_blind_ref": TARGET_BLIND_REL,
        "target_blind_row_usage": "bounded aggregate table retained as external context; row-level evidence is derived from finite-model input/output artifact separation",
        "source_assessment": source_assessment(evidence),
        "source_separation": evidence.source_separation,
        "candidate_n": evidence.eligible_n,
        "minimum_n": min_n,
        "missing_n": max(0, min_n - evidence.eligible_n),
        "support_route": "formal",
        "formal_support_allowed": pack["formal_support_allowed"],
        "formal_support_verdict": pack["formal_support_verdict"],
        "empirical_support_allowed": False,
        "grand_toe_support_allowed": pack["grand_toe_support_allowed"],
        "grand_empirical_support_allowed": False,
        "route_separation_policy": pack["route_separation_policy"],
        "residuals": {
            "model": evidence.model_residual,
            "comparator": evidence.comparator_residual,
            "superiority_margin": evidence.superiority_margin,
            "metric_scope": "formal_replay_audit_only_not_empirical_superiority",
        },
        "negative_controls": [
            {
                "control_id": "OC133-MATH-FINITE-PROOF-ACCEPT-ALL-NEGATIVE-CONTROL",
                "description": "The accept-all comparator must be rejected by theorem_case rows whose pre-execution verdict is REJECT and whose runner observation is REJECT.",
                "rejected": evidence.negative_control_total > 0
                and evidence.negative_control_total == evidence.negative_control_rejected_total,
                "scope": "formal_replay_audit_only",
            },
            {
                "control_id": "OC133-MATH-FINITE-PROOF-MODEL-BINDING-CONTROL",
                "description": "Input and executed row model hashes, Lean refs, and derived passed flags must remain bound for every counted case.",
                "rejected": not evidence.corpus_failures and all(row.valid for row in evidence.cases),
                "scope": "formal_replay_audit_only",
            },
        ],
        "falsifiers": pack["formal_falsifiers"],
        "formal_theorem_ids": pack["theorem_ids"],
        "formal_proof_sheet_refs": pack["proof_sheet_refs"],
        "formal_lean_refs": pack["lean_refs"],
        "formal_finite_case_ids": pack["finite_case_ids"],
        "formal_obligations": pack["formal_obligations"],
        "formal_audit_failures": formal_audit["failures"],
        "corpus_failures": evidence.corpus_failures,
        "grand_gate_failures": gate_failures,
        "tamper_test_total": len(tamper_tests),
        "tamper_tests": tamper_tests,
        "case_total": len(evidence.cases),
        "valid_case_total": evidence.eligible_n,
        "case_rows": case_rows_for_report(evidence),
        "valid_under_executor": valid_under_executor and evidence.valid_under_executor,
        "valid_under_current_grand_schema": False,
        "valid_under_grand_gate": False,
        "empirical_gate_rejects_formal_pack": "FORMAL_SUPPORT_ROUTE_NOT_EMPIRICAL_GRAND_EVIDENCE" in gate_failures,
        "blockers": ordered_unique([*blockers, *formal_blockers]),
    }
    return DomainCandidate(domain=DOMAIN, pack_ref=pack_ref, pack=pack, report_row=report_row)


def protocol_steps(min_n: int) -> list[str]:
    return [
        "join pre-execution finite-model input rows to executed proof-corpus rows by case_id",
        "exclude rows whose raw model facts, Lean refs, expected verdicts, observed verdicts, or derived passed flags are not bound",
        "bind every formal theorem to exact theorem ID, proof sheet ref, Lean ref, finite positive case, finite negative case, and public claim boundary",
        f"require at least {min_n} eligible machine-checkable finite cases for the formal route",
        "emit a separate formal_support_verdict and keep empirical_support_allowed false",
        "retain negative-control rows, target-leakage checks, tamper checks, and formal falsifier conditions even when a candidate fails",
    ]


def build_protocol_payload(candidate: DomainCandidate) -> dict[str, Any]:
    row = candidate.report_row
    protocol = {
        "schema_id": PROTOCOL_PACKET_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "executor": EXECUTOR_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "formal_evidence_schema_id": FORMAL_EVIDENCE_SCHEMA_ID,
        "target_blind_ref": TARGET_BLIND_REL,
        "domain_total": 1,
        "blocked_domain_total": 0 if row["valid_under_executor"] else 1,
        "rows": [
            {
                "domain": DOMAIN,
                "status": row["status"],
                "candidate_pack_ref": candidate.pack_ref,
                "candidate_n": row["candidate_n"],
                "minimum_n": row["minimum_n"],
                "missing_n": row["missing_n"],
                "support_route": row["support_route"],
                "formal_support_verdict": row["formal_support_verdict"],
                "formal_support_allowed": row["formal_support_allowed"],
                "empirical_support_allowed": row["empirical_support_allowed"],
                "grand_toe_support_allowed": row["grand_toe_support_allowed"],
                "source_kind": row["source_assessment"]["source_kind"],
                "grand_empirical_source": row["source_assessment"]["grand_empirical_source"],
                "blockers": row["blockers"],
                "required_protocol_steps": protocol_steps(int(row["minimum_n"])),
            }
        ],
        "registry_integration_policy": "The generated mathematics pack is a formal-support artifact, not a grand empirical evidence pack; grand empirical registry sync must reject it for empirical support.",
    }
    protocol["protocol_sha256"] = sha256_object({key: value for key, value in protocol.items() if key != "protocol_sha256"})
    return protocol


def build_execution_payload(
    root: Path,
    snapshot_ref: str = DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> tuple[dict[str, Any], DomainCandidate, dict[str, Any]]:
    candidate = build_domain_candidate(root, snapshot_ref=snapshot_ref, output_root_rel=output_root_rel)
    protocol = build_protocol_payload(candidate)
    report_ref = f"{output_root_rel}/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json"
    protocol_ref = f"{output_root_rel}/OC133_MATHEMATICS_EVIDENCE_PROTOCOL.json"
    valid = candidate.report_row["formal_support_allowed"] and candidate.report_row["valid_under_executor"]
    report = {
        "schema_id": EXECUTION_REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "executor": EXECUTOR_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "formal_evidence_schema_id": FORMAL_EVIDENCE_SCHEMA_ID,
        "grand_factory_ref": "validation/grand_science/evidence_pack_factory.py",
        "output_root_ref": output_root_rel,
        "report_ref": report_ref,
        "protocol_ref": protocol_ref,
        "candidate_pack_refs": [candidate.pack_ref],
        "candidate_pack_total": 1,
        "valid_under_current_grand_schema_total": 1 if candidate.report_row["valid_under_current_grand_schema"] else 0,
        "valid_under_grand_gate_total": 1 if candidate.report_row["valid_under_grand_gate"] else 0,
        "formal_support_allowed_total": 1 if candidate.report_row["formal_support_allowed"] else 0,
        "valid_under_executor_total": 1 if candidate.report_row["valid_under_executor"] else 0,
        "valid_pack_total": 1 if valid else 0,
        "blocked_pack_total": 0 if valid else 1,
        "blocked_domain_total": 0 if valid else 1,
        "protocol_sha256": protocol["protocol_sha256"],
        "domains": [candidate.report_row],
        "verdict": "MATHEMATICS_FORMAL_SUPPORT_ROUTE_READY" if valid else "BLOCKED_PENDING_MATHEMATICS_FORMAL_EVIDENCE",
        "empirical_grand_gate_verdict": "REJECTED_FORMAL_ONLY_NOT_EMPIRICAL",
        "no_fabricated_success_policy": "Rows are counted only for formal support when the executor can rederive them from raw finite-model/proof artifacts and bind theorem IDs, proof sheets, Lean refs, finite cases, and claim boundaries.",
        "route_separation_policy": "Formal mathematics support is audited separately from grand empirical support; the empirical grand gate must not count this corpus as empirical evidence.",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    return report, candidate, protocol


def render_readme(report: dict[str, Any]) -> str:
    row = report["domains"][0]
    lines = [
        "# Mathematics Formal Support Capability",
        "",
        "This directory is generated by `validation/heldout/domain_evidence/mathematics_evidence_executor.py`.",
        "",
        "The candidate pack is derived from joined finite-model input rows and executed proof-corpus rows. N counts eligible theorem-case executions for formal support only, not empirical grand-science evidence.",
        "",
        "| Domain | Candidate pack | Formal support | Empirical support | N | Minimum N | Status |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
        "| `{domain}` | `{pack}` | `{formal}` | `{empirical}` | `{n}` | `{minimum}` | `{status}` |".format(
            domain=row["domain"],
            pack=row["candidate_pack_ref"],
            formal=str(row["formal_support_allowed"]).lower(),
            empirical=str(row["empirical_support_allowed"]).lower(),
            n=row["candidate_n"],
            minimum=row["minimum_n"],
            status=row["status"],
        ),
        "",
        "Generated artifacts remain no-send. The formal route can support formal claims only; the grand empirical gate rejects this pack as formal-only.",
        "",
    ]
    return "\n".join(lines)


def build_all(
    root: Path | None = None,
    snapshot_ref: str = DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> dict[str, Any]:
    root = root or repo_root()
    report, candidate, protocol = build_execution_payload(root, snapshot_ref=snapshot_ref, output_root_rel=output_root_rel)
    return {
        candidate.pack_ref: candidate.pack,
        report["protocol_ref"]: protocol,
        report["report_ref"]: report,
        f"{output_root_rel}/README.md": render_readme(report),
    }


def write_outputs(
    root: Path | None = None,
    snapshot_ref: str = DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> dict[str, Any]:
    root = root or repo_root()
    payloads = build_all(root, snapshot_ref=snapshot_ref, output_root_rel=output_root_rel)
    for rel_path, payload in payloads.items():
        path = root / rel_path
        if isinstance(payload, str):
            write_text(path, payload)
        else:
            write_json(path, payload)
    return payloads[f"{output_root_rel}/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json"]


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    failures: list[str] = []
    for rel_path, payload in expected.items():
        path = root / rel_path
        if isinstance(payload, str):
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != payload:
                failures.append(f"{rel_path} is not synchronized with {EXECUTOR_REL}")
        else:
            if not path.exists():
                failures.append(f"{rel_path} is not synchronized with {EXECUTOR_REL}")
                continue
            actual = read_json(path)
            if actual != payload:
                failures.append(f"{rel_path} is not synchronized with {EXECUTOR_REL}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build mathematics finite-model/proof-corpus evidence pack.")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    parser.add_argument("--snapshot-ref", default=DEFAULT_SNAPSHOT_REF)
    parser.add_argument("--output-root-ref", default=OUTPUT_ROOT_REL)
    parser.add_argument("--write", action="store_true", help="write candidate pack and protocol artifacts")
    parser.add_argument("--check", action="store_true", help="check stored artifacts against deterministic output")
    parser.add_argument("--check-only", action="store_true", help="build report without writing artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even when the pack remains blocked")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print("mathematics evidence artifact check passed")
        return 0

    if args.write:
        report = write_outputs(root, snapshot_ref=args.snapshot_ref, output_root_rel=args.output_root_ref)
    else:
        report, _candidate, _protocol = build_execution_payload(
            root,
            snapshot_ref=args.snapshot_ref,
            output_root_rel=args.output_root_ref,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["blocked_pack_total"]:
        return 0 if args.allow_blocked_exit_zero else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
