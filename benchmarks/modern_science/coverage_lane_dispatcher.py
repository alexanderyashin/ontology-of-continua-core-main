from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
SCHEMA_ID = "OC133_MODERN_SCIENCE_COVERAGE_LANE_QUEUE_v1"
TELEMETRY_SCHEMA_ID = "OC133_MODERN_SCIENCE_COVERAGE_LANE_TELEMETRY_v1"

WORK_ORDERS_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
COVERAGE_EXECUTABLE_SPECS_REL = "benchmarks/modern_science/coverage_executable_specs"
DOMAIN_LOCAL_COVERAGE_ROOT_REL = "validation/heldout/grand_science"
DOMAIN_LOCAL_COVERAGE_GLOB = "*/coverage_work_orders/*MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
QUEUE_REPORT_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json"
TELEMETRY_REPORT_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_TELEMETRY.json"
COCKPIT_REL = "operations/logion_release_mission/oc_core_1_3_3/OC133_MODERN_SCIENCE_COVERAGE_LANE_COCKPIT.md"
DISPATCHER_REF = "benchmarks/modern_science/coverage_lane_dispatcher.py"

PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}

NO_SEND_LOCKS = {
    "no_send": True,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
    "registry_write_allowed": False,
    "journal_submission_allowed": False,
    "email_allowed": False,
    "coverage_closure_allowed": False,
    "broad_modern_science_superiority_allowed": False,
    "all_domain_scientific_closure_allowed": False,
}

OWNER_CAPABILITIES = {
    "formal_mathematics_and_logic": "Logion Formal Methods / Proof-Route Planning",
    "physical_sciences": "Logion Physics Evidence / Official Constants and Measurements",
    "chemical_sciences": "Logion Chemistry Evidence / Official Descriptor and Reaction Data",
    "earth_space_environmental_sciences": "Logion Earth-Space Evidence / Official Geophysical Data",
    "biological_life_sciences": "Logion Biology Evidence / Public Repository Targets",
    "medical_health_sciences": "Logion Health Evidence / Regulated Clinical and Epidemiology Sources",
    "agricultural_food_sciences": "Logion Agriculture Evidence / Food, Crop, and Veterinary Sources",
    "engineering_materials_sciences": "Logion Engineering Evidence / Applied Measurement Sources",
    "computer_information_sciences": "Logion CS Evidence / Verification and Evaluation Sources",
    "cognitive_behavioral_neurosciences": "Logion Neurobehavioral Evidence / Public Experiment Sources",
    "social_economic_political_sciences": "Logion Systems Evidence / Official Statistical Sources",
    "complex_systems_operations_science": "Logion Operations Evidence / Intervention and Queueing Sources",
}

OFFICIAL_SOURCE_DEFAULTS = {
    "formal_mathematics_and_logic": [
        "Lean/mathlib or equivalent formal corpus with stable artifact hashes",
        "proof-checker logs, theorem inventory snapshots, and protocol-only source capsules",
    ],
    "physical_sciences": [
        "NIST/CODATA/SI official constants and relationship tables",
        "mission or laboratory measurement archives with immutable snapshot hashes",
    ],
    "chemical_sciences": [
        "PubChem, NIST Chemistry WebBook, IUPAC, or equivalent public chemistry records",
        "target descriptor/reaction snapshots with target-hidden scoring attestations",
    ],
    "earth_space_environmental_sciences": [
        "NOAA, NASA, USGS, ESA/Copernicus, or equivalent official earth/space archives",
        "time-locked remote-sensing, hydrology, geophysical, climate, or planetary snapshots",
    ],
    "biological_life_sciences": [
        "NCBI, EMBL-EBI, Ensembl, GBIF, or equivalent public life-science repositories",
        "held-out target panels with source separation and negative controls",
    ],
    "medical_health_sciences": [
        "ClinicalTrials.gov, WHO, CDC, FDA, NIH, or equivalent regulated/public health sources",
        "deidentified public outcome or biomarker snapshots with explicit ethics boundary",
    ],
    "agricultural_food_sciences": [
        "USDA, FAOSTAT, CGIAR, WOAH, or equivalent agriculture/food/veterinary sources",
        "crop, soil, animal health, nutrition, or food safety target panels",
    ],
    "engineering_materials_sciences": [
        "NIST materials/measurement datasets, standards bodies, or official laboratory archives",
        "property, control, signal, transport, energy, or failure-measurement snapshots",
    ],
    "computer_information_sciences": [
        "language specifications, proof benchmarks, NIST/NVD, MLPerf, or equivalent public corpora",
        "predeclared program, security, network, or model-evaluation targets",
    ],
    "cognitive_behavioral_neurosciences": [
        "OpenNeuro, NIH, Human Connectome, or equivalent public experiment repositories",
        "predeclared neural, behavioral, psychometric, learning, or perception targets",
    ],
    "social_economic_political_sciences": [
        "World Bank WDI, OECD, UN, Census, FRED, or equivalent official statistical sources",
        "time-locked demographic, economic, institutional, network, or policy target panels",
    ],
    "complex_systems_operations_science": [
        "official operations, logistics, resilience, risk, queue, or intervention datasets",
        "predeclared multi-agent, supply-chain, response, or decision-system target panels",
    ],
}

PHYSICS_CHEMISTRY_DOMAIN_IDS = {"physical_sciences", "chemical_sciences"}
EXECUTABLE_SPEC_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_EXECUTABLE_COVERAGE_LANE_SPEC_v1"
EXECUTABLE_SPEC_REQUIRED_TOP_LEVEL_FIELDS = [
    "domain_class_id",
    "phenomenon_class_id",
    "coverage_closure_status",
]
EXECUTABLE_SPEC_REQUIRED_BLOCKS = [
    "official_data_source",
    "target_variable",
    "formula_requirement",
    "incumbent_comparator_requirement",
    "uncertainty_requirement",
    "residual_requirement",
    "negative_control_requirement",
    "falsifier_requirement",
    "execution_requirements",
    "current_evidence",
]
EXECUTABLE_SPEC_REQUIRED_PREDICATES = [
    "STRICT_PACK_SCHEMA_PASS",
    "OFFICIAL_SOURCE_SNAPSHOT_LOCKED",
    "TARGET_VARIABLE_EXACTLY_DECLARED",
    "FORMULA_OR_MODEL_PREREGISTERED",
    "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
    "UNCERTAINTY_POLICY_DECLARED",
    "RESIDUAL_METRIC_EXECUTABLE",
    "NEGATIVE_CONTROLS_EXECUTABLE_AND_REJECTED",
    "FALSIFIERS_EXECUTABLE_AND_NOT_TRIGGERED",
    "INDEPENDENT_REPLAY_PASS",
    "COVERAGE_REGISTER_GAP_CLOSED_BY_REVIEW",
]
PLACEHOLDER_TOKENS = ("tbd", "placeholder", "authoritative source(s)", "equivalent public")

DEFAULT_EXECUTABLE_LANE_SPECS: dict[tuple[str, str], dict[str, Any]] = {
    (
        "physical_sciences",
        "dynamical_laws_and_conservation",
    ): {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "coverage_closure_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "source_plan_id": "MS-PHYS-DYNAMICS-JPL-HORIZONS-VECTORS-v1",
        "official_data_source": {
            "source_id": "physics_jpl_horizons_state_vectors_earth_sun_v1",
            "source_name": "NASA/JPL Solar System Dynamics HORIZONS API vector ephemerides",
            "source_authority": "NASA Jet Propulsion Laboratory Solar System Dynamics",
            "official_documentation_url": "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
            "official_endpoint_url": "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='399'&OBJ_DATA='NO'&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&CENTER='500@10'&START_TIME='2026-Jan-01'&STOP_TIME='2026-Jan-21'&STEP_SIZE='1%20d'&VEC_TABLE='3'&OUT_UNITS='KM-S'&CSV_FORMAT='YES'",
            "required_local_snapshot_ref": "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/OC133_PHYSICS_JPL_HORIZONS_EARTH_SUN_VECTORS.json",
            "required_lock_ref": "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/OC133_PHYSICS_JPL_HORIZONS_EARTH_SUN_VECTORS.lock.json",
            "minimum_rows_required": 20,
            "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
        },
        "target_variable": {
            "name": "next_epoch_heliocentric_cartesian_state_vector",
            "unit": "km and km/s",
            "target_fields": ["X", "Y", "Z", "VX", "VY", "VZ"],
            "extraction_rule": "For each epoch after the first, hide the official HORIZONS vector row until the predeclared dynamical propagation is materialized from prior visible rows.",
        },
        "formula_requirement": {
            "formula_or_model": "Two-body Kepler/Newton propagation from the previous heliocentric state vector using the predeclared solar GM constant and fixed integration step.",
            "required_inputs": ["prior_epoch_XYZ_VXYZ", "delta_t_seconds", "solar_GM_km3_s2"],
            "target_values_may_be_used_for_model_design": False,
        },
        "incumbent_comparator_requirement": {
            "baseline_name": "constant-velocity Cartesian extrapolation baseline",
            "prediction_rule": "Propagate the previous vector by linear X,Y,Z += VX,VY,VZ*delta_t and keep velocity unchanged.",
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
            "required_material_margin": "model vector RMSE must be lower than comparator vector RMSE on the same hidden epochs",
        },
        "uncertainty_requirement": {
            "metric": "componentwise absolute error with vector RMSE aggregation",
            "rule": "Use HORIZONS output precision from the locked snapshot plus a preregistered numerical integration tolerance; do not tune tolerance after target opening.",
        },
        "residual_requirement": {
            "metric_id": "vector_rmse_with_component_uncertainty_v1",
            "formula": "sqrt(mean((predicted_component - observed_component)^2)) over X,Y,Z,VX,VY,VZ after unit normalization",
            "superiority_rule": "model_residual < comparator_residual and residual_within_declared_uncertainty is true",
        },
        "negative_control_requirement": {
            "control_id": "PHYS-DYNAMICS-CONSTANT-VELOCITY-BASELINE",
            "rule": "constant-velocity extrapolation must be materially worse than the preregistered dynamical propagation on the same hidden target rows",
        },
        "falsifier_requirement": {
            "falsifier_id": "PHYS-DYNAMICS-HORIZONS-STATE-FALSIFIER",
            "trigger": "model vector RMSE exceeds the declared uncertainty, comparator is not worse, target vector appears in visible inputs, or fewer than 20 locked official epochs are scored",
        },
        "execution_requirements": {
            "minimum_n": 20,
            "source_separation_mode": "prospective",
            "target_hidden_until_scoring": True,
            "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
            "replay_command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        },
        "current_evidence": {
            "executable_evidence_exists": False,
            "executable_evidence_ref": None,
            "reason": "No locked NASA/JPL HORIZONS snapshot, target projection, scorer, or strict evidence pack exists for this coverage class.",
        },
        "closure_predicates_required": EXECUTABLE_SPEC_REQUIRED_PREDICATES,
    },
    (
        "physical_sciences",
        "condensed_matter_fields_and_measurements",
    ): {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "coverage_closure_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "source_plan_id": "MS-PHYS-CONDENSED-NIST-JARVIS-DFT-v1",
        "official_data_source": {
            "source_id": "physics_nist_jarvis_dft_bandgap_v1",
            "source_name": "NIST-JARVIS JARVIS-DFT materials property records",
            "source_authority": "National Institute of Standards and Technology",
            "official_documentation_url": "https://jarvis.nist.gov/",
            "official_endpoint_url": "https://jarvis.nist.gov/optimade/jarvisdft/",
            "required_local_snapshot_ref": "validation/heldout/grand_science/physics_chemistry/nist_jarvis_dft/OC133_NIST_JARVIS_DFT_BANDGAP_SNAPSHOT.json",
            "required_lock_ref": "validation/heldout/grand_science/physics_chemistry/nist_jarvis_dft/OC133_NIST_JARVIS_DFT_BANDGAP_SNAPSHOT.lock.json",
            "minimum_rows_required": 20,
            "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
        },
        "target_variable": {
            "name": "optB88vdW_electronic_bandgap_eV",
            "unit": "eV",
            "target_fields": ["optB88vdW electronic bandgap"],
            "extraction_rule": "Hide the JARVIS-DFT bandgap field until a predeclared composition/structure model and comparator have been materialized from visible formula and structure descriptors.",
        },
        "formula_requirement": {
            "formula_or_model": "Predeclared composition/structure descriptor model mapping visible stoichiometry, elements, density, and lattice descriptors to bandgap_eV.",
            "required_inputs": ["formula", "elements", "stoichiometry", "lattice_descriptors"],
            "target_values_may_be_used_for_model_design": False,
        },
        "incumbent_comparator_requirement": {
            "baseline_name": "composition-family median bandgap baseline",
            "prediction_rule": "Predict the median bandgap of the visible chemical-system or element-count family computed without hidden target rows.",
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
            "required_material_margin": "model MAE must be lower than comparator MAE by a preregistered positive margin",
        },
        "uncertainty_requirement": {
            "metric": "mean_absolute_error_eV_with_bootstrap_interval",
            "rule": "Declare row-level tolerance and bootstrap confidence interval before target opening; source field precision alone cannot close the lane.",
        },
        "residual_requirement": {
            "metric_id": "bandgap_mae_eV_with_bootstrap_superiority_v1",
            "formula": "mean(abs(predicted_bandgap_eV - observed_bandgap_eV))",
            "superiority_rule": "model_MAE + upper_interval_margin < comparator_MAE",
        },
        "negative_control_requirement": {
            "control_id": "PHYS-CONDENSED-COMPOSITION-MEDIAN-BASELINE",
            "rule": "composition-family median and shuffled-structure controls must be worse than the preregistered model",
        },
        "falsifier_requirement": {
            "falsifier_id": "PHYS-CONDENSED-JARVIS-BANDGAP-FALSIFIER",
            "trigger": "target bandgap leaks into visible inputs, N<20, model interval overlaps or loses to comparator, or official snapshot/lock hash is missing",
        },
        "execution_requirements": {
            "minimum_n": 20,
            "source_separation_mode": "target_blind",
            "target_hidden_until_scoring": True,
            "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
            "replay_command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        },
        "current_evidence": {
            "executable_evidence_exists": False,
            "executable_evidence_ref": None,
            "reason": "No locked NIST-JARVIS snapshot, target projection, scorer, or strict evidence pack exists for this coverage class.",
        },
        "closure_predicates_required": EXECUTABLE_SPEC_REQUIRED_PREDICATES,
    },
    (
        "physical_sciences",
        "astronomical_and_cosmological_observables",
    ): {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "coverage_closure_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "source_plan_id": "MS-PHYS-ASTRO-NASA-EXOPLANET-KEPLER-v1",
        "official_data_source": {
            "source_id": "physics_nasa_exoplanet_archive_pscomppars_kepler_v1",
            "source_name": "NASA Exoplanet Archive TAP Planetary Systems Composite Parameters",
            "source_authority": "NASA Exoplanet Archive / IPAC",
            "official_documentation_url": "https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html",
            "official_endpoint_url": "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_orbper,st_mass,pl_orbsmax,pl_orbsmaxerr1,pl_orbsmaxerr2+from+pscomppars+where+pl_orbper+is+not+null+and+st_mass+is+not+null+and+pl_orbsmax+is+not+null&format=json",
            "required_local_snapshot_ref": "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/OC133_NASA_EXOPLANET_PS_COMPOSITE_KEPLER.json",
            "required_lock_ref": "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/OC133_NASA_EXOPLANET_PS_COMPOSITE_KEPLER.lock.json",
            "minimum_rows_required": 20,
            "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
        },
        "target_variable": {
            "name": "pl_orbsmax",
            "unit": "AU",
            "target_fields": ["pl_orbsmax", "pl_orbsmaxerr1", "pl_orbsmaxerr2"],
            "extraction_rule": "Hide semi-major-axis target columns until the Kepler-law calculation is materialized from visible orbital period and stellar mass columns.",
        },
        "formula_requirement": {
            "formula_or_model": "Kepler third-law semi-major axis: ((G * st_mass * M_sun * (pl_orbper_days*86400)^2)/(4*pi^2))^(1/3) / AU",
            "required_inputs": ["pl_orbper", "st_mass"],
            "target_values_may_be_used_for_model_design": False,
        },
        "incumbent_comparator_requirement": {
            "baseline_name": "period-only median stellar-mass Kepler baseline",
            "prediction_rule": "Use the same formula but replace each hidden row's stellar mass with the preregistered visible-panel median stellar mass.",
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
            "required_material_margin": "formula residual must beat the median-mass comparator residual on the same hidden rows",
        },
        "uncertainty_requirement": {
            "metric": "absolute_AU_error_with_archive_errorbar_or_materiality_floor",
            "rule": "Use pl_orbsmaxerr1/pl_orbsmaxerr2 when present and a preregistered AU materiality floor otherwise.",
        },
        "residual_requirement": {
            "metric_id": "semi_major_axis_absolute_error_AU_v1",
            "formula": "abs(predicted_pl_orbsmax_AU - observed_pl_orbsmax_AU)",
            "superiority_rule": "mean model residual must be lower than comparator residual and within declared uncertainty/materiality policy",
        },
        "negative_control_requirement": {
            "control_id": "PHYS-ASTRO-MEDIAN-MASS-KEPLER-BASELINE",
            "rule": "median-stellar-mass Kepler baseline and period-shuffle control must be worse than the rowwise formula",
        },
        "falsifier_requirement": {
            "falsifier_id": "PHYS-ASTRO-EXOPLANET-KEPLER-FALSIFIER",
            "trigger": "target semi-major-axis leaks into visible inputs, N<20, residuals exceed uncertainty policy, or comparator is not worse",
        },
        "execution_requirements": {
            "minimum_n": 20,
            "source_separation_mode": "target_blind",
            "target_hidden_until_scoring": True,
            "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
            "replay_command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        },
        "current_evidence": {
            "executable_evidence_exists": False,
            "executable_evidence_ref": None,
            "reason": "No locked NASA Exoplanet Archive snapshot, target projection, scorer, or strict evidence pack exists for this coverage class.",
        },
        "closure_predicates_required": EXECUTABLE_SPEC_REQUIRED_PREDICATES,
    },
    (
        "chemical_sciences",
        "reaction_and_kinetics_prediction",
    ): {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "coverage_closure_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "source_plan_id": "MS-CHEM-KINETICS-NIST-WATER-v1",
        "official_data_source": {
            "source_id": "chemistry_nist_kinetics_water_v1",
            "source_name": "NIST Chemical Kinetics Database gas-phase reaction records",
            "source_authority": "National Institute of Standards and Technology",
            "official_documentation_url": "https://kinetics.nist.gov/kinetics/",
            "official_endpoint_url": "https://kinetics.nist.gov/kinetics/rpSearch?cas=7732185",
            "required_local_snapshot_ref": "validation/_raw/chemistry_nist_kinetics_water_v1.html",
            "required_lock_ref": "validation/heldout/grand_science/physics_chemistry/official_batch/locks/chemistry_nist_kinetics_water_v1.json",
            "minimum_rows_required": 20,
            "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
        },
        "target_variable": {
            "name": "rate_constant_k_T",
            "unit": "source-declared kinetics units",
            "target_fields": ["A", "n", "Ea", "T_min", "T_max", "k(T)"],
            "extraction_rule": "Hide rate constants or Arrhenius parameters until predictions are materialized from visible reactant/product identifiers, temperature grid, and preregistered formula.",
        },
        "formula_requirement": {
            "formula_or_model": "Arrhenius or modified Arrhenius replay: k(T)=A*T^n*exp(-Ea/(R*T)) with all coefficient-use rules declared before target opening.",
            "required_inputs": ["reaction_identifiers", "temperature_K", "visible_A_n_Ea_when_not_target", "gas_constant_R"],
            "target_values_may_be_used_for_model_design": False,
        },
        "incumbent_comparator_requirement": {
            "baseline_name": "temperature-shuffled Arrhenius coefficient baseline",
            "prediction_rule": "Use preregistered shuffled or family-median Arrhenius coefficients that do not read the hidden target row.",
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
            "required_material_margin": "model log10(k) residual must be lower than comparator residual",
        },
        "uncertainty_requirement": {
            "metric": "absolute_log10_rate_error_with_source_uncertainty_or_declared_dex_floor",
            "rule": "Use source uncertainty when present; otherwise use a preregistered dex tolerance before target opening.",
        },
        "residual_requirement": {
            "metric_id": "kinetics_log10_rate_residual_v1",
            "formula": "abs(log10(predicted_k_T) - log10(observed_k_T))",
            "superiority_rule": "mean log residual must beat comparator and meet uncertainty/materiality threshold",
        },
        "negative_control_requirement": {
            "control_id": "CHEM-KINETICS-SHUFFLED-ARRHENIUS-BASELINE",
            "rule": "temperature-shuffled or family-median Arrhenius baseline must be materially worse than the preregistered kinetic formula/model",
        },
        "falsifier_requirement": {
            "falsifier_id": "CHEM-KINETICS-NIST-FALSIFIER",
            "trigger": "target rate constants leak into visible inputs, N<20, source lock missing, residuals exceed uncertainty, or comparator is not worse",
        },
        "execution_requirements": {
            "minimum_n": 20,
            "source_separation_mode": "prospective",
            "target_hidden_until_scoring": True,
            "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
            "replay_command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        },
        "current_evidence": {
            "executable_evidence_exists": False,
            "executable_evidence_ref": None,
            "reason": "No locked NIST kinetics snapshot, target projection, scorer, or strict evidence pack exists for this coverage class.",
        },
        "closure_predicates_required": EXECUTABLE_SPEC_REQUIRED_PREDICATES,
    },
    (
        "chemical_sciences",
        "thermochemistry_and_phase_behavior",
    ): {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "coverage_closure_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "source_plan_id": "MS-CHEM-THERMO-NIST-WEBBOOK-WATER-v1",
        "official_data_source": {
            "source_id": "chemistry_nist_webbook_water_gas_thermo_v1",
            "source_name": "NIST Chemistry WebBook SRD 69 gas-phase thermochemistry tables",
            "source_authority": "National Institute of Standards and Technology",
            "official_documentation_url": "https://webbook.nist.gov/chemistry/",
            "official_endpoint_url": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI&Mask=1#Thermo-Gas",
            "required_local_snapshot_ref": "validation/_raw/chemistry_nist_webbook_water_gas_thermo_v1.html",
            "required_lock_ref": "validation/heldout/grand_science/physics_chemistry/official_batch/locks/chemistry_nist_webbook_water_gas_thermo_v1.json",
            "minimum_rows_required": 20,
            "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
        },
        "target_variable": {
            "name": "Shomate_thermochemistry_table_values",
            "unit": "J/mol/K, kJ/mol, or source-declared SI units",
            "target_fields": ["Cp", "S", "H_minus_H_298", "Delta_f_H"],
            "extraction_rule": "Hide tabulated thermochemistry values until Shomate-equation predictions are materialized from visible coefficients and temperature grid.",
        },
        "formula_requirement": {
            "formula_or_model": "NIST WebBook Shomate equation replay for Cp(T), S(T), and H(T)-H(298.15 K), with coefficient visibility fixed before scoring.",
            "required_inputs": ["Shomate_coefficients", "temperature_K"],
            "target_values_may_be_used_for_model_design": False,
        },
        "incumbent_comparator_requirement": {
            "baseline_name": "constant-Cp and linear-enthalpy thermochemistry baseline",
            "prediction_rule": "Use source-visible 298.15 K anchors or panel medians, not hidden target values, to predict all temperatures.",
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
            "required_material_margin": "Shomate replay residual must beat constant/linear baseline residual",
        },
        "uncertainty_requirement": {
            "metric": "absolute_thermochemistry_error_with_table_precision_or_source_uncertainty",
            "rule": "Bind source precision/uncertainty or a preregistered SI-unit tolerance before target opening.",
        },
        "residual_requirement": {
            "metric_id": "thermochemistry_absolute_error_normalized_v1",
            "formula": "abs(predicted_value - observed_value) / declared_uncertainty_or_precision_floor",
            "superiority_rule": "normalized residual must be within tolerance and lower than comparator residual",
        },
        "negative_control_requirement": {
            "control_id": "CHEM-THERMO-CONSTANT-CP-LINEAR-H-BASELINE",
            "rule": "constant-Cp/linear-enthalpy baseline and coefficient-shuffle control must be materially worse than Shomate replay",
        },
        "falsifier_requirement": {
            "falsifier_id": "CHEM-THERMO-WEBBOOK-FALSIFIER",
            "trigger": "target thermochemistry table leaks into visible inputs, N<20, source lock missing, residual exceeds uncertainty, or comparator is not worse",
        },
        "execution_requirements": {
            "minimum_n": 20,
            "source_separation_mode": "target_blind",
            "target_hidden_until_scoring": True,
            "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
            "replay_command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        },
        "current_evidence": {
            "executable_evidence_exists": False,
            "executable_evidence_ref": None,
            "reason": "No locked NIST WebBook thermochemistry snapshot, target projection, scorer, or strict evidence pack exists for this coverage class.",
        },
        "closure_predicates_required": EXECUTABLE_SPEC_REQUIRED_PREDICATES,
    },
    (
        "chemical_sciences",
        "materials_and_spectroscopy_observables",
    ): {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "coverage_closure_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "source_plan_id": "MS-CHEM-SPECTROSCOPY-NIST-WEBBOOK-IR-v1",
        "official_data_source": {
            "source_id": "chemistry_nist_webbook_water_ir_spectrum_v1",
            "source_name": "NIST Chemistry WebBook SRD 69 infrared spectrum records",
            "source_authority": "National Institute of Standards and Technology",
            "official_documentation_url": "https://webbook.nist.gov/chemistry/",
            "official_endpoint_url": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI&Mask=80#IR-Spec",
            "required_local_snapshot_ref": "validation/_raw/chemistry_nist_webbook_water_ir_spectrum_v1.html",
            "required_lock_ref": "validation/heldout/grand_science/physics_chemistry/official_batch/locks/chemistry_nist_webbook_water_ir_spectrum_v1.json",
            "minimum_rows_required": 20,
            "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
        },
        "target_variable": {
            "name": "infrared_peak_wavenumber_and_intensity",
            "unit": "cm^-1 and source-declared intensity units",
            "target_fields": ["peak_wavenumber_cm^-1", "relative_intensity"],
            "extraction_rule": "Hide IR peak positions/intensities until a preregistered peak model is materialized from visible molecular identity and non-target metadata.",
        },
        "formula_requirement": {
            "formula_or_model": "Predeclared spectroscopy peak extractor/model mapping visible molecular identifiers and allowed metadata to target IR peak positions and intensities.",
            "required_inputs": ["molecular_identifier", "allowed_non_target_metadata"],
            "target_values_may_be_used_for_model_design": False,
        },
        "incumbent_comparator_requirement": {
            "baseline_name": "peak-shuffle and molecule-family median spectrum baseline",
            "prediction_rule": "Predict peak positions/intensities from preregistered shuffled or family-median peak lists without reading hidden target peaks.",
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
            "required_material_margin": "peak-match residual must beat shuffled/family-median comparator residual",
        },
        "uncertainty_requirement": {
            "metric": "peak_position_absolute_error_with_intensity_weighting",
            "rule": "Declare cm^-1 tolerance, intensity tolerance, and peak-matching policy before target opening.",
        },
        "residual_requirement": {
            "metric_id": "ir_peak_match_weighted_residual_v1",
            "formula": "weighted mean of matched abs(predicted_wavenumber - observed_wavenumber) plus preregistered intensity penalty",
            "superiority_rule": "model weighted residual must beat comparator residual and meet declared cm^-1/intensity tolerances",
        },
        "negative_control_requirement": {
            "control_id": "CHEM-SPECTROSCOPY-PEAK-SHUFFLE-BASELINE",
            "rule": "peak-shuffle and family-median spectrum baselines must be materially worse than the preregistered model",
        },
        "falsifier_requirement": {
            "falsifier_id": "CHEM-SPECTROSCOPY-WEBBOOK-IR-FALSIFIER",
            "trigger": "target peaks leak into visible inputs, N<20, official snapshot/lock missing, peak residual exceeds uncertainty, or comparator is not worse",
        },
        "execution_requirements": {
            "minimum_n": 20,
            "source_separation_mode": "target_blind",
            "target_hidden_until_scoring": True,
            "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
            "replay_command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        },
        "current_evidence": {
            "executable_evidence_exists": False,
            "executable_evidence_ref": None,
            "reason": "No locked NIST WebBook IR spectrum snapshot, target projection, scorer, or strict evidence pack exists for this coverage class.",
        },
        "closure_predicates_required": EXECUTABLE_SPEC_REQUIRED_PREDICATES,
    },
}


class ExecutableSpecRegistryError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def path_ref(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def lane_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("domain_class_id", "")), str(row.get("phenomenon_class_id", "")))


def is_physics_chemistry_gap(row: dict[str, Any]) -> bool:
    return str(row.get("domain_class_id", "")) in PHYSICS_CHEMISTRY_DOMAIN_IDS


def canonical_executable_spec(
    spec: dict[str, Any],
    *,
    domain_class_id: str | None = None,
    phenomenon_class_id: str | None = None,
) -> dict[str, Any]:
    row = copy.deepcopy(spec)
    if domain_class_id and not row.get("domain_class_id"):
        row["domain_class_id"] = domain_class_id
    if phenomenon_class_id and not row.get("phenomenon_class_id"):
        row["phenomenon_class_id"] = phenomenon_class_id
    return row


def normalized_payload(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def iter_executable_specs_from_payload(payload: Any, *, source_ref: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "executable_coverage_specs" in payload:
        specs = payload.get("executable_coverage_specs")
        if isinstance(specs, list):
            if any(not isinstance(item, dict) for item in specs):
                raise ExecutableSpecRegistryError([f"EXECUTABLE_SPEC_LIST_ITEM_MALFORMED::{source_ref}"])
            return [item for item in specs if isinstance(item, dict)]
        raise ExecutableSpecRegistryError([f"EXECUTABLE_SPEC_LIST_MALFORMED::{source_ref}"])
    if isinstance(payload, dict) and "executable_lane_specs" in payload:
        specs = payload.get("executable_lane_specs")
        if isinstance(specs, list):
            if any(not isinstance(item, dict) for item in specs):
                raise ExecutableSpecRegistryError([f"EXECUTABLE_SPEC_LIST_ITEM_MALFORMED::{source_ref}"])
            return [item for item in specs if isinstance(item, dict)]
        raise ExecutableSpecRegistryError([f"EXECUTABLE_SPEC_LIST_MALFORMED::{source_ref}"])
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        if any(not isinstance(item, dict) for item in payload):
            raise ExecutableSpecRegistryError([f"EXECUTABLE_SPEC_LIST_ITEM_MALFORMED::{source_ref}"])
        return [item for item in payload if isinstance(item, dict)]
    raise ExecutableSpecRegistryError([f"EXECUTABLE_SPEC_FILE_MALFORMED::{source_ref}"])


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def first_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return {}


def first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def replay_command_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        commands = string_list(value.get("commands"))
        if commands:
            return " && ".join(commands)
    return ""


def domain_local_source(row: dict[str, Any], executable: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    source = as_dict(executable.get("official_source")) or first_dict(row.get("official_sources"))
    snapshot_ref = first_nonempty(
        source.get("required_local_snapshot_ref"),
        first_nonempty(*string_list(source.get("required_local_snapshot_refs"))) if source.get("required_local_snapshot_refs") else None,
        source.get("local_snapshot_ref"),
        evidence.get("implemented_snapshot_ref"),
        evidence.get("source_snapshot_ref"),
        evidence.get("snapshot_ref"),
    )
    lock_ref = first_nonempty(
        source.get("required_lock_ref"),
        source.get("lock_ref"),
        evidence.get("implemented_lock_ref"),
    )
    return {
        "source_id": first_nonempty(source.get("source_id"), f"{row.get('domain_class_id')}_{row.get('phenomenon_class_id')}_source"),
        "source_name": first_nonempty(source.get("source_name"), source.get("title"), "Domain-local official source"),
        "source_authority": first_nonempty(source.get("source_authority"), source.get("title"), "Domain-local source authority"),
        "official_documentation_url": first_nonempty(source.get("official_documentation_url"), source.get("documentation_url"), source.get("official_url")),
        "official_endpoint_url": first_nonempty(source.get("official_endpoint_url"), source.get("official_url")),
        "required_local_snapshot_ref": snapshot_ref,
        "required_lock_ref": lock_ref,
        "minimum_rows_required": int_value(first_nonempty(row.get("minimum_n"), as_dict(executable.get("N")).get("minimum_n"), as_dict(row.get("target_variable")).get("minimum_target_rows"))) or 20,
        "snapshot_status": "ACQUIRED_OR_BOUND" if snapshot_ref else "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
    }


def domain_local_target(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    target = as_dict(executable.get("target_variable")) or as_dict(row.get("target_variable")) or as_dict(row.get("target_theorem_or_property"))
    return {
        "name": first_nonempty(target.get("name"), target.get("target_name"), row.get("phenomenon_class_id")),
        "unit": first_nonempty(target.get("unit"), target.get("target_unit"), "declared in domain-local artifact"),
        "target_fields": string_list(first_nonempty(target.get("target_fields"), target.get("hidden_target_fields"), target.get("target_field"))),
        "extraction_rule": first_nonempty(
            target.get("extraction_rule"),
            target.get("target_field"),
            as_dict(executable.get("target_hidden_split")).get("split_rule"),
            as_dict(row.get("target_hidden_split")).get("split_rule"),
            as_dict(row.get("split")).get("split_rule"),
            "Target values remain hidden until scoring according to the domain-local work order.",
        ),
    }


def domain_local_formula(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    formula = (
        as_dict(executable.get("formula_or_model"))
        or as_dict(row.get("formula_model"))
        or as_dict(row.get("formula_or_model"))
        or as_dict(row.get("prediction_formula"))
        or as_dict(row.get("proof_or_model"))
    )
    return {
        "formula_or_model": first_nonempty(formula.get("rule"), formula.get("formula_or_model"), formula.get("description"), formula.get("model_id"), "Domain-local predeclared model"),
        "required_inputs": string_list(first_nonempty(formula.get("required_inputs"), formula.get("visible_inputs"), formula.get("inputs"))),
        "target_values_may_be_used_for_model_design": bool(formula.get("target_values_used_for_model_design") is True or formula.get("target_values_may_be_used_for_model_design") is True),
    }


def domain_local_comparator(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    comparator = (
        as_dict(executable.get("preregistered_comparator"))
        or as_dict(row.get("preregistered_comparator"))
        or as_dict(row.get("incumbent_comparator"))
        or as_dict(row.get("comparator_baseline"))
    )
    return {
        "baseline_name": first_nonempty(comparator.get("baseline_name"), comparator.get("name"), comparator.get("comparator_id"), "Domain-local preregistered comparator"),
        "prediction_rule": first_nonempty(comparator.get("prediction_rule"), comparator.get("rule"), comparator.get("description"), "Preregistered comparator from the domain-local work order."),
        "pre_registered": comparator.get("pre_registered") is not False,
        "target_values_used_for_baseline_design": comparator.get("target_values_used_for_baseline_design") is True,
        "required_material_margin": first_nonempty(comparator.get("required_material_margin"), comparator.get("materiality_rule"), "model residual must beat comparator residual under the declared domain-local metric"),
    }


def domain_local_uncertainty(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    metric = (
        as_dict(executable.get("uncertainty_and_residual"))
        or as_dict(row.get("uncertainty_residual_metric"))
        or as_dict(row.get("uncertainty_and_residual"))
        or as_dict(row.get("residual_or_error_notion"))
    )
    return {
        "metric": first_nonempty(metric.get("residual_metric"), metric.get("metric"), "domain-local residual metric"),
        "rule": first_nonempty(metric.get("uncertainty_method"), metric.get("rule"), metric.get("description"), "Domain-local uncertainty policy declared before scoring."),
    }


def domain_local_residual(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    metric = (
        as_dict(executable.get("uncertainty_and_residual"))
        or as_dict(row.get("uncertainty_residual_metric"))
        or as_dict(row.get("uncertainty_and_residual"))
        or as_dict(row.get("residual_or_error_notion"))
    )
    return {
        "metric_id": first_nonempty(metric.get("metric_id"), f"{row.get('work_order_id')}_domain_local_residual"),
        "formula": first_nonempty(metric.get("residual_metric"), metric.get("formula"), "domain-local residual formula"),
        "superiority_rule": first_nonempty(metric.get("superiority_rule"), metric.get("superiority_predicate"), "model residual must be strictly better than the preregistered comparator under the declared uncertainty policy"),
    }


def domain_local_negative_control(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    negative = as_dict(executable.get("negative_control")) or as_dict(row.get("negative_control"))
    return {
        "control_id": first_nonempty(negative.get("control_id"), f"{row.get('work_order_id')}_negative_control"),
        "rule": first_nonempty(negative.get("rejection_predicate"), negative.get("rule"), negative.get("description"), "Domain-local negative control must be rejected."),
    }


def domain_local_falsifier(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    falsifier = as_dict(executable.get("falsifier")) or as_dict(row.get("falsifier")) or {"triggers": row.get("falsifier_predicates")}
    trigger = first_nonempty(falsifier.get("trigger"), "; ".join(string_list(falsifier.get("triggers"))), "; ".join(string_list(row.get("falsifier_predicates"))))
    return {
        "falsifier_id": first_nonempty(falsifier.get("falsifier_id"), f"{row.get('work_order_id')}_falsifier"),
        "trigger": trigger or "Domain-local falsifier triggers if source locks, target hiding, comparator, controls, or replay predicates fail.",
    }


def domain_local_current_evidence(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    evidence = (
        as_dict(row.get("current_evidence_status"))
        or as_dict(row.get("current_evidence_assessment"))
        or as_dict(executable.get("fail_closed_current_evidence"))
    )
    evidence_ref = first_nonempty(
        evidence.get("implemented_scoring_pack_ref"),
        evidence.get("strict_evidence_pack_ref"),
        evidence.get("scoring_pack_ref"),
        evidence.get("candidate_pack_ref"),
    )
    exists = evidence.get("executable_evidence_exists") is True or bool(evidence_ref)
    return {
        "executable_evidence_exists": exists,
        "executable_evidence_ref": evidence_ref,
        "reason": first_nonempty(evidence.get("reason"), evidence.get("status_code"), row.get("lane_status"), "Domain-local evidence state imported by the coverage bridge."),
    }


def domain_local_spec_rank(spec: dict[str, Any]) -> tuple[int, int, str]:
    evidence = as_dict(spec.get("current_evidence"))
    source = as_dict(spec.get("official_data_source"))
    bridge = as_dict(spec.get("domain_local_bridge"))
    evidence_missing_rank = 0 if evidence.get("executable_evidence_exists") is True else 1
    source_missing_rank = 0 if source.get("required_local_snapshot_ref") else 1
    return (
        evidence_missing_rank,
        source_missing_rank,
        str(bridge.get("source_ref", "")),
    )


def domain_local_execution(row: dict[str, Any], executable: dict[str, Any]) -> dict[str, Any]:
    split = as_dict(executable.get("target_hidden_split")) or as_dict(row.get("target_hidden_split")) or as_dict(row.get("split"))
    command_text = replay_command_text(first_nonempty(executable.get("replay_command"), row.get("replay_command"), as_dict(row.get("replay_protocol")).get("replay_command")))
    return {
        "minimum_n": int_value(first_nonempty(row.get("minimum_n"), as_dict(row.get("N")).get("minimum_n"), as_dict(executable.get("N")).get("minimum_n"))) or 20,
        "source_separation_mode": "target_blind" if split.get("target_hidden_until_scoring") is not False else "prospective",
        "target_hidden_until_scoring": split.get("target_hidden_until_scoring") is not False,
        "evidence_pack_schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
        "replay_command": command_text or "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
    }


def domain_local_closure_predicates(row: dict[str, Any], executable: dict[str, Any]) -> list[str]:
    predicates = list(EXECUTABLE_SPEC_REQUIRED_PREDICATES)
    for source in [
        as_dict(row.get("replay_protocol")).get("acceptance_predicates"),
        as_dict(executable.get("replay_command")).get("acceptance_predicates"),
    ]:
        for predicate in string_list(source):
            if predicate not in predicates:
                predicates.append(predicate)
    return predicates


def domain_local_executable_spec(row: dict[str, Any], *, source_ref: str) -> dict[str, Any] | None:
    if str(row.get("domain_class_id", "")) == "formal_mathematics_and_logic":
        return None
    executable = as_dict(row.get("executable_spec"))
    evidence = domain_local_current_evidence(row, executable)
    status = str(row.get("lane_status") or as_dict(executable.get("fail_closed_current_evidence")).get("current_status") or "OPEN_FAIL_CLOSED_DOMAIN_LOCAL_BRIDGE")
    if not status.startswith("OPEN"):
        status = f"OPEN_FAIL_CLOSED_{status}"
    spec = {
        "spec_schema_id": EXECUTABLE_SPEC_SCHEMA_ID,
        "domain_class_id": row.get("domain_class_id"),
        "phenomenon_class_id": row.get("phenomenon_class_id"),
        "coverage_closure_status": status,
        "source_plan_id": f"{row.get('work_order_id')}-domain-local-bridge",
        "official_data_source": domain_local_source(row, executable, evidence),
        "target_variable": domain_local_target(row, executable),
        "formula_requirement": domain_local_formula(row, executable),
        "incumbent_comparator_requirement": domain_local_comparator(row, executable),
        "uncertainty_requirement": domain_local_uncertainty(row, executable),
        "residual_requirement": domain_local_residual(row, executable),
        "negative_control_requirement": domain_local_negative_control(row, executable),
        "falsifier_requirement": domain_local_falsifier(row, executable),
        "execution_requirements": domain_local_execution(row, executable),
        "current_evidence": evidence,
        "closure_predicates_required": domain_local_closure_predicates(row, executable),
        "domain_local_bridge": {
            "source_ref": source_ref,
            "work_order_id": row.get("work_order_id"),
            "coverage_closure_allowed": False,
            "broad_modern_science_superiority_allowed": False,
            "artifact_exists_is_not_closure": True,
        },
    }
    return canonical_executable_spec(spec)


def load_domain_local_executable_specs(root: Path | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    root = root or repo_root()
    specs: dict[tuple[str, str], dict[str, Any]] = {}
    sources: dict[tuple[str, str], str] = {}
    errors: list[str] = []
    for path in sorted((root / DOMAIN_LOCAL_COVERAGE_ROOT_REL).glob(DOMAIN_LOCAL_COVERAGE_GLOB)):
        source_ref = path_ref(root, path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"DOMAIN_LOCAL_COVERAGE_JSON_INVALID::{source_ref}::{exc.msg}")
            continue
        for index, row in enumerate(as_list(payload.get("work_orders")), start=1):
            if not isinstance(row, dict):
                continue
            spec = domain_local_executable_spec(row, source_ref=f"{source_ref}#{index}")
            if spec is None:
                continue
            spec_errors = validate_executable_spec(spec, context=f"{source_ref}#{index}")
            if spec_errors:
                continue
            key = lane_key(spec)
            if key not in specs:
                specs[key] = spec
                sources[key] = source_ref
            elif normalized_payload(specs[key]) != normalized_payload(spec):
                current_rank = domain_local_spec_rank(specs[key])
                candidate_rank = domain_local_spec_rank(spec)
                if candidate_rank < current_rank:
                    specs[key] = spec
                    sources[key] = source_ref
    if errors:
        raise ExecutableSpecRegistryError(errors)
    return specs


def register_executable_spec(
    registry: dict[tuple[str, str], dict[str, Any]],
    sources: dict[tuple[str, str], str],
    spec: dict[str, Any],
    *,
    source_ref: str,
    errors: list[str],
) -> None:
    key = lane_key(spec)
    context = "::".join(part for part in [source_ref, key[0], key[1]] if part)
    spec_errors = validate_executable_spec(spec, context=context or source_ref)
    if spec_errors:
        errors.extend(spec_errors)
        return
    existing = registry.get(key)
    if existing is None:
        registry[key] = copy.deepcopy(spec)
        sources[key] = source_ref
        return
    if normalized_payload(existing) != normalized_payload(spec):
        errors.append(f"EXECUTABLE_SPEC_DUPLICATE_CONFLICT::{key[0]}::{key[1]}::{sources[key]}::{source_ref}")


def build_builtin_executable_spec_registry() -> dict[tuple[str, str], dict[str, Any]]:
    registry: dict[tuple[str, str], dict[str, Any]] = {}
    sources: dict[tuple[str, str], str] = {}
    errors: list[str] = []
    for key, spec in sorted(DEFAULT_EXECUTABLE_LANE_SPECS.items()):
        canonical = canonical_executable_spec(spec, domain_class_id=key[0], phenomenon_class_id=key[1])
        register_executable_spec(registry, sources, canonical, source_ref="built-in physics/chemistry executable specs", errors=errors)
    if errors:
        raise ExecutableSpecRegistryError(errors)
    return registry


def load_executable_spec_registry(root: Path | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    root = root or repo_root()
    registry = build_builtin_executable_spec_registry()
    sources = {key: "built-in physics/chemistry executable specs" for key in registry}
    errors: list[str] = []
    specs_dir = root / COVERAGE_EXECUTABLE_SPECS_REL
    if specs_dir.exists():
        for path in sorted(specs_dir.rglob("*.json")):
            source_ref = path_ref(root, path)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                specs = iter_executable_specs_from_payload(payload, source_ref=source_ref)
            except json.JSONDecodeError as exc:
                errors.append(f"EXECUTABLE_SPEC_JSON_INVALID::{source_ref}::{exc.msg}")
                continue
            except ExecutableSpecRegistryError as exc:
                errors.extend(exc.errors)
                continue
            if not specs:
                errors.append(f"EXECUTABLE_SPEC_FILE_HAS_NO_SPECS::{source_ref}")
                continue
            for index, spec in enumerate(specs, start=1):
                register_executable_spec(registry, sources, canonical_executable_spec(spec), source_ref=f"{source_ref}#{index}", errors=errors)
    try:
        domain_local_specs = load_domain_local_executable_specs(root)
    except ExecutableSpecRegistryError as exc:
        errors.extend(exc.errors)
        domain_local_specs = {}
    for key, spec in sorted(domain_local_specs.items()):
        if key in registry:
            continue
        register_executable_spec(
            registry,
            sources,
            canonical_executable_spec(spec),
            source_ref=str(spec.get("domain_local_bridge", {}).get("source_ref", "domain-local coverage bridge")),
            errors=errors,
        )
    if errors:
        raise ExecutableSpecRegistryError(errors)
    return registry


def has_executable_spec(row: dict[str, Any]) -> bool:
    return isinstance(row.get("executable_lane_spec"), dict) or isinstance(row.get("executable_work_order"), dict)


def executable_lane_spec(
    work_order: dict[str, Any],
    executable_spec_registry: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    spec = work_order.get("executable_lane_spec")
    if isinstance(spec, dict):
        return canonical_executable_spec(spec, domain_class_id=str(work_order.get("domain_class_id", "")), phenomenon_class_id=str(work_order.get("phenomenon_class_id", "")))
    if executable_spec_registry is not None:
        default = executable_spec_registry.get(lane_key(work_order))
        return copy.deepcopy(default) if isinstance(default, dict) else None
    default = DEFAULT_EXECUTABLE_LANE_SPECS.get(lane_key(work_order))
    if isinstance(default, dict):
        domain_class_id, phenomenon_class_id = lane_key(work_order)
        return canonical_executable_spec(default, domain_class_id=domain_class_id, phenomenon_class_id=phenomenon_class_id)
    return None


def executable_lane_context(row: dict[str, Any]) -> str:
    spec = row.get("executable_lane_spec") if isinstance(row.get("executable_lane_spec"), dict) else row.get("executable_work_order")
    if isinstance(spec, dict):
        return "::".join([stable_lane_id(row), str(spec.get("domain_class_id", "")), str(spec.get("phenomenon_class_id", ""))])
    return stable_lane_id(row)


def executable_data_lanes(spec: dict[str, Any]) -> list[dict[str, Any]]:
    source = spec.get("official_data_source", {})
    target = spec.get("target_variable", {})
    formula = spec.get("formula_requirement", {})
    comparator = spec.get("incumbent_comparator_requirement", {})
    uncertainty = spec.get("uncertainty_requirement", {})
    residual = spec.get("residual_requirement", {})
    negative = spec.get("negative_control_requirement", {})
    falsifier = spec.get("falsifier_requirement", {})
    return [
        {
            "lane_role": "official_data_source",
            "requirement": f"Acquire and hash {source.get('source_name')} from {source.get('official_endpoint_url')}.",
            "source_id": source.get("source_id"),
            "required_local_snapshot_ref": source.get("required_local_snapshot_ref"),
            "required_lock_ref": source.get("required_lock_ref"),
        },
        {
            "lane_role": "target_variable",
            "requirement": str(target.get("extraction_rule", "")),
            "target_name": target.get("name"),
            "target_fields": target.get("target_fields", []),
            "unit": target.get("unit"),
        },
        {
            "lane_role": "formula_or_model",
            "requirement": str(formula.get("formula_or_model", "")),
            "required_inputs": formula.get("required_inputs", []),
        },
        {
            "lane_role": "incumbent_comparator",
            "requirement": str(comparator.get("prediction_rule", "")),
            "baseline_name": comparator.get("baseline_name"),
            "pre_registered": comparator.get("pre_registered"),
        },
        {
            "lane_role": "uncertainty_policy",
            "requirement": str(uncertainty.get("rule", "")),
            "metric": uncertainty.get("metric"),
        },
        {
            "lane_role": "residual_metric",
            "requirement": str(residual.get("formula", "")),
            "metric_id": residual.get("metric_id"),
            "superiority_rule": residual.get("superiority_rule"),
        },
        {
            "lane_role": "negative_control",
            "requirement": str(negative.get("rule", "")),
            "control_id": negative.get("control_id"),
        },
        {
            "lane_role": "falsifier",
            "requirement": str(falsifier.get("trigger", "")),
            "falsifier_id": falsifier.get("falsifier_id"),
        },
    ]


def executable_proof_lanes(work_order: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    proof_lanes = [str(item) for item in work_order.get("required_proof_lanes", []) if item]
    required = [
        "executable lane spec declares exact official source, target variable, formula/model, comparator, uncertainty, residual metric, negative control, and falsifier",
        "source snapshot and target projection are locked before scoring",
        "strict evidence pack exists and validates under independent replay",
        "coverage remains open until every closure predicate is reviewed",
    ]
    for item in required:
        if item not in proof_lanes:
            proof_lanes.append(item)
    fail_closed = "fail-closed evidence gate: executable evidence is not yet bound"
    if spec.get("current_evidence", {}).get("executable_evidence_exists") is not True and fail_closed not in proof_lanes:
        proof_lanes.append(fail_closed)
    return proof_lanes


def executable_acceptance_predicates(work_order: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    predicates = [str(item) for item in work_order.get("acceptance_predicates", []) if item]
    for item in spec.get("closure_predicates_required", []):
        value = str(item)
        if value and value not in predicates:
            predicates.append(value)
    for item in ("EXECUTABLE_LANE_SPEC_DECLARED", "FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND"):
        if item not in predicates:
            predicates.append(item)
    return predicates


def coverage_gap_priority(gap: dict[str, Any], coverage_register: dict[str, Any]) -> str:
    domain_class_id = str(gap.get("domain_class_id", ""))
    domain_has_any_lane = any(
        mapping.get("domain_class_id") == domain_class_id
        for mapping in coverage_register.get("current_empirical_lane_mapping", [])
        if isinstance(mapping, dict)
    )
    priority = "P0" if not domain_has_any_lane else "P1"
    if domain_class_id in {"medical_health_sciences", "earth_space_environmental_sciences"}:
        priority = "P0"
    return priority


def build_base_work_order(index: int, gap: dict[str, Any], coverage_register: dict[str, Any]) -> dict[str, Any]:
    priority = coverage_gap_priority(gap, coverage_register)
    return {
        "work_order_id": f"MS-COV-WO-{index:03d}",
        "blocker_id": "coverage_extends_to_all_of_modern_science",
        "priority": priority,
        "domain_class_id": gap["domain_class_id"],
        "phenomenon_class_id": gap["phenomenon_class_id"],
        "title": f"Build source-backed lane for {gap['domain_label']} / {gap['phenomenon_label']}",
        "current_status": "OPEN",
        "required_data_lanes": [
            {
                "lane_role": "source_capsule",
                "requirement": "Add authoritative source capsule(s) or an internally declared formal target corpus with stable hashes.",
            },
            {
                "lane_role": "target_acquisition",
                "requirement": "Acquire target-blind or prospective targets with pre-target lock and target-hidden-until-scoring attestation.",
            },
            {
                "lane_role": "incumbent_comparator",
                "requirement": "Declare preregistered modern-science comparator baselines and score them on the same held-out targets.",
            },
            {
                "lane_role": "oc_scoring",
                "requirement": "Score OC predictions with residuals, uncertainty interval, materiality threshold, and pack hash binding.",
            },
        ],
        "required_proof_lanes": [
            "domain-scope survey explaining why the lane is representative of the phenomenon class",
            "negative controls rejected",
            "falsifiers declared and executable",
            "independent clean-checkout replay bound to coverage register and report",
        ],
        "acceptance_predicates": [
            "STRICT_PACK_SCHEMA_PASS",
            "MINIMUM_N_GE_20_OR_FORMAL_EQUIVALENT_JUSTIFIED",
            "SOURCE_SEPARATION_PASS",
            "COMPARATOR_PREREGISTERED",
            "RESIDUAL_SUPERIORITY_POSITIVE",
            "UNCERTAINTY_DECLARED",
            "NEGATIVE_CONTROLS_REJECTED",
            "FALSIFIERS_DECLARED",
            "COVERAGE_REGISTER_GAP_CLOSED",
        ],
        "must_not_unlock": [
            "broad modern-science superiority",
            "all-domain scientific closure",
        ],
    }


def enrich_work_order(
    work_order: dict[str, Any],
    executable_spec_registry: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row = copy.deepcopy(work_order)
    spec = executable_lane_spec(row, executable_spec_registry)
    if not spec:
        return row
    row["executable_lane_spec"] = spec
    row["required_data_lanes"] = executable_data_lanes(spec)
    row["required_proof_lanes"] = executable_proof_lanes(row, spec)
    row["acceptance_predicates"] = executable_acceptance_predicates(row, spec)
    row["current_status"] = spec.get("coverage_closure_status", row.get("current_status", "OPEN"))
    row["coverage_closure_policy"] = {
        "mark_closed_allowed": False,
        "reason": "Exact executable requirements are declared, but coverage stays fail-closed until official source locks, target-hidden scoring, strict pack validation, controls, falsifiers, and independent replay exist.",
    }
    return row


def build_concrete_work_orders_from_coverage_register(
    coverage_register: dict[str, Any],
    executable_spec_registry: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    executable_spec_registry = executable_spec_registry if executable_spec_registry is not None else build_builtin_executable_spec_registry()
    work_orders = [
        enrich_work_order(build_base_work_order(index, gap, coverage_register), executable_spec_registry)
        for index, gap in enumerate(coverage_register.get("coverage_gap_rows", []), start=1)
        if isinstance(gap, dict)
    ]
    return {
        "schema_id": "OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion Research/PriorArt",
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "work_order_total": len(work_orders),
        "open_work_order_total": len(work_orders),
        "priority_counts": {
            "P0": sum(1 for row in work_orders if row["priority"] == "P0"),
            "P1": sum(1 for row in work_orders if row["priority"] == "P1"),
        },
        "work_orders": work_orders,
        "executable_spec_registry_ref": COVERAGE_EXECUTABLE_SPECS_REL,
        "executable_work_order_total": sum(1 for row in work_orders if has_executable_spec(row)),
        "physics_chemistry_executable_work_order_total": sum(1 for row in work_orders if is_physics_chemistry_gap(row) and has_executable_spec(row)),
        "automation_ref": DISPATCHER_REF,
        "fail_closed_policy": (
            "Executable coverage work orders are specifications only. "
            "They cannot close coverage unless executable evidence refs, official source locks, strict scoring, controls, "
            "falsifiers, and independent replay are bound and reviewed."
        ),
    }


def build_concrete_work_orders(root: Path | None = None, coverage_register: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root or repo_root()
    coverage_register = coverage_register or load_json(root / COVERAGE_REGISTER_REL)
    return build_concrete_work_orders_from_coverage_register(coverage_register, load_executable_spec_registry(root))


def all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(all_strings(item))
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(all_strings(item))
        return out
    return []


def int_value(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate_executable_spec(spec: Any, *, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return [f"EXECUTABLE_SPEC_MISSING::{context}"]
    if spec.get("spec_schema_id") != EXECUTABLE_SPEC_SCHEMA_ID:
        errors.append(f"EXECUTABLE_SPEC_SCHEMA_MISMATCH::{context}")
    for field in EXECUTABLE_SPEC_REQUIRED_TOP_LEVEL_FIELDS:
        if not str(spec.get(field, "")):
            errors.append(f"EXECUTABLE_SPEC_TOP_LEVEL_FIELD_MISSING::{context}::{field}")
    for block in EXECUTABLE_SPEC_REQUIRED_BLOCKS:
        if not isinstance(spec.get(block), dict):
            errors.append(f"EXECUTABLE_SPEC_BLOCK_MISSING::{context}::{block}")

    source = spec.get("official_data_source", {})
    source = source if isinstance(source, dict) else {}
    if not str(source.get("source_id", "")):
        errors.append(f"OFFICIAL_SOURCE_ID_MISSING::{context}")
    if not str(source.get("source_name", "")):
        errors.append(f"OFFICIAL_SOURCE_NAME_MISSING::{context}")
    if not str(source.get("source_authority", "")):
        errors.append(f"OFFICIAL_SOURCE_AUTHORITY_MISSING::{context}")
    documentation_url = str(source.get("official_documentation_url") or "")
    if not documentation_url.startswith("https://"):
        errors.append(f"OFFICIAL_SOURCE_DOCUMENTATION_HTTPS_URL_MISSING::{context}")
    url = str(source.get("official_endpoint_url") or source.get("official_url") or "")
    if not url.startswith("https://"):
        errors.append(f"OFFICIAL_SOURCE_HTTPS_URL_MISSING::{context}")
    if not str(source.get("required_local_snapshot_ref", "")):
        errors.append(f"OFFICIAL_SOURCE_LOCAL_SNAPSHOT_REF_MISSING::{context}")
    if not str(source.get("required_lock_ref", "")):
        errors.append(f"OFFICIAL_SOURCE_LOCK_REF_MISSING::{context}")
    minimum_rows_required = int_value(source.get("minimum_rows_required"))
    if minimum_rows_required is None or minimum_rows_required < 20:
        errors.append(f"OFFICIAL_SOURCE_MINIMUM_ROWS_LT_20::{context}")

    target = spec.get("target_variable", {})
    target = target if isinstance(target, dict) else {}
    if not str(target.get("name", "")):
        errors.append(f"TARGET_VARIABLE_NAME_MISSING::{context}")
    if not target.get("target_fields"):
        errors.append(f"TARGET_FIELDS_MISSING::{context}")

    formula = spec.get("formula_requirement", {})
    formula = formula if isinstance(formula, dict) else {}
    if not str(formula.get("formula_or_model", "")):
        errors.append(f"FORMULA_OR_MODEL_MISSING::{context}")
    if formula.get("target_values_may_be_used_for_model_design") is not False:
        errors.append(f"FORMULA_TARGET_LEAK_ALLOWED::{context}")

    comparator = spec.get("incumbent_comparator_requirement", {})
    comparator = comparator if isinstance(comparator, dict) else {}
    if comparator.get("pre_registered") is not True:
        errors.append(f"COMPARATOR_NOT_PREREGISTERED::{context}")
    if comparator.get("target_values_used_for_baseline_design") is not False:
        errors.append(f"COMPARATOR_TARGET_LEAK_ALLOWED::{context}")
    if not str(comparator.get("prediction_rule", "")):
        errors.append(f"COMPARATOR_RULE_MISSING::{context}")

    for block, field in [
        ("uncertainty_requirement", "rule"),
        ("residual_requirement", "formula"),
        ("negative_control_requirement", "rule"),
        ("falsifier_requirement", "trigger"),
    ]:
        block_value = spec.get(block, {})
        block_dict = block_value if isinstance(block_value, dict) else {}
        if not str(block_dict.get(field, "")):
            errors.append(f"{block.upper()}_{field.upper()}_MISSING::{context}")

    execution = spec.get("execution_requirements", {})
    execution = execution if isinstance(execution, dict) else {}
    minimum_n = int_value(execution.get("minimum_n"))
    if minimum_n is None or minimum_n < 20:
        errors.append(f"EXECUTION_MINIMUM_N_LT_20::{context}")
    if execution.get("source_separation_mode") not in {"target_blind", "prospective"}:
        errors.append(f"EXECUTION_SOURCE_SEPARATION_MODE_INVALID::{context}")
    if execution.get("target_hidden_until_scoring") is not True:
        errors.append(f"EXECUTION_TARGET_NOT_HIDDEN_UNTIL_SCORING::{context}")
    if not str(execution.get("replay_command", "")):
        errors.append(f"EXECUTION_REPLAY_COMMAND_MISSING::{context}")

    evidence = spec.get("current_evidence", {})
    evidence = evidence if isinstance(evidence, dict) else {}
    if evidence.get("executable_evidence_exists") not in {True, False}:
        errors.append(f"EXECUTABLE_EVIDENCE_FLAG_MISSING::{context}")
    if evidence.get("executable_evidence_exists") is True and not evidence.get("executable_evidence_ref"):
        errors.append(f"EXECUTABLE_EVIDENCE_TRUE_WITHOUT_REF::{context}")
    if evidence.get("executable_evidence_exists") is not True:
        status = str(spec.get("coverage_closure_status", ""))
        if not status.startswith("OPEN_FAIL_CLOSED"):
            errors.append(f"FAIL_CLOSED_STATUS_MISSING::{context}")

    closure_predicates_value = spec.get("closure_predicates_required", [])
    closure_predicates = {str(item) for item in closure_predicates_value} if isinstance(closure_predicates_value, list) else set()
    for predicate in EXECUTABLE_SPEC_REQUIRED_PREDICATES:
        if predicate not in closure_predicates:
            errors.append(f"EXECUTABLE_CLOSURE_PREDICATE_MISSING::{context}::{predicate}")

    spec_text = "\n".join(all_strings(spec)).lower()
    for token in PLACEHOLDER_TOKENS:
        if token in spec_text:
            errors.append(f"PLACEHOLDER_TOKEN_IN_EXECUTABLE_SPEC::{context}::{token}")
    return errors


def validate_work_orders_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = [row for row in payload.get("work_orders", []) if isinstance(row, dict)]
    for row in rows:
        spec_present = isinstance(row.get("executable_lane_spec"), dict)
        if is_physics_chemistry_gap(row) and not spec_present:
            errors.append(f"PHYSICS_CHEMISTRY_EXECUTABLE_SPEC_MISSING::{stable_lane_id(row)}")
        if spec_present:
            context = executable_lane_context(row)
            errors.extend(validate_executable_spec(row.get("executable_lane_spec"), context=context))
            roles = {item.get("lane_role") for item in row.get("required_data_lanes", []) if isinstance(item, dict)}
            required_roles = {
                "official_data_source",
                "target_variable",
                "formula_or_model",
                "incumbent_comparator",
                "uncertainty_policy",
                "residual_metric",
                "negative_control",
                "falsifier",
            }
            missing = sorted(required_roles - roles)
            if missing:
                errors.append(f"EXECUTABLE_DATA_LANES_MISSING::{context}::{','.join(missing)}")
            if row.get("coverage_closure_policy", {}).get("mark_closed_allowed") is not False:
                errors.append(f"WORK_ORDER_CLOSURE_POLICY_NOT_FAIL_CLOSED::{context}")
    expected = sum(1 for row in rows if has_executable_spec(row))
    if payload.get("executable_work_order_total") not in {None, expected}:
        errors.append("EXECUTABLE_WORK_ORDER_TOTAL_MISMATCH")
    expected_physics_chemistry = sum(1 for row in rows if is_physics_chemistry_gap(row) and has_executable_spec(row))
    if payload.get("physics_chemistry_executable_work_order_total") not in {None, expected_physics_chemistry}:
        errors.append("PHYSICS_CHEMISTRY_EXECUTABLE_WORK_ORDER_TOTAL_MISMATCH")
    return errors


def no_send_sort_rank(locks: dict[str, Any]) -> int:
    required_false = [key for key in NO_SEND_LOCKS if key != "no_send"]
    return 0 if locks.get("no_send") is True and all(locks.get(key) is False for key in required_false) else 1


def stable_lane_id(work_order: dict[str, Any]) -> str:
    return "::".join(
        [
            str(work_order.get("work_order_id", "")),
            str(work_order.get("domain_class_id", "")),
            str(work_order.get("phenomenon_class_id", "")),
        ]
    )


def route_for(domain_class_id: str) -> str:
    if domain_class_id == "formal_mathematics_and_logic":
        return "FORMAL_ROUTE_PROTOCOL_ONLY"
    return "EMPIRICAL_SOURCE_BACKED_BENCHMARK"


def dependency_chain(route: str) -> list[dict[str, Any]]:
    if route == "FORMAL_ROUTE_PROTOCOL_ONLY":
        return [
            {"dependency_id": "formal_source_capsule_lock", "required_before": "formal_protocol_stub", "state": "OPEN"},
            {"dependency_id": "proof_corpus_hash_binding", "required_before": "formal_acceptance_review", "state": "OPEN"},
            {"dependency_id": "scope_text_blocks_empirical_superiority", "required_before": "coverage_review", "state": "OPEN"},
        ]
    return [
        {"dependency_id": "source_capsule_lock", "required_before": "target_acquisition", "state": "OPEN"},
        {"dependency_id": "target_blind_or_prospective_lock", "required_before": "incumbent_comparator", "state": "OPEN"},
        {"dependency_id": "incumbent_comparator_preregistration", "required_before": "oc_scoring", "state": "OPEN"},
        {"dependency_id": "oc_scoring_with_uncertainty", "required_before": "proof_lane_review", "state": "OPEN"},
        {"dependency_id": "controls_falsifiers_replay", "required_before": "coverage_review", "state": "OPEN"},
    ]


def dependency_key(route: str) -> str:
    return dependency_chain(route)[0]["dependency_id"]


def required_data_lanes(work_order: dict[str, Any], route: str) -> list[dict[str, Any]]:
    if route == "FORMAL_ROUTE_PROTOCOL_ONLY":
        return [
            {
                "lane_role": "formal_source_capsule",
                "requirement": "Bind a proof-system or formal-corpus source capsule with stable artifact hashes.",
            },
            {
                "lane_role": "formal_protocol_stub",
                "requirement": "Declare theorem/proof reconstruction obligations without empirical target acquisition or prediction support.",
            },
            {
                "lane_role": "scope_boundary",
                "requirement": "Assert protocol-only handling and block theorem-prover/formal-mathematics superiority wording.",
            },
        ]
    return list(work_order.get("required_data_lanes", []))


def required_proof_lanes(work_order: dict[str, Any], route: str) -> list[str]:
    proof_lanes = [str(item) for item in work_order.get("required_proof_lanes", []) if item]
    if route == "FORMAL_ROUTE_PROTOCOL_ONLY":
        return [
            "formal route review showing why no empirical protocol is being asserted",
            "proof-corpus hash binding and replay command declared",
            "scope text blocks empirical, theorem-prover, and broad modern-science superiority claims",
            "coverage register remains open until a reviewed formal-equivalent closure predicate exists",
        ]
    return proof_lanes


def acceptance_predicates(work_order: dict[str, Any], route: str) -> list[str]:
    predicates = [str(item) for item in work_order.get("acceptance_predicates", []) if item]
    if route == "FORMAL_ROUTE_PROTOCOL_ONLY":
        predicates = [
            "FORMAL_ROUTE_PROTOCOL_ONLY_DECLARED",
            "FORMAL_SOURCE_CAPSULE_HASH_BOUND",
            "PROOF_CORPUS_HASH_BOUND",
            "NO_EMPIRICAL_PROTOCOL_OR_PREDICTION_SUPPORT_ASSERTED",
            "CLAIM_TEXT_EXCLUDES_THEOREM_PROVER_OR_FORMAL_MATH_SUPERIORITY",
            "COVERAGE_REGISTER_GAP_REMAINS_OPEN_UNTIL_REVIEW",
        ]
    return predicates + ["NO_BROAD_SUPERIORITY_CERTIFICATION"]


def resource_estimate(priority: str, route: str) -> dict[str, Any]:
    if route == "FORMAL_ROUTE_PROTOCOL_ONLY":
        return {
            "planning_points": 5,
            "minimum_evidence_pack_n": "formal-equivalent review only; no empirical n asserted",
            "expected_worker_roles": ["formal methods owner", "protocol reviewer", "release-scope reviewer"],
        }
    return {
        "planning_points": 8 if priority == "P0" else 5,
        "minimum_evidence_pack_n": 20,
        "expected_worker_roles": ["source acquisition owner", "comparator owner", "scoring owner", "replay reviewer"],
    }


def build_dispatch_row(index: int, work_order: dict[str, Any], gap_by_key: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    domain_class_id = str(work_order.get("domain_class_id", ""))
    phenomenon_class_id = str(work_order.get("phenomenon_class_id", ""))
    route = route_for(domain_class_id)
    stable_id = stable_lane_id(work_order)
    priority = str(work_order.get("priority", "P2"))
    gap = gap_by_key.get((domain_class_id, phenomenon_class_id), {})
    verification_command = "python benchmarks/modern_science/coverage_lane_dispatcher.py --check"
    spec = executable_lane_spec(work_order)
    evidence = spec.get("current_evidence", {}) if isinstance(spec, dict) else {}
    executable_evidence_exists = evidence.get("executable_evidence_exists") is True and bool(evidence.get("executable_evidence_ref"))
    current_status = str(work_order.get("current_status", "OPEN"))
    if spec and not executable_evidence_exists:
        current_status = str(spec.get("coverage_closure_status", "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE"))
    execution_state = (
        "FAIL_CLOSED_EXECUTABLE_SPEC_READY_EVIDENCE_MISSING"
        if spec and not executable_evidence_exists
        else "READY_TO_PLAN_NOT_STARTED"
    )
    return {
        "queue_rank": index,
        "dispatch_id": f"MS-COV-DISPATCH-{index:03d}",
        "stable_id": stable_id,
        "work_order_id": work_order.get("work_order_id"),
        "coverage_gap_id": gap.get("gap_id"),
        "blocker_id": work_order.get("blocker_id", "coverage_extends_to_all_of_modern_science"),
        "priority": priority,
        "domain_class_id": domain_class_id,
        "phenomenon_class_id": phenomenon_class_id,
        "phenomenon_label": gap.get("phenomenon_label"),
        "lane_route": route,
        "owner_capability": OWNER_CAPABILITIES.get(domain_class_id, "Logion Coverage Evidence Planning"),
        "execution_state": execution_state,
        "dependency_key": dependency_key(route),
        "dependencies": dependency_chain(route),
        "required_data_lanes": required_data_lanes(work_order, route),
        "required_proof_lanes": required_proof_lanes(work_order, route),
        "official_source_defaults": OFFICIAL_SOURCE_DEFAULTS.get(domain_class_id, []),
        "expected_acceptance_predicates": acceptance_predicates(work_order, route),
        "executable_work_order": spec,
        "evidence_gate": {
            "executable_evidence_exists": executable_evidence_exists,
            "executable_evidence_ref": evidence.get("executable_evidence_ref"),
            "closure_allowed": False,
            "status": "EVIDENCE_BOUND_PENDING_REVIEW" if executable_evidence_exists else "FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        },
        "verification_command": verification_command,
        "resource_estimate": resource_estimate(priority, route),
        "no_send_locks": dict(NO_SEND_LOCKS),
        "coverage_closure": {
            "current_status": current_status,
            "mark_closed_allowed": False,
            "reason": (
                evidence.get("reason")
                if spec and not executable_evidence_exists
                else "Dispatcher emits executable plans only; evidence and reviewed closure predicates are still absent."
            ),
        },
    }


def sorted_work_orders(work_orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        work_orders,
        key=lambda row: (
            no_send_sort_rank(NO_SEND_LOCKS),
            PRIORITY_RANK.get(str(row.get("priority", "P2")), 99),
            str(row.get("domain_class_id", "")),
            str(row.get("phenomenon_class_id", "")),
            dependency_key(route_for(str(row.get("domain_class_id", "")))),
            stable_lane_id(row),
        ),
    )


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_queue(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    work_orders_payload = build_concrete_work_orders(root)
    coverage_register = load_json(root / COVERAGE_REGISTER_REL)
    gap_by_key = {
        (str(row.get("domain_class_id")), str(row.get("phenomenon_class_id"))): row
        for row in coverage_register.get("coverage_gap_rows", [])
        if isinstance(row, dict)
    }
    rows = [
        build_dispatch_row(index, work_order, gap_by_key)
        for index, work_order in enumerate(sorted_work_orders(work_orders_payload.get("work_orders", [])), start=1)
        if isinstance(work_order, dict)
    ]
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion IT/Planning Worker AE",
        "dispatcher_ref": DISPATCHER_REF,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "coverage_work_orders_ref": WORK_ORDERS_REL,
        "executable_spec_registry_ref": COVERAGE_EXECUTABLE_SPECS_REL,
        "queue_policy": "Sort by no-send safety lock, priority, domain class, phenomenon class, dependency, then stable id.",
        "queue_size": len(rows),
        "open_lane_total": sum(1 for row in rows if str(row.get("coverage_closure", {}).get("current_status", "")).startswith("OPEN")),
        "no_send_locked_lane_total": sum(1 for row in rows if no_send_sort_rank(row.get("no_send_locks", {})) == 0),
        "executable_lane_total": sum(1 for row in rows if isinstance(row.get("executable_work_order"), dict)),
        "physics_chemistry_executable_lane_total": sum(1 for row in rows if is_physics_chemistry_gap(row) and isinstance(row.get("executable_work_order"), dict)),
        "priority_counts": count_by(rows, "priority"),
        "route_counts": count_by(rows, "lane_route"),
        "lanes": rows,
        "certification_policy": {
            "mark_coverage_closed": False,
            "broad_modern_science_superiority_certified": False,
            "release_promotion_allowed": False,
        },
    }


def build_telemetry(queue: dict[str, Any]) -> dict[str, Any]:
    lanes = queue.get("lanes", [])
    top = [
        {
            "queue_rank": row.get("queue_rank"),
            "stable_id": row.get("stable_id"),
            "priority": row.get("priority"),
            "lane_route": row.get("lane_route"),
            "owner_capability": row.get("owner_capability"),
        }
        for row in lanes[:5]
    ]
    return {
        "schema_id": TELEMETRY_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": "Logion IT/Planning Worker AE",
        "queue_ref": QUEUE_REPORT_REL,
        "queue_size": queue.get("queue_size", 0),
        "open_lane_total": queue.get("open_lane_total", 0),
        "executable_lane_total": queue.get("executable_lane_total", 0),
        "physics_chemistry_executable_lane_total": queue.get("physics_chemistry_executable_lane_total", 0),
        "top_planned_lanes": top,
        "priority_counts": queue.get("priority_counts", {}),
        "route_counts": queue.get("route_counts", {}),
        "no_send_locks": dict(NO_SEND_LOCKS),
        "coverage_gaps_remain": int(queue.get("open_lane_total", 0) or 0) > 0,
        "broad_modern_science_superiority_certified": False,
        "release_promotion_allowed": False,
        "blockers": [
            f"{queue.get('open_lane_total', 0)} coverage gaps remain open until source-backed reviewed lanes are built.",
            f"{queue.get('executable_lane_total', 0)} coverage gaps have executable specs but remain fail-closed until executable evidence exists.",
            f"{queue.get('physics_chemistry_executable_lane_total', 0)} physics/chemistry coverage gaps have executable specs but remain fail-closed until evidence exists.",
            "The dispatcher provides executable planning rows only and does not close evidence predicates.",
            "Public release, publication, registry write, journal submission, email, and broad superiority paths remain locked.",
        ],
        "verification_commands": [
            "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
            "python tools/oc133_modern_science_comparator_factory.py --check",
            "python tools/oc133_modern_science_benchmark_protocol_planner.py --check",
        ],
    }


def render_cockpit(queue: dict[str, Any], telemetry: dict[str, Any]) -> str:
    lines = [
        "# OC133 Modern Science Coverage Lane Cockpit",
        "",
        f"Queue size: `{queue.get('queue_size')}`",
        f"Open lanes: `{queue.get('open_lane_total')}`",
        "Broad modern-science superiority certified: `false`",
        "Release promotion allowed: `false`",
        "",
        "Top planned lanes:",
        "",
    ]
    for lane in telemetry.get("top_planned_lanes", []):
        lines.append(
            "- `#{rank}` `{stable}` `{priority}` `{route}`".format(
                rank=lane.get("queue_rank"),
                stable=lane.get("stable_id"),
                priority=lane.get("priority"),
                route=lane.get("lane_route"),
            )
        )
    lines.extend(["", "Verification:", ""])
    for command in telemetry.get("verification_commands", []):
        lines.append(f"- `{command}`")
    lines.append("")
    return "\n".join(lines)


def build_all(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    queue = build_queue(root)
    telemetry = build_telemetry(queue)
    return {
        QUEUE_REPORT_REL: queue,
        TELEMETRY_REPORT_REL: telemetry,
        COCKPIT_REL: {"text": render_cockpit(queue, telemetry)},
    }


def validate_queue(queue: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    lanes = queue.get("lanes", [])
    if queue.get("queue_size") != len(lanes):
        errors.append("QUEUE_SIZE_MISMATCH")
    if queue.get("open_lane_total") != len(lanes):
        errors.append("OPEN_LANE_TOTAL_MISMATCH")
    executable_lane_total = sum(1 for row in lanes if isinstance(row.get("executable_work_order"), dict))
    if queue.get("executable_lane_total") not in {None, executable_lane_total}:
        errors.append("EXECUTABLE_LANE_TOTAL_MISMATCH")
    physics_chemistry_executable_lane_total = sum(
        1 for row in lanes if is_physics_chemistry_gap(row) and isinstance(row.get("executable_work_order"), dict)
    )
    if queue.get("physics_chemistry_executable_lane_total") != physics_chemistry_executable_lane_total:
        errors.append("PHYSICS_CHEMISTRY_EXECUTABLE_LANE_TOTAL_MISMATCH")
    sorted_ids = [stable_lane_id(row) for row in sorted_work_orders(lanes)]
    actual_ids = [str(row.get("stable_id")) for row in lanes]
    if actual_ids != sorted_ids:
        errors.append("QUEUE_ORDER_NOT_DETERMINISTIC")
    for row in lanes:
        locks = row.get("no_send_locks", {})
        if no_send_sort_rank(locks) != 0:
            errors.append(f"NO_SEND_LOCK_OPEN::{row.get('stable_id')}")
        closure = row.get("coverage_closure", {})
        if closure.get("mark_closed_allowed") is not False:
            errors.append(f"COVERAGE_CLOSURE_ENABLED::{row.get('stable_id')}")
        if row.get("lane_route") == "FORMAL_ROUTE_PROTOCOL_ONLY":
            if any(item.get("lane_role") == "target_acquisition" for item in row.get("required_data_lanes", [])):
                errors.append(f"FORMAL_ROUTE_HAS_EMPIRICAL_TARGET_ACQUISITION::{row.get('stable_id')}")
            if "NO_EMPIRICAL_PROTOCOL_OR_PREDICTION_SUPPORT_ASSERTED" not in row.get("expected_acceptance_predicates", []):
                errors.append(f"FORMAL_ROUTE_MISSING_NO_EMPIRICAL_PREDICATE::{row.get('stable_id')}")
        spec_present = isinstance(row.get("executable_work_order"), dict)
        if is_physics_chemistry_gap(row) and not spec_present:
            errors.append(f"PHYSICS_CHEMISTRY_EXECUTABLE_SPEC_MISSING::{row.get('stable_id')}")
        if spec_present:
            context = executable_lane_context(row)
            errors.extend(validate_executable_spec(row.get("executable_work_order"), context=context))
            evidence_gate = row.get("evidence_gate", {})
            if evidence_gate.get("closure_allowed") is not False:
                errors.append(f"EXECUTABLE_EVIDENCE_GATE_ALLOWS_CLOSURE::{context}")
            if evidence_gate.get("executable_evidence_exists") is not True:
                status = str(row.get("coverage_closure", {}).get("current_status", ""))
                if not status.startswith("OPEN_FAIL_CLOSED"):
                    errors.append(f"EXECUTABLE_GAP_NOT_FAIL_CLOSED::{context}")
            expected_predicates = set(str(item) for item in row.get("expected_acceptance_predicates", []))
            for predicate in ("EXECUTABLE_LANE_SPEC_DECLARED", "FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND"):
                if predicate not in expected_predicates:
                    errors.append(f"EXECUTABLE_ACCEPTANCE_PREDICATE_MISSING::{context}::{predicate}")
    policy = queue.get("certification_policy", {})
    if policy.get("broad_modern_science_superiority_certified") is not False:
        errors.append("BROAD_SUPERIORITY_CERTIFIED_IN_QUEUE")
    if policy.get("release_promotion_allowed") is not False:
        errors.append("RELEASE_PROMOTION_ALLOWED_IN_QUEUE")
    return errors


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []
    stored_work_orders = load_json(root / WORK_ORDERS_REL)
    expected_work_orders = build_concrete_work_orders(root)
    if stored_work_orders != expected_work_orders:
        errors.append(f"{WORK_ORDERS_REL} is not synchronized with {DISPATCHER_REF}")
    errors.extend(validate_work_orders_payload(stored_work_orders))
    queue = build_queue(root)
    errors.extend(validate_queue(queue))
    return errors


def check_output_artifacts(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    errors: list[str] = []
    for rel, payload in expected.items():
        path = root / rel
        if rel.endswith(".md"):
            actual_text = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual_text != payload["text"]:
                errors.append(f"{rel} is not synchronized with {DISPATCHER_REF}")
        else:
            actual = load_json(path)
            if actual != payload:
                errors.append(f"{rel} is not synchronized with {DISPATCHER_REF}")
    errors.extend(validate_queue(expected[QUEUE_REPORT_REL]))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check modern-science coverage lane dispatch queue.")
    parser.add_argument("--write", action="store_true", help="Write queue, telemetry, and cockpit artifacts.")
    parser.add_argument("--write-work-orders", action="store_true", help="Write concrete executable coverage work orders only.")
    parser.add_argument("--check", action="store_true", help="Check concrete work orders and queue fail-closed predicates.")
    parser.add_argument("--check-output-artifacts", action="store_true", help="Check queue, telemetry, and cockpit output artifacts are synchronized.")
    args = parser.parse_args(argv)

    root = repo_root()
    try:
        if args.write_work_orders:
            write_json(root / WORK_ORDERS_REL, build_concrete_work_orders(root))
            print("modern-science coverage work orders materialized; executable lanes remain fail-closed")
            return 0

        if args.write:
            write_json(root / WORK_ORDERS_REL, build_concrete_work_orders(root))
            for rel, payload in build_all(root).items():
                path = root / rel
                if rel.endswith(".md"):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(payload["text"], encoding="utf-8", newline="\n")
                else:
                    write_json(path, payload)
            print("modern-science coverage lane queue materialized; all no-send locks remain closed")
            return 0

        errors = check_output_artifacts(root) if args.check_output_artifacts else check_stored(root)
    except ExecutableSpecRegistryError as exc:
        errors = exc.errors
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern-science coverage lane dispatcher check passed; coverage remains open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
