from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "comparators" / "OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES = REPO_ROOT / "benchmarks" / "modern_science" / "OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
COVERAGE_REGISTER = REPO_ROOT / "comparators" / "modern_science" / "OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
COVERAGE_WORK_ORDERS = REPO_ROOT / "benchmarks" / "modern_science" / "OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
REPORT = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
REPORT_MD = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.md"
FACTORY = REPO_ROOT / "tools" / "oc133_modern_science_comparator_factory.py"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_factory() -> Any:
    spec = importlib.util.spec_from_file_location("oc133_modern_science_comparator_factory", FACTORY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factory: {FACTORY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    factory = load_factory()
    register = load_json(REGISTER)
    lanes = load_json(LANES)
    coverage = load_json(COVERAGE_REGISTER)
    work_orders = load_json(COVERAGE_WORK_ORDERS)
    report = load_json(REPORT)
    expected = factory.build_all(REPO_ROOT)

    if register != expected[factory.REGISTER_REL]:
        errors.append("register is not factory-synchronized")
    if lanes != expected[factory.LANES_REL]:
        errors.append("benchmark lanes are not factory-synchronized")
    if coverage != expected[factory.COVERAGE_REGISTER_REL]:
        errors.append("coverage register is not factory-synchronized")
    if work_orders != expected[factory.COVERAGE_WORK_ORDERS_REL]:
        errors.append("coverage work orders are not factory-synchronized")
    if report != expected[factory.REPORT_JSON_REL]:
        errors.append("report is not factory-synchronized")
    if REPORT_MD.read_text(encoding="utf-8") != expected[factory.REPORT_MD_REL]["text"]:
        errors.append("markdown report is not factory-synchronized")

    errors.extend(factory.validate_register_payload(register, REPO_ROOT))
    errors.extend(factory.validate_coverage_payload(coverage, work_orders))

    if register.get("superiority_certified_total") != 0:
        errors.append("legacy broad superiority counter must remain zero")
    if register.get("broad_modern_science_superiority_certified_total") != 0:
        errors.append("broad modern-science superiority must remain uncertified")
    if report.get("release_promotion_allowed") is not False:
        errors.append("report allows broad release promotion")
    if report.get("modern_science_comparator_superiority", {}).get("state") != "FAIL":
        errors.append("modern_science_comparator_superiority broad state is not FAIL")

    matrix = register.get("domain_evidence_matrix", [])
    if {row.get("domain") for row in matrix} != set(factory.EMPIRICAL_DOMAINS):
        errors.append("domain evidence matrix does not match empirical strict-pack domains")
    if register.get("benchmark_scoped_superiority_certified_total") != len(factory.EMPIRICAL_DOMAINS):
        errors.append("not every empirical domain has benchmark-scoped certification")
    if lanes.get("benchmark_scoped_certified_lane_total") != len(factory.EMPIRICAL_DOMAINS):
        errors.append("lane benchmark-scoped certification total mismatch")

    for row in matrix:
        domain = row.get("domain", "<missing>")
        strict_pack = row.get("strict_evidence_pack", {})
        certification = row.get("certification_verdict", {})
        if not strict_pack.get("ref", "").startswith("validation/heldout/grand_science/"):
            errors.append(f"{domain} is not bound to current heldout grand-science evidence")
        if "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json" in strict_pack.get("ref", ""):
            errors.append(f"{domain} still points at stale target-blind rows")
        if certification.get("benchmark_scoped_superiority", {}).get("certified") is not True:
            errors.append(f"{domain} benchmark-scoped superiority is not certified")
        if certification.get("broad_modern_science_superiority", {}).get("certified") is not False:
            errors.append(f"{domain} broad superiority is certified")
        if certification.get("benchmark_scoped_superiority", {}).get("scope") != "declared strict evidence pack baselines only":
            errors.append(f"{domain} benchmark certification scope is not narrow enough")

    broad_predicates = register.get("broad_claim_predicates", {})
    if all(broad_predicates.values()):
        errors.append("broad predicates unexpectedly all pass")
    replay = register.get("independent_clean_checkout_replay", {})
    if broad_predicates.get("independent_clean_checkout_replay_bound_to_register") is not True:
        errors.append("independent clean temp-tree replay predicate is not closed")
    if replay.get("status") != "PASS" or replay.get("satisfies_register_predicate") is not True:
        errors.append("independent replay certificate is not passing")
    if not replay.get("command_results") or not replay.get("selected_evidence_pack_sha256"):
        errors.append("independent replay is missing command or pack hash bindings")
    if replay.get("no_send_locks", {}).get("public_release_action_allowed") is not False:
        errors.append("independent replay public release lock is open")
    if (
        broad_predicates.get("independent_clean_checkout_replay_bound_to_register") is True
        and broad_predicates.get("coverage_extends_to_all_of_modern_science") is True
        and report.get("modern_science_comparator_superiority", {}).get("state") == "FAIL"
    ):
        errors.append("independent replay and coverage predicates are true but broad state remains FAIL")
    if broad_predicates.get("coverage_extends_to_all_of_modern_science") is not False:
        errors.append("all-modern-science coverage predicate should remain false")
    if coverage.get("coverage_gap_total", 0) <= 0:
        errors.append("coverage register must expose open modern-science gaps")
    if coverage.get("coverage_closure_decision", {}).get("coverage_extends_to_all_of_modern_science") is not False:
        errors.append("coverage closure must remain false while gaps remain")
    if work_orders.get("open_work_order_total") != coverage.get("coverage_gap_total"):
        errors.append("coverage work orders must enumerate every coverage gap")
    if report.get("coverage_gap_total") != coverage.get("coverage_gap_total"):
        errors.append("report coverage gap total mismatch")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern science register: benchmark-scoped strict-pack baselines pass; broad modern-science superiority remains blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
