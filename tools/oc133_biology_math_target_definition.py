from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
SCHEMA_ID = "OC133_BIOLOGY_MATH_TARGET_DEFINITIONS_v1"
BLOCKER_SCHEMA_ID = "OC133_BIOLOGY_MATH_TARGET_BLOCKERS_v1"
PLANNER_REF = "tools/oc133_biology_math_target_definition.py"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
BIOLOGY_SNAPSHOT_REL = "validation/_raw/biology_ncbi_geo_platform.txt"
FINITE_CHECKS_REL = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"
LEAN_CERTIFICATE_REL = "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json"

OUTPUT_ROOT_REL = "validation/heldout/acquisition_plans/biology_math_targets"
TARGETS_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_MATH_TARGET_DEFINITIONS.json"
BLOCKERS_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_MATH_TARGET_BLOCKERS.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"

MINIMUM_N = 20
CURRENT_N = 1
SUPPORT_POLICY = (
    "Current biology API pagination and mathematics proof-corpus aggregates are target definitions only: "
    "API pagination/proof corpus are not grand evidence, N<20, no support allowed."
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(lf_bytes(path)).hexdigest()


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def as_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def minimum_n(root: Path) -> int:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return MINIMUM_N
    payload = read_json(path)
    if not isinstance(payload, dict):
        return MINIMUM_N
    value = payload.get("minimum_per_domain_n", MINIMUM_N)
    return as_int(value, MINIMUM_N) or MINIMUM_N


def biology_target(root: Path, min_n: int) -> dict[str, Any]:
    snapshot_path = resolve_under_root(root, BIOLOGY_SNAPSHOT_REL)
    payload = read_json(snapshot_path)
    esearch = payload.get("esearchresult", {}) if isinstance(payload, dict) else {}
    if not isinstance(esearch, dict):
        esearch = {}
    idlist = esearch.get("idlist", [])
    if not isinstance(idlist, list):
        idlist = []
    retstart = as_int(esearch.get("retstart"), 0)
    retmax = as_int(esearch.get("retmax"), len(idlist))
    total_count = as_int(esearch.get("count"), 0)

    predicted = float(retstart + len(idlist))
    observed = float(retmax)
    comparator = float(total_count)
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    blockers = [
        "BIOLOGY_API_PAGINATION_NOT_GRAND_EVIDENCE::API pagination is not grand evidence",
        f"N_BELOW_MINIMUM::biology::{CURRENT_N}/{min_n}::N<20",
        "NO_SUPPORT_ALLOWED::biology::no support allowed",
    ]
    return {
        "target_id": "OC133-BIOLOGY-MATH-BIOLOGY-PAGINATION-001",
        "domain": "biology",
        "target_kind": "api_pagination_replay",
        "source_ref": BIOLOGY_SNAPSHOT_REL,
        "source_sha256": sha256_file(snapshot_path),
        "source_byte_count": len(lf_bytes(snapshot_path)),
        "source_assessment": {
            "source_kind": "NCBI_GEO_ESearch_API_snapshot",
            "grand_evidence": False,
            "scope_statement": "API pagination is not grand evidence; this is a bounded retmax target definition.",
        },
        "target_definition": {
            "visible_fields": ["esearchresult.retstart", "esearchresult.idlist"],
            "withheld_field": "esearchresult.retmax",
            "formula": "retstart + len(idlist)",
            "predicted_value": predicted,
            "observed_value": observed,
            "comparator_baseline": "esearchresult.count total-hit count",
            "comparator_prediction": comparator,
            "residuals": {
                "model": model_residual,
                "comparator": comparator_residual,
            },
            "falsifier": "retmax differs from retstart plus returned id count",
        },
        "current_n": CURRENT_N,
        "minimum_n": min_n,
        "missing_n": max(0, min_n - CURRENT_N),
        "support_allowed": False,
        "status": "BLOCKED_TARGET_DEFINITION_ONLY",
        "blockers": blockers,
    }


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


def lean_certificate(root: Path, finite_checks: dict[str, Any]) -> dict[str, Any]:
    path = root / LEAN_CERTIFICATE_REL
    if not path.exists():
        return {
            "present": False,
            "ref": LEAN_CERTIFICATE_REL,
        }
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {
            "present": False,
            "ref": LEAN_CERTIFICATE_REL,
            "parse_status": "NOT_OBJECT",
        }
    cert_source_sha = payload.get("lean_source_sha256")
    finite_cert_source_sha = finite_checks.get("certificate_lean_source_sha256")
    finite_current_source_sha = finite_checks.get("current_lean_source_sha256")
    return {
        "present": True,
        "ref": LEAN_CERTIFICATE_REL,
        "sha256": sha256_file(path),
        "execution_status": payload.get("execution_status"),
        "returncode": payload.get("returncode"),
        "clean_returncode": payload.get("clean_returncode"),
        "theorem_ref_present_total": payload.get("theorem_ref_present_total"),
        "theorem_ref_missing_total": payload.get("theorem_ref_missing_total"),
        "lean_source_ref": payload.get("lean_source_ref"),
        "lean_source_sha256": cert_source_sha,
        "finite_checks_certificate_source_sha256": finite_cert_source_sha,
        "finite_checks_current_source_sha256": finite_current_source_sha,
        "source_sha256_matches_finite_checks": bool(
            cert_source_sha and finite_cert_source_sha and cert_source_sha == finite_cert_source_sha
        ),
    }


def mathematics_target(root: Path, min_n: int) -> dict[str, Any]:
    finite_path = resolve_under_root(root, FINITE_CHECKS_REL)
    payload = read_json(finite_path)
    if not isinstance(payload, dict):
        payload = {}
    theorem_ids = accepted_theorem_ids(payload)
    machine_checked = as_int(payload.get("machine_checked_subset_total"), len(theorem_ids))
    positive_cases = as_int(payload.get("positive_case_total"), 0)

    predicted = float(len(theorem_ids))
    observed = float(machine_checked)
    comparator = float(positive_cases)
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    blockers = [
        "MATHEMATICS_PROOF_CORPUS_NOT_GRAND_EVIDENCE::proof corpus is not grand evidence",
        f"N_BELOW_MINIMUM::mathematics::{CURRENT_N}/{min_n}::N<20",
        "NO_SUPPORT_ALLOWED::mathematics::no support allowed",
    ]
    return {
        "target_id": "OC133-BIOLOGY-MATH-MATHEMATICS-PROOF-CORPUS-001",
        "domain": "mathematics",
        "target_kind": "finite_proof_corpus_aggregate",
        "source_ref": FINITE_CHECKS_REL,
        "source_sha256": sha256_file(finite_path),
        "source_byte_count": len(lf_bytes(finite_path)),
        "source_assessment": {
            "source_kind": "finite_lean_proof_corpus",
            "grand_evidence": False,
            "scope_statement": "proof corpus is not grand evidence; this is a bounded formal QA aggregate.",
        },
        "finite_checks": {
            "case_total": as_int(payload.get("case_total"), 0),
            "positive_case_total": positive_cases,
            "machine_checked_subset_total": machine_checked,
            "unique_accepted_theorem_total": len(theorem_ids),
            "lean_theorem_ref_total": as_int(payload.get("lean_theorem_ref_total"), 0),
            "lean_build_returncode": payload.get("lean_build_returncode"),
            "live_lean_build_returncode": payload.get("live_lean_build_returncode"),
            "lean_source_ref": payload.get("lean_source_ref"),
            "current_lean_source_sha256": payload.get("current_lean_source_sha256"),
            "certificate_lean_source_sha256": payload.get("certificate_lean_source_sha256"),
        },
        "lean_certificate": lean_certificate(root, payload),
        "target_definition": {
            "visible_fields": ["rows.case_type", "rows.observed_verdict", "rows.passed", "rows.theorem_id"],
            "withheld_field": "machine_checked_subset_total",
            "formula": "count_unique(theorem_id where case_type='theorem_case' and observed_verdict='ACCEPT' and passed=true)",
            "predicted_value": predicted,
            "observed_value": observed,
            "comparator_baseline": "positive_case_total",
            "comparator_prediction": comparator,
            "residuals": {
                "model": model_residual,
                "comparator": comparator_residual,
            },
            "falsifier": "accepted theorem aggregate differs from machine_checked_subset_total",
        },
        "current_n": CURRENT_N,
        "minimum_n": min_n,
        "missing_n": max(0, min_n - CURRENT_N),
        "support_allowed": False,
        "status": "BLOCKED_TARGET_DEFINITION_ONLY",
        "blockers": blockers,
    }


def build_blockers_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "domain": row["domain"],
            "target_id": row["target_id"],
            "support_allowed": False,
            "blockers": row["blockers"],
        }
        for row in payload["target_definitions"]
    ]
    blockers = ordered_unique([blocker for row in rows for blocker in row["blockers"]])
    out = {
        "schema_id": BLOCKER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "planner": PLANNER_REF,
        "target_definitions_ref": TARGETS_REL,
        "support_allowed": False,
        "open_blocker_total": len(blockers),
        "open_blocker_ids": blockers,
        "rows": rows,
        "support_policy": SUPPORT_POLICY,
        "no_send": True,
        "publish_allowed": False,
        "verdict": payload["verdict"],
    }
    out["blocker_hash"] = sha256_object(blockers)
    return out


def build_payload(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    min_n = minimum_n(root)
    targets = [
        biology_target(root, min_n),
        mathematics_target(root, min_n),
    ]
    blockers = ordered_unique([blocker for row in targets for blocker in row["blockers"]])
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "planner": PLANNER_REF,
        "capability_owner": CAPABILITY_OWNER,
        "requirements_ref": REQUIREMENTS_REL,
        "output_root_ref": OUTPUT_ROOT_REL,
        "artifact_refs": {
            "target_definitions": TARGETS_REL,
            "blockers": BLOCKERS_REL,
            "readme": README_REL,
        },
        "input_refs": {
            "biology_snapshot": BIOLOGY_SNAPSHOT_REL,
            "finite_checks": FINITE_CHECKS_REL,
            "lean_certificate_optional": LEAN_CERTIFICATE_REL,
        },
        "minimum_n": min_n,
        "target_definition_total": len(targets),
        "blocked_target_total": len(targets),
        "support_allowed": False,
        "open_blocker_total": len(blockers),
        "open_blocker_ids": blockers,
        "target_definitions": targets,
        "support_policy": SUPPORT_POLICY,
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
        "verdict": "BLOCKED_TARGET_DEFINITIONS_ONLY_NO_SUPPORT_ALLOWED",
    }
    payload["target_definition_hash"] = sha256_object(targets)
    payload["blocker_hash"] = sha256_object(blockers)
    return payload


def render_readme(payload: dict[str, Any]) -> str:
    lines = [
        "# Biology + Mathematics Target Definitions",
        "",
        f"Verdict: `{payload['verdict']}`",
        "Support allowed: `false`",
        f"Open blockers: `{payload['open_blocker_total']}`",
        "",
        SUPPORT_POLICY,
        "",
        "| Domain | Target | N | Minimum N | Status |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["target_definitions"]:
        lines.append(
            f"| `{row['domain']}` | `{row['target_kind']}` | `{row['current_n']}` | "
            f"`{row['minimum_n']}` | `{row['status']}` |"
        )
    lines.append("")
    lines.append("Blockers:")
    for blocker in payload["open_blocker_ids"]:
        lines.append(f"- `{blocker}`")
    return "\n".join(lines) + "\n"


def build_all(root: Path | None = None) -> dict[str, Any]:
    payload = build_payload(root)
    blockers = build_blockers_payload(payload)
    return {
        TARGETS_REL: payload,
        BLOCKERS_REL: blockers,
        README_REL: render_readme(payload),
    }


def write_outputs(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    outputs = build_all(root)
    for rel_path, payload in outputs.items():
        path = root / rel_path
        if isinstance(payload, str):
            write_text(path, payload)
        else:
            write_json(path, payload)
    return outputs[TARGETS_REL]


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    failures: list[str] = []
    for rel_path, payload in expected.items():
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        if isinstance(payload, str):
            if path.read_text(encoding="utf-8") != payload:
                failures.append(f"mismatch::{rel_path}")
        elif read_json(path) != payload:
            failures.append(f"mismatch::{rel_path}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC133 biology/math target-definition blockers.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write target definition artifacts")
    parser.add_argument("--check", action="store_true", help="check stored artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even when blockers remain")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print("biology/math target definition check passed")
        return 0

    payload = write_outputs(root) if args.write else build_payload(root)
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if args.allow_blocked_exit_zero or payload["open_blocker_total"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
