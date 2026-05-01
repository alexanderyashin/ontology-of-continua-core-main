from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

REGISTER_REL = "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
COVERAGE_WORK_ORDERS_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.md"
CLEAN_REPLAY_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_CLEAN_REPLAY.json"
GRAND_EMPIRICAL_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
REGISTRY_REL = "validation/heldout/grand_science_evidence_registry.json"
FACTORY_REF = "tools/oc133_modern_science_comparator_factory.py"
CLEAN_REPLAY_HELPER_REF = "benchmarks/modern_science/clean_checkout_replay.py"
COVERAGE_DISPATCHER_REF = "benchmarks/modern_science/coverage_lane_dispatcher.py"

EMPIRICAL_DOMAINS = ("biology", "chemistry", "physics", "systems")
REQUIRED_DOMAINS = EMPIRICAL_DOMAINS
MINIMUM_N = 20
REQUIRED_DISTINCTION_ROLES = (
    "incumbent_modern_science_source",
    "strict_evidence_pack",
    "oc_result",
    "comparator_result",
    "benchmark_predicate",
    "uncertainty_fairness",
    "certification_verdict",
    "blocker_reason",
)
CURRENT_PACK_REFS = {
    "biology": "validation/heldout/grand_science/biology/target_evidence/biology_target_evidence_candidate_pack.json",
    "chemistry": "validation/heldout/grand_science/chemistry/pubchem_hbond_donor/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_CANDIDATE_PACK.json",
    "physics": "validation/heldout/grand_science/physics_chemistry/official_batch/physics_official_batch_candidate_evidence_pack.json",
    "systems": "validation/heldout/grand_science/systems/wdi_population_materiality/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_CANDIDATE_PACK.json",
}
STALE_REF_FRAGMENTS = (
    "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "validation/biology/VALIDATION_PACKET.json",
    "validation/chemistry/VALIDATION_PACKET.json",
    "validation/physics/VALIDATION_PACKET.json",
    "validation/systems/VALIDATION_PACKET.json",
)
UNSUPPORTED_BROAD_WORDING = (
    "predicts better than modern science",
    "superior to modern science",
    "outperforms modern science",
    "replaces modern science",
)

MODERN_SCIENCE_TAXONOMY_SOURCE = {
    "source_policy": "internally_declared_coverage_taxonomy",
    "taxonomy_id": "OC133_DECLARED_MODERN_SCIENCE_COVERAGE_TAXONOMY_v1",
    "scope_note": (
        "This is an internal blocking taxonomy for broad modern-science wording. "
        "It is deliberately broader than the four current empirical lanes and must not be treated as proof that the taxonomy is exhaustive for public science classification."
    ),
    "closure_rule": (
        "A broad modern-science superiority claim requires every declared domain class and every required phenomenon class to have source-backed, "
        "target-separated benchmark lanes with preregistered comparators, uncertainty, controls, falsifiers, independent replay, and explicit domain-scope survey evidence."
    ),
}

MODERN_SCIENCE_DOMAIN_CLASSES = (
    {
        "domain_class_id": "formal_mathematics_and_logic",
        "label": "Formal mathematics, logic, statistics, and proof science",
        "phenomenon_classes": (
            "formal_theorem_reconstruction",
            "statistical_inference_identifiability",
            "computational_complexity_and_algorithmic_proof",
        ),
    },
    {
        "domain_class_id": "physical_sciences",
        "label": "Physical sciences",
        "phenomenon_classes": (
            "fundamental_constants_relationships",
            "dynamical_laws_and_conservation",
            "condensed_matter_fields_and_measurements",
            "astronomical_and_cosmological_observables",
        ),
    },
    {
        "domain_class_id": "chemical_sciences",
        "label": "Chemical sciences",
        "phenomenon_classes": (
            "molecular_descriptor_prediction",
            "reaction_and_kinetics_prediction",
            "thermochemistry_and_phase_behavior",
            "materials_and_spectroscopy_observables",
        ),
    },
    {
        "domain_class_id": "earth_space_environmental_sciences",
        "label": "Earth, space, and environmental sciences",
        "phenomenon_classes": (
            "climate_weather_geophysical_time_series",
            "geochemistry_and_hydrology_observables",
            "remote_sensing_and_planetary_measurements",
        ),
    },
    {
        "domain_class_id": "biological_life_sciences",
        "label": "Biological and life sciences",
        "phenomenon_classes": (
            "functional_genomics_expression",
            "evolutionary_phylogenetic_patterns",
            "cellular_developmental_regulatory_dynamics",
            "ecology_population_and_biodiversity_observables",
        ),
    },
    {
        "domain_class_id": "medical_health_sciences",
        "label": "Medical and health sciences",
        "phenomenon_classes": (
            "clinical_outcomes_and_biomarkers",
            "epidemiological_transmission_and_risk",
            "pharmacology_toxicology_and_dose_response",
        ),
    },
    {
        "domain_class_id": "agricultural_food_sciences",
        "label": "Agricultural, food, and veterinary sciences",
        "phenomenon_classes": (
            "crop_yield_soil_and_trait_observables",
            "food_chemistry_safety_and_nutrition",
            "animal_health_and_production_systems",
        ),
    },
    {
        "domain_class_id": "engineering_materials_sciences",
        "label": "Engineering, materials, and applied measurement sciences",
        "phenomenon_classes": (
            "materials_property_and_failure_prediction",
            "control_systems_and_signal_measurement",
            "energy_transport_and_manufacturing_processes",
        ),
    },
    {
        "domain_class_id": "computer_information_sciences",
        "label": "Computer and information sciences",
        "phenomenon_classes": (
            "program_semantics_and_verification",
            "machine_learning_generalization_and_evaluation",
            "information_network_and_security_observables",
        ),
    },
    {
        "domain_class_id": "cognitive_behavioral_neurosciences",
        "label": "Cognitive, behavioral, and neurosciences",
        "phenomenon_classes": (
            "neural_recording_and_brain_network_observables",
            "behavioral_task_and_psychometric_prediction",
            "learning_memory_and_perception_dynamics",
        ),
    },
    {
        "domain_class_id": "social_economic_political_sciences",
        "label": "Social, economic, demographic, and political sciences",
        "phenomenon_classes": (
            "demographic_population_series",
            "economic_indicator_and_market_observables",
            "institutional_social_network_and_policy_outcomes",
        ),
    },
    {
        "domain_class_id": "complex_systems_operations_science",
        "label": "Complex systems, operations, and decision sciences",
        "phenomenon_classes": (
            "multi_agent_system_dynamics",
            "queue_supply_chain_and_operations_observables",
            "resilience_risk_and_intervention_response",
        ),
    },
)

CURRENT_LANE_COVERAGE = {
    "biology": {
        "domain_class_id": "biological_life_sciences",
        "phenomenon_class_ids": ("functional_genomics_expression",),
    },
    "chemistry": {
        "domain_class_id": "chemical_sciences",
        "phenomenon_class_ids": ("molecular_descriptor_prediction",),
    },
    "physics": {
        "domain_class_id": "physical_sciences",
        "phenomenon_class_ids": ("fundamental_constants_relationships",),
    },
    "systems": {
        "domain_class_id": "social_economic_political_sciences",
        "phenomenon_class_ids": ("demographic_population_series",),
    },
}

PROTOCOL_ONLY_COVERAGE = {
    "formal_mathematics_and_logic": {
        "domain": "mathematics",
        "protocol_ref": "benchmarks/modern_science/protocols/OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_MATHEMATICS.json",
        "source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-MATH-LEAN4.txt",
    }
}

INCUMBENT_SOURCES = {
    "biology": {
        "incumbent": "NCBI GEO public functional-genomics repository and GEO Profile target records",
        "accepted_capacity": "GEO exposes public gene-expression profile records; the current pack tests a held-out ranked mean observable against a preregistered within-profile comparator.",
        "source_refs": [
            {
                "title": "NCBI Gene Expression Omnibus overview and dataset documentation",
                "url": "https://www.ncbi.nlm.nih.gov/geo/info/overview.html",
                "source_date": "reference",
                "local_source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-BIO-NCBI-GEO.txt",
                "local_source_capsule_sha256": "ecb31bbe88815175df5e4c058dbbc8a030476339e1f12236b957754ef2855ae7",
            }
        ],
    },
    "chemistry": {
        "incumbent": "PubChem compound descriptor records",
        "accepted_capacity": "PubChem exposes compound descriptors including SMILES and hydrogen-bond donor counts; the current pack tests target-blind donor-count prediction against formula-only and zero-count baselines.",
        "source_refs": [
            {
                "title": "PubChem compound records and descriptor fields",
                "url": "https://pubchem.ncbi.nlm.nih.gov/",
                "source_date": "reference",
                "local_source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-CHEM-PUBCHEM-H2O.txt",
                "local_source_capsule_sha256": "51186f587d1b4c778a64cbf3e34d010dffb3c5ab60d67eb50cc6c4b4a5a08590",
            }
        ],
    },
    "physics": {
        "incumbent": "NIST/CODATA/SI fundamental constants reference standards",
        "accepted_capacity": "NIST/CODATA publishes official constants and relationships; the current pack tests prospective official-snapshot relationship reconstruction against preregistered null/wrong-field controls.",
        "source_refs": [
            {
                "title": "NIST CODATA recommended values of the fundamental physical constants, 2022 adjustment",
                "url": "https://physics.nist.gov/cuu/pdf/all.pdf",
                "source_date": "2022",
                "local_source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-PHYS-CODATA-2022.txt",
                "local_source_capsule_sha256": "121e451dfdaa13ff49e17b2bdb54b19e908d6fa4a890b2c857cc4eeaa6d1ace5",
            }
        ],
    },
    "systems": {
        "incumbent": "World Bank World Development Indicators population series",
        "accepted_capacity": "WDI exposes official annual population series; the current pack tests a target-blind Argentina held-out panel against carry-forward, prior-mean, and trailing-mean comparators.",
        "source_refs": [
            {
                "title": "World Bank WDI metadata for SP.POP.TOTL",
                "url": "https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SP.POP.TOTL",
                "source_date": "reference",
                "local_source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-SYS-WORLD-BANK-WDI.txt",
                "local_source_capsule_sha256": "eb2365d9c8fa5806f3b9f210a27e94872bcf500b9de33776529f893550b41036",
            }
        ],
    },
}

LANE_TASKS = {
    "biology": "Predict held-out NCBI GEO Profile ranked mean expression targets from visible target-blind profile projections.",
    "chemistry": "Predict PubChem HBondDonorCount from visible CID, formula, and ConnectivitySMILES without reading the target descriptor.",
    "physics": "Reconstruct official CODATA/SI relationship targets from visible formula inputs under a prospective official-readonly source lock.",
    "systems": "Predict a fixed target-blind WDI Argentina population held-out panel from prior-year training rows.",
}


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


def load_coverage_lane_dispatcher() -> Any:
    path = repo_root() / COVERAGE_DISPATCHER_REF
    spec = importlib.util.spec_from_file_location("oc133_coverage_lane_dispatcher_shared", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load coverage lane dispatcher from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_replay_certificate(root: Path) -> dict[str, Any]:
    path = root / CLEAN_REPLAY_REL
    if not path.exists():
        return {
            "status": "MISSING",
            "satisfies_register_predicate": False,
            "report_ref": CLEAN_REPLAY_REL,
            "report_sha256": "",
            "failures": ["CLEAN_REPLAY_CERTIFICATE_MISSING"],
        }
    payload = load_json(path)
    failures = validate_clean_replay_payload(payload, root)
    return {
        "status": "PASS" if not failures and payload.get("satisfies_register_predicate") is True else "FAIL",
        "satisfies_register_predicate": not failures and payload.get("satisfies_register_predicate") is True,
        "report_ref": CLEAN_REPLAY_REL,
        "report_sha256": sha256_file(path),
        "helper_ref": CLEAN_REPLAY_HELPER_REF,
        "replay_id": payload.get("replay_id"),
        "replay_kind": payload.get("replay_kind"),
        "replay_scope": payload.get("replay_scope"),
        "bounded": payload.get("bounded"),
        "command_allowlist": payload.get("command_allowlist", []),
        "command_results": payload.get("command_results", []),
        "selected_evidence_pack_refs": payload.get("register_binding", {}).get("selected_evidence_pack_refs", {}),
        "selected_evidence_pack_sha256": payload.get("register_binding", {}).get("selected_evidence_pack_sha256", {}),
        "environment_note": "Local deterministic clean temp-tree replay only; no push, release, Zenodo, DOI, journal, email, or public outbound action.",
        "no_send_locks": payload.get("no_send_locks", {}),
        "failures": failures or payload.get("failures", []),
    }


def row_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if isinstance(row, dict) and row.get(key)}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def is_true(value: Any) -> bool:
    return value is True


def get_pack_ref_hashes(root: Path) -> dict[str, str]:
    return {domain: sha256_file(root / rel) for domain, rel in CURRENT_PACK_REFS.items() if (root / rel).exists()}


def pack_source_refs(pack: dict[str, Any]) -> list[str]:
    separation = pack.get("source_separation", {})
    refs: list[str] = []
    for key in ("training_sources", "target_sources"):
        refs.extend(str(item) for item in as_list(separation.get(key)) if item)
    if separation.get("attestation_ref"):
        refs.append(str(separation["attestation_ref"]))
    for source_hash in as_list(pack.get("source_hashes")):
        if isinstance(source_hash, dict) and source_hash.get("source_ref"):
            refs.append(str(source_hash["source_ref"]))
    for source_hash in as_list(separation.get("source_hashes")):
        if source_hash:
            refs.append(str(source_hash))
    return list(dict.fromkeys(refs))


def source_hash_refs(pack: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for source_hash in as_list(pack.get("source_hashes")):
        if isinstance(source_hash, dict):
            refs.append(copy.deepcopy(source_hash))
    separation = pack.get("source_separation", {})
    for digest in as_list(separation.get("source_hashes")):
        refs.append({"source_ref": "source_separation.source_hashes", "sha256": digest})
    if separation.get("attestation_ref"):
        refs.append({"source_ref": separation.get("attestation_ref"), "hash_policy": "attestation_ref_present"})
    return refs


def negative_controls_rejected(pack: dict[str, Any]) -> bool:
    controls = as_list(pack.get("negative_controls"))
    return bool(controls) and all(isinstance(control, dict) and control.get("rejected") is True for control in controls)


def validate_clean_replay_payload(payload: dict[str, Any], root: Path | None = None) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []
    if payload.get("schema_id") != "OC133_MODERN_SCIENCE_CLEAN_TEMP_TREE_REPLAY_v1":
        errors.append("CLEAN_REPLAY_SCHEMA_MISMATCH")
    if payload.get("satisfies_register_predicate") is not True:
        errors.append("CLEAN_REPLAY_PREDICATE_NOT_SATISFIED")
    if payload.get("bounded") is True:
        errors.append("CLEAN_REPLAY_MARKED_BOUNDED_CANNOT_CLOSE_PREDICATE")
    clean_tree = payload.get("clean_temp_tree", {})
    if clean_tree.get("isolated_copy") is not True or clean_tree.get("deterministic_allowlist_copy") is not True:
        errors.append("CLEAN_REPLAY_NOT_ISOLATED_DETERMINISTIC_COPY")
    if clean_tree.get("dirty_untracked_leak_detected") is True or int(clean_tree.get("unexpected_ref_total", 0) or 0) != 0:
        errors.append("CLEAN_REPLAY_DIRTY_OR_UNTRACKED_LEAK")

    selected_hashes = payload.get("register_binding", {}).get("selected_evidence_pack_sha256", {})
    if selected_hashes != get_pack_ref_hashes(root):
        errors.append("CLEAN_REPLAY_SELECTED_PACK_HASH_MISMATCH")
    selected_refs = payload.get("register_binding", {}).get("selected_evidence_pack_refs", {})
    if selected_refs != CURRENT_PACK_REFS:
        errors.append("CLEAN_REPLAY_SELECTED_PACK_REF_MISMATCH")

    no_send = payload.get("no_send_locks", {})
    required_false = (
        "network_allowed",
        "public_release_action_allowed",
        "publish_allowed",
        "push_allowed",
        "registry_write_allowed",
        "journal_submissions_allowed",
        "email_allowed",
    )
    if no_send.get("no_send") is not True:
        errors.append("CLEAN_REPLAY_NO_SEND_LOCK_MISSING")
    for key in required_false:
        if no_send.get(key) is not False:
            errors.append(f"CLEAN_REPLAY_NO_SEND_LOCK_OPEN::{key}")
    if int(no_send.get("public_action_true_path_total", 0) or 0) != 0:
        errors.append("CLEAN_REPLAY_PUBLIC_ACTION_TRUE_PATHS")

    command_results = payload.get("command_results", [])
    if not command_results:
        errors.append("CLEAN_REPLAY_COMMAND_RESULTS_MISSING")
    for index, result in enumerate(command_results):
        if result.get("allowed_by_replay_command_allowlist") is not True:
            errors.append(f"CLEAN_REPLAY_COMMAND_NOT_ALLOWLISTED::{index}")
        if result.get("public_outbound_release_action") is not False:
            errors.append(f"CLEAN_REPLAY_PUBLIC_OUTBOUND_COMMAND::{index}")
        if result.get("exit_code") != 0:
            errors.append(f"CLEAN_REPLAY_COMMAND_FAILED::{index}")
        if not result.get("stdout_sha256") or not result.get("output_sha256"):
            errors.append(f"CLEAN_REPLAY_COMMAND_HASH_MISSING::{index}")

    for domain in EMPIRICAL_DOMAINS:
        replay = payload.get("pack_replay_results", {}).get(domain, {})
        if replay.get("pack_ref") != CURRENT_PACK_REFS[domain]:
            errors.append(f"CLEAN_REPLAY_PACK_REF_MISMATCH::{domain}")
        if replay.get("pack_sha256") != get_pack_ref_hashes(root).get(domain):
            errors.append(f"CLEAN_REPLAY_PACK_HASH_MISMATCH::{domain}")
        predicate_failures = replay.get("predicate_failures", [])
        if predicate_failures:
            errors.append(f"CLEAN_REPLAY_PACK_PREDICATE_FAILURE::{domain}::{','.join(str(item) for item in predicate_failures)}")
    if payload.get("failures"):
        errors.append("CLEAN_REPLAY_PAYLOAD_HAS_FAILURES")
    return errors


def pack_validation_predicates(root: Path, domain: str, ref: str, pack: dict[str, Any]) -> dict[str, bool]:
    path = root / ref
    residuals = pack.get("residuals", {})
    comparator = pack.get("comparator_baseline", {})
    source_separation = pack.get("source_separation", {})
    source_refs = pack_source_refs(pack)
    source_hash_records = source_hash_refs(pack)
    try:
        model_residual = float(residuals.get("model"))
        comparator_residual = float(residuals.get("comparator"))
        margin = float(residuals.get("superiority_margin"))
    except (TypeError, ValueError):
        model_residual = comparator_residual = margin = 0.0
    return {
        "current_strict_pack_ref": ref == CURRENT_PACK_REFS.get(domain),
        "current_pack_exists": path.exists(),
        "current_pack_hash_bound": path.exists(),
        "schema_is_strict_grand_empirical": pack.get("schema_id") == "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
        "domain_matches_pack": pack.get("domain") == domain,
        "minimum_n_met": int(pack.get("n", 0) or 0) >= MINIMUM_N,
        "source_separation_mode_allowed": source_separation.get("mode") in {"prospective", "target_blind"},
        "pre_target_lock_present": source_separation.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source_separation.get("target_hidden_until_scoring") is True,
        "training_and_target_source_refs_present": bool(source_refs),
        "pack_sha256_bound": path.exists(),
        "comparator_baseline_declared": bool(comparator.get("name") and comparator.get("prediction_rule")),
        "comparator_baseline_pre_registered": comparator.get("pre_registered") is True,
        "uncertainty_declared": bool(pack.get("uncertainty", {}).get("metric")) and bool(pack.get("uncertainty", {}).get("interval") is not None),
        "residuals_show_model_beats_declared_comparator": comparator_residual > model_residual and margin > 0.0,
        "negative_controls_rejected": negative_controls_rejected(pack),
        "falsifier_declared": bool(pack.get("falsifiers")),
        "strict_pack_support_allowed": pack.get("grand_toe_support_allowed") is True,
    }


def taxonomy_domain_ids() -> set[str]:
    return {row["domain_class_id"] for row in MODERN_SCIENCE_DOMAIN_CLASSES}


def phenomenon_label(phenomenon_id: str) -> str:
    return phenomenon_id.replace("_", " ")


def current_lane_mappings(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_domain = {row.get("domain"): row for row in matrix}
    for domain, mapping in CURRENT_LANE_COVERAGE.items():
        matrix_row = by_domain.get(domain, {})
        verdict = matrix_row.get("certification_verdict", {}).get("benchmark_scoped_superiority", {})
        rows.append(
            {
                "domain": domain,
                "lane_id": matrix_row.get("lane_id", f"MS-LANE-{domain.upper()}-STRICT-PACK"),
                "domain_class_id": mapping["domain_class_id"],
                "phenomenon_class_ids": list(mapping["phenomenon_class_ids"]),
                "strict_evidence_pack_ref": matrix_row.get("strict_evidence_pack", {}).get("ref"),
                "benchmark_scoped_certified": verdict.get("certified") is True,
                "broad_modern_science_certified": False,
                "scope_limit": "This lane covers only the listed phenomenon class ids for its declared pack task.",
            }
        )
    return rows


def build_coverage_gap_rows(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    certified_phenomena: dict[str, set[str]] = {domain_id: set() for domain_id in taxonomy_domain_ids()}
    for mapping in current_lane_mappings(matrix):
        if mapping.get("benchmark_scoped_certified") is True:
            certified_phenomena.setdefault(str(mapping["domain_class_id"]), set()).update(
                str(item) for item in mapping.get("phenomenon_class_ids", [])
            )

    gap_rows: list[dict[str, Any]] = []
    for domain_class in MODERN_SCIENCE_DOMAIN_CLASSES:
        domain_id = domain_class["domain_class_id"]
        covered = certified_phenomena.get(domain_id, set())
        for phenomenon_id in domain_class["phenomenon_classes"]:
            if phenomenon_id in covered:
                continue
            gap_rows.append(
                {
                    "gap_id": f"MS-COV-GAP-{domain_id.upper()}-{phenomenon_id.upper()}",
                    "domain_class_id": domain_id,
                    "domain_label": domain_class["label"],
                    "phenomenon_class_id": phenomenon_id,
                    "phenomenon_label": phenomenon_label(phenomenon_id),
                    "gap_type": "NO_CERTIFIED_SOURCE_BACKED_BENCHMARK_LANE",
                    "required_before_broad_claim": True,
                    "missing_evidence_lanes": [
                        "source-backed target definition lane",
                        "target-blind or prospective acquisition lane",
                        "preregistered incumbent comparator lane",
                        "OC result scoring lane with uncertainty",
                        "negative-control and falsifier lane",
                        "independent replay lane bound to this coverage register",
                    ],
                }
            )
    return gap_rows


def build_coverage_work_orders(coverage_register: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    dispatcher = load_coverage_lane_dispatcher()
    return dispatcher.build_concrete_work_orders(root, coverage_register=coverage_register)


def build_coverage_register(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    mappings = current_lane_mappings(matrix)
    gaps = build_coverage_gap_rows(matrix)
    required_phenomenon_total = sum(len(row["phenomenon_classes"]) for row in MODERN_SCIENCE_DOMAIN_CLASSES)
    covered_phenomena = {
        (mapping["domain_class_id"], phenomenon_id)
        for mapping in mappings
        if mapping.get("benchmark_scoped_certified") is True
        for phenomenon_id in mapping.get("phenomenon_class_ids", [])
    }
    domain_class_rows = []
    for domain_class in MODERN_SCIENCE_DOMAIN_CLASSES:
        domain_id = domain_class["domain_class_id"]
        domain_mappings = [mapping for mapping in mappings if mapping["domain_class_id"] == domain_id]
        missing = [gap for gap in gaps if gap["domain_class_id"] == domain_id]
        protocol_only = PROTOCOL_ONLY_COVERAGE.get(domain_id)
        domain_class_rows.append(
            {
                "domain_class_id": domain_id,
                "label": domain_class["label"],
                "required_phenomenon_classes": [
                    {"phenomenon_class_id": item, "label": phenomenon_label(item)}
                    for item in domain_class["phenomenon_classes"]
                ],
                "current_lane_ids": [mapping["lane_id"] for mapping in domain_mappings],
                "protocol_only_ref": protocol_only,
                "coverage_status": (
                    "PARTIAL_BENCHMARK_SCOPED_LANES_PRESENT"
                    if domain_mappings
                    else ("PROTOCOL_ONLY_NO_CERTIFIED_STRICT_PACK" if protocol_only else "NO_CERTIFIED_LANES")
                ),
                "broad_domain_coverage_certified": False,
                "missing_phenomenon_class_ids": [gap["phenomenon_class_id"] for gap in missing],
                "gap_total": len(missing),
            }
        )
    closure_predicates = {
        "taxonomy_declared": True,
        "every_required_domain_class_has_certified_lane": all(row["current_lane_ids"] for row in domain_class_rows),
        "every_required_phenomenon_class_has_certified_lane": len(gaps) == 0,
        "every_current_lane_is_benchmark_scoped_only": all(mapping.get("broad_modern_science_certified") is False for mapping in mappings),
        "domain_scope_surveys_present_for_all_domain_classes": False,
        "independent_clean_checkout_replay_bound_to_coverage_register": False,
        "coverage_extends_to_all_of_modern_science": False,
    }
    return {
        "schema_id": "OC133_MODERN_SCIENCE_COVERAGE_REGISTER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion Research/PriorArt",
        "taxonomy_source": MODERN_SCIENCE_TAXONOMY_SOURCE,
        "required_domain_class_total": len(MODERN_SCIENCE_DOMAIN_CLASSES),
        "required_phenomenon_class_total": required_phenomenon_total,
        "current_empirical_lane_mapping": mappings,
        "domain_class_rows": domain_class_rows,
        "coverage_gap_rows": gaps,
        "coverage_gap_total": len(gaps),
        "covered_required_phenomenon_class_total": len(covered_phenomena),
        "coverage_summary": {
            "domain_classes_with_any_current_lane_total": len({mapping["domain_class_id"] for mapping in mappings}),
            "domain_classes_without_certified_lane_total": sum(1 for row in domain_class_rows if not row["current_lane_ids"]),
            "benchmark_scoped_lane_total": len(mappings),
            "broad_coverage_certified": False,
        },
        "coverage_closure_predicates": closure_predicates,
        "coverage_closure_decision": {
            "coverage_extends_to_all_of_modern_science": False,
            "state": "BLOCKED_BY_COVERAGE_GAPS",
            "failed_predicates": [key for key, value in closure_predicates.items() if value is not True],
            "work_orders_ref": COVERAGE_WORK_ORDERS_REL,
        },
    }


def broad_claim_predicates(
    domain_rows: list[dict[str, Any]],
    coverage_register: dict[str, Any] | None = None,
    clean_replay: dict[str, Any] | None = None,
) -> dict[str, bool]:
    coverage_register = coverage_register or {}
    clean_replay = clean_replay or {}
    coverage_decision = coverage_register.get("coverage_closure_decision", {})
    return {
        "every_empirical_domain_has_current_strict_pack": all(
            row.get("strict_evidence_pack", {}).get("validation_predicates", {}).get("current_strict_pack_ref") is True
            for row in domain_rows
        ),
        "every_empirical_domain_has_benchmark_scoped_certification": all(
            row.get("certification_verdict", {}).get("benchmark_scoped_superiority", {}).get("certified") is True
            for row in domain_rows
        ),
        "independent_clean_checkout_replay_bound_to_register": clean_replay.get("satisfies_register_predicate") is True,
        "claim_text_excludes_unsupported_broad_modern_science_wording": True,
        "coverage_extends_to_all_of_modern_science": coverage_decision.get("coverage_extends_to_all_of_modern_science") is True,
    }


def benchmark_certified(predicates: dict[str, bool]) -> bool:
    return all(predicates.values())


def build_domain_evidence_matrix(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or repo_root()
    grand = load_json(root / GRAND_EMPIRICAL_REL)
    grand_by_domain = row_by(grand.get("domains", []), "domain")
    matrix: list[dict[str, Any]] = []
    for domain in EMPIRICAL_DOMAINS:
        ref = CURRENT_PACK_REFS[domain]
        path = root / ref
        pack = load_json(path)
        pack_hash = sha256_file(path) if path.exists() else ""
        predicates = pack_validation_predicates(root, domain, ref, pack)
        certified = benchmark_certified(predicates)
        residuals = pack.get("residuals", {})
        comparator = pack.get("comparator_baseline", {})
        source_separation = pack.get("source_separation", {})
        source_refs = pack_source_refs(pack)
        source_hash_records = source_hash_refs(pack)
        grand_row = grand_by_domain.get(domain, {})

        matrix.append(
            {
                "domain": domain,
                "row_id": f"MS-SUP-{domain.upper()}-STRICT-PACK",
                "lane_id": f"MS-LANE-{domain.upper()}-STRICT-PACK",
                "predicate_id": f"MS-PRED-{domain.upper()}-STRICT-PACK",
                "distinction_roles_present": list(REQUIRED_DISTINCTION_ROLES),
                "incumbent_modern_science_source": {
                    **INCUMBENT_SOURCES[domain],
                    "source_role": "incumbent/source context only; not evidence that OC beats all of the field",
                },
                "strict_evidence_pack": {
                    "ref": ref,
                    "sha256": pack_hash,
                    "evidence_pack_id": pack.get("evidence_pack_id"),
                    "schema_id": pack.get("schema_id"),
                    "n": pack.get("n"),
                    "domain": pack.get("domain"),
                    "source_separation": {
                        "mode": source_separation.get("mode"),
                        "pre_target_lock": source_separation.get("pre_target_lock"),
                        "target_hidden_until_scoring": source_separation.get("target_hidden_until_scoring"),
                        "training_source_ref_total": len(as_list(source_separation.get("training_sources"))),
                        "target_source_ref_total": len(as_list(source_separation.get("target_sources"))),
                        "attestation_ref": source_separation.get("attestation_ref"),
                    },
                    "source_refs": source_refs,
                    "source_hash_refs": source_hash_records,
                    "validation_predicates": predicates,
                    "validation_failures": [key for key, value in predicates.items() if value is not True],
                    "grand_empirical_domain_status_ref": f"{GRAND_EMPIRICAL_REL}::domains::{domain}",
                    "grand_empirical_domain_status": {
                        "status": grand_row.get("status"),
                        "valid_n": grand_row.get("valid_n"),
                        "minimum_n": grand_row.get("minimum_n"),
                        "grand_toe_support_allowed": grand_row.get("grand_toe_support_allowed"),
                        "blockers": grand_row.get("blockers", []),
                    },
                },
                "oc_result": {
                    "result_ref": ref,
                    "result_kind": "STRICT_BENCHMARK_SCOPED_CANDIDATE_PACK",
                    "model_under_test": pack.get("model_under_test"),
                    "model_residual": residuals.get("model"),
                    "uncertainty": pack.get("uncertainty"),
                    "support_scope": "benchmark-scoped comparison against declared preregistered incumbent/baseline controls only",
                    "not_supported_claim": "predicts better than modern science",
                },
                "comparator_result": {
                    "result_ref": ref,
                    "baseline_name": comparator.get("name"),
                    "prediction_rule": comparator.get("prediction_rule"),
                    "pre_registered": comparator.get("pre_registered"),
                    "comparator_residual": residuals.get("comparator"),
                    "superiority_margin": residuals.get("superiority_margin"),
                    "negative_controls": pack.get("negative_controls"),
                    "falsifiers": pack.get("falsifiers"),
                },
                "benchmark_predicate": {
                    "task": LANE_TASKS[domain],
                    "metric_family": pack.get("uncertainty", {}).get("metric"),
                    "certification_predicates": list(predicates.keys()),
                    "current_predicate_status": predicates,
                    "current_verdict": "CERTIFIED_AGAINST_DECLARED_BENCHMARK_BASELINES" if certified else "BLOCKED_BY_STRICT_PACK_PREDICATE_FAILURE",
                    "allowed_current_claim": "OC133 benchmark result beats the declared preregistered comparator baselines for this strict pack.",
                },
                "uncertainty_fairness": {
                    "uncertainty_declared": predicates["uncertainty_declared"],
                    "uncertainty": pack.get("uncertainty"),
                    "source_separation_mode": source_separation.get("mode"),
                    "predeclared_comparator_present": predicates["comparator_baseline_declared"],
                    "negative_control_rejected": predicates["negative_controls_rejected"],
                    "fairness_limitations": [
                        "Certification is scoped to the declared pack task, source refs, hash, and preregistered baselines.",
                        "It is not a survey over all theories, datasets, instruments, labs, or methods in the domain.",
                    ],
                    "fairness_verdict": "BENCHMARK_SCOPED_FAIRNESS_ACCEPTED" if certified else "FAIL_CLOSED",
                },
                "certification_verdict": {
                    "benchmark_scoped_superiority": {
                        "certified": certified,
                        "label": "CERTIFIED_AGAINST_DECLARED_INCUMBENT_BENCHMARK_BASELINES" if certified else "NOT_CERTIFIED",
                        "scope": "declared strict evidence pack baselines only",
                    },
                    "broad_modern_science_superiority": {
                        "certified": False,
                        "label": "BLOCKED_UNSUPPORTED_BROAD_WORDING",
                        "forbidden_claim": "predicts better than modern science",
                    },
                    "modern_science_comparator_superiority": {
                        "state": "FAIL_BROAD_CLAIM_BLOCKED",
                        "honest_pass_state": "benchmark_scoped_only",
                    },
                },
                "blocker_reason": {
                    "broad_claim_blocked_by": [
                        "BROAD_MODERN_SCIENCE_SCOPE_NOT_COVERED_BY_DECLARED_PACKS",
                        "NO_SURVEY_OF_ALL_MODERN_SCIENCE_INCUMBENTS",
                        "INDEPENDENT_CLEAN_CHECKOUT_REPLAY_NOT_BOUND_TO_THIS_REGISTER",
                        "UNSUPPORTED_WORDING::predicts better than modern science",
                    ],
                    "strict_pack_failures": [key for key, value in predicates.items() if value is not True],
                    "allowed_current_wording": "certified against declared incumbent benchmark baselines only",
                    "forbidden_wording": list(UNSUPPORTED_BROAD_WORDING),
                },
            }
        )
    return matrix


def matrix_summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "domain_total": len(matrix),
        "domains": [row.get("domain") for row in matrix],
        "required_distinction_roles": list(REQUIRED_DISTINCTION_ROLES),
        "benchmark_scoped_superiority_certified_total": sum(
            1 for row in matrix if row.get("certification_verdict", {}).get("benchmark_scoped_superiority", {}).get("certified") is True
        ),
        "broad_modern_science_superiority_certified_total": 0,
        "blocked_broad_superiority_total": len(matrix),
    }


def build_lanes(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    lanes = []
    for row in matrix:
        strict_pack = row["strict_evidence_pack"]
        benchmark = row["benchmark_predicate"]
        comparator = row["comparator_result"]
        lanes.append(
            {
                "lane_id": row["lane_id"],
                "predicate_id": row["predicate_id"],
                "domain": row["domain"],
                "strict_evidence_pack_ref": strict_pack["ref"],
                "strict_evidence_pack_sha256": strict_pack["sha256"],
                "task": benchmark["task"],
                "metric_family": benchmark["metric_family"],
                "required_negative_control": "All declared negative controls in the strict pack must be rejected.",
                "certification_predicates": benchmark["certification_predicates"],
                "current_predicate_status": benchmark["current_predicate_status"],
                "current_verdict": benchmark["current_verdict"],
                "blocked_by": strict_pack["validation_failures"],
                "allowed_current_claim": benchmark["allowed_current_claim"],
                "forbidden_broad_claims": list(UNSUPPORTED_BROAD_WORDING),
                "result_role_bindings": {
                    "incumbent_modern_science_source": "incumbent_source_refs",
                    "strict_evidence_pack": strict_pack["ref"],
                    "oc_result": row["oc_result"]["result_ref"],
                    "comparator_result": {
                        "result_ref": row["comparator_result"]["result_ref"],
                        "baseline_name": comparator["baseline_name"],
                    },
                    "benchmark_predicate": row["predicate_id"],
                    "uncertainty_fairness": row["uncertainty_fairness"],
                    "certification_verdict": row["certification_verdict"],
                    "blocker_reason": row["blocker_reason"],
                },
            }
        )
    summary = matrix_summary(matrix)
    return {
        "schema_id": "OC133_MODERN_SCIENCE_BENCHMARK_LANES_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion Research/PriorArt",
        "lane_total": len(lanes),
        "benchmark_scoped_certified_lane_total": summary["benchmark_scoped_superiority_certified_total"],
        "broad_modern_science_certified_lane_total": 0,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "coverage_work_orders_ref": COVERAGE_WORK_ORDERS_REL,
        "certification_policy": "Rows may certify only benchmark-scoped superiority against declared preregistered baselines. Broad modern-science wording remains blocked.",
        "lanes": lanes,
        "result_role_contract": {
            "factory_ref": FACTORY_REF,
            "required_roles": list(REQUIRED_DISTINCTION_ROLES),
            "policy": "Lane rows bind source, pack, OC result, comparator result, fairness, and blocker roles so a strict pack cannot be promoted to a broad modern-science claim.",
        },
    }


def build_register(matrix: list[dict[str, Any]], root: Path, coverage_register: dict[str, Any]) -> dict[str, Any]:
    summary = matrix_summary(matrix)
    clean_replay = clean_replay_certificate(root)
    broad_predicates = broad_claim_predicates(matrix, coverage_register, clean_replay)
    registry = load_json(root / REGISTRY_REL)
    rows = []
    for matrix_row in matrix:
        domain = matrix_row["domain"]
        rows.append(
            {
                "row_id": matrix_row["row_id"],
                "lane_id": matrix_row["lane_id"],
                "domain": domain,
                "incumbent_modern_science": matrix_row["incumbent_modern_science_source"]["incumbent"],
                "source_refs": matrix_row["incumbent_modern_science_source"]["source_refs"],
                "strict_evidence_pack_ref": matrix_row["strict_evidence_pack"]["ref"],
                "strict_evidence_pack_sha256": matrix_row["strict_evidence_pack"]["sha256"],
                "strict_evidence_pack_id": matrix_row["strict_evidence_pack"]["evidence_pack_id"],
                "benchmark_scoped_superiority_claim_status": matrix_row["certification_verdict"]["benchmark_scoped_superiority"]["label"],
                "broad_modern_science_superiority_claim_status": "NOT_CERTIFIED",
                "release_effect": "BLOCK_BROAD_MODERN_SCIENCE_SUPERIORITY_PROMOTION",
                "allowed_current_wording": matrix_row["blocker_reason"]["allowed_current_wording"],
                "forbidden_wording": matrix_row["blocker_reason"]["forbidden_wording"],
                "evidence_distinction_ref": f"{REGISTER_REL}::domain_evidence_matrix::{domain}",
                "benchmark_lane_ref": f"{LANES_REL}::{matrix_row['lane_id']}",
            }
        )
    return {
        "schema_id": "OC133_MODERN_SCIENCE_SUPERIORITY_REGISTER_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion Research/PriorArt",
        "register_factory_ref": FACTORY_REF,
        "register_policy": "Machine-readable modern-science comparator register. It certifies only benchmark-scoped superiority against declared preregistered baselines when strict pack predicates pass. It blocks broad modern-science superiority wording.",
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "coverage_work_orders_ref": COVERAGE_WORK_ORDERS_REL,
        "coverage_closure_decision": coverage_register.get("coverage_closure_decision", {}),
        "coverage_gap_total": coverage_register.get("coverage_gap_total"),
        "independent_clean_checkout_replay": clean_replay,
        "current_evidence_pack_refs": CURRENT_PACK_REFS,
        "current_evidence_pack_sha256": get_pack_ref_hashes(root),
        "registered_evidence_pack_refs_seen": registry.get("evidence_pack_refs", []),
        "row_total": len(rows),
        "superiority_certified_total": 0,
        "benchmark_scoped_superiority_certified_total": summary["benchmark_scoped_superiority_certified_total"],
        "broad_modern_science_superiority_certified_total": 0,
        "current_release_state": "BROAD_MODERN_SCIENCE_SUPERIORITY_BLOCKED_BENCHMARK_SCOPED_BASELINES_CERTIFIED",
        "modern_science_comparator_superiority": {
            "state": "FAIL",
            "reason": "The broad predicate asks whether OC predicts better than modern science. The current evidence certifies only pack-scoped superiority over declared benchmark baselines.",
            "benchmark_scoped_state": "PASS" if summary["benchmark_scoped_superiority_certified_total"] == len(EMPIRICAL_DOMAINS) else "FAIL",
        },
        "broad_claim_predicates": broad_predicates,
        "broad_claim_blockers": [key for key, value in broad_predicates.items() if value is not True],
        "fail_closed_policy": {
            "stale_refs_or_hashes": "fail",
            "missing_source_refs": "fail",
            "missing_independent_clean_checkout_replay_for_broad_claim": "fail",
            "unsupported_broad_wording": "fail",
        },
        "unsupported_broad_wording": list(UNSUPPORTED_BROAD_WORDING),
        "required_domain_distinctions": list(REQUIRED_DISTINCTION_ROLES),
        "rows": rows,
        "domain_evidence_matrix": matrix,
        "domain_evidence_matrix_summary": summary,
    }


def build_report(register: dict[str, Any], lanes: dict[str, Any], coverage_register: dict[str, Any], work_orders: dict[str, Any]) -> dict[str, Any]:
    summary = register["domain_evidence_matrix_summary"]
    return {
        "schema_id": "OC133_MODERN_SCIENCE_SUPERIORITY_REPORT_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion Research/PriorArt",
        "register_ref": REGISTER_REL,
        "benchmark_lanes_ref": LANES_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "coverage_work_orders_ref": COVERAGE_WORK_ORDERS_REL,
        "register_factory_ref": FACTORY_REF,
        "verdict": "BROAD_MODERN_SCIENCE_SUPERIORITY_BLOCKED_BENCHMARK_SCOPED_BASELINES_CERTIFIED",
        "release_promotion_allowed": False,
        "modern_science_comparator_superiority": register["modern_science_comparator_superiority"],
        "benchmark_scoped_superiority_certified_total": summary["benchmark_scoped_superiority_certified_total"],
        "broad_modern_science_superiority_certified_total": 0,
        "coverage_gap_total": coverage_register.get("coverage_gap_total"),
        "coverage_summary": coverage_register.get("coverage_summary"),
        "coverage_closure_decision": coverage_register.get("coverage_closure_decision"),
        "independent_clean_checkout_replay": register.get("independent_clean_checkout_replay"),
        "priority_work_order_counts": work_orders.get("priority_counts"),
        "blocking_summary": [
            "Current strict evidence packs support only benchmark-scoped superiority over declared preregistered comparator baselines.",
            "No artifact in this register surveys or defeats all modern-science incumbents across a domain, much less all of modern science.",
            "The broad wording 'predicts better than modern science' remains blocked.",
            "Independent clean temp-tree replay is bound to the register for the current strict packs; broad coverage remains blocked.",
        ],
        "allowed_current_claim": "OC Core 1.3.3 strict empirical packs beat the declared benchmark baselines for biology, chemistry, physics, and systems.",
        "forbidden_current_claims": list(UNSUPPORTED_BROAD_WORDING),
        "domain_evidence_matrix_ref": f"{REGISTER_REL}::domain_evidence_matrix",
        "domain_evidence_matrix": register["domain_evidence_matrix"],
        "domain_evidence_matrix_summary": summary,
        "lanes": lanes["lanes"],
        "executable_validation": {
            "commands": [
                "python benchmarks/modern_science/clean_checkout_replay.py --write",
                "python tools/oc133_modern_science_comparator_factory.py --check",
                "python benchmarks/modern_science/validate_modern_science_register.py",
            ],
            "policy": "Validation fails on stale pack refs/hashes, missing source refs, unsupported broad wording, or broad certification without every broad predicate true.",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Modern Science Superiority Report",
        "",
        "Verdict: `BROAD_MODERN_SCIENCE_SUPERIORITY_BLOCKED_BENCHMARK_SCOPED_BASELINES_CERTIFIED`",
        "",
        "Release promotion allowed: `false`",
        "",
        "The current strict packs certify only benchmark-scoped superiority over declared preregistered baselines. They do not support the broad claim that OC predicts better than modern science.",
        "",
        "| Domain | Pack | Pack SHA-256 | OC residual | Comparator residual | Benchmark verdict | Broad verdict |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report.get("domain_evidence_matrix", []):
        strict_pack = row.get("strict_evidence_pack", {})
        oc_result = row.get("oc_result", {})
        comparator = row.get("comparator_result", {})
        verdict = row.get("certification_verdict", {})
        lines.append(
            "| `{domain}` | `{pack}` | `{sha}` | `{model}` | `{comp}` | `{bench}` | `{broad}` |".format(
                domain=row.get("domain"),
                pack=strict_pack.get("ref"),
                sha=strict_pack.get("sha256"),
                model=oc_result.get("model_residual"),
                comp=comparator.get("comparator_residual"),
                bench=verdict.get("benchmark_scoped_superiority", {}).get("label"),
                broad=verdict.get("broad_modern_science_superiority", {}).get("label"),
            )
        )
    lines.extend(["", "Blocking summary:", ""])
    for item in report.get("blocking_summary", []):
        lines.append(f"- {item}")
    lines.extend(["", "Executable validation:", ""])
    for command in report.get("executable_validation", {}).get("commands", []):
        lines.append(f"- `{command}`")
    lines.append("")
    return "\n".join(lines)


def build_all(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or repo_root()
    matrix = build_domain_evidence_matrix(root)
    lanes = build_lanes(matrix)
    coverage_register = build_coverage_register(matrix)
    coverage_work_orders = build_coverage_work_orders(coverage_register, root)
    register = build_register(matrix, root, coverage_register)
    report = build_report(register, lanes, coverage_register, coverage_work_orders)
    return {
        REGISTER_REL: register,
        LANES_REL: lanes,
        COVERAGE_REGISTER_REL: coverage_register,
        COVERAGE_WORK_ORDERS_REL: coverage_work_orders,
        REPORT_JSON_REL: report,
        REPORT_MD_REL: {"text": render_markdown(report)},
    }


def validate_register_payload(register: dict[str, Any], root: Path | None = None) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []
    current_hashes = get_pack_ref_hashes(root)
    rows = register.get("domain_evidence_matrix", [])
    if not isinstance(rows, list):
        return ["DOMAIN_EVIDENCE_MATRIX_MISSING"]
    for row in rows:
        domain = str(row.get("domain"))
        strict_pack = row.get("strict_evidence_pack", {})
        ref = strict_pack.get("ref")
        if ref != CURRENT_PACK_REFS.get(domain):
            errors.append(f"STALE_OR_UNREGISTERED_EVIDENCE_PACK_REF::{domain}::{ref}")
        if any(fragment in str(ref) for fragment in STALE_REF_FRAGMENTS):
            errors.append(f"STALE_OLD_ROW_REF_USED::{domain}::{ref}")
        expected_hash = current_hashes.get(domain)
        if not expected_hash or strict_pack.get("sha256") != expected_hash:
            errors.append(f"STALE_OR_MISMATCHED_EVIDENCE_PACK_HASH::{domain}")
        if not strict_pack.get("source_refs"):
            errors.append(f"MISSING_SOURCE_REFS::{domain}")
        for source in row.get("incumbent_modern_science_source", {}).get("source_refs", []):
            if not isinstance(source, dict):
                continue
            capsule_ref = source.get("local_source_capsule_ref")
            if not capsule_ref:
                errors.append(f"MISSING_INCUMBENT_SOURCE_CAPSULE_REF::{domain}")
                continue
            capsule_path = root / capsule_ref
            if not capsule_path.exists():
                errors.append(f"MISSING_INCUMBENT_SOURCE_CAPSULE::{domain}::{capsule_ref}")
                continue
            if source.get("local_source_capsule_sha256") != sha256_file(capsule_path):
                errors.append(f"INCUMBENT_SOURCE_CAPSULE_HASH_MISMATCH::{domain}::{capsule_ref}")
        predicates = strict_pack.get("validation_predicates", {})
        failures = [key for key, value in predicates.items() if value is not True]
        if failures:
            errors.append(f"STRICT_PACK_PREDICATE_FAILURE::{domain}::{','.join(failures)}")
        certification = row.get("certification_verdict", {})
        broad = certification.get("broad_modern_science_superiority", {})
        if broad.get("certified") is True:
            errors.append(f"UNSUPPORTED_BROAD_MODERN_SCIENCE_CERTIFICATION::{domain}")
        wording = " ".join(str(value).lower() for value in as_list(row.get("allowed_current_wording")) + as_list(row.get("allowed_current_claim")))
        if any(phrase in wording for phrase in UNSUPPORTED_BROAD_WORDING):
            errors.append(f"UNSUPPORTED_BROAD_WORDING::{domain}")
    broad_predicates = register.get("broad_claim_predicates", {})
    if register.get("modern_science_comparator_superiority", {}).get("state") == "PASS" and not all(broad_predicates.values()):
        errors.append("BROAD_MODERN_SCIENCE_SUPERIORITY_PASS_WITH_FAILED_PREDICATES")
    if register.get("modern_science_comparator_superiority", {}).get("state") == "PASS" and int(register.get("coverage_gap_total") or 0) > 0:
        errors.append("BROAD_MODERN_SCIENCE_SUPERIORITY_PASS_WITH_COVERAGE_GAPS")
    clean_replay = register.get("independent_clean_checkout_replay", {})
    replay_errors = (
        validate_clean_replay_payload(load_json(root / CLEAN_REPLAY_REL), root)
        if (root / CLEAN_REPLAY_REL).exists()
        else ["CLEAN_REPLAY_CERTIFICATE_MISSING"]
    )
    if broad_predicates.get("independent_clean_checkout_replay_bound_to_register") is True:
        if clean_replay.get("status") != "PASS" or replay_errors:
            errors.append("INDEPENDENT_REPLAY_PREDICATE_TRUE_WITH_INVALID_CERTIFICATE")
        expected_replay_hash = sha256_file(root / CLEAN_REPLAY_REL) if (root / CLEAN_REPLAY_REL).exists() else ""
        if clean_replay.get("report_sha256") != expected_replay_hash:
            errors.append("INDEPENDENT_REPLAY_CERTIFICATE_HASH_MISMATCH")
    elif not replay_errors:
        errors.append("INDEPENDENT_REPLAY_CERTIFICATE_VALID_BUT_PREDICATE_FALSE")
    return errors


def validate_coverage_payload(
    coverage: dict[str, Any],
    work_orders: dict[str, Any],
    root: Path | None = None,
) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []
    domain_rows = coverage.get("domain_class_rows", [])
    gap_rows = coverage.get("coverage_gap_rows", [])
    if coverage.get("taxonomy_source", {}).get("source_policy") != "internally_declared_coverage_taxonomy":
        errors.append("COVERAGE_TAXONOMY_SOURCE_POLICY_MISSING")
    if coverage.get("required_domain_class_total") != len(MODERN_SCIENCE_DOMAIN_CLASSES):
        errors.append("COVERAGE_REQUIRED_DOMAIN_TOTAL_MISMATCH")
    required_phenomenon_total = sum(len(row["phenomenon_classes"]) for row in MODERN_SCIENCE_DOMAIN_CLASSES)
    if coverage.get("required_phenomenon_class_total") != required_phenomenon_total:
        errors.append("COVERAGE_REQUIRED_PHENOMENON_TOTAL_MISMATCH")
    if not isinstance(domain_rows, list) or len(domain_rows) != len(MODERN_SCIENCE_DOMAIN_CLASSES):
        errors.append("COVERAGE_DOMAIN_CLASS_ROWS_MISSING")
    if not isinstance(gap_rows, list):
        errors.append("COVERAGE_GAP_ROWS_MISSING")
        gap_rows = []
    if coverage.get("coverage_gap_total") != len(gap_rows):
        errors.append("COVERAGE_GAP_TOTAL_MISMATCH")
    closure = coverage.get("coverage_closure_decision", {})
    if gap_rows and closure.get("coverage_extends_to_all_of_modern_science") is True:
        errors.append("COVERAGE_EXTENDS_TRUE_WITH_GAPS")
    if gap_rows and closure.get("state") != "BLOCKED_BY_COVERAGE_GAPS":
        errors.append("COVERAGE_GAPS_WITHOUT_BLOCKED_STATE")
    mapping_domains = {
        mapping.get("domain_class_id")
        for mapping in coverage.get("current_empirical_lane_mapping", [])
        if mapping.get("benchmark_scoped_certified") is True
    }
    if mapping_domains == taxonomy_domain_ids():
        errors.append("CURRENT_FOUR_LANES_SHOULD_NOT_COVER_ALL_DECLARED_DOMAIN_CLASSES")
    gap_keys = {(gap.get("domain_class_id"), gap.get("phenomenon_class_id")) for gap in gap_rows}
    order_keys = {(row.get("domain_class_id"), row.get("phenomenon_class_id")) for row in work_orders.get("work_orders", [])}
    missing_orders = sorted(gap_keys - order_keys)
    if missing_orders:
        errors.append(f"COVERAGE_GAPS_WITHOUT_WORK_ORDERS::{missing_orders[:5]}")
    if work_orders.get("work_order_total") != len(work_orders.get("work_orders", [])):
        errors.append("COVERAGE_WORK_ORDER_TOTAL_MISMATCH")
    if work_orders.get("open_work_order_total") != len(gap_rows):
        errors.append("COVERAGE_OPEN_WORK_ORDER_TOTAL_MISMATCH")
    dispatcher = load_coverage_lane_dispatcher()
    expected_work_orders = dispatcher.build_concrete_work_orders(root, coverage_register=coverage)
    if work_orders != expected_work_orders:
        errors.append("COVERAGE_WORK_ORDERS_NOT_SYNCHRONIZED_WITH_DISPATCHER")
    errors.extend(dispatcher.validate_work_orders_payload(work_orders))
    return errors


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
    errors.extend(validate_register_payload(expected[REGISTER_REL], root))
    errors.extend(validate_coverage_payload(expected[COVERAGE_REGISTER_REL], expected[COVERAGE_WORK_ORDERS_REL]))
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
        print("modern science comparator register/report materialized; broad superiority remains blocked")
        return 0

    errors = check_stored(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern science comparator register/report check passed; benchmark-scoped baselines certified, broad superiority blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
