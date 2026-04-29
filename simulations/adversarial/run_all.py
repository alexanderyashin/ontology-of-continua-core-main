from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CASES = [
    ("ADV-K0-RAW-DISCRETENESS", "continuous raw states share rho-cell", "REJECT_RAW_DISCRETENESS_LEAK", ["FM-T133-K0-RES-NEG"]),
    ("ADV-LIVE-STATIC-LABEL", "static label without cycle", "REJECT_LIVE_STATUS", ["FM-T133-CYCLE-NEG"]),
    ("ADV-KZERO-NO-CAUSE", "k zero asserted without zero-cause", "REJECT_K_ZERO", ["FM-T133-K-ZERO-NEG"]),
    ("ADV-BOUNDARY-FAKE-METRIC", "logical boundary forced into metric", "REJECT_FAKE_METRIC", ["FM-T133-BOUNDARY-NEG"]),
    ("ADV-HYBRID-UNIVERSAL-DERIVATIVE", "rewrite state differentiated", "REJECT_SMOOTH_OVERREACH", ["FM-T133-HYBRID-PROOF-UPDATE-NEG"]),
    ("ADV-DIM-RANK-CONFLATION", "historical axis erased by rank drop", "REJECT_AXIS_ERASURE", ["FM-T133-DIM-NEG"]),
    ("ADV-ID-REBIRTH-AS-IDENTITY", "rebirth called same identity", "REJECT_IDENTITY_EQUIVOCATION", ["FM-T133-ID-NEG"]),
    ("ADV-MIN-REMOVE-BOUNDARY", "boundary component removed", "VERDICT_CHANGE_DETECTED", ["FM-MIN-boundaries"]),
    ("ADV-KLEVEL-COLLAPSE", "K3 reduced to K2 despite closure witness", "REDUCTION_FAILS_WITH_WITNESS", ["FM-KLEVEL-K2_to_K3"]),
    ("ADV-NOSEND-PUBLISH", "publish_allowed true with owner_approved false", "REJECT_PUBLIC_ACTION", ["ADV-NOSEND-PUBLISH"]),
]


def observed_from_evidence(case_id: str, evidence_rows: list[dict]) -> str:
    if not evidence_rows or any(row is None for row in evidence_rows):
        return "EVIDENCE_MISSING"
    if case_id == "ADV-MIN-REMOVE-BOUNDARY":
        return "VERDICT_CHANGE_DETECTED" if all(
            row.get("observed_keep_verdict") == "PASS" and row.get("observed_drop_verdict") == "FAIL"
            for row in evidence_rows
        ) else "NO_VERDICT_CHANGE"
    if case_id == "ADV-KLEVEL-COLLAPSE":
        return "REDUCTION_FAILS_WITH_WITNESS" if all(
            row.get("observed_reduction_verdict") == "FAILS_WITH_WITNESS"
            for row in evidence_rows
        ) else "REDUCTION_NOT_REJECTED"
    if case_id == "ADV-NOSEND-PUBLISH":
        return "REJECT_PUBLIC_ACTION" if all(
            row.get("observed_verdict") == "REJECT_PUBLIC_ACTION"
            for row in evidence_rows
        ) else "PUBLIC_ACTION_NOT_REJECTED"
    reject_label = {
        "ADV-K0-RAW-DISCRETENESS": "REJECT_RAW_DISCRETENESS_LEAK",
        "ADV-LIVE-STATIC-LABEL": "REJECT_LIVE_STATUS",
        "ADV-KZERO-NO-CAUSE": "REJECT_K_ZERO",
        "ADV-BOUNDARY-FAKE-METRIC": "REJECT_FAKE_METRIC",
        "ADV-HYBRID-UNIVERSAL-DERIVATIVE": "REJECT_SMOOTH_OVERREACH",
        "ADV-DIM-RANK-CONFLATION": "REJECT_AXIS_ERASURE",
        "ADV-ID-REBIRTH-AS-IDENTITY": "REJECT_IDENTITY_EQUIVOCATION",
    }.get(case_id, "REJECTED")
    return reject_label if all(row.get("observed_verdict") == "REJECT" for row in evidence_rows) else "ATTACK_NOT_REJECTED"


def build_report() -> dict:
    finite_cmd = [sys.executable, str(ROOT / "proofs" / "finite_model_checks" / "run_finite_model_checks.py")]
    finite_completed = subprocess.run(
        finite_cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=600,
    )
    finite_path = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
    finite_payload = json.loads(finite_path.read_text(encoding="utf-8"))
    finite_by_id = {row.get("case_id"): row for row in finite_payload.get("rows", [])}
    rows = []
    for case_id, attack, verdict, evidence_case_ids in CASES:
        evidence_rows = [finite_by_id.get(evidence_id) for evidence_id in evidence_case_ids]
        observed = observed_from_evidence(case_id, evidence_rows)
        rows.append({
            "case_id": case_id,
            "attack": attack,
            "expected_verdict": verdict,
            "evidence_case_ids": evidence_case_ids,
            "evidence_observed_values": [
                {
                    "case_id": evidence_id,
                    "observed_verdict": (finite_by_id.get(evidence_id) or {}).get("observed_verdict"),
                    "observed_drop_verdict": (finite_by_id.get(evidence_id) or {}).get("observed_drop_verdict"),
                    "observed_reduction_verdict": (finite_by_id.get(evidence_id) or {}).get("observed_reduction_verdict"),
                    "passed": (finite_by_id.get(evidence_id) or {}).get("passed"),
                }
                for evidence_id in evidence_case_ids
            ],
            "evidence_cases_passed": all((row or {}).get("passed") is True for row in evidence_rows),
            "observed_verdict": observed,
            "passed": observed == verdict,
        })
    finite_failed = finite_completed.returncode != 0 or finite_payload.get("failure_total", 1) != 0
    if finite_failed:
        rows.append({
            "case_id": "ADV-FINITE-RUNNER-FAILED",
            "attack": "finite semantic evaluator failed during adversarial run",
            "expected_verdict": "FINITE_RUNNER_PASS",
            "observed_verdict": "FINITE_RUNNER_FAIL",
            "evidence_case_ids": [],
            "passed": False,
            "finite_runner_returncode": finite_completed.returncode,
        })
    failure_total = sum(1 for row in rows if not row["passed"])
    return {
        "schema_id": "OC133_ADVERSARIAL_SIMULATION_REPORT_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "runner": "simulations/adversarial/run_all.py",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "finite_runner_ref": "proofs/finite_model_checks/run_finite_model_checks.py",
        "finite_runner_returncode": finite_completed.returncode,
        "finite_failure_total": finite_payload.get("failure_total"),
        "case_total": len(rows),
        "failure_total": failure_total,
        "rows": rows,
        "verdict": "PASS" if failure_total == 0 else "FAIL",
    }


def main() -> int:
    report = build_report()
    output = ROOT / "reports" / "OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report.get("failure_total") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
