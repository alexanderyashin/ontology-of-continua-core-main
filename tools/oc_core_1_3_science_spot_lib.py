from __future__ import annotations

import json
import re
import shutil
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EDITORIAL_DIR = REPO_ROOT / "releases" / "oc_core_1_3" / "editorial"
MONOGRAPH_SOURCE_DIR = REPO_ROOT / "releases" / "oc_core_1_3" / "monograph" / "source"
ROOT_CONTENT_GENERATED_DIR = REPO_ROOT / "content" / "generated"
ROOT_APPENDIX_GENERATED_DIR = REPO_ROOT / "appendix" / "generated"
ROOT_TOE_DIR = REPO_ROOT / "content" / "toe"
SOURCE_CONTENT_GENERATED_DIR = MONOGRAPH_SOURCE_DIR / "content" / "generated"
SOURCE_APPENDIX_GENERATED_DIR = MONOGRAPH_SOURCE_DIR / "appendix" / "generated"
SOURCE_TOE_DIR = MONOGRAPH_SOURCE_DIR / "content" / "toe"
SCIENCE_SOURCE_DIR = EDITORIAL_DIR / "science_sources"
SCIENCE_SOURCE_CLOSURE_BUNDLE_DIR = SCIENCE_SOURCE_DIR / "closure_bundles"
SCIENCE_SOURCE_HOSTILE_REVIEW_DIR = SCIENCE_SOURCE_DIR / "hostile_review"
SCIENCE_SOURCE_K_LEVEL_DIR = SCIENCE_SOURCE_DIR / "k_levels"
SCIENCE_SOURCE_PRACTICAL_UTILITY_DIR = SCIENCE_SOURCE_DIR / "practical_utility"
SCIENCE_SOURCE_SERIOUS_MODEL_COMPARISON_FILE = SCIENCE_SOURCE_PRACTICAL_UTILITY_DIR / "serious_model_comparison_catalog.json"
DOSSIER_PACKAGE_DIR = EDITORIAL_DIR / "dossier_packages"
CLOSURE_BUNDLE_DOSSIER_DIR = DOSSIER_PACKAGE_DIR / "closure_bundles"
HOSTILE_REVIEW_DOSSIER_DIR = DOSSIER_PACKAGE_DIR / "hostile_review"
PHASE1_DOSSIER_DIR = DOSSIER_PACKAGE_DIR / "phase1_closed_core"
LEGACY_DOMAIN_PACKET_DIR = EDITORIAL_DIR / "domain_packets"

ALLOWED_SCIENTIFIC_CLASSES = [
    "THEOREM_NATIVE",
    "BRIDGE_ONLY",
    "FRAME_ONLY",
    "EXTENSION",
    "REFUTED",
]
ALLOWED_CLOSURE_VERDICTS = ["PASS", "FAIL_CLOSED"]
ALLOWED_GAP_TYPES = [
    "missing theorem",
    "missing observable definition",
    "missing parameter law",
    "missing held-out test",
    "missing falsifier",
    "surface contradiction",
]

CORE_DOMAIN_IDS = [
    "MATHEMATICS",
    "PHYSICS",
    "CHEMISTRY",
    "BIOLOGY",
    "SYSTEMS_CIVILIZATIONAL_PROJECTION",
]
SPOT_DOMAIN_ORDER = CORE_DOMAIN_IDS + ["DRT", "METAONTOLOGY"]
TOE_LEVEL_IDS = [f"K{index}" for index in range(13)]
TOE_SUPPORT_REQUIRED_HEADINGS = [
    r"\paragraph{Theorem claim.}",
    r"\paragraph{Operator and K-level binding.}",
    r"\paragraph{Parameter law.}",
    r"\paragraph{Observable binding and units.}",
    r"\paragraph{Numerical instantiation and prediction table.}",
    r"\paragraph{Falsifier and collapse boundary.}",
    r"\paragraph{Closed-domain bindings.}",
]

PRACTICAL_SUPPORT_CLASS_ORDER = [
    "FORMALLY_PROVED",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
    "FRONTIER_PROGRAM",
    "HYPOTHESIS_ONLY",
]
USABLE_NOW_SUPPORT_CLASSES = {
    "FORMALLY_PROVED",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
}
PRACTICAL_SUPPORT_CLASS_LABELS = {
    "FORMALLY_PROVED": "formally proved",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED": "theorem-native + empirical / held-out validated",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS": "operationally supported within bounds",
    "FRONTIER_PROGRAM": "frontier program",
    "HYPOTHESIS_ONLY": "hypothesis only",
}
SERIOUS_MODEL_RELATIONSHIP_VALUES = [
    "complements",
    "integrates",
    "subsumes_in_scope",
    "still_superior_in_lane",
    "open",
]
PRACTICAL_USE_REQUIRED_FIELDS = [
    "use_case_id",
    "problem_class",
    "support_class",
    "what_can_be_predicted_or_done",
    "how_to_apply",
    "scope_boundary",
    "required_inputs_or_observables",
    "output_or_decision",
    "trace_refs",
    "benchmark_comparators",
    "serious_model_families",
    "what_remains_open",
]
PRACTICAL_PLAYBOOK_REQUIRED_FIELDS = [
    "playbook_id",
    "title",
    "when_to_use",
    "required_inputs_or_observables",
    "procedure_steps",
    "output_or_decision",
    "support_class",
    "scope_boundary",
    "trace_refs",
    "failure_boundary",
]
SERIOUS_MODEL_COMPARISON_REQUIRED_FIELDS = [
    "comparison_id",
    "domain_id",
    "serious_model_family",
    "problem_class",
    "what_it_already_explains_or_predicts",
    "where_fragmentation_or_limit_remains",
    "what_oc_adds_or_unifies",
    "relationship_to_oc",
    "scope_boundary",
    "practical_takeaway",
    "source_refs",
]

TOE_LEVEL_SPECS = {
    "K0": {
        "title": "Structural Conditions for Any Universe",
        "toe_file_ref": "content/toe/toe_k0",
        "appendix_table_label": "tab:k0-structural-parameters",
        "theorem_native_claim": "K0 fixes the non-empty admissible meta-domain required for any lawful continuum and therefore bounds every later K-level before empirical specialization.",
        "operator_binding_summary": "The local K0 root process glyphs Psi_0, Phi_0, and Lambda_0 fix distinction generation, relational reconfiguration, and compositional assembly; compact synthesis aliases F_0, Q_0, and U_0 label the corresponding root constraints only where they are defined locally.",
        "parameter_law_display": r"\mu(\Omega(K_0)) > 0,\quad \forall x \in \{1,\dots,12\}: \mathrm{DoF}(M_x)>0\ \mathrm{and}\ \frac{\mathrm{DoF}(K_x)}{\mathrm{DoF}(M_x)} \leq 1,\quad C_{\mathrm{triv}} \geq 1",
        "observable_map_summary": "Meta-admissibility, meta-space compatibility, and the presence of at least one trivial lawful cycle.",
        "synthetic_observable_ids": [
            "K0::ADMISSIBLE_STATE_MEASURE",
            "K0::META_SPACE_COMPATIBILITY_RATIO",
            "K0::NONTRIVIAL_CYCLE_PRESENCE",
        ],
        "numerical_rows": [
            {
                "quantity": "Admissible-state measure floor",
                "symbol_tex": r"\mu(\Omega(K_0))",
                "value_tex": r"> 0",
                "units_note": "dimensionless lower bound",
            },
            {
                "quantity": "Meta-space compatibility ratio for each promoted level",
                "symbol_tex": r"\mathrm{DoF}(K_x)/\mathrm{DoF}(M_x)",
                "value_tex": r"\leq 1",
                "units_note": "dimensionless ratio; applies for each promoted level",
            },
            {
                "quantity": "Trivial cycle presence",
                "symbol_tex": r"C_{\mathrm{triv}}",
                "value_tex": r"1",
                "units_note": "present",
            },
        ],
        "collapse_boundary": "Collapse occurs if the admissible set degenerates, if a later K-level exceeds its meta-space, or if the structural substrate loses its last trivial lawful cycle.",
    },
    "K1": {
        "title": "Minimal Observable Distinctions and Energetic Axes",
        "toe_file_ref": "content/toe/toe_k1",
        "appendix_table_label": "tab:k1-minimal-observable-parameters",
        "theorem_native_claim": "K1 introduces resolvable energetic and temporal distinctions while preserving the admissible-state floor inherited from K0.",
        "operator_binding_summary": "F, G, and U bind contradiction load to resolvable energetic distinctions, monotonic update order, and a non-degenerate observable region.",
        "parameter_law_display": r"\Delta E \geq \Theta_{\Delta E},\quad \frac{dt}{d\tau} > 0,\quad \mu(\Omega(K_1)) > 0",
        "observable_map_summary": "Energy-gap resolution, monotonic update ordering, and positive configuration-space measure in the first observable regime.",
        "synthetic_observable_ids": [
            "K1::ENERGY_GAP_THRESHOLD",
            "K1::TEMPORAL_MONOTONICITY",
            "K1::CONFIGURATION_MEASURE",
        ],
        "numerical_rows": [
            {
                "quantity": "Minimal resolvable energy scale",
                "symbol_tex": r"\Theta_{\Delta E}",
                "value_tex": r"10^{-34}\text{--}10^{-33}",
                "units_note": r"\mathrm{J}",
            },
            {
                "quantity": "Temporal monotonicity",
                "symbol_tex": r"dt/d\tau",
                "value_tex": r"> 0",
                "units_note": "ordered update constraint",
            },
            {
                "quantity": "Configuration-space measure floor",
                "symbol_tex": r"\mu(\Omega(K_1))",
                "value_tex": r"> 0",
                "units_note": "dimensionless lower bound",
            },
        ],
        "collapse_boundary": "Collapse begins when energetic distinctions are no longer resolvable, temporal order breaks, or the first observable state space degenerates.",
    },
    "K2": {
        "title": "Fields, Phases, and Large-Scale Structure",
        "toe_file_ref": "content/toe/toe_k2",
        "appendix_table_label": "tab:k2-cosmological-parameters",
        "theorem_native_claim": "K2 binds field configurations, expansion history, and phase thresholds into the first large-scale physical continuum admissible under the kernel operators.",
        "operator_binding_summary": "F, H, and R constrain field admissibility, phase transitions, and large-scale stabilization margins inside the physical continuum.",
        "parameter_law_display": r"H_0 > 0,\quad 0 < \Omega_{\mathrm{m}} < 1,\quad |\Omega_k| < 2 \times 10^{-3},\quad \mathcal{T}_{\mathrm{phase}}(t) \in \{T_c^{\mathrm{EW}}, T_c^{\mathrm{QCD}}\}",
        "observable_map_summary": "Expansion rate, curvature, cosmological density fractions, and critical phase windows tied to physical observables and replay packets.",
        "synthetic_observable_ids": [
            "K2::EXPANSION_RATE",
            "K2::CURVATURE_BOUND",
            "K2::PHASE_TRANSITION_WINDOW",
        ],
        "numerical_rows": [
            {
                "quantity": "Hubble parameter today",
                "symbol_tex": r"H_0",
                "value_tex": r"67.4 \pm 0.5",
                "units_note": r"\mathrm{km\,s^{-1}\,Mpc^{-1}}",
            },
            {
                "quantity": "Matter density fraction",
                "symbol_tex": r"\Omega_{\mathrm{m}}",
                "value_tex": r"0.315 \pm 0.007",
                "units_note": "dimensionless",
            },
            {
                "quantity": "Critical phase windows",
                "symbol_tex": r"T_c^{\mathrm{EW}},\ T_c^{\mathrm{QCD}}",
                "value_tex": r"\sim 100\ \mathrm{GeV};\ 150\text{--}170\ \mathrm{MeV}",
                "units_note": "closed phase set",
            },
            {
                "quantity": "Curvature bound",
                "symbol_tex": r"\Omega_k",
                "value_tex": r"|\Omega_k| < 2 \times 10^{-3}",
                "units_note": "dimensionless",
            },
        ],
        "collapse_boundary": "K2 collapses when curvature exits the admissible band, phase windows fail to close lawfully, or large-scale physical observables lose replayable stabilization.",
    },
    "K3": {
        "title": "Molecular Organization and Chemical Bonding",
        "toe_file_ref": "content/toe/toe_k3",
        "appendix_table_label": "tab:k3-molecular-parameters",
        "theorem_native_claim": "K3 packages bounded molecular organization through lawful bond-length, bond-energy, and activation-energy envelopes derived from lower-level admissibility.",
        "operator_binding_summary": "G, H, and R bind composition-sensitive bonding, activation barriers, and molecular-scale stabilization windows.",
        "parameter_law_display": r"r_{\mathrm{cov}} \in [0.1, 0.2]\,\mathrm{nm},\quad E_{\mathrm{bond}} \in [1, 5]\,\mathrm{eV},\quad E^\ddagger \in [0.1, 1]\,\mathrm{eV}",
        "observable_map_summary": "Bond lengths, dissociation energies, dielectric context, and activation barriers for bounded chemistry lanes.",
        "synthetic_observable_ids": [
            "K3::BOND_LENGTH",
            "K3::BOND_ENERGY",
            "K3::ACTIVATION_ENERGY",
        ],
        "numerical_rows": [
            {
                "quantity": "Bond length (covalent)",
                "symbol_tex": r"r_{\mathrm{cov}}",
                "value_tex": r"0.1\text{--}0.2",
                "units_note": r"\mathrm{nm}",
            },
            {
                "quantity": "Bond dissociation energy",
                "symbol_tex": r"E_{\mathrm{bond}}",
                "value_tex": r"1\text{--}5",
                "units_note": r"\mathrm{eV}",
            },
            {
                "quantity": "Reaction activation energy",
                "symbol_tex": r"E^\ddagger",
                "value_tex": r"0.1\text{--}1",
                "units_note": r"\mathrm{eV}",
            },
        ],
        "collapse_boundary": "K3 collapses when bond- and barrier-level regularities cannot be bounded by a non-degenerate parameter law or when chemical observables drift outside admissible molecular windows.",
    },
    "K4": {
        "title": "Compartmental and Membrane Thresholds",
        "toe_file_ref": "content/toe/toe_k4",
        "appendix_table_label": "tab:k4-membrane-parameters",
        "theorem_native_claim": "K4 closes the first compartmental organization packet by binding membrane thickness, bending stability, and gradient maintenance to lawful biological thresholds.",
        "operator_binding_summary": "H, R, and S couple membrane stability, osmotic admissibility, and retained gradients into a bounded protocellular regime.",
        "parameter_law_display": r"d_{\mathrm{mem}} \in [3, 5]\,\mathrm{nm},\quad \kappa \in [10, 25]\,k_{\mathrm{B}}T,\quad \Delta pH \in [0.5, 2]",
        "observable_map_summary": "Membrane thickness, bending modulus, osmotic pressure, proton gradient, and permeability lanes for compartmental organization.",
        "synthetic_observable_ids": [
            "K4::MEMBRANE_THICKNESS",
            "K4::BENDING_MODULUS",
            "K4::PROTON_GRADIENT",
        ],
        "numerical_rows": [
            {
                "quantity": "Membrane thickness",
                "symbol_tex": r"d_{\mathrm{mem}}",
                "value_tex": r"3\text{--}5",
                "units_note": r"\mathrm{nm}",
            },
            {
                "quantity": "Membrane bending modulus",
                "symbol_tex": r"\kappa",
                "value_tex": r"10\text{--}25",
                "units_note": r"k_{\mathrm{B}}T",
            },
            {
                "quantity": "Typical proton gradient",
                "symbol_tex": r"\Delta pH",
                "value_tex": r"0.5\text{--}2",
                "units_note": "pH units",
            },
        ],
        "collapse_boundary": "K4 collapses if compartments cannot retain a lawful gradient, if membranes lose structural stability, or if permeability escapes the admissible packet.",
    },
    "K5": {
        "title": "Excitable and Early Neural Continua",
        "toe_file_ref": "content/toe/toe_k5",
        "appendix_table_label": "tab:k5-excitable-parameters",
        "theorem_native_claim": "K5 binds excitability, refractory timing, and membrane potential maintenance into the first lawful neural packet.",
        "operator_binding_summary": "F, G, and S stabilize excitable-state transitions, ion-channel gating, and refractory boundaries in bounded neural lanes.",
        "parameter_law_display": r"C_m = 1\,\mu\mathrm{F/cm^2},\quad V_{\mathrm{rest}} \in [-75,-60]\,\mathrm{mV},\quad \tau_{\mathrm{ref}} \in [2,5]\,\mathrm{ms}",
        "observable_map_summary": "Membrane capacitance, resting potential, channel conductance, and refractory timing for bounded excitable systems.",
        "synthetic_observable_ids": [
            "K5::MEMBRANE_CAPACITANCE",
            "K5::RESTING_POTENTIAL",
            "K5::REFRACTORY_TIME",
        ],
        "numerical_rows": [
            {
                "quantity": "Membrane capacitance",
                "symbol_tex": r"C_m",
                "value_tex": r"1",
                "units_note": r"\mu\mathrm{F/cm^2}",
            },
            {
                "quantity": "Resting membrane potential",
                "symbol_tex": r"V_{\mathrm{rest}}",
                "value_tex": r"-75\text{--}-60",
                "units_note": r"\mathrm{mV}",
            },
            {
                "quantity": "Refractory time",
                "symbol_tex": r"\tau_{\mathrm{ref}}",
                "value_tex": r"2\text{--}5",
                "units_note": r"\mathrm{ms}",
            },
        ],
        "collapse_boundary": "K5 collapses when excitability loses bounded thresholds, refractory timing fails, or the neural packet cannot survive counterexample pressure across datasets.",
    },
    "K6": {
        "title": "Cognitive Prediction and Representation",
        "toe_file_ref": "content/toe/toe_k6",
        "appendix_table_label": "tab:k6-cognitive-parameters",
        "theorem_native_claim": "K6 formalizes bounded cognitive prediction and representation by linking prediction-error thresholds, working-memory span, and adaptation strength.",
        "operator_binding_summary": "Q, R, and S bind representation stability, prediction thresholds, and adaptive update constraints in bounded cognitive lanes.",
        "parameter_law_display": r"\Theta_{\mathrm{pred}} \in [0.05,0.15],\quad M_{\mathrm{WM}} \in [3,7],\quad \eta \in [10^{-3},10^{-1}]",
        "observable_map_summary": "Prediction error, working-memory span, and adaptation strength for bounded cognitive organization.",
        "synthetic_observable_ids": [
            "K6::PREDICTION_ERROR_THRESHOLD",
            "K6::WORKING_MEMORY_SPAN",
            "K6::HEBBIAN_STRENGTH",
        ],
        "numerical_rows": [
            {
                "quantity": "Prediction-error threshold",
                "symbol_tex": r"\Theta_{\mathrm{pred}}",
                "value_tex": r"0.05\text{--}0.15",
                "units_note": "normalized units",
            },
            {
                "quantity": "Working-memory span",
                "symbol_tex": r"M_{\mathrm{WM}}",
                "value_tex": r"3\text{--}7",
                "units_note": "bound items",
            },
            {
                "quantity": "Hebbian strength coefficient",
                "symbol_tex": r"\eta",
                "value_tex": r"10^{-3}\text{--}10^{-1}",
                "units_note": "dimensionless",
            },
        ],
        "collapse_boundary": "K6 collapses when predictive stabilization fails across bounded cognitive observables or when representation thresholds require hidden freedom.",
    },
    "K7": {
        "title": "Social Coordination and Group Stability",
        "toe_file_ref": "content/toe/toe_k7",
        "appendix_table_label": "tab:k7-social-parameters",
        "theorem_native_claim": "K7 closes bounded social coordination through group-size, communication-bandwidth, and coordination-threshold packets.",
        "operator_binding_summary": "R, S, and U bind coordination thresholds, communication throughput, and conflict costs into admissible social trajectories.",
        "parameter_law_display": r"N_s \in [120,180],\quad J_{\mathrm{comm}} \in [1,5]\,\mathrm{bits/s},\quad \Theta_{\mathrm{coord}} \in [0.2,0.4]",
        "observable_map_summary": "Group stability size, communication throughput, coordination threshold, and conflict cost inside social coordination continua.",
        "synthetic_observable_ids": [
            "K7::GROUP_STABILITY_SIZE",
            "K7::COMMUNICATION_BANDWIDTH",
            "K7::COORDINATION_THRESHOLD",
        ],
        "numerical_rows": [
            {
                "quantity": "Group stability size",
                "symbol_tex": r"N_s",
                "value_tex": r"120\text{--}180",
                "units_note": "agents",
            },
            {
                "quantity": "Information-flow bandwidth per agent",
                "symbol_tex": r"J_{\mathrm{comm}}",
                "value_tex": r"1\text{--}5",
                "units_note": r"\mathrm{bits/s}",
            },
            {
                "quantity": "Coordination threshold",
                "symbol_tex": r"\Theta_{\mathrm{coord}}",
                "value_tex": r"0.2\text{--}0.4",
                "units_note": "dimensionless",
            },
        ],
        "collapse_boundary": "K7 collapses when communication throughput and coordination thresholds cannot stabilize social group trajectories without hidden rescue assumptions.",
    },
    "K8": {
        "title": "Civilizational Flows and Infrastructural Stability",
        "toe_file_ref": "content/toe/toe_k8",
        "appendix_table_label": "tab:k8-civilizational-parameters",
        "theorem_native_claim": "K8 binds civilizational energy density, renewal timing, and repair-decay balance into bounded macro-process trajectories and regime-shift packets.",
        "operator_binding_summary": "H, R, and U bind throughput, repair-decay balance, and regime-shift boundaries in bounded systems-level observables.",
        "parameter_law_display": r"E_{\mathrm{dens}} \in [10^2,10^3]\,\mathrm{W/m^2},\quad \tau_{\mathrm{infra}} \in [20,50]\,\mathrm{years},\quad R_{\mathrm{rep}} \in [0.8,1.2]",
        "observable_map_summary": "Energy density, infrastructure renewal, information coherence, and repair-decay balance in bounded civilizational lanes.",
        "synthetic_observable_ids": [
            "K8::ENERGY_CONSUMPTION_DENSITY",
            "K8::INFRASTRUCTURE_RENEWAL_TIME",
            "K8::REPAIR_TO_DECAY_RATIO",
        ],
        "numerical_rows": [
            {
                "quantity": "Energy consumption density",
                "symbol_tex": r"E_{\mathrm{dens}}",
                "value_tex": r"10^2\text{--}10^3",
                "units_note": r"\mathrm{W/m^2}",
            },
            {
                "quantity": "Infrastructure renewal time",
                "symbol_tex": r"\tau_{\mathrm{infra}}",
                "value_tex": r"20\text{--}50",
                "units_note": "years",
            },
            {
                "quantity": "Repair-to-decay ratio",
                "symbol_tex": r"R_{\mathrm{rep}}",
                "value_tex": r"0.8\text{--}1.2",
                "units_note": "dimensionless",
            },
        ],
        "collapse_boundary": "K8 collapses when macro-trajectories lose bounded turning-point fidelity, when repair-decay balance drifts outside its band, or when regime-shift packets require discretionary knobs.",
    },
    "K9": {
        "title": "Knowledge Systems and Scientific Memory",
        "toe_file_ref": "content/toe/toe_k9",
        "appendix_table_label": "tab:k9-knowledge-parameters",
        "theorem_native_claim": "K9 formalizes bounded scientific-knowledge continua through anomaly accumulation, paradigm coherence, and model-validation bandwidth.",
        "operator_binding_summary": "Q, R, and U bind anomaly handling, paradigm coherence, and memory retention inside knowledge-system packets.",
        "parameter_law_display": r"\Theta_{\mathrm{par}} \in [0.15,0.25],\quad J_{\mathrm{anom}} \in [10^{-4},10^{-2}],\quad \tau_{\mathrm{mem}} \in [30,200]\,\mathrm{years}",
        "observable_map_summary": "Paradigm coherence, anomaly accumulation, validation bandwidth, and scientific-memory half-life.",
        "synthetic_observable_ids": [
            "K9::PARADIGM_COHERENCE_THRESHOLD",
            "K9::ANOMALY_ACCUMULATION_RATE",
            "K9::SCIENTIFIC_MEMORY_HALF_LIFE",
        ],
        "numerical_rows": [
            {
                "quantity": "Paradigm-coherence threshold",
                "symbol_tex": r"\Theta_{\mathrm{par}}",
                "value_tex": r"0.15\text{--}0.25",
                "units_note": "dimensionless",
            },
            {
                "quantity": "Anomaly accumulation rate",
                "symbol_tex": r"J_{\mathrm{anom}}",
                "value_tex": r"10^{-4}\text{--}10^{-2}",
                "units_note": "per cycle",
            },
            {
                "quantity": "Scientific-memory half-life",
                "symbol_tex": r"\tau_{\mathrm{mem}}",
                "value_tex": r"30\text{--}200",
                "units_note": "years",
            },
        ],
        "collapse_boundary": "K9 collapses if anomaly load outruns lawful model revision or if scientific memory and validation bandwidth fail to stabilize the knowledge packet.",
    },
    "K10": {
        "title": "Formal Systems and Recursion",
        "toe_file_ref": "content/toe/toe_k10",
        "appendix_table_label": "tab:k10-formal-parameters",
        "theorem_native_claim": "K10 binds bounded recursion, expressivity classes, and proof-flow capacity into the formal-system lane of the unified-science closure stack.",
        "operator_binding_summary": "F, Q, and U bind recursion depth, proof throughput, and consistency thresholds in formal continua.",
        "parameter_law_display": r"d_{\mathrm{rec}} \in [10,10^4],\quad \Theta_{\mathrm{cons}} \in [0.01,0.05],\quad J_{\mathrm{proof}} \in [1,10^3]",
        "observable_map_summary": "Recursion depth, consistency threshold, expressivity class, and proof-flow capacity in bounded formal systems.",
        "synthetic_observable_ids": [
            "K10::RECURSION_DEPTH",
            "K10::CONSISTENCY_THRESHOLD",
            "K10::PROOF_FLOW_CAPACITY",
        ],
        "numerical_rows": [
            {
                "quantity": "Recursion depth (effective)",
                "symbol_tex": r"d_{\mathrm{rec}}",
                "value_tex": r"10\text{--}10^4",
                "units_note": "steps",
            },
            {
                "quantity": "Consistency threshold",
                "symbol_tex": r"\Theta_{\mathrm{cons}}",
                "value_tex": r"0.01\text{--}0.05",
                "units_note": "dimensionless",
            },
            {
                "quantity": "Proof-flow capacity",
                "symbol_tex": r"J_{\mathrm{proof}}",
                "value_tex": r"1\text{--}10^3",
                "units_note": "steps/s",
            },
        ],
        "collapse_boundary": "K10 collapses if formal recursion and proof throughput cannot remain bounded without violating consistency thresholds.",
    },
    "K11": {
        "title": "Meta-Theoretical Reflexivity",
        "toe_file_ref": "content/toe/toe_k11",
        "appendix_table_label": "tab:k11-meta-parameters",
        "theorem_native_claim": "K11 captures meta-theoretical reflexivity only if cross-framework coherence carries irreducible work beyond K10.",
        "operator_binding_summary": "Q, R, and S bind meta-coherence, reflexive depth, and cross-landscape coupling under the requirement that no K10-only translation preserves all declared upper-level burdens.",
        "parameter_law_display": r"\Theta_{\mathrm{meta}} \in [0.02,0.1],\quad d_{\mathrm{refl}} \in [3,50],\quad J_X \in [0.1,1]",
        "observable_map_summary": "Meta-coherence, reflexive depth, and cross-landscape coupling in the meta-theoretical packet.",
        "synthetic_observable_ids": [
            "K11::META_COHERENCE_THRESHOLD",
            "K11::REFLEXIVE_DEPTH",
            "K11::CROSS_LANDSCAPE_COUPLING",
        ],
        "numerical_rows": [
            {
                "quantity": "Meta-coherence threshold",
                "symbol_tex": r"\Theta_{\mathrm{meta}}",
                "value_tex": r"0.02\text{--}0.1",
                "units_note": "dimensionless",
            },
            {
                "quantity": "Reflexive depth",
                "symbol_tex": r"d_{\mathrm{refl}}",
                "value_tex": r"3\text{--}50",
                "units_note": "levels",
            },
            {
                "quantity": "Cross-landscape coupling",
                "symbol_tex": r"J_X",
                "value_tex": r"0.1\text{--}1",
                "units_note": "dimensionless",
            },
        ],
        "collapse_boundary": "K11 collapses if an explicit K10-only reduction preserves the declared meta-theoretical burdens or if meta-coherence depends on an excluded lift route.",
    },
    "K12": {
        "title": "Global Semantic Coherence",
        "toe_file_ref": "content/toe/toe_k12",
        "appendix_table_label": "tab:k12-universal-parameters",
        "theorem_native_claim": "K12 packages global semantic coherence only if cross-domain meaning remains jointly interpretable and no surviving global falsifier breaks the unified atlas.",
        "operator_binding_summary": "Q, R, S, and U bind semantic coherence, global compatibility, and reference stability into the final unified-science synthesis layer.",
        "parameter_law_display": r"C_{\mathrm{uni}} \in [10^3,10^{12}],\quad \Theta_{\mathrm{uni}} \in [10^{-3},10^{-2}],\quad R_{\mathrm{uni}} \in [0.1,1]",
        "observable_map_summary": "Universal integration capacity, cross-continuum compatibility, and structural reachability.",
        "synthetic_observable_ids": [
            "K12::UNIVERSAL_INTEGRATION_CAPACITY",
            "K12::CROSS_CONTINUUM_COMPATIBILITY",
            "K12::STRUCTURAL_REACHABILITY",
        ],
        "numerical_rows": [
            {
                "quantity": "Universal integration capacity",
                "symbol_tex": r"C_{\mathrm{uni}}",
                "value_tex": r"10^3\text{--}10^{12}",
                "units_note": "dimensionless",
            },
            {
                "quantity": "Cross-continuum compatibility",
                "symbol_tex": r"\Theta_{\mathrm{uni}}",
                "value_tex": r"10^{-3}\text{--}10^{-2}",
                "units_note": "dimensionless",
            },
            {
                "quantity": "Structural reachability",
                "symbol_tex": r"R_{\mathrm{uni}}",
                "value_tex": r"0.1\text{--}1",
                "units_note": "dimensionless",
            },
        ],
        "collapse_boundary": "K12 collapses if cross-domain compatibility fragments, if the unified atlas cannot pass integrability, or if a surviving global falsifier breaks semantic coherence.",
    },
}

STATEMENT_CLASS_ROWS = [
    {
        "statement_class": "AXIOMATIC",
        "meaning": "Accepted as part of the declared Core canon; not advertised as empirical closure.",
    },
    {
        "statement_class": "DERIVED",
        "meaning": "Positive outward science is permitted only when the statement is source-bound, proof-bound, and dependency-exact.",
    },
    {
        "statement_class": "EMPIRICAL",
        "meaning": "Requires a standalone domain packet, data route, numerical packet, replay procedure, and falsifier before promotion.",
    },
    {
        "statement_class": "STRUCTURAL",
        "meaning": "Structural or boundary-setting statements may constrain the model class without by themselves constituting empirical promotion.",
    },
    {
        "statement_class": "INTERPRETIVE",
        "meaning": "Interpretive readings may remain inside the research program, but must not leak into positive outward science without formal promotion.",
    },
    {
        "statement_class": "FRONTIER",
        "meaning": "May remain inside the research program, but must not leak into positive outward science without formal promotion.",
    },
]

REVISION_LAW_ROWS = [
    {
        "priority": 1,
        "layer": "EMPIRICAL_BRIDGES_AND_REPLAY_BINDINGS",
        "revision_rule": "REVISE_EMPIRICAL_BRIDGES_FIRST",
        "conflict_trigger": "OFFICIAL_OR_INSTITUTE_RUN_REPLAY_BREACH",
        "current_status": "STABLE",
    },
    {
        "priority": 2,
        "layer": "PARAMETERIZATION_AND_NUMERICAL_PACKETS",
        "revision_rule": "REVISE_PARAMETERIZATIONS_BEFORE_THEOREM_SCOPE",
        "conflict_trigger": "RESIDUAL_OR_CALIBRATION_BREACH_PERSISTS_AFTER_BRIDGE_REPAIR",
        "current_status": "STABLE",
    },
    {
        "priority": 3,
        "layer": "STANDALONE_DOMAIN_PACKETS_AND_DERIVED_THEOREMS",
        "revision_rule": "REVISE_STANDALONE_DOMAIN_PACKETS_BEFORE_ROOT_KERNEL",
        "conflict_trigger": "MULTI_BENCHMARK_FAILURE_PERSISTS_AFTER_PARAMETERIZATION_REPAIR",
        "current_status": "REAUDIT_REQUIRED_FOR_BRIDGE_ONLY_DOMAINS",
    },
    {
        "priority": 4,
        "layer": "ROOT_KERNEL",
        "revision_rule": "ROOT_KERNEL_REVISION_ALLOWED_ONLY_AFTER_ACCUMULATED_CROSS_DOMAIN_FAILURE",
        "conflict_trigger": "ACCUMULATED_CROSS_DOMAIN_FAILURE_EXCEEDS_DECLARED_THRESHOLD",
        "current_status": "LOCKED_PENDING_ACCUMULATED_CROSS_DOMAIN_FAILURE",
    },
]

MINIMALITY_ROWS = [
    {
        "component": "ROOT_THEOREM_STACK",
        "kind": "KERNEL_COMPONENT",
        "ablation_status": "NECESSARY_UNDER_CURRENT_PROOF_STACK",
        "removal_effect": "Collapses the promoted contradiction-lift-or-collapse doctrine.",
    },
    {
        "component": "K_LEVEL_PARTITION",
        "kind": "K_LEVEL_BOUNDARY",
        "ablation_status": "FRONTIER_PENDING_STRICT_IRREDUCIBILITY_PROOF",
        "removal_effect": "Would blur the explicit K-level doctrine and weaken the current boundary ledger.",
    },
    {
        "component": "EMPIRICAL_ANCHORING_DISCIPLINE",
        "kind": "PROMOTION_GUARD",
        "ablation_status": "NECESSARY_FOR_NON_RUBBERIZING_PROMOTION",
        "removal_effect": "Would allow positive outward science without observables, data routes, and replayable falsifiers.",
    },
    {
        "component": "STRICT_UNIQUENESS_OR_MINIMALITY",
        "kind": "META_THEOREM",
        "ablation_status": "EXPLICIT_FRONTIER_RESIDUE_LOCALIZED",
        "removal_effect": "The strongest current result remains an impossibility boundary rather than a strict uniqueness proof.",
    },
]

COMPRESSION_ROWS = [
    {
        "axis": "THEOREM_SUPPORT_DESCRIPTION_LENGTH",
        "complexity_units": 17,
        "performance_value": 0.294118,
        "interpretation": "How much validated domain coverage is currently carried per rooted theorem-support statement.",
    },
    {
        "axis": "EMPIRICAL_PACKET_COMPLEXITY_VS_RESIDUAL_PERFORMANCE",
        "complexity_units": 5,
        "performance_value": 1.0,
        "interpretation": "How much validated coverage is carried per active numerical packet under the present replay bar.",
    },
    {
        "axis": "COVERAGE_PER_COMPLEXITY_VS_COMPETITORS",
        "complexity_units": 5,
        "performance_value": 0.384615,
        "interpretation": "Computed as 5 validated lanes divided by 13 declared same-claim and domain-baseline comparator units; source row: alternative-model competition matrix.",
    },
]

LOAD_BEARING_DEPENDENCY_ATLAS = [
    {
        "edge_id": "SPINE::AXIOM_3_2_AND_DEFINITIONS_12_1_12_3_12_4_TO_SOURCE_THEOREM_3",
        "premises": ["Axiom 3.2", "Definition 12.1", "Definition 12.3", "Definition 12.4"],
        "result": "Source Theorem 3",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/theorems_master.tex"],
    },
    {
        "edge_id": "SPINE::SOURCE_THEOREM_3_TO_LEMMA_1",
        "premises": ["Source Theorem 3"],
        "result": "Lemma 1",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/theorems_master.tex"],
    },
    {
        "edge_id": "SPINE::AXIOM_3_3_AND_DEFINITION_12_6_TO_SOURCE_COROLLARY_3_2",
        "premises": ["Axiom 3.3", "Definition 12.6"],
        "result": "Source Corollary 3.2",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
    {
        "edge_id": "SPINE::SOURCE_COROLLARY_3_2_TO_LEMMA_3",
        "premises": ["Source Corollary 3.2"],
        "result": "Lemma 3",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
    {
        "edge_id": "SPINE::LEMMA_1_AND_DEFINITION_12_5_TO_LEMMA_2",
        "premises": ["Lemma 1", "Definition 12.5"],
        "result": "Lemma 2",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/theorems_master.tex"],
    },
    {
        "edge_id": "SPINE::LEMMA_2_TO_THEOREM_A",
        "premises": ["Lemma 2"],
        "result": "Theorem A",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/04_results.tex"],
    },
]

PROOF_OBLIGATION_SHEETS = [
    {
        "obligation_id": "OBLIGATION::SOURCE_THEOREM_3",
        "statement": "Show that Axiom 3.2 plus Definitions 12.1, 12.3, and 12.4 lawfully imply Source Theorem 3.",
        "premises": ["Axiom 3.2", "Definition 12.1", "Definition 12.3", "Definition 12.4"],
        "forbidden_shortcuts": [
            "No interpretive prose may replace an admissibility premise.",
            "No excluded lift-heavy theorem family may be imported silently.",
        ],
        "excluded_dependencies": ["Excluded lift theorem family", "Journal-core-only compression"],
        "falsifier_condition": "If the implication requires a hidden excluded dependency or the admissibility premises do not suffice, Source Theorem 3 must be narrowed or withdrawn.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
    {
        "obligation_id": "OBLIGATION::LEMMA_1",
        "statement": "Show that Source Theorem 3 closes Lemma 1 without widening the claim boundary.",
        "premises": ["Source Theorem 3"],
        "forbidden_shortcuts": [
            "No downstream lemma may be imported back as support.",
            "No journal-core enlargement beyond the master route is allowed.",
        ],
        "excluded_dependencies": ["Interpretive-only support", "Compression-only support"],
        "falsifier_condition": "If Lemma 1 requires support not traceable to Source Theorem 3, the spine is broken and the positive body must be rebuilt.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
    {
        "obligation_id": "OBLIGATION::SOURCE_COROLLARY_3_2",
        "statement": "Show that Axiom 3.3 plus Definition 12.6 lawfully imply Source Corollary 3.2 and preserve irreversibility.",
        "premises": ["Axiom 3.3", "Definition 12.6"],
        "forbidden_shortcuts": [
            "No residue-to-identity leap is allowed.",
            "No numerically identical restoration after lawful death is allowed without explicit theorem support.",
        ],
        "excluded_dependencies": ["Identity restoration after lawful death", "Metaphorical rebirth language"],
        "falsifier_condition": "If the same continuum can return numerically identical after lawful death without violating Axiom 3.3, the irreversibility corollary must be revised or withdrawn.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
    {
        "obligation_id": "OBLIGATION::LEMMA_3",
        "statement": "Show that Source Corollary 3.2 closes Lemma 3 under the declared residue and rebirth boundary.",
        "premises": ["Source Corollary 3.2"],
        "forbidden_shortcuts": [
            "Residue may not be counted as full live identity.",
            "Post-collapse continuation may not be classified as persistence without a new theorem.",
        ],
        "excluded_dependencies": ["Persistence-by-analogy", "Undeclared rebirth equivalence"],
        "falsifier_condition": "If residue preserves full live identity instead of structural aftermath only, the classification boundary must be rewritten.",
        "refs": ["content/21_oc_core_1_3_worked_examples.tex", "content/04_results.tex"],
    },
    {
        "obligation_id": "OBLIGATION::LEMMA_2",
        "statement": "Show that Lemma 1 plus Definition 12.5 imply Lemma 2 without hidden extensions.",
        "premises": ["Lemma 1", "Definition 12.5"],
        "forbidden_shortcuts": [
            "No extension branch may be used as hidden proof support.",
            "No empirical bridge may masquerade as theorem support.",
        ],
        "excluded_dependencies": ["EXTENSION branches", "BRIDGE_ONLY packets"],
        "falsifier_condition": "If Lemma 2 requires an excluded branch or bridge-only evidence as proof support, the theorem route is illegitimate.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/19_oc_core_1_3_foundational_consistency.tex"],
    },
    {
        "obligation_id": "OBLIGATION::THEOREM_A",
        "statement": "Show that Lemma 2 is sufficient for Theorem A and that the journal-core extraction does not exceed the master theorem scope.",
        "premises": ["Lemma 2"],
        "forbidden_shortcuts": [
            "No journal-core claim may be stronger than the master monograph.",
            "No excluded theorem family may be reintroduced in compressed form.",
        ],
        "excluded_dependencies": ["Journal-core-only strengthening", "Excluded lift-heavy theorem family"],
        "falsifier_condition": "If the journal core requires support not present in the master route, the article must be narrowed or the master must be repaired first.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
]

HOSTILE_REVIEW_BACKLOG_ROWS = [
    {
        "review_id": "HOSTILE::LAWFUL_COLLAPSE",
        "challenge": "Collapse must be tied to the loss of admissible realization rather than to loose metaphor.",
        "current_status": "PENDING_FORMAL_DOSSIER",
        "blocks_global_pass": True,
        "exit_criterion": "A formal dossier links collapse claims to admissible-state loss, threshold logic, and source witnesses without prose leakage.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex", "content/04_results.tex"],
    },
    {
        "review_id": "HOSTILE::IRREVERSIBILITY",
        "challenge": "Irreversibility under Axiom 3.3 must forbid numerical identity restoration after lawful death.",
        "current_status": "PENDING_FORMAL_DOSSIER",
        "blocks_global_pass": True,
        "exit_criterion": "The irreversibility corollary is formalized as a dossier with explicit counterexample conditions and no identity loophole.",
        "refs": ["content/21_oc_core_1_3_worked_examples.tex", "content/04_results.tex"],
    },
    {
        "review_id": "HOSTILE::RESIDUE_REBIRTH_BOUNDARY",
        "challenge": "Residue and rebirth must remain controlled classifications rather than narrative labels.",
        "current_status": "PENDING_FORMAL_DOSSIER",
        "blocks_global_pass": True,
        "exit_criterion": "Residue, rebirth, and persistence are separated by theorem-backed boundary conditions with declared falsifiers.",
        "refs": ["content/21_oc_core_1_3_worked_examples.tex", "content/12_collapse_rebirth.tex"],
    },
    {
        "review_id": "HOSTILE::EXCLUDED_LIFT_FIREWALL",
        "challenge": "No excluded lift-heavy theorem family may be smuggled into the positive bounded argument.",
        "current_status": "PENDING_FORMAL_DOSSIER",
        "blocks_global_pass": True,
        "exit_criterion": "An exclusion ledger proves that forbidden theorem families and forbidden branches do not enter the core proof path.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex", "content/19_oc_core_1_3_foundational_consistency.tex"],
    },
    {
        "review_id": "HOSTILE::JOURNAL_CORE_ASYMMETRY",
        "challenge": "The journal core must remain a lawful extraction from the master and must never enlarge the claim.",
        "current_status": "PENDING_FORMAL_DOSSIER",
        "blocks_global_pass": True,
        "exit_criterion": "A journal-core extraction dossier proves that every public theorem claim is traceably derived from the master route.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
    {
        "review_id": "HOSTILE::K11_K12_IRREDUCIBILITY",
        "challenge": "K11 and K12 must be proved necessary beyond K10 or explicitly demoted with the dependency graph rebuilt.",
        "current_status": "PENDING_IRREDUCIBILITY_CAMPAIGN",
        "blocks_global_pass": True,
        "exit_criterion": "Either an irreducibility dossier proves that K11 and K12 carry nonreducible scientific work, or the upper levels are demoted and all dependent routes are rebuilt.",
        "refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "content/21_oc_core_1_3_worked_examples.tex"],
    },
]

METHOD_LADDER_ROWS = [
    {
        "order": 1,
        "method_class": "SOURCE_EXTRACTION",
        "entry_rule": "Use when a claim lacks an exact theorem target, exact dependency list, or exact source text.",
        "advance_condition": "The claim is reduced to an exact theorem packet or exact falsifiable subclaim.",
        "anti_cycle_condition": "May not be repeated unless a new source block, new theorem family, or newly scoped parent claim is introduced.",
    },
    {
        "order": 2,
        "method_class": "FRESH_DERIVATION_FROM_OPERATORS",
        "entry_rule": "Use when source extraction alone does not close the theorem-native route.",
        "advance_condition": "A new derivation binds the claim back to kernel operators and K-level doctrine without hidden auxiliary hypotheses.",
        "anti_cycle_condition": "May not be repeated unless a new formal premise or a new decomposition of the claim space appears.",
    },
    {
        "order": 3,
        "method_class": "REPARAMETERIZATION_OR_CLAIM_DECOMPOSITION",
        "entry_rule": "Use when the claim is too wide, rubberized, or under-specified to admit a lawful parameter law.",
        "advance_condition": "The claim is replaced by narrower child claims with explicit parent relations and non-degenerate parameter laws.",
        "anti_cycle_condition": "May not be repeated unless a new observable family or a new admissible regime is declared before replay.",
    },
    {
        "order": 4,
        "method_class": "NEW_DATA_OR_MEASUREMENT_ROUTE",
        "entry_rule": "Use only after theorem target, parameter law, and held-out policy are already fixed.",
        "advance_condition": "A new primary-data or institute-run route closes a genuinely missing observable family without widening scope.",
        "anti_cycle_condition": "May not be repeated unless the new route adds a previously unavailable observable family or a nonoverlapping held-out family.",
    },
    {
        "order": 5,
        "method_class": "SAME_CLAIM_CLASS_ADVERSARIAL_COMPARISON",
        "entry_rule": "Use when the claim survives internal closure steps and must now face simpler same-claim-class competitors.",
        "advance_condition": "No simpler comparator explains the same claim class better under the declared cost and evidence bar.",
        "anti_cycle_condition": "May not be repeated unless a new comparator family or a new cost-normalized metric is introduced.",
    },
]

PROGRAM_PHASE_ROWS = [
    {
        "phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
        "objective": "Stabilize the load-bearing theorem spine, hostile-review dossiers, and mathematics anchor before outward theoremization.",
        "exit_criterion": "Closed core survives hostile review, excluded-lift leakage is blocked, and the mathematics anchor is maintained as theorem-native.",
    },
    {
        "phase_id": "PHASE_2_DOMAIN_THEOREMIZATION",
        "objective": "Turn each blocked domain into an exact theorem-native research target before replay or measurement escalation.",
        "exit_criterion": "Every blocked domain owns an exact theorem packet, parameter-law packet, observable map, and locked held-out policy.",
    },
    {
        "phase_id": "PHASE_3_PHYSICS_CLOSURE",
        "objective": "Close the first domain theorem-native route over bounded physical benchmark families.",
        "exit_criterion": "Physics theorem packet, parameter law, observable route, and held-out replay all pass under the declared promotion bar.",
    },
    {
        "phase_id": "PHASE_4_CHEMISTRY_CLOSURE",
        "objective": "Close chemistry as the next source-near organizational bridge after physics.",
        "exit_criterion": "Chemistry theorem packet survives held-out compound or reaction rotation without hidden fit freedom.",
    },
    {
        "phase_id": "PHASE_5_BIOLOGY_CLOSURE",
        "objective": "Close bounded biological state-transition and response-signature science without overclaiming general biology.",
        "exit_criterion": "Biological theorem-native packets survive cross-dataset held-out tests and do not rest on a single dataset family.",
    },
    {
        "phase_id": "PHASE_6_SYSTEMS_CLOSURE",
        "objective": "Close K8 systems projection packets strictly on measurable macro-process trajectories and regime shifts.",
        "exit_criterion": "Systems turning-point and trajectory claims survive held-out interval replay with no out-of-band behavior.",
    },
    {
        "phase_id": "PHASE_7_CROSS_DOMAIN_UNIFICATION",
        "objective": "Build one unified atlas and integrability suite across closed domains.",
        "exit_criterion": "Shared operators, invariants, and observables remain globally noncontradictory and no global falsifier survives.",
    },
    {
        "phase_id": "PHASE_8_FULL_CIVILIZATION_PROGRAM",
        "objective": "Run controlled expansion after first global PASS without mixing frontier work with closed canon.",
        "exit_criterion": "New claims are promoted only through the same ladder and the atlas continues to compress ignorance rather than inflate rhetoric.",
    },
]

CLOSURE_ARTIFACT_ORDER = [
    "theorem_packet",
    "parameter_law_packet",
    "observable_binding_spec",
    "dataset_data_route_manifest",
    "held_out_replay_spec",
    "falsifier_ledger",
    "counterexample_ledger",
    "same_claim_class_comparator_ledger",
]

ARTIFACT_ASSIGNEE_ROLE_MAP = {
    "theorem_packet": "FORMAL_THEOREM_TRACK",
    "parameter_law_packet": "PARAMETER_LAW_TRACK",
    "observable_binding_spec": "OBSERVABLE_BINDING_TRACK",
    "dataset_data_route_manifest": "DATA_ROUTE_TRACK",
    "held_out_replay_spec": "REPLAY_PROTOCOL_TRACK",
    "falsifier_ledger": "FALSIFIER_TRACK",
    "counterexample_ledger": "COUNTEREXAMPLE_TRACK",
    "same_claim_class_comparator_ledger": "ADVERSARIAL_BASELINE_TRACK",
}

ARTIFACT_ENTRY_GATE_MAP = {
    "theorem_packet": "ENTRY_IMMEDIATE",
    "parameter_law_packet": "ENTRY_AFTER_THEOREM_TARGET_LOCKS",
    "observable_binding_spec": "ENTRY_AFTER_THEOREM_AND_PARAMETER_LAW_LOCK",
    "dataset_data_route_manifest": "ENTRY_AFTER_OBSERVABLE_BINDING_LOCKS",
    "held_out_replay_spec": "ENTRY_AFTER_DATA_ROUTE_LOCKS",
    "falsifier_ledger": "ENTRY_AFTER_THEOREM_SCOPE_LOCKS",
    "counterexample_ledger": "ENTRY_AFTER_THEOREM_SCOPE_LOCKS",
    "same_claim_class_comparator_ledger": "ENTRY_AFTER_REPLAY_AND_FALSIFIER_LOCK",
}

ARTIFACT_PASS_TRANSITION_MAP = {
    "theorem_packet": "MARK_COMPLETE_AND_UNLOCK_PARAMETER_LAW_GATE",
    "parameter_law_packet": "MARK_COMPLETE_AND_UNLOCK_OBSERVABLE_BINDING_GATE",
    "observable_binding_spec": "MARK_COMPLETE_AND_UNLOCK_DATA_ROUTE_GATE",
    "dataset_data_route_manifest": "MARK_COMPLETE_AND_LOCK_HELD_OUT_POLICY",
    "held_out_replay_spec": "MARK_COMPLETE_AND_UNLOCK_PROMOTION_AUDIT",
    "falsifier_ledger": "MARK_COMPLETE_AND_UNLOCK_COUNTEREXAMPLE_AUDIT",
    "counterexample_ledger": "MARK_COMPLETE_IF_NO_SURVIVING_COUNTEREXAMPLE_REMAINS",
    "same_claim_class_comparator_ledger": "MARK_COMPLETE_ONLY_IF_NO_SIMPLER_SUPERIOR_BASELINE_SURVIVES",
}

ARTIFACT_FAIL_TRANSITION_MAP = {
    "theorem_packet": "KEEP_FAIL_CLOSED_AND_REQUIRE_SPLIT_WITH_EXPLICIT_PARENT_RELATION_OR_REFUTE_OR_SUSPEND",
    "parameter_law_packet": "KEEP_FAIL_CLOSED_AND_REQUIRE_REPARAMETERIZATION_OR_CLAIM_DECOMPOSITION",
    "observable_binding_spec": "KEEP_FAIL_CLOSED_AND_REQUIRE_EXPLICIT_THEOREM_TO_OBSERVABLE_REBUILD",
    "dataset_data_route_manifest": "KEEP_FAIL_CLOSED_AND_REQUIRE_NEW_DATA_ROUTE_JUSTIFICATION",
    "held_out_replay_spec": "KEEP_FAIL_CLOSED_AND_FORBID_PROMOTION",
    "falsifier_ledger": "KEEP_FAIL_CLOSED_AND_WITHDRAW_POSITIVE_OUTWARD_SCIENCE",
    "counterexample_ledger": "KEEP_FAIL_CLOSED_AND_REFUTE_OR_NARROW_SCOPE",
    "same_claim_class_comparator_ledger": "KEEP_FAIL_CLOSED_AND_DEMOTE_TO_FRONTIER_OR_SUPERSEDE_CLAIM",
}

PHASE1_EXIT_CRITERIA_ROWS = [
    "All hostile-review rows carry an explicit pass or fail outcome rather than a narrative placeholder.",
    "Load-bearing proof obligations are fully specified with premises, forbidden shortcuts, excluded dependencies, and falsifier conditions.",
    "No closed-core route depends on excluded lift or extension leakage.",
    "The mathematics anchor remains theorem-native and survives intensified counterexample search.",
]

MATHEMATICS_ANCHOR_MAINTENANCE = {
    "scope_rule": "MAINTAIN_EXISTING_EXACT_QUESTION_WIDTH_ONLY",
    "required_actions": [
        "Expand the exact-question corpus without widening the claim by rhetoric alone.",
        "Intensify counterexample search on the exact theorem-native anchor.",
        "Strengthen exact terminalization and minimal-denominator control.",
    ],
    "promotion_rule": "ANCHOR_MAY_NOT_BE_MARKETED_AS_TOTAL_MATHEMATICS",
}

DOMAIN_CLOSURE_CONFIG = {
    "MATHEMATICS": {
        "formal_derivation_order": 0,
        "empirical_cost_order": 0,
        "closure_impact": 10,
        "dependency_centrality": 10,
        "expected_information_gain": 7,
        "compute_cost": 2,
        "data_cost": 1,
        "measurement_cost": 1,
        "editorial_cost": 2,
        "phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
        "launch_rule": "MAINTAIN_ALWAYS_ON",
        "minimum_theorem_native_claim": "Maintain the exact-question theorem-native anchor and expand the counterexample search without broadening scope by rhetoric alone.",
        "parameter_law_target": "Strengthen exact terminalization and minimal-denominator control on the current exact-question corpus.",
        "parallelism_note": "Runs continuously as the formal anchor for all later domains.",
        "current_priority_label": "ANCHOR_MAINTENANCE",
    },
    "PHYSICS": {
        "formal_derivation_order": 1,
        "empirical_cost_order": 1,
        "closure_impact": 9,
        "dependency_centrality": 9,
        "expected_information_gain": 8,
        "compute_cost": 2,
        "data_cost": 2,
        "measurement_cost": 3,
        "editorial_cost": 3,
        "phase_id": "PHASE_3_PHYSICS_CLOSURE",
        "launch_rule": "START_IMMEDIATELY_AFTER_PHASE_1",
        "minimum_theorem_native_claim": "Prove a bounded theorem-native physics packet for K1/K2 contradiction-load and stabilization-margin operators over constants, spectral lines, and transport residual families.",
        "parameter_law_target": "Derive explicit parameter laws for bounded physical families and eliminate pure fitted-envelope interpretations.",
        "parallelism_note": "Primary first closure lane; no later domain should outrun it.",
        "current_priority_label": "CHEAPEST_AND_NEAREST_CORE_BRIDGE",
    },
    "CHEMISTRY": {
        "formal_derivation_order": 2,
        "empirical_cost_order": 2,
        "closure_impact": 8,
        "dependency_centrality": 8,
        "expected_information_gain": 7,
        "compute_cost": 3,
        "data_cost": 3,
        "measurement_cost": 4,
        "editorial_cost": 4,
        "phase_id": "PHASE_4_CHEMISTRY_CLOSURE",
        "launch_rule": "START_AFTER_PHYSICS_THEOREM_PACKET_LOCKS",
        "minimum_theorem_native_claim": "Prove a bounded theorem-native chemistry packet for thermochemical, spectroscopic, and kinetic observable families.",
        "parameter_law_target": "Derive composition-sensitive thermochemical and kinetic parameter laws with explicit admissible regimes and no hidden fit freedom.",
        "parallelism_note": "Next formal lane after physics; some data preparation may run earlier, but promotion waits for the physics shell to lock.",
        "current_priority_label": "SECOND_CORE_BRIDGE",
    },
    "BIOLOGY": {
        "formal_derivation_order": 3,
        "empirical_cost_order": 4,
        "closure_impact": 7,
        "dependency_centrality": 7,
        "expected_information_gain": 8,
        "compute_cost": 4,
        "data_cost": 5,
        "measurement_cost": 8,
        "editorial_cost": 5,
        "phase_id": "PHASE_5_BIOLOGY_CLOSURE",
        "launch_rule": "START_AFTER_CHEMISTRY_THEOREM_PACKET_LOCKS",
        "minimum_theorem_native_claim": "Prove bounded theorem-native biological packets for expression-signature, state-transition-order, and response-onset lanes.",
        "parameter_law_target": "Derive state-transition and response-signature parameter laws that survive cross-dataset tests.",
        "parallelism_note": "Formal order precedes systems, but the high measurement cost makes it a slower lane.",
        "current_priority_label": "HIGH_INFORMATION_BUT_EXPENSIVE",
    },
    "SYSTEMS_CIVILIZATIONAL_PROJECTION": {
        "formal_derivation_order": 4,
        "empirical_cost_order": 3,
        "closure_impact": 6,
        "dependency_centrality": 6,
        "expected_information_gain": 6,
        "compute_cost": 2,
        "data_cost": 3,
        "measurement_cost": 4,
        "editorial_cost": 4,
        "phase_id": "PHASE_6_SYSTEMS_CLOSURE",
        "launch_rule": "ALLOW_PARALLEL_DATA_PREP_AFTER_CHEMISTRY_BUT_FINAL_PROMOTION_AFTER_BIOLOGY_FORMAL_ROUTE",
        "minimum_theorem_native_claim": "Prove a bounded theorem-native systems packet for measurable macro-process trajectories and regime-shift signatures only.",
        "parameter_law_target": "Derive change-point and throughput parameter laws without discretionary knobs.",
        "parallelism_note": "Cheaper empirical prep than biology is allowed, but final unification waits for the biological formal route.",
        "current_priority_label": "CHEAPER_PREP_BUT_LATE_PROMOTION",
    },
}

SCIENCE_SURFACE_TARGETS = {
    "spot": EDITORIAL_DIR / "OC_CORE_1_3_SCIENCE_SPOT_latest.json",
    "foundational": EDITORIAL_DIR / "FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
    "protocols": EDITORIAL_DIR / "DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
    "matrix": EDITORIAL_DIR / "EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
    "command_board": EDITORIAL_DIR / "DOMAIN_HARD_CLOSURE_COMMAND_BOARD_latest.json",
    "legacy_hard_closure_program": EDITORIAL_DIR / "DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json",
    "legacy_institute_run_program": EDITORIAL_DIR / "INSTITUTE_RUN_MEASUREMENT_PROGRAM_latest.json",
    "autoprop": EDITORIAL_DIR / "SCIENCE_OPERATIONALIZATION_AUTOPROPAGATION_CONTRACT_latest.json",
    "closure_program": EDITORIAL_DIR / "OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_latest.json",
    "atlas": EDITORIAL_DIR / "OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
    "proof_obligations": EDITORIAL_DIR / "OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
    "hostile_review": EDITORIAL_DIR / "OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json",
    "closure_bundles": EDITORIAL_DIR / "OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json",
    "phase1_dossier": EDITORIAL_DIR / "OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json",
    "toe_synthesis": EDITORIAL_DIR / "OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
    "practical_utility": EDITORIAL_DIR / "OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json",
}

TEMPLATE_SYNC_MAP = {
    REPO_ROOT / "oc_core_1_3_master_monograph.tex": MONOGRAPH_SOURCE_DIR / "oc_core_1_3_master_monograph.tex",
    REPO_ROOT / "content" / "frontmatter_oc_core_1_3_master.tex": MONOGRAPH_SOURCE_DIR / "content" / "frontmatter_oc_core_1_3_master.tex",
    REPO_ROOT / "content" / "17_oc_core_1_3_reader_guide.tex": MONOGRAPH_SOURCE_DIR / "content" / "17_oc_core_1_3_reader_guide.tex",
    REPO_ROOT / "content" / "22_oc_core_1_3_operationalization_program.tex": MONOGRAPH_SOURCE_DIR / "content" / "22_oc_core_1_3_operationalization_program.tex",
    REPO_ROOT / "content" / "23_oc_core_1_3_empirical_execution_protocols.tex": MONOGRAPH_SOURCE_DIR / "content" / "23_oc_core_1_3_empirical_execution_protocols.tex",
    REPO_ROOT / "content" / "24_oc_core_1_3_proof_machinery.tex": MONOGRAPH_SOURCE_DIR / "content" / "24_oc_core_1_3_proof_machinery.tex",
    REPO_ROOT / "content" / "25_oc_core_1_3_toe_synthesis.tex": MONOGRAPH_SOURCE_DIR / "content" / "25_oc_core_1_3_toe_synthesis.tex",
    REPO_ROOT / "content" / "26_oc_core_1_3_practical_utility.tex": MONOGRAPH_SOURCE_DIR / "content" / "26_oc_core_1_3_practical_utility.tex",
    REPO_ROOT / "appendix" / "G_oc_core_1_3_empirical_validation_matrix.tex": MONOGRAPH_SOURCE_DIR / "appendix" / "G_oc_core_1_3_empirical_validation_matrix.tex",
    REPO_ROOT / "appendix" / "M_oc_core_1_3_proof_machinery_appendix.tex": MONOGRAPH_SOURCE_DIR / "appendix" / "M_oc_core_1_3_proof_machinery_appendix.tex",
    REPO_ROOT / "appendix" / "R_oc_core_1_3_practical_utility_model_comparison_atlas.tex": MONOGRAPH_SOURCE_DIR / "appendix" / "R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
}

ROOT_TEX_TARGETS = {
    "operationalization": ROOT_CONTENT_GENERATED_DIR / "oc_core_1_3_operationalization_program_generated.tex",
    "protocols": ROOT_CONTENT_GENERATED_DIR / "oc_core_1_3_empirical_execution_protocols_generated.tex",
    "proof_machinery": ROOT_CONTENT_GENERATED_DIR / "oc_core_1_3_proof_machinery_generated.tex",
    "toe_synthesis": ROOT_CONTENT_GENERATED_DIR / "oc_core_1_3_toe_synthesis_generated.tex",
    "practical_utility": ROOT_CONTENT_GENERATED_DIR / "oc_core_1_3_practical_utility_generated.tex",
    "appendix_matrix": ROOT_APPENDIX_GENERATED_DIR / "oc_core_1_3_empirical_validation_matrix_generated.tex",
    "appendix_proof": ROOT_APPENDIX_GENERATED_DIR / "oc_core_1_3_proof_machinery_appendix_generated.tex",
    "appendix_practical_utility": ROOT_APPENDIX_GENERATED_DIR / "oc_core_1_3_practical_utility_model_comparison_atlas_generated.tex",
}

SOURCE_TEX_TARGETS = {
    "operationalization": SOURCE_CONTENT_GENERATED_DIR / "oc_core_1_3_operationalization_program_generated.tex",
    "protocols": SOURCE_CONTENT_GENERATED_DIR / "oc_core_1_3_empirical_execution_protocols_generated.tex",
    "proof_machinery": SOURCE_CONTENT_GENERATED_DIR / "oc_core_1_3_proof_machinery_generated.tex",
    "toe_synthesis": SOURCE_CONTENT_GENERATED_DIR / "oc_core_1_3_toe_synthesis_generated.tex",
    "practical_utility": SOURCE_CONTENT_GENERATED_DIR / "oc_core_1_3_practical_utility_generated.tex",
    "appendix_matrix": SOURCE_APPENDIX_GENERATED_DIR / "oc_core_1_3_empirical_validation_matrix_generated.tex",
    "appendix_proof": SOURCE_APPENDIX_GENERATED_DIR / "oc_core_1_3_proof_machinery_appendix_generated.tex",
    "appendix_practical_utility": SOURCE_APPENDIX_GENERATED_DIR / "oc_core_1_3_practical_utility_model_comparison_atlas_generated.tex",
}

ROOT_TOE_SUPPORT_TARGETS = {"toe_master": ROOT_TOE_DIR / "toe_master.tex"} | {
    level_id: ROOT_TOE_DIR / f"toe_{level_id.lower()}" for level_id in TOE_LEVEL_IDS
}

SOURCE_TOE_SUPPORT_TARGETS = {"toe_master": SOURCE_TOE_DIR / "toe_master.tex"} | {
    level_id: SOURCE_TOE_DIR / f"toe_{level_id.lower()}" for level_id in TOE_LEVEL_IDS
}

DOMAIN_POLICY = {
    "MATHEMATICS": {
        "scientific_class": "THEOREM_NATIVE",
        "trace_status": "TRACE_COMPLETE",
        "evidence_status": "EVIDENCE_COMPLETE",
        "closure_verdict": "PASS",
        "gap_types": [],
        "scope_role": "core_domain",
        "inclusion_verdict": "INTEGRATED_DOMAIN_THEOREM_NATIVE",
        "promotion_scope_status": "THEOREM_NATIVE_TRACE_CLOSED",
        "claim_level": "VALIDATED_ANCHOR",
        "scientific_state": "THEOREM_NATIVE_ANCHOR",
        "next_required_action": "MAINTAIN_REPLAY_DISCIPLINE",
        "platinum_gate_reason": "Theorem-native anchor lane is trace-closed and replayable.",
        "non_inclusion_reason": "",
        "core_proof_path_branch_ids": [],
    },
    "PHYSICS": {
        "scientific_class": "BRIDGE_ONLY",
        "trace_status": "TRACE_INCOMPLETE_MISSING_DOMAIN_THEOREM",
        "evidence_status": "EVIDENCE_BRIDGE_REPLAY_PRESENT",
        "closure_verdict": "FAIL_CLOSED",
        "gap_types": ["missing theorem", "missing parameter law"],
        "scope_role": "core_domain",
        "inclusion_verdict": "INTEGRATED_DOMAIN_BRIDGE_ONLY",
        "promotion_scope_status": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "claim_level": "BRIDGE_EVIDENCE_ONLY",
        "scientific_state": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "next_required_action": "CLOSE_TRACE_GAPS_AND_RERUN_REPLAY",
        "platinum_gate_reason": "Bounded bridge replay exists on official data, but no standalone theorem-native physics trace has been closed.",
        "non_inclusion_reason": "Bounded bridge replay exists on pinned official datasets, but no source-native standalone physics theorem package or parameter law closes the theorem-to-observable trace.",
        "core_proof_path_branch_ids": [],
    },
    "CHEMISTRY": {
        "scientific_class": "BRIDGE_ONLY",
        "trace_status": "TRACE_INCOMPLETE_MISSING_DOMAIN_THEOREM",
        "evidence_status": "EVIDENCE_BRIDGE_REPLAY_PRESENT",
        "closure_verdict": "FAIL_CLOSED",
        "gap_types": ["missing theorem", "missing parameter law"],
        "scope_role": "core_domain",
        "inclusion_verdict": "INTEGRATED_DOMAIN_BRIDGE_ONLY",
        "promotion_scope_status": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "claim_level": "BRIDGE_EVIDENCE_ONLY",
        "scientific_state": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "next_required_action": "CLOSE_TRACE_GAPS_AND_RERUN_REPLAY",
        "platinum_gate_reason": "Chemistry replay is bounded and useful, but it remains nonpromotable until theorem-native chemistry closure is shown.",
        "non_inclusion_reason": "Bounded chemistry replay exists on pinned thermochemical and spectroscopic references, but no source-native standalone chemistry theorem package or parameter law closes the trace.",
        "core_proof_path_branch_ids": [],
    },
    "BIOLOGY": {
        "scientific_class": "BRIDGE_ONLY",
        "trace_status": "TRACE_INCOMPLETE_MISSING_DOMAIN_THEOREM",
        "evidence_status": "EVIDENCE_BRIDGE_REPLAY_PRESENT",
        "closure_verdict": "FAIL_CLOSED",
        "gap_types": ["missing theorem", "missing parameter law"],
        "scope_role": "core_domain",
        "inclusion_verdict": "INTEGRATED_DOMAIN_BRIDGE_ONLY",
        "promotion_scope_status": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "claim_level": "BRIDGE_EVIDENCE_ONLY",
        "scientific_state": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "next_required_action": "CLOSE_TRACE_GAPS_AND_RERUN_REPLAY",
        "platinum_gate_reason": "Biology replay is bounded and useful, but it remains nonpromotable until theorem-native biological closure is shown.",
        "non_inclusion_reason": "Bounded biological replay exists on frozen signature datasets, but no source-native standalone biology theorem package or parameter law closes the trace.",
        "core_proof_path_branch_ids": [],
    },
    "SYSTEMS_CIVILIZATIONAL_PROJECTION": {
        "scientific_class": "BRIDGE_ONLY",
        "trace_status": "TRACE_INCOMPLETE_MISSING_DOMAIN_THEOREM",
        "evidence_status": "EVIDENCE_BRIDGE_REPLAY_PRESENT",
        "closure_verdict": "FAIL_CLOSED",
        "gap_types": ["missing theorem", "missing parameter law"],
        "scope_role": "core_domain",
        "inclusion_verdict": "INTEGRATED_DOMAIN_BRIDGE_ONLY",
        "promotion_scope_status": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "claim_level": "BRIDGE_EVIDENCE_ONLY",
        "scientific_state": "BRIDGE_ONLY_PENDING_TRACE_CLOSURE",
        "next_required_action": "CLOSE_TRACE_GAPS_AND_RERUN_REPLAY",
        "platinum_gate_reason": "Systems replay is bounded and useful, but it remains nonpromotable until theorem-native K8 systems closure is shown.",
        "non_inclusion_reason": "Bounded systems replay exists on official macro-process series, but no source-native standalone systems theorem package or parameter law closes the trace.",
        "core_proof_path_branch_ids": [],
    },
    "DRT": {
        "scientific_class": "REFUTED",
        "trace_status": "TRACE_EXCLUDED_FROM_CORE",
        "evidence_status": "EVIDENCE_REFUTED_SCOPE_CLOSED",
        "closure_verdict": "FAIL_CLOSED",
        "gap_types": [],
        "scope_role": "branch_only",
        "inclusion_verdict": "REFUTED_AS_NONCANONICAL_ARTIFACT",
        "promotion_scope_status": "REFUTED_SCOPE_CLOSED",
        "claim_level": "REFUTED_SCOPE_ONLY",
        "scientific_state": "REFUTED_SCOPE_CLOSED",
        "next_required_action": "KEEP_EXCLUDED_FROM_CORE",
        "platinum_gate_reason": "Refuted branch remains explicitly excluded from the canonical core proof path.",
        "non_inclusion_reason": "Only isolated draft/source artifact traces are present; no proved OC-native bridge survives as a canonical domain package.",
        "core_proof_path_branch_ids": [],
    },
    "METAONTOLOGY": {
        "scientific_class": "FRAME_ONLY",
        "trace_status": "TRACE_COMPLETE_FRAME_ONLY",
        "evidence_status": "EVIDENCE_FRAME_ONLY_NOT_REQUIRED",
        "closure_verdict": "PASS",
        "gap_types": [],
        "scope_role": "frame_only_domain",
        "inclusion_verdict": "INTEGRATED_CORE_FRAME_ONLY",
        "promotion_scope_status": "CORE_FRAME_ONLY",
        "claim_level": "FRAME_ONLY",
        "scientific_state": "FRAME_ONLY",
        "next_required_action": "MAINTAIN_FRAME_ONLY_BOUNDARY",
        "platinum_gate_reason": "Metaontology remains a core frame and is not itself a standalone empirical promotion lane.",
        "non_inclusion_reason": "",
        "core_proof_path_branch_ids": [],
    },
}

BRANCH_POLICY = {
    "DRT": {
        "branch_title": "DRT",
        "scientific_class": "REFUTED",
        "trace_status": "TRACE_EXCLUDED_FROM_CORE",
        "evidence_status": "EVIDENCE_REFUTED_SCOPE_CLOSED",
        "closure_verdict": "FAIL_CLOSED",
        "core_leakage_policy": "FORBIDDEN",
        "refs": [
            "releases/oc_core_1_3/editorial/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
            "releases/oc_core_1_3/editorial/DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json",
        ],
    },
    "METAONTOLOGY": {
        "branch_title": "Metaontology",
        "scientific_class": "FRAME_ONLY",
        "trace_status": "TRACE_COMPLETE_FRAME_ONLY",
        "evidence_status": "EVIDENCE_FRAME_ONLY_NOT_REQUIRED",
        "closure_verdict": "PASS",
        "core_leakage_policy": "FRAME_ONLY_ALLOWED",
        "refs": [
            "content/18_oc_core_1_3_source_audit.tex",
            "content/19_oc_core_1_3_foundational_consistency.tex",
        ],
    },
    "ESTRA_EA_EXTENSIONS": {
        "branch_title": "ESTRA / EA extensions",
        "scientific_class": "EXTENSION",
        "trace_status": "TRACE_EXTENSION_ONLY",
        "evidence_status": "EVIDENCE_EXTENSION_NOT_CORE",
        "closure_verdict": "FAIL_CLOSED",
        "core_leakage_policy": "FORBIDDEN",
        "refs": [
            "releases/oc_core_1_3/assets/TABLE_01_CROSS_DOMAIN_PROJECTION_MAP_latest.md",
            "content/18_oc_core_1_3_source_audit.tex",
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_sha(repo_root: Path) -> str:
    try:
        return (
            subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )
    except Exception:
        return "UNKNOWN"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    return load_json(path)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def dump_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def slugify_identifier(value: str) -> str:
    slug = []
    for char in value.lower():
        if char.isalnum():
            slug.append(char)
        else:
            slug.append("_")
    normalized = "".join(slug)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def closure_bundle_package_dir(claim_id: str) -> Path:
    return CLOSURE_BUNDLE_DOSSIER_DIR / slugify_identifier(claim_id)


def hostile_review_package_dir(review_id: str) -> Path:
    return HOSTILE_REVIEW_DOSSIER_DIR / slugify_identifier(review_id)


def closure_bundle_source_file(claim_id: str) -> Path:
    return SCIENCE_SOURCE_CLOSURE_BUNDLE_DIR / slugify_identifier(claim_id) / "bundle.json"


def hostile_review_source_file(review_id: str) -> Path:
    return SCIENCE_SOURCE_HOSTILE_REVIEW_DIR / f"{slugify_identifier(review_id)}.json"


def k_level_source_file(level_id: str) -> Path:
    return SCIENCE_SOURCE_K_LEVEL_DIR / f"{level_id.lower()}.json"


def serious_model_comparison_source_file() -> Path:
    return SCIENCE_SOURCE_SERIOUS_MODEL_COMPARISON_FILE


SCIENCE_SOURCE_BUNDLE_REQUIRED_FIELDS = [
    "claim_id",
    "domain_id",
    "scientific_class",
    "trace_status",
    "evidence_status",
    "closure_verdict",
    "gap_types",
    "claim_level",
    "scientific_state",
    "next_required_action",
    "inclusion_verdict",
    "promotion_scope_status",
    "minimum_theorem_native_claim",
    "parameter_law_target",
    "artifact_statuses",
    "artifacts",
]

SCIENCE_SOURCE_ARTIFACT_FIELD_MAP = {
    "theorem_packet": ["status", "exact_formal_statement", "premises", "derivation_steps", "excluded_dependencies", "scope_boundary"],
    "parameter_law_packet": [
        "status",
        "symbols",
        "units",
        "regime",
        "asymptotics",
        "sign_order_constraints",
        "collapse_boundary",
        "forbidden_rubberization",
    ],
    "observable_binding_spec": [
        "status",
        "theorem_to_observable_map",
        "observable_ids",
        "units_by_observable",
        "dataset_field_bindings",
    ],
    "dataset_data_route_manifest": [
        "status",
        "official_route_ids",
        "pinned_dataset_ids",
        "pinned_dataset_versions",
        "split_lock",
    ],
    "held_out_replay_spec": [
        "status",
        "calibration_case_ids",
        "held_out_case_ids",
        "acceptance_metrics",
        "no_post_hoc_split_rule",
        "acceptance_criterion",
    ],
    "falsifier_ledger": ["status", "falsifier_classes", "kill_conditions", "boundary_statement"],
    "counterexample_ledger": ["status", "attempted_counterexamples", "current_survivors", "resolution_state"],
    "same_claim_class_comparator_ledger": ["status", "comparator_families", "complexity_budget", "verdict"],
}

SCIENCE_SOURCE_HOSTILE_REVIEW_REQUIRED_FIELDS = [
    "review_id",
    "current_status",
    "blocks_global_pass",
    "challenge_statement",
    "exact_theorem_route_under_attack",
    "premises",
    "forbidden_shortcuts",
    "formal_argument_body",
    "falsifier_conditions",
    "exit_criterion",
    "resolution_outcome",
    "refs",
]

SCIENCE_SOURCE_K_LEVEL_REQUIRED_FIELDS = [
    "level_id",
    "scientific_class",
    "trace_status",
    "evidence_status",
    "closure_verdict",
    "theorem_schema",
    "benchmark",
    "prediction_interface_status",
    "projected_domain_ids",
    "falsifier",
    "title",
    "toe_file_ref",
    "appendix_table_label",
    "theorem_native_claim",
    "operator_binding_summary",
    "parameter_law_display",
    "observable_map_summary",
    "synthetic_observable_ids",
    "numerical_rows",
    "collapse_boundary",
    "refs",
]


def load_science_source_corpus(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    bundle_ids = CORE_DOMAIN_IDS + ["METAONTOLOGY", "LOAD_BEARING_SPINE", "K11_K12_IRREDUCIBILITY"]
    review_ids = [row["review_id"] for row in HOSTILE_REVIEW_BACKLOG_ROWS]
    corpus: dict[str, Any] = {
        "root_dir": repo_root / "releases" / "oc_core_1_3" / "editorial" / "science_sources",
        "closure_bundles": {},
        "hostile_review": {},
        "k_levels": {},
        "serious_model_comparison_catalog": {},
        "missing_bundle_ids": [],
        "missing_review_ids": [],
        "missing_k_levels": [],
        "missing_serious_model_comparison_catalog": False,
    }
    for claim_id in bundle_ids:
        path = repo_root / repo_rel(closure_bundle_source_file(claim_id))
        payload = load_json_if_exists(path)
        if payload is None:
            corpus["missing_bundle_ids"].append(claim_id)
            continue
        payload["source_file_ref"] = repo_rel(path)
        corpus["closure_bundles"][claim_id] = payload
    for review_id in review_ids:
        path = repo_root / repo_rel(hostile_review_source_file(review_id))
        payload = load_json_if_exists(path)
        if payload is None:
            corpus["missing_review_ids"].append(review_id)
            continue
        payload["source_file_ref"] = repo_rel(path)
        corpus["hostile_review"][review_id] = payload
    for level_id in TOE_LEVEL_IDS:
        path = repo_root / repo_rel(k_level_source_file(level_id))
        payload = load_json_if_exists(path)
        if payload is None:
            corpus["missing_k_levels"].append(level_id)
            continue
        payload["source_file_ref"] = repo_rel(path)
        corpus["k_levels"][level_id] = payload
    comparison_path = repo_root / repo_rel(serious_model_comparison_source_file())
    comparison_payload = load_json_if_exists(comparison_path)
    if comparison_payload is None:
        corpus["missing_serious_model_comparison_catalog"] = True
    else:
        comparison_payload["source_file_ref"] = repo_rel(comparison_path)
        corpus["serious_model_comparison_catalog"] = comparison_payload
    return corpus


def validate_science_source_corpus(corpus: dict[str, Any], repo_root: Path | None = None) -> list[str]:
    repo_root = repo_root or REPO_ROOT
    errors: list[str] = []
    for claim_id in corpus.get("missing_bundle_ids", []):
        errors.append(f"Missing science source closure bundle: {repo_rel(closure_bundle_source_file(claim_id))}")
    for review_id in corpus.get("missing_review_ids", []):
        errors.append(f"Missing science source hostile review: {repo_rel(hostile_review_source_file(review_id))}")
    for level_id in corpus.get("missing_k_levels", []):
        errors.append(f"Missing science source K-level file: {repo_rel(k_level_source_file(level_id))}")
    if corpus.get("missing_serious_model_comparison_catalog"):
        errors.append(f"Missing practical-utility comparison catalog: {repo_rel(serious_model_comparison_source_file())}")
    for claim_id, payload in corpus.get("closure_bundles", {}).items():
        for field in SCIENCE_SOURCE_BUNDLE_REQUIRED_FIELDS:
            if field not in payload:
                errors.append(f"{payload.get('source_file_ref', claim_id)}: missing field {field}")
        artifact_statuses = payload.get("artifact_statuses", {})
        artifacts = payload.get("artifacts", {})
        if set(artifact_statuses.keys()) != set(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{payload.get('source_file_ref', claim_id)}: artifact_statuses must cover the canonical eight-artifact contract")
        if set(artifacts.keys()) != set(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{payload.get('source_file_ref', claim_id)}: artifacts must cover the canonical eight-artifact contract")
        for artifact_kind, required_fields in SCIENCE_SOURCE_ARTIFACT_FIELD_MAP.items():
            artifact_payload = artifacts.get(artifact_kind, {})
            for field in required_fields:
                if field not in artifact_payload:
                    errors.append(f"{payload.get('source_file_ref', claim_id)}:{artifact_kind}: missing field {field}")
        if claim_id in CORE_DOMAIN_IDS:
            practical_rows = payload.get("practical_use_rows")
            playbooks = payload.get("operational_playbooks")
            if not isinstance(practical_rows, list) or not practical_rows:
                errors.append(f"{payload.get('source_file_ref', claim_id)}: core-domain bundles must declare non-empty practical_use_rows")
            else:
                for index, row in enumerate(practical_rows):
                    for field in PRACTICAL_USE_REQUIRED_FIELDS:
                        if field not in row:
                            errors.append(f"{payload.get('source_file_ref', claim_id)}:practical_use_rows[{index}]: missing field {field}")
                    if row.get("support_class") not in PRACTICAL_SUPPORT_CLASS_ORDER:
                        errors.append(
                            f"{payload.get('source_file_ref', claim_id)}:practical_use_rows[{index}]: illegal support_class {row.get('support_class')}"
                        )
                    for ref in row.get("trace_refs", []):
                        assert_ref_exists(repo_root, ref, errors)
            if not isinstance(playbooks, list) or not playbooks:
                errors.append(f"{payload.get('source_file_ref', claim_id)}: core-domain bundles must declare non-empty operational_playbooks")
            else:
                for index, row in enumerate(playbooks):
                    for field in PRACTICAL_PLAYBOOK_REQUIRED_FIELDS:
                        if field not in row:
                            errors.append(f"{payload.get('source_file_ref', claim_id)}:operational_playbooks[{index}]: missing field {field}")
                    if row.get("support_class") not in PRACTICAL_SUPPORT_CLASS_ORDER:
                        errors.append(
                            f"{payload.get('source_file_ref', claim_id)}:operational_playbooks[{index}]: illegal support_class {row.get('support_class')}"
                        )
                    for ref in row.get("trace_refs", []):
                        assert_ref_exists(repo_root, ref, errors)
        for ref in payload.get("refs", []):
            assert_ref_exists(repo_root, ref, errors)
    for review_id, payload in corpus.get("hostile_review", {}).items():
        for field in SCIENCE_SOURCE_HOSTILE_REVIEW_REQUIRED_FIELDS:
            if field not in payload:
                errors.append(f"{payload.get('source_file_ref', review_id)}: missing field {field}")
        for ref in payload.get("refs", []):
            assert_ref_exists(repo_root, ref, errors)
    comparison_catalog = corpus.get("serious_model_comparison_catalog", {})
    if comparison_catalog:
        for field in ["catalog_id", "comparison_scope", "relationship_values", "rows"]:
            if field not in comparison_catalog:
                errors.append(f"{comparison_catalog.get('source_file_ref', 'serious_model_comparison_catalog')}: missing field {field}")
        if set(comparison_catalog.get("relationship_values", [])) != set(SERIOUS_MODEL_RELATIONSHIP_VALUES):
            errors.append("Serious model comparison catalog must declare the canonical relationship values")
        rows = comparison_catalog.get("rows", [])
        if not isinstance(rows, list) or not rows:
            errors.append("Serious model comparison catalog must declare non-empty rows")
        for index, row in enumerate(rows):
            for field in SERIOUS_MODEL_COMPARISON_REQUIRED_FIELDS:
                if field not in row:
                    errors.append(f"{comparison_catalog.get('source_file_ref', 'serious_model_comparison_catalog')}:rows[{index}]: missing field {field}")
            if row.get("relationship_to_oc") not in SERIOUS_MODEL_RELATIONSHIP_VALUES:
                errors.append(
                    f"{comparison_catalog.get('source_file_ref', 'serious_model_comparison_catalog')}:rows[{index}]: illegal relationship_to_oc {row.get('relationship_to_oc')}"
                )
            for ref in row.get("source_refs", []):
                assert_ref_exists(repo_root, ref, errors)
    for level_id, payload in corpus.get("k_levels", {}).items():
        for field in SCIENCE_SOURCE_K_LEVEL_REQUIRED_FIELDS:
            if field not in payload:
                errors.append(f"{payload.get('source_file_ref', level_id)}: missing field {field}")
        for ref in payload.get("refs", []):
            assert_ref_exists(repo_root, ref, errors)
    return errors


def artifact_status_is_transition_blocker(status: str) -> bool:
    return status.startswith("MISSING") or status.startswith("PENDING") or status in {
        "ACTIVE_REDUCTION_SEARCH",
        "ACTIVE_COUNTEREXAMPLE_SEARCH_OPEN",
    }


def bundle_current_transition_gate(closure_verdict: str, artifacts: dict[str, str]) -> str:
    if closure_verdict == "PASS":
        return "MAINTENANCE_ONLY"
    for artifact_kind in CLOSURE_ARTIFACT_ORDER:
        status = artifacts.get(artifact_kind, "")
        if artifact_status_is_transition_blocker(status):
            return f"{artifact_kind.upper()}_PENDING"
    return "FAIL_CLOSED_REAUDIT_REQUIRED"


def rows_by_domain(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["domain_id"]: row for row in rows}


def load_input_bundle(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    editorial_dir = repo_root / "releases" / "oc_core_1_3" / "editorial"
    foundational = load_json(editorial_dir / "FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json")
    protocols = load_json(editorial_dir / "DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json")
    matrix = load_json(editorial_dir / "EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json")
    command_board = load_json(editorial_dir / "DOMAIN_HARD_CLOSURE_COMMAND_BOARD_latest.json")
    numerical = load_json(editorial_dir / "DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json")
    external = load_json(editorial_dir / "DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json")
    replay = load_json(editorial_dir / "PREDICTION_REPLAY_LEDGER_latest.json")
    science_sources = load_science_source_corpus(repo_root)
    return {
        "foundational": foundational,
        "foundational_rows": rows_by_domain(foundational["domain_boundary_rows"]),
        "k_level_doctrine": foundational["k_level_doctrine"],
        "protocols": protocols,
        "protocol_rows": rows_by_domain(protocols["rows"]),
        "matrix": matrix,
        "matrix_rows": rows_by_domain(matrix["rows"]),
        "command_board": command_board,
        "command_rows": rows_by_domain(command_board["rows"]),
        "numerical": numerical,
        "numerical_rows": rows_by_domain(numerical["rows"]),
        "external": external,
        "external_rows": rows_by_domain(external["rows"]),
        "replay": replay,
        "replay_rows": rows_by_domain(replay["rows"]),
        "science_sources": science_sources,
    }


def k_level_file_key(level_id: str) -> str:
    return level_id[1:].lower()


def build_level_refs(level_id: str) -> list[str]:
    suffix = k_level_file_key(level_id)
    return [
        f"content/k_levels/k{suffix}.tex",
        f"content/predictions/predictions_k{suffix}.tex",
        f"content/falsifiability/falsifiability_k{suffix}.tex",
        f"content/processes/processes_k{suffix}.tex",
        f"content/experiments/experiments_k{suffix}.tex",
    ]


def build_domain_theorem_refs(primary_k_levels: list[str]) -> list[str]:
    refs = [
        "content/03_model.tex",
        "content/10_klevels_full.tex",
        "content/11_operators_full.tex",
        "content/theorems_master.tex",
        "content/predictions/predictions_master.tex",
        "content/falsifiability/falsifiability_master.tex",
    ]
    for level_id in primary_k_levels:
        refs.extend(build_level_refs(level_id))
    return unique_strings(refs)


def collect_case_ids(case_metrics: list[dict[str, Any]], held_out_only: bool) -> list[str]:
    case_ids: list[str] = []
    for metric in case_metrics:
        case_id = metric.get("case_id")
        if not case_id:
            continue
        held_out_marker = f"{metric.get('held_out_role', '')} {metric.get('prediction_split_role', '')}".upper()
        is_held_out = "HELD_OUT" in held_out_marker
        if held_out_only and not is_held_out:
            continue
        case_ids.append(case_id)
    return unique_strings(case_ids)


def build_observable_ids(domain_id: str, numerical_row: dict[str, Any]) -> list[str]:
    manifest = numerical_row.get("benchmark_dataset_manifest") or []
    observable_ids: list[str] = []
    for item in manifest:
        observable_name = item.get("observable_name")
        if observable_name:
            observable_ids.append(f"{domain_id}::{observable_name.upper()}")
    if not observable_ids:
        for observable_name in numerical_row.get("measurable_outputs", []):
            observable_ids.append(f"{domain_id}::{observable_name.upper()}")
    return unique_strings(observable_ids)


def build_blocking_ids(domain_id: str, gap_types: list[str]) -> list[str]:
    return [f"{domain_id}__{gap_type.upper().replace(' ', '_')}" for gap_type in gap_types]


def promotion_scope_for(policy: dict[str, Any]) -> str:
    return policy["promotion_scope_status"]


def quantitative_status_for(domain_id: str, policy: dict[str, Any], numerical_row: dict[str, Any]) -> str:
    if domain_id == "MATHEMATICS":
        return numerical_row.get("quantitative_acceptance_result", "PASS_TERMINALIZED_NUMERICAL_REPLAY")
    if policy["scientific_class"] == "BRIDGE_ONLY":
        return "BRIDGE_REPLAY_PRESENT_NONPROMOTABLE"
    if policy["scientific_class"] == "FRAME_ONLY":
        return "NOT_REQUIRED"
    if policy["scientific_class"] == "REFUTED":
        return "NOT_READY"
    return "EXTENSION_SCOPE_ONLY"


def matrix_quantitative_result(domain_id: str, policy: dict[str, Any], domain_record: dict[str, Any]) -> str:
    if domain_id == "MATHEMATICS":
        return "PASS"
    if policy["scientific_class"] == "BRIDGE_ONLY":
        return "BRIDGE_REPLAY_PRESENT_NONPROMOTABLE"
    if policy["scientific_class"] == "FRAME_ONLY":
        return "NOT_REQUIRED"
    return "FAIL_CLOSED"


def build_domain_record(domain_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    policy = DOMAIN_POLICY[domain_id]
    source_bundle = inputs.get("science_sources", {}).get("closure_bundles", {}).get(domain_id, {})
    fcd_row = deepcopy(inputs["foundational_rows"].get(domain_id, {}))
    numerical_row = deepcopy(inputs["numerical_rows"].get(domain_id, {}))
    protocol_row = deepcopy(inputs["protocol_rows"].get(domain_id, {}))
    replay_row = deepcopy(inputs["replay_rows"].get(domain_id, {}))
    matrix_row = deepcopy(inputs["matrix_rows"].get(domain_id, {}))
    command_row = deepcopy(inputs["command_rows"].get(domain_id, {}))
    primary_k_levels = fcd_row.get("primary_k_levels", [])
    case_metrics = replay_row.get("case_metrics", [])
    official_route_refs = protocol_row.get("official_route_refs", [])
    benchmark_manifest = numerical_row.get("benchmark_dataset_manifest", [])
    dataset_ids = unique_strings([item.get("benchmark_id", "") for item in benchmark_manifest])
    if not dataset_ids and numerical_row.get("benchmark"):
        dataset_ids = [numerical_row["benchmark"]]
    blocking_ids = build_blocking_ids(domain_id, policy["gap_types"])
    theorem_refs = build_domain_theorem_refs(primary_k_levels)
    observable_ids = build_observable_ids(domain_id, numerical_row)
    metric_summary = deepcopy(protocol_row.get("official_metrics_summary", {}))
    if domain_id == "MATHEMATICS" and not metric_summary:
        metric_summary = deepcopy(numerical_row.get("validation_evidence", {}))
    result = {
        "domain_id": domain_id,
        "domain_title": source_bundle.get("domain_title")
        or fcd_row.get("domain_title")
        or numerical_row.get("domain_title")
        or protocol_row.get("domain_title")
        or domain_id,
        "scope_role": policy["scope_role"],
        "scientific_class": policy["scientific_class"],
        "trace_status": policy["trace_status"],
        "evidence_status": policy["evidence_status"],
        "closure_verdict": policy["closure_verdict"],
        "gap_types": policy["gap_types"],
        "gap_ids": blocking_ids,
        "classification_rationale": policy["platinum_gate_reason"],
        "claim_level": policy["claim_level"],
        "scientific_state": policy["scientific_state"],
        "primary_k_levels": primary_k_levels,
        "theorem_refs": theorem_refs,
        "root_operator_refs": [
            "content/03_model.tex",
            "content/10_klevels_full.tex",
            "content/11_operators_full.tex",
        ],
        "observable_ids": observable_ids,
        "dataset_ids": dataset_ids,
        "held_out_case_ids": collect_case_ids(case_metrics, held_out_only=True),
        "declared_case_ids": collect_case_ids(case_metrics, held_out_only=False),
        "falsifier_refs": unique_strings(
            [
                "content/falsifiability/falsifiability_master.tex",
                *[f"content/falsifiability/falsifiability_k{k_level_file_key(level_id)}.tex" for level_id in primary_k_levels],
            ]
        ),
        "metric_summary": metric_summary,
        "benchmark": numerical_row.get("benchmark", ""),
        "benchmark_families": numerical_row.get("benchmark_families", []),
        "benchmark_dataset_manifest": benchmark_manifest,
        "measurable_outputs": numerical_row.get("measurable_outputs", []),
        "measurement_schema": numerical_row.get("measurement_schema", ""),
        "acceptance_criterion": numerical_row.get("acceptance_criterion", command_row.get("acceptance_criterion", "")),
        "falsifier_specification": numerical_row.get("falsifier_specification", command_row.get("falsifier_specification", "")),
        "measurement_escalation_rule": numerical_row.get("measurement_escalation_rule", ""),
        "next_required_action": policy["next_required_action"],
        "nonclaim_boundary": numerical_row.get("nonclaim_boundary", ""),
        "theorem_to_observable_map": numerical_row.get("theorem_to_observable_map", []),
        "official_route_refs": official_route_refs,
        "selected_route_institutions": unique_strings([route.get("institution", "") for route in official_route_refs]),
        "official_source_status": protocol_row.get("official_source_status", "NOT_REQUIRED"),
        "numerical_packet_status": numerical_row.get("numerical_packet_status", protocol_row.get("numerical_packet_status", "NOT_REQUIRED")),
        "quantitative_packet_status": numerical_row.get("quantitative_packet_status", ""),
        "prediction_contract_status": numerical_row.get("prediction_contract_status", ""),
        "validation_evidence": numerical_row.get("validation_evidence", {}),
        "quantitative_acceptance_result": numerical_row.get("quantitative_acceptance_result", ""),
        "benchmark_wave_id": protocol_row.get("benchmark_wave_id", ""),
        "benchmark_design": protocol_row.get("benchmark_design", {}),
        "evidence_bar": protocol_row.get("evidence_bar", "HYBRID_ESCALATION"),
        "protocol_id": protocol_row.get("protocol_id", ""),
        "execution_basis_class": protocol_row.get("execution_basis_class", ""),
        "execution_scope": protocol_row.get("execution_scope", ""),
        "replay_harness": protocol_row.get("replay_harness", {}),
        "replay_status": protocol_row.get("replay_status", replay_row.get("replay_status", "NOT_REQUIRED")),
        "quantitative_acceptance_thresholds": protocol_row.get("quantitative_acceptance_thresholds", {}),
        "official_coverage_summary": protocol_row.get("official_coverage_summary", {}),
        "official_metrics_summary": protocol_row.get("official_metrics_summary", {}),
        "institute_run_escalation": protocol_row.get("institute_run_escalation", {}),
        "matrix_snapshot": {
            "benchmark_case_total": matrix_row.get("benchmark_case_total", replay_row.get("benchmark_case_total", 0)),
            "benchmark_dataset_total": matrix_row.get("benchmark_dataset_total", len(dataset_ids)),
            "case_coverage_ratio": matrix_row.get("case_coverage_ratio", replay_row.get("case_coverage_ratio", 0.0)),
            "prediction_declared_case_total": matrix_row.get("prediction_declared_case_total", 0),
            "minimum_cases_total": matrix_row.get("minimum_cases_total", protocol_row.get("benchmark_design", {}).get("minimum_cases_total", 0)),
        },
        "inclusion_verdict": policy["inclusion_verdict"],
        "promotion_scope_status": promotion_scope_for(policy),
        "quantitative_validation_status": quantitative_status_for(domain_id, policy, numerical_row),
        "non_inclusion_reason": policy["non_inclusion_reason"],
        "nonclaim_refs": fcd_row.get("nonclaim_refs", []),
        "core_proof_path_branch_ids": policy["core_proof_path_branch_ids"],
        "source_refs": unique_strings(
            [
                *fcd_row.get("refs", []),
                *numerical_row.get("refs", []),
                *protocol_row.get("refs", []),
                *replay_row.get("refs", []),
            ]
        ),
    }
    if source_bundle:
        for field in [
            "scope_role",
            "scientific_class",
            "trace_status",
            "evidence_status",
            "closure_verdict",
            "gap_types",
            "classification_rationale",
            "claim_level",
            "scientific_state",
            "next_required_action",
            "inclusion_verdict",
            "promotion_scope_status",
            "non_inclusion_reason",
            "theorem_refs",
            "root_operator_refs",
            "observable_ids",
            "dataset_ids",
            "held_out_case_ids",
            "declared_case_ids",
            "falsifier_refs",
            "benchmark",
            "benchmark_families",
            "benchmark_dataset_manifest",
            "measurable_outputs",
            "measurement_schema",
            "acceptance_criterion",
            "falsifier_specification",
            "measurement_escalation_rule",
            "theorem_to_observable_map",
            "official_route_refs",
            "selected_route_institutions",
            "official_source_status",
            "numerical_packet_status",
            "quantitative_packet_status",
            "prediction_contract_status",
            "validation_evidence",
            "quantitative_acceptance_result",
            "benchmark_wave_id",
            "benchmark_design",
            "evidence_bar",
            "protocol_id",
            "execution_basis_class",
            "execution_scope",
            "replay_harness",
            "replay_status",
            "quantitative_acceptance_thresholds",
            "official_coverage_summary",
            "official_metrics_summary",
            "institute_run_escalation",
            "matrix_snapshot",
            "quantitative_validation_status",
            "nonclaim_refs",
            "core_proof_path_branch_ids",
        ]:
            if field in source_bundle:
                result[field] = deepcopy(source_bundle[field])
        result["gap_ids"] = build_blocking_ids(domain_id, result.get("gap_types", []))
        result["source_bundle_ref"] = source_bundle.get("source_file_ref", "")
        result["source_refs"] = unique_strings([source_bundle.get("source_file_ref", ""), *source_bundle.get("refs", []), *result["source_refs"]])
    return result


def build_kernel() -> dict[str, Any]:
    return {
        "kernel_id": "OC_CORE_1_3_ROOT_KERNEL",
        "scientific_class": "THEOREM_NATIVE",
        "trace_status": "TRACE_COMPLETE",
        "evidence_status": "EVIDENCE_COMPLETE",
        "closure_verdict": "PASS",
        "metamodel_summary": "OC Core 1.3 carries the root metamodel, operator family, K-level hierarchy, theorem grammar, prediction grammar, and falsifiability grammar as one source-first kernel.",
        "operator_family": ["F", "G", "H", "Q", "R", "S", "U"],
        "root_refs": [
            "content/03_model.tex",
            "content/10_klevels_full.tex",
            "content/11_operators_full.tex",
            "content/theorems_master.tex",
            "content/predictions/predictions_master.tex",
            "content/falsifiability/falsifiability_master.tex",
            "content/19_oc_core_1_3_foundational_consistency.tex",
            "content/20_oc_core_1_3_theorem_roadmap.tex",
            "content/21_oc_core_1_3_worked_examples.tex",
        ],
        "revision_policy": "DERIVED_FIRST",
        "root_revision_status": "LOCKED_PENDING_ACCUMULATED_CROSS_DOMAIN_FAILURE",
    }


def build_k_levels(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    levels: list[dict[str, Any]] = []
    for row in inputs["k_level_doctrine"]:
        level_id = row["level_id"]
        source_level = inputs.get("science_sources", {}).get("k_levels", {}).get(level_id, {})
        refs = unique_strings([*source_level.get("refs", []), *row.get("refs", []), *build_level_refs(level_id)])
        levels.append(
            {
                "level_id": level_id,
                "scientific_class": source_level.get("scientific_class", "THEOREM_NATIVE"),
                "trace_status": source_level.get("trace_status", "TRACE_COMPLETE"),
                "evidence_status": source_level.get("evidence_status", "EVIDENCE_COMPLETE"),
                "closure_verdict": source_level.get("closure_verdict", "PASS" if row.get("theorem_packet_status") == "PASS" else "FAIL_CLOSED"),
                "theorem_schema": source_level.get("theorem_schema", row.get("theorem_schema", "")),
                "benchmark": source_level.get("benchmark", row.get("benchmark", "")),
                "prediction_interface_status": source_level.get("prediction_interface_status", row.get("prediction_interface_status", "")),
                "projected_domain_ids": source_level.get("projected_domain_ids", row.get("projected_domain_ids", [])),
                "falsifier": source_level.get("falsifier", row.get("falsifier", "")),
                "toe_spec": {
                    "title": source_level.get("title", TOE_LEVEL_SPECS[level_id]["title"]),
                    "toe_file_ref": source_level.get("toe_file_ref", TOE_LEVEL_SPECS[level_id]["toe_file_ref"]),
                    "appendix_table_label": source_level.get("appendix_table_label", TOE_LEVEL_SPECS[level_id]["appendix_table_label"]),
                    "theorem_native_claim": source_level.get("theorem_native_claim", TOE_LEVEL_SPECS[level_id]["theorem_native_claim"]),
                    "operator_binding_summary": source_level.get("operator_binding_summary", TOE_LEVEL_SPECS[level_id]["operator_binding_summary"]),
                    "parameter_law_display": source_level.get("parameter_law_display", TOE_LEVEL_SPECS[level_id]["parameter_law_display"]),
                    "observable_map_summary": source_level.get("observable_map_summary", TOE_LEVEL_SPECS[level_id]["observable_map_summary"]),
                    "synthetic_observable_ids": deepcopy(source_level.get("synthetic_observable_ids", TOE_LEVEL_SPECS[level_id]["synthetic_observable_ids"])),
                    "numerical_rows": deepcopy(source_level.get("numerical_rows", TOE_LEVEL_SPECS[level_id]["numerical_rows"])),
                    "collapse_boundary": source_level.get("collapse_boundary", TOE_LEVEL_SPECS[level_id]["collapse_boundary"]),
                },
                "refs": refs,
            }
        )
    return levels


def build_theorem_spine(domain_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spine: list[dict[str, Any]] = [
        {
            "spine_id": "ROOT::MODEL_AND_OPERATORS",
            "scientific_class": "THEOREM_NATIVE",
            "trace_status": "TRACE_COMPLETE",
            "evidence_status": "EVIDENCE_COMPLETE",
            "closure_verdict": "PASS",
            "summary": "Root metamodel and operator family constrain lawful projections from contradiction load to collapse or lift.",
            "refs": [
                "content/03_model.tex",
                "content/11_operators_full.tex",
            ],
            "projected_domain_ids": ["ALL"],
        },
        {
            "spine_id": "ROOT::K_LEVEL_HIERARCHY",
            "scientific_class": "THEOREM_NATIVE",
            "trace_status": "TRACE_COMPLETE",
            "evidence_status": "EVIDENCE_COMPLETE",
            "closure_verdict": "PASS",
            "summary": "K0--K12 hierarchy remains the formal topology that all domain projections must trace through explicitly.",
            "refs": [
                "content/10_klevels_full.tex",
                "content/19_oc_core_1_3_foundational_consistency.tex",
                "content/20_oc_core_1_3_theorem_roadmap.tex",
            ],
            "projected_domain_ids": ["ALL"],
        },
        {
            "spine_id": "ROOT::PREDICTION_AND_FALSIFIABILITY_GRAMMAR",
            "scientific_class": "THEOREM_NATIVE",
            "trace_status": "TRACE_COMPLETE",
            "evidence_status": "EVIDENCE_COMPLETE",
            "closure_verdict": "PASS",
            "summary": "Prediction grammar and falsifiability grammar stay canonical, but empirical promotion remains gated by theorem-native trace closure.",
            "refs": [
                "content/predictions/predictions_master.tex",
                "content/falsifiability/falsifiability_master.tex",
            ],
            "projected_domain_ids": ["ALL"],
        },
    ]
    for domain in domain_registry:
        spine.append(
            {
                "spine_id": f"DOMAIN::{domain['domain_id']}::TRACE_ROUTE",
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "summary": domain["classification_rationale"],
                "refs": domain["theorem_refs"],
                "projected_domain_ids": [domain["domain_id"]],
            }
        )
    return spine


def build_observable_registry(domain_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observables: list[dict[str, Any]] = []
    for domain in domain_registry:
        if not domain["observable_ids"]:
            continue
        dataset_cycle = domain["dataset_ids"] or [domain["benchmark"] or domain["domain_id"]]
        falsifier_refs = domain["falsifier_refs"]
        for index, observable_id in enumerate(domain["observable_ids"]):
            dataset_id = dataset_cycle[min(index, len(dataset_cycle) - 1)] if dataset_cycle else domain["domain_id"]
            observables.append(
                {
                    "observable_id": observable_id,
                    "domain_id": domain["domain_id"],
                    "scientific_class": domain["scientific_class"],
                    "trace_status": domain["trace_status"],
                    "evidence_status": domain["evidence_status"],
                    "closure_verdict": domain["closure_verdict"],
                    "dataset_ids": [dataset_id],
                    "k_level_refs": domain["primary_k_levels"],
                    "theorem_refs": domain["theorem_refs"],
                    "falsifier_refs": falsifier_refs,
                }
            )
    return observables


def toe_release_candidate_summary(
    domain_registry: list[dict[str, Any]],
    hostile_review_backlog: list[dict[str, Any]],
    unified_science_atlas: dict[str, Any],
) -> dict[str, Any]:
    empirical_domains = [domain for domain in domain_registry if domain["domain_id"] in CORE_DOMAIN_IDS[1:]]
    blockers: list[str] = []
    if any(domain["scientific_class"] == "BRIDGE_ONLY" for domain in domain_registry if domain["domain_id"] in CORE_DOMAIN_IDS):
        blockers.append("BRIDGE_ONLY_DOMAINS_REMAIN")
    if any(domain["closure_verdict"] != "PASS" for domain in empirical_domains):
        blockers.append("EMPIRICAL_CORE_DOMAINS_NOT_PASS")
    if any(not domain.get("held_out_case_ids") for domain in empirical_domains):
        blockers.append("HELD_OUT_PREDICTION_TABLES_MISSING")
    if any(item["blocks_global_pass"] and item["current_status"] != "PASS" for item in hostile_review_backlog):
        blockers.append("HOSTILE_REVIEW_BLOCKERS_OPEN")
    if unified_science_atlas["atlas_status"] != "PASS":
        blockers.append("UNIFIED_ATLAS_NOT_PASS")
    return {
        "status": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "reason": "Final unified-science promotion is valid only when every core empirical domain is theorem-native, held-out prediction tables are present, hostile-review blockers are closed, and the unified atlas passes.",
    }


def toe_branding_payload(status: str) -> dict[str, Any]:
    if status == "PASS":
        return {
            "branding_mode": "STRICT_TOE_PROMOTED",
            "public_chapter_title": "Unified Science Synthesis",
            "public_surface_label": "Unified synthesis surface",
            "public_status_label": "Final unified-synthesis release status",
            "public_gate_title": "Final Unified Synthesis Release Gate",
            "public_intro_text": (
                "This chapter states the promoted synthesis projected from the canonical science SPOT. "
                "It gives the lawfully promoted unified synthesis with explicit K0--K12 parameter laws, numerical rows, falsifiers, and empirical held-out prediction summaries."
            ),
            "public_empirical_summary_text": (
                "The following summary records the empirical synthesis lanes that have already cleared theorem-native promotion and held-out prediction review."
            ),
            "optimistic_toe_naming_allowed": True,
        }
    return {
        "branding_mode": "DEMOTED_CLOSURE_ATTEMPT",
        "public_chapter_title": "Unified Science Closure Attempt",
        "public_surface_label": "Unified-science closure surface",
        "public_status_label": "Current fail-closed closure status",
        "public_gate_title": "Final Promotion Gate",
        "public_intro_text": (
            "This chapter states the strongest synthesis projected from the canonical science SPOT. "
            "It exposes the strongest fail-closed unified-science closure attempt the repository can lawfully support at build time, "
            "including explicit K0--K12 parameter laws, numerical rows, falsifiers, and empirical held-out prediction summaries."
        ),
        "public_empirical_summary_text": (
            "The following summary keeps the empirical closure lanes explicit. Final promotion remains blocked until every row below is theorem-native and reports PASS under the canonical SPOT vocabulary."
        ),
        "optimistic_toe_naming_allowed": False,
    }


def toe_level_binding_summary(
    level_row: dict[str, Any],
    domain_registry: list[dict[str, Any]],
    domain_closure_bundles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_map = {domain["domain_id"]: domain for domain in domain_registry}
    bundle_map = {
        bundle["domain_id"]: bundle
        for bundle in domain_closure_bundles
        if bundle.get("bundle_id", "").startswith("CLOSURE_BUNDLE::")
    }
    bindings: list[dict[str, Any]] = []
    for domain_id in level_row.get("projected_domain_ids", []):
        domain = domain_map.get(domain_id)
        if domain is None:
            continue
        bundle = bundle_map.get(domain_id, {})
        bindings.append(
            {
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "observable_ids": domain["observable_ids"],
                "held_out_case_ids": domain["held_out_case_ids"],
                "held_out_case_total": len(domain["held_out_case_ids"]),
                "metric_summary": deepcopy(domain["metric_summary"]),
                "closure_bundle_ref": bundle.get("dossier_package_ref", ""),
                "closure_bundle_id": bundle.get("bundle_id", ""),
                "parameter_law_status": "COMPLETE" if "missing parameter law" not in domain.get("gap_types", []) else "PENDING",
                "theorem_packet_status": "COMPLETE" if "missing theorem" not in domain.get("gap_types", []) else "PENDING",
                "theorem_refs": domain["theorem_refs"],
                "falsifier_refs": domain["falsifier_refs"],
            }
        )
    return bindings


def build_toe_synthesis_registry(
    kernel: dict[str, Any],
    k_levels: list[dict[str, Any]],
    domain_registry: list[dict[str, Any]],
    domain_closure_bundles: list[dict[str, Any]],
    global_verdict: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    empirical_prediction_rows: list[dict[str, Any]] = []
    branding = toe_branding_payload(global_verdict["toe_release_candidate_status"])
    for domain in domain_registry:
        if domain["domain_id"] not in CORE_DOMAIN_IDS[1:]:
            continue
        bundle = next(
            (
                bundle_row
                for bundle_row in domain_closure_bundles
                if bundle_row.get("domain_id") == domain["domain_id"]
                and bundle_row.get("bundle_id", "").startswith("CLOSURE_BUNDLE::")
            ),
            {},
        )
        empirical_prediction_rows.append(
            {
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "scientific_class": domain["scientific_class"],
                "closure_verdict": domain["closure_verdict"],
                "held_out_case_total": len(domain["held_out_case_ids"]),
                "held_out_case_ids": domain["held_out_case_ids"],
                "metric_summary": deepcopy(domain["metric_summary"]),
                "closure_bundle_ref": bundle.get("dossier_package_ref", ""),
            }
        )
    for level_row in k_levels:
        spec = deepcopy(level_row.get("toe_spec", TOE_LEVEL_SPECS[level_row["level_id"]]))
        domain_bindings = toe_level_binding_summary(level_row, domain_registry, domain_closure_bundles)
        blocking_domain_ids = [
            binding["domain_id"]
            for binding in domain_bindings
            if binding["domain_id"] in CORE_DOMAIN_IDS and binding["closure_verdict"] != "PASS"
        ]
        observable_ids = unique_strings(
            [
                *spec["synthetic_observable_ids"],
                *[
                    observable_id
                    for binding in domain_bindings
                    for observable_id in binding.get("observable_ids", [])
                ],
            ]
        )
        theorem_refs = unique_strings(
            [
                *level_row["refs"],
                spec["toe_file_ref"],
                *[
                    theorem_ref
                    for binding in domain_bindings
                    for theorem_ref in binding.get("theorem_refs", [])
                ],
            ]
        )
        rows.append(
            {
                "level_id": level_row["level_id"],
                "level_title": spec["title"],
                "scientific_class": "THEOREM_NATIVE",
                "trace_status": "TRACE_COMPLETE" if not blocking_domain_ids else "TRACE_COMPLETE_PENDING_BOUND_DOMAIN_CLOSURE",
                "evidence_status": "EVIDENCE_COMPLETE" if not blocking_domain_ids else "EVIDENCE_NUMERICAL_PRESENT_PENDING_DOMAIN_PROMOTION",
                "closure_verdict": "PASS" if level_row["closure_verdict"] == "PASS" and not blocking_domain_ids else "FAIL_CLOSED",
                "theorem_native_claim": spec["theorem_native_claim"],
                "operator_binding_summary": spec["operator_binding_summary"],
                "parameter_law_display": spec["parameter_law_display"],
                "observable_map_summary": spec["observable_map_summary"],
                "theorem_refs": theorem_refs,
                "operator_refs": unique_strings(
                    [
                        "content/03_model.tex",
                        "content/10_klevels_full.tex",
                        "content/11_operators_full.tex",
                        spec["toe_file_ref"],
                    ]
                ),
                "parameter_law_refs": unique_strings([spec["toe_file_ref"], "appendix/toe_data.tex"]),
                "observable_ids": observable_ids,
                "numerical_rows": deepcopy(spec["numerical_rows"]),
                "appendix_table_label": spec["appendix_table_label"],
                "falsifier_summary": level_row["falsifier"],
                "collapse_boundary": spec["collapse_boundary"],
                "falsifier_refs": unique_strings(
                    [
                        spec["toe_file_ref"],
                        *[
                            falsifier_ref
                            for binding in domain_bindings
                            for falsifier_ref in binding.get("falsifier_refs", [])
                        ],
                    ]
                ),
                "domain_bindings": domain_bindings,
                "blocking_domain_ids": blocking_domain_ids,
                "manuscript_anchor_refs": unique_strings(
                    [
                        "content/25_oc_core_1_3_toe_synthesis.tex",
                        "content/generated/oc_core_1_3_toe_synthesis_generated.tex",
                        spec["toe_file_ref"],
                        "appendix/toe_data.tex",
                    ]
                ),
            }
        )
    return {
        "toe_id": "OC_CORE_1_3_UNIFIED_SYNTHESIS",
        "manuscript_target": "ENGLISH_MASTER_MONOGRAPH_ONLY",
        "kernel_ref": kernel["kernel_id"],
        "status": global_verdict["toe_release_candidate_status"],
        "branding": branding,
        "public_chapter_title": branding["public_chapter_title"],
        "public_surface_label": branding["public_surface_label"],
        "optimistic_toe_naming_allowed": branding["optimistic_toe_naming_allowed"],
        "release_candidate_status": global_verdict["toe_release_candidate_status"],
        "release_candidate_blockers": global_verdict["toe_release_candidate_blockers"],
        "release_candidate_reason": global_verdict["toe_release_candidate_reason"],
        "bridge_only_domain_total": global_verdict["bridge_only_domain_total"],
        "hostile_review_blocking_total": global_verdict["hostile_review_blocking_total"],
        "integrability_suite_status": global_verdict["integrability_suite_status"],
        "acceptance_rule": "Final unified-science promotion requires every empirical core domain to be theorem-native. It also requires zero bridge-only domains, a passed atlas, a resolved hostile-review backlog, and explicit K0--K12 numerical presentation.",
        "k_level_rows": rows,
        "empirical_prediction_rows": empirical_prediction_rows,
    }


def practical_support_sort_key(support_class: str) -> int:
    try:
        return PRACTICAL_SUPPORT_CLASS_ORDER.index(support_class)
    except ValueError:
        return len(PRACTICAL_SUPPORT_CLASS_ORDER)


def practical_support_label(support_class: str) -> str:
    return PRACTICAL_SUPPORT_CLASS_LABELS.get(support_class, support_class.lower().replace("_", " "))


def build_practical_utility_atlas(
    domain_registry: list[dict[str, Any]],
    domain_closure_bundles: list[dict[str, Any]],
    global_verdict: dict[str, Any],
    unified_science_atlas: dict[str, Any],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    source_bundles = inputs.get("science_sources", {}).get("closure_bundles", {})
    comparison_catalog = inputs.get("science_sources", {}).get("serious_model_comparison_catalog", {})
    domain_map = {domain["domain_id"]: domain for domain in domain_registry}
    closure_bundle_map = {
        bundle["domain_id"]: bundle
        for bundle in domain_closure_bundles
        if bundle.get("bundle_id", "").startswith("CLOSURE_BUNDLE::")
    }
    use_case_rows: list[dict[str, Any]] = []
    operational_playbooks: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    for domain_id in CORE_DOMAIN_IDS:
        domain = domain_map.get(domain_id)
        source_bundle = source_bundles.get(domain_id, {})
        if not domain or not source_bundle:
            continue
        closure_bundle = closure_bundle_map.get(domain_id, {})
        comparator_ledger = source_bundle.get("artifacts", {}).get("same_claim_class_comparator_ledger", {})
        baseline_rows.append(
            {
                "comparison_id": f"SAME_CLAIM_CLASS::{domain_id}",
                "domain_id": domain_id,
                "domain_title": domain["domain_title"],
                "comparator_families": deepcopy(comparator_ledger.get("comparator_families", [])),
                "complexity_budget": comparator_ledger.get("complexity_budget", ""),
                "verdict": comparator_ledger.get("verdict", ""),
                "comparison_scope": domain.get("classification_rationale", ""),
                "closure_verdict": domain["closure_verdict"],
                "source_bundle_ref": source_bundle.get("source_file_ref", ""),
                "closure_bundle_ref": closure_bundle.get("dossier_package_ref", ""),
            }
        )
        for row in source_bundle.get("practical_use_rows", []):
            use_case_rows.append(
                {
                    "use_case_id": row["use_case_id"],
                    "domain_id": domain_id,
                    "domain_title": domain["domain_title"],
                    "problem_class": row["problem_class"],
                    "support_class": row["support_class"],
                    "support_label": practical_support_label(row["support_class"]),
                    "usable_now": row["support_class"] in USABLE_NOW_SUPPORT_CLASSES,
                    "what_can_be_predicted_or_done": row["what_can_be_predicted_or_done"],
                    "how_to_apply": row["how_to_apply"],
                    "scope_boundary": row["scope_boundary"],
                    "required_inputs_or_observables": deepcopy(row["required_inputs_or_observables"]),
                    "output_or_decision": row["output_or_decision"],
                    "trace_refs": deepcopy(row["trace_refs"]),
                    "benchmark_comparators": deepcopy(row["benchmark_comparators"]),
                    "serious_model_families": deepcopy(row["serious_model_families"]),
                    "what_remains_open": row["what_remains_open"],
                    "benchmark_families": deepcopy(domain.get("benchmark_families", [])),
                    "held_out_case_total": len(domain.get("held_out_case_ids", [])),
                    "closure_verdict": domain["closure_verdict"],
                    "quantitative_acceptance_result": domain.get("quantitative_acceptance_result", ""),
                    "closure_bundle_ref": closure_bundle.get("dossier_package_ref", ""),
                    "source_bundle_ref": source_bundle.get("source_file_ref", ""),
                }
            )
        for playbook in source_bundle.get("operational_playbooks", []):
            operational_playbooks.append(
                {
                    "playbook_id": playbook["playbook_id"],
                    "domain_id": domain_id,
                    "domain_title": domain["domain_title"],
                    "title": playbook["title"],
                    "when_to_use": playbook["when_to_use"],
                    "required_inputs_or_observables": deepcopy(playbook["required_inputs_or_observables"]),
                    "procedure_steps": deepcopy(playbook["procedure_steps"]),
                    "output_or_decision": playbook["output_or_decision"],
                    "support_class": playbook["support_class"],
                    "support_label": practical_support_label(playbook["support_class"]),
                    "scope_boundary": playbook["scope_boundary"],
                    "trace_refs": deepcopy(playbook["trace_refs"]),
                    "failure_boundary": playbook["failure_boundary"],
                    "closure_verdict": domain["closure_verdict"],
                    "source_bundle_ref": source_bundle.get("source_file_ref", ""),
                    "closure_bundle_ref": closure_bundle.get("dossier_package_ref", ""),
                }
            )
    use_case_rows.append(
        {
            "use_case_id": "UNIFIED_USE_001_CROSS_DOMAIN_ROUTE_SELECTION",
            "domain_id": "CROSS_DOMAIN",
            "domain_title": "Cross-domain / unified science",
            "problem_class": "Cross-domain route selection, escalation discipline, and packet coordination",
            "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
            "support_label": practical_support_label("OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS"),
            "usable_now": global_verdict["closure_verdict"] == "PASS" and unified_science_atlas["atlas_status"] == "PASS",
            "what_can_be_predicted_or_done": "Choose the lawful domain packet, comparator set, and escalation route for a mixed scientific or operational problem without letting rhetoric outrun the closed packet boundary.",
            "how_to_apply": "Map the problem to its measurable observable family, identify the bounded domain packet that already closes that lane, inspect shared operator and invariant constraints, and then run the pinned replay or comparator route before any escalation.",
            "scope_boundary": "This row supports bounded cross-domain routing and coordination only. It does not authorize an unrestricted one-shot universal predictor or universal intervention engine.",
            "required_inputs_or_observables": [
                "declared problem class",
                "target observable family",
                "decision horizon or held-out interval",
                "candidate same-claim baselines",
            ],
            "output_or_decision": "A lawful packet-selection decision, a comparator shortlist, and an explicit escalation path when the closed packet is not enough.",
            "trace_refs": [
                "content/22_oc_core_1_3_operationalization_program.tex",
                "content/23_oc_core_1_3_empirical_execution_protocols.tex",
                "content/24_oc_core_1_3_proof_machinery.tex",
                "content/25_oc_core_1_3_toe_synthesis.tex",
            ],
            "benchmark_comparators": [
                "best-in-class local-model portfolio governance",
                "multi-model expert routing without shared theorem trace",
            ],
            "serious_model_families": [
                "Best-in-class local-model portfolio governance across separate domain theories",
                "Complexity-science and multiscale integration programs",
            ],
            "what_remains_open": "Unrestricted cross-domain intervention planning beyond the declared closed packets remains outside lawful promotion.",
            "benchmark_families": [],
            "held_out_case_total": sum(len(domain.get("held_out_case_ids", [])) for domain in domain_registry if domain["domain_id"] in CORE_DOMAIN_IDS[1:]),
            "closure_verdict": "PASS" if global_verdict["closure_verdict"] == "PASS" else "FAIL_CLOSED",
            "quantitative_acceptance_result": global_verdict["closure_verdict"],
            "closure_bundle_ref": "",
            "source_bundle_ref": "",
        }
    )
    operational_playbooks.append(
        {
            "playbook_id": "UNIFIED_PLAYBOOK_001_ROUTE_SELECTION",
            "domain_id": "CROSS_DOMAIN",
            "domain_title": "Cross-domain / unified science",
            "title": "Cross-domain packet selection and escalation playbook",
            "when_to_use": "Use when a scientific or engineering problem touches more than one domain lane and the team must decide which closed packet, comparator family, and evidence route should govern the next action.",
            "required_inputs_or_observables": [
                "declared target problem class",
                "bounded observable family",
                "candidate domain packets",
                "decision or intervention objective",
            ],
            "procedure_steps": [
                "Map the target problem to the narrowest lawful observable family.",
                "Select the closed packet whose theorem-to-observable map already governs that family.",
                "Check same-claim baselines and serious comparators before claiming advantage.",
                "Escalate only when the closed packet boundary is reached and the atlas permits the translation.",
            ],
            "output_or_decision": "A lawful route-selection decision with explicit packet, comparator, falsifier, and escalation boundaries.",
            "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
            "support_label": practical_support_label("OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS"),
            "scope_boundary": "This playbook coordinates closed packets; it does not license unconstrained whole-world prediction.",
            "trace_refs": [
                "content/22_oc_core_1_3_operationalization_program.tex",
                "content/23_oc_core_1_3_empirical_execution_protocols.tex",
                "content/24_oc_core_1_3_proof_machinery.tex",
                "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
            ],
            "failure_boundary": "Stop and demote to frontier if the observable family is outside every closed packet or if two candidate routes produce incompatible bounded verdicts.",
            "closure_verdict": "PASS" if global_verdict["closure_verdict"] == "PASS" else "FAIL_CLOSED",
            "closure_bundle_ref": "",
        }
    )
    serious_rows: list[dict[str, Any]] = []
    fragmentation_rows: list[dict[str, Any]] = []
    for row in comparison_catalog.get("rows", []):
        domain = domain_map.get(row["domain_id"])
        enriched = {
            "comparison_id": row["comparison_id"],
            "domain_id": row["domain_id"],
            "domain_title": domain["domain_title"] if domain else "Cross-domain / unified science",
            "serious_model_family": row["serious_model_family"],
            "problem_class": row["problem_class"],
            "what_it_already_explains_or_predicts": row["what_it_already_explains_or_predicts"],
            "where_fragmentation_or_limit_remains": row["where_fragmentation_or_limit_remains"],
            "what_oc_adds_or_unifies": row["what_oc_adds_or_unifies"],
            "relationship_to_oc": row["relationship_to_oc"],
            "scope_boundary": row["scope_boundary"],
            "practical_takeaway": row["practical_takeaway"],
            "source_refs": unique_strings(
                [
                    comparison_catalog.get("source_file_ref", ""),
                    source_bundles.get(row["domain_id"], {}).get("source_file_ref", ""),
                    *row.get("source_refs", []),
                ]
            ),
        }
        serious_rows.append(enriched)
        fragmentation_rows.append(
            {
                "comparison_id": row["comparison_id"],
                "domain_id": row["domain_id"],
                "problem_class": row["problem_class"],
                "prior_science_strength": row["what_it_already_explains_or_predicts"],
                "fragmentation_boundary": row["where_fragmentation_or_limit_remains"],
                "oc_closure_or_gain": row["what_oc_adds_or_unifies"],
                "relationship_to_oc": row["relationship_to_oc"],
                "what_remains_open": row["scope_boundary"],
            }
        )
    use_case_rows.sort(key=lambda row: (SPOT_DOMAIN_ORDER.index(row["domain_id"]) if row["domain_id"] in SPOT_DOMAIN_ORDER else 999, practical_support_sort_key(row["support_class"]), row["use_case_id"]))
    operational_playbooks.sort(key=lambda row: (SPOT_DOMAIN_ORDER.index(row["domain_id"]) if row["domain_id"] in SPOT_DOMAIN_ORDER else 999, practical_support_sort_key(row["support_class"]), row["playbook_id"]))
    serious_rows.sort(key=lambda row: (SPOT_DOMAIN_ORDER.index(row["domain_id"]) if row["domain_id"] in SPOT_DOMAIN_ORDER else 999, row["comparison_id"]))
    fragmentation_rows.sort(key=lambda row: (SPOT_DOMAIN_ORDER.index(row["domain_id"]) if row["domain_id"] in SPOT_DOMAIN_ORDER else 999, row["comparison_id"]))
    readiness_rows = [
        {
            "use_case_id": row["use_case_id"],
            "domain_id": row["domain_id"],
            "domain_title": row["domain_title"],
            "support_class": row["support_class"],
            "support_label": row["support_label"],
            "usable_now": row["usable_now"],
            "what_remains_open": row["what_remains_open"],
        }
        for row in use_case_rows
    ]
    usable_now_rows = [row for row in use_case_rows if row["support_class"] in USABLE_NOW_SUPPORT_CLASSES]
    frontier_rows = [row for row in use_case_rows if row["support_class"] == "FRONTIER_PROGRAM"]
    hypothesis_rows = [row for row in use_case_rows if row["support_class"] == "HYPOTHESIS_ONLY"]
    return {
        "atlas_id": "OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS",
        "schema_id": "OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_v1",
        "status": "PASS" if global_verdict["closure_verdict"] == "PASS" else "FAIL_CLOSED",
        "chapter_title": "Practical Consequences, Predictive Power, and Use of OC Core 1.3",
        "appendix_title": "Practical Utility and Model Comparison Atlas",
        "support_class_legend": [
            {
                "support_class": support_class,
                "label": practical_support_label(support_class),
                "usable_now": support_class in USABLE_NOW_SUPPORT_CLASSES,
            }
            for support_class in PRACTICAL_SUPPORT_CLASS_ORDER
        ],
        "executive_summary": {
            "usable_now_total": len(usable_now_rows),
            "frontier_total": len(frontier_rows),
            "hypothesis_total": len(hypothesis_rows),
            "same_claim_baseline_total": len(baseline_rows),
            "serious_comparison_total": len(serious_rows),
            "key_points": [
                "The theorem-native domain lanes are usable under explicit theorem, data-route, and falsifier discipline; the cross-domain route-selection lane is operationally supported within bounds and is used for packet selection rather than as a domain-level theorem claim.",
                "Its closed practical value is not unrestricted universal prediction; it is lawful packet selection, bounded residual prediction, anomaly screening, state-transition auditing, regime-shift monitoring, and cross-domain route selection within one source-bound routing framework.",
                (
                    f"The atlas also keeps {len(frontier_rows)} frontier-program "
                    f"{'row' if len(frontier_rows) == 1 else 'rows'} and {len(hypothesis_rows)} "
                    f"hypothesis-only {'row' if len(hypothesis_rows) == 1 else 'rows'} explicit so practical ambition does not masquerade as finished closure."
                ),
            ],
        },
        "use_case_rows": use_case_rows,
        "operational_playbooks": operational_playbooks,
        "same_claim_class_baseline_rows": baseline_rows,
        "serious_model_comparison_rows": serious_rows,
        "fragmentation_closure_rows": fragmentation_rows,
        "readiness_matrix_rows": readiness_rows,
        "policy": {
            "chapter_rule": "NO_PRACTICAL_CLAIM_MAY_OUTRUN_THE_CANONICAL_UTILITY_ATLAS",
            "usable_now_support_classes": sorted(USABLE_NOW_SUPPORT_CLASSES, key=practical_support_sort_key),
            "frontier_support_classes": ["FRONTIER_PROGRAM", "HYPOTHESIS_ONLY"],
            "chapter_25_nonduplication_rule": "PRACTICAL_UTILITY_CHAPTER_MAY_NOT_DUPLICATE_THE_CANONICAL_UNIFIED_SYNTHESIS",
        },
    }


def build_branch_registry() -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for branch_id, policy in BRANCH_POLICY.items():
        branches.append(
            {
                "branch_id": branch_id,
                "branch_title": policy["branch_title"],
                "scientific_class": policy["scientific_class"],
                "trace_status": policy["trace_status"],
                "evidence_status": policy["evidence_status"],
                "closure_verdict": policy["closure_verdict"],
                "core_leakage_policy": policy["core_leakage_policy"],
                "refs": policy["refs"],
            }
        )
    return branches


def build_gap_closure_registry(domain_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for domain in domain_registry:
        for gap_type in domain["gap_types"]:
            gaps.append(
                {
                    "gap_id": f"{domain['domain_id']}::{gap_type.upper().replace(' ', '_')}",
                    "domain_id": domain["domain_id"],
                    "gap_type": gap_type,
                    "scientific_class": domain["scientific_class"],
                    "trace_status": domain["trace_status"],
                    "evidence_status": domain["evidence_status"],
                    "closure_verdict": domain["closure_verdict"],
                }
            )
    return gaps


def closure_priority_score(config: dict[str, Any]) -> float:
    numerator = config["closure_impact"] * config["dependency_centrality"] * config["expected_information_gain"]
    denominator = config["compute_cost"] + config["data_cost"] + config["measurement_cost"] + config["editorial_cost"]
    return round(numerator / denominator, 6)


def unit_families_for_domain(domain_id: str) -> list[str]:
    return {
        "MATHEMATICS": ["exact arithmetic quantities", "minimal denominators", "epsilon-star scales"],
        "PHYSICS": ["SI constants", "wavelength or frequency units", "sigma-normalized residual units"],
        "CHEMISTRY": ["thermochemical energies", "spectroscopic transition units", "kinetic or equilibrium residual units"],
        "BIOLOGY": ["expression amplitudes", "state-transition ordering", "response-onset timing or residual units"],
        "SYSTEMS_CIVILIZATIONAL_PROJECTION": ["macro-process trajectory units", "turning-point error units", "regime-score units"],
    }.get(domain_id, ["domain-specific units"])


def build_closed_canon(domain_registry: list[dict[str, Any]], hostile_review_backlog: list[dict[str, Any]]) -> dict[str, Any]:
    theorem_native_domains = [domain["domain_id"] for domain in domain_registry if domain["scientific_class"] == "THEOREM_NATIVE"]
    unresolved_review_ids = [
        item["review_id"]
        for item in hostile_review_backlog
        if item["blocks_global_pass"] and item["current_status"] != "PASS"
    ]
    return {
        "governance_mode": "TWO_TIER_CANON_PLUS_FRONTIER_WORKBENCH",
        "canon_entry_rule": "THEOREM_NATIVE_ONLY",
        "current_status": "STABILIZING_UNDER_HOSTILE_REVIEW" if unresolved_review_ids else "STABLE",
        "canon_entity_ids": [
            "OC_CORE_1_3_ROOT_KERNEL",
            "ROOT::MODEL_AND_OPERATORS",
            "ROOT::K_LEVEL_HIERARCHY",
            "ROOT::PREDICTION_AND_FALSIFIABILITY_GRAMMAR",
            *[f"K_LEVEL::{level_id}" for level_id in [f"K{i}" for i in range(13)]],
            *theorem_native_domains,
        ],
        "open_audit_ids": unresolved_review_ids,
        "refs": [
            "content/19_oc_core_1_3_foundational_consistency.tex",
            "content/20_oc_core_1_3_theorem_roadmap.tex",
            "content/21_oc_core_1_3_worked_examples.tex",
        ],
    }


def build_frontier_workbench(domain_registry: list[dict[str, Any]]) -> dict[str, Any]:
    campaigns = []
    for domain in domain_registry:
        if domain["scientific_class"] != "BRIDGE_ONLY":
            continue
        config = DOMAIN_CLOSURE_CONFIG.get(domain["domain_id"], {})
        campaigns.append(
            {
                "campaign_id": f"FRONTIER::{domain['domain_id']}",
                "domain_id": domain["domain_id"],
                "current_state": domain["scientific_state"],
                "launch_rule": config.get("launch_rule", "LOCKED"),
                "target_phase_id": config.get("phase_id", "PHASE_2_DOMAIN_THEOREMIZATION"),
                "goal": config.get("minimum_theorem_native_claim", domain["classification_rationale"]),
                "blocking_ids": domain["gap_ids"],
            }
        )
    campaigns.extend(
        [
            {
                "campaign_id": "FRONTIER::K11_K12_IRREDUCIBILITY",
                "domain_id": "GLOBAL",
                "current_state": "PENDING_IRREDUCIBILITY_CAMPAIGN",
                "launch_rule": "RUN_INSIDE_PHASE_1",
                "target_phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
                "goal": "Either prove K11 and K12 necessary beyond K10 or demote them and rebuild the dependency graph.",
                "blocking_ids": ["HOSTILE::K11_K12_IRREDUCIBILITY"],
            },
            {
                "campaign_id": "FRONTIER::CROSS_DOMAIN_UNIFICATION",
                "domain_id": "GLOBAL",
                "current_state": "LOCKED_PENDING_DOMAIN_CLOSURE",
                "launch_rule": "RUN_AFTER_ALL_BLOCKED_DOMAINS_CLOSE",
                "target_phase_id": "PHASE_7_CROSS_DOMAIN_UNIFICATION",
                "goal": "Build one unified science atlas and prove cross-domain integrability.",
                "blocking_ids": ["GLOBAL::UNIFIED_SCIENCE_ATLAS_PENDING"],
            },
        ]
    )
    return {
        "entry_rule": "FRONTIER_CLAIMS_MUST_NOT_BE_PRESENTED_AS_CLOSED_SCIENCE",
        "current_status": "ACTIVE",
        "campaigns": campaigns,
    }


def build_dependency_atlas() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in LOAD_BEARING_DEPENDENCY_ATLAS:
        rows.append(
            {
                "edge_id": row["edge_id"],
                "scientific_class": "THEOREM_NATIVE",
                "trace_status": "TRACE_COMPLETE",
                "evidence_status": "EVIDENCE_COMPLETE",
                "closure_verdict": "PASS",
                "premises": row["premises"],
                "result": row["result"],
                "refs": row["refs"],
            }
        )
    return rows


def build_proof_obligation_registry() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet in PROOF_OBLIGATION_SHEETS:
        rows.append(
            {
                "obligation_id": sheet["obligation_id"],
                "scientific_class": "THEOREM_NATIVE",
                "trace_status": "TRACE_COMPLETE",
                "evidence_status": "EVIDENCE_COMPLETE",
                "closure_verdict": "PASS",
                "sheet_status": "DECLARED_CANONICAL_SHEET",
                "statement": sheet["statement"],
                "premises": sheet["premises"],
                "forbidden_shortcuts": sheet["forbidden_shortcuts"],
                "excluded_dependencies": sheet["excluded_dependencies"],
                "falsifier_condition": sheet["falsifier_condition"],
                "refs": sheet["refs"],
            }
        )
    return rows


def hostile_review_resolution_state(current_status: str) -> str:
    if current_status == "PASS":
        return "RESOLVED_PASS"
    if current_status.startswith("PENDING"):
        return "PENDING_FORMAL_RESOLUTION"
    return "FAIL_CLOSED_REAUDIT_REQUIRED"


def build_hostile_review_dossier_refs(review_id: str) -> dict[str, str]:
    package_dir = hostile_review_package_dir(review_id)
    return {
        "package_dir": repo_rel(package_dir),
        "manifest": repo_rel(package_dir / "manifest.json"),
        "readme": repo_rel(package_dir / "README.md"),
        "formal_dossier": repo_rel(package_dir / "formal_dossier.md"),
    }


def bundle_phase_metadata(claim_id: str, domain_id: str) -> dict[str, Any]:
    if domain_id in DOMAIN_CLOSURE_CONFIG:
        config = DOMAIN_CLOSURE_CONFIG[domain_id]
        return {
            "phase_id": config["phase_id"],
            "launch_rule": config["launch_rule"],
            "formal_derivation_order": config["formal_derivation_order"],
            "empirical_cost_order": config["empirical_cost_order"],
        }
    if claim_id == "LOAD_BEARING_SPINE":
        return {
            "phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
            "launch_rule": "ENTRY_IMMEDIATE",
            "formal_derivation_order": 0,
            "empirical_cost_order": 0,
        }
    if claim_id == "K11_K12_IRREDUCIBILITY":
        return {
            "phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
            "launch_rule": "ENTRY_IMMEDIATE_IRREDUCIBILITY_FORK",
            "formal_derivation_order": 0,
            "empirical_cost_order": 0,
        }
    return {
        "phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
        "launch_rule": "FRAME_ONLY_MONITORING",
        "formal_derivation_order": 0,
        "empirical_cost_order": 0,
    }


def build_bundle_dossier_refs(claim_id: str) -> dict[str, str]:
    package_dir = closure_bundle_package_dir(claim_id)
    return {
        "package_dir": repo_rel(package_dir),
        "manifest": repo_rel(package_dir / "manifest.json"),
        "readme": repo_rel(package_dir / "README.md"),
        "task_board": repo_rel(package_dir / "task_board.json"),
    }


def build_bundle_artifact_file_refs(claim_id: str) -> dict[str, str]:
    package_dir = closure_bundle_package_dir(claim_id)
    return {artifact_kind: repo_rel(package_dir / f"{artifact_kind}.md") for artifact_kind in CLOSURE_ARTIFACT_ORDER}


def build_bundle_task_rows(claim_id: str, artifacts: dict[str, str], artifact_file_refs: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_kind in CLOSURE_ARTIFACT_ORDER:
        rows.append(
            {
                "task_id": f"TASK::{claim_id}::{artifact_kind.upper()}",
                "artifact_kind": artifact_kind,
                "assignee_role": ARTIFACT_ASSIGNEE_ROLE_MAP[artifact_kind],
                "entry_gate": ARTIFACT_ENTRY_GATE_MAP[artifact_kind],
                "current_artifact_status": artifacts[artifact_kind],
                "artifact_file_ref": artifact_file_refs[artifact_kind],
                "pass_transition": ARTIFACT_PASS_TRANSITION_MAP[artifact_kind],
                "fail_transition": ARTIFACT_FAIL_TRANSITION_MAP[artifact_kind],
            }
        )
    return rows


def build_hostile_review_backlog(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_reviews = inputs.get("science_sources", {}).get("hostile_review", {})
    for fallback_item in HOSTILE_REVIEW_BACKLOG_ROWS:
        item = deepcopy(source_reviews.get(fallback_item["review_id"], fallback_item))
        dossier_refs = build_hostile_review_dossier_refs(item["review_id"])
        rows.append(
            {
                **item,
                "challenge": item.get("challenge", item.get("challenge_statement", "")),
                "scientific_class": item.get("scientific_class", "THEOREM_NATIVE"),
                "trace_status": item.get("trace_status", "TRACE_COMPLETE_REQUIRES_DOSSIER_LOCK"),
                "evidence_status": item.get("evidence_status", "EVIDENCE_PENDING_HOSTILE_REVIEW_DOSSIER"),
                "closure_verdict": "FAIL_CLOSED" if item["blocks_global_pass"] and item["current_status"] != "PASS" else "PASS",
                "task_id": f"TASK::{item['review_id']}::FORMAL_DOSSIER",
                "dossier_package_ref": dossier_refs["package_dir"],
                "dossier_manifest_ref": dossier_refs["manifest"],
                "dossier_readme_ref": dossier_refs["readme"],
                "dossier_ref": dossier_refs["formal_dossier"],
                "resolution_if_pass": "CLEAR_HOSTILE_REVIEW_BLOCKER_AND_LOCK_CLOSED_CORE_ROUTE",
                "resolution_if_fail": "KEEP_FAIL_CLOSED_AND_REBUILD_AFFECTED_CLOSED_CORE_ROUTE",
                "current_resolution_state": item.get("current_resolution_state", hostile_review_resolution_state(item["current_status"])),
            }
        )
    return rows


def domain_bundle_artifact_statuses(domain: dict[str, Any]) -> dict[str, str]:
    if domain["domain_id"] == "MATHEMATICS":
        return {
            "theorem_packet": "COMPLETE",
            "parameter_law_packet": "COMPLETE",
            "observable_binding_spec": "COMPLETE",
            "dataset_data_route_manifest": "COMPLETE",
            "held_out_replay_spec": "COMPLETE",
            "falsifier_ledger": "COMPLETE",
            "counterexample_ledger": "ACTIVE_CONTINUOUS_SEARCH",
            "same_claim_class_comparator_ledger": "DECLARED_NO_SUPERIOR_BASELINE",
        }
    if domain["scientific_class"] == "BRIDGE_ONLY":
        return {
            "theorem_packet": "MISSING_DOMAIN_THEOREM",
            "parameter_law_packet": "MISSING_PARAMETER_LAW",
            "observable_binding_spec": "DECLARED_BRIDGE_ROUTE_PRESENT",
            "dataset_data_route_manifest": "PINNED_DATA_ROUTE_PRESENT",
            "held_out_replay_spec": "DECLARED_HELD_OUT_REPLAY_PRESENT",
            "falsifier_ledger": "DECLARED_FALSIFIER_PRESENT",
            "counterexample_ledger": "ACTIVE_COUNTEREXAMPLE_SEARCH_OPEN",
            "same_claim_class_comparator_ledger": "PENDING_ADVERSARIAL_BASELINE_AUDIT",
        }
    if domain["scientific_class"] == "FRAME_ONLY":
        return {
            "theorem_packet": "FRAME_ONLY_COMPLETE",
            "parameter_law_packet": "NOT_REQUIRED_FRAME_ONLY",
            "observable_binding_spec": "NOT_REQUIRED_FRAME_ONLY",
            "dataset_data_route_manifest": "NOT_REQUIRED_FRAME_ONLY",
            "held_out_replay_spec": "NOT_REQUIRED_FRAME_ONLY",
            "falsifier_ledger": "FRAME_BOUNDARY_DECLARED",
            "counterexample_ledger": "ACTIVE_BOUNDARY_MONITORING",
            "same_claim_class_comparator_ledger": "NOT_REQUIRED_FRAME_ONLY",
        }
    return {
        "theorem_packet": "EXCLUDED",
        "parameter_law_packet": "EXCLUDED",
        "observable_binding_spec": "EXCLUDED",
        "dataset_data_route_manifest": "EXCLUDED",
        "held_out_replay_spec": "EXCLUDED",
        "falsifier_ledger": "EXCLUDED",
        "counterexample_ledger": "EXCLUDED",
        "same_claim_class_comparator_ledger": "EXCLUDED",
    }


def source_bundle_artifact_statuses(source_bundle: dict[str, Any], fallback_domain: dict[str, Any] | None = None) -> dict[str, str]:
    statuses = deepcopy(source_bundle.get("artifact_statuses", {}))
    if set(statuses.keys()) == set(CLOSURE_ARTIFACT_ORDER):
        return statuses
    if fallback_domain is not None:
        return domain_bundle_artifact_statuses(fallback_domain)
    return {artifact_kind: "PENDING_SOURCE_COMPLETION" for artifact_kind in CLOSURE_ARTIFACT_ORDER}


def build_bundle_from_source(
    claim_id: str,
    source_bundle: dict[str, Any],
    fallback_domain: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phase_meta = bundle_phase_metadata(claim_id, source_bundle.get("domain_id", claim_id))
    artifacts = source_bundle_artifact_statuses(source_bundle, fallback_domain=fallback_domain)
    complete_total = sum(
        1 for status in artifacts.values() if status in {"COMPLETE", "FRAME_ONLY_COMPLETE", "DECLARED_NO_SUPERIOR_BASELINE"}
    )
    dossier_refs = build_bundle_dossier_refs(claim_id)
    artifact_file_refs = build_bundle_artifact_file_refs(claim_id)
    task_rows = build_bundle_task_rows(claim_id, artifacts, artifact_file_refs)
    return {
        "bundle_id": f"CLOSURE_BUNDLE::{claim_id}",
        "claim_id": claim_id,
        "domain_id": source_bundle.get("domain_id", fallback_domain["domain_id"] if fallback_domain else "GLOBAL"),
        "phase_id": source_bundle.get("phase_id", phase_meta["phase_id"]),
        "launch_rule": source_bundle.get("launch_rule", phase_meta["launch_rule"]),
        "formal_derivation_order": source_bundle.get("formal_derivation_order", phase_meta["formal_derivation_order"]),
        "empirical_cost_order": source_bundle.get("empirical_cost_order", phase_meta["empirical_cost_order"]),
        "execution_order_authority": source_bundle.get("execution_order_authority", "DOMAIN_PRIORITY_BOARD_ONLY"),
        "scientific_class": source_bundle.get("scientific_class", fallback_domain["scientific_class"] if fallback_domain else "THEOREM_NATIVE"),
        "trace_status": source_bundle.get("trace_status", fallback_domain["trace_status"] if fallback_domain else "TRACE_COMPLETE"),
        "evidence_status": source_bundle.get("evidence_status", fallback_domain["evidence_status"] if fallback_domain else "EVIDENCE_COMPLETE"),
        "closure_verdict": source_bundle.get("closure_verdict", fallback_domain["closure_verdict"] if fallback_domain else "FAIL_CLOSED"),
        "artifact_contract": deepcopy(CLOSURE_ARTIFACT_ORDER),
        "artifact_statuses": artifacts,
        "artifact_payloads": deepcopy(source_bundle.get("artifacts", {})),
        "source_file_ref": source_bundle.get("source_file_ref", ""),
        "dossier_package_ref": dossier_refs["package_dir"],
        "dossier_manifest_ref": dossier_refs["manifest"],
        "dossier_readme_ref": dossier_refs["readme"],
        "task_board_ref": dossier_refs["task_board"],
        "artifact_file_refs": artifact_file_refs,
        "task_rows": task_rows,
        "task_ids": [row["task_id"] for row in task_rows],
        "current_transition_gate": source_bundle.get("current_transition_gate", bundle_current_transition_gate(source_bundle.get("closure_verdict", "FAIL_CLOSED"), artifacts)),
        "pass_transition": source_bundle.get("pass_transition", "PROMOTE_TO_PASS_ONLY_AFTER_ALL_REQUIRED_ARTIFACTS_LOCK_AND_NO_SUPERIOR_BASELINE_SURVIVES"),
        "fail_transition": source_bundle.get("fail_transition", "KEEP_FAIL_CLOSED_AND_REQUIRE_ADVANCE_SPLIT_OR_REFUTE_OR_SUSPEND"),
        "complete_artifact_total": complete_total,
        "artifact_total": len(artifacts),
        "blocking_ids": deepcopy(source_bundle.get("blocking_ids", fallback_domain.get("gap_ids", []) if fallback_domain else [])),
        "minimum_theorem_native_claim": source_bundle.get("minimum_theorem_native_claim", "FRAME_ONLY_MONITORING_ONLY"),
        "parameter_law_target": source_bundle.get("parameter_law_target", "NOT_REQUIRED_FRAME_ONLY"),
        "theorem_to_observable_map": deepcopy(source_bundle.get("theorem_to_observable_map", fallback_domain.get("theorem_to_observable_map", []) if fallback_domain else [])),
        "observable_ids": deepcopy(source_bundle.get("observable_ids", fallback_domain.get("observable_ids", []) if fallback_domain else [])),
        "selected_route_institutions": deepcopy(source_bundle.get("selected_route_institutions", fallback_domain.get("selected_route_institutions", []) if fallback_domain else [])),
        "held_out_case_ids": deepcopy(source_bundle.get("held_out_case_ids", fallback_domain.get("held_out_case_ids", []) if fallback_domain else [])),
        "falsifier_specification": source_bundle.get("falsifier_specification", fallback_domain.get("falsifier_specification", "FRAME_ONLY_BOUNDARY_MONITORING") if fallback_domain else "FRAME_ONLY_BOUNDARY_MONITORING"),
        "metric_summary": deepcopy(source_bundle.get("metric_summary", fallback_domain.get("metric_summary", {}) if fallback_domain else {})),
        "refs": unique_strings([source_bundle.get("source_file_ref", ""), *source_bundle.get("refs", []), "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json"]),
    }


def build_domain_closure_bundles(domain_registry: list[dict[str, Any]], inputs: dict[str, Any]) -> list[dict[str, Any]]:
    bundles: list[dict[str, Any]] = []
    source_bundles = inputs.get("science_sources", {}).get("closure_bundles", {})
    for domain in domain_registry:
        if domain["domain_id"] not in CORE_DOMAIN_IDS and domain["domain_id"] != "METAONTOLOGY":
            continue
        source_bundle = source_bundles.get(domain["domain_id"])
        if source_bundle:
            bundles.append(build_bundle_from_source(domain["domain_id"], source_bundle, fallback_domain=domain))
            continue
        phase_meta = bundle_phase_metadata(domain["domain_id"], domain["domain_id"])
        artifacts = domain_bundle_artifact_statuses(domain)
        complete_total = sum(
            1 for status in artifacts.values() if status in {"COMPLETE", "FRAME_ONLY_COMPLETE", "DECLARED_NO_SUPERIOR_BASELINE"}
        )
        dossier_refs = build_bundle_dossier_refs(domain["domain_id"])
        artifact_file_refs = build_bundle_artifact_file_refs(domain["domain_id"])
        task_rows = build_bundle_task_rows(domain["domain_id"], artifacts, artifact_file_refs)
        config = DOMAIN_CLOSURE_CONFIG.get(domain["domain_id"], {})
        bundles.append(
            {
                "bundle_id": f"CLOSURE_BUNDLE::{domain['domain_id']}",
                "claim_id": domain["domain_id"],
                "domain_id": domain["domain_id"],
                "phase_id": phase_meta["phase_id"],
                "launch_rule": phase_meta["launch_rule"],
                "formal_derivation_order": phase_meta["formal_derivation_order"],
                "empirical_cost_order": phase_meta["empirical_cost_order"],
                "execution_order_authority": "DOMAIN_PRIORITY_BOARD_ONLY",
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "artifact_contract": deepcopy(CLOSURE_ARTIFACT_ORDER),
                "artifact_statuses": artifacts,
                "dossier_package_ref": dossier_refs["package_dir"],
                "dossier_manifest_ref": dossier_refs["manifest"],
                "dossier_readme_ref": dossier_refs["readme"],
                "task_board_ref": dossier_refs["task_board"],
                "artifact_file_refs": artifact_file_refs,
                "task_rows": task_rows,
                "task_ids": [row["task_id"] for row in task_rows],
                "current_transition_gate": bundle_current_transition_gate(domain["closure_verdict"], artifacts),
                "pass_transition": "PROMOTE_TO_PASS_ONLY_AFTER_ALL_REQUIRED_ARTIFACTS_LOCK_AND_NO_SUPERIOR_BASELINE_SURVIVES",
                "fail_transition": "KEEP_FAIL_CLOSED_AND_REQUIRE_ADVANCE_SPLIT_OR_REFUTE_OR_SUSPEND",
                "complete_artifact_total": complete_total,
                "artifact_total": len(artifacts),
                "blocking_ids": domain["gap_ids"],
                "minimum_theorem_native_claim": config.get("minimum_theorem_native_claim", "FRAME_ONLY_MONITORING_ONLY"),
                "parameter_law_target": config.get("parameter_law_target", "NOT_REQUIRED_FRAME_ONLY"),
                "theorem_to_observable_map": deepcopy(domain.get("theorem_to_observable_map", [])),
                "observable_ids": deepcopy(domain.get("observable_ids", [])),
                "selected_route_institutions": deepcopy(domain.get("selected_route_institutions", [])),
                "held_out_case_ids": deepcopy(domain.get("held_out_case_ids", [])),
                "falsifier_specification": domain.get("falsifier_specification", "FRAME_ONLY_BOUNDARY_MONITORING"),
                "metric_summary": deepcopy(domain.get("metric_summary", {})),
                "refs": unique_strings(["releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json", *domain["source_refs"]]),
            }
        )
    for claim_id in ["LOAD_BEARING_SPINE", "K11_K12_IRREDUCIBILITY"]:
        source_bundle = source_bundles.get(claim_id)
        if source_bundle:
            bundles.append(build_bundle_from_source(claim_id, source_bundle))
    return bundles


def build_unified_science_atlas(domain_registry: list[dict[str, Any]]) -> dict[str, Any]:
    core_domains = [domain for domain in domain_registry if domain["domain_id"] in CORE_DOMAIN_IDS]
    atlas_pass = not any(domain["scientific_class"] == "BRIDGE_ONLY" for domain in core_domains)
    domain_translation_rows = []
    for domain in core_domains:
        domain_translation_rows.append(
            {
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "primary_k_levels": domain["primary_k_levels"],
                "kernel_operator_refs": domain["root_operator_refs"],
                "theorem_to_observable_map": domain["theorem_to_observable_map"],
                "observable_ids": domain["observable_ids"],
                "measurable_outputs": domain["measurable_outputs"],
                "unit_families": unit_families_for_domain(domain["domain_id"]),
                "invariant_families": [
                    "explicit claim boundary",
                    "held-out evidence before promotion",
                    "no hidden extension or refuted leakage",
                ],
                "failure_modes": [domain["falsifier_specification"], *domain["gap_types"]],
            }
        )
    shared_operator_families = [
        {
            "operator_id": operator_id,
            "current_status": "GLOBAL_LOCKED" if atlas_pass else "KERNEL_DEFINED_DOMAIN_TRANSLATION_PENDING_GLOBAL_LOCK",
            "projected_domain_ids": CORE_DOMAIN_IDS,
            "refs": ["content/03_model.tex", "content/11_operators_full.tex"],
        }
        for operator_id in ["F", "G", "H", "Q", "R", "S", "U"]
    ]
    parameter_manifold_rows = [
        {
            "domain_id": domain["domain_id"],
            "domain_title": domain["domain_title"],
            "closure_verdict": domain["closure_verdict"],
            "primary_k_levels": domain["primary_k_levels"],
            "measurable_outputs": domain["measurable_outputs"],
            "measurement_schema": domain["measurement_schema"],
            "acceptance_criterion": domain["acceptance_criterion"],
        }
        for domain in core_domains
    ]
    invariant_catalog = [
        {
            "invariant_id": "EXPLICIT_CLAIM_BOUNDARY",
            "status": "PASS" if atlas_pass else "PENDING_DOMAIN_CLOSURE",
            "statement": "Every closed-domain packet remains bounded by its declared scope and may not widen by rhetoric alone.",
        },
        {
            "invariant_id": "HELD_OUT_EVIDENCE_BEFORE_PROMOTION",
            "status": "PASS" if atlas_pass else "PENDING_DOMAIN_CLOSURE",
            "statement": "Empirical promotion remains lawful only when held-out evidence is locked before replay and survives the declared thresholds.",
        },
        {
            "invariant_id": "NO_EXCLUDED_BRANCH_LEAKAGE",
            "status": "PASS",
            "statement": "No extension or refuted branch may leak into the core proof path of a promoted domain packet.",
        },
    ]
    integrability_suite = {
        "status": "PASS" if atlas_pass else "NOT_RUN_PENDING_DOMAIN_CLOSURE",
        "checked_domain_ids": [domain["domain_id"] for domain in core_domains],
        "blocking_domain_ids": [domain["domain_id"] for domain in core_domains if domain["closure_verdict"] != "PASS"],
        "rules": [
            "A shared operator may not take mutually incompatible meanings across closed domains.",
            "Shared observables may not receive conflicting verdicts across closed domains.",
            "No domain-level law may violate an already closed upstream route.",
        ],
    }
    global_falsifier_matrix = {
        "status": "PASS" if atlas_pass else "NOT_RUN_PENDING_DOMAIN_CLOSURE",
        "surviving_global_falsifiers": [] if atlas_pass else ["DOMAIN_CLOSURE_PENDING"],
        "collapse_rule": "Any surviving cross-domain contradiction or incompatible shared observable verdict collapses global PASS.",
    }
    return {
        "atlas_id": "OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS",
        "atlas_status": "PASS" if atlas_pass else "FRONTIER_PENDING_DOMAIN_CLOSURE",
        "shared_operator_families": shared_operator_families,
        "operator_vocabulary": shared_operator_families,
        "parameter_manifold_rows": parameter_manifold_rows,
        "invariant_catalog": invariant_catalog,
        "domain_translation_rows": domain_translation_rows,
        "integrability_suite": integrability_suite,
        "global_falsifier_matrix": global_falsifier_matrix,
        "global_integrability_rule": "A shared operator may not take mutually incompatible meanings across closed domains.",
        "global_falsifier_rule": "Any surviving cross-domain contradiction or incompatible shared observable verdict collapses global PASS.",
    }


def build_domain_priority_board(domain_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain in domain_registry:
        if domain["domain_id"] not in CORE_DOMAIN_IDS:
            continue
        config = DOMAIN_CLOSURE_CONFIG[domain["domain_id"]]
        rows.append(
            {
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "phase_id": config["phase_id"],
                "formal_derivation_order": config["formal_derivation_order"],
                "empirical_cost_order": config["empirical_cost_order"],
                "closure_gain_per_cost": closure_priority_score(config),
                "closure_impact": config["closure_impact"],
                "dependency_centrality": config["dependency_centrality"],
                "expected_information_gain": config["expected_information_gain"],
                "compute_cost": config["compute_cost"],
                "data_cost": config["data_cost"],
                "measurement_cost": config["measurement_cost"],
                "editorial_cost": config["editorial_cost"],
                "launch_rule": config["launch_rule"],
                "current_priority_label": config["current_priority_label"],
                "minimum_theorem_native_claim": config["minimum_theorem_native_claim"],
                "parameter_law_target": config["parameter_law_target"],
                "parallelism_note": config["parallelism_note"],
                "blocking_ids": domain["gap_ids"],
                "next_required_action": domain["next_required_action"],
            }
        )
    return rows


def build_scientific_program(domain_registry: list[dict[str, Any]], hostile_review_backlog: list[dict[str, Any]]) -> dict[str, Any]:
    domain_priority_board = build_domain_priority_board(domain_registry)
    return {
        "governance_mode": "CLOSED_CANON_PLUS_FRONTIER_WORKBENCH",
        "execution_order_authority": "DOMAIN_PRIORITY_BOARD_ONLY",
        "broadening_freeze_status": "ACTIVE_UNTIL_PHASE_1_AND_PHYSICS_THEOREM_PACKET_LOCK",
        "broadening_freeze_rule": "No new domains, external claims, or narrative universes may enter the scientific canon until Phase 1 stabilizes and the physics theorem packet locks.",
        "execution_cadence": [
            "CORE_AND_HOSTILE_REVIEW_DOSSIERS_PRIMARY",
            "PHYSICS_THEOREMIZATION_PRIMARY",
            "CHEMISTRY_DATA_PREP_SIDECAR_ONLY",
        ],
        "closure_bundle_contract": deepcopy(CLOSURE_ARTIFACT_ORDER),
        "ticket_admissibility_rule": "Every scientific task must map to exactly one closure-bundle artifact or one hostile-review dossier.",
        "prioritization_formula": "(closure impact x dependency centrality x expected information gain) / (compute cost + data cost + measurement cost + editorial cost)",
        "anti_cycle_rule": "A method class may not be repeated unless a new formal premise, new dataset family, or new observable family enters the claim.",
        "stalled_outcomes": ["advance", "split_with_explicit_parent_relation", "refute_or_suspend"],
        "method_ladder": deepcopy(METHOD_LADDER_ROWS),
        "phase_registry": deepcopy(PROGRAM_PHASE_ROWS),
        "domain_priority_board": domain_priority_board,
        "hostile_review_blocking_ids": [
            item["review_id"]
            for item in hostile_review_backlog
            if item["blocks_global_pass"] and item["current_status"] != "PASS"
        ],
    }


def build_surface_projection_manifest() -> dict[str, Any]:
    return {
        "generated_surfaces": [
            {
                "surface_id": "FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "DOMAIN_HARD_CLOSURE_COMMAND_BOARD_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/DOMAIN_HARD_CLOSURE_COMMAND_BOARD_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "INSTITUTE_RUN_MEASUREMENT_PROGRAM_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/INSTITUTE_RUN_MEASUREMENT_PROGRAM_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "SCIENCE_OPERATIONALIZATION_AUTOPROPAGATION_CONTRACT_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/SCIENCE_OPERATIONALIZATION_AUTOPROPAGATION_CONTRACT_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json",
                "target_path": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
        ],
        "generated_tex": [
            {
                "surface_id": "content/generated/oc_core_1_3_operationalization_program_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "content/generated/oc_core_1_3_empirical_execution_protocols_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "content/generated/oc_core_1_3_proof_machinery_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "content/generated/oc_core_1_3_toe_synthesis_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "content/generated/oc_core_1_3_practical_utility_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "appendix/generated/oc_core_1_3_empirical_validation_matrix_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "appendix/generated/oc_core_1_3_proof_machinery_appendix_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "surface_id": "appendix/generated/oc_core_1_3_practical_utility_model_comparison_atlas_generated.tex",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
        ],
        "generated_dossier_packages": [
            {
                "package_class": "closure_bundle_packages",
                "target_path": "releases/oc_core_1_3/editorial/dossier_packages/closure_bundles/",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "package_class": "hostile_review_packages",
                "target_path": "releases/oc_core_1_3/editorial/dossier_packages/hostile_review/",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
            {
                "package_class": "phase1_closed_core_package",
                "target_path": "releases/oc_core_1_3/editorial/dossier_packages/phase1_closed_core/",
                "projection_rule": "DERIVE_FROM_SPOT_ONLY",
            },
        ],
    }


def build_global_verdict(
    domain_registry: list[dict[str, Any]],
    gap_registry: list[dict[str, Any]],
    hostile_review_backlog: list[dict[str, Any]],
    unified_science_atlas: dict[str, Any],
) -> dict[str, Any]:
    core_domains = [domain for domain in domain_registry if domain["scope_role"] == "core_domain"]
    blocking_domains = [domain["domain_id"] for domain in core_domains if domain["closure_verdict"] != "PASS"]
    passing_domains = [domain["domain_id"] for domain in core_domains if domain["closure_verdict"] == "PASS"]
    hostile_review_blocking_ids = [
        item["review_id"]
        for item in hostile_review_backlog
        if item["blocks_global_pass"] and item["current_status"] != "PASS"
    ]
    toe_release = toe_release_candidate_summary(domain_registry, hostile_review_backlog, unified_science_atlas)
    return {
        "closure_verdict": "PASS" if not blocking_domains and not hostile_review_blocking_ids and unified_science_atlas["atlas_status"] == "PASS" else "FAIL_CLOSED",
        "scientific_truth_mode": "ALL_OR_NOTHING_CORE_CLOSURE",
        "core_domain_total": len(core_domains),
        "core_domain_pass_total": len(passing_domains),
        "core_domain_fail_closed_total": len(blocking_domains),
        "passing_domains": passing_domains,
        "blocking_domains": blocking_domains,
        "blocking_ids": [gap["gap_id"] for gap in gap_registry if gap["domain_id"] in blocking_domains],
        "hostile_review_blocking_total": len(hostile_review_blocking_ids),
        "hostile_review_blocking_ids": hostile_review_blocking_ids,
        "program_blocking_total": len([gap["gap_id"] for gap in gap_registry if gap["domain_id"] in blocking_domains]) + len(hostile_review_blocking_ids),
        "bridge_only_domain_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "BRIDGE_ONLY"),
        "theorem_native_domain_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "THEOREM_NATIVE"),
        "frame_only_domain_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "FRAME_ONLY"),
        "refuted_domain_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "REFUTED"),
        "translation_isolation_status": "PASS",
        "atlas_status": unified_science_atlas["atlas_status"],
        "integrability_suite_status": "NOT_RUN_PENDING_DOMAIN_CLOSURE" if unified_science_atlas["atlas_status"] != "PASS" else "PASS",
        "toe_release_candidate_status": toe_release["status"],
        "toe_release_candidate_blockers": toe_release["blockers"],
        "toe_release_candidate_reason": toe_release["reason"],
        "reason": "Global science remains fail-closed until every core empirical domain closes a theorem-native trace, hostile-review blockers are cleared, and the unified atlas passes integrability.",
    }


def build_policy() -> dict[str, Any]:
    return {
        "scientific_authority_id": "OC_CORE_1_3_SCIENCE_SPOT",
        "scientific_truth_scope": "CORE_1_3_SCIENCE_ONLY",
        "scientific_source_corpus": repo_rel(SCIENCE_SOURCE_DIR),
        "scientific_authoring_rule": "SCIENCE_IS_AUTHORED_ONLY_IN_SOURCE_OWNED_SCIENCE_CORPUS_AND_ALL_EDITORIAL_SURFACES_ARE_PROJECTIONS",
        "allowed_scientific_classes": ALLOWED_SCIENTIFIC_CLASSES,
        "allowed_closure_verdicts": ALLOWED_CLOSURE_VERDICTS,
        "allowed_gap_types": ALLOWED_GAP_TYPES,
        "promotion_bar": {
            "deterministic_statements": "EXACT_MATCH_REQUIRED",
            "sigma_semantic_lanes": "HELD_OUT_RESULTS_MUST_CLEAR_5_SIGMA_WITHOUT_TAIL_BREACHES",
            "bridge_residual_containment": "INSUFFICIENT_FOR_PROMOTION",
        },
        "translation_isolation_policy": "TRANSLATION_AND_PUBLICATION_READINESS_MUST_NOT_CHANGE_SCIENCE_VERDICTS",
        "packaging_surface_exclusion": [
            "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_ARTIFACT_CONTRACT.json",
        ],
        "toe_release_bar": {
            "manuscript_target": "ENGLISH_MASTER_MONOGRAPH_ONLY",
            "bridge_only_domains_allowed": 0,
            "hostile_review_blockers_allowed": 0,
            "required_atlas_status": "PASS",
            "required_integrability_suite_status": "PASS",
            "required_k_level_rows": [f"K{index}" for index in range(13)],
            "required_empirical_prediction_tables": CORE_DOMAIN_IDS[1:],
            "truth_first_naming_policy": {
                "fail_closed_public_chapter_title": "Unified Science Closure Attempt",
                "pass_public_chapter_title": "Unified Science Synthesis",
                "synthesis_title_allowed_only_if": "FINAL_UNIFIED_SYNTHESIS_VALIDATOR_PASS",
            },
        },
    }


def build_spot(inputs: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    source_errors = validate_science_source_corpus(inputs.get("science_sources", {}), repo_root=repo_root)
    if source_errors:
        raise ValueError("Science source corpus is incomplete:\n" + "\n".join(source_errors))
    kernel = build_kernel()
    k_levels = build_k_levels(inputs)
    domain_registry = [build_domain_record(domain_id, inputs) for domain_id in SPOT_DOMAIN_ORDER]
    gap_registry = build_gap_closure_registry(domain_registry)
    hostile_review_backlog = build_hostile_review_backlog(inputs)
    domain_closure_bundles = build_domain_closure_bundles(domain_registry, inputs)
    unified_science_atlas = build_unified_science_atlas(domain_registry)
    global_verdict = build_global_verdict(domain_registry, gap_registry, hostile_review_backlog, unified_science_atlas)
    toe_synthesis_registry = build_toe_synthesis_registry(
        kernel,
        k_levels,
        domain_registry,
        domain_closure_bundles,
        global_verdict,
    )
    practical_utility_atlas = build_practical_utility_atlas(
        domain_registry,
        domain_closure_bundles,
        global_verdict,
        unified_science_atlas,
        inputs,
    )
    return {
        "metadata": {
            "repo_sha": git_sha(repo_root),
            "script": "tools/build_oc_core_1_3_science_spot.py",
            "surface": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "ts_utc": utc_now(),
        },
        "policy": build_policy(),
        "kernel": kernel,
        "k_levels": k_levels,
        "theorem_spine": build_theorem_spine(domain_registry),
        "observable_registry": build_observable_registry(domain_registry),
        "domain_registry": domain_registry,
        "branch_registry": build_branch_registry(),
        "closed_canon": build_closed_canon(domain_registry, hostile_review_backlog),
        "frontier_workbench": build_frontier_workbench(domain_registry),
        "dependency_atlas": build_dependency_atlas(),
        "proof_obligation_registry": build_proof_obligation_registry(),
        "hostile_review_backlog": hostile_review_backlog,
        "domain_closure_bundles": domain_closure_bundles,
        "unified_science_atlas": unified_science_atlas,
        "toe_synthesis_registry": toe_synthesis_registry,
        "practical_utility_atlas": practical_utility_atlas,
        "scientific_program": build_scientific_program(domain_registry, hostile_review_backlog),
        "gap_closure_registry": gap_registry,
        "surface_projection_manifest": build_surface_projection_manifest(),
        "global_verdict": global_verdict,
    }


def normalize_for_compare(payload: Any) -> Any:
    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            if key == "metadata" and isinstance(value, dict):
                result[key] = {k: normalize_for_compare(v) for k, v in value.items() if k != "ts_utc"}
            else:
                result[key] = normalize_for_compare(value)
        return result
    if isinstance(payload, list):
        return [normalize_for_compare(item) for item in payload]
    return payload


def compare_normalized(a: Any, b: Any) -> bool:
    return normalize_for_compare(a) == normalize_for_compare(b)


def foundational_summary(spot: dict[str, Any]) -> dict[str, Any]:
    domain_registry = spot["domain_registry"]
    empirical_core = [domain for domain in domain_registry if domain["domain_id"] in CORE_DOMAIN_IDS[1:]]
    return {
        "domain_total": len(domain_registry),
        "empirical_frontier_total": sum(1 for domain in empirical_core if domain["scientific_class"] == "BRIDGE_ONLY"),
        "empirical_hard_closed_total": sum(1 for domain in empirical_core if domain["closure_verdict"] == "PASS"),
        "k_level_total": len(spot["k_levels"]),
        "platinum_blocking_total": spot["global_verdict"]["core_domain_fail_closed_total"],
        "platinum_release_status": spot["global_verdict"]["closure_verdict"],
        "required_empirical_domain_total": len(empirical_core),
        "bridge_only_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "BRIDGE_ONLY"),
        "frame_only_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "FRAME_ONLY"),
        "refuted_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "REFUTED"),
        "theorem_native_total": sum(1 for domain in domain_registry if domain["scientific_class"] == "THEOREM_NATIVE"),
        "hostile_review_blocking_total": spot["global_verdict"]["hostile_review_blocking_total"],
        "program_blocking_total": spot["global_verdict"]["program_blocking_total"],
        "closed_canon_entity_total": len(spot["closed_canon"]["canon_entity_ids"]),
        "frontier_campaign_total": len(spot["frontier_workbench"]["campaigns"]),
    }


def project_foundational_dossier(spot: dict[str, Any]) -> dict[str, Any]:
    domain_boundary_rows = []
    for domain in spot["domain_registry"]:
        domain_boundary_rows.append(
            {
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "inclusion_verdict": domain["inclusion_verdict"],
                "non_inclusion_reason": domain["non_inclusion_reason"],
                "nonclaim_refs": domain["nonclaim_refs"],
                "prediction_contract_status": domain["prediction_contract_status"],
                "primary_k_levels": domain["primary_k_levels"],
                "promotion_scope_status": domain["promotion_scope_status"],
                "quantitative_validation_status": domain["quantitative_validation_status"],
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "refs": unique_strings(["releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json", *domain["source_refs"]]),
            }
        )
    k_level_doctrine = []
    for level in spot["k_levels"]:
        k_level_doctrine.append(
            {
                "level_id": level["level_id"],
                "benchmark": level["benchmark"],
                "falsifier": level["falsifier"],
                "prediction_interface_status": level["prediction_interface_status"],
                "projected_domain_ids": level["projected_domain_ids"],
                "theorem_packet_status": "PASS" if level["closure_verdict"] == "PASS" else "FAIL_CLOSED",
                "theorem_schema": level["theorem_schema"],
                "scientific_class": level["scientific_class"],
                "trace_status": level["trace_status"],
                "evidence_status": level["evidence_status"],
                "closure_verdict": level["closure_verdict"],
                "refs": unique_strings(["releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json", *level["refs"]]),
            }
        )
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
            "ts_utc": utc_now(),
        },
        "domain_boundary_rows": domain_boundary_rows,
        "k_level_doctrine": k_level_doctrine,
        "platinum_blockers": spot["global_verdict"]["blocking_ids"],
        "hostile_review_blockers": spot["global_verdict"]["hostile_review_blocking_ids"],
        "promotion_classifier_rows": [
            {
                "promotion_classifier": scientific_class,
                "meaning": {
                    "THEOREM_NATIVE": "Admitted as theorem-native science with full trace closure.",
                    "BRIDGE_ONLY": "Empirical bridge evidence exists but theorem-native closure is not yet demonstrated.",
                    "FRAME_ONLY": "Core frame constrains later science but does not itself claim standalone empirical promotion.",
                    "EXTENSION": "Extension branch may reuse the grammar but is not core canon.",
                    "REFUTED": "Explicitly excluded from the core scientific proof path.",
                }[scientific_class],
            }
            for scientific_class in ALLOWED_SCIENTIFIC_CLASSES
        ],
        "promotion_rule": {
            "empirical_promotion_rule": "EMPIRICAL_DOMAIN_PROMOTION_REQUIRES_THEOREM_NATIVE_TRACE_DATA_ROUTE_NUMERICAL_PACKET_HELD_OUT_EVIDENCE_AND_EXPLICIT_FALSIFIER",
            "journal_core_rule": "JOURNAL_CORE_MUST_BE_TRACEABLY_DERIVED_FROM_THE_MASTER_MONOGRAPH",
            "positive_outward_science_rule": "NOTHING_REACHES_POSITIVE_OUTWARD_SCIENCE_UNLESS_SPOT_TRACE_AND_EVIDENCE_ARE_BOTH_CLOSED",
            "science_spot_rule": "ALL_SCIENTIFIC_SURFACES_ARE_DERIVED_FROM_OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "governance_rule": "CLOSED_CANON_AND_FRONTIER_WORKBENCH_MUST_REMAIN_EXPLICITLY_SEPARATED",
            "anti_cycle_rule": "NO_METHOD_CLASS_MAY_REPEAT_WITHOUT_A_NEW_PREMISE_DATASET_OR_OBSERVABLE_FAMILY",
        },
        "refs": [
            "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "content/19_oc_core_1_3_foundational_consistency.tex",
            "content/20_oc_core_1_3_theorem_roadmap.tex",
            "content/21_oc_core_1_3_worked_examples.tex",
        ],
        "schema_id": "FOUNDATIONAL_CONSISTENCY_DOSSIER_v1",
        "statement_class_rows": deepcopy(STATEMENT_CLASS_ROWS),
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": foundational_summary(spot),
    }


def protocols_summary(spot: dict[str, Any]) -> dict[str, Any]:
    core_domains = [domain for domain in spot["domain_registry"] if domain["domain_id"] in CORE_DOMAIN_IDS]
    bridge_domains = [domain for domain in core_domains if domain["scientific_class"] == "BRIDGE_ONLY"]
    return {
        "domain_total": len(core_domains),
        "hard_closed_total": sum(1 for domain in core_domains if domain["closure_verdict"] == "PASS"),
        "bridge_only_fail_closed_total": sum(1 for domain in bridge_domains if domain["closure_verdict"] == "FAIL_CLOSED"),
        "hybrid_escalation_domain_total": len(core_domains),
        "institute_run_wave_total": sum(1 for domain in bridge_domains if domain["institute_run_escalation"].get("measurement_wave_id")),
        "official_partial_execution_complete_total": sum(1 for domain in bridge_domains if domain["official_route_refs"]),
        "proxy_execution_complete_total": 0,
        "ready_for_execution_total": sum(1 for domain in core_domains if domain["closure_verdict"] == "PASS"),
    }


def protocol_current_state(domain: dict[str, Any]) -> str:
    if domain["scientific_class"] == "THEOREM_NATIVE":
        return "VALIDATED_ANCHOR_ACTIVE"
    if domain["scientific_class"] == "BRIDGE_ONLY":
        return "BRIDGE_ONLY_FAIL_CLOSED"
    return "FAIL_CLOSED"


def project_domain_empirical_execution_protocols(spot: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS:
            continue
        domain_config = DOMAIN_CLOSURE_CONFIG[domain["domain_id"]]
        institute_run = deepcopy(domain["institute_run_escalation"])
        if domain["scientific_class"] == "BRIDGE_ONLY":
            institute_run["current_status"] = "STAND_BY_UNTIL_TRACE_GAPS_CLOSE"
        rows.append(
            {
                "benchmark_design": domain["benchmark_design"],
                "benchmark_wave_id": domain["benchmark_wave_id"],
                "blocking_ids": domain["gap_ids"],
                "current_state": protocol_current_state(domain),
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "evidence_bar": domain["evidence_bar"],
                "execution_basis_class": domain["execution_basis_class"],
                "execution_readiness_status": domain["closure_verdict"],
                "execution_scope": domain["execution_scope"],
                "closure_bundle_id": f"CLOSURE_BUNDLE::{domain['domain_id']}",
                "program_phase_id": domain_config["phase_id"],
                "launch_rule": domain_config["launch_rule"],
                "closure_gain_per_cost": closure_priority_score(domain_config),
                "institute_run_escalation": institute_run,
                "numerical_packet_status": domain["numerical_packet_status"],
                "official_coverage_summary": domain["official_coverage_summary"],
                "official_metrics_summary": domain["official_metrics_summary"],
                "official_route_refs": domain["official_route_refs"],
                "official_source_status": domain["official_source_status"],
                "protocol_id": domain["protocol_id"],
                "proxy_basis_allowed_for_dev_visibility": None,
                "proxy_basis_pass_eligible": None,
                "proxy_metrics_summary": {},
                "quantitative_acceptance_thresholds": domain["quantitative_acceptance_thresholds"],
                "refs": [
                    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json",
                    "releases/oc_core_1_3/editorial/PREDICTION_REPLAY_LEDGER_latest.json",
                ],
                "replay_harness": domain["replay_harness"],
                "replay_status": domain["replay_status"],
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
            }
        )
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
            "ts_utc": utc_now(),
        },
        "policy_refs": [
            "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        ],
        "rows": rows,
        "schema_id": "DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_v1",
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": protocols_summary(spot),
    }


def project_empirical_domain_validation_matrix(spot: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS:
            continue
        domain_config = DOMAIN_CLOSURE_CONFIG[domain["domain_id"]]
        is_pass = domain["closure_verdict"] == "PASS"
        checked_thresholds = deepcopy(domain["quantitative_acceptance_thresholds"])
        checked_thresholds["trace_complete_required"] = True
        checked_thresholds["theorem_native_required"] = True
        rows.append(
            {
                "benchmark_case_total": domain["matrix_snapshot"]["benchmark_case_total"],
                "benchmark_dataset_total": domain["matrix_snapshot"]["benchmark_dataset_total"],
                "blocking_ids": domain["gap_ids"],
                "case_coverage_ratio": domain["matrix_snapshot"]["case_coverage_ratio"],
                "claim_level": domain["claim_level"],
                "closure_program_status": "VALIDATED_ANCHOR_ACTIVE" if domain["scientific_class"] == "THEOREM_NATIVE" else "BRIDGE_ONLY_FAIL_CLOSED",
                "coverage_readiness_status": "PASS_CASESET_MINIMUM_REACHED" if domain["matrix_snapshot"]["minimum_cases_total"] else "NOT_REQUIRED",
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "evidence_bar": domain["evidence_bar"],
                "execution_protocol_id": domain["protocol_id"],
                "execution_protocol_status": domain["closure_verdict"],
                "execution_readiness": "ready" if is_pass else "fail_closed",
                "institute_run_measurement_wave_id": domain["institute_run_escalation"].get("measurement_wave_id", ""),
                "measurement_escalation_status": domain["institute_run_escalation"].get("current_status", "NOT_REQUIRED"),
                "measurement_provenance_status": "OFFICIAL_OR_OPEN_REPLAY_EXECUTED" if domain["official_route_refs"] else "NOT_REQUIRED",
                "measurement_wave_execution_mode": "NOT_REQUIRED" if is_pass else "REAUDIT_FIRST",
                "minimum_cases_total": domain["matrix_snapshot"]["minimum_cases_total"],
                "next_required_action": domain["next_required_action"],
                "numerical_packet_status": domain["numerical_packet_status"],
                "official_acceptance_summary": {
                    "acceptance_mode": "EXACT_MATCH_REQUIRED" if domain["domain_id"] == "MATHEMATICS" else "SIGMA_WITH_THEOREM_NATIVE_PROMOTION_BAR",
                    "checked_thresholds": checked_thresholds,
                    "failure_ids": [] if is_pass else domain["gap_ids"],
                    "pass_eligible": is_pass,
                },
                "program_phase_id": domain_config["phase_id"],
                "closure_gain_per_cost": closure_priority_score(domain_config),
                "parameterization_status": domain["quantitative_packet_status"] or "NOT_REQUIRED",
                "platinum_gate_reason": domain["classification_rationale"],
                "prediction_declared_case_total": domain["matrix_snapshot"]["prediction_declared_case_total"],
                "promotion_scope_status": domain["promotion_scope_status"],
                "quantitative_pass_result": matrix_quantitative_result(domain["domain_id"], DOMAIN_POLICY[domain["domain_id"]], domain),
                "refs": [
                    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
                    "releases/oc_core_1_3/editorial/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
                ],
                "replay_report_status": domain["replay_status"],
                "replay_status": domain["replay_status"],
                "scientific_state": domain["scientific_state"],
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "source_route_status": domain["official_source_status"],
                "validation_status": domain["closure_verdict"],
            }
        )
    pass_total = sum(1 for row in rows if row["validation_status"] == "PASS")
    return {
        "blocking_ids": [gap for domain in spot["domain_registry"] if domain["domain_id"] in CORE_DOMAIN_IDS for gap in domain["gap_ids"]],
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
            "ts_utc": utc_now(),
        },
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "foundational_consistency_dossier": "releases/oc_core_1_3/editorial/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
            "domain_empirical_execution_protocols": "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
        },
        "rows": rows,
        "schema_id": "EMPIRICAL_DOMAIN_VALIDATION_MATRIX_v1",
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": {
            "blocking_total": sum(len(row["blocking_ids"]) > 0 for row in rows),
            "bundle_backed": True,
            "bundle_task_profile": "scientific_internal",
            "checked_domain_total": len(rows),
            "measurement_escalation_required_total": 0,
            "pass_total": pass_total,
            "bridge_only_fail_closed_total": sum(1 for row in rows if row["scientific_class"] == "BRIDGE_ONLY"),
            "platinum_release_status": spot["global_verdict"]["closure_verdict"],
        },
    }


def command_phase_for(domain: dict[str, Any]) -> str:
    return "MAINTENANCE" if domain["closure_verdict"] == "PASS" else "REAUDIT"


def command_board_summary(spot: dict[str, Any]) -> dict[str, Any]:
    core_domains = [domain for domain in spot["domain_registry"] if domain["domain_id"] in CORE_DOMAIN_IDS]
    return {
        "blocked_total": sum(1 for domain in core_domains if domain["closure_verdict"] != "PASS"),
        "bundle_backed": True,
        "bundle_task_profile": "diagnostic",
        "checked_domain_total": len(core_domains),
        "executable_now_total": sum(1 for domain in core_domains if domain["closure_verdict"] == "PASS"),
        "pass_already_total": sum(1 for domain in core_domains if domain["closure_verdict"] == "PASS"),
        "stand_by_measurement_wave_total": 0,
        "reaudit_bridge_total": sum(1 for domain in core_domains if domain["scientific_class"] == "BRIDGE_ONLY"),
    }


def project_domain_hard_closure_command_board(spot: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS:
            continue
        domain_config = DOMAIN_CLOSURE_CONFIG[domain["domain_id"]]
        rows.append(
            {
                "acceptance_criterion": domain["acceptance_criterion"],
                "benchmark_case_total": domain["matrix_snapshot"]["benchmark_case_total"],
                "benchmark_dataset_total": domain["matrix_snapshot"]["benchmark_dataset_total"],
                "blocking_ids": domain["gap_ids"],
                "can_execute_now": domain["closure_verdict"] == "PASS",
                "case_coverage_ratio": domain["matrix_snapshot"]["case_coverage_ratio"],
                "claim_level": domain["claim_level"],
                "closure_wave_id": domain["benchmark_wave_id"],
                "command_phase": command_phase_for(domain),
                "command_ref": domain["replay_harness"].get("command_ref", ""),
                "coverage_readiness_status": "PASS_CASESET_MINIMUM_REACHED" if domain["matrix_snapshot"]["minimum_cases_total"] else "NOT_REQUIRED",
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "execution_protocol_status": domain["closure_verdict"],
                "execution_readiness": "ready" if domain["closure_verdict"] == "PASS" else "fail_closed",
                "falsifier_specification": domain["falsifier_specification"],
                "measurement_provenance_status": "OFFICIAL_OR_OPEN_REPLAY_EXECUTED" if domain["official_route_refs"] else "NOT_REQUIRED",
                "measurement_wave_execution_mode": "NOT_REQUIRED" if domain["closure_verdict"] == "PASS" else "REAUDIT_FIRST",
                "measurement_wave_id": domain["institute_run_escalation"].get("measurement_wave_id", ""),
                "measurement_wave_pipeline_refs": [],
                "measurement_wave_status": "NOT_REQUIRED" if domain["closure_verdict"] == "PASS" else "STAND_BY_UNTIL_TRACE_GAPS_CLOSE",
                "minimum_cases_total": domain["matrix_snapshot"]["minimum_cases_total"],
                "next_required_action": domain["next_required_action"],
                "program_phase_id": domain_config["phase_id"],
                "launch_rule": domain_config["launch_rule"],
                "closure_gain_per_cost": closure_priority_score(domain_config),
                "official_acceptance_summary": {
                    "acceptance_mode": "EXACT_MATCH_REQUIRED" if domain["domain_id"] == "MATHEMATICS" else "SIGMA_WITH_THEOREM_NATIVE_PROMOTION_BAR",
                    "pass_eligible": domain["closure_verdict"] == "PASS",
                },
                "official_coverage_summary": domain["official_coverage_summary"],
                "official_metrics_summary": domain["official_metrics_summary"],
                "parameterization_status": domain["quantitative_packet_status"] or "NOT_REQUIRED",
                "prediction_declared_case_total": domain["matrix_snapshot"]["prediction_declared_case_total"],
                "prerequisite_ids": [
                    "PINNED_SOURCE_ROUTE",
                    "BENCHMARK_DATASET_MANIFEST",
                    "NUMERICAL_PACKET_SPEC",
                    "REPLAY_HARNESS",
                    "EXPLICIT_FALSIFIER",
                    "THEOREM_NATIVE_TRACE",
                ],
                "refs": [
                    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
                    "releases/oc_core_1_3/editorial/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
                ],
                "replay_status": domain["replay_status"],
                "scientific_state": domain["scientific_state"],
                "scientific_class": domain["scientific_class"],
                "trace_status": domain["trace_status"],
                "evidence_status": domain["evidence_status"],
                "closure_verdict": domain["closure_verdict"],
                "source_route_status": domain["official_source_status"],
                "validation_status": domain["closure_verdict"],
            }
        )
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/DOMAIN_HARD_CLOSURE_COMMAND_BOARD_latest.json",
            "ts_utc": utc_now(),
        },
        "rows": rows,
        "schema_id": "DOMAIN_HARD_CLOSURE_COMMAND_BOARD_v1",
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": command_board_summary(spot),
    }


def legacy_target_state(domain: dict[str, Any]) -> str:
    if domain["closure_verdict"] == "PASS":
        return "VALIDATED_ANCHOR_ACTIVE"
    return "THEOREM_NATIVE_PASS_REQUIRED"


def project_legacy_domain_hard_closure_execution_program(spot: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS:
            continue
        rows.append(
            {
                "acceptance_criterion": domain["acceptance_criterion"],
                "benchmark_dataset_manifest": deepcopy(domain["benchmark_dataset_manifest"]),
                "benchmark_families": deepcopy(domain["benchmark_families"]),
                "blocking_ids": deepcopy(domain["gap_ids"]),
                "closure_wave_id": domain["benchmark_wave_id"],
                "current_state": protocol_current_state(domain),
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "falsifier_specification": domain["falsifier_specification"],
                "measurable_outputs": deepcopy(domain["measurable_outputs"]),
                "measurement_escalation_rule": domain["measurement_escalation_rule"],
                "measurement_escalation_status": domain["institute_run_escalation"].get("current_status", "NOT_REQUIRED"),
                "measurement_schema": domain["measurement_schema"],
                "measurement_wave_execution_mode": "NOT_REQUIRED" if domain["closure_verdict"] == "PASS" else "STAND_BY_UNTIL_TRACE_GAPS_CLOSE",
                "next_required_action": domain["next_required_action"],
                "official_acceptance_summary": {
                    "acceptance_mode": "EXACT_MATCH_REQUIRED" if domain["domain_id"] == "MATHEMATICS" else "SIGMA_WITH_THEOREM_NATIVE_PROMOTION_BAR",
                    "pass_eligible": domain["closure_verdict"] == "PASS",
                },
                "official_coverage_summary": deepcopy(domain["official_coverage_summary"]),
                "official_metrics_summary": deepcopy(domain["official_metrics_summary"]),
                "official_source_family_targets": deepcopy(domain["selected_route_institutions"]),
                "official_source_route_status": domain["official_source_status"],
                "official_source_routes": deepcopy(domain["official_route_refs"]),
                "prediction_declared_case_total": domain["matrix_snapshot"]["prediction_declared_case_total"],
                "quantitative_acceptance_thresholds": deepcopy(domain["quantitative_acceptance_thresholds"]),
                "quantitative_pass_result": domain["quantitative_acceptance_result"] if domain["closure_verdict"] == "PASS" else "BRIDGE_ONLY_FAIL_CLOSED",
                "replay_command_ref": domain["replay_harness"].get("command_ref", ""),
                "replay_status": domain["replay_status"],
                "refs": [
                    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
                    "releases/oc_core_1_3/editorial/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
                ],
                "target_state": legacy_target_state(domain),
            }
        )
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json",
            "ts_utc": utc_now(),
        },
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "domain_empirical_execution_protocols": "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
            "empirical_domain_validation_matrix": "releases/oc_core_1_3/editorial/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
        },
        "rows": rows,
        "schema_id": "DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_v1",
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": {
            "checked_domain_total": len(rows),
            "validated_anchor_total": sum(1 for row in rows if row["current_state"] == "VALIDATED_ANCHOR_ACTIVE"),
            "bridge_only_fail_closed_total": sum(1 for row in rows if row["current_state"] == "BRIDGE_ONLY_FAIL_CLOSED"),
            "target_theorem_native_total": sum(1 for row in rows if row["target_state"] == "THEOREM_NATIVE_PASS_REQUIRED"),
        },
    }


def project_legacy_institute_run_measurement_program(spot: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS[1:]:
            continue
        rows.append(
            {
                "active_observation_request_queue_ref": "",
                "active_observation_request_total": 0,
                "active_request_group_rows": [],
                "blocking_ids": deepcopy(domain["gap_ids"]),
                "current_domain_state": protocol_current_state(domain),
                "domain_id": domain["domain_id"],
                "domain_title": domain["domain_title"],
                "escalation_trigger": domain["institute_run_escalation"].get("escalation_trigger", "NOT_REQUIRED"),
                "evidence_input_refs": [
                    "releases/oc_core_1_3/editorial/DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_BENCHMARK_CASESET_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_BENCHMARK_DATASET_MANIFEST_latest.json",
                ],
                "failure_ids": deepcopy(domain["gap_ids"]),
                "lawful_ingestion_pipeline_refs": [
                    "logion/k7/spe/orchestrator/science/build_observation_request_queue_v1.py",
                    "logion/k7/spe/orchestrator/intake/build_observation_input_instance_v1.py",
                    "logion/k7/spe/orchestrator/intake/normalize_observations_v1.py",
                    "logion/k7/spe/orchestrator/intake/validate_observation_semantic_integrity_v1.py",
                ],
                "measurement_plan_summary": domain["institute_run_escalation"].get("measurement_plan_summary", ""),
                "measurement_provenance_status": "OFFICIAL_OR_OPEN_REPLAY_EXECUTED" if domain["official_route_refs"] else "NOT_REQUIRED",
                "measurement_wave_id": domain["institute_run_escalation"].get("measurement_wave_id", ""),
                "missing_family_ids": deepcopy(domain["gap_ids"]),
                "next_required_action": domain["next_required_action"],
                "open_missing_family_ids": deepcopy(domain["gap_ids"]),
                "open_observation_request_case_ids": [],
                "open_observation_request_ids": [],
                "post_wave_promotion_policy": "PROMOTE_ONLY_AFTER_THEOREM_NATIVE_TRACE_AND_QUANTITATIVE_THRESHOLDS_PASS",
                "refs": [
                    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json",
                    "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
                ],
                "wave_activation_status": domain["institute_run_escalation"].get("current_status", ""),
                "wave_execution_mode": "NOT_REQUIRED" if domain["closure_verdict"] == "PASS" else "STAND_BY_UNTIL_TRACE_GAPS_CLOSE",
                "wave_input_signature_status": "PENDING_TRACE_CLOSURE" if domain["closure_verdict"] != "PASS" else "NOT_REQUIRED",
                "wave_status": domain["institute_run_escalation"].get("current_status", "NOT_REQUIRED"),
                "wave_terminal_status": "NOT_REQUIRED" if domain["closure_verdict"] == "PASS" else "FAIL_CLOSED_UNTIL_TRACE_LOCKS",
            }
        )
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/INSTITUTE_RUN_MEASUREMENT_PROGRAM_latest.json",
            "ts_utc": utc_now(),
        },
        "rows": rows,
        "schema_id": "INSTITUTE_RUN_MEASUREMENT_PROGRAM_v1",
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": {
            "measurement_wave_total": len(rows),
            "stand_by_wave_total": sum(1 for row in rows if row["wave_execution_mode"] == "STAND_BY_UNTIL_TRACE_GAPS_CLOSE"),
            "strict_real_run_wave_total": 0,
        },
    }


def project_science_operationalization_autopropagation_contract(spot: dict[str, Any]) -> dict[str, Any]:
    targets = [
        ("SCIENCE_ARTIFACTS", "Master monograph, journal core, and companion packet set"),
        ("COCKPIT_OWNER_CATALOG", "Owner outbound artifact catalog, channel catalog, and briefs"),
        ("OUTBOUND_CHANNEL_DERIVATIVES", "Science, social, toolkit/product, and business/client payloads"),
        ("PUBLIC_RELEASE_BUNDLE", "Release manifest, Zenodo preview, editorial bundle, and source package"),
    ]
    rows = []
    for target_id, target_summary in targets:
        rows.append(
            {
                "autopropagation_status": "PASS",
                "consumer_proof_requirement": "Each target must expose the propagated ref in its authoritative contract.",
                "projection_rule": "DERIVE_ONLY_FROM_OC_CORE_1_3_SCIENCE_SPOT_AND_PROPAGATE_THE_CANONICAL_FAIL_CLOSED_OR_PASS_VERDICT_WITHOUT_MANUAL_OVERRIDE",
                "propagated_science_verdict": spot["global_verdict"]["closure_verdict"],
                "target_id": target_id,
                "target_summary": target_summary,
                "trigger_rule": "SCIENCE_SPOT_DELTA",
            }
        )
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/SCIENCE_OPERATIONALIZATION_AUTOPROPAGATION_CONTRACT_latest.json",
            "ts_utc": utc_now(),
        },
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "foundational_consistency_dossier": "releases/oc_core_1_3/editorial/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
            "domain_empirical_execution_protocols": "releases/oc_core_1_3/editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json",
            "empirical_domain_validation_matrix": "releases/oc_core_1_3/editorial/EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json",
            "domain_hard_closure_command_board": "releases/oc_core_1_3/editorial/DOMAIN_HARD_CLOSURE_COMMAND_BOARD_latest.json",
        },
        "rows": rows,
        "schema_id": "SCIENCE_OPERATIONALIZATION_AUTOPROPAGATION_CONTRACT_v1",
        "status": "PASS",
        "summary": {
            "domains_with_cases_total": len(CORE_DOMAIN_IDS) - 1,
            "executable_now_total": sum(
                1
                for domain in spot["domain_registry"]
                if domain["domain_id"] in CORE_DOMAIN_IDS[1:] and domain["closure_verdict"] == "PASS"
            ),
            "platinum_release_status": spot["global_verdict"]["closure_verdict"],
            "propagated_science_verdict": spot["global_verdict"]["closure_verdict"],
            "target_total": len(rows),
        },
    }


def project_full_scientific_closure_program(spot: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_latest.json",
            "ts_utc": utc_now(),
        },
        "summary": {
            "goal": "One continuous scientific chain from kernel through K0--K12 and domain theorems to observables, datasets, held-out replay, falsifiers, and a global verdict.",
            "current_global_verdict": spot["global_verdict"]["closure_verdict"],
            "closed_canon_status": spot["closed_canon"]["current_status"],
            "frontier_workbench_status": spot["frontier_workbench"]["current_status"],
        },
        "governance": {
            "mode": spot["scientific_program"]["governance_mode"],
            "execution_order_authority": spot["scientific_program"]["execution_order_authority"],
            "broadening_freeze_status": spot["scientific_program"]["broadening_freeze_status"],
            "broadening_freeze_rule": spot["scientific_program"]["broadening_freeze_rule"],
            "execution_cadence": spot["scientific_program"]["execution_cadence"],
            "closure_bundle_contract": spot["scientific_program"]["closure_bundle_contract"],
            "ticket_admissibility_rule": spot["scientific_program"]["ticket_admissibility_rule"],
            "closed_canon": spot["closed_canon"],
            "frontier_workbench": spot["frontier_workbench"],
            "anti_cycle_rule": spot["scientific_program"]["anti_cycle_rule"],
            "stalled_outcomes": spot["scientific_program"]["stalled_outcomes"],
        },
        "prioritization_formula": spot["scientific_program"]["prioritization_formula"],
        "method_ladder": spot["scientific_program"]["method_ladder"],
        "phase_registry": spot["scientific_program"]["phase_registry"],
        "domain_priority_board": spot["scientific_program"]["domain_priority_board"],
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "proof_obligations": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
            "hostile_review_backlog": "releases/oc_core_1_3/editorial/OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json",
            "unified_science_atlas": "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
            "domain_closure_bundles": "releases/oc_core_1_3/editorial/OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json",
            "phase1_closed_core_dossier": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json",
            "dossier_packages_dir": "releases/oc_core_1_3/editorial/dossier_packages/",
        },
        "schema_id": "OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_v1",
        "status": spot["global_verdict"]["closure_verdict"],
    }


def project_unified_science_atlas(spot: dict[str, Any]) -> dict[str, Any]:
    atlas = deepcopy(spot["unified_science_atlas"])
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
            "ts_utc": utc_now(),
        },
        **atlas,
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "foundational_consistency_dossier": "releases/oc_core_1_3/editorial/FOUNDATIONAL_CONSISTENCY_DOSSIER_latest.json",
        },
        "schema_id": "OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_v1",
        "status": atlas["atlas_status"],
    }


def project_proof_obligation_registry(spot: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
            "ts_utc": utc_now(),
        },
        "dependency_atlas": deepcopy(spot["dependency_atlas"]),
        "proof_obligation_sheets": deepcopy(spot["proof_obligation_registry"]),
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "theorem_roadmap": "content/20_oc_core_1_3_theorem_roadmap.tex",
            "worked_examples": "content/21_oc_core_1_3_worked_examples.tex",
        },
        "schema_id": "OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_v1",
        "status": "PASS",
        "summary": {
            "dependency_edge_total": len(spot["dependency_atlas"]),
            "proof_obligation_total": len(spot["proof_obligation_registry"]),
        },
    }


def project_phase1_closed_core_dossier(spot: dict[str, Any]) -> dict[str, Any]:
    bundle_rows = {row["claim_id"]: row for row in spot["domain_closure_bundles"]}
    hostile_rows = deepcopy(spot["hostile_review_backlog"])
    blocking_ids = [row["review_id"] for row in hostile_rows if row["current_status"] != "PASS"]
    status = "FAIL_CLOSED" if blocking_ids or bundle_rows["K11_K12_IRREDUCIBILITY"]["closure_verdict"] != "PASS" else "PASS"
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json",
            "ts_utc": utc_now(),
        },
        "dossier_id": "OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER",
        "phase_id": "PHASE_1_STABILIZE_CLOSED_CORE",
        "execution_order_authority": spot["scientific_program"]["execution_order_authority"],
        "broadening_freeze_status": spot["scientific_program"]["broadening_freeze_status"],
        "broadening_freeze_rule": spot["scientific_program"]["broadening_freeze_rule"],
        "dossier_package_ref": repo_rel(PHASE1_DOSSIER_DIR),
        "dossier_manifest_ref": repo_rel(PHASE1_DOSSIER_DIR / "manifest.json"),
        "dossier_readme_ref": repo_rel(PHASE1_DOSSIER_DIR / "README.md"),
        "load_bearing_core_dossier": {
            "dependency_atlas": deepcopy(spot["dependency_atlas"]),
            "proof_obligation_sheets": deepcopy(spot["proof_obligation_registry"]),
            "closure_bundle": deepcopy(bundle_rows["LOAD_BEARING_SPINE"]),
        },
        "hostile_review_dossiers": hostile_rows,
        "mathematics_anchor_maintenance": {
            **deepcopy(MATHEMATICS_ANCHOR_MAINTENANCE),
            "closure_bundle": deepcopy(bundle_rows["MATHEMATICS"]),
        },
        "k11_k12_irreducibility_fork": {
            "allowed_final_states": ["PROVED_NECESSARY_BEYOND_K10", "DEMOTED_AND_GRAPH_REBUILT"],
            "closure_bundle": deepcopy(bundle_rows["K11_K12_IRREDUCIBILITY"]),
        },
        "exit_criteria": deepcopy(PHASE1_EXIT_CRITERIA_ROWS),
        "blocking_ids": blocking_ids,
        "schema_id": "OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_v1",
        "status": status,
        "summary": {
            "dependency_edge_total": len(spot["dependency_atlas"]),
            "proof_obligation_total": len(spot["proof_obligation_registry"]),
            "hostile_review_total": len(hostile_rows),
            "hostile_review_blocking_total": len(blocking_ids),
        },
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "proof_obligations": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
            "hostile_review_backlog": "releases/oc_core_1_3/editorial/OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json",
            "closure_bundles": "releases/oc_core_1_3/editorial/OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json",
        },
    }


def project_toe_synthesis_surface(spot: dict[str, Any]) -> dict[str, Any]:
    toe = deepcopy(spot["toe_synthesis_registry"])
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
            "ts_utc": utc_now(),
        },
        **toe,
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "unified_science_atlas": "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json",
            "phase1_closed_core_dossier": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json",
            "english_master_monograph": "oc_core_1_3_master_monograph.tex",
            "toe_chapter": "content/25_oc_core_1_3_toe_synthesis.tex",
            "toe_appendix": "appendix/toe_data.tex",
        },
        "schema_id": "OC_CORE_1_3_UNIFIED_SYNTHESIS_v1",
        "status": toe["status"],
    }


def project_practical_utility_atlas(spot: dict[str, Any]) -> dict[str, Any]:
    atlas = deepcopy(spot["practical_utility_atlas"])
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json",
            "ts_utc": utc_now(),
        },
        **atlas,
        "refs": {
            "science_spot": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "toe_synthesis": "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
            "proof_machinery": "releases/oc_core_1_3/editorial/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json",
            "manuscript_chapter": "content/26_oc_core_1_3_practical_utility.tex",
            "manuscript_appendix": "appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
        },
        "schema_id": "OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_v1",
    }


def project_hostile_review_backlog(spot: dict[str, Any]) -> dict[str, Any]:
    rows = deepcopy(spot["hostile_review_backlog"])
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json",
            "ts_utc": utc_now(),
        },
        "rows": rows,
        "schema_id": "OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_v2",
        "status": "FAIL_CLOSED" if any(row["blocks_global_pass"] and row["current_status"] != "PASS" for row in rows) else "PASS",
        "summary": {
            "blocking_total": sum(1 for row in rows if row["blocks_global_pass"] and row["current_status"] != "PASS"),
            "item_total": len(rows),
            "dossier_total": len(rows),
        },
    }


def project_domain_closure_bundle_registry(spot: dict[str, Any]) -> dict[str, Any]:
    bundles = deepcopy(spot["domain_closure_bundles"])
    return {
        "metadata": {
            "repo_sha": spot["metadata"]["repo_sha"],
            "script": spot["metadata"]["script"],
            "surface": "logion/k0/governance/status/OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json",
            "ts_utc": utc_now(),
        },
        "rows": bundles,
        "schema_id": "OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_v2",
        "status": spot["global_verdict"]["closure_verdict"],
        "summary": {
            "bundle_total": len(bundles),
            "fail_closed_bundle_total": sum(1 for bundle in bundles if bundle["closure_verdict"] != "PASS"),
            "pass_bundle_total": sum(1 for bundle in bundles if bundle["closure_verdict"] == "PASS"),
            "task_total": sum(len(bundle.get("task_rows", [])) for bundle in bundles),
        },
    }


def bundle_manifest_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_type": "closure_bundle",
        "bundle_id": bundle["bundle_id"],
        "claim_id": bundle["claim_id"],
        "domain_id": bundle["domain_id"],
        "phase_id": bundle["phase_id"],
        "launch_rule": bundle["launch_rule"],
        "execution_order_authority": bundle["execution_order_authority"],
        "closure_verdict": bundle["closure_verdict"],
        "current_transition_gate": bundle["current_transition_gate"],
        "artifact_contract": deepcopy(bundle["artifact_contract"]),
        "artifact_statuses": deepcopy(bundle["artifact_statuses"]),
        "artifact_file_refs": deepcopy(bundle["artifact_file_refs"]),
        "task_ids": deepcopy(bundle["task_ids"]),
        "blocking_ids": deepcopy(bundle["blocking_ids"]),
        "refs": deepcopy(bundle["refs"]),
    }


def bundle_task_board_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_type": "closure_bundle_task_board",
        "bundle_id": bundle["bundle_id"],
        "claim_id": bundle["claim_id"],
        "phase_id": bundle["phase_id"],
        "status": bundle["closure_verdict"],
        "rows": deepcopy(bundle["task_rows"]),
    }


def bundle_artifact_context_lines(bundle: dict[str, Any], artifact_kind: str) -> list[str]:
    if artifact_kind == "theorem_packet":
        return [f"Minimum theorem-native claim: {bundle['minimum_theorem_native_claim']}"]
    if artifact_kind == "parameter_law_packet":
        return [f"Parameter-law target: {bundle['parameter_law_target']}"]
    if artifact_kind == "observable_binding_spec":
        return [
            f"Theorem-to-observable map: {', '.join(bundle['theorem_to_observable_map']) or 'none'}",
            f"Observable ids: {', '.join(bundle['observable_ids']) or 'none'}",
        ]
    if artifact_kind == "dataset_data_route_manifest":
        return [f"Pinned route institutions: {', '.join(bundle['selected_route_institutions']) or 'none'}"]
    if artifact_kind == "held_out_replay_spec":
        return [f"Held-out case ids: {', '.join(bundle['held_out_case_ids']) or 'none'}"]
    if artifact_kind == "falsifier_ledger":
        return [f"Declared falsifier: {bundle['falsifier_specification']}"]
    if artifact_kind == "counterexample_ledger":
        return [f"Counterexample-search status: {bundle['artifact_statuses']['counterexample_ledger']}"]
    if artifact_kind == "same_claim_class_comparator_ledger":
        return [f"Comparator-ledger status: {bundle['artifact_statuses']['same_claim_class_comparator_ledger']}"]
    return []


def markdown_lines_for_value(label: str, value: Any) -> list[str]:
    if value is None or value == "" or value == [] or value == {}:
        return []
    if isinstance(value, list):
        lines = [f"## {label}", ""]
        for item in value:
            if isinstance(item, dict):
                serialized = ", ".join(f"{key}={item[key]}" for key in sorted(item.keys()))
                lines.append(f"- {serialized}")
            else:
                lines.append(f"- {item}")
        return lines + [""]
    if isinstance(value, dict):
        lines = [f"## {label}", ""]
        for key in sorted(value.keys()):
            lines.append(f"- `{key}`: {value[key]}")
        return lines + [""]
    return [f"## {label}", "", str(value), ""]


def render_bundle_artifact_text(bundle: dict[str, Any], artifact_kind: str) -> str:
    task_row = next(row for row in bundle["task_rows"] if row["artifact_kind"] == artifact_kind)
    payload = deepcopy(bundle.get("artifact_payloads", {}).get(artifact_kind, {}))
    lines = [
        f"# {artifact_kind}",
        "",
        f"- Bundle: `{bundle['bundle_id']}`",
        f"- Claim: `{bundle['claim_id']}`",
        f"- Phase: `{bundle['phase_id']}`",
        f"- Current artifact status: `{bundle['artifact_statuses'][artifact_kind]}`",
        f"- Current transition gate: `{bundle['current_transition_gate']}`",
        f"- Task id: `{task_row['task_id']}`",
        f"- Assignee role: `{task_row['assignee_role']}`",
        f"- Entry gate: `{task_row['entry_gate']}`",
        f"- Pass transition: `{task_row['pass_transition']}`",
        f"- Fail transition: `{task_row['fail_transition']}`",
    ]
    for line in bundle_artifact_context_lines(bundle, artifact_kind):
        lines.append(f"- {line}")
    lines.append("")
    if payload:
        lines.extend(markdown_lines_for_value("Status", payload.get("status")))
        for field in [
            "exact_formal_statement",
            "premises",
            "derivation_steps",
            "excluded_dependencies",
            "scope_boundary",
            "symbols",
            "units",
            "regime",
            "asymptotics",
            "sign_order_constraints",
            "collapse_boundary",
            "forbidden_rubberization",
            "theorem_to_observable_map",
            "observable_ids",
            "units_by_observable",
            "dataset_field_bindings",
            "official_route_ids",
            "pinned_dataset_ids",
            "pinned_dataset_versions",
            "split_lock",
            "calibration_case_ids",
            "held_out_case_ids",
            "acceptance_metrics",
            "no_post_hoc_split_rule",
            "acceptance_criterion",
            "falsifier_classes",
            "kill_conditions",
            "boundary_statement",
            "attempted_counterexamples",
            "current_survivors",
            "resolution_state",
            "comparator_families",
            "complexity_budget",
            "verdict",
        ]:
            lines.extend(markdown_lines_for_value(field.replace("_", " ").title(), payload.get(field)))
    lines.extend(["Refs:"])
    for ref in unique_strings([*payload.get("refs", []), *bundle["refs"]]):
        lines.append(f"- `{ref}`")
    return "\n".join(lines)


def render_bundle_readme(bundle: dict[str, Any]) -> str:
    lines = [
        f"# {bundle['bundle_id']}",
        "",
        f"- Claim: `{bundle['claim_id']}`",
        f"- Phase: `{bundle['phase_id']}`",
        f"- Launch rule: `{bundle['launch_rule']}`",
        f"- Verdict: `{bundle['closure_verdict']}`",
        f"- Transition gate: `{bundle['current_transition_gate']}`",
        f"- Execution order authority: `{bundle['execution_order_authority']}`",
        f"- Blocking ids: {', '.join(bundle['blocking_ids']) or 'none'}",
        f"- Minimum theorem-native claim: {bundle['minimum_theorem_native_claim']}",
        f"- Parameter-law target: {bundle['parameter_law_target']}",
        "",
        "Artifact contract:",
    ]
    for artifact_kind in bundle["artifact_contract"]:
        lines.append(f"- `{artifact_kind}` -> `{bundle['artifact_statuses'][artifact_kind]}`")
    return "\n".join(lines)


def hostile_review_manifest_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_type": "hostile_review_dossier",
        "review_id": row["review_id"],
        "current_status": row["current_status"],
        "current_resolution_state": row["current_resolution_state"],
        "blocks_global_pass": row["blocks_global_pass"],
        "task_id": row["task_id"],
        "resolution_if_pass": row["resolution_if_pass"],
        "resolution_if_fail": row["resolution_if_fail"],
        "refs": deepcopy(row["refs"]),
    }


def render_hostile_review_readme(row: dict[str, Any]) -> str:
    lines = [
        f"# {row['review_id']}",
        "",
        f"- Status: `{row['current_status']}`",
        f"- Resolution state: `{row['current_resolution_state']}`",
        f"- Blocks global PASS: `{row['blocks_global_pass']}`",
        f"- Task id: `{row['task_id']}`",
        f"- Challenge: {row['challenge']}",
        f"- Exit criterion: {row['exit_criterion']}",
    ]
    return "\n".join(lines)


def render_hostile_review_formal_dossier(row: dict[str, Any]) -> str:
    lines = [
        f"# Formal Dossier for {row['review_id']}",
        "",
        f"- Challenge: {row.get('challenge_statement', row['challenge'])}",
        f"- Current status: `{row['current_status']}`",
        f"- Current resolution state: `{row['current_resolution_state']}`",
        f"- Resolution if pass: `{row['resolution_if_pass']}`",
        f"- Resolution if fail: `{row['resolution_if_fail']}`",
        f"- Resolution outcome: `{row.get('resolution_outcome', row['current_resolution_state'])}`",
        f"- Exit criterion: {row['exit_criterion']}",
        "",
    ]
    lines.extend(markdown_lines_for_value("Exact Theorem Route Under Attack", row.get("exact_theorem_route_under_attack")))
    lines.extend(markdown_lines_for_value("Premises", row.get("premises")))
    lines.extend(markdown_lines_for_value("Forbidden Shortcuts", row.get("forbidden_shortcuts")))
    lines.extend(markdown_lines_for_value("Formal Argument Body", row.get("formal_argument_body")))
    lines.extend(markdown_lines_for_value("Falsifier Conditions", row.get("falsifier_conditions")))
    lines.append("Refs:")
    for ref in unique_strings([row.get("source_file_ref", ""), *row["refs"]]):
        lines.append(f"- `{ref}`")
    return "\n".join(lines)


def phase1_manifest_payload(phase1: dict[str, Any]) -> dict[str, Any]:
    return {
        "package_type": "phase1_closed_core",
        "dossier_id": phase1["dossier_id"],
        "phase_id": phase1["phase_id"],
        "status": phase1["status"],
        "execution_order_authority": phase1["execution_order_authority"],
        "broadening_freeze_status": phase1["broadening_freeze_status"],
        "blocking_ids": deepcopy(phase1["blocking_ids"]),
        "summary": deepcopy(phase1["summary"]),
        "refs": deepcopy(phase1["refs"]),
    }


def render_phase1_readme(phase1: dict[str, Any]) -> str:
    lines = [
        f"# {phase1['dossier_id']}",
        "",
        f"- Phase: `{phase1['phase_id']}`",
        f"- Status: `{phase1['status']}`",
        f"- Execution order authority: `{phase1['execution_order_authority']}`",
        f"- Broadening freeze status: `{phase1['broadening_freeze_status']}`",
        f"- Blocking ids: {', '.join(phase1['blocking_ids']) or 'none'}",
        "",
        "Exit criteria:",
    ]
    for criterion in phase1["exit_criteria"]:
        lines.append(f"- {criterion}")
    return "\n".join(lines)


def render_phase1_load_bearing_text(phase1: dict[str, Any]) -> str:
    bundle = phase1["load_bearing_core_dossier"]["closure_bundle"]
    return "\n".join(
        [
            "# Load-Bearing Core Dossier",
            "",
            f"- Bundle: `{bundle['bundle_id']}`",
            f"- Verdict: `{bundle['closure_verdict']}`",
            f"- Transition gate: `{bundle['current_transition_gate']}`",
            f"- Proof obligations: `{phase1['summary']['proof_obligation_total']}`",
            f"- Dependency edges: `{phase1['summary']['dependency_edge_total']}`",
        ]
    )


def render_phase1_hostile_review_text(phase1: dict[str, Any]) -> str:
    lines = [
        "# Hostile Review Summary",
        "",
        f"- Blocking total: `{phase1['summary']['hostile_review_blocking_total']}`",
    ]
    for row in phase1["hostile_review_dossiers"]:
        lines.append(f"- `{row['review_id']}` -> `{row['current_status']}` / `{row['current_resolution_state']}`")
    return "\n".join(lines)


def render_phase1_mathematics_anchor_text(phase1: dict[str, Any]) -> str:
    lines = [
        "# Mathematics Anchor Maintenance",
        "",
        f"- Scope rule: `{phase1['mathematics_anchor_maintenance']['scope_rule']}`",
        f"- Promotion rule: `{phase1['mathematics_anchor_maintenance']['promotion_rule']}`",
        "",
        "Required actions:",
    ]
    for action in phase1["mathematics_anchor_maintenance"]["required_actions"]:
        lines.append(f"- {action}")
    return "\n".join(lines)


def render_phase1_k11_text(phase1: dict[str, Any]) -> str:
    fork = phase1["k11_k12_irreducibility_fork"]
    lines = [
        "# K11/K12 Irreducibility Fork",
        "",
        f"- Bundle: `{fork['closure_bundle']['bundle_id']}`",
        f"- Verdict: `{fork['closure_bundle']['closure_verdict']}`",
        f"- Transition gate: `{fork['closure_bundle']['current_transition_gate']}`",
        "",
        "Allowed final states:",
    ]
    for state in fork["allowed_final_states"]:
        lines.append(f"- `{state}`")
    return "\n".join(lines)


def render_phase1_exit_criteria_text(phase1: dict[str, Any]) -> str:
    lines = ["# Phase 1 Exit Criteria", ""]
    for criterion in phase1["exit_criteria"]:
        lines.append(f"- {criterion}")
    return "\n".join(lines)


def legacy_domain_packet_path(domain_id: str) -> Path:
    return LEGACY_DOMAIN_PACKET_DIR / f"{slugify_identifier(domain_id)}_domain_packet.md"


def render_legacy_domain_packet(domain: dict[str, Any]) -> str:
    lines = [
        f"# OC Core 1.3 / {domain['domain_title']} Domain Packet",
        "",
        "## Status Snapshot",
        "",
        f"- Current state: `{protocol_current_state(domain)}`",
        f"- Target state: `{legacy_target_state(domain)}`",
        f"- Scientific class: `{domain['scientific_class']}`",
        f"- Trace status: `{domain['trace_status']}`",
        f"- Closure verdict: `{domain['closure_verdict']}`",
        f"- Quantitative pass result: `{domain['quantitative_acceptance_result'] or 'BRIDGE_ONLY_FAIL_CLOSED'}`",
        f"- Next required action: `{domain['next_required_action']}`",
        f"- Replay status: `{domain['replay_status']}`",
        "",
        "## Theorem-to-Observable Map",
        "",
    ]
    for item in domain.get("theorem_to_observable_map", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Benchmark Dataset Manifest", ""])
    for item in domain.get("benchmark_dataset_manifest", []):
        lines.append(
            f"- {item.get('benchmark_id', '')}: {item.get('observable_name', '')} | {item.get('authority_ref', '')} | {item.get('dataset_url', '')} | held-out: {item.get('held_out_policy', '')}"
        )
    lines.extend(["", "## Pinned Official Route Protocol", ""])
    for route in domain.get("official_route_refs", []):
        lines.append(
            f"- {route.get('route_id', '')}: {route.get('institution', '')} ({route.get('authority_class', '')}) -> {route.get('official_url', '')} | purpose: {route.get('purpose', '')}"
        )
    lines.extend(["", "## Measurable Outputs", ""])
    for item in domain.get("measurable_outputs", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Measurement Schema",
            "",
            domain.get("measurement_schema", ""),
            "",
            "## Acceptance Criterion",
            "",
            domain.get("acceptance_criterion", ""),
            "",
            "## Falsifier",
            "",
            domain.get("falsifier_specification", ""),
            "",
            "## Quantitative Acceptance Thresholds",
            "",
        ]
    )
    for key, value in sorted(domain.get("quantitative_acceptance_thresholds", {}).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Replay Harness",
            "",
            f"- Replay command: `{domain.get('replay_harness', {}).get('command_ref', '')}`",
            f"- Evidence bar: `{domain.get('evidence_bar', '')}`",
            f"- Protocol id: `{domain.get('protocol_id', '')}`",
            "",
            "## Institute-run Escalation",
            "",
            f"- Current escalation status: `{domain.get('institute_run_escalation', {}).get('current_status', 'NOT_REQUIRED')}`",
            f"- Escalation trigger: `{domain.get('institute_run_escalation', {}).get('escalation_trigger', 'NOT_REQUIRED')}`",
            f"- Measurement wave id: `{domain.get('institute_run_escalation', {}).get('measurement_wave_id', '')}`",
            f"- Measurement plan: {domain.get('institute_run_escalation', {}).get('measurement_plan_summary', '')}",
            "",
            "## Blocking IDs",
            "",
        ]
    )
    if domain.get("gap_ids"):
        for gap_id in domain["gap_ids"]:
            lines.append(f"- `{gap_id}`")
    else:
        lines.append("- None.")
    return "\n".join(lines)


def expected_legacy_domain_packet_files(spot: dict[str, Any]) -> dict[Path, str]:
    files: dict[Path, str] = {}
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS:
            continue
        files[legacy_domain_packet_path(domain["domain_id"])] = render_legacy_domain_packet(domain)
    return files


def expected_dossier_package_files(spot: dict[str, Any]) -> dict[Path, tuple[str, Any]]:
    files: dict[Path, tuple[str, Any]] = {}
    for bundle in spot["domain_closure_bundles"]:
        files[REPO_ROOT / bundle["dossier_manifest_ref"]] = ("json", bundle_manifest_payload(bundle))
        files[REPO_ROOT / bundle["task_board_ref"]] = ("json", bundle_task_board_payload(bundle))
        files[REPO_ROOT / bundle["dossier_readme_ref"]] = ("text", render_bundle_readme(bundle))
        for artifact_kind, rel_path in bundle["artifact_file_refs"].items():
            files[REPO_ROOT / rel_path] = ("text", render_bundle_artifact_text(bundle, artifact_kind))
    for row in spot["hostile_review_backlog"]:
        files[REPO_ROOT / row["dossier_manifest_ref"]] = ("json", hostile_review_manifest_payload(row))
        files[REPO_ROOT / row["dossier_readme_ref"]] = ("text", render_hostile_review_readme(row))
        files[REPO_ROOT / row["dossier_ref"]] = ("text", render_hostile_review_formal_dossier(row))
    phase1 = project_phase1_closed_core_dossier(spot)
    files[REPO_ROOT / phase1["dossier_manifest_ref"]] = ("json", phase1_manifest_payload(phase1))
    files[REPO_ROOT / phase1["dossier_readme_ref"]] = ("text", render_phase1_readme(phase1))
    files[PHASE1_DOSSIER_DIR / "load_bearing_core_dossier.md"] = ("text", render_phase1_load_bearing_text(phase1))
    files[PHASE1_DOSSIER_DIR / "hostile_review_summary.md"] = ("text", render_phase1_hostile_review_text(phase1))
    files[PHASE1_DOSSIER_DIR / "mathematics_anchor.md"] = ("text", render_phase1_mathematics_anchor_text(phase1))
    files[PHASE1_DOSSIER_DIR / "k11_k12_irreducibility.md"] = ("text", render_phase1_k11_text(phase1))
    files[PHASE1_DOSSIER_DIR / "exit_criteria.md"] = ("text", render_phase1_exit_criteria_text(phase1))
    return files


def tex_escape(text: Any) -> str:
    value = str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = value.replace("OC Core 1.3", r"OC Core~1.3")
    return value


def publication_code_alias(text: Any) -> str:
    """Render legacy internal paths with publication-safe synthesis labels.

    Some historical file names still contain the old synthesis acronym.  The
    repository keeps those paths for compatibility, but the manuscript should
    expose the scientific role of the anchor rather than the legacy path name.
    """
    value = str(text)
    normalized = value.replace("\\", "/")
    match = re.fullmatch(r"content/toe/toe_k(\d+)(?:_(ru|de))?(?:\.tex)?", normalized)
    if match:
        locale = f" ({match.group(2).upper()})" if match.group(2) else ""
        return f"APPENDIX_Q_SYNTHESIS_DOSSIER_K{match.group(1)}{locale}"
    if re.fullmatch(r"content/toe/toe_master(?:_(ru|de))?\.tex", normalized):
        return "APPENDIX_Q_SYNTHESIS_SUPPORT_MASTER"
    aliases = {
        "content/25_oc_core_1_3_toe_synthesis.tex": "CHAPTER_25_UNIFIED_SYNTHESIS",
        "content/generated/oc_core_1_3_toe_synthesis_generated.tex": "GENERATED_UNIFIED_SYNTHESIS_SURFACE",
        "appendix/toe_data.tex": "APPENDIX_C_SYNTHESIS_CONSTANTS",
        "appendix/toe_data_ru.tex": "APPENDIX_C_SYNTHESIS_CONSTANTS_RU",
        "appendix/toe_data_de.tex": "APPENDIX_C_SYNTHESIS_CONSTANTS_DE",
        "content/_auto_core_platinum_toe_support_inputs.tex": "PLATINUM_SYNTHESIS_SUPPORT_INCLUDE_LIST",
    }
    return aliases.get(normalized, value)


def tex_code(text: Any) -> str:
    return r"\occode{" + publication_code_alias(text) + "}"


def tex_operator_binding_summary(row: dict[str, Any]) -> str:
    text = tex_escape(row["operator_binding_summary"])
    if row.get("level_id") == "K0":
        replacements = {
            r"Psi\_0": r"\(\Psi_0\)",
            r"Phi\_0": r"\(\Phi_0\)",
            r"Lambda\_0": r"\(\Lambda_0\)",
            r"F\_0": r"\(F_0\)",
            r"Q\_0": r"\(Q_0\)",
            r"U\_0": r"\(U_0\)",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
    return text


def tex_list(items: list[Any], wrap_code: bool = False) -> str:
    if not items:
        return "none"
    if wrap_code:
        return r", \allowbreak ".join(tex_code(item) for item in items)
    return r", \allowbreak ".join(tex_escape(item) for item in items)


def normalize_sentence(text: Any) -> str:
    sentence = " ".join(str(text).split()).strip()
    while sentence.endswith(".."):
        sentence = sentence[:-1]
    if sentence and not sentence.endswith((".", "!", "?", ":")):
        sentence += "."
    return sentence


def britishize_text(text: Any) -> str:
    if text is None:
        return ""
    value = str(text)
    replacements = {
        "organization": "organisation",
        "organizations": "organisations",
        "organized": "organised",
        "organizing": "organising",
        "organizational": "organisational",
        "modeling": "modelling",
        "modeled": "modelled",
        "behavior": "behaviour",
        "behaviors": "behaviours",
        "stabilization": "stabilisation",
        "prioritization": "prioritisation",
        "specialized": "specialised",
        "materialized": "materialised",
        "signaling": "signalling",
    }
    for source, target in replacements.items():
        value = re.sub(rf"\b{re.escape(source)}\b", target, value)
        value = re.sub(rf"\b{re.escape(source.capitalize())}\b", target.capitalize(), value)
    return value


def tex_math_or_text(value: Any) -> str:
    text = str(value)
    if any(token in text for token in ["\\", "^", "_"]):
        return f"${text}$"
    return tex_escape(text)


def summarize_metrics_for_tex(metric_summary: dict[str, Any], preferred_keys: list[str] | None = None) -> str:
    if not metric_summary:
        return "none"
    keys = preferred_keys or [
        "strict_campaign_acceptance_status",
        "strict_terminalized_total",
        "covered_case_total",
        "covered_held_out_case_total",
        "normalized_error_mean_abs",
        "normalized_error_p95",
        "normalized_error_max",
        "tail_breach_count",
    ]
    parts = []
    for key in keys:
        if key in metric_summary:
            parts.append(f"{tex_code(key)}={tex_escape(metric_summary[key])}")
    return r", \allowbreak ".join(parts) if parts else "none"


def summarize_metrics_for_sentence(metric_summary: dict[str, Any]) -> str:
    if not metric_summary:
        return "No quantitative replay metrics are required for this row."
    parts = []
    if "strict_campaign_acceptance_status" in metric_summary:
        parts.append(f"campaign status {tex_code(metric_summary['strict_campaign_acceptance_status'])}")
    if "strict_terminalized_total" in metric_summary:
        parts.append(f"{tex_escape(metric_summary['strict_terminalized_total'])} terminalized cases")
    if "covered_case_total" in metric_summary:
        parts.append(f"{tex_escape(metric_summary['covered_case_total'])} covered cases")
    if "covered_held_out_case_total" in metric_summary:
        parts.append(f"{tex_escape(metric_summary['covered_held_out_case_total'])} held-out cases")
    if "normalized_error_mean_abs" in metric_summary:
        parts.append(f"mean absolute normalized error {tex_escape(metric_summary['normalized_error_mean_abs'])} sigma")
    if "normalized_error_p95" in metric_summary:
        parts.append(f"95th-percentile normalized error {tex_escape(metric_summary['normalized_error_p95'])} sigma")
    if "normalized_error_max" in metric_summary:
        parts.append(f"maximum normalized error {tex_escape(metric_summary['normalized_error_max'])} sigma")
    if "tail_breach_count" in metric_summary:
        parts.append(f"tail breaches {tex_escape(metric_summary['tail_breach_count'])}")
    return normalize_sentence("; ".join(parts)) if parts else "No quantitative replay metrics are required for this row."


def summarize_thresholds_for_sentence(threshold_snapshot: dict[str, Any], minimum_cases: Any) -> str:
    parts = [f"minimum cases {tex_escape(minimum_cases)}"]
    if threshold_snapshot.get("strict_terminalized_total_min") is not None:
        parts.append(f"strictly terminalized cases at least {tex_escape(threshold_snapshot['strict_terminalized_total_min'])}")
    if threshold_snapshot.get("counterexample_survivor_total_max") is not None:
        parts.append(f"counterexample survivors capped at {tex_escape(threshold_snapshot['counterexample_survivor_total_max'])}")
    if threshold_snapshot.get("replay_divergence_total_max") is not None:
        parts.append(f"replay divergences capped at {tex_escape(threshold_snapshot['replay_divergence_total_max'])}")
    if threshold_snapshot.get("coverage_ratio_required") is not None:
        parts.append(f"coverage ratio {tex_escape(threshold_snapshot['coverage_ratio_required'])}")
    if threshold_snapshot.get("normalized_error_mean_abs_max_sigma") is not None:
        parts.append(f"mean absolute normalized error at or below {tex_escape(threshold_snapshot['normalized_error_mean_abs_max_sigma'])} sigma")
    if threshold_snapshot.get("normalized_error_p95_max_sigma") is not None:
        parts.append(f"95th-percentile normalized error at or below {tex_escape(threshold_snapshot['normalized_error_p95_max_sigma'])} sigma")
    if threshold_snapshot.get("normalized_error_max_max_sigma") is not None:
        parts.append(f"maximum normalized error at or below {tex_escape(threshold_snapshot['normalized_error_max_max_sigma'])} sigma")
    if threshold_snapshot.get("tail_breach_count_max") is not None:
        parts.append(f"tail breaches capped at {tex_escape(threshold_snapshot['tail_breach_count_max'])}")
    if threshold_snapshot.get("critical_residual_sigma_threshold") is not None:
        parts.append(f"critical residual threshold {tex_escape(threshold_snapshot['critical_residual_sigma_threshold'])} sigma")
    if threshold_snapshot.get("severe_residual_sigma_threshold") is not None:
        parts.append(f"severe residual threshold {tex_escape(threshold_snapshot['severe_residual_sigma_threshold'])} sigma")
    if threshold_snapshot.get("brier_score_max") is not None:
        parts.append(f"Brier score at or below {tex_escape(threshold_snapshot['brier_score_max'])}")
    if threshold_snapshot.get("expected_calibration_error_max") is not None:
        parts.append(f"expected calibration error at or below {tex_escape(threshold_snapshot['expected_calibration_error_max'])}")
    if threshold_snapshot.get("critical_failure_f1_min") is not None:
        parts.append(f"critical-failure F1 at least {tex_escape(threshold_snapshot['critical_failure_f1_min'])}")
    if threshold_snapshot.get("critical_failure_precision_min") is not None:
        parts.append(f"critical-failure precision at least {tex_escape(threshold_snapshot['critical_failure_precision_min'])}")
    if threshold_snapshot.get("critical_failure_recall_min") is not None:
        parts.append(f"critical-failure recall at least {tex_escape(threshold_snapshot['critical_failure_recall_min'])}")
    return normalize_sentence("; ".join(parts))


def render_toe_numeric_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        r"\begin{longtable}{@{}L{0.27\textwidth}L{0.15\textwidth}L{0.24\textwidth}L{0.16\textwidth}@{}}",
        r"\toprule",
        r"Quantity & Symbol & Value / range & Units or note \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Quantity & Symbol & Value / range & Units or note \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in rows:
        symbol_tex = str(row["symbol_tex"]).replace(",", r",\allowbreak ").replace("/", r"/\allowbreak ")
        value_tex = str(row["value_tex"]).replace(";", r";\allowbreak ")
        lines.append(
            f"{tex_escape(row['quantity'])} & $\\scriptstyle {symbol_tex}$ & ${value_tex}$ & {tex_math_or_text(row['units_note'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}"])
    return lines


def render_centered_tabular(column_spec: str, header_row: str, body_rows: list[str]) -> list[str]:
    return [
        r"\begin{center}",
        rf"\begin{{tabular}}{{{column_spec}}}",
        r"\toprule",
        header_row,
        r"\midrule",
        *body_rows,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{center}",
    ]


def tex_block_label(label: str) -> str:
    return rf"\paragraph{{{tex_escape(label)}}}"


def render_toe_support_level_tex(row: dict[str, Any]) -> str:
    lines = [
        f"% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json for {row['level_id']}",
        rf"\subsection{{Level {row['level_id']}: {tex_escape(row['level_title']).lower()}}}",
        rf"\label{{subsec:synthesis-support-{row['level_id'].lower()}}}",
        (
            f"Current closure status: {tex_code(row['closure_verdict'])}. "
            + (
                f"Promotion blockers: {tex_list(row['blocking_domain_ids'], wrap_code=True)}."
                if row["blocking_domain_ids"]
                else "Promotion blockers: none."
            )
        ),
        "",
        tex_block_label("Theorem claim."),
        tex_escape(row["theorem_native_claim"]),
        "",
        tex_block_label("Operator and K-level binding."),
        tex_operator_binding_summary(row)
        + " "
        + f"Kernel refs: {tex_list(row['operator_refs'], wrap_code=True)}.",
        "",
        tex_block_label("Parameter law."),
        r"\[",
        row["parameter_law_display"],
        r"\]",
        "",
        tex_block_label("Observable binding and units."),
        tex_escape(row["observable_map_summary"])
        + " "
        + f"Observable ids: {tex_list(row['observable_ids'], wrap_code=True)}.",
        "",
        tex_block_label("Numerical instantiation and prediction table."),
        f"Numerical backing rows are synchronized with Appendix~\\ref{{{row['appendix_table_label']}}}.",
    ]
    lines.extend(render_toe_numeric_table(row["numerical_rows"]))
    lines.extend(
        [
            "",
            tex_block_label("Falsifier and collapse boundary."),
            tex_escape(row["collapse_boundary"])
            + " "
            + f"Falsifier refs: {tex_list(row['falsifier_refs'], wrap_code=True)}.",
            "",
            tex_block_label("Closed-domain bindings."),
        ]
    )
    if row["domain_bindings"]:
        for binding in row["domain_bindings"]:
            lines.append(
                f"{tex_code(binding['domain_id'])}: class {tex_code(binding['scientific_class'])}, verdict {tex_code(binding['closure_verdict'])}, "
                f"held-out cases {tex_code(binding['held_out_case_total'])}, theorem packet {tex_code(binding['theorem_packet_status'])}, "
                f"parameter law {tex_code(binding['parameter_law_status'])}. "
                f"Packet ref: {tex_code(binding['closure_bundle_ref'] or 'none')}. "
                f"Metrics: {summarize_metrics_for_tex(binding['metric_summary'])}."
            )
    else:
        lines.append("No bound domain packets are attached to this level in the current SPOT.")
    return "\n".join(lines)


def render_toe_support_master_tex(spot: dict[str, Any]) -> str:
    toe = spot["toe_synthesis_registry"]
    branding = toe["branding"]
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        r"\section{Observed universe as a structured continuum}",
        r"\label{sec:observed-universe-continuum}",
        "",
        "This section is now generated from the canonical science SPOT as a level-anchored closure-support corpus.",
        (
            f"It therefore stays aligned with the current truth state: {tex_code(toe['release_candidate_status'])}. "
            + (
                "Public synthesis naming remains demoted until the final validator promotes the repository to PASS."
                if not toe["optimistic_toe_naming_allowed"]
                else "The final validator has promoted the repository to PASS, so unified-synthesis naming is lawful."
            )
        ),
        "",
        branding["public_intro_text"],
        "",
        "Each level file below follows one fixed proof-corpus structure: theorem claim, operator binding, parameter law, observable binding, numerical table, falsifier boundary, and current domain packet bindings.",
        "",
    ]
    for level_id in TOE_LEVEL_IDS:
        lines.append(rf"\input{{content/toe/toe_{level_id.lower()}}}")
    return "\n".join(lines)


def render_toe_support_corpus_from_spot(spot: dict[str, Any]) -> dict[str, str]:
    toe = spot["toe_synthesis_registry"]
    rendered = {"toe_master": render_toe_support_master_tex(spot)}
    for row in toe["k_level_rows"]:
        rendered[row["level_id"]] = render_toe_support_level_tex(row)
    return rendered


def render_toe_synthesis_tex(spot: dict[str, Any]) -> str:
    toe = spot["toe_synthesis_registry"]
    branding = toe["branding"]
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        rf"\section{{{tex_escape(branding['public_chapter_title'])}}}",
        r"\label{sec:oc-core-1-3-unified-synthesis}",
        f"{tex_escape(branding['public_status_label'])}: {tex_code(toe['release_candidate_status'])}.",
        "",
        normalize_sentence(branding["public_intro_text"]),
        (
            "The title and scope of this chapter follow the canonical SPOT "
            "record; release-gate metadata is confined to the opening status "
            "lines and the dedicated gate paragraph below."
        ),
        "",
        rf"\subsection{{{tex_escape(branding['public_gate_title'])}}}",
        f"Exact validator: {tex_code('FINAL_UNIFIED_SYNTHESIS_VALIDATOR_PASS')}.",
        (
            f"The release gate now reports {tex_code(toe['bridge_only_domain_total'])} bridge-only domains, "
            f"{tex_code(toe['hostile_review_blocking_total'])} hostile-review blockers, "
            f"and integrability at {tex_code(toe['integrability_suite_status'])}."
        ),
        (
            "The final promotion rule is parallel: every empirical core domain must be theorem-native; "
            "the bridge-only domain total must be zero; the hostile-review blocker total must be zero; "
            "the unified atlas and integrability suite must pass; and the K0--K12 numerical rows must remain explicit."
        ),
        (
            "No release blocker remains in the canonical SPOT."
            if not toe["release_candidate_blockers"]
            else f"Remaining release blockers: {tex_list(toe['release_candidate_blockers'], wrap_code=True)}."
        ),
    ]
    for row in toe["k_level_rows"]:
        claim_label = "Promoted theorem-native claim." if row["closure_verdict"] == "PASS" else "Candidate theorem claim."
        parameter_label = "Parameter law." if row["closure_verdict"] == "PASS" else "Target parameter law."
        promoted_bindings = [
            binding for binding in row["domain_bindings"] if binding["closure_verdict"] == "PASS"
        ]
        omitted_binding_total = len(row["domain_bindings"]) - len(promoted_bindings)
        lines.extend(
            [
                "",
                rf"\subsection{{{row['level_id']}: {tex_escape(row['level_title'])}}}",
                rf"\label{{sec:oc-core-1-3-synthesis-{row['level_id'].lower()}}}",
                (
                    f"This row is currently {tex_code(row['closure_verdict'])} and therefore contributes lawfully to the closed synthesis stack."
                    if row["closure_verdict"] == "PASS"
                    else f"This row is currently {tex_code(row['closure_verdict'])} and remains outside the promoted synthesis stack."
                ),
                (
                    f"Promotion blockers: {tex_list(row['blocking_domain_ids'], wrap_code=True)}."
                    if row["blocking_domain_ids"]
                    else "Promotion blockers: none remain at this level."
                ),
                "",
                tex_block_label(claim_label),
                normalize_sentence(tex_escape(row["theorem_native_claim"])),
                "",
                tex_block_label("Operator and K-level binding."),
                normalize_sentence(tex_operator_binding_summary(row)),
                "Core witness anchors are tabulated in Appendix~\\ref{sec:oc-core-1-3-synthesis-support-dossiers} and Appendix~\\ref{app:synthesis-constants-and-parameters}.",
                "",
                tex_block_label(parameter_label),
                r"\[",
                row["parameter_law_display"],
                r"\]",
                "",
                tex_block_label("Observable map and units."),
                normalize_sentence(tex_escape(row["observable_map_summary"])),
                f"Registered observables: {tex_list(row['observable_ids'], wrap_code=True)}.",
                "",
                tex_block_label("Numerical instantiation and prediction table."),
                f"The numerical rows below are synchronized with Appendix~\\ref{{{row['appendix_table_label']}}}.",
            ]
        )
        lines.extend(render_toe_numeric_table(row["numerical_rows"]))
        lines.extend(
            [
                "",
                tex_block_label("Falsifier and collapse boundary."),
                normalize_sentence(tex_escape(row["collapse_boundary"])),
                "Falsifier witness anchors are tabulated in Appendix~\\ref{sec:oc-core-1-3-synthesis-support-dossiers}.",
                "",
                tex_block_label("Domain packet bindings."),
            ]
        )
        if promoted_bindings:
            lines.append(r"\begin{itemize}[leftmargin=1.6em,nosep]")
            for binding in promoted_bindings:
                metric_sentence = summarize_metrics_for_sentence(binding["metric_summary"]).rstrip(".")
                if metric_sentence == "No quantitative replay metrics are required for this row":
                    metric_clause = "No quantitative replay metrics are required for this row. "
                else:
                    metric_clause = f"The key replay metrics are {metric_sentence}. "
                binding_status_clause = (
                    f"The theorem packet is {tex_code(binding['theorem_packet_status'])} "
                    f"and the parameter law is {tex_code(binding['parameter_law_status'])}. "
                )
                lines.append(
                    r"\item "
                    + f"{tex_escape(binding['domain_title'])} is closed as {tex_code(binding['scientific_class'])} with verdict {tex_code(binding['closure_verdict'])} "
                    + f"and {tex_code(binding['held_out_case_total'])} held-out cases. "
                    + binding_status_clause
                    + metric_clause
                    + "The closure dossier anchor is listed in Appendix~\\ref{sec:oc-core-1-3-synthesis-support-dossiers}."
                )
            lines.append(r"\end{itemize}")
            if omitted_binding_total:
                omitted_ids = [binding["domain_id"] for binding in row["domain_bindings"] if binding["closure_verdict"] != "PASS"]
                lines.append(
                    f"The SPOT also tracks {tex_code(omitted_binding_total)} excluded or non-promoted side bindings for this level outside the closed synthesis summary: {tex_list(omitted_ids, wrap_code=True)}. The corresponding source rows remain in the canonical surfaces and support appendices, not in the promoted synthesis stack."
                )
        else:
            lines.append("No promoted domain packets are attached to this level in the current SPOT.")
    lines.extend(
        [
            "",
            r"\subsection{Empirical Held-Out Prediction Summary}",
            normalize_sentence(branding["public_empirical_summary_text"]),
            r"Where a promoted lane carries severe cases or false negatives, those adverse metrics are reported explicitly below. The pass/fail policy is the validation matrix in Appendix~\ref{sec:oc-core-1-3-empirical-validation-matrix}; Appendix~\ref{app:synthesis-constants-and-parameters} and the canonical synthesis surface retain the full numerical record.",
            r"Metric labels are printed with their canonical surface names; \occode{critical_failure_recall} is the promoted systems recall metric used by the synthesis surface.",
            "",
        ]
    )
    lines.extend(
        [
            r"\begin{longtable}{@{}L{0.17\textwidth}L{0.11\textwidth}L{0.11\textwidth}L{0.09\textwidth}L{0.36\textwidth}@{}}",
            r"\toprule",
            r"Domain & Class & Verdict & Held-out total & Metrics \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Domain & Class & Verdict & Held-out total & Metrics \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in toe["empirical_prediction_rows"]:
        lines.append(
            f"{tex_escape(row['domain_title'])} & {tex_code(row['scientific_class'])} & {tex_code(row['closure_verdict'])} & {tex_code(row['held_out_case_total'])} & {summarize_metrics_for_tex(row['metric_summary'], preferred_keys=['covered_case_total', 'covered_held_out_case_total', 'normalized_error_mean_abs', 'normalized_error_p95', 'normalized_error_max', 'severe_case_total', 'fn', 'critical_failure_precision', 'critical_failure_recall', 'critical_failure_f1', 'tail_breach_count'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}"])
    return "\n".join(lines)


def render_practical_utility_tex(spot: dict[str, Any]) -> str:
    atlas = spot["practical_utility_atlas"]
    usable_now_rows = [row for row in atlas["use_case_rows"] if row["usable_now"]]
    frontier_rows = [row for row in atlas["use_case_rows"] if row["support_class"] == "FRONTIER_PROGRAM"]
    hypothesis_rows = [row for row in atlas["use_case_rows"] if row["support_class"] == "HYPOTHESIS_ONLY"]
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        r"\subsection{Practical value and support boundary}",
        (
            f"The practical utility atlas currently tracks {tex_code(len(usable_now_rows))} usable-now rows, "
            f"{tex_code(len(frontier_rows))} frontier-program {'row' if len(frontier_rows) == 1 else 'rows'}, "
            f"and {tex_code(len(hypothesis_rows))} hypothesis-only {'row' if len(hypothesis_rows) == 1 else 'rows'}."
        ),
    ]
    for sentence in atlas["executive_summary"]["key_points"]:
        lines.append(normalize_sentence(britishize_text(sentence)))
    lines.extend(
        [
            "",
            r"\subsection{Support classes}",
            "Every practical claim below is explicitly labeled so the reader can see what is already usable, what is bounded, and what still remains exploratory.",
            r"\begin{itemize}[leftmargin=1.6em,nosep]",
        ]
    )
    for row in atlas["support_class_legend"]:
        lines.append(
            rf"\item {tex_code(row['support_class'])} means {tex_escape(britishize_text(row['label']))}"
            + (" and is usable now within the declared bounds." if row["usable_now"] else " and is not yet a lawful usable-now claim.")
        )
    def main_trace(row: dict[str, Any], row_id_key: str) -> str:
        parts = [f"row {tex_code(row[row_id_key])}"]
        if row.get("source_bundle_ref"):
            parts.append(f"source {tex_code(row['source_bundle_ref'])}")
        if row.get("closure_bundle_ref"):
            parts.append(f"closure {tex_code(row['closure_bundle_ref'])}")
        refs = row.get("trace_refs") or row.get("source_refs") or []
        if refs:
            parts.append("refs " + tex_list(refs[:2], wrap_code=True))
        return r"; \allowbreak ".join(parts)

    lines.extend([r"\end{itemize}", "", r"\subsection{What is already usable now}"])
    lines.extend(
        [
            r"\begingroup",
            r"\scriptsize",
            r"\setlength{\emergencystretch}{1.5em}",
            r"\setlength{\tabcolsep}{2pt}",
            r"\setlength{\LTleft}{0pt}",
            r"\setlength{\LTright}{0pt}",
            r"\begin{longtable}{@{}L{0.11\textwidth}L{0.16\textwidth}L{0.19\textwidth}L{0.12\textwidth}L{0.18\textwidth}L{0.16\textwidth}@{}}",
            r"\toprule",
            r"Domain & Problem class & What OC gives now & Support & Output / decision & Trace \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Domain & Problem class & What OC gives now & Support & Output / decision & Trace \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in usable_now_rows:
        lines.append(
            f"{tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text(row['problem_class']))} & {tex_escape(britishize_text(row['what_can_be_predicted_or_done']))} & {tex_escape(britishize_text(row['support_label']))} & {tex_escape(britishize_text(row['output_or_decision']))} & {main_trace(row, 'use_case_id')} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", "", r"\subsection{How to use OC in practice}"])
    lines.append("The playbooks below answer the operational question directly: when to use OC, what inputs are required, what procedure to run, and what the resulting decision or prediction actually is.")
    for playbook in atlas["operational_playbooks"]:
        when_text = normalize_sentence(britishize_text(playbook["when_to_use"]))
        inputs_text = r"; \allowbreak ".join(tex_escape(britishize_text(item)) for item in playbook["required_inputs_or_observables"])
        procedure_text = " ".join(
            f"{index}. {tex_escape(britishize_text(item).rstrip('.'))}."
            for index, item in enumerate(playbook["procedure_steps"], start=1)
        )
        lines.extend(
            [
                "",
                rf"\paragraph{{{tex_escape(britishize_text(playbook['domain_title']))}: {tex_escape(britishize_text(playbook['title']))}}}",
                tex_escape(when_text),
                f"Inputs: {inputs_text}.",
                f"Procedure: {procedure_text.rstrip('.')}.",
                f"Output: {tex_escape(normalize_sentence(britishize_text(playbook['output_or_decision'])))}",
                f"Support class: {tex_escape(britishize_text(playbook['support_label']))}.",
                f"Trace: {main_trace(playbook, 'playbook_id')}.",
                f"Failure boundary: {tex_escape(normalize_sentence(britishize_text(playbook['failure_boundary'])))}",
            ]
        )
    lines.extend(["", r"\subsection{What OC predicts across the closed empirical domains}"])
    for domain_id in CORE_DOMAIN_IDS[1:]:
        domain = next(domain for domain in spot["domain_registry"] if domain["domain_id"] == domain_id)
        domain_rows = [row for row in atlas["use_case_rows"] if row["domain_id"] == domain_id and row["usable_now"]]
        open_rows = [row for row in atlas["use_case_rows"] if row["domain_id"] == domain_id and not row["usable_now"]]
        capability_text = "; ".join(row["what_can_be_predicted_or_done"] for row in domain_rows) if domain_rows else "No usable-now lane is currently declared"
        capability_clause = capability_text[:1].lower() + capability_text[1:] if capability_text else capability_text
        open_text = "; ".join(row["what_remains_open"] for row in open_rows) if open_rows else "no explicit frontier row remains for this domain in the current atlas"
        outputs_text = ", ".join(tex_code(item) for item in domain["measurable_outputs"])
        benchmark_text = "; ".join(
            tex_code(item) if "_BENCH_" in item else tex_escape(britishize_text(item))
            for item in domain["benchmark_families"]
        )
        row_trace_text = r"; \allowbreak ".join(main_trace(row, "use_case_id") for row in domain_rows) if domain_rows else "no usable-now use-case row"
        lines.extend(
            [
                "",
                rf"\paragraph{{{tex_escape(britishize_text(domain['domain_title']))}.}}",
                tex_escape(
                    normalize_sentence(
                        britishize_text(
                            f"For this domain, OC currently uses the closed packet to {capability_clause}"
                        )
                    )
                ),
                f"Use-case trace: {row_trace_text}.",
                f"Measured outputs: {outputs_text}.",
                f"Benchmark families: {benchmark_text}.",
                f"Held-out case total: {len(domain['held_out_case_ids'])}.",
                tex_escape(normalize_sentence(britishize_text(f"What remains open: {open_text}"))),
            ]
        )
    lines.extend(
        [
            "",
            r"\subsection{Benchmark against serious alternatives}",
            "This chapter distinguishes between simpler same-claim-class baselines and serious established model families. The first question is whether a cheaper competitor already solves the same bounded lane. The second is whether OC merely coexists with, integrates, or improves the fragmented scientific picture around that lane.",
            "Each comparison row below is an indexed main-body summary rather than a standalone verdict. The comparison id is the row-level trace anchor; Appendix~\\ref{sec:oc-core-1-3-practical-utility-atlas} expands that id into the source refs, scope boundary, comparator row, and trace hooks that make the summary auditable.",
            "",
            r"\paragraph{Same-claim-class baselines.}",
            r"\begingroup",
            r"\scriptsize",
            r"\setlength{\emergencystretch}{1.5em}",
            r"\setlength{\tabcolsep}{2pt}",
            r"\setlength{\LTleft}{0pt}",
            r"\setlength{\LTright}{0pt}",
            r"\begin{longtable}{@{}L{0.14\textwidth}L{0.10\textwidth}L{0.17\textwidth}L{0.10\textwidth}L{0.23\textwidth}L{0.18\textwidth}@{}}",
            r"\toprule",
            r"Comparison id & Domain & Comparator families & Verdict & Comparison scope & Trace \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Comparison id & Domain & Comparator families & Verdict & Comparison scope & Trace \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["same_claim_class_baseline_rows"]:
        comparison_scope = (
            tex_escape(britishize_text(row["comparison_scope"]))
            + r" \allowbreak Cost-normalized budget: "
            + tex_code(row.get("complexity_budget", "NOT_DECLARED"))
        )
        lines.append(
            f"{tex_code(row['comparison_id'])} & {tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text('; '.join(row['comparator_families'])))} & {tex_code(row['verdict'])} & {comparison_scope} & {main_trace(row, 'comparison_id')} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            r"\endgroup",
            "",
            r"\paragraph{Serious model families.}",
            r"\begingroup",
            r"\scriptsize",
            r"\setlength{\emergencystretch}{1.5em}",
            r"\setlength{\tabcolsep}{2pt}",
            r"\setlength{\LTleft}{0pt}",
            r"\setlength{\LTright}{0pt}",
            r"\begin{longtable}{@{}L{0.14\textwidth}L{0.09\textwidth}L{0.14\textwidth}L{0.12\textwidth}L{0.10\textwidth}L{0.18\textwidth}L{0.15\textwidth}@{}}",
            r"\toprule",
            r"Comparison id & Domain & Model family & Problem class & Relation to OC & What OC adds or closes & Source refs \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Comparison id & Domain & Model family & Problem class & Relation to OC & What OC adds or closes & Source refs \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["serious_model_comparison_rows"]:
        relationship_labels = {
            "complements": "complements",
            "integrates": "integrates",
            "subsumes_in_scope": "subsumes within scope",
            "still_superior_in_lane": "remains superior within its lane",
            "open": "open",
        }
        relationship_label = relationship_labels.get(row["relationship_to_oc"], row["relationship_to_oc"].replace("_", " "))
        lines.append(
            f"{tex_code(row['comparison_id'])} & {tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text(row['serious_model_family']))} & {tex_escape(britishize_text(row['problem_class']))} & {tex_escape(britishize_text(relationship_label))} & {tex_escape(britishize_text(row['what_oc_adds_or_unifies']))} & {tex_list(row['source_refs'][:2], wrap_code=True)} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", "", r"\subsection{What prior science could do, what remained fragmented, and what OC closes}"])
    lines.extend(
        [
            r"\begingroup",
            r"\scriptsize",
            r"\setlength{\emergencystretch}{1.5em}",
            r"\setlength{\tabcolsep}{2pt}",
            r"\setlength{\LTleft}{0pt}",
            r"\setlength{\LTright}{0pt}",
            r"\begin{longtable}{@{}L{0.17\textwidth}L{0.09\textwidth}L{0.17\textwidth}L{0.17\textwidth}L{0.20\textwidth}L{0.14\textwidth}@{}}",
            r"\toprule",
            r"Comparison id & Domain & Prior science already did & Fragmentation or limit & What OC closes or adds & Open boundary \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Comparison id & Domain & Prior science already did & Fragmentation or limit & What OC closes or adds & Open boundary \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["fragmentation_closure_rows"]:
        domain_title = next((item["domain_title"] for item in atlas["serious_model_comparison_rows"] if item["comparison_id"] == row["comparison_id"]), row["domain_id"])
        lines.append(
            f"{tex_code(row['comparison_id'])} & {tex_escape(britishize_text(domain_title))} & {tex_escape(britishize_text(row['prior_science_strength']))} & {tex_escape(britishize_text(row['fragmentation_boundary']))} & {tex_escape(britishize_text(row['oc_closure_or_gain']))} & {tex_escape(britishize_text(row['what_remains_open']))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", "", r"\subsection{What remains frontier or hypothesis}"])
    if frontier_rows or hypothesis_rows:
        lines.extend(
            [
                r"\begingroup",
                r"\scriptsize",
                r"\setlength{\emergencystretch}{1.5em}",
                r"\setlength{\tabcolsep}{2pt}",
                r"\setlength{\LTleft}{0pt}",
                r"\setlength{\LTright}{0pt}",
                r"\begin{longtable}{@{}L{0.11\textwidth}L{0.19\textwidth}L{0.14\textwidth}L{0.48\textwidth}@{}}",
                r"\toprule",
                r"Domain & Problem class & Support & Why this is not yet closed \\",
                r"\midrule",
                r"\endfirsthead",
                r"\toprule",
                r"Domain & Problem class & Support & Why this is not yet closed \\",
                r"\midrule",
                r"\endhead",
            ]
        )
        for row in [*frontier_rows, *hypothesis_rows]:
            lines.append(
                f"{tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text(row['problem_class']))} & {tex_escape(britishize_text(row['support_label']))} & {tex_escape(britishize_text(row['what_remains_open']))} \\\\"
            )
        lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup"])
    else:
        lines.append("No explicit frontier or hypothesis-only practical rows remain in the current atlas.")
    return "\n".join(lines)


def render_practical_utility_appendix_tex(spot: dict[str, Any]) -> str:
    atlas = spot["practical_utility_atlas"]
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        "",
        r"\begingroup",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2pt}",
        "",
        r"\subsection{Full use-case table}",
        r"\begin{longtable}{@{}L{0.13\textwidth}L{0.14\textwidth}L{0.12\textwidth}L{0.18\textwidth}L{0.17\textwidth}L{0.20\textwidth}@{}}",
        r"\toprule",
        r"Use-case id & Domain & Support & Required inputs & Output / decision & Scope boundary \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Use-case id & Domain & Support & Required inputs & Output / decision & Scope boundary \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in atlas["use_case_rows"]:
        inputs_text = r"; \allowbreak ".join(tex_escape(britishize_text(item)) for item in row["required_inputs_or_observables"])
        lines.append(
            f"{tex_code(row['use_case_id'])} & {tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text(row['support_label']))} & {inputs_text} & {tex_escape(britishize_text(row['output_or_decision']))} & {tex_escape(britishize_text(row['scope_boundary']))} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Use-case trace-anchor matrix}",
            "Trace anchors in this appendix use publication-safe alias keys for legacy compatibility filenames. The alias keys are stable release anchors resolved by the review-target manifest and by the generated projection surfaces.",
            r"\begin{longtable}{@{}L{0.16\textwidth}L{0.38\textwidth}L{0.34\textwidth}@{}}",
            r"\toprule",
            r"Use-case id & Trace anchors & Bundle / comparator hooks \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Use-case id & Trace anchors & Bundle / comparator hooks \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["use_case_rows"]:
        hook_parts = []
        if row.get("source_bundle_ref"):
            hook_parts.append(f"Source bundle {tex_code(row['source_bundle_ref'])}")
        if row.get("closure_bundle_ref"):
            hook_parts.append(f"Closure dossier {tex_code(row['closure_bundle_ref'])}")
        if row.get("benchmark_comparators"):
            hook_parts.append(
                "Comparators "
                + tex_escape(britishize_text("; ".join(row["benchmark_comparators"])))
            )
        lines.append(
            f"{tex_code(row['use_case_id'])} & {tex_list(row['trace_refs'], wrap_code=True)} & {normalize_sentence('; '.join(hook_parts) if hook_parts else 'No additional bundle hook is declared for this row')} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Operational playbook matrix}",
            r"\begin{longtable}{@{}L{0.15\textwidth}L{0.13\textwidth}L{0.18\textwidth}L{0.38\textwidth}@{}}",
            r"\toprule",
            r"Playbook id & Domain & When to use & Procedure and failure boundary \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Playbook id & Domain & When to use & Procedure and failure boundary \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["operational_playbooks"]:
        procedure_text = " ".join(
            f"{index}. {tex_escape(britishize_text(item).rstrip('.'))}."
            for index, item in enumerate(row["procedure_steps"], start=1)
        )
        lines.append(
            f"{tex_code(row['playbook_id'])} & {tex_escape(britishize_text(row['domain_title']))} & "
            f"{tex_escape(normalize_sentence(britishize_text(row['when_to_use'])))} & "
            f"Procedure: {procedure_text.rstrip('.')}. \\allowbreak Failure boundary: "
            f"{tex_escape(normalize_sentence(britishize_text(row['failure_boundary'])))} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Operational playbook trace-anchor matrix}",
            r"\begin{longtable}{@{}L{0.16\textwidth}L{0.38\textwidth}L{0.34\textwidth}@{}}",
            r"\toprule",
            r"Playbook id & Trace anchors & Bundle hooks \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Playbook id & Trace anchors & Bundle hooks \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["operational_playbooks"]:
        hook_parts = []
        if row.get("source_bundle_ref"):
            hook_parts.append(f"Source bundle {tex_code(row['source_bundle_ref'])}")
        if row.get("closure_bundle_ref"):
            hook_parts.append(f"Closure dossier {tex_code(row['closure_bundle_ref'])}")
        lines.append(
            f"{tex_code(row['playbook_id'])} & {tex_list(row['trace_refs'], wrap_code=True)} & {normalize_sentence('; '.join(hook_parts) if hook_parts else 'No additional bundle hook is declared for this playbook')} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Same-claim baseline matrix}",
            r"\begin{longtable}{@{}L{0.17\textwidth}L{0.11\textwidth}L{0.25\textwidth}L{0.35\textwidth}@{}}",
            r"\toprule",
            r"Comparison id & Domain & Comparator families & Verdict / trace anchors \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Comparison id & Domain & Comparator families & Verdict / trace anchors \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["same_claim_class_baseline_rows"]:
        trace_parts = [f"Verdict {tex_code(row['verdict'])}"]
        trace_parts.append(f"Cost-normalized budget {tex_code(row.get('complexity_budget', 'NOT_DECLARED'))}")
        if row.get("source_bundle_ref"):
            trace_parts.append(f"Source bundle {tex_code(row['source_bundle_ref'])}")
        if row.get("closure_bundle_ref"):
            trace_parts.append(f"Closure dossier {tex_code(row['closure_bundle_ref'])}")
        lines.append(
            f"{tex_code(row['comparison_id'])} & {tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text('; '.join(row['comparator_families'])))} & {normalize_sentence('; '.join(trace_parts))} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Serious model comparison matrix}",
            r"\begin{longtable}{@{}L{0.09\textwidth}L{0.14\textwidth}L{0.12\textwidth}L{0.23\textwidth}L{0.12\textwidth}L{0.22\textwidth}@{}}",
            r"\toprule",
            r"Domain & Model family & Problem class & Prior strength / fragmentation & Relation & OC gain \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Domain & Model family & Problem class & Prior strength / fragmentation & Relation & OC gain \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["serious_model_comparison_rows"]:
        prior_strength = tex_escape(normalize_sentence(britishize_text(row["what_it_already_explains_or_predicts"])))
        fragmentation = tex_escape(normalize_sentence(britishize_text(row["where_fragmentation_or_limit_remains"])))
        relationship_labels = {
            "complements": "complements",
            "integrates": "integrates",
            "subsumes_in_scope": "subsumes in scope",
            "still_superior_in_lane": "remains superior within its lane",
            "open": "open",
        }
        relationship_label = relationship_labels.get(row["relationship_to_oc"], row["relationship_to_oc"].replace("_", " "))
        lines.append(
            f"{tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text(row['serious_model_family']))} & {tex_escape(britishize_text(row['problem_class']))} & {prior_strength} \\allowbreak {fragmentation} & {tex_escape(britishize_text(relationship_label))} & {tex_escape(britishize_text(row['what_oc_adds_or_unifies']))} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Serious model comparison trace matrix}",
            r"\begin{longtable}{@{}L{0.20\textwidth}L{0.11\textwidth}L{0.33\textwidth}L{0.28\textwidth}@{}}",
            r"\toprule",
            r"Comparison id & Domain & Trace anchors & Scope boundary \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Comparison id & Domain & Trace anchors & Scope boundary \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["serious_model_comparison_rows"]:
        lines.append(
            f"{tex_code(row['comparison_id'])} & {tex_escape(britishize_text(row['domain_title']))} & {tex_list(row['source_refs'], wrap_code=True)} & {tex_escape(britishize_text(row['scope_boundary']))} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Readiness and open-frontier matrix}",
            r"\begin{longtable}{@{}L{0.15\textwidth}L{0.12\textwidth}L{0.13\textwidth}L{0.50\textwidth}@{}}",
            r"\toprule",
            r"Use-case id & Domain & Readiness & What remains open \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Use-case id & Domain & Readiness & What remains open \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in atlas["readiness_matrix_rows"]:
        lines.append(
            f"{tex_code(row['use_case_id'])} & {tex_escape(britishize_text(row['domain_title']))} & {tex_escape(britishize_text(row['support_label']))} & {tex_escape(britishize_text(row['what_remains_open']))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup"])
    return "\n".join(lines)


def render_operationalization_tex(spot: dict[str, Any]) -> str:
    core_domains = [domain for domain in spot["domain_registry"] if domain["domain_id"] in CORE_DOMAIN_IDS]
    pass_total = sum(1 for domain in core_domains if domain["closure_verdict"] == "PASS")
    fail_total = len(core_domains) - pass_total
    global_pass = spot["global_verdict"]["closure_verdict"] == "PASS"
    priority_rows = sorted(
        spot["scientific_program"]["domain_priority_board"],
        key=lambda row: (row["formal_derivation_order"], row["empirical_cost_order"]),
    )
    current_release_truth = (
        f"Mathematics is the formal anchor for exact proof obligations, while physics, chemistry, biology, and Systems / Civilizational projection now clear theorem-native closure on their locked held-out routes. "
        f"Within the declared {tex_code('CORE_1_3_SCIENCE_ONLY')} scope, the hostile-review backlog is closed and the Core~1.3 science verdict is PASS."
        if global_pass
        else f"Mathematics remains the formal anchor for exact proof obligations. Physics, chemistry, biology, and systems retain bounded bridge replay, but they do not yet qualify as theorem-native closure. The global backlog also keeps {tex_code(spot['global_verdict']['hostile_review_blocking_total'])} hostile-review dossiers open before any Core~1.3 PASS is lawful within the declared {tex_code('CORE_1_3_SCIENCE_ONLY')} scope."
    )
    release_consequence = (
        "The kernel, theorem spine, domain packets, held-out evidence, hostile-review dossiers, and unified atlas are now mutually aligned under the declared promotion bar."
        if global_pass
        else "This is not a denial of the kernel. It is a fail-closed refusal to overclaim beyond what is theorem-native, trace-complete, externally replayable, and hostile-review-clean under the declared promotion bar."
    )
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        r"\subsection{Why the present release separates explanatory force from predictive promotion}",
        "The canonical science SPOT distinguishes explanatory reach from lawful promotion. Empirical and predictive outward claims are promoted only when a domain closes one continuous trace from the kernel and K-level theorem spine through observables to held-out evidence and explicit falsifiers; theorem-native mathematical claims close by proof route rather than by measurement surface.",
        "",
        r"\subsection{Current release truth}",
        f"The canonical SPOT checks {len(core_domains)} core lanes. At present {tex_code(pass_total)} lanes satisfy the full promotion bar, while {tex_code(fail_total)} lanes remain fail-closed.",
        normalize_sentence(current_release_truth),
        "",
        r"\subsection{Closed canon and frontier workbench}",
        "The program therefore runs in two layers. Closed canon admits theorem-native results only. Frontier workbench holds broader unified-science campaigns under explicit promotion gates and may not be advertised as closed science.",
        f"The closed canon currently tracks {tex_code(len(spot['closed_canon']['canon_entity_ids']))} entities, while the frontier workbench tracks {tex_code(len(spot['frontier_workbench']['campaigns']))} active campaigns.",
        f"Execution order remains {tex_code(spot['scientific_program']['execution_order_authority'])}, and Phase 1 is tracked as a first-class dossier surface rather than as drifting editorial placeholder text.",
        "",
        r"\subsection{Closure economics and anti-cycle law}",
        f"Priority is ranked by {tex_escape(spot['scientific_program']['prioritization_formula'])}.",
        f"Anti-cycle rule: {normalize_sentence(tex_escape(spot['scientific_program']['anti_cycle_rule']))}",
        "",
        r"\subsection{Program board}",
        r"\begin{longtable}{@{}L{0.15\textwidth}L{0.07\textwidth}L{0.07\textwidth}L{0.10\textwidth}L{0.16\textwidth}L{0.20\textwidth}@{}}",
        r"\toprule",
        r"Domain & Formal order & Cost order & Gain per cost & Phase & Launch rule \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Domain & Formal order & Cost order & Gain per cost & Phase & Launch rule \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in priority_rows:
        lines.append(
            f"{tex_escape(row['domain_title'])} & {tex_escape(row['formal_derivation_order'])} & {tex_escape(row['empirical_cost_order'])} & {tex_code(row['closure_gain_per_cost'])} & {tex_code(row['phase_id'])} & {tex_code(row['launch_rule'])} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            "",
            r"\subsection{Domain order and promotion rule}",
            "The formal derivation order remains physics, chemistry, biology, and then Systems / Civilizational projection. The empirical cost order lets cheaper systems data preparation run early, but final systems promotion still waits for the biology formal route to lock.",
            "Bridge evidence may support the research program, but it cannot by itself promote a domain to closed science.",
            "",
            r"\subsection{Operationalization table}",
            r"\begin{longtable}{@{}L{0.16\textwidth}L{0.11\textwidth}L{0.13\textwidth}L{0.13\textwidth}L{0.10\textwidth}L{0.17\textwidth}@{}}",
            r"\toprule",
            r"Domain & Class & Trace & Evidence & Verdict & Next lawful action \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Domain & Class & Trace & Evidence & Verdict & Next lawful action \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for domain in core_domains:
        lines.append(
            f"{tex_escape(domain['domain_title'])} & {tex_code(domain['scientific_class'])} & {tex_code(domain['trace_status'])} & {tex_code(domain['evidence_status'])} & {tex_code(domain['closure_verdict'])} & {tex_code(domain['next_required_action'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", "", r"\subsection{Per-domain status}"])
    for domain in core_domains:
        lines.extend(
            [
                rf"\paragraph{{{tex_escape(domain['domain_title'])}.}}",
                f"Wave {tex_code(domain['benchmark_wave_id'] or 'NONE')} currently places the domain in class {tex_code(domain['scientific_class'])}, with trace status {tex_code(domain['trace_status'])}, evidence status {tex_code(domain['evidence_status'])}, and verdict {tex_code(domain['closure_verdict'])}.",
                f"Benchmark families cover {tex_list(domain['benchmark_families'], wrap_code=True)}.",
                f"Measured outputs track {tex_list(domain['measurable_outputs'], wrap_code=True)}.",
                f"Measurement schema: {normalize_sentence(tex_escape(domain['measurement_schema']))}",
                (
                    "The theorem-to-observable route has three claims. "
                    + " ".join(normalize_sentence(tex_escape(item)) for item in domain["theorem_to_observable_map"])
                    if domain["theorem_to_observable_map"]
                    else "This formal lane does not introduce a separate external theorem-to-observable route; it closes as a theorem-native mathematical anchor without an additional measurement surface."
                ),
                f"Acceptance criterion: {normalize_sentence(tex_escape(domain['acceptance_criterion']))}",
                f"Falsifier: {normalize_sentence(tex_escape(domain['falsifier_specification']))}",
                f"Primary route institutions: {tex_list(domain['selected_route_institutions'])}.",
                f"Numerical packet / replay status: {tex_code(domain['numerical_packet_status'] or 'NOT_REQUIRED')} / {tex_code(domain['replay_status'] or 'NOT_REQUIRED')}.",
                f"Open gaps: {tex_list(domain['gap_types'])}.",
                f"Next lawful action: {tex_code(domain['next_required_action'])}.",
                "",
            ]
        )
    lines.extend(
        [
            r"\subsection{Release consequence}",
            f"The scientific SPOT therefore sets the Core~1.3 science verdict, within scope {tex_code('CORE_1_3_SCIENCE_ONLY')}, to {tex_code(spot['global_verdict']['closure_verdict'])}.",
            release_consequence,
        ]
    )
    return "\n".join(lines)


def render_protocols_tex(spot: dict[str, Any]) -> str:
    core_domains = [domain for domain in spot["domain_registry"] if domain["domain_id"] in CORE_DOMAIN_IDS]
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        "The evidence bar is now locked to the canonical SPOT rather than to drifting summary surfaces. The mathematics anchor is replay-only: it requires deterministic exact replay rather than a data-backed benchmark route. The empirical domain lanes require held-out results that clear the declared five-sigma bar without tail-breach inflation. Residual containment by itself is not enough for promotion.",
        "",
        r"\subsection{Global evidence bar}",
        "The default empirical bar remains hybrid escalation: official or open primary data first, then institute-run measurements only if the observable family cannot be closed otherwise. That escalation sits behind theorem-native trace closure rather than replacing it.",
        "",
        r"\subsection{Execution protocol matrix}",
        r"\begingroup",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{1.5pt}",
        r"\begin{longtable}{@{}L{0.13\textwidth}L{0.10\textwidth}L{0.12\textwidth}L{0.14\textwidth}L{0.16\textwidth}L{0.13\textwidth}L{0.10\textwidth}@{}}",
        r"\toprule",
        r"Domain & Wave & Evidence bar & Held-out policy & Replay command & Replay status & Closure verdict \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Domain & Wave & Evidence bar & Held-out policy & Replay command & Replay status & Closure verdict \\",
        r"\midrule",
        r"\endhead",
    ]
    for domain in core_domains:
        replay_command = domain["replay_harness"].get("command_ref", "NOT_REQUIRED")
        replay_command = replay_command.replace("logion/k7/spe/orchestrator/science/", "")
        lines.append(
            f"{tex_escape(domain['domain_title'])} & {tex_code(domain['benchmark_wave_id'] or 'NONE')} & {tex_code(domain['evidence_bar'])} & {tex_code(domain['benchmark_design'].get('held_out_policy', 'NOT_REQUIRED'))} & {tex_code(replay_command)} & {tex_code(domain.get('replay_status', 'NOT_RECORDED'))} & {tex_code(domain['closure_verdict'])} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{longtable}",
            r"\endgroup",
            "",
            r"\subsection{Method ladder}",
            r"\begin{longtable}{@{}L{0.07\textwidth}L{0.18\textwidth}L{0.26\textwidth}L{0.27\textwidth}@{}}",
            r"\toprule",
            r"Order & Method class & Entry rule & Anti-cycle condition \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Order & Method class & Entry rule & Anti-cycle condition \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in spot["scientific_program"]["method_ladder"]:
        lines.append(
            f"{tex_escape(row['order'])} & {tex_code(row['method_class'])} & {tex_escape(row['entry_rule'])} & {tex_escape(row['anti_cycle_condition'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", "", r"\subsection{Per-domain escalation doctrine}"])
    for domain in core_domains:
        threshold_snapshot = domain["quantitative_acceptance_thresholds"]
        lines.extend(
            [
                rf"\paragraph{{{tex_escape(domain['domain_title'])}.}}",
                f"Protocol {tex_code(domain['protocol_id'] or 'NONE')} runs under evidence bar {tex_code(domain['evidence_bar'])} and currently reports readiness {tex_code(domain['closure_verdict'])}.",
                f"Closure phase: {tex_code(DOMAIN_CLOSURE_CONFIG[domain['domain_id']]['phase_id'])}. Launch rule: {tex_code(DOMAIN_CLOSURE_CONFIG[domain['domain_id']]['launch_rule'])}.",
                f"Pinned route institutions: {tex_list(domain['selected_route_institutions'])}.",
                f"Held-out policy: {tex_code(domain['benchmark_design'].get('held_out_policy', 'NOT_REQUIRED'))}, with minimum cases {tex_code(domain['matrix_snapshot']['minimum_cases_total'])}.",
                f"Quantitative gate: {summarize_thresholds_for_sentence(threshold_snapshot, domain['matrix_snapshot']['minimum_cases_total'])}",
                f"Replay harness: {tex_code(domain['replay_harness'].get('command_ref', 'NOT_REQUIRED'))}.",
                f"Institute-run trigger: {tex_code(domain['institute_run_escalation'].get('escalation_trigger', 'NOT_REQUIRED'))}. Measurement wave: {tex_code(domain['institute_run_escalation'].get('measurement_wave_id', 'NONE') or 'NONE')}.",
                f"Open gaps: {tex_list(domain['gap_types'])}.",
                f"Escalation plan: {normalize_sentence(tex_escape(domain['measurement_escalation_rule']))}",
                "",
            ]
        )
    return "\n".join(lines)


def competition_rows_for_spot(spot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "competition_id": "SAME_CLAIM_CLASS::META_MODEL",
            "competition_class": "SAME_CLAIM_CLASS_METAMODEL",
            "evaluation_status": "PENDING_COMPLEXITY_PENALIZED_SAME_CLAIM_CLASS_COMPARISON",
            "comparison_scope": "Whole-kernel explanatory and predictive claim class",
        }
    ]
    for domain in spot["domain_registry"]:
        if domain["domain_id"] not in CORE_DOMAIN_IDS[1:]:
            continue
        rows.append(
            {
                "competition_id": f"DOMAIN_BASELINE::{domain['domain_id']}",
                "competition_class": "DOMAIN_BASELINE",
                "evaluation_status": "DOMAIN_BASELINE_COMPARISON_PASS_ELIGIBLE" if domain["closure_verdict"] == "PASS" else "BRIDGE_ONLY_REAUDIT_REQUIRED",
                "comparison_scope": domain["classification_rationale"],
            }
        )
    return rows


def render_proof_machinery_tex(spot: dict[str, Any]) -> str:
    summary = foundational_summary(spot)
    competition_rows = competition_rows_for_spot(spot)
    ready_total = sum(1 for row in competition_rows if row["evaluation_status"] == "DOMAIN_BASELINE_COMPARISON_PASS_ELIGIBLE")
    global_pass = spot["global_verdict"]["closure_verdict"] == "PASS"
    hostile_review_sentence = (
        "The hostile-review backlog is now fully locked, so no open dossier remains capable of blocking the promoted global PASS."
        if summary["hostile_review_blocking_total"] == 0
        else f"The current program also keeps {tex_code(summary['hostile_review_blocking_total'])} hostile-review dossiers open, and these dossiers block any future global PASS even if the domain packets later close."
    )
    irreducibility_sentence = (
        f"The strongest honest meta-result remains {tex_code('STRONGEST_IMPOSSIBILITY_BOUNDARY')}, and K11/K12 now stand under a locked irreducibility result beyond K10."
        if global_pass
        else f"The strongest honest meta-result remains {tex_code('STRONGEST_IMPOSSIBILITY_BOUNDARY')} rather than a blurred uniqueness slogan. K11 and K12 now live under an explicit irreducibility campaign rather than under decorative level inflation."
    )
    atlas_sentence = (
        f"The unified atlas status is {tex_code(spot['unified_science_atlas']['atlas_status'])}. Shared operators are now globally locked across closed domains and no surviving cross-domain contradiction remains in the falsifier matrix."
        if spot["unified_science_atlas"]["atlas_status"] == "PASS"
        else f"The unified atlas status is {tex_code(spot['unified_science_atlas']['atlas_status'])}. Shared operators may not receive incompatible meanings across closed domains, and any unresolved cross-domain contradiction remains a global falsifier candidate."
    )
    return "\n".join(
        [
            "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "The proof machinery is projected from one scientific authority. This keeps foundational consistency, empirical bridge status, revision law, and competition pressure under one coherent scientific verdict instead of across contradictory summary layers.",
            "",
            r"\subsection{Consistency and promotion law}",
            f"The foundational dossier tracks {tex_code(summary['k_level_total'])} K-level doctrine rows and sets the overall science verdict to {tex_code(summary['platinum_release_status'])}.",
            "The promotion law keeps two gates distinct. A derived claim is admissible only when it is source-bound, proof-bound, and dependency-exact. An empirical claim must satisfy the foundational empirical gate: standalone domain packet, data route, numerical packet, replay procedure, and explicit falsifier. Separately, the science SPOT invariant requires held-out evidence to be locked before replay and to survive the declared thresholds. The theorem-to-observable trace remains packet evidence, not an extra foundational gate.",
            normalize_sentence(hostile_review_sentence),
            "Closure work is now executed through generated dossier packages and a first-class Phase 1 closed-core dossier rather than through drifting editorial reminders.",
            "",
            r"\subsection{Revision law}",
            f"The declared revision mutability remains {tex_code('DERIVED_FIRST')}, while the root revision status remains {tex_code('LOCKED_PENDING_ACCUMULATED_CROSS_DOMAIN_FAILURE')}.",
            "",
            r"\subsection{Proof obligations}",
            f"The load-bearing dependency atlas now tracks {tex_code(len(spot['dependency_atlas']))} explicit spine edges and {tex_code(len(spot['proof_obligation_registry']))} proof-obligation sheets. Together they replace vague prose summaries with explicit admissibility burdens, forbidden shortcuts, excluded dependencies, and falsifier conditions.",
            "",
            r"\subsection{Minimality and irreducibility}",
            normalize_sentence(irreducibility_sentence),
            "",
            r"\subsection{Alternative-model competition}",
            f"The competition policy remains {tex_code('BOTH')}: same-claim-class competition and domain-baseline competition are both in force. The matrix currently tracks {tex_code(len(competition_rows))} comparison rows, of which {tex_code(ready_total)} are pass-eligible under the present SPOT.",
            "",
            r"\subsection{Unified-science atlas}",
            normalize_sentence(atlas_sentence),
            "",
            r"\subsection{Compression as a bounded metric}",
            f"The release treats compression as {tex_code('BOUNDED_METRIC')} rather than as a central theorem claim. Coverage per rooted theorem-support statement remains {tex_code(COMPRESSION_ROWS[0]['performance_value'])}, while coverage per active numerical packet remains {tex_code(COMPRESSION_ROWS[1]['performance_value'])}.",
        ]
    )


def render_appendix_matrix_tex(spot: dict[str, Any]) -> str:
    core_domains = [domain for domain in spot["domain_registry"] if domain["domain_id"] in CORE_DOMAIN_IDS]
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        "This appendix is projected from the canonical SPOT. It reports both bridge evidence and promotion verdicts without letting one masquerade as the other.",
        "",
    ]
    table_rows: list[str] = []
    for domain in core_domains:
        sources = ", ".join(domain["selected_route_institutions"]) or "none"
        replay_ref = domain["replay_harness"].get("command_ref", "NOT_REQUIRED")
        metric_summary = domain["metric_summary"]
        metric_notes = []
        if metric_summary.get("strict_campaign_acceptance_status"):
            metric_notes.append(f"Campaign {tex_code(metric_summary['strict_campaign_acceptance_status'])}")
        if metric_summary.get("strict_terminalized_total") is not None:
            metric_notes.append(f"{tex_escape(metric_summary['strict_terminalized_total'])} terminalized cases")
        if metric_summary.get("covered_case_total") is not None:
            covered = tex_escape(metric_summary["covered_case_total"])
            held_out = tex_escape(metric_summary.get("covered_held_out_case_total", "0"))
            metric_notes.append(f"{covered} covered / {held_out} held-out cases")
        if metric_summary.get("normalized_error_mean_abs") is not None:
            metric_notes.append(
                "Mean abs. normalized error "
                f"{tex_escape(metric_summary['normalized_error_mean_abs'])} sigma"
            )
        if metric_summary.get("normalized_error_p95") is not None:
            metric_notes.append(
                f"P95 normalized error {tex_escape(metric_summary['normalized_error_p95'])} sigma"
            )
        if metric_summary.get("normalized_error_max") is not None:
            metric_notes.append(
                f"Maximum normalized error {tex_escape(metric_summary['normalized_error_max'])} sigma"
            )
        if metric_summary.get("tail_breach_count") is not None:
            metric_notes.append(f"Tail breaches {tex_escape(metric_summary['tail_breach_count'])}")
        notes = [
            f"Sources: {tex_escape(sources)}",
            f"Replay: {tex_code(replay_ref)}",
            f"Metrics: {'; '.join(metric_notes) if metric_notes else 'No quantitative replay metrics are required for this row.'}",
            f"Next action: {tex_code(domain['next_required_action'])}",
        ]
        table_rows.append(
            f"{tex_escape(domain['domain_title'])} & {tex_code(domain['scientific_class'])} & {tex_code(domain['trace_status'])} & {tex_code(domain['evidence_status'])} & {tex_code(domain['closure_verdict'])} & {tex_list(domain['gap_ids'], wrap_code=True)} & {'; '.join(notes)} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.14\textwidth}L{0.10\textwidth}L{0.10\textwidth}L{0.10\textwidth}L{0.08\textwidth}L{0.10\textwidth}L{0.32\textwidth}@{}",
            r"Domain & Class & Trace & Evidence & Verdict & Blocking ids & Notes \\",
            table_rows,
        )
    )
    return "\n".join(lines)


def render_appendix_proof_tex(spot: dict[str, Any]) -> str:
    competition_rows = competition_rows_for_spot(spot)
    priority_rows = sorted(
        spot["scientific_program"]["domain_priority_board"],
        key=lambda row: (row["formal_derivation_order"], row["empirical_cost_order"]),
    )
    lines = [
        "% Generated from OC_CORE_1_3_SCIENCE_SPOT_latest.json",
        r"\subsection{Revision law authority}",
    ]
    revision_rows: list[str] = []
    for row in REVISION_LAW_ROWS:
        revision_rows.append(
            f"{tex_escape(row['priority'])} & {tex_code(row['layer'])} & {tex_code(row['revision_rule'])} & {tex_code(row['conflict_trigger'])} & {tex_code(row['current_status'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.08\textwidth}L{0.17\textwidth}L{0.23\textwidth}L{0.24\textwidth}L{0.22\textwidth}@{}",
            r"Priority & Layer & Revision rule & Conflict trigger & Current status \\",
            revision_rows,
        )
    )
    lines.extend(["", r"\subsection{Load-bearing proof obligations}"])
    obligation_rows: list[str] = []
    for row in spot["proof_obligation_registry"]:
        obligation_rows.append(
            f"{tex_code(row['obligation_id'])} & {tex_escape(row['statement'])} & {tex_escape(', '.join(row['excluded_dependencies']))} & {tex_escape(row['falsifier_condition'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.18\textwidth}L{0.28\textwidth}L{0.22\textwidth}L{0.26\textwidth}@{}",
            r"Obligation id & Statement & Excluded dependencies & Falsifier condition \\",
            obligation_rows,
        )
    )
    lines.extend(["", r"\subsection{Hostile-review backlog}"])
    hostile_rows: list[str] = []
    for row in spot["hostile_review_backlog"]:
        hostile_rows.append(
            f"{tex_code(row['review_id'])} & {tex_escape(row['challenge'])} & {tex_code(row['current_status'])} & {tex_code(row.get('current_resolution_state', 'NOT_RECORDED'))} & {tex_escape(row['exit_criterion'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.18\textwidth}L{0.25\textwidth}L{0.11\textwidth}L{0.15\textwidth}L{0.23\textwidth}@{}",
            r"Review id & Challenge & Status & Lock state & Exit criterion \\",
            hostile_rows,
        )
    )
    lines.extend(["", r"\subsection{Closure priority board}"])
    priority_table_rows: list[str] = []
    for row in priority_rows:
        priority_table_rows.append(
            f"{tex_escape(row['domain_title'])} & {tex_escape(row['formal_derivation_order'])} & {tex_escape(row['empirical_cost_order'])} & {tex_code(row['closure_gain_per_cost'])} & {tex_code(row['phase_id'])} & {tex_escape(row['parallelism_note'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.16\textwidth}L{0.09\textwidth}L{0.09\textwidth}L{0.10\textwidth}L{0.18\textwidth}L{0.30\textwidth}@{}",
            r"Domain & Formal order & Cost order & Gain per cost & Phase & Parallelism note \\",
            priority_table_rows,
        )
    )
    lines.extend(["", r"\subsection{Minimality and irreducibility ablation ledger}"])
    minimality_rows: list[str] = []
    for row in MINIMALITY_ROWS:
        minimality_rows.append(
            f"{tex_code(row['component'])} & {tex_code(row['kind'])} & {tex_code(row['ablation_status'])} & {tex_escape(row['removal_effect'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.20\textwidth}L{0.14\textwidth}L{0.23\textwidth}L{0.35\textwidth}@{}",
            r"Component & Kind & Ablation status & Removal effect \\",
            minimality_rows,
        )
    )
    lines.extend(["", r"\subsection{Alternative-model competition matrix}"])
    competition_table_rows: list[str] = []
    for row in competition_rows:
        competition_table_rows.append(
            f"{tex_code(row['competition_id'])} & {tex_code(row['competition_class'])} & {tex_code(row['evaluation_status'])} & {tex_escape(row['comparison_scope'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.22\textwidth}L{0.16\textwidth}L{0.20\textwidth}L{0.34\textwidth}@{}",
            r"Competition id & Class & Evaluation status & Comparison scope \\",
            competition_table_rows,
        )
    )
    lines.extend(["", r"\subsection{Bounded compression benchmark}"])
    compression_rows: list[str] = []
    for row in COMPRESSION_ROWS:
        compression_rows.append(
            f"{tex_code(row['axis'])} & {tex_escape(row['complexity_units'])} & {tex_escape(row['performance_value'])} & {tex_escape(row['interpretation'])} \\\\"
        )
    lines.extend(
        render_centered_tabular(
            r"@{}L{0.24\textwidth}L{0.12\textwidth}L{0.13\textwidth}L{0.41\textwidth}@{}",
            r"Axis & Complexity units & Performance value & Interpretation \\",
            compression_rows,
        )
    )
    return "\n".join(lines)


def project_surfaces_from_spot(spot: dict[str, Any]) -> dict[str, Any]:
    return {
        "foundational": project_foundational_dossier(spot),
        "protocols": project_domain_empirical_execution_protocols(spot),
        "matrix": project_empirical_domain_validation_matrix(spot),
        "command_board": project_domain_hard_closure_command_board(spot),
        "legacy_hard_closure_program": project_legacy_domain_hard_closure_execution_program(spot),
        "legacy_institute_run_program": project_legacy_institute_run_measurement_program(spot),
        "autoprop": project_science_operationalization_autopropagation_contract(spot),
        "closure_program": project_full_scientific_closure_program(spot),
        "atlas": project_unified_science_atlas(spot),
        "proof_obligations": project_proof_obligation_registry(spot),
        "hostile_review": project_hostile_review_backlog(spot),
        "closure_bundles": project_domain_closure_bundle_registry(spot),
        "phase1_dossier": project_phase1_closed_core_dossier(spot),
        "toe_synthesis": project_toe_synthesis_surface(spot),
        "practical_utility": project_practical_utility_atlas(spot),
    }


def render_tex_from_spot(spot: dict[str, Any]) -> dict[str, str]:
    return {
        "operationalization": render_operationalization_tex(spot),
        "protocols": render_protocols_tex(spot),
        "proof_machinery": render_proof_machinery_tex(spot),
        "toe_synthesis": render_toe_synthesis_tex(spot),
        "practical_utility": render_practical_utility_tex(spot),
        "appendix_matrix": render_appendix_matrix_tex(spot),
        "appendix_proof": render_appendix_proof_tex(spot),
        "appendix_practical_utility": render_practical_utility_appendix_tex(spot),
    }


def assert_ref_exists(repo_root: Path, ref: str, errors: list[str]) -> None:
    if ref.startswith("logion/") or ref.startswith("http://") or ref.startswith("https://"):
        return
    path = repo_root / ref
    if not path.exists():
        errors.append(f"Missing reference path: {ref}")


def validate_spot_structure(
    spot: dict[str, Any],
    repo_root: Path | None = None,
    science_sources: dict[str, Any] | None = None,
) -> list[str]:
    repo_root = repo_root or REPO_ROOT
    science_sources = science_sources or {}
    errors: list[str] = []
    for key in [
        "policy",
        "kernel",
        "k_levels",
        "theorem_spine",
        "observable_registry",
        "domain_registry",
        "branch_registry",
        "closed_canon",
        "frontier_workbench",
        "dependency_atlas",
        "proof_obligation_registry",
        "hostile_review_backlog",
        "domain_closure_bundles",
        "unified_science_atlas",
        "toe_synthesis_registry",
        "practical_utility_atlas",
        "scientific_program",
        "gap_closure_registry",
        "surface_projection_manifest",
        "global_verdict",
    ]:
        if key not in spot:
            errors.append(f"Missing SPOT section: {key}")
    entities = (
        spot.get("domain_registry", [])
        + spot.get("branch_registry", [])
        + spot.get("k_levels", [])
        + spot.get("theorem_spine", [])
        + spot.get("observable_registry", [])
        + spot.get("dependency_atlas", [])
        + spot.get("proof_obligation_registry", [])
        + spot.get("hostile_review_backlog", [])
    )
    for entity in entities:
        if entity.get("scientific_class") not in ALLOWED_SCIENTIFIC_CLASSES:
            errors.append(f"Illegal scientific_class: {entity.get('scientific_class')}")
        if entity.get("closure_verdict") not in ALLOWED_CLOSURE_VERDICTS:
            errors.append(f"Illegal closure_verdict: {entity.get('closure_verdict')}")
    branch_class_map = {branch["branch_id"]: branch["scientific_class"] for branch in spot.get("branch_registry", [])}
    for domain in spot.get("domain_registry", []):
        if domain["scope_role"] == "core_domain":
            if not domain.get("theorem_refs"):
                errors.append(f"{domain['domain_id']}: missing theorem refs")
            if not domain.get("observable_ids"):
                errors.append(f"{domain['domain_id']}: missing observable ids")
            if not domain.get("falsifier_refs"):
                errors.append(f"{domain['domain_id']}: missing falsifier refs")
            if domain["scientific_class"] == "THEOREM_NATIVE" and domain["closure_verdict"] != "PASS":
                errors.append(f"{domain['domain_id']}: theorem-native domains must pass")
            if domain["scientific_class"] == "BRIDGE_ONLY" and domain["closure_verdict"] != "FAIL_CLOSED":
                errors.append(f"{domain['domain_id']}: bridge-only domains must stay fail-closed")
            if domain["scientific_class"] == "BRIDGE_ONLY" and not domain.get("gap_types"):
                errors.append(f"{domain['domain_id']}: bridge-only domain is missing gap registry")
            forbidden = [
                branch_id
                for branch_id in domain.get("core_proof_path_branch_ids", [])
                if branch_class_map.get(branch_id) in {"EXTENSION", "REFUTED"}
            ]
            if forbidden:
                errors.append(f"{domain['domain_id']}: forbidden branch leakage {forbidden}")
        if domain["scientific_class"] in {"THEOREM_NATIVE", "BRIDGE_ONLY"}:
            for ref in [*domain.get("theorem_refs", []), *domain.get("root_operator_refs", []), *domain.get("falsifier_refs", [])]:
                assert_ref_exists(repo_root, ref, errors)
    packaging = spot.get("policy", {}).get("packaging_surface_exclusion", [])
    if "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_ARTIFACT_CONTRACT.json" not in packaging:
        errors.append("Packaging surface exclusion is missing the science artifact contract")
    projection_surface_ids = {
        row.get("surface_id") for row in spot.get("surface_projection_manifest", {}).get("generated_surfaces", [])
    }
    if "OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json" not in projection_surface_ids:
        errors.append("Surface projection manifest is missing the Phase 1 closed-core dossier")
    if "OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json" not in projection_surface_ids:
        errors.append("Surface projection manifest is missing the unified synthesis surface")
    if "OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json" not in projection_surface_ids:
        errors.append("Surface projection manifest is missing the practical-utility atlas")
    generated_tex_ids = {
        row.get("surface_id") for row in spot.get("surface_projection_manifest", {}).get("generated_tex", [])
    }
    for required_generated_tex in [
        "content/generated/oc_core_1_3_practical_utility_generated.tex",
        "appendix/generated/oc_core_1_3_practical_utility_model_comparison_atlas_generated.tex",
    ]:
        if required_generated_tex not in generated_tex_ids:
            errors.append(f"Surface projection manifest is missing generated TeX {required_generated_tex}")
    dossier_package_classes = {
        row.get("package_class") for row in spot.get("surface_projection_manifest", {}).get("generated_dossier_packages", [])
    }
    if dossier_package_classes != {"closure_bundle_packages", "hostile_review_packages", "phase1_closed_core_package"}:
        errors.append("Surface projection manifest dossier-package classes are incomplete")
    method_ladder = spot.get("scientific_program", {}).get("method_ladder", [])
    if len(method_ladder) != 5:
        errors.append("Scientific program must declare exactly five method-ladder classes")
    if len({row.get("method_class") for row in method_ladder}) != len(method_ladder):
        errors.append("Scientific program method ladder contains duplicate method classes")
    if spot.get("scientific_program", {}).get("execution_order_authority") != "DOMAIN_PRIORITY_BOARD_ONLY":
        errors.append("Scientific program execution order authority must be DOMAIN_PRIORITY_BOARD_ONLY")
    if spot.get("scientific_program", {}).get("closure_bundle_contract") != CLOSURE_ARTIFACT_ORDER:
        errors.append("Scientific program closure-bundle contract does not match the canonical eight-artifact contract")
    if not spot.get("scientific_program", {}).get("ticket_admissibility_rule"):
        errors.append("Scientific program is missing the ticket admissibility rule")
    hostile_review_blocking_ids = [
        row["review_id"]
        for row in spot.get("hostile_review_backlog", [])
        if row.get("blocks_global_pass") and row.get("current_status") != "PASS"
    ]
    if hostile_review_blocking_ids != spot.get("global_verdict", {}).get("hostile_review_blocking_ids", []):
        errors.append("Hostile-review blocking ids do not match the global verdict")
    bundle_domain_ids = {
        row.get("domain_id")
        for row in spot.get("domain_closure_bundles", [])
        if row.get("bundle_id", "").startswith("CLOSURE_BUNDLE::")
    }
    for domain_id in CORE_DOMAIN_IDS:
        if domain_id not in bundle_domain_ids:
            errors.append(f"Missing closure bundle for core domain {domain_id}")
    priority_board_rows = spot.get("scientific_program", {}).get("domain_priority_board", [])
    priority_board_ids = {row.get("domain_id") for row in priority_board_rows}
    if priority_board_ids != set(CORE_DOMAIN_IDS):
        errors.append("Domain priority board must cover every core domain exactly once")
    priority_board_map = {row["domain_id"]: row for row in priority_board_rows}
    for row in spot.get("hostile_review_backlog", []):
        for field in [
            "task_id",
            "dossier_package_ref",
            "dossier_manifest_ref",
            "dossier_readme_ref",
            "dossier_ref",
            "resolution_if_pass",
            "resolution_if_fail",
            "current_resolution_state",
            "exact_theorem_route_under_attack",
            "premises",
            "forbidden_shortcuts",
            "formal_argument_body",
            "falsifier_conditions",
            "resolution_outcome",
        ]:
            if not row.get(field):
                errors.append(f"{row.get('review_id', 'UNKNOWN_REVIEW')}: missing hostile-review field {field}")
    for bundle in spot.get("domain_closure_bundles", []):
        if bundle.get("artifact_contract") != CLOSURE_ARTIFACT_ORDER:
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: artifact contract mismatch")
        if set(bundle.get("artifact_statuses", {}).keys()) != set(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: artifact statuses do not cover the canonical contract")
        if set(bundle.get("artifact_file_refs", {}).keys()) != set(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: artifact file refs do not cover the canonical contract")
        if set(bundle.get("artifact_payloads", {}).keys()) != set(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: artifact payloads do not cover the canonical contract")
        for field in [
            "phase_id",
            "launch_rule",
            "execution_order_authority",
            "source_file_ref",
            "dossier_package_ref",
            "dossier_manifest_ref",
            "dossier_readme_ref",
            "task_board_ref",
            "current_transition_gate",
            "pass_transition",
            "fail_transition",
        ]:
            if not bundle.get(field):
                errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: missing bundle field {field}")
        if bundle.get("execution_order_authority") != "DOMAIN_PRIORITY_BOARD_ONLY":
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: bundle execution order authority must be DOMAIN_PRIORITY_BOARD_ONLY")
        task_rows = bundle.get("task_rows", [])
        if len(task_rows) != len(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: task rows must cover all eight closure artifacts")
        if len({row.get('task_id') for row in task_rows}) != len(task_rows):
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: task ids must be unique")
        if {row.get('artifact_kind') for row in task_rows} != set(CLOSURE_ARTIFACT_ORDER):
            errors.append(f"{bundle.get('bundle_id', 'UNKNOWN_BUNDLE')}: task rows must cover every artifact kind exactly once")
        if bundle.get("domain_id") in CORE_DOMAIN_IDS:
            priority_row = priority_board_map.get(bundle["domain_id"])
            if priority_row is None:
                errors.append(f"{bundle['bundle_id']}: core-domain bundle missing priority-board row")
            else:
                if bundle.get("phase_id") != priority_row.get("phase_id"):
                    errors.append(f"{bundle['bundle_id']}: phase_id does not match priority board")
                if bundle.get("launch_rule") != priority_row.get("launch_rule"):
                    errors.append(f"{bundle['bundle_id']}: launch_rule does not match priority board")
            if bundle.get("closure_verdict") == "PASS" and bundle.get("scientific_class") != "THEOREM_NATIVE":
                errors.append(f"{bundle['bundle_id']}: promoted core-domain bundles must be theorem-native")
            if bundle.get("closure_verdict") == "PASS":
                if bundle["artifact_statuses"].get("theorem_packet") != "COMPLETE":
                    errors.append(f"{bundle['bundle_id']}: promoted core-domain bundle is missing a complete theorem packet")
                if bundle["artifact_statuses"].get("parameter_law_packet") != "COMPLETE":
                    errors.append(f"{bundle['bundle_id']}: promoted core-domain bundle is missing a complete parameter-law packet")
    if spot.get("closed_canon", {}).get("governance_mode") != "TWO_TIER_CANON_PLUS_FRONTIER_WORKBENCH":
        errors.append("Closed canon governance mode is not locked to the two-tier program")
    if not spot.get("unified_science_atlas", {}).get("domain_translation_rows"):
        errors.append("Unified science atlas is missing domain translation rows")
    toe = spot.get("toe_synthesis_registry", {})
    if not toe.get("branding"):
        errors.append("Unified synthesis registry is missing branding policy")
    if not toe.get("public_chapter_title"):
        errors.append("Unified synthesis registry is missing public chapter title")
    expected_k_levels = {f"K{index}" for index in range(13)}
    toe_rows = toe.get("k_level_rows", [])
    if {row.get("level_id") for row in toe_rows} != expected_k_levels:
        errors.append("Unified synthesis registry must contain exactly K0-K12 rows")
    for row in toe_rows:
        for field in [
            "theorem_refs",
            "operator_refs",
            "parameter_law_refs",
            "observable_ids",
            "numerical_rows",
            "falsifier_refs",
            "manuscript_anchor_refs",
        ]:
            if not row.get(field):
                errors.append(f"{row.get('level_id', 'UNKNOWN_K')}: unified synthesis row is missing {field}")
        expected_appendix_label = science_sources.get("k_levels", {}).get(row.get("level_id"), {}).get(
            "appendix_table_label",
            TOE_LEVEL_SPECS.get(row.get("level_id"), {}).get("appendix_table_label"),
        )
        if row.get("appendix_table_label") != expected_appendix_label:
            errors.append(f"{row.get('level_id', 'UNKNOWN_K')}: synthesis appendix table label is not synchronized")
    empirical_prediction_rows = toe.get("empirical_prediction_rows", [])
    if {row.get("domain_id") for row in empirical_prediction_rows} != set(CORE_DOMAIN_IDS[1:]):
        errors.append("Unified synthesis empirical prediction rows must cover physics, chemistry, biology, and systems")
    for row in empirical_prediction_rows:
        if row.get("held_out_case_total", 0) <= 0:
            errors.append(f"{row.get('domain_id', 'UNKNOWN_DOMAIN')}: synthesis empirical prediction row is missing held-out cases")
    practical = spot.get("practical_utility_atlas", {})
    for field in [
        "support_class_legend",
        "executive_summary",
        "use_case_rows",
        "operational_playbooks",
        "same_claim_class_baseline_rows",
        "serious_model_comparison_rows",
        "fragmentation_closure_rows",
        "readiness_matrix_rows",
    ]:
        if not practical.get(field):
            errors.append(f"Practical utility atlas is missing {field}")
    domain_map = {domain["domain_id"]: domain for domain in spot.get("domain_registry", [])}
    use_case_rows = practical.get("use_case_rows", [])
    for row in use_case_rows:
        for field in ["use_case_id", "domain_id", "problem_class", "support_class", "scope_boundary", "trace_refs", "what_remains_open"]:
            if not row.get(field):
                errors.append(f"Practical utility row is missing {field}")
        if row.get("support_class") not in PRACTICAL_SUPPORT_CLASS_ORDER:
            errors.append(f"{row.get('use_case_id', 'UNKNOWN_USE_CASE')}: illegal practical support class")
        if row.get("support_class") in USABLE_NOW_SUPPORT_CLASSES:
            if row.get("domain_id") in domain_map:
                domain = domain_map[row["domain_id"]]
                if domain.get("closure_verdict") != "PASS" or domain.get("scientific_class") != "THEOREM_NATIVE":
                    errors.append(f"{row.get('use_case_id', 'UNKNOWN_USE_CASE')}: usable-now row lacks a passed theorem-native domain packet")
            elif row.get("domain_id") == "CROSS_DOMAIN":
                if spot.get("global_verdict", {}).get("closure_verdict") != "PASS" or spot.get("unified_science_atlas", {}).get("atlas_status") != "PASS":
                    errors.append(f"{row.get('use_case_id', 'UNKNOWN_USE_CASE')}: cross-domain usable-now row lacks a passed global route")
    for domain_id in CORE_DOMAIN_IDS[1:]:
        domain_rows = [row for row in use_case_rows if row.get("domain_id") == domain_id]
        if not domain_rows:
            errors.append(f"{domain_id}: practical utility atlas is missing use-case rows")
            continue
        if not any(row.get("support_class") in USABLE_NOW_SUPPORT_CLASSES for row in domain_rows):
            errors.append(f"{domain_id}: practical utility atlas must expose at least one usable-now row")
        if not any(row.get("support_class") in {"FRONTIER_PROGRAM", "HYPOTHESIS_ONLY"} for row in domain_rows):
            errors.append(f"{domain_id}: practical utility atlas must expose at least one explicit frontier or hypothesis row")
    playbooks = practical.get("operational_playbooks", [])
    for domain_id in CORE_DOMAIN_IDS[1:]:
        if not any(row.get("domain_id") == domain_id for row in playbooks):
            errors.append(f"{domain_id}: practical utility atlas is missing an operational playbook")
    if not any(row.get("domain_id") == "CROSS_DOMAIN" for row in use_case_rows):
        errors.append("Practical utility atlas is missing the cross-domain use-case row")
    serious_rows = practical.get("serious_model_comparison_rows", [])
    for domain_id in CORE_DOMAIN_IDS[1:]:
        if not any(row.get("domain_id") == domain_id for row in serious_rows):
            errors.append(f"{domain_id}: practical utility atlas is missing a serious-model comparison row")
    return errors


def validate_existing_bundle(repo_root: Path | None = None, require_final_toe_pass: bool = False) -> list[str]:
    repo_root = repo_root or REPO_ROOT
    errors: list[str] = []
    science_sources = load_science_source_corpus(repo_root)
    errors.extend(validate_science_source_corpus(science_sources, repo_root=repo_root))
    spot = load_json(SCIENCE_SURFACE_TARGETS["spot"])
    errors.extend(validate_spot_structure(spot, repo_root=repo_root, science_sources=science_sources))
    expected_surfaces = project_surfaces_from_spot(spot)
    for name, target_path in SCIENCE_SURFACE_TARGETS.items():
        if name == "spot":
            continue
        if not target_path.exists():
            errors.append(f"Missing projected surface: {target_path}")
            continue
        actual = load_json(target_path)
        if not compare_normalized(expected_surfaces[name], actual):
            errors.append(f"Surface mismatch for {target_path.name}")
    expected_tex = render_tex_from_spot(spot)
    expected_toe_support = render_toe_support_corpus_from_spot(spot)
    for key, target_path in ROOT_TEX_TARGETS.items():
        if not target_path.exists():
            errors.append(f"Missing generated TeX fragment: {target_path}")
            continue
        if target_path.read_text(encoding="utf-8").rstrip() != expected_tex[key].rstrip():
            errors.append(f"Generated TeX mismatch for {target_path}")
    for key, target_path in SOURCE_TEX_TARGETS.items():
        if not target_path.exists():
            errors.append(f"Missing generated monograph source TeX fragment: {target_path}")
            continue
        if target_path.read_text(encoding="utf-8").rstrip() != expected_tex[key].rstrip():
            errors.append(f"Generated source TeX mismatch for {target_path}")
    for key, target_path in ROOT_TOE_SUPPORT_TARGETS.items():
        if not target_path.exists():
            errors.append(f"Missing generated synthesis support file: {target_path}")
            continue
        if target_path.read_text(encoding="utf-8").rstrip() != expected_toe_support[key].rstrip():
            errors.append(f"Generated synthesis support mismatch for {target_path}")
    for key, target_path in SOURCE_TOE_SUPPORT_TARGETS.items():
        if not target_path.exists():
            errors.append(f"Missing generated source synthesis support file: {target_path}")
            continue
        if target_path.read_text(encoding="utf-8").rstrip() != expected_toe_support[key].rstrip():
            errors.append(f"Generated source synthesis support mismatch for {target_path}")
    for path, (payload_kind, payload) in expected_dossier_package_files(spot).items():
        if not path.exists():
            errors.append(f"Missing generated dossier package file: {path}")
            continue
        if payload_kind == "json":
            actual = load_json(path)
            if not compare_normalized(payload, actual):
                errors.append(f"Dossier package JSON mismatch for {path}")
        else:
            if path.read_text(encoding='utf-8').rstrip() != str(payload).rstrip():
                errors.append(f"Dossier package text mismatch for {path}")
    for path, payload in expected_legacy_domain_packet_files(spot).items():
        if not path.exists():
            errors.append(f"Missing generated legacy domain packet: {path}")
            continue
        if path.read_text(encoding="utf-8").rstrip() != payload.rstrip():
            errors.append(f"Legacy domain packet mismatch for {path}")
    toe_wrapper = repo_root / "content" / "25_oc_core_1_3_toe_synthesis.tex"
    if not toe_wrapper.exists():
        errors.append(f"Missing unified synthesis chapter wrapper: {toe_wrapper}")
    else:
        wrapper_text = toe_wrapper.read_text(encoding="utf-8")
        if r"\section{" in wrapper_text:
            errors.append("Unified synthesis chapter wrapper must not carry a hard-coded section title")
    practical_wrapper = repo_root / "content" / "26_oc_core_1_3_practical_utility.tex"
    if not practical_wrapper.exists():
        errors.append(f"Missing practical-utility chapter wrapper: {practical_wrapper}")
    appendix_wrapper = repo_root / "appendix" / "R_oc_core_1_3_practical_utility_model_comparison_atlas.tex"
    if not appendix_wrapper.exists():
        errors.append(f"Missing practical-utility appendix wrapper: {appendix_wrapper}")
    master_targets = [
        repo_root / "oc_core_1_3_master_monograph.tex",
        repo_root / "releases" / "oc_core_1_3" / "monograph" / "source" / "oc_core_1_3_master_monograph.tex",
    ]
    required_master_inputs = [
        r"\input{content/25_oc_core_1_3_toe_synthesis.tex}",
        r"\input{content/26_oc_core_1_3_practical_utility.tex}",
        r"\input{appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex}",
    ]
    for master_path in master_targets:
        if not master_path.exists():
            errors.append(f"Missing master manuscript file: {master_path}")
            continue
        master_text = master_path.read_text(encoding="utf-8")
        for required_input in required_master_inputs:
            if required_input not in master_text:
                errors.append(f"Master manuscript is missing required input {required_input}: {master_path}")
    toe_tex = expected_tex["toe_synthesis"]
    expected_title = spot.get("toe_synthesis_registry", {}).get("public_chapter_title", "")
    if expected_title and rf"\section{{{expected_title}}}" not in toe_tex:
        errors.append("Generated unified synthesis chapter is missing the expected public chapter title")
    if spot.get("toe_synthesis_registry", {}).get("status") != "PASS" and r"\section{Unified Science Synthesis}" in toe_tex:
        errors.append("Fail-closed closure chapter must not present itself with deprecated total-theory language")
    for level_id in [f"K{index}" for index in range(13)]:
        if rf"\subsection{{{level_id}:" not in toe_tex:
            errors.append(f"Generated unified synthesis chapter is missing subsection for {level_id}")
    if toe_tex.count(r"\begin{longtable}") < 14:
        errors.append("Generated unified synthesis chapter must contain numerical longtables for K0-K12 and empirical prediction summary")
    practical_tex = expected_tex["practical_utility"]
    if r"\subsection{Practical value and support boundary}" not in practical_tex:
        errors.append("Generated practical-utility chapter is missing the usefulness subsection")
    if r"\subsection{Benchmark against serious alternatives}" not in practical_tex:
        errors.append("Generated practical-utility chapter is missing the serious-alternatives subsection")
    if r"\subsection{What remains frontier or hypothesis}" not in practical_tex:
        errors.append("Generated practical-utility chapter is missing the frontier / hypothesis subsection")
    toe_master_root = repo_root / "content" / "toe" / "toe_master.tex"
    if toe_master_root.exists():
        toe_master_text = toe_master_root.read_text(encoding="utf-8")
        for level_id in TOE_LEVEL_IDS:
            if rf"\input{{content/toe/toe_{level_id.lower()}}}" not in toe_master_text:
                errors.append(f"Synthesis support master is missing {level_id} input")
    for level_id in TOE_LEVEL_IDS:
        level_path = repo_root / "content" / "toe" / f"toe_{level_id.lower()}"
        if not level_path.exists():
            errors.append(f"Missing synthesis support level file: {level_path}")
            continue
        level_text = level_path.read_text(encoding="utf-8")
        for heading in TOE_SUPPORT_REQUIRED_HEADINGS:
            if heading not in level_text:
                errors.append(f"{level_path.name}: missing structured heading {heading}")
    readme_path = repo_root / "releases" / "oc_core_1_3" / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8")
        if spot.get("toe_synthesis_registry", {}).get("status") != "PASS" and "generated `Unified Science Synthesis` chapter" in readme_text:
            errors.append("Fail-closed release README must not advertise deprecated total-theory language")
    if require_final_toe_pass:
        if spot.get("global_verdict", {}).get("closure_verdict") != "PASS":
            errors.append("Final synthesis validation failed: global verdict is not PASS")
        if spot.get("global_verdict", {}).get("bridge_only_domain_total") != 0:
            errors.append("Final synthesis validation failed: bridge-only domains remain")
        if spot.get("global_verdict", {}).get("hostile_review_blocking_total") != 0:
            errors.append("Final synthesis validation failed: hostile-review blockers remain open")
        if spot.get("global_verdict", {}).get("integrability_suite_status") != "PASS":
            errors.append("Final synthesis validation failed: integrability suite is not PASS")
        if spot.get("toe_synthesis_registry", {}).get("status") != "PASS":
            errors.append("Final synthesis validation failed: unified synthesis surface is not PASS")
        for row in spot.get("toe_synthesis_registry", {}).get("empirical_prediction_rows", []):
            if row.get("closure_verdict") != "PASS":
                errors.append(f"Final synthesis validation failed: {row.get('domain_id', 'UNKNOWN_DOMAIN')} is not PASS")
    return errors


def write_projection_bundle(spot: dict[str, Any]) -> None:
    dump_json(SCIENCE_SURFACE_TARGETS["spot"], spot)
    projected_surfaces = project_surfaces_from_spot(spot)
    for name, payload in projected_surfaces.items():
        dump_json(SCIENCE_SURFACE_TARGETS[name], payload)
    rendered_tex = render_tex_from_spot(spot)
    for key, path in ROOT_TEX_TARGETS.items():
        dump_text(path, rendered_tex[key])
    for key, path in SOURCE_TEX_TARGETS.items():
        dump_text(path, rendered_tex[key])
    rendered_toe_support = render_toe_support_corpus_from_spot(spot)
    for key, path in ROOT_TOE_SUPPORT_TARGETS.items():
        dump_text(path, rendered_toe_support[key])
    for key, path in SOURCE_TOE_SUPPORT_TARGETS.items():
        dump_text(path, rendered_toe_support[key])
    for source_path, target_path in TEMPLATE_SYNC_MAP.items():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    for path, payload in expected_legacy_domain_packet_files(spot).items():
        dump_text(path, payload)
    for path, (payload_kind, payload) in expected_dossier_package_files(spot).items():
        if payload_kind == "json":
            dump_json(path, payload)
        else:
            dump_text(path, str(payload))
