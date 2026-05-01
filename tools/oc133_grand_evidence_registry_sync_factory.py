from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory  # noqa: E402


SCHEMA_ID = "OC133_GRAND_EVIDENCE_REGISTRY_SYNC_v1"
WORK_ORDER_SCHEMA_ID = "OC133_GRAND_EVIDENCE_REPAIR_WORK_ORDERS_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_GRAND_EVIDENCE_REGISTRY_SYNC.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_GRAND_EVIDENCE_REGISTRY_SYNC.md"
WORK_ORDERS_REL = "validation/heldout/OC133_GRAND_EVIDENCE_REPAIR_WORK_ORDERS.json"

NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "journal_submissions_allowed": False,
    "external_network_allowed": False,
    "owner_approval_required": True,
}

FAILURE_CLASS_RULES = (
    (
        "insufficient_sample_size",
        ("N_BELOW_MINIMUM", "GENUINE_EVIDENCE_N_BELOW_MINIMUM"),
        "Research/EmpiricalScience",
        "Collect or construct a larger target-blind/prospective held-out set before scoring.",
    ),
    (
        "source_separation_failure",
        (
            "SOURCE_SEPARATION",
            "PRE_TARGET_LOCK",
            "TARGET_HIDDEN",
            "TRAINING_AND_TARGET",
            "TRAINING_TARGET_SOURCE_OVERLAP",
            "TRAINING_OR_TARGET_SOURCE_DUPLICATE",
        ),
        "Research/EmpiricalScience",
        "Rebuild the protocol with separate training and target sources, pre-target lock, and hidden target values.",
    ),
    (
        "comparator_or_residual_failure",
        (
            "COMPARATOR",
            "RESIDUAL",
            "SUPERIORITY_MARGIN",
            "MODEL_RESIDUAL",
        ),
        "Research/EmpiricalScience",
        "Re-score OC and comparator under the same pre-registered residual metric and uncertainty method.",
    ),
    (
        "negative_control_failure",
        ("NEGATIVE_CONTROL",),
        "Review/ClaimBoundary",
        "Keep the claim blocked until declared negative controls fail as expected under the same replay.",
    ),
    (
        "falsifier_failure",
        ("FALSIFIER",),
        "Review/ClaimBoundary",
        "Add explicit falsifier conditions and keep them active even when the candidate evidence fails.",
    ),
    (
        "schema_or_identity_failure",
        (
            "MISSING_FIELD",
            "SCHEMA_ID",
            "RELEASE_ID",
            "CAPABILITY_OWNER",
            "UNKNOWN_DOMAIN",
            "DUPLICATE_EVIDENCE_PACK_ID",
            "SAMPLE_PACK",
        ),
        "Logion IT/Research",
        "Repair the evidence-pack generator contract; do not hand-edit the pack into compliance.",
    ),
    (
        "grand_support_not_authorized",
        ("GRAND_TOE_SUPPORT",),
        "Review/ClaimBoundary",
        "Do not register bounded or self-declared weak evidence as grand support; either upgrade the evidence or demote the promoted claim.",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def failure_class(failure: str) -> tuple[str, str, str]:
    normalized = failure.upper()
    for class_id, needles, owner, required_repair in FAILURE_CLASS_RULES:
        if any(needle in normalized for needle in needles):
            return class_id, owner, required_repair
    return (
        "unclassified_evidence_failure",
        "Research/EmpiricalScience",
        "Inspect the strict gate failure and add a class-specific automated repair before retrying.",
    )


def registry_refs(registry: dict[str, Any]) -> list[str]:
    refs = registry.get("evidence_pack_refs", [])
    if not isinstance(refs, list):
        return []
    return ordered_unique([str(ref).replace("\\", "/") for ref in refs if isinstance(ref, str) and ref.strip()])


def build_work_orders(report: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in report.get("candidate_rows", []):
        if not isinstance(row, dict) or row.get("valid_for_grand_support") is True:
            continue
        domain = str(row.get("domain") or "unknown")
        source_ref = str(row.get("source_ref") or "")
        for failure in row.get("failures", []):
            class_id, owner, required_repair = failure_class(str(failure))
            key = (domain, class_id, owner)
            item = grouped.setdefault(
                key,
                {
                    "work_order_id": f"OC133-GRAND-EVIDENCE-REPAIR-{domain.upper()}-{class_id.upper()}",
                    "domain": domain,
                    "failure_class": class_id,
                    "owner_capability": owner,
                    "status": "OPEN",
                    "required_repair": required_repair,
                    "candidate_refs": [],
                    "failure_examples": [],
                    "before_predicate": "candidate evidence pack fails validation.grand_science.evidence_pack_factory.pack_failure_reasons",
                    "after_predicate": "the same pack or successor pack validates with valid_for_grand_support=true and is registered by this sync factory",
                    "closure_evidence_required": [
                        "candidate row valid_for_grand_support=true",
                        "registered evidence_pack_ref points to the validated pack",
                        "grand empirical gate re-audits the domain without this failure class",
                    ],
                    "artifact_exists_is_not_closure": True,
                    **NO_SEND_LOCKS,
                },
            )
            item["candidate_refs"] = ordered_unique([*item["candidate_refs"], source_ref])
            item["failure_examples"] = ordered_unique([*item["failure_examples"], str(failure)])

    rows = sorted(grouped.values(), key=lambda item: (item["domain"], item["failure_class"], item["work_order_id"]))
    return {
        "schema_id": WORK_ORDER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": utc_now(),
        "capability_owner": CAPABILITY_OWNER,
        "work_order_total": len(rows),
        "open_work_order_total": len(rows),
        "rows": rows,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "closure_policy": "A work order closes only when the strict grand empirical gate validates the affected evidence pack; status tokens and artifact existence do not close it.",
    }


def apply_valid_refs(root: Path, registry: dict[str, Any], additions: list[str]) -> tuple[dict[str, Any], bool]:
    if not additions:
        return registry, False
    current = registry_refs(registry)
    merged = ordered_unique([*current, *additions])
    if merged == current:
        return registry, False
    updated = dict(registry)
    updated.setdefault("schema_id", "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1")
    updated.setdefault("release_id", RELEASE_ID)
    updated.setdefault("capability_owner", CAPABILITY_OWNER)
    updated["evidence_pack_refs"] = merged
    write_json(root / grand_factory.REGISTRY_REL, updated)
    return updated, True


def build_payload(root: Path, *, write: bool = False) -> dict[str, Any]:
    before_registry = read_json(root / grand_factory.REGISTRY_REL)
    before_refs = registry_refs(before_registry)
    report_before = grand_factory.build_grand_empirical_payload(root)
    candidate_rows = [row for row in report_before.get("candidate_rows", []) if isinstance(row, dict)]
    valid_refs = [
        str(row["source_ref"])
        for row in candidate_rows
        if row.get("valid_for_grand_support") is True and isinstance(row.get("source_ref"), str)
    ]
    additions = sorted(ref for ref in valid_refs if ref not in before_refs)
    after_registry, registry_updated = apply_valid_refs(root, before_registry, additions) if write else (before_registry, False)
    report_after = grand_factory.build_grand_empirical_payload(root) if registry_updated else report_before
    after_refs = registry_refs(after_registry)
    invalid_rows = [row for row in candidate_rows if row.get("valid_for_grand_support") is not True]
    failure_class_counts: dict[str, int] = defaultdict(int)
    for row in invalid_rows:
        failures = row.get("failures", [])
        if not isinstance(failures, list):
            continue
        for failure in failures:
            class_id, _, _ = failure_class(str(failure))
            failure_class_counts[class_id] += 1
    work_orders = build_work_orders(report_after)

    if additions:
        verdict = "REGISTRY_SYNC_APPLIED_VALID_PACKS" if write else "REGISTRY_SYNC_VALID_PACKS_AVAILABLE"
    elif report_after.get("blocked_domain_total", 0):
        verdict = "REGISTRY_SYNC_BLOCKED_PENDING_VALID_PACKS"
    else:
        verdict = "REGISTRY_SYNC_CURRENT"

    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": utc_now(),
        "capability_owner": CAPABILITY_OWNER,
        "registry_ref": grand_factory.REGISTRY_REL,
        "grand_empirical_report_ref": grand_factory.REPORT_JSON_REL,
        "work_orders_ref": WORK_ORDERS_REL,
        "candidate_total": len(candidate_rows),
        "valid_candidate_total": len(valid_refs),
        "invalid_candidate_total": len(invalid_rows),
        "registered_ref_total_before": len(before_refs),
        "registered_ref_total_after": len(after_refs),
        "new_valid_ref_total": len(additions),
        "new_valid_refs": additions,
        "registry_updated": registry_updated,
        "blocked_domain_total_after_sync": report_after.get("blocked_domain_total"),
        "grand_toe_support_allowed_after_sync": report_after.get("grand_toe_support_allowed"),
        "failure_class_counts": dict(sorted(failure_class_counts.items())),
        "open_repair_work_order_total": work_orders["open_work_order_total"],
        "no_send_locks": dict(NO_SEND_LOCKS),
        **NO_SEND_LOCKS,
        "verdict": verdict,
        "closure_policy": "The sync factory only registers evidence packs already accepted by the strict grand empirical validator. It never edits packs or upgrades grand_toe_support_allowed.",
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_json(root / WORK_ORDERS_REL, work_orders)
        write_markdown(root / REPORT_MD_REL, payload, work_orders)
    return payload


def write_markdown(path: Path, payload: dict[str, Any], work_orders: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Grand Evidence Registry Sync",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Candidate packs: `{payload['candidate_total']}`",
        f"Valid candidates: `{payload['valid_candidate_total']}`",
        f"New valid refs registered: `{payload['new_valid_ref_total']}`",
        f"Blocked domains after sync: `{payload['blocked_domain_total_after_sync']}`",
        f"Open repair work orders: `{payload['open_repair_work_order_total']}`",
        f"No-send: `{payload['no_send']}`",
        "",
        payload["closure_policy"],
        "",
        "## Failure Classes",
        "",
    ]
    if not payload["failure_class_counts"]:
        lines.append("- `none`")
    else:
        for class_id, count in payload["failure_class_counts"].items():
            lines.append(f"- `{class_id}`: `{count}`")
    lines.extend(["", "## Repair Work Orders", ""])
    if not work_orders.get("rows"):
        lines.append("- `none`")
    else:
        lines.extend(
            [
                "| Work Order | Domain | Failure Class | Owner | Candidate Refs |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in work_orders["rows"]:
            refs = ", ".join(f"`{ref}`" for ref in row.get("candidate_refs", []))
            lines.append(
                f"| `{row['work_order_id']}` | `{row['domain']}` | `{row['failure_class']}` | `{row['owner_capability']}` | {refs} |"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize strict grand empirical evidence packs into the held-out registry.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--write", action="store_true", help="write the sync report, work orders, and any validated registry additions")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(Path(args.root).resolve(), write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
