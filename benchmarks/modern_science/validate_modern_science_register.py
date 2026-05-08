from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "comparators" / "OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES = REPO_ROOT / "benchmarks" / "modern_science" / "OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
COVERAGE_REGISTER = REPO_ROOT / "comparators" / "modern_science" / "OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
REPORT = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
REPORT_MD = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_file(errors: list[str], ref: str, label: str) -> None:
    if not ref:
        errors.append(f"{label} missing ref")
        return
    path = REPO_ROOT / ref
    if not path.exists():
        errors.append(f"{label} missing file: {ref}")


def main() -> int:
    errors: list[str] = []
    register = load_json(REGISTER)
    lanes = load_json(LANES)
    coverage = load_json(COVERAGE_REGISTER)
    report = load_json(REPORT)

    if REPORT_MD.exists() and not REPORT_MD.read_text(encoding="utf-8").strip():
        errors.append("markdown report is empty")

    for name, payload in {
        "register": register,
        "lanes": lanes,
        "coverage": coverage,
        "report": report,
    }.items():
        if payload.get("release_id") != "oc_core_1_3_3":
            errors.append(f"{name} release_id mismatch")
        if str(payload.get("version")) not in {"1.3.3", "1.4"}:
            errors.append(f"{name} version mismatch")

    broad_predicates = register.get("broad_claim_predicates", {})
    broad_pass = bool(broad_predicates) and all(value is True for value in broad_predicates.values())
    coverage_decision = coverage.get("coverage_closure_decision", {})
    report_decision = report.get("coverage_closure_decision", {})

    if register.get("coverage_gap_total") != coverage.get("coverage_gap_total"):
        errors.append("register coverage gap total mismatch")
    if report.get("coverage_gap_total") != coverage.get("coverage_gap_total"):
        errors.append("report coverage gap total mismatch")
    if coverage_decision.get("coverage_extends_to_all_of_modern_science") != broad_predicates.get("coverage_extends_to_all_of_modern_science"):
        errors.append("coverage predicate mismatch")
    if report_decision.get("coverage_extends_to_all_of_modern_science") != coverage_decision.get("coverage_extends_to_all_of_modern_science"):
        errors.append("report coverage predicate mismatch")

    if broad_pass:
        if register.get("modern_science_comparator_superiority", {}).get("state") != "PASS":
            errors.append("broad predicates pass but register state is not PASS")
        if report.get("modern_science_comparator_superiority", {}).get("state") != "PASS":
            errors.append("broad predicates pass but report state is not PASS")
        if report.get("release_promotion_allowed") is not True:
            errors.append("broad predicates pass but report release promotion is not derived true")
        if coverage.get("coverage_gap_total") != 0:
            errors.append("broad predicates pass but coverage gaps remain")
        if int(register.get("broad_modern_science_superiority_certified_total") or 0) != int(coverage.get("required_phenomenon_class_total") or 0):
            errors.append("broad certification total does not match declared phenomenon coverage")
    else:
        if register.get("modern_science_comparator_superiority", {}).get("state") == "PASS":
            errors.append("register reports PASS while broad predicates are incomplete")
        if report.get("release_promotion_allowed") is True:
            errors.append("report allows broad release promotion while broad predicates are incomplete")

    matrix = register.get("domain_evidence_matrix", [])
    if not matrix:
        errors.append("domain evidence matrix is empty")
    matrix_domains = {row.get("domain") for row in matrix if row.get("domain")}
    if int(register.get("benchmark_scoped_superiority_certified_total") or 0) != len(matrix_domains):
        errors.append("benchmark scoped certification total does not match domain matrix")
    if int(lanes.get("benchmark_scoped_certified_lane_total") or 0) < len(matrix_domains):
        errors.append("lane benchmark scoped certification total is too small")

    for row in matrix:
        domain = row.get("domain", "<missing>")
        strict_pack = row.get("strict_evidence_pack", {})
        certification = row.get("certification_verdict", {})
        ref = strict_pack.get("ref", "")
        require_file(errors, ref, f"{domain} strict evidence pack")
        if "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json" in ref:
            errors.append(f"{domain} still points at stale target-blind rows")
        if certification.get("benchmark_scoped_superiority", {}).get("certified") is not True:
            errors.append(f"{domain} benchmark-scoped superiority is not certified")
        if certification.get("benchmark_scoped_superiority", {}).get("scope") != "declared strict evidence pack baselines only":
            errors.append(f"{domain} benchmark certification scope is not narrow enough")

    for row in coverage.get("current_empirical_lane_mapping", []):
        lane = row.get("lane_id", "<missing>")
        require_file(errors, row.get("strict_evidence_pack_ref", ""), f"{lane} strict evidence pack")
        if row.get("benchmark_scoped_certified") is not True:
            errors.append(f"{lane} benchmark-scoped certification is not true")

    replay = register.get("independent_clean_checkout_replay", {})
    if replay.get("status") != "PASS" or replay.get("satisfies_register_predicate") is not True:
        errors.append("independent clean checkout replay is not passing")
    require_file(errors, replay.get("report_ref", ""), "independent clean checkout replay report")
    if replay.get("no_send_locks", {}).get("public_release_action_allowed") is not False:
        errors.append("independent replay public release lock is open")

    for domain, ref in register.get("current_evidence_pack_refs", {}).items():
        require_file(errors, ref, f"{domain} current evidence pack")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        "modern science register: declared-taxonomy broad superiority pass"
        if broad_pass
        else "modern science register: benchmark-scoped strict-pack baselines pass; broad modern-science superiority remains blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
