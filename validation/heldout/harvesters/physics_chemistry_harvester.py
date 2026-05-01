from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_HARVESTER_BLOCKER_REPORT_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
BLOCKER_ID = "grand_toe_empirical_superiority"

TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
OUTPUT_ROOT_REL = "validation/heldout/grand_science/physics_chemistry/harvested"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_PHYSICS_CHEMISTRY_HARVESTER_BLOCKER_REPORT.json"

DOMAINS = ("physics", "chemistry")
MINIMUM_N_DEFAULT = 20


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def minimum_n(root: Path) -> int:
    requirements = read_json(root / REQUIREMENTS_REL)
    value = requirements.get("minimum_per_domain_n", MINIMUM_N_DEFAULT)
    return value if isinstance(value, int) and not isinstance(value, bool) else MINIMUM_N_DEFAULT


def target_blind_rows(root: Path) -> list[dict[str, Any]]:
    rows = read_json(root / TARGET_BLIND_REL).get("rows", [])
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and row.get("lane") in DOMAINS
    ]


def is_bounded_baseline(row: dict[str, Any]) -> bool:
    scope = str(row.get("support_scope") or "").lower()
    return (
        "bounded" in scope
        or "not a novel" in scope
        or "not a physics law" in scope
        or "not a chemistry law" in scope
        or row.get("grand_empirical_support_allowed") is not True
    )


def baseline_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": row.get("claim_id"),
        "domain": row.get("lane"),
        "source_ref": f"{TARGET_BLIND_REL}::{row.get('claim_id')}",
        "dataset_snapshot_ref": row.get("dataset_snapshot_ref"),
        "formula": row.get("formula"),
        "support_scope": row.get("support_scope"),
        "prediction_support_allowed": row.get("prediction_support_allowed") is True,
        "empirical_support_allowed": row.get("empirical_support_allowed") is True,
        "grand_toe_support_allowed": False,
        "grand_n_credit": 0,
        "classification": "BOUNDED_BASELINE_NOT_GRAND_EVIDENCE",
        "row_sha256": sha256_object({key: value for key, value in row.items() if key not in {"replay_hash", "replay_hash_policy"}}),
    }


def domain_report(domain: str, rows: list[dict[str, Any]], min_n: int) -> dict[str, Any]:
    domain_rows = [row for row in rows if row.get("lane") == domain]
    grand_eligible = [row for row in domain_rows if not is_bounded_baseline(row)]
    blockers = [
        f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{len(grand_eligible)}/{min_n}",
        "CURRENT_TARGET_BLIND_ROWS_ARE_BOUNDED_BASELINE_NOT_GRAND_EVIDENCE",
        "GRAND_TOE_SUPPORT_NOT_ALLOWED",
    ]
    if not domain_rows:
        blockers.append("NO_CURRENT_TARGET_BLIND_ROWS")
    return {
        "domain": domain,
        "minimum_n": min_n,
        "current_target_blind_row_total": len(domain_rows),
        "grand_eligible_row_total": len(grand_eligible),
        "bounded_baseline_row_total": len(domain_rows) - len(grand_eligible),
        "candidate_pack_total": 0,
        "valid_pack_total": 0,
        "grand_toe_support_allowed": False,
        "status": "BLOCKED_CURRENT_ROWS_ARE_BASELINE_ONLY",
        "blockers": ordered_unique(blockers),
        "baseline_rows": [baseline_summary(row) for row in domain_rows],
    }


def build_report(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    min_n = minimum_n(root)
    rows = target_blind_rows(root)
    domains = [domain_report(domain, rows, min_n) for domain in DOMAINS]
    blockers = ordered_unique([blocker for domain in domains for blocker in domain["blockers"]])
    report: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "harvester": "validation/heldout/harvesters/physics_chemistry_harvester.py",
        "target_blind_ref": TARGET_BLIND_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "output_ref": REPORT_REL,
        "offline": True,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "candidate_pack_total": 0,
        "valid_pack_total": 0,
        "valid_candidate_pack_total": 0,
        "blocked_candidate_pack_total": 0,
        "current_target_blind_row_total": len(rows),
        "bounded_baseline_row_total": sum(domain["bounded_baseline_row_total"] for domain in domains),
        "grand_eligible_row_total": sum(domain["grand_eligible_row_total"] for domain in domains),
        "minimum_per_domain_n": min_n,
        "grand_toe_support_allowed": False,
        "blocker_total": len(blockers),
        "open_blocker_total": len(blockers),
        "blockers": blockers,
        "domains": domains,
        "explanation": [
            "N<20: current physics/chemistry target-blind rows provide zero grand-eligible rows against the required minimum.",
            "The current rows are bounded baseline reconstructions, not grand evidence.",
            "No candidate evidence pack is emitted from these rows; valid_pack_total remains 0.",
        ],
        "verdict": "BLOCKED_PENDING_GENUINE_PHYSICS_CHEMISTRY_EVIDENCE",
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    return report


def build_payload(root: Path | None = None) -> dict[str, Any]:
    return build_report(root)


def write_outputs(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    report = build_report(root)
    write_json(root / REPORT_REL, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit offline physics/chemistry target-blind blocker report.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    report = write_outputs(root) if args.write else build_report(root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["valid_pack_total"] == 0 and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
