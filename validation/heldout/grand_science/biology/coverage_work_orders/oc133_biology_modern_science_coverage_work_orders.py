from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_BIOLOGY_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Research/Biology Coverage"

SCRIPT_REL = (
    "validation/heldout/grand_science/biology/coverage_work_orders/"
    "oc133_biology_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/biology/coverage_work_orders/"
    "OC133_BIOLOGY_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
MODERN_PROTOCOL_REL = "benchmarks/modern_science/protocols/OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_BIOLOGY.json"
TARGET_EVIDENCE_PACK_REL = "validation/heldout/grand_science/biology/target_evidence/biology_target_evidence_candidate_pack.json"
TARGET_EVIDENCE_PROTOCOL_REL = "validation/heldout/grand_science/biology/target_evidence/OC133_BIOLOGY_TARGET_EVIDENCE_PROTOCOL.json"
TARGET_EVIDENCE_REPORT_REL = "validation/heldout/grand_science/biology/target_evidence/OC133_BIOLOGY_TARGET_EVIDENCE_REPORT.json"
TARGET_EVIDENCE_WORK_ORDER_REL = "validation/heldout/grand_science/biology/target_evidence/OC133_BIOLOGY_TARGET_EVIDENCE_WORK_ORDER.json"

NO_SEND_LOCKS = {
    "no_send": True,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
    "registry_write_allowed": False,
    "journal_submission_allowed": False,
    "email_allowed": False,
    "doi_registration_allowed": False,
    "coverage_closure_allowed": False,
    "broad_modern_science_superiority_allowed": False,
}

REQUIRED_ROW_FIELDS = (
    "official_sources",
    "target_variable",
    "prediction_formula",
    "incumbent_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier_predicates",
    "replay_protocol",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def ncbi_eutils_url(endpoint: str, params: dict[str, str]) -> str:
    return f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{endpoint}?{urlencode(params)}"


def no_send() -> dict[str, Any]:
    return dict(NO_SEND_LOCKS)


def with_hash(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["row_sha256"] = sha256_object(row)
    return row


def common_acceptance_predicates(extra: list[str] | None = None) -> list[str]:
    return [
        "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND",
        "TARGET_VARIABLE_DECLARED",
        "TARGET_HIDDEN_OR_PROSPECTIVE_LOCK_DECLARED",
        "PREDICTION_FORMULA_DECLARED_BEFORE_SCORING",
        "COMPARATOR_PREREGISTERED_AND_NONTRIVIAL",
        "UNCERTAINTY_AND_RESIDUAL_DECLARED",
        "NEGATIVE_CONTROL_REJECTION_REQUIRED",
        "FALSIFIER_PREDICATES_EXECUTABLE",
        "INDEPENDENT_REPLAY_REQUIRED",
        "COVERAGE_GAP_REMAINS_OPEN_UNTIL_REVIEW",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        *(extra or []),
    ]


def build_work_orders() -> list[dict[str, Any]]:
    rows = [
        {
            "work_order_id": "OC133-BIOLOGY-COVERAGE-EVOLUTIONARY-PHYLOGENETIC-PATTERNS",
            "coverage_gap_id": "MS-COV-GAP-BIOLOGICAL_LIFE_SCIENCES-EVOLUTIONARY_PHYLOGENETIC_PATTERNS",
            "domain_class_id": "biological_life_sciences",
            "phenomenon_class_id": "evolutionary_phylogenetic_patterns",
            "phenomenon_label": "evolutionary phylogenetic patterns",
            "lane_status": "FAIL_CLOSED_PENDING_OFFICIAL_SOURCE_ACQUISITION_AND_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": (
                "The current NCBI/GEO expression lane is biological but does not test phylogenetic "
                "topology, sequence distance, or evolutionary history targets."
            ),
            "official_sources": [
                {
                    "source_id": "NCBI_EUTILS_TAXONOMY",
                    "title": "NCBI Taxonomy through E-utilities",
                    "official_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "ALLOWLISTED",
                },
                {
                    "source_id": "NCBI_EUTILS_NUCLEOTIDE",
                    "title": "NCBI Nucleotide/GenBank marker records through E-utilities",
                    "official_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "ALLOWLISTED",
                },
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-BIO-COV-PHYLO-NCBI-NUCLEOTIDE-ESEARCH-0001",
                    "http_method": "GET",
                    "official_endpoint_url": ncbi_eutils_url(
                        "esearch.fcgi",
                        {
                            "db": "nucleotide",
                            "term": "COI[Gene] AND txid7742[Organism:exp]",
                            "retmode": "json",
                            "retmax": "200",
                            "sort": "relevance",
                        },
                    ),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/biology/coverage_work_orders/raw/"
                        "phylogenetic_patterns/ncbi_nucleotide_coi_esearch.json"
                    ),
                    "hash_required": True,
                    "no_send_lock": True,
                },
                {
                    "request_id": "OC133-BIO-COV-PHYLO-NCBI-NUCLEOTIDE-EFETCH-0001",
                    "http_method": "GET",
                    "official_endpoint_url_template": (
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
                        "db=nucleotide&id={comma_joined_esearch_ids}&rettype=fasta&retmode=text"
                    ),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/biology/coverage_work_orders/raw/"
                        "phylogenetic_patterns/ncbi_nucleotide_coi_sequences.fasta"
                    ),
                    "depends_on": "OC133-BIO-COV-PHYLO-NCBI-NUCLEOTIDE-ESEARCH-0001",
                    "hash_required": True,
                    "no_send_lock": True,
                },
            ],
            "target_variable": {
                "name": "heldout_pairwise_marker_sequence_distance",
                "unit": "substitutions_per_site",
                "target_field": "distance_matrix[target_taxon_pair]",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": {
                "formula_id": "BIO-PHYLO-TRAINING-CLade-MEDIAN-DISTANCE",
                "rule": (
                    "y_hat(pair) = median(training_pairwise_distance for the lowest shared locked clade) "
                    "* marker_length_pair / median(training_marker_length)"
                ),
                "inputs_visible_before_target": [
                    "locked taxon identifiers",
                    "official marker sequence lengths",
                    "training-only pairwise distances",
                    "locked clade assignments",
                ],
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "neighbor-joining/Jukes-Cantor training-only comparator",
                "prediction_rule": (
                    "fit a standard training-only distance correction/tree baseline and predict the "
                    "heldout pairwise sequence distance for the same locked target pairs"
                ),
                "pre_registered": True,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute residual per heldout pair; aggregate mean absolute residual",
                "uncertainty_method": "training-clade bootstrap envelope declared before target unsealing",
                "superiority_predicate": "mean_model_residual + uncertainty_upper < mean_comparator_residual",
            },
            "negative_control": {
                "control_id": "BIO-PHYLO-TAXON-LABEL-PERMUTATION",
                "description": "permute target taxon labels after source lock; replay must lose source/target consistency",
                "rejection_predicate": "permuted-label comparator residual is larger than the locked model residual",
            },
            "falsifier_predicates": [
                "target pair sequence distances are read before prediction materialization",
                "source snapshot hash changes between acquisition and scoring",
                "any heldout comparator residual is less than or equal to model residual after uncertainty",
                "taxon-label permutation does not change row hashes",
            ],
            "replay_protocol": {
                "commands": [
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_phylogenetic_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/biology/coverage_work_orders/oc133_biology_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "NCBI Taxonomy/Nucleotide source snapshots",
                    "pre-target source lock declaration",
                    "target-hidden pairwise-distance task table",
                    "strict evidence candidate pack",
                ],
                "acceptance_predicates": common_acceptance_predicates(),
            },
            "remaining_blockers": [
                "OFFICIAL_PHYLOGENETIC_SOURCE_SNAPSHOTS_NOT_ACQUIRED",
                "STRICT_PHYLOGENETIC_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "OC133-BIOLOGY-COVERAGE-CELLULAR-DEVELOPMENTAL-REGULATORY-DYNAMICS",
            "coverage_gap_id": "MS-COV-GAP-BIOLOGICAL_LIFE_SCIENCES-CELLULAR_DEVELOPMENTAL_REGULATORY_DYNAMICS",
            "domain_class_id": "biological_life_sciences",
            "phenomenon_class_id": "cellular_developmental_regulatory_dynamics",
            "phenomenon_label": "cellular developmental regulatory dynamics",
            "lane_status": "READY_FOR_REPLAY_REVIEW_NOT_COVERAGE_CLOSED",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": (
                "The existing NCBI/GEO target-evidence lane is an honest official-data candidate for "
                "gene-expression observables, but coverage closure still requires review against the "
                "broader cellular/developmental/regulatory phenomenon scope."
            ),
            "existing_official_lane_refs": [
                TARGET_EVIDENCE_PACK_REL,
                TARGET_EVIDENCE_PROTOCOL_REL,
                TARGET_EVIDENCE_REPORT_REL,
                TARGET_EVIDENCE_WORK_ORDER_REL,
            ],
            "official_sources": [
                {
                    "source_id": "NCBI_GEO_PROFILES_EUTILS",
                    "title": "NCBI GEO Profiles through E-utilities ESearch/ESummary",
                    "official_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                    "local_source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-BIO-NCBI-GEO.txt",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "ALLOWLISTED",
                }
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-BIO-TARGET-GEOPROFILES-ESEARCH-0001",
                    "http_method": "GET",
                    "official_endpoint_url": ncbi_eutils_url(
                        "esearch.fcgi",
                        {
                            "db": "geoprofiles",
                            "term": "GDS3716[All Fields] AND Homo sapiens[ORGN] AND count[VTYP] NOT Control[All Fields]",
                            "retmode": "json",
                            "retmax": "30",
                            "retstart": "0",
                            "sort": "relevance",
                        },
                    ),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/biology/target_evidence/raw/"
                        "OC133_BIOLOGY_TARGET_GEO_PROFILE_SEARCH.json"
                    ),
                    "hash_required": True,
                    "no_send_lock": True,
                }
            ],
            "target_variable": {
                "name": "NCBI_GEO_Profile_ranked_mean_expression",
                "unit": "official GEO Profile rmean count/rank value",
                "target_field": "result.<uid>.rmean",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": {
                "formula_id": "BIO-GEO-RSTD-PREDICTS-RMEAN",
                "rule": "y_hat(uid) = official visible result.<uid>.rstd after source-lock materialization",
                "inputs_visible_before_target": [
                    "uid",
                    "gds",
                    "gpl",
                    "idref",
                    "genename",
                    "vmin",
                    "vmax",
                    "rstd",
                ],
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "within-profile maximum expression-count biological baseline",
                "prediction_rule": "predict the same GEO Profile heldout rmean target using official visible vmax",
                "pre_registered": True,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute residual per GEO Profile row; aggregate mean absolute residual",
                "uncertainty_method": "deterministic official GEO Profile ranked-score residuals with zero added measurement slack",
                "superiority_predicate": "mean_model_residual < mean_comparator_residual and every negative control is rejected",
            },
            "negative_control": {
                "control_id": "BIO-GEO-VMAX-NEGATIVE-CONTROL",
                "description": "within-profile vmax baseline must have a larger heldout residual than the locked rstd predictor",
                "rejection_predicate": "abs(vmax - rmean) > abs(rstd - rmean) for every accepted row",
            },
            "falsifier_predicates": [
                "any GEO Profile target row is pagination, retmax, retstart, idlist, or total-hit-count QA",
                "training_source and target_source overlap",
                "official bundle hash differs from the source hash registered in the report",
                "vmax comparator is not worse than the model residual on any heldout target",
            ],
            "replay_protocol": {
                "commands": [
                    "python tools/oc133_biology_target_official_bundle_builder.py --allow-blocked-exit-zero",
                    "python tools/oc133_biology_target_evidence_factory.py --check",
                    "python validation/heldout/grand_science/biology/coverage_work_orders/oc133_biology_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    TARGET_EVIDENCE_PACK_REL,
                    TARGET_EVIDENCE_PROTOCOL_REL,
                    TARGET_EVIDENCE_REPORT_REL,
                    TARGET_EVIDENCE_WORK_ORDER_REL,
                ],
                "acceptance_predicates": common_acceptance_predicates(
                    ["BIOLOGY_GEO_EXPRESSION_SCOPE_REVIEWED_FOR_CELLULAR_REGULATORY_COVERAGE"]
                ),
            },
            "remaining_blockers": [
                "COVERAGE_SCOPE_REVIEW_NOT_PERFORMED",
                "BROAD_BIOLOGY_COVERAGE_NOT_CLOSED_BY_SINGLE_GEO_LANE",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "OC133-BIOLOGY-COVERAGE-ECOLOGY-POPULATION-BIODIVERSITY-OBSERVABLES",
            "coverage_gap_id": "MS-COV-GAP-BIOLOGICAL_LIFE_SCIENCES-ECOLOGY_POPULATION_AND_BIODIVERSITY_OBSERVABLES",
            "domain_class_id": "biological_life_sciences",
            "phenomenon_class_id": "ecology_population_and_biodiversity_observables",
            "phenomenon_label": "ecology population and biodiversity observables",
            "lane_status": "FAIL_CLOSED_PENDING_GBIF_SOURCE_CAPSULE_AND_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": (
                "No existing official biology lane covers ecological abundance, occupancy, richness, or "
                "biodiversity occurrence targets."
            ),
            "official_sources": [
                {
                    "source_id": "GBIF_OCCURRENCE_API",
                    "title": "GBIF occurrence search API",
                    "official_url": "https://api.gbif.org/v1/occurrence/search",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "BLOCKED_PENDING_ALLOWLIST_ENTRY_AND_SOURCE_CAPSULE",
                }
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-BIO-COV-ECOLOGY-GBIF-OCCURRENCE-0001",
                    "http_method": "GET",
                    "official_endpoint_url": (
                        "https://api.gbif.org/v1/occurrence/search?"
                        + urlencode(
                            {
                                "country": "AR",
                                "hasCoordinate": "true",
                                "year": "1990,2024",
                                "limit": "300",
                            }
                        )
                    ),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/biology/coverage_work_orders/raw/"
                        "ecology_biodiversity/gbif_occurrence_argentina_1990_2024.json"
                    ),
                    "hash_required": True,
                    "no_send_lock": True,
                    "blocked_until": "official_readonly_runner_allowlist_adds_GBIF_API",
                }
            ],
            "target_variable": {
                "name": "heldout_grid_cell_species_occurrence_count",
                "unit": "GBIF occurrence records per locked grid cell and year",
                "target_field": "occurrence_count[grid_cell, target_year]",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": {
                "formula_id": "BIO-ECOLOGY-TRAILING-OCCUPANCY-SLOPE",
                "rule": "y_hat(cell, year) = y_t-1 + mean(delta_y over the prior five locked years)",
                "inputs_visible_before_target": [
                    "grid cell identifier",
                    "species key",
                    "prior-year occurrence counts",
                    "coordinate uncertainty filters",
                ],
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "GBIF carry-forward/trailing-mean biodiversity baseline",
                "prediction_rule": "predict heldout occurrence count from prior-year count and trailing five-year mean only",
                "pre_registered": True,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute count residual per grid-cell/year; aggregate mean absolute residual",
                "uncertainty_method": "prior-year rolling residual envelope with coordinate-uncertainty exclusion",
                "superiority_predicate": "model residual plus uncertainty is smaller than best preregistered comparator residual",
            },
            "negative_control": {
                "control_id": "BIO-ECOLOGY-GRID-YEAR-SHUFFLE",
                "description": "shuffle heldout grid-cell/year assignment after lock; accepted replay must reject the shuffled target mapping",
                "rejection_predicate": "shuffled mapping changes row hashes and worsens residuals relative to locked targets",
            },
            "falsifier_predicates": [
                "GBIF source snapshot cannot be hashed or replayed",
                "target-year occurrence counts leak into formula selection",
                "carry-forward or trailing-mean comparator ties or beats the model within uncertainty",
                "grid/year shuffle does not change row hashes",
            ],
            "replay_protocol": {
                "commands": [
                    "extend official_readonly_acquisition_runner allowlist for api.gbif.org/v1/occurrence/search",
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_gbif_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/biology/coverage_work_orders/oc133_biology_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "GBIF source capsule with official URL and snapshot hash",
                    "target-hidden grid/year target declaration",
                    "strict ecology biodiversity evidence candidate pack",
                ],
                "acceptance_predicates": common_acceptance_predicates(
                    ["GBIF_ALLOWLIST_AND_SOURCE_CAPSULE_REVIEWED"]
                ),
            },
            "remaining_blockers": [
                "GBIF_SOURCE_CAPSULE_NOT_PRESENT",
                "GBIF_RUNNER_ALLOWLIST_NOT_PRESENT",
                "STRICT_ECOLOGY_BIODIVERSITY_EVIDENCE_PACK_NOT_BUILT",
            ],
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def build_payload() -> dict[str, Any]:
    rows = build_work_orders()
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "modern_science_protocol_ref": MODERN_PROTOCOL_REL,
        "domain_class_id": "biological_life_sciences",
        "work_order_total": len(rows),
        "fail_closed_or_review_pending_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "no_send_locks": no_send(),
        "work_orders": rows,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("work_orders", [])
    if payload.get("coverage_closure_allowed") is not False:
        failures.append("PAYLOAD_COVERAGE_CLOSURE_ALLOWED")
    if payload.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("PAYLOAD_BROAD_SUPERIORITY_ALLOWED")
    if not isinstance(rows, list) or payload.get("work_order_total") != len(rows):
        failures.append("WORK_ORDER_TOTAL_MISMATCH")
        return failures
    expected_phenomena = {
        "evolutionary_phylogenetic_patterns",
        "cellular_developmental_regulatory_dynamics",
        "ecology_population_and_biodiversity_observables",
    }
    actual_phenomena = {str(row.get("phenomenon_class_id")) for row in rows if isinstance(row, dict)}
    if actual_phenomena != expected_phenomena:
        failures.append("BIOLOGY_PHENOMENON_SET_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if str(row.get("lane_status")).upper() == "PASS":
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        for field in REQUIRED_ROW_FIELDS:
            if not row.get(field):
                failures.append(f"REQUIRED_FIELD_MISSING::{row_id}::{field}")
        if not row.get("target_variable", {}).get("name"):
            failures.append(f"TARGET_VARIABLE_NAME_MISSING::{row_id}")
        if not row.get("prediction_formula", {}).get("rule"):
            failures.append(f"PREDICTION_FORMULA_RULE_MISSING::{row_id}")
        if not row.get("incumbent_comparator", {}).get("prediction_rule"):
            failures.append(f"COMPARATOR_RULE_MISSING::{row_id}")
        if not row.get("uncertainty_and_residual", {}).get("residual_metric"):
            failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
        if not row.get("negative_control", {}).get("rejection_predicate"):
            failures.append(f"NEGATIVE_CONTROL_PREDICATE_MISSING::{row_id}")
        if not row.get("falsifier_predicates"):
            failures.append(f"FALSIFIER_PREDICATES_MISSING::{row_id}")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    return failures


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    path = root / OUTPUT_REL
    expected = build_payload()
    failures = validate_payload(expected)
    if not path.exists():
        return [*failures, f"missing::{OUTPUT_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{OUTPUT_REL}")
    failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check biology modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write the deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL}, indent=2))
        return 0
    payload = build_payload()
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
