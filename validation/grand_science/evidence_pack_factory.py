from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


EVIDENCE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
REPORT_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_REPORT_v1"
FACTORY_SCAN_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN_v1"
DECOMPOSITION_QUEUE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
FORMAL_ROUTE_DOMAIN_SET = {"mathematics"}

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
REGISTRY_REL = "validation/heldout/grand_science_evidence_registry.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
MATHEMATICS_FORMAL_SUPPORT_REPORT_REL = (
    "validation/heldout/grand_science/mathematics/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json"
)
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.md"
SCAN_REL = "validation/heldout/OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json"
QUEUE_REL = "validation/heldout/OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json"
SAMPLE_PACK_REL = "validation/heldout/samples/grand_empirical_evidence_pack.sample.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
PROTOCOL_SCHEMA_REL = "validation/grand_science/grand_empirical_protocol.schema.json"

DEFAULT_CANDIDATE_ROOTS = (
    "validation/heldout",
    "validation/grand_science",
)

DISCOVERY_EXCLUDED_NAMES = {
    "grand_science_evidence_registry.json",
    "OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json",
    "OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json",
}

DISCOVERY_EXCLUDED_SUFFIXES = (
    ".schema.json",
    ".sample.json",
)

REQUIRED_PACK_FIELDS = (
    "schema_id",
    "release_id",
    "capability_owner",
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

BIOLOGY_PAGINATION_TOKENS = (
    "page-size",
    "page size",
    "pagination",
    "retmax",
    "idlist",
    "esearch",
    "total-hit-count",
    "total hit count",
    "gpl96[accession]",
)

BIOLOGY_SILLY_COMPARATOR_TOKENS = (
    "page-size",
    "page size",
    "pagination",
    "retmax",
    "idlist",
    "esearchresult.count",
    "total-hit-count",
    "total hit count",
    "constant zero",
    "null baseline",
    "visible-only null",
)

SHA256_RE = re.compile(r"[0-9a-fA-F]{64}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def first_metadata_value(pack: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in pack:
            return pack[key]
    for metadata_key in ("metadata", "evidence_metadata", "pack_metadata", "supersession"):
        metadata = pack.get(metadata_key)
        if not isinstance(metadata, dict):
            continue
        for key in keys:
            if key in metadata:
                return metadata[key]
    return None


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [str(value)]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(string_list(item))
        return ordered_unique(out)
    if isinstance(value, dict):
        out = []
        for key in (
            "evidence_pack_id",
            "pack_id",
            "source_ref",
            "ref",
            "id",
            "evidence_pack_ids",
            "pack_ids",
            "source_refs",
            "refs",
        ):
            out.extend(string_list(value.get(key)))
        return ordered_unique(out)
    return []


def text_blob(*values: Any) -> str:
    return " ".join(string_list(list(values))).lower()


def biology_target_rows(pack: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("biological_target_rows", "biology_target_rows", "target_evidence_rows", "target_rows"):
        rows = pack.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    rows = first_metadata_value(pack, ("biological_target_rows", "biology_target_rows", "target_evidence_rows", "target_rows"))
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return []


def row_value(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def biology_specific_failure_reasons(pack: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    if pack.get("domain") != "biology":
        return []
    failures: list[str] = []
    source = pack.get("source_separation", {}) if isinstance(pack.get("source_separation"), dict) else {}
    comparator = pack.get("comparator_baseline", {}) if isinstance(pack.get("comparator_baseline"), dict) else {}
    combined = text_blob(
        pack.get("evidence_pack_id"),
        pack.get("model_under_test"),
        pack.get("falsifiers"),
        comparator.get("name"),
        comparator.get("prediction_rule"),
        source.get("training_sources"),
        source.get("target_sources"),
        pack.get("evidence_family"),
        pack.get("source_contract"),
        pack.get("source_contracts"),
    )
    if any(token in combined for token in BIOLOGY_PAGINATION_TOKENS):
        failures.append("BIOLOGY_PAGINATION_QA_NOT_GRAND_EVIDENCE")
    comparator_text = text_blob(comparator.get("name"), comparator.get("prediction_rule"))
    if any(token in comparator_text for token in BIOLOGY_SILLY_COMPARATOR_TOKENS):
        failures.append("BIOLOGY_COMPARATOR_STRUCTURALLY_SILLY_OR_PAGINATION_ONLY")

    rows = biology_target_rows(pack)
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    if len(rows) < minimum_n:
        failures.append(f"BIOLOGY_TARGET_ROWS_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
    if not rows:
        failures.append("BIOLOGY_TARGET_ROWS_REQUIRED")
    for idx, row in enumerate(rows):
        target_id = row_value(row, ("biological_target_id", "target_id", "observation_id"))
        target_kind = str(row_value(row, ("biological_target_kind", "target_kind", "target_type")) or "").lower()
        source_hash = row_value(row, ("source_sha256", "source_hash", "snapshot_sha256"))
        source_ref = row_value(row, ("source_ref", "snapshot_ref", "target_source"))
        if not isinstance(target_id, str) or not target_id.strip():
            failures.append(f"BIOLOGY_TARGET_ROW_ID_MISSING::{idx}")
        if not target_kind:
            failures.append(f"BIOLOGY_TARGET_KIND_MISSING::{idx}")
        elif any(token in target_kind for token in ("pagination", "page_size", "page-size", "retmax", "idlist", "esearch")):
            failures.append(f"BIOLOGY_TARGET_KIND_IS_API_PAGINATION::{idx}")
        if not isinstance(source_ref, str) or not source_ref.strip():
            failures.append(f"BIOLOGY_TARGET_SOURCE_REF_MISSING::{idx}")
        if not isinstance(source_hash, str) or not SHA256_RE.fullmatch(source_hash):
            failures.append(f"BIOLOGY_TARGET_SOURCE_HASH_MISSING::{idx}")
    return ordered_unique(failures)


def ref_hash_pairs_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    pairs: list[str] = []
    for row in rows:
        source_ref = row_value(row, ("source_ref", "snapshot_ref", "target_source"))
        source_hash = row_value(row, ("source_sha256", "source_hash", "snapshot_sha256", "sha256"))
        if isinstance(source_ref, str) and source_ref.strip() and isinstance(source_hash, str) and SHA256_RE.fullmatch(source_hash):
            pairs.append(f"{source_ref.strip()}::{source_hash.lower()}")
    return ordered_unique(pairs)


def source_hash_artifact_pairs(pack: dict[str, Any]) -> list[str]:
    pairs = ref_hash_pairs_from_rows(biology_target_rows(pack))
    for key in ("source_hashes", "source_artifacts", "artifact_hashes", "artifact_refs"):
        entries = first_metadata_value(pack, (key,))
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            source_ref = row_value(entry, ("source_ref", "artifact_ref", "snapshot_ref", "ref"))
            source_hash = row_value(entry, ("source_sha256", "source_hash", "snapshot_sha256", "sha256", "artifact_sha256"))
            if isinstance(source_ref, str) and source_ref.strip() and isinstance(source_hash, str) and SHA256_RE.fullmatch(source_hash):
                pairs.append(f"{source_ref.strip()}::{source_hash.lower()}")
    return ordered_unique(pairs)


def pack_supersedes(pack: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "supersedes",
        "supersedes_refs",
        "supersedes_ref",
        "supersedes_source_refs",
        "supersedes_pack_refs",
        "supersedes_pack_ids",
        "supersedes_evidence_pack_ids",
        "superseded_refs",
        "superseded_pack_ids",
    ):
        refs.extend(string_list(first_metadata_value(pack, (key,))))
    return ordered_unique([ref.replace("\\", "/") for ref in refs if ref.strip()])


def pack_family(pack: dict[str, Any]) -> str | None:
    value = first_metadata_value(
        pack,
        (
            "evidence_family",
            "pack_family",
            "candidate_family",
            "family",
            "supersession_family",
        ),
    )
    if value is None:
        return None
    family = str(value).strip()
    return family or None


def pack_version(pack: dict[str, Any]) -> str | None:
    value = first_metadata_value(
        pack,
        (
            "evidence_pack_version",
            "pack_version",
            "candidate_version",
            "evidence_version",
            "version",
        ),
    )
    if value is None:
        return None
    version = str(value).strip()
    return version or None


def source_contract_tokens_from_value(value: Any) -> list[str]:
    tokens: list[str] = []
    for item in string_list(value):
        normalized = item.replace("\\", "/").lower()
        source_head = normalized.split("::", 1)[0]
        for part in source_head.split("+"):
            compact = part.replace("-", "_")
            if "pubchem" in compact:
                tokens.append("pubchem")
            if "nist_webbook" in compact:
                tokens.append("nist_webbook")
            if "nist_constants" in compact or "codata" in compact:
                tokens.append("nist_codata")
            if "world_bank" in compact or "wdi" in compact:
                tokens.append("world_bank_wdi")
            if "ncbi" in compact:
                tokens.append("ncbi")
    return ordered_unique(tokens)


def pack_source_contracts(pack: dict[str, Any], source_ref: str) -> list[str]:
    explicit: list[str] = []
    for key in (
        "source_contract",
        "source_contract_id",
        "source_contracts",
        "source_family",
        "source_family_id",
        "source_families",
        "dataset_family",
        "dataset_family_id",
        "official_source_family",
    ):
        explicit.extend(string_list(first_metadata_value(pack, (key,))))
    if explicit:
        return ordered_unique([normalized_identifier(item).lower() for item in explicit if normalized_identifier(item)])

    source = pack.get("source_separation", {})
    values: list[Any] = [source_ref]
    if isinstance(source, dict):
        values.extend([source.get("training_sources"), source.get("target_sources")])
    tokens: list[str] = []
    for value in values:
        tokens.extend(source_contract_tokens_from_value(value))
    return ordered_unique(tokens)


def version_key(value: str | None) -> list[int]:
    if value is None:
        return []
    return [int(part) for part in re.findall(r"\d+", value)]


def normalized_identifier(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip()


def resolve_under_root(root: Path, ref: str) -> Path | None:
    try:
        path = (root / ref).resolve()
        path.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return path


def configured_required_domains(requirements: dict[str, Any]) -> list[str]:
    return [
        str(domain)
        for domain in requirements.get("required_domains", [])
        if str(domain).strip()
    ]


def formal_required_domains(requirements: dict[str, Any]) -> list[str]:
    configured = configured_required_domains(requirements)
    explicit = requirements.get("formal_required_domains", [])
    explicit_formal = [str(domain) for domain in explicit if str(domain).strip()] if isinstance(explicit, list) else []
    inferred_formal = [domain for domain in configured if domain in FORMAL_ROUTE_DOMAIN_SET]
    return ordered_unique([*inferred_formal, *explicit_formal])


def empirical_required_domains(requirements: dict[str, Any]) -> list[str]:
    explicit = requirements.get("empirical_required_domains")
    formal_domains = set(formal_required_domains(requirements))
    if isinstance(explicit, list):
        return [
            str(domain)
            for domain in explicit
            if str(domain).strip() and str(domain) not in formal_domains
        ]
    return [domain for domain in configured_required_domains(requirements) if domain not in formal_domains]


def all_required_domains(requirements: dict[str, Any]) -> list[str]:
    return ordered_unique([*empirical_required_domains(requirements), *formal_required_domains(requirements)])


def is_formal_only_pack(pack: dict[str, Any]) -> bool:
    """Predicate for artifacts that may support formal claims but cannot count as empirical evidence."""
    schema_id = str(pack.get("schema_id") or "")
    route_values = [
        pack.get("support_route"),
        pack.get("evidence_route"),
        pack.get("route"),
        pack.get("claim_support_scope"),
    ]
    source_assessment = pack.get("source_assessment")
    if isinstance(source_assessment, dict):
        route_values.extend(
            [
                source_assessment.get("support_route"),
                source_assessment.get("source_kind"),
                source_assessment.get("scope_statement"),
            ]
        )
    normalized_route_text = " ".join(str(value or "").lower() for value in route_values)
    return (
        schema_id.startswith("OC133_FORMAL_SUPPORT")
        or pack.get("formal_support_allowed") is True
        or pack.get("empirical_support_allowed") is False
        or "formal" in normalized_route_text
        or "proof_corpus" in normalized_route_text
        or "finite/proof" in normalized_route_text
    )


def candidate_roots(requirements: dict[str, Any]) -> list[str]:
    configured = requirements.get("candidate_evidence_pack_roots", DEFAULT_CANDIDATE_ROOTS)
    if not isinstance(configured, list):
        return list(DEFAULT_CANDIDATE_ROOTS)
    roots = [str(item) for item in configured if str(item).strip()]
    return roots or list(DEFAULT_CANDIDATE_ROOTS)


def should_skip_discovered_path(path: Path) -> bool:
    name = path.name
    if name in DISCOVERY_EXCLUDED_NAMES:
        return True
    if any(name.endswith(suffix) for suffix in DISCOVERY_EXCLUDED_SUFFIXES):
        return True
    if "samples" in {part.lower() for part in path.parts}:
        return True
    return False


def looks_like_evidence_pack(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("schema_id") == EVIDENCE_SCHEMA_ID:
        return True
    if str(payload.get("schema_id") or "").startswith("OC133_FORMAL_SUPPORT"):
        return bool(payload.get("evidence_pack_id"))
    evidence_fields = set(REQUIRED_PACK_FIELDS) - {"evidence_pack_id"}
    return "evidence_pack_id" in payload and any(field in payload for field in evidence_fields)


def load_candidate_records(
    root: Path,
    registry: dict[str, Any],
    requirements: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    records_by_ref: dict[str, dict[str, Any]] = {}
    failures: list[str] = []

    def add_ref(ref: str, origin: str) -> None:
        path = resolve_under_root(root, ref)
        if path is None:
            failures.append(f"EVIDENCE_PACK_REF_OUTSIDE_REPO::{ref}")
            return
        if not path.exists():
            failures.append(f"EVIDENCE_PACK_REF_MISSING::{ref}")
            return
        if not path.is_file():
            failures.append(f"EVIDENCE_PACK_REF_NOT_FILE::{ref}")
            return
        try:
            payload = read_json(path)
        except Exception as exc:
            failures.append(f"EVIDENCE_PACK_JSON_PARSE_FAILED::{ref}::{exc.__class__.__name__}")
            return
        if not isinstance(payload, dict):
            failures.append(f"EVIDENCE_PACK_NOT_OBJECT::{ref}")
            return
        if not looks_like_evidence_pack(payload):
            failures.append(f"EVIDENCE_PACK_REF_NOT_EVIDENCE_PACK::{ref}")
            return
        existing = records_by_ref.setdefault(
            ref,
            {
                "source_ref": ref,
                "origins": [],
                "payload": payload,
            },
        )
        existing["origins"] = ordered_unique([*existing["origins"], origin])

    for ref in registry.get("evidence_pack_refs", []):
        if not isinstance(ref, str) or not ref.strip():
            failures.append(f"EVIDENCE_PACK_REF_INVALID::{ref!r}")
            continue
        add_ref(ref.strip(), "registry")

    for root_ref in candidate_roots(requirements):
        root_path = resolve_under_root(root, root_ref)
        if root_path is None or not root_path.exists():
            continue
        for path in sorted(root_path.rglob("*.json")):
            if should_skip_discovered_path(path):
                continue
            try:
                ref = rel(root, path)
            except ValueError:
                continue
            try:
                payload = read_json(path)
            except Exception:
                continue
            if looks_like_evidence_pack(payload):
                existing = records_by_ref.setdefault(
                    ref,
                    {
                        "source_ref": ref,
                        "origins": [],
                        "payload": payload,
                    },
                )
                existing["origins"] = ordered_unique([*existing["origins"], "discovered"])

    return list(records_by_ref.values()), failures


def pack_failure_reasons(pack: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if is_formal_only_pack(pack):
        failures.append("FORMAL_SUPPORT_ROUTE_NOT_EMPIRICAL_GRAND_EVIDENCE")
    for field in REQUIRED_PACK_FIELDS:
        if field not in pack:
            failures.append(f"MISSING_FIELD::{field}")

    if pack.get("schema_id") != EVIDENCE_SCHEMA_ID:
        failures.append("SCHEMA_ID_MISMATCH")
    if pack.get("release_id") != RELEASE_ID:
        failures.append("RELEASE_ID_MISMATCH")
    if pack.get("capability_owner") != CAPABILITY_OWNER:
        failures.append("CAPABILITY_OWNER_MISMATCH")

    required_domains = set(all_required_domains(requirements))
    if pack.get("domain") not in required_domains:
        failures.append("UNKNOWN_DOMAIN")
    if pack.get("domain") in set(formal_required_domains(requirements)):
        failures.append("FORMAL_REQUIRED_DOMAIN_NOT_EMPIRICAL_EVIDENCE")

    evidence_pack_id = str(pack.get("evidence_pack_id", ""))
    if "SAMPLE" in evidence_pack_id.upper() or pack.get("sample_only") is True:
        failures.append("SAMPLE_PACK_NOT_EVIDENCE")

    source = pack.get("source_separation", {})
    if not isinstance(source, dict):
        failures.append("SOURCE_SEPARATION_NOT_OBJECT")
        source = {}
    allowed_modes = set(requirements.get("required_source_separation_modes", []))
    if source.get("mode") not in allowed_modes:
        failures.append("SOURCE_SEPARATION_MODE_NOT_ALLOWED")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    training_sources = source.get("training_sources", [])
    target_sources = source.get("target_sources", [])
    if not isinstance(training_sources, list) or not isinstance(target_sources, list):
        failures.append("TRAINING_AND_TARGET_SOURCES_MUST_BE_LISTS")
        training_sources = []
        target_sources = []
    elif not training_sources or not target_sources:
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    elif not all(isinstance(item, str) and item.strip() for item in [*training_sources, *target_sources]):
        failures.append("TRAINING_AND_TARGET_SOURCES_MUST_BE_NONEMPTY_STRINGS")
    if len(set(training_sources)) != len(training_sources) or len(set(target_sources)) != len(target_sources):
        failures.append("TRAINING_OR_TARGET_SOURCE_DUPLICATE")
    if set(training_sources) & set(target_sources):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")

    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    n = pack.get("n")
    if not isinstance(n, int) or isinstance(n, bool):
        failures.append("N_NOT_INTEGER")
    elif n < minimum_n:
        failures.append(f"N_BELOW_MINIMUM::{minimum_n}")

    comparator = pack.get("comparator_baseline", {})
    if not isinstance(comparator, dict):
        failures.append("COMPARATOR_BASELINE_NOT_OBJECT")
        comparator = {}
    if not comparator.get("name") or not comparator.get("prediction_rule"):
        failures.append("COMPARATOR_BASELINE_INCOMPLETE")
    if comparator.get("pre_registered") is not True:
        failures.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")

    uncertainty = pack.get("uncertainty", {})
    if not isinstance(uncertainty, dict):
        failures.append("UNCERTAINTY_NOT_OBJECT")
        uncertainty = {}
    interval = uncertainty.get("interval")
    interval_valid = (
        bool(uncertainty.get("metric"))
        and bool(uncertainty.get("method"))
        and isinstance(interval, list)
        and len(interval) == 2
        and all(is_number(value) for value in interval)
    )
    if not interval_valid:
        failures.append("UNCERTAINTY_INTERVAL_INCOMPLETE")
        interval = None
    elif float(interval[0]) > float(interval[1]):
        failures.append("UNCERTAINTY_INTERVAL_NOT_ORDERED")

    residuals = pack.get("residuals", {})
    if not isinstance(residuals, dict):
        failures.append("RESIDUALS_NOT_OBJECT")
        residuals = {}
    missing_residual_fields = [
        field
        for field in ("model", "comparator", "superiority_margin")
        if field not in residuals
    ]
    if missing_residual_fields:
        failures.append(f"RESIDUAL_FIELDS_MISSING::{','.join(missing_residual_fields)}")
    model_residual = residuals.get("model")
    comparator_residual = residuals.get("comparator")
    superiority_margin = residuals.get("superiority_margin")
    if not is_number(model_residual) or float(model_residual) < 0:
        failures.append("MODEL_RESIDUAL_INVALID")
    if not is_number(comparator_residual) or float(comparator_residual) < 0:
        failures.append("COMPARATOR_RESIDUAL_INVALID")
    if not is_number(superiority_margin):
        failures.append("SUPERIORITY_MARGIN_INVALID")
    if is_number(model_residual) and is_number(comparator_residual):
        if float(comparator_residual) <= float(model_residual):
            failures.append("COMPARATOR_NOT_WORSE_THAN_MODEL")
        if interval_valid and float(interval[0]) <= float(interval[1]):
            if not (float(interval[0]) <= float(model_residual) <= float(interval[1])):
                failures.append("MODEL_RESIDUAL_OUTSIDE_UNCERTAINTY_INTERVAL")
    if is_number(model_residual) and is_number(comparator_residual) and is_number(superiority_margin):
        expected_margin = float(comparator_residual) - float(model_residual)
        if float(superiority_margin) <= 0:
            failures.append("SUPERIORITY_MARGIN_NOT_POSITIVE")
        if abs(float(superiority_margin) - expected_margin) > 1e-9:
            failures.append("SUPERIORITY_MARGIN_MISMATCH")

    negative_controls = pack.get("negative_controls", [])
    if not isinstance(negative_controls, list) or not negative_controls:
        failures.append("NEGATIVE_CONTROL_REQUIRED")
    else:
        for idx, row in enumerate(negative_controls):
            if not isinstance(row, dict):
                failures.append(f"NEGATIVE_CONTROL_NOT_OBJECT::{idx}")
                continue
            if not row.get("control_id") or not row.get("description"):
                failures.append(f"NEGATIVE_CONTROL_INCOMPLETE::{idx}")
            if row.get("rejected") is not True:
                failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{idx}")

    falsifiers = pack.get("falsifiers", [])
    if not isinstance(falsifiers, list) or not falsifiers:
        failures.append("FALSIFIER_REQUIRED")
    elif not all(isinstance(row, str) and row.strip() for row in falsifiers):
        failures.append("FALSIFIER_REQUIRED")

    if "grand_toe_support_allowed" not in pack:
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_NOT_EXPLICIT")
    elif not isinstance(pack.get("grand_toe_support_allowed"), bool):
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_NOT_BOOLEAN")
    elif pack.get("grand_toe_support_allowed") is not True:
        failures.append("GRAND_TOE_SUPPORT_NOT_ALLOWED")

    failures.extend(biology_specific_failure_reasons(pack, requirements))
    return ordered_unique(failures)


def _version_sort_tuple(row: dict[str, Any]) -> tuple[int, ...]:
    key = [int(item) for item in row.get("pack_version_key", []) if isinstance(item, int)]
    return tuple(-item for item in (key + [0, 0, 0, 0, 0, 0])[:6])


def biology_target_successor_row(row: dict[str, Any]) -> bool:
    if row.get("domain") != "biology" or row.get("valid_for_grand_support") is not True:
        return False
    row_total = row.get("biology_target_row_total")
    if not isinstance(row_total, int) or row_total <= 0:
        return False
    if not row.get("biology_target_artifact_ref_hashes"):
        return False
    combined = text_blob(
        row.get("evidence_pack_id"),
        row.get("evidence_family"),
        row.get("source_contracts"),
        row.get("source_ref"),
    )
    return "biology-target" in combined or "biological-target" in combined or "official_biology_target_bundle" in combined


def bounded_biology_pagination_or_template_row(row: dict[str, Any]) -> bool:
    if row.get("domain") != "biology" or row.get("valid_for_grand_support") is True:
        return False
    failures = [str(item) for item in row.get("failures", []) if isinstance(item, str)]
    combined = text_blob(
        row.get("source_ref"),
        row.get("evidence_pack_id"),
        row.get("evidence_family"),
        row.get("source_contracts"),
        failures,
    )
    bounded_marker = (
        "ncbi" in combined
        or "pagination" in combined
        or "retmax" in combined
        or "idlist" in combined
        or "esearch" in combined
        or "candidate_pack_template" in combined
        or "bounded-acquisition-template" in combined
        or "source-template" in combined
        or "source_template" in combined
        or "biology_systems" in combined
    )
    pagination_failure = any(
        failure.startswith("BIOLOGY_PAGINATION_QA_NOT_GRAND_EVIDENCE")
        or failure.startswith("BIOLOGY_COMPARATOR_STRUCTURALLY_SILLY_OR_PAGINATION_ONLY")
        or failure.startswith("BIOLOGY_TARGET_KIND_IS_API_PAGINATION")
        for failure in failures
    )
    if not bounded_marker or not pagination_failure:
        return False
    target_row_total = row.get("biology_target_row_total")
    if isinstance(target_row_total, int) and target_row_total > 0:
        return pagination_failure
    return True


def apply_candidate_supersession(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    identifiers: dict[str, list[int]] = {}
    superseded_by: dict[int, list[str]] = {idx: [] for idx in range(len(rows))}
    supersession_reasons: dict[int, list[str]] = {idx: [] for idx in range(len(rows))}

    for idx, row in enumerate(rows):
        for identifier in (row.get("evidence_pack_id"), row.get("source_ref")):
            normalized = normalized_identifier(identifier)
            if not normalized:
                continue
            identifiers.setdefault(normalized, []).append(idx)

    for successor_idx, row in enumerate(rows):
        if row.get("valid_for_grand_support") is not True:
            continue
        successor_id = str(row["evidence_pack_id"])
        successor_domain = row.get("domain")
        for target in row.get("supersedes", []):
            for target_idx in identifiers.get(normalized_identifier(target), []):
                if target_idx == successor_idx:
                    continue
                if rows[target_idx].get("domain") != successor_domain:
                    continue
                superseded_by[target_idx] = ordered_unique([*superseded_by[target_idx], successor_id])
                supersession_reasons[target_idx] = ordered_unique(
                    [*supersession_reasons[target_idx], f"EXPLICIT_SUPERSESSION::{successor_id}"]
                )

    family_groups: dict[tuple[str, str, str], list[int]] = {}
    for idx, row in enumerate(rows):
        family = row.get("evidence_family")
        contracts = row.get("source_contracts", [])
        version = row.get("pack_version_key")
        domain = row.get("domain")
        if not domain or not family or not contracts or not version:
            continue
        for contract in contracts:
            family_groups.setdefault((str(domain), str(family), str(contract)), []).append(idx)

    for (domain, family, contract), group in family_groups.items():
        if domain == "biology" and contract == "official_biology_target_bundle":
            continue
        for idx in group:
            row_version = rows[idx].get("pack_version_key", [])
            higher = [
                other_idx
                for other_idx in group
                if rows[other_idx].get("pack_version_key", []) > row_version
                and rows[other_idx].get("valid_for_grand_support") is True
            ]
            for successor_idx in sorted(higher, key=lambda item: (rows[item]["pack_version_key"], rows[item]["source_ref"])):
                successor_id = str(rows[successor_idx]["evidence_pack_id"])
                superseded_by[idx] = ordered_unique([*superseded_by[idx], successor_id])
                supersession_reasons[idx] = ordered_unique(
                    [
                        *supersession_reasons[idx],
                        f"FAMILY_VERSION_SOURCE_CONTRACT_SUPERSESSION::{domain}::{family}::{contract}::{successor_id}",
                    ]
                )

    contract_groups: dict[tuple[str, str], list[int]] = {}
    for idx, row in enumerate(rows):
        domain = row.get("domain")
        if not domain:
            continue
        for contract in row.get("source_contracts", []):
            contract_groups.setdefault((str(domain), str(contract)), []).append(idx)

    for (domain, contract), group in contract_groups.items():
        if domain == "biology" and contract == "official_biology_target_bundle":
            continue
        valid_successors = [
            idx
            for idx in group
            if rows[idx].get("valid_for_grand_support") is True
        ]
        for idx in group:
            if rows[idx].get("valid_for_grand_support") is True:
                continue
            for successor_idx in sorted(
                valid_successors,
                key=lambda item: (
                    -int(rows[item].get("n") or 0) if isinstance(rows[item].get("n"), int) else 0,
                    rows[item]["source_ref"],
                ),
            ):
                if successor_idx == idx:
                    continue
                successor_id = str(rows[successor_idx]["evidence_pack_id"])
                superseded_by[idx] = ordered_unique([*superseded_by[idx], successor_id])
                supersession_reasons[idx] = ordered_unique(
                    [
                        *supersession_reasons[idx],
                        f"SOURCE_CONTRACT_VALID_SUCCESSOR_SUPERSESSION::{domain}::{contract}::{successor_id}",
                    ]
                )

    biology_successors = [
        idx
        for idx, row in enumerate(rows)
        if biology_target_successor_row(row)
    ]
    for idx, row in enumerate(rows):
        if not bounded_biology_pagination_or_template_row(row):
            continue
        for successor_idx in sorted(
            biology_successors,
            key=lambda item: (
                -int(rows[item].get("n") or 0) if isinstance(rows[item].get("n"), int) else 0,
                rows[item]["source_ref"],
            ),
        ):
            if successor_idx == idx:
                continue
            successor = rows[successor_idx]
            artifact_pair = str(successor.get("biology_target_artifact_ref_hashes", [""])[0])
            successor_id = str(successor["evidence_pack_id"])
            superseded_by[idx] = ordered_unique([*superseded_by[idx], successor_id])
            supersession_reasons[idx] = ordered_unique(
                [
                    *supersession_reasons[idx],
                    f"BIOLOGY_TARGET_VALID_SUCCESSOR_SUPERSESSION::{successor_id}::{artifact_pair}",
                ]
            )

    for idx, row in enumerate(rows):
        row["superseded_by"] = superseded_by[idx]
        row["supersession_reasons"] = supersession_reasons[idx]
        row["supersession_status"] = "superseded" if superseded_by[idx] else "current"
        row["selected_for_domain_support"] = (
            row.get("valid_for_grand_support") is True and row["supersession_status"] == "current"
        )

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            str(row.get("domain") or ""),
            1 if row.get("supersession_status") == "superseded" else 0,
            -len(row.get("supersedes", [])),
            _version_sort_tuple(row),
            0 if row.get("valid_for_grand_support") is True else 1,
            str(row.get("source_ref") or ""),
        ),
    )
    for rank, row in enumerate(sorted_rows, start=1):
        row["candidate_preference_rank"] = rank
    return sorted_rows


def candidate_rows(records: list[dict[str, Any]], requirements: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_ids: dict[str, int] = {}
    for record in records:
        pack = record["payload"]
        pack_id = str(pack.get("evidence_pack_id") or record["source_ref"])
        seen_ids[pack_id] = seen_ids.get(pack_id, 0) + 1

    for record in records:
        pack = record["payload"]
        pack_id = str(pack.get("evidence_pack_id") or record["source_ref"])
        failures = pack_failure_reasons(pack, requirements)
        if seen_ids.get(pack_id, 0) > 1:
            failures.append("DUPLICATE_EVIDENCE_PACK_ID")
        failures = ordered_unique(failures)
        residuals = pack.get("residuals", {}) if isinstance(pack.get("residuals"), dict) else {}
        family = pack_family(pack)
        version = pack_version(pack)
        target_rows = biology_target_rows(pack)
        artifact_pairs = source_hash_artifact_pairs(pack)
        empirical_domain_candidate_support_allowed = not failures and pack.get("grand_toe_support_allowed") is True
        row = {
            "source_ref": record["source_ref"],
            "origins": record["origins"],
            "evidence_pack_id": pack_id,
            "domain": pack.get("domain"),
            "formal_only_pack": is_formal_only_pack(pack),
            "evidence_family": family,
            "source_contracts": pack_source_contracts(pack, record["source_ref"]),
            "pack_version": version,
            "pack_version_key": version_key(version),
            "supersedes": pack_supersedes(pack),
            "biology_target_row_total": len(target_rows) if pack.get("domain") == "biology" else 0,
            "biology_target_artifact_ref_hash_total": len(artifact_pairs) if pack.get("domain") == "biology" else 0,
            "biology_target_artifact_ref_hashes": artifact_pairs if pack.get("domain") == "biology" else [],
            "n": pack.get("n"),
            "source_separation_mode": (pack.get("source_separation") or {}).get("mode") if isinstance(pack.get("source_separation"), dict) else None,
            "model_residual": residuals.get("model"),
            "comparator_residual": residuals.get("comparator"),
            "superiority_margin": residuals.get("superiority_margin"),
            "input_pack_grand_toe_support_allowed": pack.get("grand_toe_support_allowed"),
            "empirical_domain_support_allowed": empirical_domain_candidate_support_allowed,
            "grand_toe_support_allowed": False,
            "grand_toe_support_scope": (
                "false in factory output; source pack field is treated only as an input requirement for "
                "empirical-domain evidence eligibility"
            ),
            "candidate_sha256": sha256_object(pack),
            "valid_for_grand_support": not failures,
            "valid_for_empirical_domain_support": not failures,
            "failure_total": len(failures),
            "failures": failures,
        }
        rows.append(row)
    return apply_candidate_supersession(rows)


def valid_packs_for_domain(
    domain: str,
    records: list[dict[str, Any]],
    candidate_report_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid_refs = {
        row["source_ref"]
        for row in candidate_report_rows
        if row.get("domain") == domain and row.get("valid_for_grand_support") is True
        and row.get("supersession_status") != "superseded"
    }
    return [record["payload"] for record in records if record["source_ref"] in valid_refs]


def bounded_baseline_rows(root: Path) -> list[dict[str, Any]]:
    target_blind_path = root / TARGET_BLIND_REL
    if not target_blind_path.exists():
        return []
    payload = read_json(target_blind_path)
    rows: list[dict[str, Any]] = []
    for row in payload.get("rows", []):
        residual = as_float(row.get("residual"))
        comparator_residual = as_float(row.get("comparator_residual"))
        rows.append(
            {
                "evidence_pack_id": row.get("claim_id"),
                "domain": row.get("lane"),
                "source_ref": TARGET_BLIND_REL,
                "source_separation_mode": "target_blind",
                "n": 1,
                "model_under_test": row.get("formula"),
                "comparator_baseline": row.get("comparator_baseline"),
                "uncertainty": row.get("uncertainty"),
                "model_residual": residual,
                "comparator_residual": comparator_residual,
                "superiority_margin": comparator_residual - residual,
                "negative_control_rejected": row.get("negative_control_rejected") is True,
                "falsifier": row.get("falsifier"),
                "grand_toe_support_allowed": False,
                "support_scope": row.get("support_scope"),
                "classification": "BOUNDED_BASELINE_NOT_GRAND_SUPPORT",
            }
        )
    return rows


def summarize_domain(
    domain: str,
    records: list[dict[str, Any]],
    candidate_report_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    domain_candidates = [row for row in candidate_report_rows if row.get("domain") == domain]
    current_domain_candidates = [row for row in domain_candidates if row.get("supersession_status") != "superseded"]
    superseded_domain_candidates = [row for row in domain_candidates if row.get("supersession_status") == "superseded"]
    valid_packs = valid_packs_for_domain(domain, records, candidate_report_rows)
    baseline = [row for row in baseline_rows if row.get("domain") == domain]
    valid_n = sum(int(pack.get("n", 0)) for pack in valid_packs)
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    blockers: list[str] = []
    if valid_n < minimum_n:
        blockers.append(f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{valid_n}/{minimum_n}")
    if not valid_packs:
        blockers.append("NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK")
    if not domain_candidates:
        blockers.append("NO_CANDIDATE_EVIDENCE_PACK_DISCOVERED")
    elif not current_domain_candidates:
        blockers.append("NO_CURRENT_CANDIDATE_EVIDENCE_PACK")
    else:
        invalid_total = sum(1 for row in current_domain_candidates if row.get("valid_for_grand_support") is not True)
        if invalid_total:
            blockers.append(f"CANDIDATE_EVIDENCE_PACKS_INVALID::{invalid_total}")
    if domain == "mathematics" and not valid_packs and baseline:
        blockers.append("CURRENT_FORMAL_CORPUS_BASELINE_IS_NOT_EMPIRICAL_GRAND_SCIENCE_EVIDENCE")

    support_allowed = not blockers and bool(valid_packs)
    return {
        "domain": domain,
        "candidate_pack_total": len(domain_candidates),
        "current_candidate_pack_total": len(current_domain_candidates),
        "superseded_candidate_pack_total": len(superseded_domain_candidates),
        "registered_pack_total": sum(1 for row in domain_candidates if "registry" in row.get("origins", [])),
        "discovered_pack_total": sum(1 for row in domain_candidates if "discovered" in row.get("origins", [])),
        "valid_pack_total": len(valid_packs),
        "valid_pack_refs": [
            row["source_ref"]
            for row in current_domain_candidates
            if row.get("valid_for_grand_support") is True
        ],
        "superseded_pack_refs": [row["source_ref"] for row in superseded_domain_candidates],
        "valid_n": valid_n,
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - valid_n),
        "bounded_baseline_row_total": len(baseline),
        "bounded_baseline_refs": [row["evidence_pack_id"] for row in baseline],
        "empirical_domain_support_allowed": support_allowed,
        "empirical_domain_predictive_superiority_supported": support_allowed,
        "grand_toe_support_allowed": False,
        "grand_toe_support_scope": (
            "false at the empirical gate; TOE/final/broad modern-science promotion is audited only by "
            "the formal grand-claim and modern-science comparator gates"
        ),
        "status": "EVIDENCE_SUFFICIENT_PENDING_REVIEW" if support_allowed else "BLOCKED",
        "blockers": blockers,
    }


def formal_route_rows(requirements: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain in formal_required_domains(requirements):
        report_ref = MATHEMATICS_FORMAL_SUPPORT_REPORT_REL if domain == "mathematics" else None
        rows.append(
            {
                "domain": domain,
                "support_route": "formal",
                "status": "ROUTED_TO_FORMAL_SUPPORT",
                "empirical_support_allowed": False,
                "grand_empirical_support_allowed": False,
                "formal_support_report_ref": report_ref,
                "route_separation_policy": (
                    "Formal support is audited by release readiness and must not be counted as grand empirical evidence."
                ),
            }
        )
    return rows


def decomposition_queue_rows(domains: list[dict[str, Any]], requirements: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain_row in domains:
        if domain_row.get("status") != "BLOCKED":
            continue
        domain = str(domain_row["domain"])
        rows.append(
            {
                "queue_id": f"OC133-GRAND-EMPIRICAL-DECOMP-{domain.upper()}",
                "blocker_id": "grand_toe_empirical_superiority",
                "domain": domain,
                "owner_capability": CAPABILITY_OWNER,
                "status": "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
                "current_valid_n": domain_row.get("valid_n"),
                "minimum_n": domain_row.get("minimum_n"),
                "missing_n": domain_row.get("missing_n"),
                "domain_blockers": domain_row.get("blockers", []),
                "required_protocol_steps": [
                    "pre-register the OC model, comparator baseline, residual metric, uncertainty method, negative controls, and falsifiers before target scoring",
                    "freeze training/source-development material separately from target/held-out sources and record stable hashes",
                    "keep target values hidden until scoring is complete, or use a genuinely prospective target source",
                    "collect at least the configured per-domain N with no training/target source overlap",
                    "score OC residuals and comparator residuals under the same metric and uncertainty protocol",
                    "reject every declared negative control and retain falsifier conditions even when the candidate fails",
                    "register the final evidence pack in validation/heldout/grand_science_evidence_registry.json only after the pack is complete",
                ],
                "required_pack_fields": list(REQUIRED_PACK_FIELDS),
                "sample_pack_ref": SAMPLE_PACK_REL,
                "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
                "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
                "registry_ref": REGISTRY_REL,
            }
        )
    return rows


def build_grand_empirical_payload(root: Path) -> dict[str, Any]:
    requirements = read_json(root / REQUIREMENTS_REL)
    registry = read_json(root / REGISTRY_REL)
    records, registry_failures = load_candidate_records(root, registry, requirements)
    candidates = candidate_rows(records, requirements)
    baseline_rows = bounded_baseline_rows(root)
    empirical_domains = empirical_required_domains(requirements)
    formal_domains = formal_required_domains(requirements)
    formal_routes = formal_route_rows(requirements)
    domains = [
        summarize_domain(domain, records, candidates, baseline_rows, requirements)
        for domain in empirical_domains
    ]
    queue_rows = decomposition_queue_rows(domains, requirements)
    blocked_total = sum(1 for row in domains if row["status"] == "BLOCKED")
    empirical_domain_support_allowed = blocked_total == 0 and all(
        row["empirical_domain_support_allowed"] is True for row in domains
    )
    pack_failures = {
        str(row["evidence_pack_id"]): row["failures"]
        for row in candidates
        if row.get("failures")
    }
    registered_refs = {
        str(ref)
        for ref in registry.get("evidence_pack_refs", [])
        if isinstance(ref, str)
    }
    payload = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_by": "validation/grand_science/run_grand_empirical_gate.py",
        "factory_module": "validation/grand_science/evidence_pack_factory.py",
        "capability_owner": CAPABILITY_OWNER,
        "requirements_ref": REQUIREMENTS_REL,
        "schema_ref": EVIDENCE_SCHEMA_REL,
        "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
        "heldout_registry_ref": REGISTRY_REL,
        "candidate_scan_ref": SCAN_REL,
        "decomposition_queue_ref": QUEUE_REL,
        "sample_pack_ref": SAMPLE_PACK_REL,
        "bounded_baseline_ref": TARGET_BLIND_REL,
        "candidate_evidence_pack_roots": candidate_roots(requirements),
        "configured_required_domains": configured_required_domains(requirements),
        "required_domains": empirical_domains,
        "empirical_required_domains": empirical_domains,
        "formal_required_domains": formal_domains,
        "formal_route_status": formal_routes,
        "formal_route_policy": "Formal required domains are exposed here as dependencies, but excluded from empirical support counts and blockers.",
        "evidence_pack_total": len(candidates),
        "registered_evidence_pack_total": sum(1 for row in candidates if row["source_ref"] in registered_refs),
        "discovered_evidence_pack_total": sum(1 for row in candidates if "discovered" in row.get("origins", [])),
        "current_evidence_pack_total": sum(1 for row in candidates if row.get("supersession_status") != "superseded"),
        "superseded_evidence_pack_total": sum(1 for row in candidates if row.get("supersession_status") == "superseded"),
        "valid_evidence_pack_total": sum(1 for row in candidates if row.get("selected_for_domain_support") is True),
        "bounded_baseline_row_total": len(baseline_rows),
        "registry_failure_total": len(registry_failures),
        "registry_failures": registry_failures,
        "evidence_pack_failure_total": sum(1 for row in candidates if row.get("failure_total", 0)),
        "current_evidence_pack_failure_total": sum(
            1
            for row in candidates
            if row.get("failure_total", 0) and row.get("supersession_status") != "superseded"
        ),
        "evidence_pack_failures": pack_failures,
        "candidate_rows": candidates,
        "domain_total": len(domains),
        "empirical_domain_total": len(domains),
        "formal_required_domain_total": len(formal_domains),
        "blocked_domain_total": blocked_total,
        "blocked_empirical_domain_total": blocked_total,
        "domains": domains,
        "bounded_baseline_rows": baseline_rows,
        "decomposition_queue_total": len(queue_rows),
        "decomposition_queue": queue_rows,
        "empirical_domain_support_allowed": empirical_domain_support_allowed,
        "empirical_domain_predictive_superiority_supported": empirical_domain_support_allowed,
        "domain_predictive_superiority_supported": empirical_domain_support_allowed,
        "grand_toe_support_allowed": False,
        "grand_toe_support_scope": (
            "false at the empirical gate; empirical-domain support is not TOE/final-theory promotion and does not "
            "claim broad modern-science superiority"
        ),
        "grand_toe_claim_promotion_allowed": False,
        "final_theory_or_toe_promotion_allowed": False,
        "broad_modern_science_coverage_promotion_allowed": False,
        "modern_science_superiority_promotion_allowed": False,
        "verdict": "EMPIRICAL_DOMAIN_SUPPORT_ALLOWED"
        if empirical_domain_support_allowed
        else "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE",
        "support_policy": requirements["support_policy"],
        "no_fabricated_pass_policy": "This factory/gate emits only bounded empirical-domain support from qualifying packs. It does not emit TOE, final-theory, broad modern-science coverage, or modern-science superiority promotion from bounded OC133 reconstructions, sample packs, or artifact existence. Unresolved domains remain BLOCKED until prospective or target-blind evidence packs clear the configured criteria.",
    }
    return payload


def candidate_scan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out = {
        "schema_id": FACTORY_SCAN_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "requirements_ref": payload["requirements_ref"],
        "registry_ref": payload["heldout_registry_ref"],
        "candidate_evidence_pack_roots": payload["candidate_evidence_pack_roots"],
        "configured_required_domains": payload["configured_required_domains"],
        "empirical_required_domains": payload["empirical_required_domains"],
        "formal_required_domains": payload["formal_required_domains"],
        "formal_route_status": payload["formal_route_status"],
        "candidate_total": payload["evidence_pack_total"],
        "current_candidate_total": payload["current_evidence_pack_total"],
        "superseded_candidate_total": payload["superseded_evidence_pack_total"],
        "valid_candidate_total": payload["valid_evidence_pack_total"],
        "failure_total": payload["evidence_pack_failure_total"],
        "current_failure_total": payload["current_evidence_pack_failure_total"],
        "registry_failure_total": payload["registry_failure_total"],
        "registry_failures": payload["registry_failures"],
        "sample_pack_excluded_from_discovery": True,
        "sample_pack_ref": payload["sample_pack_ref"],
        "rows": payload["candidate_rows"],
    }
    for key in ("generated_at", "sync_run_id", "gate_run_id", "source_artifact_set_sha256", "source_artifact_hashes"):
        if key in payload:
            out[key] = payload[key]
    return out


def decomposition_queue_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out = {
        "schema_id": DECOMPOSITION_QUEUE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": "grand_toe_empirical_superiority",
        "verdict": payload["verdict"],
        "blocked_domain_total": payload["blocked_domain_total"],
        "blocked_empirical_domain_total": payload["blocked_empirical_domain_total"],
        "queue_total": payload["decomposition_queue_total"],
        "requirements_ref": payload["requirements_ref"],
        "empirical_required_domains": payload["empirical_required_domains"],
        "formal_required_domains": payload["formal_required_domains"],
        "formal_route_status": payload["formal_route_status"],
        "evidence_schema_ref": payload["schema_ref"],
        "protocol_schema_ref": payload["protocol_schema_ref"],
        "sample_pack_ref": payload["sample_pack_ref"],
        "rows": payload["decomposition_queue"],
    }
    for key in ("generated_at", "sync_run_id", "gate_run_id", "source_artifact_set_sha256", "source_artifact_hashes"):
        if key in payload:
            out[key] = payload[key]
    return out


def write_markdown(root: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Grand Empirical Report",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Empirical-domain support allowed: `{str(payload['empirical_domain_support_allowed']).lower()}`",
        f"TOE/final/broad modern-science promotion allowed by this gate: `{str(payload['final_theory_or_toe_promotion_allowed']).lower()}`",
        f"Candidate evidence packs: `{payload['evidence_pack_total']}`",
        f"Current evidence packs: `{payload['current_evidence_pack_total']}`",
        f"Superseded evidence packs: `{payload['superseded_evidence_pack_total']}`",
        f"Valid evidence packs: `{payload['valid_evidence_pack_total']}`",
        f"Bounded baseline rows: `{payload['bounded_baseline_row_total']}`",
        f"Blocked empirical domains: `{payload['blocked_empirical_domain_total']}/{payload['empirical_domain_total']}`",
        f"Formal required domains: `{payload['formal_required_domain_total']}`",
        f"Decomposition queue rows: `{payload['decomposition_queue_total']}`",
        f"Sync run: `{payload.get('sync_run_id', 'not-bound')}`",
        f"Source artifact set: `{payload.get('source_artifact_set_sha256', 'not-bound')}`",
        "",
        payload["no_fabricated_pass_policy"],
        payload["formal_route_policy"],
        "",
        "| Domain | Status | Candidate packs | Current packs | Superseded packs | Valid packs | Valid N | Minimum N | Bounded baseline rows | Empirical-domain support | TOE/final promotion | Blockers |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in payload["domains"]:
        blockers = "; ".join(row["blockers"])
        lines.append(
            f"| `{row['domain']}` | `{row['status']}` | `{row['candidate_pack_total']}` | "
            f"`{row['current_candidate_pack_total']}` | `{row['superseded_candidate_pack_total']}` | "
            f"`{row['valid_pack_total']}` | `{row['valid_n']}` | `{row['minimum_n']}` | `{row['bounded_baseline_row_total']}` | "
            f"`{str(row['empirical_domain_support_allowed']).lower()}` | `{str(row['grand_toe_support_allowed']).lower()}` | {blockers} |"
        )
    lines.extend(
        [
            "",
            "## Formal Route Dependencies",
            "",
            "| Domain | Route | Status | Empirical support allowed | Formal support report |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["formal_route_status"]:
        lines.append(
            f"| `{row['domain']}` | `{row['support_route']}` | `{row['status']}` | "
            f"`{str(row['empirical_support_allowed']).lower()}` | {row.get('formal_support_report_ref') or ''} |"
        )
    lines.extend(
        [
            "",
            "## Candidate Factory",
            "",
            f"Candidate scan: `{payload['candidate_scan_ref']}`",
            f"Decomposition queue: `{payload['decomposition_queue_ref']}`",
            f"Sample-only pack: `{payload['sample_pack_ref']}`",
            "",
            "## Bounded Baseline",
            "",
            "Current target-blind rows are retained as bounded reconstruction evidence only. They are not promoted to broad domain validation, TOE/final-theory support, or modern-science superiority.",
            "",
            "| Domain | Baseline ID | N | Model residual | Comparator residual | Support scope |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["bounded_baseline_rows"]:
        lines.append(
            f"| `{row['domain']}` | `{row['evidence_pack_id']}` | `{row['n']}` | "
            f"`{row['model_residual']}` | `{row['comparator_residual']}` | {row.get('support_scope') or ''} |"
        )
    report_path = root / REPORT_MD_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_grand_empirical_outputs(root: Path, payload: dict[str, Any]) -> None:
    write_json(root / REPORT_JSON_REL, payload)
    write_json(root / SCAN_REL, candidate_scan_payload(payload))
    write_json(root / QUEUE_REL, decomposition_queue_payload(payload))
    write_markdown(root, payload)
