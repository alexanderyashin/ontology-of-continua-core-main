from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
FACTORY_REF = "tools/oc133_biology_target_evidence_factory.py"

OFFICIAL_BUNDLE_SCHEMA_ID = "OC133_BIOLOGY_TARGET_OFFICIAL_BUNDLE_v1"
PROTOCOL_SCHEMA_ID = "OC133_BIOLOGY_TARGET_EVIDENCE_PROTOCOL_v1"
WORK_ORDER_SCHEMA_ID = "OC133_BIOLOGY_TARGET_EVIDENCE_WORK_ORDER_v1"
REPORT_SCHEMA_ID = "OC133_BIOLOGY_TARGET_EVIDENCE_REPORT_v1"
HASHES_SCHEMA_ID = "OC133_BIOLOGY_TARGET_EVIDENCE_HASHES_v1"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/biology/target_evidence"
CANDIDATE_PACK_REL = f"{OUTPUT_ROOT_REL}/biology_target_evidence_candidate_pack.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_EVIDENCE_PROTOCOL.json"
WORK_ORDER_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_EVIDENCE_WORK_ORDER.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_EVIDENCE_REPORT.json"
HASHES_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_EVIDENCE_HASHES.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
DEFAULT_DISCOVERY_ROOTS = (
    "validation/_raw",
    "data/biology",
    f"{OUTPUT_ROOT_REL}/raw",
    "validation/heldout/acquisition_runs/oc133_official_readonly/snapshots",
)

EVIDENCE_PACK_ID = "OC133-BIOLOGY-TARGET-EVIDENCE-CANDIDATE"
EVIDENCE_FAMILY = "biology-target-outcome-evidence"
SOURCE_CONTRACT = "official_biology_target_bundle"
MINIMUM_N = 20

PAGINATION_TOKENS = (
    "pagination",
    "page-size",
    "page size",
    "retmax",
    "retstart",
    "idlist",
    "esearch",
    "esearchresult",
    "total-hit-count",
    "total hit count",
    "gpl96[accession]",
)

BIOLOGICAL_OUTCOME_TOKENS = (
    "abundance",
    "assay",
    "biological",
    "biomarker",
    "cell",
    "concentration",
    "expression",
    "fold_change",
    "fold-change",
    "gene",
    "growth",
    "metabolite",
    "observable",
    "phenotype",
    "protein",
    "response",
    "rna",
    "survival",
    "viability",
)

TRIVIAL_COMPARATOR_TOKENS = (
    "constant zero",
    "null baseline",
    "copy target",
    "copy observed",
    "observed value",
    "target value",
    "identity",
    "oracle",
    "pagination",
    "page-size",
    "retmax",
    "idlist",
    "esearch",
    "total-hit-count",
)


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def ordered_unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for value in values:
        key = canonical_json(value) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if isinstance(value, bool):
            return default
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def load_requirements(root: Path) -> dict[str, Any]:
    fallback = {
        "minimum_per_domain_n": MINIMUM_N,
        "required_domains": ["biology"],
        "required_source_separation_modes": ["target_blind", "prospective"],
    }
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return fallback
    payload = read_json(path)
    if not isinstance(payload, dict):
        return fallback
    return {**fallback, **payload}


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def text_blob(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return " ".join(parts).lower()


def has_64_hex(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def discover_official_bundle_refs(root: Path, explicit_refs: list[str] | None = None) -> list[str]:
    if explicit_refs:
        return ordered_unique([ref.replace("\\", "/") for ref in explicit_refs if ref.strip()])
    refs: list[str] = []
    for base_ref in DEFAULT_DISCOVERY_ROOTS:
        base = root / base_ref
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            if not path.is_file():
                continue
            if path.name.startswith("OC133_BIOLOGY_TARGET_EVIDENCE_") or path.name == Path(CANDIDATE_PACK_REL).name:
                continue
            try:
                payload = read_json(path)
            except Exception:
                continue
            if isinstance(payload, dict) and payload.get("schema_id") == OFFICIAL_BUNDLE_SCHEMA_ID:
                refs.append(rel(root, path))
    return ordered_unique(refs)


def source_separation_from_bundle(bundle: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    raw = bundle.get("source_separation")
    source = raw if isinstance(raw, dict) else {}
    training_sources = list_of_strings(source.get("training_sources"))
    target_sources = list_of_strings(source.get("target_sources"))
    if not training_sources:
        training_sources = ordered_unique([as_str(row.get("training_source")) for row in rows if row.get("training_source")])
    if not target_sources:
        target_sources = ordered_unique([as_str(row.get("target_source")) for row in rows if row.get("target_source")])
    return {
        "mode": as_str(source.get("mode"), ""),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "training_sources": training_sources,
        "target_sources": target_sources,
    }


def comparator_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    raw = bundle.get("comparator_baseline")
    comparator = raw if isinstance(raw, dict) else {}
    return {
        "name": as_str(comparator.get("name")),
        "prediction_rule": as_str(comparator.get("prediction_rule")),
        "pre_registered": comparator.get("pre_registered") is True,
    }


def raw_target_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("biological_target_rows", "target_rows", "observations", "rows"):
        rows = bundle.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def normalize_target_row(row: dict[str, Any], idx: int, bundle_ref: str, bundle_sha256: str) -> dict[str, Any]:
    source_ref = as_str(row.get("source_ref") or row.get("target_source") or f"{bundle_ref}::row={idx}")
    source_sha256 = as_str(row.get("source_sha256") or row.get("source_hash") or row.get("snapshot_sha256") or bundle_sha256)
    observed = as_float(row.get("observed_value"))
    predicted = as_float(row.get("predicted_value"))
    comparator = as_float(row.get("comparator_prediction"))
    uncertainty = as_float(row.get("uncertainty"), 0.0)
    normalized = {
        "biological_target_id": as_str(
            row.get("biological_target_id") or row.get("target_id") or row.get("observation_id") or f"BIO-TARGET-{idx:04d}"
        ),
        "biological_target_kind": as_str(row.get("biological_target_kind") or row.get("target_kind") or row.get("target_type")),
        "biological_observable": as_str(row.get("biological_observable") or row.get("observable") or row.get("outcome")),
        "source_ref": source_ref,
        "source_sha256": source_sha256,
        "training_source": as_str(row.get("training_source")),
        "target_source": as_str(row.get("target_source") or source_ref),
        "predicted_value": predicted,
        "observed_value": observed,
        "comparator_prediction": comparator,
        "uncertainty": uncertainty,
        "negative_control_id": as_str(row.get("negative_control_id")),
        "negative_control_description": as_str(row.get("negative_control_description") or row.get("negative_control")),
        "falsifier": as_str(row.get("falsifier")),
    }
    normalized["model_residual"] = abs(predicted - observed) if is_number(predicted) and is_number(observed) else math.nan
    normalized["comparator_residual"] = abs(comparator - observed) if is_number(comparator) and is_number(observed) else math.nan
    normalized["row_sha256"] = sha256_object({key: value for key, value in normalized.items() if key != "row_sha256"})
    return normalized


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    model = [float(row["model_residual"]) for row in rows if is_number(row.get("model_residual"))]
    comparator = [float(row["comparator_residual"]) for row in rows if is_number(row.get("comparator_residual"))]
    model_mean = sum(model) / len(model) if model else 0.0
    comparator_mean = sum(comparator) / len(comparator) if comparator else 0.0
    return {
        "model": model_mean,
        "comparator": comparator_mean,
        "superiority_margin": comparator_mean - model_mean,
    }


def uncertainty_interval(rows: list[dict[str, Any]], residuals: dict[str, float]) -> list[float]:
    budgets = [max(0.0, float(row.get("uncertainty", 0.0))) for row in rows if is_number(row.get("uncertainty"))]
    budget = sum(budgets) / len(budgets) if budgets else 0.0
    return [max(0.0, residuals["model"] - budget), residuals["model"] + budget]


def validate_source_separation(source: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    allowed_modes = set(requirements.get("required_source_separation_modes", ["target_blind", "prospective"]))
    if source.get("mode") not in allowed_modes:
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


def validate_comparator(comparator: dict[str, Any], model_under_test: str) -> list[str]:
    failures: list[str] = []
    comparator_text = text_blob(comparator.get("name"), comparator.get("prediction_rule"))
    if not comparator.get("name") or not comparator.get("prediction_rule"):
        failures.append("COMPARATOR_BASELINE_INCOMPLETE")
    if comparator.get("pre_registered") is not True:
        failures.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")
    if comparator_text == text_blob(model_under_test) or any(token in comparator_text for token in TRIVIAL_COMPARATOR_TOKENS):
        failures.append("BIOLOGY_COMPARATOR_TRIVIAL_OR_NONBIOLOGICAL")
    return failures


def validate_rows(rows: list[dict[str, Any]], source: dict[str, Any], minimum_n: int) -> list[str]:
    failures: list[str] = []
    pagination_row_seen = False
    if len(rows) < minimum_n:
        failures.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
    training_sources = set(source.get("training_sources", [])) if isinstance(source.get("training_sources"), list) else set()
    target_sources = set(source.get("target_sources", [])) if isinstance(source.get("target_sources"), list) else set()
    seen_ids: set[str] = set()
    for idx, row in enumerate(rows):
        prefix = f"BIOLOGY_TARGET_ROW::{idx}::{row.get('biological_target_id')}"
        target_id = as_str(row.get("biological_target_id"))
        if not target_id:
            failures.append(f"{prefix}::TARGET_ID_MISSING")
        elif target_id in seen_ids:
            failures.append(f"{prefix}::TARGET_ID_DUPLICATE")
        seen_ids.add(target_id)

        kind = as_str(row.get("biological_target_kind")).lower()
        observable = as_str(row.get("biological_observable")).lower()
        row_text = text_blob(kind, observable, row.get("source_ref"))
        if not kind:
            failures.append(f"{prefix}::BIOLOGICAL_TARGET_KIND_MISSING")
        if any(token in row_text for token in PAGINATION_TOKENS):
            pagination_row_seen = True
            failures.append(f"{prefix}::API_PAGINATION_ROW_NOT_BIOLOGICAL_TARGET")
        if not any(token in row_text for token in BIOLOGICAL_OUTCOME_TOKENS):
            failures.append(f"{prefix}::BIOLOGICAL_OUTCOME_OBSERVABLE_NOT_DECLARED")
        if not has_64_hex(row.get("source_sha256")):
            failures.append(f"{prefix}::SOURCE_HASH_MISSING_OR_INVALID")

        training_source = as_str(row.get("training_source"))
        target_source = as_str(row.get("target_source"))
        if not training_source or not target_source:
            failures.append(f"{prefix}::ROW_SOURCE_SEPARATION_MISSING")
        if training_source == target_source:
            failures.append(f"{prefix}::TARGET_LEAKAGE_TRAINING_EQUALS_TARGET")
        if training_source in target_sources or target_source in training_sources:
            failures.append(f"{prefix}::TARGET_LEAKAGE_SOURCE_OVERLAP")

        for field in ("predicted_value", "observed_value", "comparator_prediction", "uncertainty"):
            if not is_number(row.get(field)):
                failures.append(f"{prefix}::{field.upper()}_INVALID")
        if is_number(row.get("uncertainty")) and float(row["uncertainty"]) < 0:
            failures.append(f"{prefix}::UNCERTAINTY_NEGATIVE")
        if not row.get("negative_control_id") or not row.get("negative_control_description"):
            failures.append(f"{prefix}::NEGATIVE_CONTROL_INCOMPLETE")
        if is_number(row.get("model_residual")) and is_number(row.get("comparator_residual")):
            if float(row["comparator_residual"]) <= float(row["model_residual"]):
                failures.append(f"{prefix}::NEGATIVE_CONTROL_NOT_REJECTED")
        if not row.get("falsifier"):
            failures.append(f"{prefix}::FALSIFIER_MISSING")
    if pagination_row_seen:
        failures.append("BIOLOGY_PAGINATION_QA_NOT_GRAND_EVIDENCE")
    return ordered_unique(failures)


def build_pack(
    *,
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    comparator: dict[str, Any],
    model_under_test: str,
    uncertainty_metric: str,
    uncertainty_method: str,
    support_allowed: bool,
    source_refs: list[str],
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    residuals = residual_summary(rows)
    target_rows = [
        {
            "biological_target_id": row["biological_target_id"],
            "biological_target_kind": row["biological_target_kind"],
            "biological_observable": row["biological_observable"],
            "source_ref": row["source_ref"],
            "source_sha256": row["source_sha256"],
            "predicted_value": row["predicted_value"],
            "observed_value": row["observed_value"],
            "comparator_prediction": row["comparator_prediction"],
            "model_residual": row["model_residual"],
            "comparator_residual": row["comparator_residual"],
            "uncertainty": row["uncertainty"],
            "row_sha256": row["row_sha256"],
        }
        for row in rows
    ]
    pack = {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": EVIDENCE_PACK_ID,
        "domain": "biology",
        "evidence_family": EVIDENCE_FAMILY,
        "pack_version": "1.0",
        "source_contract": SOURCE_CONTRACT,
        "supersedes": supersedes or ["OC133-BIOLOGY-NCBI-BATCH-CANDIDATE"],
        "source_separation": source,
        "n": len(rows),
        "model_under_test": model_under_test,
        "comparator_baseline": comparator,
        "uncertainty": {
            "metric": uncertainty_metric,
            "method": uncertainty_method,
            "interval": uncertainty_interval(rows, residuals),
        },
        "residuals": residuals,
        "negative_controls": [
            {
                "control_id": row["negative_control_id"],
                "description": row["negative_control_description"],
                "rejected": is_number(row.get("comparator_residual"))
                and is_number(row.get("model_residual"))
                and float(row["comparator_residual"]) > float(row["model_residual"]),
            }
            for row in rows
        ],
        "falsifiers": ordered_unique([row["falsifier"] for row in rows if row.get("falsifier")]),
        "source_hashes": ordered_unique(
            [
                {
                    "source_ref": row["source_ref"],
                    "sha256": row["source_sha256"],
                    "hash_policy": "official source snapshot sha256 declared by acquisition lock or bundle hash",
                }
                for row in rows
            ]
        ),
        "biological_target_rows": target_rows,
        "source_bundle_refs": source_refs,
        "grand_toe_support_allowed": support_allowed,
    }
    return pack


def parse_official_bundle(root: Path, bundle_ref: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[str]]:
    path = resolve_under_root(root, bundle_ref)
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("schema_id") != OFFICIAL_BUNDLE_SCHEMA_ID:
        raise ValueError(f"not an {OFFICIAL_BUNDLE_SCHEMA_ID} bundle: {bundle_ref}")
    bundle_sha = sha256_bytes(path.read_bytes())
    rows = [
        normalize_target_row(row, idx, bundle_ref, bundle_sha)
        for idx, row in enumerate(raw_target_rows(payload), start=1)
    ]
    source = source_separation_from_bundle(payload, rows)
    comparator = comparator_from_bundle(payload)
    model = as_str(payload.get("model_under_test"))
    uncertainty_metric = as_str(payload.get("uncertainty_metric"), "mean absolute residual")
    uncertainty_method = as_str(payload.get("uncertainty_method"), "row-level official biological observable residual interval")
    return (
        payload,
        rows,
        {
            "source": source,
            "comparator": comparator,
            "model_under_test": model,
            "uncertainty_metric": uncertainty_metric,
            "uncertainty_method": uncertainty_method,
            "bundle_sha256": bundle_sha,
        },
        [],
    )


def build_acquisition_work_order(minimum_n: int) -> dict[str, Any]:
    query = {
        "db": "geoprofiles",
        "term": "GDS3716[All Fields] AND Homo sapiens[ORGN] AND count[VTYP] NOT Control[All Fields]",
        "retmode": "json",
        "retmax": "30",
        "retstart": "0",
        "sort": "relevance",
    }
    return {
        "schema_id": WORK_ORDER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "factory": FACTORY_REF,
        "status": "NO_LOCAL_OFFICIAL_BIOLOGICAL_TARGET_BUNDLE_FOUND",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
        "minimum_n": minimum_n,
        "official_source_policy": "Use official NCBI/GEO or another official biological repository only; do not transcribe or invent target values.",
        "preferred_local_helper": "tools/oc133_biology_target_official_bundle_builder.py",
        "preferred_helper_command": (
            "python tools/oc133_biology_target_official_bundle_builder.py --execute-network "
            "--allow-blocked-exit-zero"
        ),
        "required_final_bundle_schema_id": OFFICIAL_BUNDLE_SCHEMA_ID,
        "required_final_bundle_fields": [
            "schema_id",
            "domain",
            "source_separation",
            "model_under_test",
            "comparator_baseline",
            "uncertainty_metric",
            "uncertainty_method",
            "biological_target_rows",
        ],
        "official_acquisition_requests": [
            {
                "request_id": "OC133-BIO-TARGET-GEOPROFILES-ESEARCH-0001",
                "http_method": "GET",
                "official_endpoint_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                + urlencode(query),
                "query_params": query,
                "expected_local_snapshot_ref": f"{OUTPUT_ROOT_REL}/raw/OC133_BIOLOGY_TARGET_GEO_PROFILE_SEARCH.json",
                "hash_required": True,
                "no_send_lock": True,
            },
            {
                "request_id": "OC133-BIO-TARGET-GEOPROFILES-ESUMMARY-0001",
                "http_method": "GET",
                "official_endpoint_url_template": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=geoprofiles&retmode=json&id={comma_joined_esearch_ids}",
                "expected_local_snapshot_ref": f"{OUTPUT_ROOT_REL}/raw/OC133_BIOLOGY_TARGET_GEO_PROFILE_SUMMARY.json",
                "depends_on": "OC133-BIO-TARGET-GEOPROFILES-ESEARCH-0001",
                "hash_required": True,
                "no_send_lock": True,
            },
        ],
        "target_materialization_protocol": [
            "Pin the GEO Profiles ESearch response with the official read-only runner.",
            "Pin the GEO Profiles ESummary response for the locked profile UIDs with the official read-only runner.",
            "Materialize a visible projection containing GEO Profile uid, dataset/platform IDs, gene/probe labels, value type, vmin, vmax, and rstd.",
            "Materialize prediction rows from the visible projection before unsealing the target projection.",
            "Unseal only the rmean target projection after prediction materialization and build one biological_target_row per official expression observable.",
            "Each target row must represent a GEO Profile gene-expression observable, never an API count, page size, retmax, retstart, or idlist property.",
        ],
        "acceptance_criteria": [
            f"N >= {minimum_n}",
            "source_separation.mode is target_blind or prospective",
            "pre_target_lock and target_hidden_until_scoring are true",
            "training_sources and target_sources are non-overlapping",
            "comparator is pre-registered, biological, and nontrivial",
            "every row has source_ref, source_sha256, uncertainty, residuals, negative control, and falsifier",
        ],
    }


def build_protocol(minimum_n: int, bundle_refs: list[str], blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "factory": FACTORY_REF,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "work_order_ref": WORK_ORDER_REL,
        "minimum_n": minimum_n,
        "official_bundle_refs": bundle_refs,
        "blockers": blockers,
        "support_policy": "Biology support is closed only by official biological target rows with target-hidden/prospective separation and nontrivial biological comparator superiority.",
        "pagination_demote_policy": "NCBI/GEO pagination or ESearch page-size reconstruction is acquisition QA only and cannot satisfy this lane.",
        "no_send": True,
    }


def build_empty_blocked_pack(work_order: dict[str, Any]) -> dict[str, Any]:
    return build_pack(
        rows=[],
        source={
            "mode": "target_blind",
            "pre_target_lock": False,
            "target_hidden_until_scoring": False,
            "training_sources": [WORK_ORDER_REL + "::visible_projection_protocol"],
            "target_sources": [WORK_ORDER_REL + "::target_projection_protocol"],
        },
        comparator={
            "name": "pending official biological comparator",
            "prediction_rule": "blocked until an official target bundle declares a nontrivial biological comparator before scoring",
            "pre_registered": False,
        },
        model_under_test="pending pre-registered biological target scoring rule",
        uncertainty_metric="mean absolute residual",
        uncertainty_method="blocked until official biological target rows are acquired",
        support_allowed=False,
        source_refs=[],
    )


def build_payload(root: Path | None = None, bundle_refs: list[str] | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    requirements = load_requirements(root)
    minimum_n = int(requirements.get("minimum_per_domain_n", MINIMUM_N))
    discovered_refs = discover_official_bundle_refs(root, bundle_refs)

    local_blockers: list[str] = []
    all_rows: list[dict[str, Any]] = []
    source: dict[str, Any] | None = None
    comparator: dict[str, Any] | None = None
    model_under_test = ""
    uncertainty_metric = "mean absolute residual"
    uncertainty_method = "row-level official biological observable residual interval"
    bundle_hashes: list[dict[str, Any]] = []

    for bundle_ref in discovered_refs:
        try:
            bundle, rows, metadata, bundle_failures = parse_official_bundle(root, bundle_ref)
        except Exception as exc:
            local_blockers.append(f"OFFICIAL_BUNDLE_PARSE_FAILED::{bundle_ref}::{exc.__class__.__name__}")
            continue
        if bundle.get("domain") != "biology":
            local_blockers.append(f"OFFICIAL_BUNDLE_DOMAIN_MISMATCH::{bundle_ref}")
            continue
        all_rows.extend(rows)
        source = source or metadata["source"]
        comparator = comparator or metadata["comparator"]
        model_under_test = model_under_test or metadata["model_under_test"]
        uncertainty_metric = metadata["uncertainty_metric"] or uncertainty_metric
        uncertainty_method = metadata["uncertainty_method"] or uncertainty_method
        local_blockers.extend(bundle_failures)
        bundle_hashes.append(
            {
                "source_ref": bundle_ref,
                "sha256": metadata["bundle_sha256"],
                "hash_policy": "sha256 over official bundle bytes as stored",
            }
        )

    work_order = build_acquisition_work_order(minimum_n)
    if not discovered_refs:
        local_blockers.extend(
            [
                "NO_LOCAL_OFFICIAL_BIOLOGICAL_TARGET_BUNDLE_FOUND",
                "OFFICIAL_ACQUISITION_WORK_ORDER_EMITTED_NO_SEND",
            ]
        )
        candidate_pack = build_empty_blocked_pack(work_order)
    else:
        source = source or {}
        comparator = comparator or {}
        local_blockers.extend(validate_source_separation(source, requirements))
        local_blockers.extend(validate_comparator(comparator, model_under_test))
        local_blockers.extend(validate_rows(all_rows, source, minimum_n))
        local_blockers = ordered_unique(local_blockers)
        gate_pack = build_pack(
            rows=all_rows,
            source=source,
            comparator=comparator,
            model_under_test=model_under_test,
            uncertainty_metric=uncertainty_metric,
            uncertainty_method=uncertainty_method,
            support_allowed=True,
            source_refs=discovered_refs,
        )
        gate_failures = grand_factory.pack_failure_reasons(gate_pack, requirements)
        support_allowed = not ordered_unique([*local_blockers, *gate_failures])
        candidate_pack = build_pack(
            rows=all_rows,
            source=source,
            comparator=comparator,
            model_under_test=model_under_test,
            uncertainty_metric=uncertainty_metric,
            uncertainty_method=uncertainty_method,
            support_allowed=support_allowed,
            source_refs=discovered_refs,
        )

    gate_failures = grand_factory.pack_failure_reasons(candidate_pack, requirements)
    blockers = ordered_unique([*local_blockers, *gate_failures])
    protocol = build_protocol(minimum_n, discovered_refs, blockers)
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "factory": FACTORY_REF,
        "requirements_ref": REQUIREMENTS_REL,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "candidate_pack_sha256": sha256_object(candidate_pack),
        "protocol_ref": PROTOCOL_REL,
        "work_order_ref": WORK_ORDER_REL,
        "official_bundle_refs": discovered_refs,
        "official_bundle_hashes": bundle_hashes,
        "candidate_n": candidate_pack["n"],
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - int(candidate_pack["n"])),
        "local_blockers": local_blockers,
        "grand_gate_failures": gate_failures,
        "blockers": blockers,
        "grand_toe_support_allowed": candidate_pack.get("grand_toe_support_allowed") is True and not blockers,
        "biology_support_closes": candidate_pack.get("grand_toe_support_allowed") is True and not blockers,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW"
        if candidate_pack.get("grand_toe_support_allowed") is True and not blockers
        else "BLOCKED_PENDING_OFFICIAL_BIOLOGICAL_TARGET_EVIDENCE",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
    }
    readme = render_readme(report)
    hashes = {
        "schema_id": HASHES_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "artifact_hashes": [
            {"artifact_ref": CANDIDATE_PACK_REL, "sha256": sha256_object(candidate_pack)},
            {"artifact_ref": PROTOCOL_REL, "sha256": sha256_object(protocol)},
            {"artifact_ref": WORK_ORDER_REL, "sha256": sha256_object(work_order)},
            {"artifact_ref": REPORT_REL, "sha256": sha256_object(report)},
            {"artifact_ref": README_REL, "sha256": sha256_bytes(readme.encode("utf-8"))},
        ],
        "official_bundle_hashes": bundle_hashes,
    }
    return {
        "candidate_pack": candidate_pack,
        "protocol": protocol,
        "work_order": work_order,
        "report": report,
        "hashes": hashes,
        "readme": readme,
    }


def render_readme(report: dict[str, Any]) -> str:
    blockers = report.get("blockers", [])
    lines = [
        "# Biology Target Evidence Lane",
        "",
        f"Verdict: `{report.get('verdict')}`",
        f"Biology support closes: `{str(report.get('biology_support_closes')).lower()}`",
        f"Rows: `{report.get('candidate_n')}`",
        f"Minimum N: `{report.get('minimum_n')}`",
        "",
        "## Blockers",
    ]
    lines.extend([f"- `{blocker}`" for blocker in blockers] or ["- `none`"])
    lines.extend(
        [
            "",
            "This lane accepts only official biological outcome/observable target rows. NCBI/GEO pagination QA remains blocked as non-biological evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(root: Path | None = None, bundle_refs: list[str] | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    payload = build_payload(root, bundle_refs=bundle_refs)
    write_json(root / CANDIDATE_PACK_REL, payload["candidate_pack"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / WORK_ORDER_REL, payload["work_order"])
    write_json(root / REPORT_REL, payload["report"])
    write_json(root / HASHES_REL, payload["hashes"])
    write_text(root / README_REL, payload["readme"])
    return payload


def check_stored(root: Path | None = None, bundle_refs: list[str] | None = None) -> list[str]:
    root = (root or repo_root()).resolve()
    expected = build_payload(root, bundle_refs=bundle_refs)
    checks = [
        (CANDIDATE_PACK_REL, expected["candidate_pack"]),
        (PROTOCOL_REL, expected["protocol"]),
        (WORK_ORDER_REL, expected["work_order"]),
        (REPORT_REL, expected["report"]),
        (HASHES_REL, expected["hashes"]),
    ]
    failures: list[str] = []
    for rel_path, payload in checks:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        if read_json(path) != payload:
            failures.append(f"mismatch::{rel_path}")
    readme = root / README_REL
    if not readme.exists():
        failures.append(f"missing::{README_REL}")
    elif readme.read_text(encoding="utf-8") != expected["readme"]:
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OC133 biology target evidence lane artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--bundle-ref", action="append", default=None, help="explicit official biology target bundle ref")
    parser.add_argument("--write", action="store_true", help="write artifacts")
    parser.add_argument("--check", action="store_true", help="check persisted artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit zero when the honest result is blocked")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root, bundle_refs=args.bundle_ref)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [CANDIDATE_PACK_REL, PROTOCOL_REL, WORK_ORDER_REL, REPORT_REL, HASHES_REL, README_REL]}, indent=2))
        return 0
    payload = write_outputs(root, bundle_refs=args.bundle_ref) if args.write else build_payload(root, bundle_refs=args.bundle_ref)
    print(json.dumps(payload["report"], ensure_ascii=True, indent=2))
    if payload["report"]["biology_support_closes"] is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
