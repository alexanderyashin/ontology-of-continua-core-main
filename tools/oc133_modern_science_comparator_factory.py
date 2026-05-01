from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

REGISTER_REL = "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.md"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
NUMERIC_REPLAY_REL = "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
GRAND_EMPIRICAL_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"

REQUIRED_DOMAINS = ("physics", "chemistry", "biology", "systems", "mathematics")
DISTINCTION_ROLES = (
    "incumbent_modern_science_source",
    "oc_result",
    "comparator_result",
    "benchmark_predicate",
    "uncertainty_fairness",
    "blocker_reason",
)
FACTORY_REF = "tools/oc133_modern_science_comparator_factory.py"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def first_ref(refs: list[str], prefix: str) -> str:
    for ref in refs:
        if str(ref).startswith(prefix):
            return str(ref)
    return ""


def ref_id(ref: str) -> str:
    return ref.rsplit("::", 1)[-1] if "::" in ref else ref


def row_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if isinstance(row, dict) and row.get(key)}


def rows_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get(key):
            grouped.setdefault(str(row.get(key)), []).append(row)
    return grouped


def numeric_value(row: dict[str, Any], key: str) -> float | None:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return None


def result_beats_comparator(row: dict[str, Any]) -> bool:
    residual = numeric_value(row, "residual")
    comparator_residual = numeric_value(row, "comparator_residual")
    if residual is None or comparator_residual is None:
        return False
    return comparator_residual > residual


def result_within_uncertainty(row: dict[str, Any]) -> bool:
    residual = numeric_value(row, "residual")
    uncertainty = numeric_value(row, "uncertainty")
    if residual is None or uncertainty is None:
        return False
    return residual <= uncertainty


def work_order_steps(domain: str, blocked_by: list[str], grand_blockers: list[str]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(predicate: str, action: str, required_artifact: str) -> None:
        if predicate in seen:
            return
        seen.add(predicate)
        steps.append(
            {
                "domain": domain,
                "blocking_predicate": predicate,
                "owner_capability": "Logion Research/PriorArt",
                "required_action": action,
                "required_artifact": required_artifact,
                "closure_rule": "Record source-backed evidence and rerun validate_modern_science_register; do not flip superiority status unless every certification predicate passes.",
            }
        )

    for predicate in blocked_by:
        if predicate == "independent_replay_passes_from_clean_checkout":
            add(
                predicate,
                "Run an independent clean-checkout replay with command, output tail, artifact hashes, and environment note recorded.",
                "clean-checkout replay record bound to the relevant OC result and comparator baseline",
            )
        elif predicate in {"domain_relevance_exceeds_exact_standard_replay", "result_is_not_merely_exact_standard_replay"}:
            add(
                predicate,
                "Replace exact reference-standard replay with a domain-relevant held-out or prospective physics benchmark before scoring.",
                "physics benchmark protocol separating CODATA/SI reference replay from candidate model performance",
            )
        elif predicate in {"domain_relevance_exceeds_curated_field_reconstruction", "not_a_curated_field_copy"}:
            add(
                predicate,
                "Separate curated-field parser replay from a chemistry benchmark whose targets, baselines, uncertainty, and negative controls are declared before scoring.",
                "chemistry benchmark protocol not reducible to NIST/PubChem field copying",
            )
        elif predicate == "biological_mechanism_test_present":
            add(
                predicate,
                "Add a source-backed biological mechanism benchmark instead of repository pagination/count reconstruction.",
                "biology mechanism benchmark with declared comparator, uncertainty, negative control, and falsifier",
            )
        elif predicate == "prospective_or_time-locked_protocol_present":
            add(
                predicate,
                "Add a prospective or time-locked WDI/systems protocol with comparator and scoring locked before the target is read.",
                "systems prospective or time-locked benchmark protocol and replay record",
            )
        elif predicate == "machine_checked_theorem_scope_matches_public_claim":
            add(
                predicate,
                "Bind public mathematical claim scope to machine-checked Lean/formal artifacts and an independently replayed proof surface.",
                "formal-scope binding record covering Lean build, finite witnesses, and public wording",
            )
        else:
            add(
                predicate,
                "Provide source-backed evidence for the blocking predicate before any superiority certification attempt.",
                "predicate-specific evidence record",
            )

    for blocker in grand_blockers:
        add(
            blocker,
            "Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.",
            "grand-science evidence pack accepted by the strict empirical gate",
        )
    return steps


def build_domain_evidence_matrix(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or repo_root()
    register = load_json(root / REGISTER_REL)
    lanes = load_json(root / LANES_REL)
    target_blind = load_json(root / TARGET_BLIND_REL)
    numeric_replay = load_json(root / NUMERIC_REPLAY_REL)
    grand_empirical = load_json(root / GRAND_EMPIRICAL_REL)

    lanes_by_id = row_by(lanes.get("lanes", []), "lane_id")
    target_by_id = row_by(target_blind.get("rows", []), "claim_id")
    target_by_domain = row_by(target_blind.get("rows", []), "lane")
    numeric_by_domain = rows_by(numeric_replay.get("rows", []), "lane")
    grand_domains = row_by(grand_empirical.get("domains", []), "domain")
    grand_baselines = row_by(grand_empirical.get("bounded_baseline_rows", []), "domain")

    matrix: list[dict[str, Any]] = []
    for row in register.get("rows", []):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain"))
        oc_refs = [str(ref) for ref in row.get("oc_current_evidence_refs", []) if ref]
        target_ref = first_ref(oc_refs, TARGET_BLIND_REL)
        oc_row = target_by_id.get(ref_id(target_ref), {}) or target_by_domain.get(domain, {})
        lane = lanes_by_id.get(str(row.get("lane_id")), {})
        numeric_rows = numeric_by_domain.get(domain, [])
        grand_row = grand_domains.get(domain, {})
        grand_baseline = grand_baselines.get(domain, {})
        blocked_by = list(dict.fromkeys([*lane.get("blocked_by", []), *row.get("blocking_predicates", [])]))
        grand_blockers = [str(blocker) for blocker in grand_row.get("blockers", []) if blocker]

        incumbent_sources = [
            {
                "title": source.get("title"),
                "url": source.get("url"),
                "source_date": source.get("source_date"),
                "local_source_capsule_ref": source.get("local_source_capsule_ref"),
                "local_source_capsule_sha256": source.get("local_source_capsule_sha256"),
            }
            for source in row.get("source_refs", [])
            if isinstance(source, dict)
        ]

        replay_controls = [
            {
                "result_ref": f"{NUMERIC_REPLAY_REL}::{control.get('claim_id')}",
                "claim_scope": control.get("claim_scope"),
                "replay_residual": control.get("replay_residual"),
                "comparator_residual": control.get("comparator_residual"),
                "performance_metric_allowed": control.get("performance_metric_allowed"),
                "promotion_status": control.get("promotion_status"),
            }
            for control in numeric_rows
        ]

        matrix.append(
            {
                "domain": domain,
                "row_id": row.get("row_id"),
                "lane_id": row.get("lane_id"),
                "predicate_id": lane.get("predicate_id"),
                "distinction_roles_present": list(DISTINCTION_ROLES),
                "incumbent_modern_science_source": {
                    "incumbent": row.get("incumbent_modern_science"),
                    "accepted_capacity": row.get("accepted_incumbent_capacity"),
                    "source_refs": incumbent_sources,
                    "source_role": "incumbent modern-science capacity only; not absence, novelty, or superiority evidence",
                },
                "oc_result": {
                    "result_ref": target_ref or first_ref(oc_refs, "validation/"),
                    "claim_id": oc_row.get("claim_id"),
                    "result_kind": "BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY",
                    "dataset_snapshot_ref": oc_row.get("dataset_snapshot_ref"),
                    "formula_or_model": oc_row.get("formula"),
                    "predicted_value": oc_row.get("predicted_value"),
                    "observed_value": oc_row.get("observed_value"),
                    "residual": oc_row.get("residual"),
                    "uncertainty": oc_row.get("uncertainty"),
                    "prediction_support_allowed": oc_row.get("prediction_support_allowed"),
                    "empirical_support_allowed": oc_row.get("empirical_support_allowed"),
                    "support_scope": oc_row.get("support_scope"),
                    "snapshot_sha256": oc_row.get("snapshot_sha256"),
                    "replay_hash": oc_row.get("replay_hash"),
                    "current_boundary": row.get("oc_current_evidence_boundary"),
                },
                "comparator_result": {
                    "result_ref": target_ref or first_ref(oc_refs, "validation/"),
                    "baseline_name": oc_row.get("comparator_baseline"),
                    "comparator_prediction": oc_row.get("comparator_prediction"),
                    "comparator_residual": oc_row.get("comparator_residual"),
                    "negative_control": oc_row.get("negative_control"),
                    "negative_control_rejected": oc_row.get("negative_control_rejected"),
                    "falsifier": oc_row.get("falsifier"),
                    "beats_comparator_on_bounded_row": result_beats_comparator(oc_row),
                    "replay_controls_not_performance": replay_controls,
                },
                "benchmark_predicate": {
                    "benchmark_predicate_ref": row.get("benchmark_predicate_ref"),
                    "task": lane.get("task"),
                    "metric_family": lane.get("metric_family"),
                    "certification_predicates": lane.get("certification_predicates", []),
                    "current_predicate_status": lane.get("current_predicate_status", {}),
                    "current_verdict": lane.get("current_verdict"),
                    "allowed_current_claim": lane.get("allowed_current_claim"),
                },
                "uncertainty_fairness": {
                    "uncertainty_declared": oc_row.get("uncertainty") is not None,
                    "uncertainty": oc_row.get("uncertainty"),
                    "residual_within_uncertainty": result_within_uncertainty(oc_row),
                    "source_separation_mode": "target_blind" if oc_row.get("target_blind_split") else "not_recorded",
                    "split_policy": oc_row.get("target_blind_split") or oc_row.get("heldout_split") or oc_row.get("heldout_policy"),
                    "predeclared_metric_present": bool(lane.get("metric_family")),
                    "predeclared_comparator_present": bool(oc_row.get("comparator_baseline")),
                    "negative_control_rejected": oc_row.get("negative_control_rejected"),
                    "fairness_limitations": [
                        "bounded baseline row only; grand_toe_support_allowed is false",
                        "current OC evidence boundary prevents incumbent-superiority wording",
                        *grand_blockers,
                    ],
                    "fairness_verdict": "BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY",
                },
                "blocker_reason": {
                    "superiority_claim_status": row.get("superiority_claim_status"),
                    "release_effect": row.get("release_effect"),
                    "blocked_by": blocked_by,
                    "grand_empirical_blockers": grand_blockers,
                    "domain_blocker_summary": row.get("oc_current_evidence_boundary"),
                    "allowed_current_wording": row.get("allowed_current_wording"),
                    "forbidden_wording": row.get("forbidden_wording", []),
                },
                "superiority_decision": {
                    "status": row.get("superiority_claim_status"),
                    "certified": False,
                    "release_promotion_allowed": False,
                    "reason": "Source-backed bounded reconstruction and comparator rows exist, but the strict superiority predicates are not all satisfied.",
                },
                "work_order_decomposition": work_order_steps(domain, blocked_by, grand_blockers),
                "bounded_baseline_grand_gate": {
                    "bounded_baseline_ref": f"{GRAND_EMPIRICAL_REL}::bounded_baseline_rows::{domain}" if grand_baseline else "",
                    "classification": grand_baseline.get("classification"),
                    "grand_toe_support_allowed": grand_baseline.get("grand_toe_support_allowed"),
                    "minimum_n": grand_row.get("minimum_n"),
                    "valid_n": grand_row.get("valid_n"),
                    "status": grand_row.get("status"),
                },
            }
        )
    return matrix


def build_work_order_decomposition(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    work_orders: list[dict[str, Any]] = []
    for row in matrix:
        work_orders.extend(row.get("work_order_decomposition", []))
    return work_orders


def matrix_summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "domain_total": len(matrix),
        "domains": [row.get("domain") for row in matrix],
        "required_distinction_roles": list(DISTINCTION_ROLES),
        "superiority_certified_total": sum(1 for row in matrix if row.get("superiority_decision", {}).get("certified") is True),
        "blocked_superiority_total": sum(1 for row in matrix if row.get("superiority_decision", {}).get("certified") is not True),
        "work_order_step_total": sum(len(row.get("work_order_decomposition", [])) for row in matrix),
    }


def enrich_lanes(lanes: dict[str, Any], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    payload = copy.deepcopy(lanes)
    by_lane = {row.get("lane_id"): row for row in matrix}
    payload["result_role_contract"] = {
        "factory_ref": FACTORY_REF,
        "required_roles": list(DISTINCTION_ROLES),
        "policy": "Lane rows bind role names to source-backed fields so an OC result cannot be confused with an incumbent source or comparator baseline.",
    }
    for lane in payload.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        matrix_row = by_lane.get(lane.get("lane_id"), {})
        oc_result = matrix_row.get("oc_result", {})
        comparator_result = matrix_row.get("comparator_result", {})
        blocker_reason = matrix_row.get("blocker_reason", {})
        lane["result_role_bindings"] = {
            "incumbent_modern_science_source": "incumbent_source_refs",
            "oc_result": oc_result.get("result_ref"),
            "comparator_result": {
                "result_ref": comparator_result.get("result_ref"),
                "baseline_name": comparator_result.get("baseline_name"),
            },
            "benchmark_predicate": lane.get("predicate_id"),
            "uncertainty_fairness": {
                "metric_family": lane.get("metric_family"),
                "negative_control": comparator_result.get("negative_control"),
            },
            "blocker_reason": blocker_reason.get("blocked_by", []),
        }
    return payload


def enrich_register(register: dict[str, Any], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    payload = copy.deepcopy(register)
    payload["register_factory_ref"] = FACTORY_REF
    payload["automatic_distinction_policy"] = (
        "The factory derives per-domain role separation from local source capsules, benchmark lanes, target-blind rows, "
        "numeric replay QA rows, and strict grand empirical blockers. It does not certify superiority."
    )
    payload["required_domain_distinctions"] = list(DISTINCTION_ROLES)
    payload["domain_evidence_matrix"] = matrix
    payload["domain_evidence_matrix_summary"] = matrix_summary(matrix)
    by_row_id = {row.get("row_id"): row for row in matrix}
    for row in payload.get("rows", []):
        if isinstance(row, dict) and row.get("row_id") in by_row_id:
            matrix_row = by_row_id[row["row_id"]]
            row["evidence_distinction_ref"] = f"{REGISTER_REL}::domain_evidence_matrix::{matrix_row.get('domain')}"
            row["work_order_decomposition_ref"] = f"{REPORT_JSON_REL}::work_order_decomposition::{matrix_row.get('domain')}"
    return payload


def enrich_report(report: dict[str, Any], matrix: list[dict[str, Any]]) -> dict[str, Any]:
    payload = copy.deepcopy(report)
    payload["register_factory_ref"] = FACTORY_REF
    payload["domain_evidence_matrix_ref"] = f"{REGISTER_REL}::domain_evidence_matrix"
    payload["domain_evidence_matrix"] = matrix
    payload["domain_evidence_matrix_summary"] = matrix_summary(matrix)
    payload["executable_validation"] = {
        "commands": [
            "python tools/oc133_modern_science_comparator_factory.py --check",
            "python benchmarks/modern_science/validate_modern_science_register.py",
        ],
        "policy": "Validation must keep the report blocked unless every source-backed per-domain superiority predicate is satisfied.",
    }
    payload["work_order_decomposition"] = build_work_order_decomposition(matrix)
    payload["work_order_policy"] = (
        "These steps decompose the blocker without certifying superiority; each closure artifact must be source-backed and replayable."
    )
    payload["verdict"] = "BLOCKED_NO_MODERN_SCIENCE_SUPERIORITY_CERTIFIED"
    payload["release_promotion_allowed"] = False
    payload["superiority_certified_total"] = 0
    payload["blocked_superiority_total"] = len(matrix)
    return payload


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Modern Science Superiority Report",
        "",
        "Verdict: `BLOCKED_NO_MODERN_SCIENCE_SUPERIORITY_CERTIFIED`",
        "",
        "Release promotion allowed: `false`",
        "",
        "This report records source-backed comparator lanes only. It does not certify OC Core 1.3.3 superiority over modern science.",
        "",
        "| Domain | Incumbent source | OC result | Comparator result | Benchmark predicate | Uncertainty/fairness | Blocker reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report.get("domain_evidence_matrix", []):
        source_titles = ", ".join(
            str(source.get("title"))
            for source in row.get("incumbent_modern_science_source", {}).get("source_refs", [])
            if source.get("title")
        )
        oc_result = row.get("oc_result", {})
        comparator_result = row.get("comparator_result", {})
        benchmark = row.get("benchmark_predicate", {})
        fairness = row.get("uncertainty_fairness", {})
        blocker = row.get("blocker_reason", {})
        lines.append(
            "| `{domain}` | {source_titles} | `{oc_kind}` residual `{residual}` | `{baseline}` residual `{comp_residual}` | `{predicate}` `{verdict}` | uncertainty `{uncertainty}`, `{fairness_verdict}` | `{blocked_by}` |".format(
                domain=row.get("domain"),
                source_titles=source_titles,
                oc_kind=oc_result.get("result_kind"),
                residual=oc_result.get("residual"),
                baseline=comparator_result.get("baseline_name"),
                comp_residual=comparator_result.get("comparator_residual"),
                predicate=row.get("predicate_id"),
                verdict=benchmark.get("current_verdict"),
                uncertainty=fairness.get("uncertainty"),
                fairness_verdict=fairness.get("fairness_verdict"),
                blocked_by=", ".join(str(item) for item in blocker.get("blocked_by", [])),
            )
        )
    lines.extend(
        [
            "",
            "Blocking summary:",
            "",
        ]
    )
    for item in report.get("blocking_summary", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Executable validation:",
            "",
        ]
    )
    for command in report.get("executable_validation", {}).get("commands", []):
        lines.append(f"- `{command}`")
    lines.extend(
        [
            "",
            "Work-order decomposition:",
            "",
        ]
    )
    for item in report.get("work_order_decomposition", []):
        lines.append(
            "- `{domain}` `{predicate}`: {action}".format(
                domain=item.get("domain"),
                predicate=item.get("blocking_predicate"),
                action=item.get("required_action"),
            )
        )
    lines.extend(
        [
            "",
            "Allowed current claim: OC Core 1.3.3 has source-backed comparator lanes and bounded reconstruction/QA predicates; it does not certify superiority to modern science.",
            "",
        ]
    )
    return "\n".join(lines)


def build_all(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or repo_root()
    matrix = build_domain_evidence_matrix(root)
    register = enrich_register(load_json(root / REGISTER_REL), matrix)
    lanes = enrich_lanes(load_json(root / LANES_REL), matrix)
    report = enrich_report(load_json(root / REPORT_JSON_REL), matrix)
    return {
        REGISTER_REL: register,
        LANES_REL: lanes,
        REPORT_JSON_REL: report,
        REPORT_MD_REL: {"text": render_markdown(report)},
    }


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    errors: list[str] = []
    for rel, payload in expected.items():
        path = root / rel
        if rel.endswith(".md"):
            actual_text = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual_text != payload["text"]:
                errors.append(f"{rel} is not synchronized with {FACTORY_REF}")
        else:
            actual = load_json(path)
            if actual != payload:
                errors.append(f"{rel} is not synchronized with {FACTORY_REF}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or check the OC133 modern-science comparator superiority register.")
    parser.add_argument("--write", action="store_true", help="Write generated register, benchmark lanes, and report files.")
    parser.add_argument("--check", action="store_true", help="Check generated files against the stored copies.")
    args = parser.parse_args()

    root = repo_root()
    if args.write:
        payloads = build_all(root)
        for rel, payload in payloads.items():
            path = root / rel
            if rel.endswith(".md"):
                path.write_text(payload["text"], encoding="utf-8", newline="\n")
            else:
                write_json(path, payload)
        print("modern science comparator register/report materialized; superiority remains blocked")
        return 0

    errors = check_stored(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern science comparator register/report factory check passed; superiority remains blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
