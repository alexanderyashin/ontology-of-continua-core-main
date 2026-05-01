from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
SCHEMA_ID = "OC133_TARGET_PROJECTION_LOCK_REPORT_v1"
VISIBLE_LOCK_SCHEMA_ID = "OC133_VISIBLE_PROJECTION_LOCK_v1"
TARGET_LOCK_SCHEMA_ID = "OC133_TARGET_PROJECTION_LOCK_v1"
PREDICTION_LOCK_SCHEMA_ID = "OC133_TARGET_BLIND_PREDICTION_MATERIALIZATION_LOCK_v1"

DEFAULT_DECLARATION_GLOB = "validation/heldout/target_projection_locks/declarations/*.json"
OUTPUT_ROOT_REL = "validation/heldout/target_projection_locks"
REPORT_JSON_REL = f"{OUTPUT_ROOT_REL}/OC133_TARGET_PROJECTION_LOCK_REPORT.json"
LOCK_ROOT_REL = f"{OUTPUT_ROOT_REL}/locks"

NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "push_allowed": False,
    "journal_submissions_allowed": False,
    "doi_registration_allowed": False,
    "zenodo_upload_allowed": False,
    "registry_write_allowed": False,
    "release_promotion_allowed": False,
}

EXPECTED_HASH_KEYS = {
    "expected_declaration_sha256",
    "expected_declaration_hash",
    "expected_snapshot_sha256",
    "expected_visible_projection_sha256",
    "expected_target_projection_sha256",
    "expected_prediction_materialization_sha256",
}


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_object(payload: Any) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def safe_lock_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._")
    return cleaned[:120] or "target_projection_lock"


def path_parts(path: str) -> tuple[str, ...]:
    return tuple(part for part in str(path).split(".") if part)


def paths_overlap(left: str, right: str) -> bool:
    left_parts = path_parts(left)
    right_parts = path_parts(right)
    if not left_parts or not right_parts:
        return False
    shorter = min(len(left_parts), len(right_parts))
    return left_parts[:shorter] == right_parts[:shorter]


def get_path(payload: Any, dotted_path: str) -> Any:
    current = payload
    for part in path_parts(dotted_path):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if 0 <= index < len(current):
                current = current[index]
                continue
        raise KeyError(dotted_path)
    return current


def declaration_payload_for_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in EXPECTED_HASH_KEYS}


def load_snapshot(path: Path, snapshot_format: str, row_path: str | None) -> list[Any]:
    fmt = snapshot_format.lower()
    if fmt == "auto":
        fmt = "ndjson" if path.suffix.lower() in {".ndjson", ".jsonl"} else "json"
    if fmt == "ndjson":
        rows = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"NDJSON_PARSE_ERROR::line_{line_number}") from exc
        return rows
    if fmt != "json":
        raise ValueError(f"UNSUPPORTED_SNAPSHOT_FORMAT::{snapshot_format}")
    payload = read_json(path)
    if row_path:
        rows = get_path(payload, row_path)
        if not isinstance(rows, list):
            raise ValueError(f"ROW_PATH_NOT_LIST::{row_path}")
        return rows
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for candidate in ("rows", "records", "data"):
            value = payload.get(candidate)
            if isinstance(value, list):
                return value
        return [payload]
    raise ValueError("SNAPSHOT_ROOT_NOT_ROWS")


def required_list(payload: dict[str, Any], key: str, blockers: list[str]) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        blockers.append(f"{key.upper()}_MISSING_OR_INVALID")
        return []
    return [str(item).strip() for item in value]


def no_send_lock_blockers(payload: dict[str, Any]) -> list[str]:
    locks = payload.get("locks")
    if not isinstance(locks, dict):
        return ["NO_SEND_LOCKS_MISSING"]
    blockers = []
    for key, expected in NO_SEND_LOCKS.items():
        if locks.get(key) is not expected:
            blockers.append(f"NO_SEND_LOCK_MISSING_OR_WEAK::{key}")
    return blockers


def declaration_paths_from_args(root: Path, declaration_args: list[str]) -> list[Path]:
    if declaration_args:
        return [resolve_under_root(root, ref) for ref in declaration_args]
    return sorted(root.glob(DEFAULT_DECLARATION_GLOB))


def included_by_rule(row: Any, row_index: int, rule: dict[str, Any]) -> bool:
    if rule.get("include_all") is True:
        return True
    if "indices" in rule:
        indices = rule.get("indices")
        return isinstance(indices, list) and row_index in indices
    field = rule.get("field")
    if not isinstance(field, str) or not field.strip():
        return False
    try:
        value = get_path(row, field)
    except KeyError:
        return False
    if "equals" in rule:
        return value == rule.get("equals")
    if "in" in rule:
        allowed = rule.get("in")
        return isinstance(allowed, list) and value in allowed
    if rule.get("exists") is True:
        return True
    if rule.get("not_null") is True:
        return value is not None
    return False


def row_id_for(row: Any, row_index: int, row_id_field: str | None) -> str:
    if row_id_field:
        try:
            value = get_path(row, row_id_field)
            if value is not None:
                return str(value)
        except KeyError:
            pass
    return str(row_index)


def project_row(row: Any, fields: list[str], *, missing_prefix: str, blockers: list[str]) -> dict[str, Any]:
    projection: dict[str, Any] = {}
    for field in fields:
        try:
            projection[field] = get_path(row, field)
        except KeyError:
            blockers.append(f"{missing_prefix}::{field}")
    return projection


def as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def visible_number(visible: dict[str, Any], field: str, blockers: list[str], prefix: str) -> float:
    if field not in visible:
        blockers.append(f"{prefix}_REFERENCES_NON_VISIBLE_FIELD::{field}")
        return 0.0
    value = as_number(visible[field])
    if value is None:
        blockers.append(f"{prefix}_FIELD_NOT_NUMERIC::{field}")
        return 0.0
    return value


def materialize_declared_prediction(
    declaration: dict[str, Any],
    visible: dict[str, Any],
    blockers: list[str],
    prefix: str,
) -> float | None:
    kind = str(declaration.get("kind") or declaration.get("type") or "").lower()
    if kind == "constant":
        value = as_number(declaration.get("value"))
        if value is None:
            blockers.append(f"{prefix}_CONSTANT_NOT_NUMERIC")
        return value
    if kind == "copy_field":
        field = str(declaration.get("field") or "")
        return visible_number(visible, field, blockers, prefix)
    if kind == "linear":
        total = as_number(declaration.get("intercept", 0.0))
        if total is None:
            blockers.append(f"{prefix}_INTERCEPT_NOT_NUMERIC")
            total = 0.0
        terms = declaration.get("terms")
        if not isinstance(terms, list) or not terms:
            blockers.append(f"{prefix}_LINEAR_TERMS_MISSING")
            return None
        for index, term in enumerate(terms):
            if not isinstance(term, dict):
                blockers.append(f"{prefix}_LINEAR_TERM_INVALID::{index}")
                continue
            field = str(term.get("field") or "")
            coefficient = as_number(term.get("coefficient"))
            if coefficient is None:
                blockers.append(f"{prefix}_COEFFICIENT_NOT_NUMERIC::{field or index}")
                continue
            total += coefficient * visible_number(visible, field, blockers, prefix)
        return total
    if kind == "sum_fields":
        fields = declaration.get("fields")
        if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
            blockers.append(f"{prefix}_SUM_FIELDS_INVALID")
            return None
        return sum(visible_number(visible, field, blockers, prefix) for field in fields)
    blockers.append(f"{prefix}_DECLARATION_KIND_UNSUPPORTED::{kind or 'missing'}")
    return None


def residual_metric_value(values: list[float], metric: str) -> float | None:
    if not values:
        return None
    metric_key = metric.lower()
    if metric_key in {"mae", "mean_absolute_error"}:
        return sum(values) / len(values)
    if metric_key in {"rmse", "root_mean_square_error"}:
        return math.sqrt(sum(value * value for value in values) / len(values))
    if metric_key in {"max_abs", "max_absolute_error"}:
        return max(values)
    raise ValueError(f"RESIDUAL_METRIC_UNSUPPORTED::{metric}")


def scalar_values(payload: Any, path: str = "$") -> list[tuple[str, Any]]:
    if isinstance(payload, dict):
        rows: list[tuple[str, Any]] = []
        for key, value in payload.items():
            rows.extend(scalar_values(value, f"{path}.{key}"))
        return rows
    if isinstance(payload, list):
        rows = []
        for index, value in enumerate(payload):
            rows.extend(scalar_values(value, f"{path}[{index}]"))
        return rows
    return [(path, payload)]


def target_value_leak_blockers(declaration: dict[str, Any], target_rows: list[dict[str, Any]]) -> list[str]:
    target_atoms = {
        canonical_json(value)
        for row in target_rows
        for value in row["target"].values()
        if value is not None and not isinstance(value, bool)
    }
    blockers = []
    searchable_declaration = declaration_payload_for_hash(declaration)
    for path, value in scalar_values(searchable_declaration):
        if canonical_json(value) in target_atoms:
            blockers.append(f"DECLARATION_CONTAINS_TARGET_VALUE::{path}")
    return sorted(set(blockers))


def validate_field_separation(
    visible_fields: list[str],
    target_fields: list[str],
    row_rule: dict[str, Any],
    model_declaration: dict[str, Any],
    comparator_declaration: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    for visible in visible_fields:
        for target in target_fields:
            if paths_overlap(visible, target):
                blockers.append(f"TARGET_FIELD_IN_VISIBLE_PROJECTION::{target}")
    rule_field = row_rule.get("field")
    if isinstance(rule_field, str) and rule_field:
        if not any(paths_overlap(rule_field, visible) for visible in visible_fields):
            blockers.append(f"ROW_INCLUSION_RULE_NOT_VISIBLE::{rule_field}")
        for target in target_fields:
            if paths_overlap(rule_field, target):
                blockers.append(f"ROW_INCLUSION_RULE_REFERENCES_TARGET_FIELD::{rule_field}")
    for name, declaration in (("MODEL", model_declaration), ("COMPARATOR", comparator_declaration)):
        for key, value in scalar_values(declaration):
            if key.endswith(".field") or key.endswith(".target_field") or ".fields[" in key:
                field_value = str(value)
                for target in target_fields:
                    if paths_overlap(field_value, target):
                        blockers.append(f"{name}_DECLARATION_REFERENCES_TARGET_FIELD::{field_value}")
    return sorted(set(blockers))


def lock_paths(lock_id: str) -> dict[str, str]:
    safe_id = safe_lock_id(lock_id)
    return {
        "visible_lock_ref": f"{LOCK_ROOT_REL}/{safe_id}.visible_projection_lock.json",
        "target_lock_ref": f"{LOCK_ROOT_REL}/{safe_id}.target_projection_lock.json",
        "prediction_lock_ref": f"{LOCK_ROOT_REL}/{safe_id}.prediction_materialization_lock.json",
    }


def build_one_lock(root: Path, declaration_path: Path) -> dict[str, Any]:
    blockers: list[str] = []
    declaration = read_json(declaration_path)
    if not isinstance(declaration, dict):
        raise ValueError(f"DECLARATION_NOT_OBJECT::{declaration_path}")
    declaration_rel = declaration_path.relative_to(root).as_posix()
    lock_id = str(declaration.get("lock_id") or declaration_path.stem)
    visible_fields = required_list(declaration, "visible_fields", blockers)
    target_fields = required_list(declaration, "target_fields", blockers)
    snapshot_ref = str(declaration.get("snapshot_ref") or "")
    row_rule = declaration.get("row_inclusion_rule")
    model_declaration = declaration.get("model_declaration") or declaration.get("model")
    comparator_declaration = declaration.get("comparator_declaration") or declaration.get("comparator")
    residual_metric = str(declaration.get("residual_metric") or "")
    uncertainty_policy = declaration.get("uncertainty_policy")
    negative_controls = declaration.get("negative_controls")

    if not snapshot_ref:
        blockers.append("SNAPSHOT_REF_MISSING")
    if not isinstance(row_rule, dict):
        blockers.append("ROW_INCLUSION_RULE_MISSING")
        row_rule = {}
    if not isinstance(model_declaration, dict):
        blockers.append("MODEL_DECLARATION_MISSING")
        model_declaration = {}
    if not isinstance(comparator_declaration, dict):
        blockers.append("COMPARATOR_DECLARATION_MISSING")
        comparator_declaration = {}
    if not residual_metric:
        blockers.append("RESIDUAL_METRIC_MISSING")
    if not isinstance(uncertainty_policy, dict):
        blockers.append("UNCERTAINTY_POLICY_MISSING")
        uncertainty_policy = {}
    if not isinstance(negative_controls, list) or not negative_controls:
        blockers.append("NEGATIVE_CONTROLS_MISSING")
        negative_controls = []
    blockers.extend(no_send_lock_blockers(declaration))
    blockers.extend(
        validate_field_separation(
            visible_fields,
            target_fields,
            row_rule,
            model_declaration,
            comparator_declaration,
        )
    )

    declaration_hash = sha256_object(declaration_payload_for_hash(declaration))
    if declaration.get("expected_declaration_sha256") not in (None, declaration_hash):
        blockers.append("DECLARATION_HASH_MISMATCH")

    snapshot_path = resolve_under_root(root, snapshot_ref) if snapshot_ref else declaration_path
    snapshot_bytes = snapshot_path.read_bytes() if snapshot_ref and snapshot_path.exists() else b""
    snapshot_sha256 = sha256_bytes(snapshot_bytes)
    if snapshot_ref and not snapshot_path.exists():
        blockers.append("SNAPSHOT_REF_NOT_FOUND")
    if declaration.get("expected_snapshot_sha256") not in (None, snapshot_sha256):
        blockers.append("SNAPSHOT_HASH_MISMATCH")

    rows: list[Any] = []
    if snapshot_ref and snapshot_path.exists():
        try:
            rows = load_snapshot(snapshot_path, str(declaration.get("snapshot_format") or "auto"), declaration.get("row_path"))
        except Exception as exc:
            blockers.append(str(exc))

    included_rows: list[tuple[int, str, Any]] = []
    row_id_field = declaration.get("row_id_field")
    for zero_index, row in enumerate(rows):
        row_index = zero_index + 1
        if included_by_rule(row, row_index, row_rule):
            included_rows.append((row_index, row_id_for(row, row_index, row_id_field), row))
    if not included_rows:
        blockers.append("NO_INCLUDED_ROWS")

    visible_rows = []
    prediction_rows = []
    for row_index, row_id, row in included_rows:
        row_blockers: list[str] = []
        visible = project_row(row, visible_fields, missing_prefix="VISIBLE_FIELD_MISSING", blockers=row_blockers)
        visible_row = {"row_index": row_index, "row_id": row_id, "visible": visible}
        visible_hash = sha256_object(visible_row)
        prediction_blockers = list(row_blockers)
        model_prediction = materialize_declared_prediction(
            model_declaration,
            visible,
            prediction_blockers,
            "MODEL",
        )
        comparator_prediction = materialize_declared_prediction(
            comparator_declaration,
            visible,
            prediction_blockers,
            "COMPARATOR",
        )
        blockers.extend(f"{blocker}::row_{row_id}" for blocker in prediction_blockers)
        visible_rows.append({**visible_row, "visible_row_sha256": visible_hash})
        prediction_rows.append(
            {
                "row_index": row_index,
                "row_id": row_id,
                "visible_row_sha256": visible_hash,
                "declaration_sha256": declaration_hash,
                "model_declaration_sha256": sha256_object(model_declaration),
                "comparator_declaration_sha256": sha256_object(comparator_declaration),
                "model_prediction": model_prediction,
                "comparator_prediction": comparator_prediction,
                "target_opened": False,
            }
        )

    visible_projection_lock = {
        "schema_id": VISIBLE_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_rel,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "declaration_sha256": declaration_hash,
        "visible_fields": visible_fields,
        "row_inclusion_rule_sha256": sha256_object(row_rule),
        "row_count": len(visible_rows),
        "rows": visible_rows,
        "locks": NO_SEND_LOCKS,
    }
    visible_projection_sha256 = sha256_object(visible_projection_lock)
    if declaration.get("expected_visible_projection_sha256") not in (None, visible_projection_sha256):
        blockers.append("VISIBLE_PROJECTION_HASH_MISMATCH")

    prediction_materialization_lock = {
        "schema_id": PREDICTION_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_rel,
        "declaration_sha256": declaration_hash,
        "visible_projection_sha256": visible_projection_sha256,
        "model_declaration": model_declaration,
        "comparator_declaration": comparator_declaration,
        "prediction_rows": prediction_rows,
        "algorithmic_target_separation": {
            "prediction_inputs": "visible projection rows plus locked declarations only",
            "target_projection_read_before_prediction_materialization": False,
            "target_opened_after_prediction_materialization": True,
        },
        "locks": NO_SEND_LOCKS,
    }
    prediction_materialization_sha256 = sha256_object(prediction_materialization_lock)
    if declaration.get("expected_prediction_materialization_sha256") not in (None, prediction_materialization_sha256):
        blockers.append("PREDICTION_MATERIALIZATION_HASH_MISMATCH")

    target_rows = []
    model_abs_errors: list[float] = []
    comparator_abs_errors: list[float] = []
    if len(target_fields) != 1:
        blockers.append("RESIDUAL_REQUIRES_EXACTLY_ONE_TARGET_FIELD")
    residual_target_field = target_fields[0] if target_fields else ""
    prediction_by_row_id = {row["row_id"]: row for row in prediction_rows}
    for row_index, row_id, row in included_rows:
        target_blockers: list[str] = []
        target = project_row(row, target_fields, missing_prefix="TARGET_FIELD_MISSING", blockers=target_blockers)
        target_row = {"row_index": row_index, "row_id": row_id, "target": target}
        target_hash = sha256_object(target_row)
        source_row_hash = sha256_object(row)
        blockers.extend(f"{blocker}::row_{row_id}" for blocker in target_blockers)
        if residual_target_field in target:
            observed = as_number(target[residual_target_field])
            predicted = prediction_by_row_id.get(row_id, {}).get("model_prediction")
            comparator = prediction_by_row_id.get(row_id, {}).get("comparator_prediction")
            predicted_number = as_number(predicted)
            comparator_number = as_number(comparator)
            if observed is None:
                blockers.append(f"TARGET_VALUE_NOT_NUMERIC::{residual_target_field}::row_{row_id}")
            if predicted_number is None:
                blockers.append(f"MODEL_PREDICTION_NOT_NUMERIC::row_{row_id}")
            if comparator_number is None:
                blockers.append(f"COMPARATOR_PREDICTION_NOT_NUMERIC::row_{row_id}")
            if observed is not None and predicted_number is not None:
                model_abs_errors.append(abs(predicted_number - observed))
            if observed is not None and comparator_number is not None:
                comparator_abs_errors.append(abs(comparator_number - observed))
        target_rows.append(
            {
                **target_row,
                "target_row_sha256": target_hash,
                "source_row_sha256": source_row_hash,
            }
        )

    target_projection_lock = {
        "schema_id": TARGET_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_rel,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "declaration_sha256": declaration_hash,
        "visible_projection_sha256": visible_projection_sha256,
        "prediction_materialization_sha256": prediction_materialization_sha256,
        "target_fields": target_fields,
        "row_count": len(target_rows),
        "rows": target_rows,
        "target_opened_after_prediction_materialization": True,
        "locks": NO_SEND_LOCKS,
    }
    target_projection_sha256 = sha256_object(target_projection_lock)
    if declaration.get("expected_target_projection_sha256") not in (None, target_projection_sha256):
        blockers.append("TARGET_PROJECTION_HASH_MISMATCH")

    blockers.extend(target_value_leak_blockers(declaration, target_rows))
    blockers = sorted(set(blockers))

    residual_summary: dict[str, Any]
    if blockers:
        residual_summary = {
            "metric": residual_metric,
            "model_residual": None,
            "comparator_residual": None,
            "not_evaluated_reason": "fail_closed_blockers_present",
        }
        verdict = "BLOCKED_FAIL_CLOSED"
    else:
        try:
            model_residual = residual_metric_value(model_abs_errors, residual_metric)
            comparator_residual = residual_metric_value(comparator_abs_errors, residual_metric)
        except ValueError as exc:
            blockers.append(str(exc))
            model_residual = None
            comparator_residual = None
            verdict = "BLOCKED_FAIL_CLOSED"
        else:
            max_model_residual = uncertainty_policy.get("max_model_residual")
            min_model_advantage = uncertainty_policy.get("min_model_advantage", 0.0)
            pass_threshold = as_number(max_model_residual)
            pass_advantage = as_number(min_model_advantage)
            if pass_advantage is None:
                pass_advantage = 0.0
            threshold_ok = pass_threshold is None or (
                model_residual is not None and model_residual <= pass_threshold
            )
            advantage_ok = (
                comparator_residual is None
                or model_residual is None
                or (comparator_residual - model_residual) >= pass_advantage
            )
            verdict = "LOCKED_PASS" if threshold_ok and advantage_ok else "LOCKED_FAIL_RESIDUAL_POLICY"
        residual_summary = {
            "metric": residual_metric,
            "target_field": residual_target_field,
            "model_residual": model_residual,
            "comparator_residual": comparator_residual,
            "model_abs_errors": model_abs_errors,
            "comparator_abs_errors": comparator_abs_errors,
            "uncertainty_policy": uncertainty_policy,
        }

    paths = lock_paths(lock_id)
    return {
        "lock_id": lock_id,
        "declaration_ref": declaration_rel,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "declaration_sha256": declaration_hash,
        "visible_projection_sha256": visible_projection_sha256,
        "target_projection_sha256": target_projection_sha256,
        "prediction_materialization_sha256": prediction_materialization_sha256,
        "visible_projection_lock": visible_projection_lock,
        "target_projection_lock": target_projection_lock,
        "prediction_materialization_lock": prediction_materialization_lock,
        "row_hashes": [
            {
                "row_index": visible_row["row_index"],
                "row_id": visible_row["row_id"],
                "visible_row_sha256": visible_row["visible_row_sha256"],
                "target_row_sha256": target_row["target_row_sha256"],
                "source_row_sha256": target_row["source_row_sha256"],
            }
            for visible_row, target_row in zip(visible_rows, target_rows)
        ],
        "tamper_controls": {
            "snapshot_sha256": snapshot_sha256,
            "declaration_sha256": declaration_hash,
            "visible_projection_sha256": visible_projection_sha256,
            "target_projection_sha256": target_projection_sha256,
            "prediction_materialization_sha256": prediction_materialization_sha256,
            "expected_hashes_checked": sorted(key for key in EXPECTED_HASH_KEYS if key in declaration),
            "no_send_locks_required": NO_SEND_LOCKS,
            "no_send_locks_present": not no_send_lock_blockers(declaration),
            "target_fields_absent_from_visible_projection": not any(
                paths_overlap(visible, target) for visible in visible_fields for target in target_fields
            ),
            "target_opened_after_prediction_materialization": True,
        },
        "residual_summary": residual_summary,
        "negative_controls": negative_controls,
        "verdict": verdict,
        "blockers": sorted(set(blockers)),
        "support_policy": "Target-projection locks are reusable infrastructure only; they do not promote claims or grant support.",
        **paths,
    }


def public_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key not in {"visible_projection_lock", "target_projection_lock", "prediction_materialization_lock"}
    }


def build_report(root: Path, declaration_paths: list[Path]) -> dict[str, Any]:
    records = [build_one_lock(root, path) for path in declaration_paths]
    blockers = sorted({blocker for record in records for blocker in record["blockers"]})
    report = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_target_projection_lock_factory.py",
        "declaration_refs": [path.relative_to(root).as_posix() for path in declaration_paths],
        "output_root_ref": OUTPUT_ROOT_REL,
        "record_total": len(records),
        "blocked_total": sum(1 for record in records if record["verdict"] == "BLOCKED_FAIL_CLOSED"),
        "locked_pass_total": sum(1 for record in records if record["verdict"] == "LOCKED_PASS"),
        "locked_fail_total": sum(1 for record in records if record["verdict"] == "LOCKED_FAIL_RESIDUAL_POLICY"),
        "open_blocker_total": len(blockers),
        "blockers": blockers,
        "records": [public_record(record) for record in records],
        "locks": NO_SEND_LOCKS,
        "support_policy": "No grand TOE support switch is set by this infrastructure capability.",
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    return report


def build_report_with_locks(root: Path, declaration_paths: list[Path]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = [build_one_lock(root, path) for path in declaration_paths]
    blockers = sorted({blocker for record in records for blocker in record["blockers"]})
    report = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_target_projection_lock_factory.py",
        "declaration_refs": [path.relative_to(root).as_posix() for path in declaration_paths],
        "output_root_ref": OUTPUT_ROOT_REL,
        "record_total": len(records),
        "blocked_total": sum(1 for record in records if record["verdict"] == "BLOCKED_FAIL_CLOSED"),
        "locked_pass_total": sum(1 for record in records if record["verdict"] == "LOCKED_PASS"),
        "locked_fail_total": sum(1 for record in records if record["verdict"] == "LOCKED_FAIL_RESIDUAL_POLICY"),
        "open_blocker_total": len(blockers),
        "blockers": blockers,
        "records": [public_record(record) for record in records],
        "locks": NO_SEND_LOCKS,
        "support_policy": "No grand TOE support switch is set by this infrastructure capability.",
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    return report, records


def write_outputs(root: Path, report: dict[str, Any], records: list[dict[str, Any]]) -> None:
    write_json(resolve_under_root(root, REPORT_JSON_REL), report)
    for record in records:
        write_json(resolve_under_root(root, record["visible_lock_ref"]), record["visible_projection_lock"])
        write_json(resolve_under_root(root, record["target_lock_ref"]), record["target_projection_lock"])
        write_json(resolve_under_root(root, record["prediction_lock_ref"]), record["prediction_materialization_lock"])


def check_stored(root: Path, declaration_paths: list[Path]) -> list[str]:
    expected_report, expected_records = build_report_with_locks(root, declaration_paths)
    failures: list[str] = []
    report_path = resolve_under_root(root, REPORT_JSON_REL)
    if not report_path.exists():
        failures.append(f"missing::{REPORT_JSON_REL}")
    else:
        try:
            actual_report = read_json(report_path)
        except Exception as exc:
            failures.append(f"parse_error::{REPORT_JSON_REL}::{exc.__class__.__name__}")
        else:
            if actual_report != expected_report:
                failures.append(f"mismatch::{REPORT_JSON_REL}")
    for record in expected_records:
        for ref_key, payload_key in (
            ("visible_lock_ref", "visible_projection_lock"),
            ("target_lock_ref", "target_projection_lock"),
            ("prediction_lock_ref", "prediction_materialization_lock"),
        ):
            ref = record[ref_key]
            path = resolve_under_root(root, ref)
            if not path.exists():
                failures.append(f"missing::{ref}")
                continue
            try:
                actual = read_json(path)
            except Exception as exc:
                failures.append(f"parse_error::{ref}::{exc.__class__.__name__}")
                continue
            if actual != record[payload_key]:
                failures.append(f"mismatch::{ref}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build target-blind visible/target projection locks.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--declaration", action="append", default=[], help="declaration JSON path relative to root")
    parser.add_argument("--write", action="store_true", help="write report and lock artifacts")
    parser.add_argument("--check", action="store_true", help="check stored report and lock artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even with fail-closed blockers")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    declaration_paths = declaration_paths_from_args(root, args.declaration)
    if not declaration_paths:
        print(json.dumps({"status": "error", "error": "NO_TARGET_PROJECTION_DECLARATIONS_FOUND"}, indent=2))
        return 1
    if args.check:
        failures = check_stored(root, declaration_paths)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [REPORT_JSON_REL]}, indent=2))
        return 0
    report, records = build_report_with_locks(root, declaration_paths)
    if args.write:
        write_outputs(root, report, records)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if report["open_blocker_total"] and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
