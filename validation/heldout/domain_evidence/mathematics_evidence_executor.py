from __future__ import annotations

import argparse
import copy
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
CAPABILITY_OWNER = "Research/EmpiricalScience"
BLOCKER_ID = "grand_toe_empirical_superiority"

EVIDENCE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
EXECUTION_REPORT_SCHEMA_ID = "OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT_v1"
PROTOCOL_PACKET_SCHEMA_ID = "OC133_MATHEMATICS_EVIDENCE_PROTOCOL_PACKET_v1"

EXECUTOR_REL = "validation/heldout/domain_evidence/mathematics_evidence_executor.py"
OUTPUT_ROOT_REL = "validation/heldout/grand_science/mathematics"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
DEFAULT_SNAPSHOT_REF = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"

DOMAIN = "mathematics"
MINIMUM_N = 20
CURRENT_CANDIDATE_N = 1
HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
OBJECT_HASH_POLICY = "sha256 over sorted canonical JSON"
TARGET_BLIND_ROW_HASH_POLICY = "sha256 over sorted JSON row before replay_hash insertion"


@dataclass(frozen=True)
class MathematicsEvidence:
    snapshot_ref: str
    snapshot_payload: dict[str, Any]
    snapshot_sha256: str
    snapshot_byte_count: int
    snapshot_canonical_sha256: str
    target_blind_row: dict[str, Any] | None
    target_blind_row_sha256: str | None
    accepted_theorem_ids: list[str]
    predicted_value: float
    observed_value: float
    comparator_prediction: float
    uncertainty: float
    model_residual: float
    comparator_residual: float
    source_separation: dict[str, Any]
    binding_failures: list[str]

    @property
    def superiority_margin(self) -> float:
        return self.comparator_residual - self.model_residual


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


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def as_float(value: Any, default: float = 0.0) -> float:
    if is_number(value):
        return float(value)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def close_enough(left: float, right: float) -> bool:
    scale = max(abs(left), abs(right), 1.0)
    return abs(left - right) <= scale * 1e-12


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


def target_blind_math_row(root: Path) -> dict[str, Any] | None:
    path = root / TARGET_BLIND_REL
    if not path.exists():
        return None
    payload = read_json(path)
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and row.get("lane") == DOMAIN:
            return row
    return None


def row_hash(row: dict[str, Any]) -> str:
    stripped = {key: value for key, value in row.items() if key not in {"replay_hash", "replay_hash_policy"}}
    return hashlib.sha256(json.dumps(stripped, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def accepted_theorem_ids(payload: dict[str, Any]) -> list[str]:
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return []
    theorem_ids = {
        str(row.get("theorem_id"))
        for row in rows
        if isinstance(row, dict)
        and row.get("case_type") == "theorem_case"
        and row.get("observed_verdict") == "ACCEPT"
        and row.get("passed") is True
        and str(row.get("theorem_id") or "").strip()
    }
    return sorted(theorem_ids)


def proof_corpus_metrics(payload: dict[str, Any], theorem_ids: list[str]) -> dict[str, Any]:
    rows = payload.get("rows", [])
    row_total = len(rows) if isinstance(rows, list) else 0
    return {
        "finite_case_total": int(payload.get("case_total", row_total) or row_total),
        "proof_corpus_row_total": row_total,
        "positive_case_total": int(payload.get("positive_case_total", 0) or 0),
        "machine_checked_subset_total": int(payload.get("machine_checked_subset_total", len(theorem_ids)) or 0),
        "unique_accepted_theorem_total": len(theorem_ids),
        "lean_theorem_ref_total": int(payload.get("lean_theorem_ref_total", 0) or 0),
        "lean_build_returncode": payload.get("lean_build_returncode"),
        "live_lean_build_returncode": payload.get("live_lean_build_returncode"),
        "lean_source_ref": payload.get("lean_source_ref"),
        "current_lean_source_sha256": payload.get("current_lean_source_sha256"),
        "certificate_lean_source_sha256": payload.get("certificate_lean_source_sha256"),
    }


def source_separation_from_row(snapshot_ref: str, row: dict[str, Any] | None) -> dict[str, Any]:
    split = str((row or {}).get("target_blind_split") or "")
    split_lower = split.lower()
    target_hidden = "withheld" in split_lower and "until scoring" in split_lower
    return {
        "mode": "target_blind",
        "pre_target_lock": row is not None and bool(snapshot_ref and split),
        "target_hidden_until_scoring": row is not None and target_hidden,
        "training_sources": [
            f"{snapshot_ref}::finite_theorem_case_rows(case_type,observed_verdict,passed,theorem_id)"
        ],
        "target_sources": [
            f"{snapshot_ref}::machine_checked_subset_total"
        ],
    }


def validate_target_blind_binding(
    root: Path,
    row: dict[str, Any] | None,
    snapshot_ref: str,
    predicted: float,
    observed: float,
    comparator_prediction: float,
    model_residual: float,
    comparator_residual: float,
) -> list[str]:
    failures: list[str] = []
    if row is None:
        return ["TARGET_BLIND_MATHEMATICS_ROW_MISSING"]

    if row.get("dataset_snapshot_ref") != snapshot_ref:
        failures.append("TARGET_BLIND_SNAPSHOT_REF_MISMATCH")
    actual_snapshot = resolve_under_root(root, snapshot_ref)
    if row.get("snapshot_sha256") != sha256_lf_normalized_text(actual_snapshot):
        failures.append("TARGET_BLIND_SNAPSHOT_SHA256_MISMATCH")
    if row.get("snapshot_sha256_policy") != HASH_POLICY:
        failures.append("TARGET_BLIND_SNAPSHOT_HASH_POLICY_MISMATCH")
    if row.get("negative_control_rejected") is not True:
        failures.append("TARGET_BLIND_NEGATIVE_CONTROL_NOT_REJECTED")
    if not close_enough(as_float(row.get("predicted_value")), predicted):
        failures.append("TARGET_BLIND_PREDICTED_VALUE_MISMATCH")
    if not close_enough(as_float(row.get("observed_value")), observed):
        failures.append("TARGET_BLIND_OBSERVED_VALUE_MISMATCH")
    if not close_enough(as_float(row.get("comparator_prediction")), comparator_prediction):
        failures.append("TARGET_BLIND_COMPARATOR_PREDICTION_MISMATCH")
    if not close_enough(as_float(row.get("residual")), model_residual):
        failures.append("TARGET_BLIND_MODEL_RESIDUAL_MISMATCH")
    if not close_enough(as_float(row.get("comparator_residual")), comparator_residual):
        failures.append("TARGET_BLIND_COMPARATOR_RESIDUAL_MISMATCH")
    if row.get("replay_hash") and row_hash(row) != row.get("replay_hash"):
        failures.append("TARGET_BLIND_ROW_REPLAY_HASH_MISMATCH")
    return ordered_unique(failures)


def load_mathematics_evidence(root: Path, snapshot_ref: str = DEFAULT_SNAPSHOT_REF) -> MathematicsEvidence:
    snapshot_path = resolve_under_root(root, snapshot_ref)
    payload = read_json(snapshot_path)
    if not isinstance(payload, dict):
        raise ValueError("mathematics proof corpus snapshot must be a JSON object")

    row = target_blind_math_row(root)
    theorem_ids = accepted_theorem_ids(payload)
    metrics = proof_corpus_metrics(payload, theorem_ids)
    predicted = float(len(theorem_ids))
    observed = float(metrics["machine_checked_subset_total"])
    comparator_prediction = float(metrics["positive_case_total"])
    uncertainty = as_float((row or {}).get("uncertainty"), 0.0)
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator_prediction - observed)
    binding_failures = validate_target_blind_binding(
        root,
        row,
        snapshot_ref,
        predicted,
        observed,
        comparator_prediction,
        model_residual,
        comparator_residual,
    )
    return MathematicsEvidence(
        snapshot_ref=snapshot_ref,
        snapshot_payload=payload,
        snapshot_sha256=sha256_lf_normalized_text(snapshot_path),
        snapshot_byte_count=len(lf_normalized_bytes(snapshot_path)),
        snapshot_canonical_sha256=sha256_object(payload),
        target_blind_row=row,
        target_blind_row_sha256=row_hash(row) if row is not None else None,
        accepted_theorem_ids=theorem_ids,
        predicted_value=predicted,
        observed_value=observed,
        comparator_prediction=comparator_prediction,
        uncertainty=uncertainty,
        model_residual=model_residual,
        comparator_residual=comparator_residual,
        source_separation=source_separation_from_row(snapshot_ref, row),
        binding_failures=binding_failures,
    )


def validate_negative_control(predicted: float, observed: float, comparator_prediction: float) -> list[str]:
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator_prediction - observed)
    failures: list[str] = []
    if comparator_residual <= model_residual:
        failures.append("COMPARATOR_NOT_WORSE_THAN_MODEL")
    if comparator_residual <= 0:
        failures.append("NEGATIVE_CONTROL_HAS_ZERO_RESIDUAL")
    return failures


def tampered_machine_checked_payload(evidence: MathematicsEvidence) -> dict[str, Any]:
    mutated = copy.deepcopy(evidence.snapshot_payload)
    current = int(mutated.get("machine_checked_subset_total", 0) or 0)
    mutated["machine_checked_subset_total"] = current + 1
    return mutated


def run_tamper_tests(evidence: MathematicsEvidence) -> list[dict[str, Any]]:
    mutated_snapshot = tampered_machine_checked_payload(evidence)
    mutated_metrics = proof_corpus_metrics(mutated_snapshot, evidence.accepted_theorem_ids)
    mutated_observed = float(mutated_metrics["machine_checked_subset_total"])
    mutated_model_residual = abs(evidence.predicted_value - mutated_observed)

    tests: list[dict[str, Any]] = [
        {
            "test_id": "mathematics-proof-corpus-aggregate-tamper-hash-changes",
            "description": "mutating machine_checked_subset_total must change the canonical proof-corpus hash",
            "passed": sha256_object(mutated_snapshot) != evidence.snapshot_canonical_sha256,
        },
        {
            "test_id": "mathematics-proof-corpus-aggregate-tamper-replay-detected",
            "description": "mutating the target aggregate must change the replayed model residual",
            "passed": not close_enough(mutated_model_residual, evidence.model_residual),
            "original_model_residual": evidence.model_residual,
            "mutated_model_residual": mutated_model_residual,
        },
        {
            "test_id": "mathematics-positive-case-negative-control-residual-test",
            "description": "positive_case_total control must have larger residual than the theorem-case aggregate",
            "passed": not validate_negative_control(
                evidence.predicted_value,
                evidence.observed_value,
                evidence.comparator_prediction,
            ),
            "model_residual": evidence.model_residual,
            "comparator_residual": evidence.comparator_residual,
        },
        {
            "test_id": "mathematics-negative-control-mutation-rejected",
            "description": "replacing the comparator with the model prediction must fail negative-control validation",
            "passed": "COMPARATOR_NOT_WORSE_THAN_MODEL"
            in validate_negative_control(evidence.predicted_value, evidence.observed_value, evidence.predicted_value),
            "expected_rejection": "COMPARATOR_NOT_WORSE_THAN_MODEL",
        },
    ]
    if evidence.target_blind_row is not None:
        mutated_row = dict(evidence.target_blind_row)
        mutated_row["observed_value"] = evidence.observed_value + 1.0
        tests.append(
            {
                "test_id": "mathematics-target-blind-row-tamper-hash-changes",
                "description": "mutating a target-blind row value must change the deterministic row hash",
                "passed": row_hash(mutated_row) != evidence.target_blind_row_sha256,
            }
        )
    return tests


def source_assessment(evidence: MathematicsEvidence) -> dict[str, Any]:
    metrics = proof_corpus_metrics(evidence.snapshot_payload, evidence.accepted_theorem_ids)
    return {
        "source_kind": "finite_lean_proof_corpus",
        "grand_empirical_source": False,
        "scope_statement": "source is finite/Lean proof corpus, not empirical grand evidence",
        "candidate_n_policy": "current N is one bounded aggregate replay; Lean theorem counts are not empirical observation N",
        "machine_checked_subset_total": metrics["machine_checked_subset_total"],
        "unique_accepted_theorem_total": metrics["unique_accepted_theorem_total"],
        "positive_case_total": metrics["positive_case_total"],
        "lean_theorem_ref_total": metrics["lean_theorem_ref_total"],
        "lean_source_ref": metrics["lean_source_ref"],
        "current_lean_source_sha256": metrics["current_lean_source_sha256"],
        "certificate_lean_source_sha256": metrics["certificate_lean_source_sha256"],
    }


def build_candidate_pack(evidence: MathematicsEvidence) -> dict[str, Any]:
    row = evidence.target_blind_row or {}
    return {
        "schema_id": EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-GRAND-MATHEMATICS-CANDIDATE",
        "domain": DOMAIN,
        "source_separation": evidence.source_separation,
        "n": CURRENT_CANDIDATE_N,
        "model_under_test": str(
            row.get("formula")
            or "count_unique(theorem_id where case_type='theorem_case' and observed_verdict='ACCEPT' and passed=true)"
        ),
        "comparator_baseline": {
            "name": str(row.get("comparator_baseline") or "positive_case_total proof-corpus negative control"),
            "prediction_rule": "Use proof-corpus positive_case_total against the same machine_checked_subset_total aggregate.",
            "pre_registered": row is not None,
        },
        "uncertainty": {
            "metric": "absolute residual over one finite proof-corpus aggregate",
            "method": "deterministic replay of the pinned Lean/finite-model proof corpus aggregate",
            "interval": [
                0.0,
                max(evidence.uncertainty, evidence.model_residual),
            ],
        },
        "residuals": {
            "model": evidence.model_residual,
            "comparator": evidence.comparator_residual,
            "superiority_margin": evidence.superiority_margin,
        },
        "negative_controls": [
            {
                "control_id": "OC133-TARGETBLIND-MATHEMATICS-001-POSITIVE-CASE-TOTAL-CONTROL",
                "description": str(
                    row.get("negative_control")
                    or "replace theorem-id aggregate by positive_case_total and require a larger residual"
                ),
                "rejected": evidence.comparator_residual > evidence.model_residual,
            }
        ],
        "falsifiers": [
            str(
                row.get("falsifier")
                or "Unique accepted theorem-case count differs from machine_checked_subset_total or broad positive-case control is not worse"
            )
        ],
        "grand_toe_support_allowed": False,
    }


def current_blockers(evidence: MathematicsEvidence, min_n: int, gate_failures: list[str]) -> list[str]:
    blockers = [
        "MATHEMATICS_CURRENT_SOURCE_IS_FINITE_LEAN_PROOF_CORPUS_NOT_EMPIRICAL_GRAND_EVIDENCE",
        f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{CURRENT_CANDIDATE_N}/{min_n}",
        "GRAND_TOE_SUPPORT_FORCED_FALSE_FOR_CURRENT_MATHEMATICS_EVIDENCE",
    ]
    if evidence.binding_failures:
        blockers.extend(f"TARGET_BLIND_BINDING::{failure}" for failure in evidence.binding_failures)
    blockers.extend(f"GRAND_GATE::{failure}" for failure in gate_failures)
    return ordered_unique(blockers)


def build_domain_candidate(
    root: Path,
    snapshot_ref: str = DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> DomainCandidate:
    min_n = minimum_n(root)
    requirements = load_requirements(root)
    evidence = load_mathematics_evidence(root, snapshot_ref)
    pack = build_candidate_pack(evidence)
    gate_failures = grand_factory.pack_failure_reasons(pack, requirements)
    tamper_tests = run_tamper_tests(evidence)
    tamper_failures = [f"TAMPER_TEST_FAILED::{row['test_id']}" for row in tamper_tests if row.get("passed") is not True]
    blockers = current_blockers(evidence, min_n, gate_failures + tamper_failures)
    pack_ref = f"{output_root_rel}/mathematics_candidate_evidence_pack.json"
    report_row = {
        "domain": DOMAIN,
        "status": "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
        "candidate_pack_ref": pack_ref,
        "candidate_pack_sha256": sha256_object(pack),
        "candidate_pack_hash_policy": OBJECT_HASH_POLICY,
        "snapshot_ref": evidence.snapshot_ref,
        "snapshot_sha256": evidence.snapshot_sha256,
        "snapshot_sha256_policy": HASH_POLICY,
        "snapshot_byte_count": evidence.snapshot_byte_count,
        "snapshot_canonical_sha256": evidence.snapshot_canonical_sha256,
        "snapshot_canonical_hash_policy": OBJECT_HASH_POLICY,
        "target_blind_ref": TARGET_BLIND_REL,
        "target_blind_row_sha256": evidence.target_blind_row_sha256,
        "target_blind_row_hash_policy": TARGET_BLIND_ROW_HASH_POLICY,
        "source_assessment": source_assessment(evidence),
        "source_separation": evidence.source_separation,
        "candidate_n": CURRENT_CANDIDATE_N,
        "minimum_n": min_n,
        "missing_n": max(0, min_n - CURRENT_CANDIDATE_N),
        "grand_toe_support_allowed": False,
        "residuals": pack["residuals"],
        "negative_controls": pack["negative_controls"],
        "falsifiers": pack["falsifiers"],
        "binding_failures": evidence.binding_failures,
        "grand_gate_failures": gate_failures,
        "tamper_test_total": len(tamper_tests),
        "tamper_tests": tamper_tests,
        "valid_under_executor": False,
        "valid_under_current_grand_schema": False,
        "valid_under_grand_gate": False,
        "blockers": blockers,
    }
    return DomainCandidate(domain=DOMAIN, pack_ref=pack_ref, pack=pack, report_row=report_row)


def protocol_steps(min_n: int) -> list[str]:
    return [
        "do not count finite Lean proof-corpus rows as empirical grand evidence",
        "pre-register a mathematics-facing empirical or target-blind protocol before target scoring",
        "separate training/development material from target material and record deterministic source hashes",
        f"collect at least {min_n} independent eligible observations under that protocol",
        "score OC and comparator residuals under the same deterministic metric",
        "retain negative controls, falsifiers, tamper checks, and explicit grand_toe_support_allowed=false until all gates pass",
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
        "target_blind_ref": TARGET_BLIND_REL,
        "domain_total": 1,
        "blocked_domain_total": 1,
        "rows": [
            {
                "domain": DOMAIN,
                "status": "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
                "candidate_pack_ref": candidate.pack_ref,
                "candidate_n": row["candidate_n"],
                "minimum_n": row["minimum_n"],
                "missing_n": row["missing_n"],
                "grand_toe_support_allowed": False,
                "source_kind": row["source_assessment"]["source_kind"],
                "grand_empirical_source": row["source_assessment"]["grand_empirical_source"],
                "blockers": row["blockers"],
                "required_protocol_steps": protocol_steps(int(row["minimum_n"])),
            }
        ],
        "registry_integration_policy": "This executor does not edit validation/heldout/grand_science_evidence_registry.json; current mathematics output remains a blocked candidate only.",
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
    report = {
        "schema_id": EXECUTION_REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "executor": EXECUTOR_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "grand_factory_ref": "validation/grand_science/evidence_pack_factory.py",
        "output_root_ref": output_root_rel,
        "report_ref": report_ref,
        "protocol_ref": protocol_ref,
        "candidate_pack_refs": [candidate.pack_ref],
        "candidate_pack_total": 1,
        "valid_under_current_grand_schema_total": 0,
        "valid_under_grand_gate_total": 0,
        "valid_under_executor_total": 0,
        "valid_pack_total": 0,
        "blocked_pack_total": 1,
        "blocked_domain_total": 1,
        "protocol_sha256": protocol["protocol_sha256"],
        "domains": [candidate.report_row],
        "verdict": "BLOCKED_PENDING_GENUINE_MATHEMATICS_EVIDENCE",
        "no_fabricated_success_policy": "Current mathematics evidence is a finite Lean/proof-corpus aggregate. It is deterministic and useful for bounded formal QA, but it is not empirical grand evidence and cannot set grand_toe_support_allowed=true.",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    return report, candidate, protocol


def render_readme(report: dict[str, Any]) -> str:
    row = report["domains"][0]
    lines = [
        "# Mathematics Grand Evidence Capability",
        "",
        "This directory is generated by `validation/heldout/domain_evidence/mathematics_evidence_executor.py`.",
        "",
        "Current mathematics evidence is kept blocked: it is a finite Lean/proof-corpus aggregate, not empirical grand evidence.",
        "",
        "| Domain | Candidate pack | Grand TOE support | N | Minimum N | Status |",
        "| --- | --- | --- | ---: | ---: | --- |",
        "| `{domain}` | `{pack}` | `{support}` | `{n}` | `{minimum}` | `{status}` |".format(
            domain=row["domain"],
            pack=row["candidate_pack_ref"],
            support=str(row["grand_toe_support_allowed"]).lower(),
            n=row["candidate_n"],
            minimum=row["minimum_n"],
            status=row["status"],
        ),
        "",
        "Do not register this pack as release evidence while the protocol status is blocked.",
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
    parser = argparse.ArgumentParser(description="Build mathematics grand empirical candidate evidence pack.")
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
