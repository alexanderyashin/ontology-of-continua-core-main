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

EXECUTOR_REL = "validation/heldout/domain_evidence/biology_systems_evidence_executor.py"
OUTPUT_ROOT_REL = "validation/heldout/grand_science/biology_systems"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
PROTOCOL_SCHEMA_REL = "validation/grand_science/grand_empirical_protocol.schema.json"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"

BIOLOGY_DEFAULT_SNAPSHOT_REF = "validation/_raw/biology_ncbi_geo_platform.txt"
SYSTEMS_DEFAULT_SNAPSHOT_REF = "validation/_raw/systems_world_bank_gdp.txt"

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
EVIDENCE_OWNER = "Research/EmpiricalScience"
BLOCKER_ID = "grand_toe_empirical_superiority"
EVIDENCE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
EXECUTION_REPORT_SCHEMA_ID = "OC133_BIOLOGY_SYSTEMS_EVIDENCE_EXECUTION_REPORT_v1"
PROTOCOL_PACKET_SCHEMA_ID = "OC133_BIOLOGY_SYSTEMS_EVIDENCE_PROTOCOL_PACKET_v1"
OFFICIAL_SNAPSHOT_BUNDLE_SCHEMA_ID = "OC133_BIOLOGY_SYSTEMS_OFFICIAL_SNAPSHOT_BUNDLE_v1"

SUPPORTED_DOMAINS = ("biology", "systems")
MINIMUM_N = 20
ALLOWED_SOURCE_MODES = ("target_blind", "prospective")
PACK_FIELDS = (
    "schema_id",
    "release_id",
    "evidence_owner",
    "evidence_pack_id",
    "domain",
    "source_separation",
    "n",
    "model_under_test",
    "comparator_baseline",
    "uncertainty",
    "residuals",
    "negative_controls",
    "falsifiers",
    "grand_toe_support_allowed",
)
OPTIONAL_PACK_FIELDS = (
    "biological_target_rows",
    "source_hashes",
    "evidence_family",
    "pack_version",
    "source_contract",
)


@dataclass(frozen=True)
class Observation:
    observation_id: str
    domain: str
    training_source: str
    target_source: str
    formula: str
    predicted_value: float
    observed_value: float
    comparator_prediction: float
    uncertainty: float
    negative_control_id: str
    negative_control_description: str
    falsifier: str

    @property
    def model_residual(self) -> float:
        return abs(self.predicted_value - self.observed_value)

    @property
    def comparator_residual(self) -> float:
        return abs(self.comparator_prediction - self.observed_value)


@dataclass(frozen=True)
class SnapshotEvidence:
    domain: str
    snapshot_ref: str
    snapshot_kind: str
    snapshot_sha256: str
    snapshot_byte_count: int
    source_separation: dict[str, Any]
    model_under_test: str
    comparator_baseline: dict[str, Any]
    uncertainty_metric: str
    uncertainty_method: str
    observations: list[Observation]
    intrinsic_blockers: list[str]
    protocol_notes: list[str]


@dataclass(frozen=True)
class DomainCandidate:
    domain: str
    pack_ref: str
    pack: dict[str, Any]
    report_row: dict[str, Any]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


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


def as_float(value: Any, field: str) -> float:
    if not is_number(value):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


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
        "minimum_per_domain_n": MINIMUM_N,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": list(ALLOWED_SOURCE_MODES),
    }


def load_requirements(root: Path) -> dict[str, Any]:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return default_requirements()
    return read_json(path)


def parse_biology_current_snapshot(root: Path, snapshot_ref: str) -> SnapshotEvidence:
    path = resolve_under_root(root, snapshot_ref)
    payload = read_json(path)
    result = payload["esearchresult"]
    id_count = len(result["idlist"])
    retstart = int(result["retstart"])
    observed = float(result["retmax"])
    predicted = float(retstart + id_count)
    comparator = float(result["count"])
    observation = Observation(
        observation_id="BIOLOGY-GEO-GPL96-PAGE-0000",
        domain="biology",
        training_source=f"{snapshot_ref}::visible_fields(retstart,idlist)",
        target_source=f"{snapshot_ref}::withheld_field(retmax)",
        formula="retstart + len(idlist)",
        predicted_value=predicted,
        observed_value=observed,
        comparator_prediction=comparator,
        uncertainty=0.0,
        negative_control_id="biology-total-hit-count-control",
        negative_control_description="replace page-size reconstruction by total GEO hit count and require larger residual",
        falsifier="retmax differs from retstart plus returned id count or total-count control is not worse",
    )
    return SnapshotEvidence(
        domain="biology",
        snapshot_ref=snapshot_ref,
        snapshot_kind="current_bounded_ncbi_geo_esearch_snapshot",
        snapshot_sha256=sha256_lf_normalized_text(path),
        snapshot_byte_count=len(lf_normalized_bytes(path)),
        source_separation={
            "mode": "target_blind",
            "pre_target_lock": False,
            "target_hidden_until_scoring": False,
            "training_sources": [observation.training_source],
            "target_sources": [observation.target_source],
        },
        model_under_test="retstart + len(idlist)",
        comparator_baseline={
            "name": "GEO total hit count pagination negative control",
            "prediction_rule": "use esearchresult.count as the retmax prediction",
            "pre_registered": False,
        },
        uncertainty_metric="mean absolute residual",
        uncertainty_method="deterministic exact parser replay over pinned NCBI GEO ESearch snapshot",
        observations=[observation],
        intrinsic_blockers=[
            "BIOLOGY_CURRENT_SNAPSHOT_IS_API_PAGINATION_QA_NOT_MECHANISM_EVIDENCE",
            "SOURCE_SEPARATION_NOT_VERIFIABLE_FROM_CURRENT_SINGLE_RAW_SNAPSHOT",
            "TARGET_VALUES_VISIBLE_IN_PINNED_RAW_SNAPSHOT",
        ],
        protocol_notes=[
            "Current GEO snapshot provides one bounded pagination reconstruction, not 20 independent biology mechanism targets.",
            "A valid future biology pack must freeze a pre-target model/comparator and score at least 20 target-hidden or prospective biology observations.",
        ],
    )


def parse_systems_current_snapshot(root: Path, snapshot_ref: str) -> SnapshotEvidence:
    path = resolve_under_root(root, snapshot_ref)
    payload = read_json(path)
    rows = payload[1]
    values = {
        int(row["date"]): float(row["value"])
        for row in rows
        if row.get("value") is not None
    }
    predicted = values[2023] + (values[2023] - values[2021]) / 2.0
    observed = values[2024]
    comparator = values[2023]
    uncertainty = observed * 0.01
    observation = Observation(
        observation_id="SYSTEMS-WDI-WORLD-GDP-2024",
        domain="systems",
        training_source=f"{snapshot_ref}::training_years(2021,2022,2023)",
        target_source=f"{snapshot_ref}::target_year(2024)",
        formula="GDP_2023 + (GDP_2023-GDP_2021)/2",
        predicted_value=predicted,
        observed_value=observed,
        comparator_prediction=comparator,
        uncertainty=uncertainty,
        negative_control_id="systems-last-observation-control",
        negative_control_description="last-observation GDP_2023 baseline must have larger residual than the slope rule",
        falsifier="held-out residual exceeds 1 percent of observed target or comparator is not worse",
    )
    return SnapshotEvidence(
        domain="systems",
        snapshot_ref=snapshot_ref,
        snapshot_kind="current_bounded_world_bank_wdi_snapshot",
        snapshot_sha256=sha256_lf_normalized_text(path),
        snapshot_byte_count=len(lf_normalized_bytes(path)),
        source_separation={
            "mode": "target_blind",
            "pre_target_lock": False,
            "target_hidden_until_scoring": False,
            "training_sources": [observation.training_source],
            "target_sources": [observation.target_source],
        },
        model_under_test="GDP_2023 + (GDP_2023-GDP_2021)/2",
        comparator_baseline={
            "name": "World GDP last-observation carry-forward",
            "prediction_rule": "use GDP_2023 as the GDP_2024 prediction",
            "pre_registered": False,
        },
        uncertainty_metric="mean absolute residual",
        uncertainty_method="deterministic WDI target-blind replay with 1 percent target tolerance",
        observations=[observation],
        intrinsic_blockers=[
            "SYSTEMS_CURRENT_SNAPSHOT_IS_RETROSPECTIVE_MACRO_REPLAY_NOT_PROSPECTIVE_CIVILIZATIONAL_EVIDENCE",
            "SOURCE_SEPARATION_NOT_VERIFIABLE_FROM_CURRENT_SINGLE_RAW_SNAPSHOT",
            "TARGET_VALUES_VISIBLE_IN_PINNED_RAW_SNAPSHOT",
        ],
        protocol_notes=[
            "Current WDI snapshot yields one retrospective GDP holdout, not 20 independent systems/civilizational targets.",
            "A valid future systems pack must pre-register the target horizon and score at least 20 target-hidden or prospective observations.",
        ],
    )


def parse_official_snapshot_bundle(root: Path, snapshot_ref: str, domain: str, payload: dict[str, Any]) -> SnapshotEvidence:
    if payload.get("domain") != domain:
        raise ValueError(f"snapshot bundle domain mismatch: expected {domain}, found {payload.get('domain')}")
    observations: list[Observation] = []
    for idx, row in enumerate(payload.get("observations", [])):
        if not isinstance(row, dict):
            raise ValueError(f"observations[{idx}] must be an object")
        observations.append(
            Observation(
                observation_id=str(row.get("observation_id") or f"{domain.upper()}-OBS-{idx + 1:04d}"),
                domain=domain,
                training_source=str(row.get("training_source", "")),
                target_source=str(row.get("target_source", "")),
                formula=str(row.get("formula") or payload.get("model_under_test") or ""),
                predicted_value=as_float(row.get("predicted_value"), f"observations[{idx}].predicted_value"),
                observed_value=as_float(row.get("observed_value"), f"observations[{idx}].observed_value"),
                comparator_prediction=as_float(row.get("comparator_prediction"), f"observations[{idx}].comparator_prediction"),
                uncertainty=as_float(row.get("uncertainty", 0.0), f"observations[{idx}].uncertainty"),
                negative_control_id=str(row.get("negative_control_id") or "declared-negative-control"),
                negative_control_description=str(row.get("negative_control_description") or row.get("negative_control") or ""),
                falsifier=str(row.get("falsifier") or ""),
            )
        )
    if not observations:
        raise ValueError("snapshot bundle observations must not be empty")
    source = copy.deepcopy(payload.get("source_separation", {}))
    if "training_sources" not in source:
        source["training_sources"] = ordered_unique([row.training_source for row in observations])
    if "target_sources" not in source:
        source["target_sources"] = ordered_unique([row.target_source for row in observations])
    comparator = copy.deepcopy(payload.get("comparator_baseline", {}))
    return SnapshotEvidence(
        domain=domain,
        snapshot_ref=snapshot_ref,
        snapshot_kind=str(payload.get("snapshot_kind") or "official_snapshot_bundle"),
        snapshot_sha256=sha256_lf_normalized_text(resolve_under_root(root, snapshot_ref)),
        snapshot_byte_count=len(lf_normalized_bytes(resolve_under_root(root, snapshot_ref))),
        source_separation=source,
        model_under_test=str(payload.get("model_under_test") or observations[0].formula),
        comparator_baseline={
            "name": str(comparator.get("name", "")),
            "prediction_rule": str(comparator.get("prediction_rule", "")),
            "pre_registered": comparator.get("pre_registered") is True,
        },
        uncertainty_metric=str(payload.get("uncertainty_metric") or "mean absolute residual"),
        uncertainty_method=str(payload.get("uncertainty_method") or "deterministic aggregate interval from row uncertainty budget"),
        observations=observations,
        intrinsic_blockers=[str(item) for item in payload.get("intrinsic_blockers", []) if str(item).strip()],
        protocol_notes=[str(item) for item in payload.get("protocol_notes", []) if str(item).strip()],
    )


def load_snapshot_evidence(root: Path, domain: str, snapshot_ref: str) -> SnapshotEvidence:
    path = resolve_under_root(root, snapshot_ref)
    payload = read_json(path)
    if isinstance(payload, dict) and payload.get("schema_id") == OFFICIAL_SNAPSHOT_BUNDLE_SCHEMA_ID:
        return parse_official_snapshot_bundle(root, snapshot_ref, domain, payload)
    if domain == "biology":
        return parse_biology_current_snapshot(root, snapshot_ref)
    if domain == "systems":
        return parse_systems_current_snapshot(root, snapshot_ref)
    raise ValueError(f"unsupported domain: {domain}")


def validate_source_separation(source: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not isinstance(source, dict):
        return ["SOURCE_SEPARATION_NOT_OBJECT"]
    if source.get("mode") not in ALLOWED_SOURCE_MODES:
        failures.append("SOURCE_SEPARATION_MODE_NOT_ALLOWED")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    training_sources = source.get("training_sources")
    target_sources = source.get("target_sources")
    if not isinstance(training_sources, list) or not isinstance(target_sources, list):
        failures.append("TRAINING_AND_TARGET_SOURCES_MUST_BE_LISTS")
        return failures
    if not training_sources or not target_sources:
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    if not all(isinstance(item, str) and item.strip() for item in [*training_sources, *target_sources]):
        failures.append("TRAINING_AND_TARGET_SOURCES_MUST_BE_NONEMPTY_STRINGS")
    if len(set(training_sources)) != len(training_sources) or len(set(target_sources)) != len(target_sources):
        failures.append("TRAINING_OR_TARGET_SOURCE_DUPLICATE")
    if set(training_sources) & set(target_sources):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")
    return failures


def validate_observations(evidence: SnapshotEvidence, minimum_n: int) -> list[str]:
    failures = list(evidence.intrinsic_blockers)
    observations = evidence.observations
    if len(observations) < minimum_n:
        failures.append(f"N_BELOW_MINIMUM::{len(observations)}/{minimum_n}")
    if not evidence.model_under_test.strip():
        failures.append("MODEL_UNDER_TEST_MISSING")
    comparator = evidence.comparator_baseline
    if not comparator.get("name") or not comparator.get("prediction_rule"):
        failures.append("COMPARATOR_BASELINE_INCOMPLETE")
    if comparator.get("pre_registered") is not True:
        failures.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")
    for idx, row in enumerate(observations):
        row_prefix = f"OBSERVATION::{idx}::{row.observation_id}"
        if row.domain != evidence.domain:
            failures.append(f"{row_prefix}::DOMAIN_MISMATCH")
        if not row.training_source.strip() or not row.target_source.strip():
            failures.append(f"{row_prefix}::SOURCE_REF_MISSING")
        if row.training_source == row.target_source:
            failures.append(f"{row_prefix}::TRAINING_TARGET_SOURCE_OVERLAP")
        if not row.formula.strip():
            failures.append(f"{row_prefix}::FORMULA_MISSING")
        if not all(is_number(value) for value in (row.predicted_value, row.observed_value, row.comparator_prediction, row.uncertainty)):
            failures.append(f"{row_prefix}::NUMERIC_FIELD_INVALID")
        if row.uncertainty < 0:
            failures.append(f"{row_prefix}::UNCERTAINTY_NEGATIVE")
        if not row.negative_control_id.strip() or not row.negative_control_description.strip():
            failures.append(f"{row_prefix}::NEGATIVE_CONTROL_INCOMPLETE")
        if row.comparator_residual <= row.model_residual:
            failures.append(f"{row_prefix}::NEGATIVE_CONTROL_NOT_REJECTED")
        if not row.falsifier.strip():
            failures.append(f"{row_prefix}::FALSIFIER_MISSING")
    return ordered_unique(failures)


def residual_summary(observations: list[Observation]) -> dict[str, float]:
    model = mean([row.model_residual for row in observations])
    comparator = mean([row.comparator_residual for row in observations])
    return {
        "model": model,
        "comparator": comparator,
        "superiority_margin": comparator - model,
    }


def uncertainty_interval(evidence: SnapshotEvidence, model_residual: float) -> list[float]:
    budget = mean([max(0.0, row.uncertainty) for row in evidence.observations])
    lower = max(0.0, model_residual - budget)
    upper = model_residual + budget
    return [lower, upper]


def negative_control_rows(evidence: SnapshotEvidence) -> list[dict[str, Any]]:
    descriptions = ordered_unique(
        [
            f"{row.negative_control_id}: {row.negative_control_description}"
            for row in evidence.observations
        ]
    )
    rejected = all(row.comparator_residual > row.model_residual for row in evidence.observations)
    return [
        {
            "control_id": f"{evidence.domain}-aggregate-negative-control",
            "description": "; ".join(descriptions[:5])
            if len(descriptions) <= 5
            else f"{len(descriptions)} row-level negative controls require comparator residuals above model residuals",
            "rejected": rejected,
        }
    ]


def falsifier_rows(evidence: SnapshotEvidence) -> list[str]:
    falsifiers = ordered_unique([row.falsifier for row in evidence.observations if row.falsifier.strip()])
    if len(falsifiers) <= 5:
        return falsifiers
    return [
        f"{len(falsifiers)} row-level falsifiers are retained in the source snapshot; any model residual outside uncertainty or comparator non-inferiority falsifies the pack."
    ]


def build_candidate_pack(evidence: SnapshotEvidence, support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(evidence.observations)
    interval = uncertainty_interval(evidence, residuals["model"])
    pack = {
        "schema_id": EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "evidence_owner": EVIDENCE_OWNER,
        "evidence_pack_id": f"OC133-GRAND-BIOLOGY-SYSTEMS-{evidence.domain.upper()}-CANDIDATE",
        "domain": evidence.domain,
        "source_separation": evidence.source_separation,
        "n": len(evidence.observations),
        "model_under_test": evidence.model_under_test,
        "comparator_baseline": evidence.comparator_baseline,
        "uncertainty": {
            "metric": evidence.uncertainty_metric,
            "method": evidence.uncertainty_method,
            "interval": interval,
        },
        "residuals": residuals,
        "negative_controls": negative_control_rows(evidence),
        "falsifiers": falsifier_rows(evidence),
        "grand_toe_support_allowed": support_allowed,
    }
    if evidence.domain == "biology":
        pack.update(
            {
                "evidence_family": "biology-target-evidence",
                "pack_version": "1.0",
                "source_contract": "official_biology_target_bundle",
                "source_hashes": [
                    {
                        "source_ref": evidence.snapshot_ref,
                        "source_sha256": evidence.snapshot_sha256,
                        "hash_policy": "LF_NORMALIZED_TEXT_SNAPSHOT_HASH",
                    }
                ],
                "biological_target_rows": [
                    {
                        "biological_target_id": row.observation_id,
                        "biological_target_kind": "biological_response_target",
                        "source_ref": row.target_source or evidence.snapshot_ref,
                        "source_sha256": evidence.snapshot_sha256,
                        "prediction": row.predicted_value,
                        "observed": row.observed_value,
                        "comparator_prediction": row.comparator_prediction,
                        "model_residual": row.model_residual,
                        "comparator_residual": row.comparator_residual,
                    }
                    for row in evidence.observations
                ],
            }
        )
    return pack


def validate_grand_schema_shape(pack: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in PACK_FIELDS:
        if field not in pack:
            failures.append(f"MISSING_FIELD::{field}")
    allowed_fields = set(PACK_FIELDS) | set(OPTIONAL_PACK_FIELDS)
    for field in pack:
        if field not in allowed_fields:
            failures.append(f"ADDITIONAL_FIELD::{field}")
    if pack.get("schema_id") != EVIDENCE_SCHEMA_ID:
        failures.append("SCHEMA_ID_MISMATCH")
    if pack.get("release_id") != RELEASE_ID:
        failures.append("RELEASE_ID_MISMATCH")
    if pack.get("evidence_owner") != EVIDENCE_OWNER:
        failures.append("EVIDENCE_OWNER_MISMATCH")
    if pack.get("domain") not in {"biology", "chemistry", "mathematics", "physics", "systems"}:
        failures.append("DOMAIN_ENUM_MISMATCH")
    n = pack.get("n")
    if not isinstance(n, int) or isinstance(n, bool):
        failures.append("N_NOT_INTEGER")
    elif n < MINIMUM_N:
        failures.append(f"N_BELOW_MINIMUM::{MINIMUM_N}")
    source = pack.get("source_separation")
    if not isinstance(source, dict):
        failures.append("SOURCE_SEPARATION_NOT_OBJECT")
    else:
        source_fields = {"mode", "pre_target_lock", "target_hidden_until_scoring", "training_sources", "target_sources"}
        for field in source_fields:
            if field not in source:
                failures.append(f"SOURCE_SEPARATION_MISSING_FIELD::{field}")
        for field in source:
            if field not in source_fields:
                failures.append(f"SOURCE_SEPARATION_ADDITIONAL_FIELD::{field}")
        if source.get("mode") not in ALLOWED_SOURCE_MODES:
            failures.append("SOURCE_SEPARATION_MODE_ENUM_MISMATCH")
        for field in ("pre_target_lock", "target_hidden_until_scoring"):
            if not isinstance(source.get(field), bool):
                failures.append(f"SOURCE_SEPARATION_BOOLEAN_INVALID::{field}")
        for field in ("training_sources", "target_sources"):
            values = source.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
                failures.append(f"SOURCE_SEPARATION_SOURCE_LIST_INVALID::{field}")
    comparator = pack.get("comparator_baseline")
    if not isinstance(comparator, dict):
        failures.append("COMPARATOR_BASELINE_NOT_OBJECT")
    else:
        if set(comparator) != {"name", "prediction_rule", "pre_registered"}:
            failures.append("COMPARATOR_BASELINE_FIELD_SET_MISMATCH")
        if not isinstance(comparator.get("name"), str) or not comparator.get("name"):
            failures.append("COMPARATOR_NAME_INVALID")
        if not isinstance(comparator.get("prediction_rule"), str) or not comparator.get("prediction_rule"):
            failures.append("COMPARATOR_RULE_INVALID")
        if not isinstance(comparator.get("pre_registered"), bool):
            failures.append("COMPARATOR_PREREGISTERED_NOT_BOOLEAN")
    uncertainty = pack.get("uncertainty")
    if not isinstance(uncertainty, dict):
        failures.append("UNCERTAINTY_NOT_OBJECT")
    else:
        interval = uncertainty.get("interval")
        if set(uncertainty) != {"metric", "method", "interval"}:
            failures.append("UNCERTAINTY_FIELD_SET_MISMATCH")
        if not isinstance(uncertainty.get("metric"), str) or not uncertainty.get("metric"):
            failures.append("UNCERTAINTY_METRIC_INVALID")
        if not isinstance(uncertainty.get("method"), str) or not uncertainty.get("method"):
            failures.append("UNCERTAINTY_METHOD_INVALID")
        if not isinstance(interval, list) or len(interval) != 2 or not all(is_number(value) for value in interval):
            failures.append("UNCERTAINTY_INTERVAL_INVALID")
        elif float(interval[0]) > float(interval[1]):
            failures.append("UNCERTAINTY_INTERVAL_NOT_ORDERED")
    residuals = pack.get("residuals")
    if not isinstance(residuals, dict):
        failures.append("RESIDUALS_NOT_OBJECT")
    else:
        if set(residuals) != {"model", "comparator", "superiority_margin"}:
            failures.append("RESIDUAL_FIELD_SET_MISMATCH")
        for field in ("model", "comparator", "superiority_margin"):
            if not is_number(residuals.get(field)):
                failures.append(f"RESIDUAL_FIELD_INVALID::{field}")
    controls = pack.get("negative_controls")
    if not isinstance(controls, list) or not controls:
        failures.append("NEGATIVE_CONTROLS_INVALID")
    else:
        for idx, row in enumerate(controls):
            if not isinstance(row, dict) or set(row) != {"control_id", "description", "rejected"}:
                failures.append(f"NEGATIVE_CONTROL_FIELD_SET_MISMATCH::{idx}")
                continue
            if not row.get("control_id") or not row.get("description") or not isinstance(row.get("rejected"), bool):
                failures.append(f"NEGATIVE_CONTROL_VALUE_INVALID::{idx}")
    falsifiers = pack.get("falsifiers")
    if not isinstance(falsifiers, list) or not falsifiers or not all(isinstance(item, str) and item for item in falsifiers):
        failures.append("FALSIFIERS_INVALID")
    if pack.get("grand_toe_support_allowed") is not True:
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_CONST_MISMATCH")
    return ordered_unique(failures)


def tamper_payload(payload: Any, domain: str) -> Any:
    mutated = copy.deepcopy(payload)
    if isinstance(mutated, dict) and mutated.get("schema_id") == OFFICIAL_SNAPSHOT_BUNDLE_SCHEMA_ID:
        observations = mutated.get("observations", [])
        if observations:
            observations[0]["observed_value"] = float(observations[0]["observed_value"]) + 1.0
        return mutated
    if domain == "biology" and isinstance(mutated, dict):
        mutated.get("esearchresult", {}).pop("retmax", None)
        return mutated
    if domain == "systems" and isinstance(mutated, list) and len(mutated) > 1:
        for row in mutated[1]:
            if row.get("date") == "2024":
                row["value"] = None
                break
        return mutated
    return mutated


def run_tamper_tests(root: Path, evidence: SnapshotEvidence) -> list[dict[str, Any]]:
    path = resolve_under_root(root, evidence.snapshot_ref)
    payload = read_json(path)
    original_hash = sha256_object(payload)
    mutated = tamper_payload(payload, evidence.domain)
    mutated_hash = sha256_object(mutated)
    tests = [
        {
            "test_id": f"{evidence.domain}-snapshot-tamper-hash-changes",
            "description": "deterministic mutation of a target-bearing field must change the canonical snapshot hash",
            "passed": mutated_hash != original_hash,
        }
    ]
    try:
        if evidence.domain == "biology" and not (
            isinstance(mutated, dict)
            and isinstance(mutated.get("esearchresult"), dict)
            and "retmax" in mutated["esearchresult"]
        ):
            raise KeyError("retmax")
        if evidence.domain == "systems":
            rows = mutated[1] if isinstance(mutated, list) and len(mutated) > 1 else []
            values = {int(row["date"]): row.get("value") for row in rows if row.get("value") is not None}
            if 2024 not in values:
                raise KeyError("2024")
        if isinstance(payload, dict) and payload.get("schema_id") == OFFICIAL_SNAPSHOT_BUNDLE_SCHEMA_ID:
            rebuilt = parse_official_snapshot_bundle(root, evidence.snapshot_ref, evidence.domain, mutated)
            if residual_summary(rebuilt.observations) == residual_summary(evidence.observations):
                raise ValueError("tampered bundle residuals did not change")
        parse_rejected = False
    except Exception:
        parse_rejected = True
    tests.append(
        {
            "test_id": f"{evidence.domain}-target-field-tamper-rejected",
            "description": "removing or mutating target-bearing data must be detected by parser or residual replay",
            "passed": parse_rejected,
        }
    )
    negative_control_rejected = all(row.comparator_residual > row.model_residual for row in evidence.observations)
    tests.append(
        {
            "test_id": f"{evidence.domain}-negative-control-residual-test",
            "description": "every declared row-level comparator/negative control must have residual above the OC model residual",
            "passed": negative_control_rejected,
        }
    )
    return tests


def build_domain_candidate(root: Path, domain: str, snapshot_ref: str, output_root_rel: str = OUTPUT_ROOT_REL) -> DomainCandidate:
    requirements = load_requirements(root)
    minimum_n = int(requirements.get("minimum_per_domain_n", MINIMUM_N))
    evidence = load_snapshot_evidence(root, domain, snapshot_ref)
    source_failures = validate_source_separation(evidence.source_separation)
    observation_failures = validate_observations(evidence, minimum_n)
    tamper_tests = run_tamper_tests(root, evidence)
    tamper_failures = [f"TAMPER_TEST_FAILED::{row['test_id']}" for row in tamper_tests if row.get("passed") is not True]
    preliminary_blockers = ordered_unique(source_failures + observation_failures + tamper_failures)
    preliminary_pack = build_candidate_pack(evidence, support_allowed=not preliminary_blockers)
    gate_failures = grand_factory.pack_failure_reasons(preliminary_pack, requirements)
    schema_failures = validate_grand_schema_shape(preliminary_pack)
    support_allowed = not preliminary_blockers and not gate_failures and not schema_failures
    pack = preliminary_pack if preliminary_pack["grand_toe_support_allowed"] == support_allowed else build_candidate_pack(evidence, support_allowed)
    gate_failures = grand_factory.pack_failure_reasons(pack, requirements)
    schema_failures = validate_grand_schema_shape(pack)
    pack_ref = f"{output_root_rel}/{domain}_candidate_evidence_pack.json"
    blockers = ordered_unique(preliminary_blockers + gate_failures + schema_failures)
    observation_rows = [
        {
            "observation_id": row.observation_id,
            "training_source": row.training_source,
            "target_source": row.target_source,
            "formula": row.formula,
            "predicted_value": row.predicted_value,
            "observed_value": row.observed_value,
            "comparator_prediction": row.comparator_prediction,
            "model_residual": row.model_residual,
            "comparator_residual": row.comparator_residual,
            "uncertainty": row.uncertainty,
            "negative_control_id": row.negative_control_id,
            "negative_control_rejected": row.comparator_residual > row.model_residual,
            "falsifier": row.falsifier,
            "row_sha256": sha256_object(
                {
                    "observation_id": row.observation_id,
                    "training_source": row.training_source,
                    "target_source": row.target_source,
                    "formula": row.formula,
                    "predicted_value": row.predicted_value,
                    "observed_value": row.observed_value,
                    "comparator_prediction": row.comparator_prediction,
                    "uncertainty": row.uncertainty,
                    "falsifier": row.falsifier,
                }
            ),
        }
        for row in evidence.observations
    ]
    report_row = {
        "domain": domain,
        "candidate_pack_ref": pack_ref,
        "candidate_pack_sha256": sha256_object(pack),
        "snapshot_ref": evidence.snapshot_ref,
        "snapshot_kind": evidence.snapshot_kind,
        "snapshot_sha256": evidence.snapshot_sha256,
        "snapshot_sha256_policy": "LF_NORMALIZED_TEXT_SNAPSHOT_HASH",
        "snapshot_byte_count": evidence.snapshot_byte_count,
        "minimum_n": minimum_n,
        "candidate_n": len(evidence.observations),
        "source_validation_failures": source_failures,
        "observation_validation_failures": observation_failures,
        "schema_validation_failures": schema_failures,
        "grand_gate_failures": gate_failures,
        "tamper_test_total": len(tamper_tests),
        "tamper_tests": tamper_tests,
        "residuals": pack["residuals"],
        "valid_under_executor": support_allowed,
        "valid_under_current_grand_schema": not schema_failures,
        "valid_under_grand_gate": not gate_failures,
        "blockers": blockers,
        "protocol_notes": evidence.protocol_notes,
        "observation_rows": observation_rows,
    }
    return DomainCandidate(domain=domain, pack_ref=pack_ref, pack=pack, report_row=report_row)


def protocol_steps_for(domain: str) -> list[str]:
    return [
        f"pre-register a {domain} OC scoring rule, comparator baseline, residual metric, uncertainty method, negative controls, and falsifiers before target scoring",
        "freeze training/source-development material separately from target/held-out material and record stable hashes",
        "use prospective target collection or target-blind material whose target values are hidden until scoring",
        "collect at least 20 independent target observations for this domain",
        "score OC and comparator residuals under the same deterministic metric",
        "reject declared negative controls and retain falsifier conditions even when the pack fails",
        "route a completed valid pack to the parent registry only after the executor and grand gate both pass",
    ]


def build_protocol_payload(candidates: list[DomainCandidate]) -> dict[str, Any]:
    rows = []
    for candidate in candidates:
        row = candidate.report_row
        rows.append(
            {
                "domain": candidate.domain,
                "status": "READY_FOR_PARENT_REGISTRY_REVIEW" if row["valid_under_grand_gate"] else "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
                "candidate_pack_ref": candidate.pack_ref,
                "candidate_n": row["candidate_n"],
                "minimum_n": row["minimum_n"],
                "missing_n": max(0, int(row["minimum_n"]) - int(row["candidate_n"])),
                "blockers": row["blockers"],
                "required_protocol_steps": protocol_steps_for(candidate.domain),
            }
        )
    return {
        "schema_id": PROTOCOL_PACKET_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "evidence_owner": EVIDENCE_OWNER,
        "blocker_id": BLOCKER_ID,
        "executor": EXECUTOR_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
        "domain_total": len(rows),
        "blocked_domain_total": sum(1 for row in rows if row["status"] != "READY_FOR_PARENT_REGISTRY_REVIEW"),
        "rows": rows,
        "registry_integration_policy": "This executor does not edit validation/heldout/grand_science_evidence_registry.json; parent capability must route registry integration after review.",
    }


def build_execution_payload(
    root: Path,
    biology_snapshot_ref: str = BIOLOGY_DEFAULT_SNAPSHOT_REF,
    systems_snapshot_ref: str = SYSTEMS_DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> tuple[dict[str, Any], list[DomainCandidate], dict[str, Any]]:
    candidates = [
        build_domain_candidate(root, "biology", biology_snapshot_ref, output_root_rel),
        build_domain_candidate(root, "systems", systems_snapshot_ref, output_root_rel),
    ]
    protocol = build_protocol_payload(candidates)
    report_ref = f"{output_root_rel}/OC133_BIOLOGY_SYSTEMS_EVIDENCE_EXECUTION_REPORT.json"
    protocol_ref = f"{output_root_rel}/OC133_BIOLOGY_SYSTEMS_EVIDENCE_PROTOCOL.json"
    report = {
        "schema_id": EXECUTION_REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "evidence_owner": EVIDENCE_OWNER,
        "blocker_id": BLOCKER_ID,
        "executor": EXECUTOR_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "grand_factory_ref": "validation/grand_science/evidence_pack_factory.py",
        "output_root_ref": output_root_rel,
        "report_ref": report_ref,
        "protocol_ref": protocol_ref,
        "candidate_pack_refs": [candidate.pack_ref for candidate in candidates],
        "candidate_pack_total": len(candidates),
        "valid_under_current_grand_schema_total": sum(
            1 for candidate in candidates if candidate.report_row["valid_under_current_grand_schema"]
        ),
        "valid_under_grand_gate_total": sum(1 for candidate in candidates if candidate.report_row["valid_under_grand_gate"]),
        "valid_under_executor_total": sum(1 for candidate in candidates if candidate.report_row["valid_under_executor"]),
        "valid_pack_total": sum(1 for candidate in candidates if candidate.report_row["valid_under_grand_gate"]),
        "blocked_pack_total": sum(1 for candidate in candidates if not candidate.report_row["valid_under_grand_gate"]),
        "blocked_domain_total": sum(1 for candidate in candidates if not candidate.report_row["valid_under_grand_gate"]),
        "protocol_sha256": sha256_object(protocol),
        "domains": [candidate.report_row for candidate in candidates],
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW"
        if all(candidate.report_row["valid_under_grand_gate"] for candidate in candidates)
        else "BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE",
        "no_fabricated_success_policy": "The executor emits grand support only when source separation, N, formula, comparator, residual, uncertainty, negative controls, falsifiers, schema shape, and grand factory gate all pass. Current bounded replay snapshots remain blocked.",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
    }
    return report, candidates, protocol


def write_outputs(
    root: Path,
    biology_snapshot_ref: str = BIOLOGY_DEFAULT_SNAPSHOT_REF,
    systems_snapshot_ref: str = SYSTEMS_DEFAULT_SNAPSHOT_REF,
    output_root_rel: str = OUTPUT_ROOT_REL,
) -> dict[str, Any]:
    report, candidates, protocol = build_execution_payload(root, biology_snapshot_ref, systems_snapshot_ref, output_root_rel)
    for candidate in candidates:
        write_json(root / candidate.pack_ref, candidate.pack)
    write_json(root / f"{output_root_rel}/OC133_BIOLOGY_SYSTEMS_EVIDENCE_PROTOCOL.json", protocol)
    write_json(root / f"{output_root_rel}/OC133_BIOLOGY_SYSTEMS_EVIDENCE_EXECUTION_REPORT.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build biology/systems grand empirical candidate evidence packs.")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    parser.add_argument("--biology-snapshot-ref", default=BIOLOGY_DEFAULT_SNAPSHOT_REF)
    parser.add_argument("--systems-snapshot-ref", default=SYSTEMS_DEFAULT_SNAPSHOT_REF)
    parser.add_argument("--output-root-ref", default=OUTPUT_ROOT_REL)
    parser.add_argument("--write", action="store_true", help="write candidate packs and protocol artifacts")
    parser.add_argument("--check-only", action="store_true", help="build report without writing artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even when packs remain blocked")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.check_only or not args.write:
        report, _candidates, _protocol = build_execution_payload(
            root,
            biology_snapshot_ref=args.biology_snapshot_ref,
            systems_snapshot_ref=args.systems_snapshot_ref,
            output_root_rel=args.output_root_ref,
        )
    else:
        report = write_outputs(
            root,
            biology_snapshot_ref=args.biology_snapshot_ref,
            systems_snapshot_ref=args.systems_snapshot_ref,
            output_root_rel=args.output_root_ref,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["valid_under_grand_gate_total"] == len(SUPPORTED_DOMAINS):
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
