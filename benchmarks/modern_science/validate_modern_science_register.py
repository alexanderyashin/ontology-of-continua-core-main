from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "comparators" / "OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES = REPO_ROOT / "benchmarks" / "modern_science" / "OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
REPORT = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
REPORT_MD = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.md"
FACTORY = REPO_ROOT / "tools" / "oc133_modern_science_comparator_factory.py"
REQUIRED_DOMAINS = {"physics", "chemistry", "biology", "systems", "mathematics"}
REQUIRED_DISTINCTION_ROLES = {
    "incumbent_modern_science_source",
    "oc_result",
    "comparator_result",
    "benchmark_predicate",
    "uncertainty_fairness",
    "blocker_reason",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(path: Path) -> str:
    data = path.read_text(encoding="utf-8").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_factory() -> Any:
    spec = importlib.util.spec_from_file_location("oc133_modern_science_comparator_factory", FACTORY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factory: {FACTORY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    register = load_json(REGISTER)
    lanes = load_json(LANES)
    report = load_json(REPORT)
    factory = load_factory()
    expected_payloads = factory.build_all(REPO_ROOT)
    expected_matrix = expected_payloads[factory.REGISTER_REL]["domain_evidence_matrix"]

    if register.get("superiority_certified_total") != 0:
        errors.append("register certifies superiority")
    if report.get("release_promotion_allowed") is not False:
        errors.append("report allows release promotion")
    if "BLOCKED" not in str(register.get("current_release_state", "")):
        errors.append("register current release state is not blocked")
    if "BLOCKED" not in str(report.get("verdict", "")):
        errors.append("report verdict is not blocked")
    if lanes.get("certified_superiority_lane_total") != 0:
        errors.append("benchmark lanes certify superiority")

    lane_by_id = {row["lane_id"]: row for row in lanes.get("lanes", [])}
    if register.get("row_total") != len(register.get("rows", [])):
        errors.append("register row_total mismatch")
    if lanes.get("lane_total") != len(lanes.get("lanes", [])):
        errors.append("lanes lane_total mismatch")
    if register.get("register_factory_ref") != "tools/oc133_modern_science_comparator_factory.py":
        errors.append("register missing comparator factory ref")
    if report.get("register_factory_ref") != "tools/oc133_modern_science_comparator_factory.py":
        errors.append("report missing comparator factory ref")
    if register.get("domain_evidence_matrix") != expected_matrix:
        errors.append("register domain evidence matrix is not factory-synchronized")
    if report.get("domain_evidence_matrix") != expected_matrix:
        errors.append("report domain evidence matrix is not factory-synchronized")
    if lanes != expected_payloads[factory.LANES_REL]:
        errors.append("benchmark lanes are not factory-synchronized")
    if register != expected_payloads[factory.REGISTER_REL]:
        errors.append("register is not factory-synchronized")
    if report != expected_payloads[factory.REPORT_JSON_REL]:
        errors.append("report is not factory-synchronized")
    if REPORT_MD.read_text(encoding="utf-8") != expected_payloads[factory.REPORT_MD_REL]["text"]:
        errors.append("markdown report is not factory-synchronized")
    if set(register.get("required_domain_distinctions", [])) != REQUIRED_DISTINCTION_ROLES:
        errors.append("register required domain distinction roles mismatch")
    if report.get("executable_validation", {}).get("commands") != [
        "python tools/oc133_modern_science_comparator_factory.py --check",
        "python benchmarks/modern_science/validate_modern_science_register.py",
    ]:
        errors.append("report executable validation commands mismatch")

    for row in register.get("rows", []):
        row_id = row.get("row_id", "<missing>")
        if row.get("superiority_claim_status") != "NOT_CERTIFIED":
            errors.append(f"{row_id} has non-blocked superiority status")
        if row.get("release_effect") != "BLOCK_RELEASE_PROMOTION_FOR_SUPERIORITY":
            errors.append(f"{row_id} does not block release promotion")
        if not row.get("source_refs"):
            errors.append(f"{row_id} has no source refs")
        if not row.get("blocking_predicates"):
            errors.append(f"{row_id} has no blocking predicates")
        if not row.get("evidence_distinction_ref"):
            errors.append(f"{row_id} has no evidence distinction ref")
        if not row.get("work_order_decomposition_ref"):
            errors.append(f"{row_id} has no work-order decomposition ref")

        lane_id = row.get("lane_id")
        lane = lane_by_id.get(lane_id)
        if lane is None:
            errors.append(f"{row_id} references missing lane {lane_id}")
        elif lane.get("current_verdict") != "BLOCKED_NO_SUPERIORITY_CERTIFIED":
            errors.append(f"{lane_id} lane verdict is not blocked")

        for source in row.get("source_refs", []):
            ref = source.get("local_source_capsule_ref")
            if not ref:
                errors.append(f"{row_id} source ref missing local capsule")
                continue
            path = REPO_ROOT / ref
            if not path.exists():
                errors.append(f"{row_id} source capsule missing: {ref}")
                continue
            expected_hash = source.get("local_source_capsule_sha256")
            if expected_hash and expected_hash != sha256_text(path):
                errors.append(f"{row_id} source capsule hash mismatch: {ref}")

    for lane in lanes.get("lanes", []):
        lane_id = lane.get("lane_id", "<missing>")
        statuses = lane.get("current_predicate_status", {})
        if not statuses:
            errors.append(f"{lane_id} has no predicate status map")
        if all(statuses.values()):
            errors.append(f"{lane_id} has all predicates true despite blocked verdict")
        if not lane.get("blocked_by"):
            errors.append(f"{lane_id} has no blocked_by predicates")
        role_bindings = lane.get("result_role_bindings", {})
        if set(role_bindings) != REQUIRED_DISTINCTION_ROLES:
            errors.append(f"{lane_id} result role bindings mismatch")

    matrix = register.get("domain_evidence_matrix", [])
    if len(matrix) != len(REQUIRED_DOMAINS):
        errors.append("domain evidence matrix row count mismatch")
    observed_domains = {str(row.get("domain")) for row in matrix if isinstance(row, dict)}
    if observed_domains != REQUIRED_DOMAINS:
        errors.append("domain evidence matrix domain set mismatch")
    work_order_total = 0
    for matrix_row in matrix:
        domain = matrix_row.get("domain", "<missing>")
        if set(matrix_row.get("distinction_roles_present", [])) != REQUIRED_DISTINCTION_ROLES:
            errors.append(f"{domain} distinction roles mismatch")
        for role in REQUIRED_DISTINCTION_ROLES:
            if not matrix_row.get(role):
                errors.append(f"{domain} missing {role}")
        oc_result = matrix_row.get("oc_result", {})
        comparator_result = matrix_row.get("comparator_result", {})
        benchmark = matrix_row.get("benchmark_predicate", {})
        uncertainty = matrix_row.get("uncertainty_fairness", {})
        blocker = matrix_row.get("blocker_reason", {})
        decision = matrix_row.get("superiority_decision", {})
        if oc_result.get("result_kind") != "BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY":
            errors.append(f"{domain} OC result kind is not bounded")
        if not oc_result.get("result_ref") or not oc_result.get("claim_id"):
            errors.append(f"{domain} OC result is not bound to a source ref")
        if not comparator_result.get("baseline_name") or comparator_result.get("comparator_residual") is None:
            errors.append(f"{domain} comparator result missing baseline or residual")
        if comparator_result.get("result_ref") == "":
            errors.append(f"{domain} comparator result missing source ref")
        if not benchmark.get("certification_predicates") or "BLOCKED" not in str(benchmark.get("current_verdict", "")):
            errors.append(f"{domain} benchmark predicate is not blocked")
        if uncertainty.get("fairness_verdict") != "BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY":
            errors.append(f"{domain} fairness verdict is not blocked")
        if uncertainty.get("predeclared_comparator_present") is not True:
            errors.append(f"{domain} lacks predeclared comparator")
        if uncertainty.get("negative_control_rejected") is not True:
            errors.append(f"{domain} lacks rejected negative control")
        if not blocker.get("blocked_by") or blocker.get("superiority_claim_status") != "NOT_CERTIFIED":
            errors.append(f"{domain} blocker reason missing or non-blocked")
        if decision.get("certified") is not False or decision.get("status") != "NOT_CERTIFIED":
            errors.append(f"{domain} superiority decision is not blocked")
        work_orders = matrix_row.get("work_order_decomposition", [])
        if not work_orders:
            errors.append(f"{domain} has no work-order decomposition")
        work_order_total += len(work_orders)

    report_work_orders = report.get("work_order_decomposition", [])
    if len(report_work_orders) != work_order_total:
        errors.append("report work-order decomposition total mismatch")
    if report.get("domain_evidence_matrix_summary", {}).get("work_order_step_total") != work_order_total:
        errors.append("report work-order summary mismatch")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern science superiority register remains source-backed and blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
