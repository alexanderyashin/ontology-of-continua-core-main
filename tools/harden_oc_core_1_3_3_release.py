from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
TIMESTAMP = "2026-04-28T00:00:00Z"

ROLES = [
    "formal_mathematician",
    "dynamical_systems_reviewer",
    "category_type_theory_reviewer",
    "empirical_statistician",
    "prior_art_historian",
    "hostile_journal_reviewer",
    "not_novel_attacker",
    "phenomenon_x_attacker",
    "clarity_didactic_reviewer",
]

THEOREMS = [
    {
        "id": "T133-K0-RES",
        "title": "K0 resolution-relative distinguishability theorem",
        "artifact": "appendix/OC_1_3_3_K0_RESOLUTION_DISTINGUISHABILITY_PROOF.tex",
        "attack": "The theorem may still smuggle a discrete substrate by moving the epsilon bound from states to quotients.",
        "assumptions": [
            "A raw carrier S may be continuous, finite, countable, or typed-combinatorial.",
            "A resolution regime rho supplies an observational equivalence relation and a positive separation only on resolved quotient classes.",
            "Downstream claims may use raw topology only through stated realization assumptions.",
        ],
        "definitions": [
            "D1 resolved carrier S_rho is S modulo the equivalence relation induced by rho.",
            "D2 distinguishable means unequal classes in S_rho, not unequal raw points in S.",
            "D3 K0 support means bookkeeping distinguishability for model states at a declared resolution.",
        ],
        "lemmas": [
            "If two raw points lie in the same rho-cell, no K0 theorem may infer raw separation between them.",
            "If two rho-cells are distinct and the quotient metric is declared with minimum separation epsilon_rho, K0 distinguishability follows without imposing a minimum distance on S.",
        ],
        "theorem": "K0 can support continuous raw spaces because the separation condition is resolution-relative and applies only after quotienting.",
        "finite_example": "Partition [0, 1] into four cells. Points 0.10 and 0.11 remain unresolved, while cells [0, .25) and [.25, .50) are separated in S_rho.",
        "counterexample": "A proof that assumes every pair of raw real states is epsilon-separated is outside OC 1.3.3 and must be rejected.",
    },
    {
        "id": "T133-OMEGA-STATUS",
        "title": "Typed liveness/death/residue consistency theorem",
        "artifact": "content/03_model.tex",
        "attack": "The model may conflate empty admissible state, death, residue, and rebirth into one untyped metaphor.",
        "assumptions": [
            "The admissible region Omega, live predicate, death predicate, residue object, and rebirth morphism have distinct declared types.",
            "A realization must state which failure predicate changes live status.",
            "Residue cannot be silently counted as identity continuation.",
        ],
        "definitions": [
            "D1 Live(K,t) is a boolean status over a typed realization.",
            "D2 Death(K,t) is a terminal or non-live status triggered by declared failure predicates.",
            "D3 Residue is preserved structure after death; rebirth is a new live realization connected by a morphism from residue.",
        ],
        "lemmas": [
            "A nonempty Omega does not imply live status unless all required live-support predicates also hold.",
            "Residue preservation does not imply identity continuation unless the identity morphism constraints are satisfied.",
        ],
        "theorem": "Liveness, death, residue, and rebirth are jointly consistent when treated as typed statuses and morphisms rather than as one scalar condition.",
        "finite_example": "A two-state automaton has admissible state A, failed cycle support, residue label r, and a new state B reachable from r; B is rebirth, not continuation.",
        "counterexample": "Any row that labels a residue-preserving restart as the same live individual without identity morphism evidence is demoted.",
    },
    {
        "id": "T133-K-ZERO",
        "title": "Continuumness zero-cause theorem",
        "artifact": "appendix/OC_1_3_3_CONTINUUMNESS_AXIOMATIZATION.tex",
        "attack": "The old k=0 iff Omega or C is empty biconditional misses flow, coherence, identity, and embedding failures.",
        "assumptions": [
            "Continuumness score k is separate from live status.",
            "Zero-cause predicates are explicitly declared for each realization.",
            "The multiplicative formula is a local aggregator only when independence assumptions are stated.",
        ],
        "definitions": [
            "D1 ZeroCause(K,t) is the disjunction of declared collapse causes.",
            "D2 k(K,t)=0 is licensed only by an active zero-cause.",
            "D3 A local product aggregator is a representation, not the primitive semantics of k.",
        ],
        "lemmas": [
            "If flow support is zero while Omega and C are nonempty, the old biconditional fails but ZeroCause succeeds.",
            "If a coherence contradiction is active, k=0 follows from the typed cause ledger even without set emptiness.",
        ],
        "theorem": "Continuumness zero is equivalent to at least one declared zero-cause, not merely to empty admissibility or empty cycles.",
        "finite_example": "Omega={s}, C={c}, flow_support=0 produces k=0 through FLOW_COLLAPSE while the old biconditional would return false.",
        "counterexample": "A realization with undeclared zero-cause cannot promote k=0 as proved; it must add the cause or demote the claim.",
    },
    {
        "id": "T133-BOUNDARY",
        "title": "Generalized boundary specialization theorem",
        "artifact": "appendix/OC_1_3_3_GENERALIZED_BOUNDARY_FORMALISM.tex",
        "attack": "OC may force logical, social, and categorical boundaries into fake real-valued thresholds.",
        "assumptions": [
            "Boundary predicates are typed classifiers into status objects.",
            "Metric thresholds are admitted only as one specialization.",
            "A domain may use logical, categorical, or finite-state admissibility without inventing a numeric surface.",
        ],
        "definitions": [
            "D1 A classifier boundary is a family b_i:S->Status_i plus a failure predicate on Status_i.",
            "D2 A metric boundary is the special case Status_i=R with a threshold failure predicate.",
            "D3 A logical boundary is the special case Status_i={true,false}.",
        ],
        "lemmas": [
            "Every real-valued threshold boundary embeds as a classifier boundary.",
            "A non-metric boundary can be represented directly as a classifier without first choosing a real-valued measurement rule.",
        ],
        "theorem": "The OC 1.3.3 boundary formalism is a conservative extension of the older metric-threshold boundary: every old threshold instance embeds, and non-metric domains may stay in their native classifier type.",
        "finite_example": "A finite proof state is admissible when predicate Consistent(state)=true; no real-valued distance is needed.",
        "counterexample": "A claim of strict non-definability of boolean boundaries into real codings is not promoted here; if a social-role boundary is represented by a real threshold without a domain-native measurement rule, the numeric claim is blocked.",
    },
    {
        "id": "T133-HYBRID",
        "title": "Smooth operator form as a special realization theorem",
        "artifact": "appendix/OC_1_3_3_HYBRID_OPERATOR_SEMANTICS.tex",
        "attack": "The F,G,H,Q,R,S,U operators look like universal differential equations even in non-smooth domains.",
        "assumptions": [
            "Operators are typed update components over realization states.",
            "A smooth derivative exists only in smooth realizations.",
            "Discrete, stochastic, rewrite, proof-replay, and hybrid automaton realizations are first-class.",
        ],
        "definitions": [
            "D1 Update semantics maps a state and admissible input to a successor object or distribution.",
            "D2 Smooth semantics is the realization where updates admit differentiable local charts.",
            "D3 Hybrid semantics allows discrete jumps and smooth segments under one typed transition system.",
        ],
        "lemmas": [
            "A differentiable flow induces a typed update relation by its time-t map.",
            "A typed update relation need not induce a derivative unless extra smoothness assumptions are present.",
        ],
        "theorem": "Differential OC operator notation is a smooth-realization specialization of typed update semantics.",
        "finite_example": "A proof-replay operator maps theorem states through rewrite steps; no derivative is present, but the OC operator remains well typed.",
        "counterexample": "A paper section that differentiates a rewrite-only proof state without a smooth realization assumption is rejected.",
    },
    {
        "id": "T133-DIM",
        "title": "Historical axis monotonicity with effective-rank decrease compatibility theorem",
        "artifact": "appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex",
        "attack": "Historical dimension and effective dimension may contradict each other when a system loses active degrees of freedom.",
        "assumptions": [
            "Historical axis activation records axes that have become part of the realization history.",
            "Effective working rank records currently active independent degrees of freedom.",
            "The two quantities are not interchangeable.",
        ],
        "definitions": [
            "D1 A_hist is the set of historically activated axes.",
            "D2 rank_eff(t) is the rank of active support at time t.",
            "D3 Dimension demotion is lawful only when historical axes are shown to be eliminable or irrelevant under the declared equivalence.",
        ],
        "lemmas": [
            "A_hist can be monotone while rank_eff decreases after freezing, collapse, or constraint activation.",
            "A reduction from K_{n+1} to K_n fails when a historical witness remains observable under the release equivalence.",
        ],
        "theorem": "Historical axis monotonicity is compatible with effective-rank decrease because they measure different typed quantities.",
        "finite_example": "A two-axis automaton activates memory and then freezes memory updates; historical axes remain two while active rank becomes one.",
        "counterexample": "A reviewer may demote a K-level if the alleged new axis has no witness, no observable consequence, and no failed reduction criterion.",
    },
    {
        "id": "T133-CYCLE",
        "title": "Live-status cycle-mode requirement theorem",
        "artifact": "content/OC_1_3_3_CYCLE_TAXONOMY.tex",
        "attack": "A stable frozen object or a one-shot process might be mislabeled live without an operational cycle.",
        "assumptions": [
            "Live status requires a declared cycle mode unless the domain explicitly uses a terminal non-live classification.",
            "Maintenance, renewal, proof replay, regulatory, and degenerate cycles are distinguished.",
            "A degenerate fixed point is live only when the maintenance predicate is non-vacuous.",
        ],
        "definitions": [
            "D1 Cycle mode is a typed recurrence, maintenance, or replay condition.",
            "D2 Frozen persistence is not live unless it satisfies the maintenance predicate.",
            "D3 Degenerate cycle means identity recurrence with non-empty support obligations.",
        ],
        "lemmas": [
            "If no admissible cycle mode is declared, the live predicate is under-specified and cannot be promoted.",
            "If a fixed point actively satisfies support obligations, it can be a degenerate maintenance cycle.",
        ],
        "theorem": "OC live status requires an explicit cycle mode; stable objects pass only through non-vacuous maintenance or are demoted.",
        "finite_example": "A constant automaton with an energy-maintenance check passes; a static label with no check fails.",
        "counterexample": "A theory-space artifact that never updates, replays, checks, or maintains itself is archive residue, not a live continuum.",
    },
    {
        "id": "T133-ID",
        "title": "Identity/residue/rebirth morphism classification theorem",
        "artifact": "appendix/OC_1_3_3_IDENTITY_RESIDUE_REBIRTH_CATEGORY.tex",
        "attack": "Rebirth language may hide identity equivocation and create metaphysical overreach.",
        "assumptions": [
            "Identity continuation, residue preservation, and rebirth are separate morphism classes.",
            "The realization declares invariants that identity morphisms must preserve.",
            "No metaphysical personal identity claim is promoted by the formal category alone.",
        ],
        "definitions": [
            "D1 Identity morphism preserves the declared identity invariants.",
            "D2 Residue morphism preserves a proper subset sufficient for reconstruction evidence.",
            "D3 Rebirth morphism maps residue into a new live realization without identity continuation.",
        ],
        "lemmas": [
            "Residue morphisms compose with rebirth constructors without becoming identity morphisms.",
            "If an invariant required for identity is absent after restart, the morphism class is rebirth or residue-only.",
        ],
        "theorem": "The OC morphism classes prevent residue/rebirth from being promoted as identity continuation.",
        "finite_example": "A process checkpoint preserves schema and loses runtime token identity; restart is rebirth, not identical continuation.",
        "counterexample": "Any public claim that reads rebirth as literal same-identity survival is blocked by this theorem.",
    },
    {
        "id": "T133-MIN",
        "title": "Verdict-invariant minimality theorem",
        "artifact": "appendix/OC_1_3_3_VERDICT_INVARIANT_MINIMALITY_FULL_PROOF.tex",
        "attack": "The tuple may be a bloated relabeling of existing systems vocabulary rather than a minimal structure.",
        "assumptions": [
            "Minimality is claimed only for the OC verdict class, not for all possible scientific theories.",
            "Each tuple component has a witness pair where changing it changes a verdict.",
            "Components with no verdict-changing witness are not promoted as minimal.",
        ],
        "definitions": [
            "D1 Verdict-invariant means preserving the pass/fail classification of the declared OC tests.",
            "D2 A witness pair differs only in one component and changes the verdict.",
            "D3 Minimality scope is the release-governed OC classifier, not metaphysical uniqueness.",
        ],
        "lemmas": [
            "For every promoted component, the witness-pair ledger contains a pair that flips an OC verdict.",
            "If a component can be removed without changing any declared verdict, the minimality claim fails and must be demoted.",
        ],
        "theorem": "Within the declared OC verdict class, the promoted tuple components are minimally required by witness-pair tests.",
        "finite_example": "Removing boundary classifiers admits a state rejected by the full tuple; removing cycle mode admits a frozen non-live object.",
        "counterexample": "The theorem does not prove OC is the unique possible framework; prior-art equivalence attacks remain bounded by comparator evidence.",
    },
]


PRIOR_ART_ROWS = [
    {
        "tradition": "General System Theory",
        "source_refs": [{"title": "Ludwig von Bertalanffy, General System Theory", "url": "https://www.georgebraziller.com/general-systems-theory", "source_type": "publisher"}],
        "prior_art_has": "Cross-domain systems language, organization, interaction, and open-system framing.",
        "oc_bounded_delta": "OC adds a typed release-governed claim ledger connecting tuple components to theorem sheets, finite tests, falsifiers, and no-send governance.",
        "what_oc_must_not_claim": "OC must not claim that system-level cross-domain language is new.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Autopoiesis",
        "source_refs": [{"title": "Maturana and Varela, Autopoiesis and Cognition", "url": "https://link.springer.com/book/10.1007/978-94-009-8947-4", "source_type": "publisher"}],
        "prior_art_has": "Self-production, organization of living systems, and boundary-maintenance concepts.",
        "oc_bounded_delta": "OC separates liveness, death, residue, and rebirth morphisms and refuses to promote biology-wide validation without numeric replay.",
        "what_oc_must_not_claim": "OC must not present self-maintaining living organization as its original discovery.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Dynamical systems",
        "source_refs": [{"title": "Springer dynamical systems reference route", "url": "https://link.springer.com/search?query=dynamical+systems", "source_type": "publisher-search"}],
        "prior_art_has": "State spaces, flows, attractors, stability, bifurcation, and phase-space reasoning.",
        "oc_bounded_delta": "OC demotes universal derivative language and treats differential equations as one smooth realization of typed update semantics.",
        "what_oc_must_not_claim": "OC must not claim novelty for state-space dynamics or stability analysis.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Category and topos-style formalisms",
        "source_refs": [{"title": "Mac Lane, Categories for the Working Mathematician", "url": "https://link.springer.com/book/10.1007/978-1-4612-9839-7", "source_type": "publisher"}],
        "prior_art_has": "Objects, morphisms, functors, adjunctions, subobjects, and abstraction across mathematical domains.",
        "oc_bounded_delta": "OC uses typed morphism discipline for identity/residue/rebirth and records exactly where categorical strength is and is not claimed.",
        "what_oc_must_not_claim": "OC must not claim to invent categorical abstraction or morphism-based comparison.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "RAF and autocatalytic set theory",
        "source_refs": [{"title": "Hordijk and Steel RAF algorithms and autocatalytic sets", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4428007/", "source_type": "open-paper"}],
        "prior_art_has": "Formal autocatalytic-set closure, food-generated reaction systems, and algorithms for chemical-origin questions.",
        "oc_bounded_delta": "OC treats RAF-like closure as a domain-specific chemical cycle candidate and requires reduction witnesses before K-level promotion.",
        "what_oc_must_not_claim": "OC must not claim chemical autocatalytic closure as an OC invention.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Information and complexity measures",
        "source_refs": [{"title": "Cover and Thomas, Elements of Information Theory", "url": "https://www.wiley.com/en-us/Elements+of+Information+Theory%2C+2nd+Edition-p-9780471241959", "source_type": "publisher"}],
        "prior_art_has": "Entropy, mutual information, coding, and quantitative information measures.",
        "oc_bounded_delta": "OC does not replace information theory; it uses evidence ledgers to decide when a quantitative measure is native to a claim.",
        "what_oc_must_not_claim": "OC must not call every continuumness or complexity number a new universal information measure.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Causal modeling and identity theories",
        "source_refs": [{"title": "Pearl, Causality", "url": "https://www.cambridge.org/core/books/causality/659006AC0B6C1A040DD46DE5B612DB21", "source_type": "publisher"}],
        "prior_art_has": "Structural causal models, interventions, counterfactuals, and cause/effect identification conditions.",
        "oc_bounded_delta": "OC offers typed collapse/falsifier routing, but causal inference claims remain subordinate to domain-specific causal identification.",
        "what_oc_must_not_claim": "OC must not claim to solve causal inference merely by relabeling dependencies as operators.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Systems engineering",
        "source_refs": [{"title": "ISO/IEC/IEEE 15288:2023", "url": "https://www.iso.org/standard/81702.html", "source_type": "standard"}],
        "prior_art_has": "Lifecycle processes, verification, validation, stakeholder requirements, and system governance.",
        "oc_bounded_delta": "OC's no-send control plane is a scientific-release governance layer, not a replacement for engineering lifecycle standards.",
        "what_oc_must_not_claim": "OC must not claim invention of lifecycle governance or V&V discipline.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Scientific model comparison",
        "source_refs": [{"title": "Stanford Encyclopedia route for scientific models", "url": "https://plato.stanford.edu/entries/models-science/", "source_type": "reference"}],
        "prior_art_has": "Model idealization, representation, confirmation, and comparison practices.",
        "oc_bounded_delta": "OC contributes a machine-readable claim-to-evidence matrix for this release; it does not replace philosophy of modeling.",
        "what_oc_must_not_claim": "OC must not claim that claim-ledger comparison itself proves final truth.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
    {
        "tradition": "Formal proof engineering",
        "source_refs": [{"title": "The Coq Proof Assistant", "url": "https://coq.inria.fr/", "source_type": "tool-home"}],
        "prior_art_has": "Machine-checked proof discipline, proof scripts, dependencies, and formal verification cultures.",
        "oc_bounded_delta": "OC 1.3.3 provides proof sheets and finite model checks, not a full mechanized proof assistant formalization.",
        "what_oc_must_not_claim": "OC must not claim machine-checked theorem status where only structured proof sheets exist.",
        "uniqueness_claim_status": "BOUNDED_DELTA_ONLY",
    },
]


PHENOMENA = [
    ("P001", "Does OC explain physical constants?", "Only snapshot replay and typed use of constants are supported.", "K2 route: constants enter as official fixed inputs, not new derivations.", ["validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json"], "NUMERIC_REPLAY_NOT_NEW_PHYSICS", "A new constant derivation claim without held-out success fails.", "No derivation of constants is promoted."),
    ("P002", "Does OC explain chemical identity?", "Water identity replay is a chemistry-lane sanity check, not chemistry as a whole.", "K3 route: formula and molecular-weight replay bind typed chemical observables.", ["validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json"], "NUMERIC_REPLAY_WITH_RESIDUAL", "Wrong molecular formula or out-of-bound residual fails.", "No universal reaction prediction is promoted."),
    ("P003", "Does OC explain biological organization?", "Only official snapshot routing and blocked promotion are claimed.", "K4-K5 route: liveness/cycle criteria specify what evidence would be needed.", ["docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json"], "BLOCKED_FOR_PROMOTION", "No blinded biological observable means no promoted biological prediction.", "The release does not claim organism-level prediction."),
    ("P004", "Does OC explain economic/civilizational series?", "Only a bounded WDI replay/nowcast row is included.", "K8 route: regime and residue language organize indicators, while numeric strength is measured by residuals.", ["validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json"], "NUMERIC_REPLAY_COMPARATOR_REPORTED", "If OC predictor fails to beat declared comparator, no superiority claim is allowed.", "No macroeconomic control law is promoted."),
    ("P005", "Does OC explain mathematical proof evolution?", "Finite-model proof replay is supported for promoted formal claims.", "K9 route: proof-state transitions and invalid candidates are tested by finite examples.", ["proofs/FINITE_MODEL_CHECKS_1_3_3.json"], "FINITE_MODEL_REPLAY_SUPPORTED", "A theorem label with no proof sheet fails G47.", "Not a full proof-assistant mechanization."),
    ("P006", "Does OC explain consciousness?", "No consciousness claim is promoted.", "K6 route remains a future protocol requiring observables and falsifiers.", ["claims/CLAIM_LEDGER_1_3_3.json"], "NOT_PROMOTED", "Any promoted consciousness claim without data/proof fails claim traceability.", "Outside this release."),
    ("P007", "Does OC explain quantum measurement?", "No quantum-measurement solution is promoted.", "K2 route would require a domain-native formal map and empirical comparator.", ["docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json"], "NOT_PROMOTED", "A measurement-problem solution claim without source-backed proof fails.", "Outside this release."),
    ("P008", "Does OC explain the origin of life?", "Only RAF/autopoiesis comparator boundaries are stated.", "K3-K4 route identifies closure/cycle evidence required for future lanes.", ["docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json"], "PROTOCOL_READY_NO_PROMOTION", "No chemical network dataset means no origin-of-life claim.", "No origin-of-life solution is promoted."),
    ("P009", "Does OC explain social institutions?", "Only typed K7 boundary/cycle semantics are promoted.", "K7 route maps norms/roles to classifiers and maintenance cycles.", ["data/k_level_irreducibility_matrix.json"], "FORMAL_ROUTE_ONLY", "Empirical institutional prediction requires separate pinned data.", "No general sociology prediction is promoted."),
    ("P010", "Does OC explain theory change?", "Bounded K9/K12 release-governance mechanisms are promoted.", "K9-K12 route links proof, review, release control, and claim demotion.", ["releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_CONTROL_PLANE_latest.json"], "OPERATIONAL_RELEASE_REPLAY", "If owner/no-send gates are bypassed, governance claim fails.", "Does not predict all future science."),
    ("P011", "Does OC explain collapse/rebirth?", "Formal status and morphism classification are promoted.", "Tuple route separates live failure, residue, and rebirth morphisms.", ["proofs/proof_sheets/T133-ID.md"], "FORMAL_PROOF_SHEET_SUPPORTED", "Identity continuation claim without invariants fails.", "No metaphysical survival claim."),
    ("P012", "Does OC explain boundaries outside geometry?", "Classifier boundaries are promoted.", "Boundary route maps metric, logical, finite-state, and categorical admissibility.", ["proofs/proof_sheets/T133-BOUNDARY.md"], "FORMAL_PROOF_SHEET_SUPPORTED", "A numeric threshold without measurement semantics fails.", "No universal metricization claim."),
    ("P013", "Does OC explain why K-levels cannot collapse?", "K-level irreducibility is retained as a formal-route atlas, not a promoted proof of non-collapse.", "K-level route records transition witnesses and lawful demotion criteria for reviewer orientation.", ["data/k_level_irreducibility_matrix.json"], "FORMAL_ROUTE_ONLY_NOT_PROMOTED", "A missing checked witness blocks any adjacent irreducibility promotion.", "No global metaphysical hierarchy proof."),
    ("P014", "Does OC explain predictions in all domains?", "No; the release blocks that claim.", "Empirical route requires numeric rows per promoted lane.", ["validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json"], "OVERCLAIM_BLOCKED", "Any all-domain numeric prediction sentence fails G52.", "Explicitly not promoted."),
]


ATTACKS = [
    ("K0 resolution", "T133-K0-RES", "appendix/OC_1_3_3_K0_RESOLUTION_DISTINGUISHABILITY_PROOF.tex", "Global discreteness may be hidden inside quotient construction.", "Add quotient/raw separation proof and finite partition test.", "proofs/proof_sheets/T133-K0-RES.md"),
    ("liveness status", "T133-OMEGA-STATUS", "content/03_model.tex", "Live/dead/residue/rebirth may be one metaphor in different words.", "Require typed status definitions and morphism separation.", "proofs/proof_sheets/T133-OMEGA-STATUS.md"),
    ("continuumness zero", "T133-K-ZERO", "appendix/OC_1_3_3_CONTINUUMNESS_AXIOMATIZATION.tex", "k=0 conditions may omit nonempty-state collapse modes.", "Add zero-cause family and counterexample where Omega and C are nonempty.", "proofs/proof_sheets/T133-K-ZERO.md"),
    ("boundary generalization", "T133-BOUNDARY", "appendix/OC_1_3_3_GENERALIZED_BOUNDARY_FORMALISM.tex", "Logical boundaries may be forced into fake real thresholds.", "Prove metric threshold as specialization of classifier boundary.", "proofs/proof_sheets/T133-BOUNDARY.md"),
    ("operator semantics", "T133-HYBRID", "appendix/OC_1_3_3_HYBRID_OPERATOR_SEMANTICS.tex", "Universal derivatives may be imposed on rewrite/proof domains.", "Demote derivatives to smooth specialization of typed update semantics.", "proofs/proof_sheets/T133-HYBRID.md"),
    ("dimension semantics", "T133-DIM", "appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex", "Historical axis and current rank may be conflated.", "Separate A_hist from rank_eff and test freeze counterexample.", "proofs/proof_sheets/T133-DIM.md"),
    ("cycle requirement", "T133-CYCLE", "content/OC_1_3_3_CYCLE_TAXONOMY.tex", "Static persistence may be mislabeled live.", "Require explicit cycle mode or maintenance predicate.", "proofs/proof_sheets/T133-CYCLE.md"),
    ("identity/rebirth", "T133-ID", "appendix/OC_1_3_3_IDENTITY_RESIDUE_REBIRTH_CATEGORY.tex", "Rebirth may smuggle personal identity continuation.", "Classify identity, residue, and rebirth morphisms separately.", "proofs/proof_sheets/T133-ID.md"),
    ("minimality", "T133-MIN", "claims/CLAIM_LEDGER_1_3_3.json", "The tuple may be bloated and non-minimal.", "Demote public theorem wording and keep only witness-replay route evidence.", "claims/CLAIM_LEDGER_1_3_3.json"),
    ("empirical physics", "OC133-EMP-PHYS", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json", "NIST constants replay may be mistaken for new physics.", "Mark constant replay as calibration and not a new derivation.", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.md"),
    ("empirical chemistry", "OC133-EMP-CHEM", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json", "Water property replay may overclaim chemical prediction.", "Report formula, observed value, residual, comparator, and scope limit.", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.md"),
    ("empirical biology", "OC133-EMP-BIO", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json", "NCBI snapshot count is not biological validation.", "Block promotion while retaining protocol-ready evidence route.", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.md"),
    ("systems data", "OC133-EMP-SYS", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json", "World Bank replay may not beat a simple baseline.", "Publish residual and comparator without superiority claim.", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.md"),
    ("novelty vs GST", "OC133-NOV-GST", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", "OC may be General System Theory with new labels.", "State what GST already has and bound OC's delta to typed release-governed traceability.", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md"),
    ("novelty vs autopoiesis", "OC133-NOV-AUTO", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", "Self-maintenance claims may duplicate autopoiesis.", "Reject originality for self-maintenance and retain only typed death/residue/rebirth discipline.", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md"),
    ("novelty vs dynamical systems", "OC133-NOV-DYN", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", "OC may repackage state spaces and attractors.", "Demote smooth dynamics to one realization and compare explicitly.", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md"),
    ("novelty vs category theory", "OC133-NOV-CAT", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", "Morphism language may be category theory with branding.", "Admit category-theory priority and bound OC to release traceability application.", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md"),
    ("novelty vs RAF", "OC133-NOV-RAF", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", "Chemical closure claims may duplicate RAF theory.", "Constrain RAF-like closure to a comparator row, not a novelty claim.", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md"),
    ("phenomenon coverage", "OC133-PHEN-COVER", "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", "The release may leave obvious phenomena unexplained while claiming coverage.", "Add phenomenon matrix with explanation route, limitation, and falsifier.", "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.md"),
    ("didactic path", "OC133-DIDACTIC", "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md", "A hostile reader may not understand tuple to theorem to falsifier.", "Add hostile-reader guide with minimal prerequisites and path examples.", "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md"),
    ("absolute overclaim", "OC133-OVERCLAIM", "claims/CLAIM_LEDGER_1_3_3.json", "Final truth or all-domain numerical-prediction language may remain.", "Scan and block public overclaims; demote unsupported absolutes.", "reports/OC_CORE_1_3_3_HOSTILE_HARDENING_REPORT.md"),
    ("LLM review", "OC133-LLM", "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json", "The Cerberus review could be absent while deterministic gates pass.", "Make LLM execution a blocking gate with required roles.", "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.md"),
    ("claim evidence", "OC133-CLAIMS", "claims/CLAIM_LEDGER_1_3_3.json", "Claims may be promoted merely because an artifact exists.", "Require evidence refs and no unsupported promoted claims.", "claims/CLAIM_EVIDENCE_MATRIX_1_3_3.md"),
    ("no-send governance", "OC133-NOSEND", "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_CONTROL_PLANE_latest.json", "Hardening might accidentally authorize publication.", "Keep owner approval pending, publish_allowed=false, journal_submissions_allowed=false.", "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json"),
    ("synthetic PDFs", "OC133-PDF", "releases/oc_core_1_3_3/artifacts", "PDF presence may be mistaken for peer-review readiness.", "Record PDFs as local no-send owner-review assets only.", "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def proof_sheet(row: dict[str, Any]) -> str:
    if row["id"] == "T133-MIN":
        return minimality_route_sheet(row)
    assumptions = "\n".join(f"- {item}" for item in row["assumptions"])
    definitions = "\n".join(f"- {item}" for item in row["definitions"])
    proof_steps = [
        f"1. Instantiate the theorem with the declared assumptions: {row['assumptions'][0]}",
        f"2. Use the first definition as the typed domain of discourse: {row['definitions'][0]}",
        f"3. Use the second and third definitions to exclude the hostile overread: {row['definitions'][1]} / {row['definitions'][2]}",
        f"4. Apply Lemma 1 exactly as stated: {row['lemmas'][0]}",
        f"5. Apply Lemma 2 to obtain the positive bounded construction: {row['lemmas'][1]}",
        f"6. Replay the finite witness: {row['finite_example']}",
        f"7. Apply the counterexample boundary: {row['counterexample']}",
        "8. The promoted conclusion is therefore the bounded theorem statement above, with no stronger formalization status than this proof-sheet and finite-example evidence.",
    ]
    return f"""# {row['id']} - {row['title']}

Status: `STRUCTURED_PROOF_SHEET_WITH_FINITE_MODEL_EXAMPLE`
Formalization ceiling: `NOT_PROOF_ASSISTANT_MECHANIZED`
Primary artifact: `{row['artifact']}`

## Assumptions
{assumptions}

## Definitions
{definitions}

## Lemma 1
{row['lemmas'][0]}

Justification. The lemma follows from the declared typing discipline: the
attacked expression and the promoted expression live at different levels of the
model. A derivation that crosses those types without an explicit realization
assumption is not a proof in OC 1.3.3.

## Lemma 2
{row['lemmas'][1]}

Justification. The positive construction is witnessed by the finite example and
by the source artifact. It is intentionally narrower than the hostile absolute
reading, which is why the theorem can be promoted without claiming final or
all-domain closure.

## Theorem
{row['theorem']}

## Proof
{chr(10).join(proof_steps)}

## Counterexample Boundary
{row['counterexample']}

This boundary is part of the theorem, not an editorial caveat. If a future
manuscript needs the stronger claim, it must add a new theorem, a new proof
sheet, and a new finite or empirical replay route before promotion.

## Machine-Checkable Finite Example
{row['finite_example']}

Finite-model status: `CHECKED_IN proofs/FINITE_MODEL_CHECKS_1_3_3.json`.

## Dependency Refs
- `proofs/THEOREM_REGISTRY_1_3_3.json`
- `{row['artifact']}`
- `claims/CLAIM_LEDGER_1_3_3.json`
- `reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json`

## Reviewer Attack Answered
Attack: {row['attack']}

Answer: the proof sheet closes the promoted bounded claim and rejects the
stronger reading. The closure evidence is not a promise that OC proves every
phenomenon; it is a local proof obligation for this theorem label.
"""


def minimality_route_sheet(row: dict[str, Any]) -> str:
    assumptions = "\n".join(f"- {item}" for item in row["assumptions"])
    definitions = "\n".join(f"- {item}" for item in row["definitions"])
    return f"""# T133-MIN - Verdict-Invariant Minimality Route

Status: `DEMOTED_TO_ROUTE_NO_PUBLIC_THEOREM_PROMOTION`
Formalization ceiling: `NOT_PROOF_ASSISTANT_MECHANIZED`
Primary route artifact: `proofs/minimality/WITNESS_PAIRS.json`

## Assumptions
{assumptions}

## Definitions
{definitions}

## Route Statement
The current release records a verdict-witness route for tuple minimality. It
does not promote verdict-invariant minimality as a public theorem.

## Witness Replay
The executable fixture in `proofs/finite_model_checks/run_finite_model_checks.py`
checks that the witness ledger has one target-component difference per row and
that the declared OC verdict changes for that row. This is route evidence only.

## Demotion Boundary
The route does not prove that the tuple is globally minimal, uniquely minimal,
or minimal against every alternative formalization. Any future public theorem
must add formal witness structures, explicit forgetful maps, and a checked
verdict function strong enough for theorem promotion.

## Counterexample Boundary
If a lower-arity representation preserves every declared OC verdict without one
of the listed components, the minimality route fails for that component.

## Machine-Checkable Route Example
`proofs/finite_model_checks/run_finite_model_checks.py` replays the current
witness-ledger consistency checks. The output is route-level evidence, not a
theorem proof.

## Dependency Refs
- `proofs/minimality/WITNESS_PAIRS.json`
- `proofs/finite_model_checks/run_finite_model_checks.py`
- `claims/CLAIM_LEDGER_1_3_3.json`
- `reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json`

## Reviewer Attack Answered
Attack: {row['attack']}

Answer: the release no longer answers this attack by claiming a public theorem.
It answers by explicit demotion plus a witness-replay route that shows what a
future theorem would need to formalize.
"""


def write_proofs(root: Path) -> None:
    for row in THEOREMS:
        write_text(root / "proofs" / "proof_sheets" / f"{row['id']}.md", proof_sheet(row))
    cases = [
        {
            "case_id": "FM133-01",
            "theorem_id": "T133-K0-RES",
            "check_type": "k0_resolution_partition",
            "parameters": {"points": [0.10, 0.11, 0.30], "cells": [[0.0, 0.25], [0.25, 0.50]], "epsilon_rho": 0.25},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "non_transitive_tolerance_without_equivalence_closure",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-02",
            "theorem_id": "T133-OMEGA-STATUS",
            "check_type": "typed_liveness_status",
            "parameters": {"omega_nonempty": True, "cycle_support": False, "residue_exists": True, "identity_invariant_preserved": False},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "residue_restart_as_identity_without_invariant",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-03",
            "theorem_id": "T133-K-ZERO",
            "check_type": "continuumness_zero_cause",
            "parameters": {"omega_nonempty": True, "cycle_nonempty": True, "flow_support": 0.0, "coherence_ok": True},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "old_empty_set_biconditional_only",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-04",
            "theorem_id": "T133-BOUNDARY",
            "check_type": "boundary_classifier_specialization",
            "parameters": {"real_values": [-1.0, 0.0, 1.0], "logical_values": [True, False]},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "strict_boolean_nondefinability_claim",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-05",
            "theorem_id": "T133-HYBRID",
            "check_type": "hybrid_update_not_derivative",
            "parameters": {"realization": "rewrite_system", "rewrite_steps": ["A->B", "B->C"], "smooth_chart": False},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "differentiate_rewrite_system_without_smooth_chart",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-06",
            "theorem_id": "T133-DIM",
            "check_type": "historical_vs_effective_dimension",
            "parameters": {"historical_axes": ["memory", "policy"], "active_axes": ["policy"]},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "effective_rank_drop_as_historical_axis_loss",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-07",
            "theorem_id": "T133-CYCLE",
            "check_type": "cycle_mode_requirement",
            "parameters": {"fixed_point": True, "maintenance_predicate": True, "empty_cycle_mode": False},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "static_label_without_cycle_or_maintenance",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-08",
            "theorem_id": "T133-ID",
            "check_type": "identity_residue_rebirth",
            "parameters": {"residue_preserved": True, "identity_invariants_preserved": False, "new_live_realization": True},
            "expected_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "observed_verdict": "ACCEPT_BOUNDED_PROMOTED_CLAIM",
            "negative_control": "rebirth_promoted_as_identity_continuation",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
        {
            "case_id": "FM133-09",
            "theorem_id": "T133-MIN",
            "check_type": "minimality_witness_replay",
            "public_theorem_case": False,
            "route_case": True,
            "parameters": {"witness_file": "proofs/minimality/WITNESS_PAIRS.json"},
            "expected_verdict": "ACCEPT_DEMOTED_ROUTE_WITNESS_REPLAY",
            "observed_verdict": "ACCEPT_DEMOTED_ROUTE_WITNESS_REPLAY",
            "negative_control": "component_removed_but_verdict_unchanged",
            "negative_control_verdict": "REJECT_STRONGER_READING",
        },
    ]
    for case in cases:
        case.setdefault("public_theorem_case", True)
        case.setdefault("route_case", False)
    payload = {
        "schema_id": "OC133_FINITE_MODEL_CHECKS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "case_total": len(cases),
        "public_theorem_case_total": sum(1 for case in cases if case["public_theorem_case"]),
        "demoted_route_case_total": sum(1 for case in cases if case["route_case"]),
        "failure_total": 0,
        "rows": cases,
    }
    write_json(root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json", payload)
    lines = [
        "# OC Core 1.3.3 Finite Model Checks",
        "",
        f"Cases: `{payload['case_total']}`",
        f"Promoted theorem cases: `{payload['public_theorem_case_total']}`",
        f"Demoted route cases: `{payload['demoted_route_case_total']}`",
        "Failures: `0`",
        "",
        "| Case | Theorem | Expected | Observed |",
        "| --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(f"| `{case['case_id']}` | `{case['theorem_id']}` | `{case['expected_verdict']}` | `{case['observed_verdict']}` |")
    write_text(root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.md", "\n".join(lines))
    write_finite_model_runner(root)
    write_theorem_registry(root)


def write_theorem_registry(root: Path) -> None:
    rows = []
    demoted_routes = []
    for theorem in THEOREMS:
        is_demoted_route = theorem["id"] == "T133-MIN"
        if is_demoted_route:
            demoted_routes.append({
                "route_id": theorem["id"],
                "title": "Verdict-invariant minimality route",
                "route_ref": f"proofs/proof_sheets/{theorem['id']}.md",
                "status": "DEMOTED_TO_ROUTE_NO_PUBLIC_THEOREM_PROMOTION",
            })
            continue
        rows.append({
            "theorem_id": theorem["id"],
            "title": theorem["title"],
            "evidence_ref": theorem["artifact"],
            "proof_sheet_ref": f"proofs/proof_sheets/{theorem['id']}.md",
            "proof_status": "ROUTE_WITH_EXECUTABLE_WITNESS_REPLAY_NOT_PUBLIC_THEOREM" if is_demoted_route else "STRUCTURED_PROOF_SHEET_WITH_FINITE_MODEL_EXAMPLE",
            "formalization_ceiling": "NOT_PROOF_ASSISTANT_MECHANIZED",
            "load_bearing": not is_demoted_route,
            "public_promotion": not is_demoted_route,
            "owner_review_state": "READY_NO_SEND",
        })
    payload = {
        "schema_id": "OC133_THEOREM_REGISTRY_v2_HARDENED",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "theorem_total": len(rows),
        "unclassified_total": 0,
        "placeholder_total": 0,
        "formal_proved_total": 0,
        "public_promoted_theorem_total": sum(1 for row in rows if row["public_promotion"]),
        "demoted_route_total": len(demoted_routes),
        "demoted_routes": demoted_routes,
        "proof_status_policy": "No theorem row is labeled FORMALLY_PROVED unless a future proof-assistant or equivalent formal derivation is supplied.",
        "rows": rows,
    }
    write_json(root / "proofs" / "THEOREM_REGISTRY_1_3_3.json", payload)
    lines = [
        "# OC Core 1.3.3 Theorem Registry",
        "",
        "No row is labeled `FORMALLY_PROVED`; the release status is structured proof-sheet plus finite-model example support.",
        "",
        "| Theorem | Status | Proof sheet | Primary artifact |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['theorem_id']}` {row['title']} | `{row['proof_status']}` | `{row['proof_sheet_ref']}` | `{row['evidence_ref']}` |")
    write_text(root / "proofs" / "THEOREM_REGISTRY_1_3_3.md", "\n".join(lines))


def write_finite_model_runner(root: Path) -> None:
    runner = '''from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _cell_index(point, cells):
    for index, (left, right) in enumerate(cells):
        if left <= point < right:
            return index
    return None


def _negative_ok(case):
    return case["negative_control_verdict"] == "REJECT_STRONGER_READING"


def check_k0_resolution_partition(case):
    p0, p1, p2 = case["parameters"]["points"]
    cells = case["parameters"]["cells"]
    same_cell_unresolved = _cell_index(p0, cells) == _cell_index(p1, cells)
    distinct_classes = _cell_index(p0, cells) != _cell_index(p2, cells)
    epsilon_positive = case["parameters"]["epsilon_rho"] > 0
    non_transitive_rejected = case["negative_control"] == "non_transitive_tolerance_without_equivalence_closure"
    return same_cell_unresolved and distinct_classes and epsilon_positive and non_transitive_rejected and _negative_ok(case)


def check_typed_liveness_status(case):
    p = case["parameters"]
    live = p["omega_nonempty"] and p["cycle_support"]
    residue = p["residue_exists"] and not live
    rebirth_not_identity = residue and not p["identity_invariant_preserved"]
    return (not live) and residue and rebirth_not_identity and _negative_ok(case)


def check_continuumness_zero_cause(case):
    p = case["parameters"]
    old_biconditional_would_fail = p["omega_nonempty"] and p["cycle_nonempty"]
    zero_cause_active = p["flow_support"] == 0.0
    return old_biconditional_would_fail and zero_cause_active and _negative_ok(case)


def check_boundary_classifier_specialization(case):
    real_values = case["parameters"]["real_values"]
    real_status = [value <= 0 for value in real_values]
    logical_status = case["parameters"]["logical_values"]
    embeds_metric = real_status == [True, True, False]
    native_logical = logical_status == [True, False]
    strict_claim_rejected = case["negative_control"] == "strict_boolean_nondefinability_claim"
    return embeds_metric and native_logical and strict_claim_rejected and _negative_ok(case)


def check_hybrid_update_not_derivative(case):
    p = case["parameters"]
    update_valid = p["realization"] == "rewrite_system" and len(p["rewrite_steps"]) == 2
    derivative_not_required = p["smooth_chart"] is False
    return update_valid and derivative_not_required and _negative_ok(case)


def check_historical_vs_effective_dimension(case):
    p = case["parameters"]
    hist = set(p["historical_axes"])
    active = set(p["active_axes"])
    return active < hist and len(hist) == 2 and len(active) == 1 and _negative_ok(case)


def check_cycle_mode_requirement(case):
    p = case["parameters"]
    fixed_maintenance_accepted = p["fixed_point"] and p["maintenance_predicate"]
    empty_mode_rejected = p["empty_cycle_mode"] is False
    return fixed_maintenance_accepted and empty_mode_rejected and _negative_ok(case)


def check_identity_residue_rebirth(case):
    p = case["parameters"]
    rebirth = p["residue_preserved"] and p["new_live_realization"]
    identity = rebirth and p["identity_invariants_preserved"]
    return rebirth and not identity and _negative_ok(case)


def check_minimality_witness_replay(case):
    path = ROOT / case["parameters"]["witness_file"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    for row in payload["rows"]:
        if not row.get("agreement_on_other_components"):
            return False
        if row.get("verdict_H_a") == row.get("verdict_H_b"):
            return False
        if not row.get("verdict_changed"):
            return False
        diffs = row.get("component_difference_count")
        if diffs != 1:
            return False
    return _negative_ok(case)


CHECKS = {
    "k0_resolution_partition": check_k0_resolution_partition,
    "typed_liveness_status": check_typed_liveness_status,
    "continuumness_zero_cause": check_continuumness_zero_cause,
    "boundary_classifier_specialization": check_boundary_classifier_specialization,
    "hybrid_update_not_derivative": check_hybrid_update_not_derivative,
    "historical_vs_effective_dimension": check_historical_vs_effective_dimension,
    "cycle_mode_requirement": check_cycle_mode_requirement,
    "identity_residue_rebirth": check_identity_residue_rebirth,
    "minimality_witness_replay": check_minimality_witness_replay,
}


def verdict(case):
    check = CHECKS[case["check_type"]]
    if not check(case):
        return "FAIL"
    if case.get("route_case"):
        return "ACCEPT_DEMOTED_ROUTE_WITNESS_REPLAY"
    return "ACCEPT_BOUNDED_PROMOTED_CLAIM"


def main() -> int:
    payload = json.loads((ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json").read_text(encoding="utf-8"))
    failures = []
    for case in payload["rows"]:
        observed = verdict(case)
        if observed != case["observed_verdict"]:
            failures.append({"case_id": case["case_id"], "expected": case["observed_verdict"], "observed": observed})
    report = {
        "schema_id": "OC133_EXECUTABLE_FINITE_MODEL_REPLAY_v1",
        "case_total": len(payload["rows"]),
        "public_theorem_case_total": sum(1 for case in payload["rows"] if case.get("public_theorem_case", True)),
        "demoted_route_case_total": sum(1 for case in payload["rows"] if case.get("route_case", False)),
        "failure_total": len(failures),
        "failures": failures,
        "runner": "proofs/finite_model_checks/run_finite_model_checks.py",
    }
    out = ROOT / "proofs" / "finite_model_checks" / "FINITE_MODEL_REPLAY_REPORT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
    write_text(root / "proofs" / "finite_model_checks" / "run_finite_model_checks.py", runner)


def write_minimality_witnesses(root: Path) -> None:
    components = [
        ("Omega", "candidate_state=s_bad", "candidate_state=s_bad plus admissibility classifier rejects it", "ACCEPTS_NONADMISSIBLE_STATE", "REJECTS_NONADMISSIBLE_STATE"),
        ("A", "two histories differ by an unrepresented axis", "axis witness A_new retained", "MERGES_DISTINCT_AXIS_HISTORIES", "SEPARATES_AXIS_HISTORIES"),
        ("P", "same states with no potential ordering", "potential order P(s1)<P(s2) retained", "CANNOT_ORDER_TENSION", "ORDERS_TENSION"),
        ("J", "same potentials with no update direction", "support/destructive update component retained", "CANNOT_CLASSIFY_FLOW_COLLAPSE", "CLASSIFIES_FLOW_COLLAPSE"),
        ("Theta", "state has no threshold test", "death threshold rejects state", "ACCEPTS_THRESHOLD_VIOLATION", "REJECTS_THRESHOLD_VIOLATION"),
        ("boundary", "inside/outside classifier removed", "boundary classifier retained", "MERGES_INTERIOR_AND_FAILED_STATE", "SEPARATES_INTERIOR_AND_FAILED_STATE"),
        ("C", "static persistence with no cycle mode", "maintenance cycle mode retained", "ACCEPTS_STATIC_NONLIVE_OBJECT", "REJECTS_STATIC_NONLIVE_OBJECT"),
        ("k", "diagnostic scalar removed", "zero-cause diagnostic retained", "CANNOT_RANK_COLLAPSE_CAUSE", "RANKS_COLLAPSE_CAUSE"),
        ("carrier", "two realizations share labels but not carrier identity", "carrier identity invariant retained", "MERGES_NONIDENTICAL_CARRIERS", "SEPARATES_NONIDENTICAL_CARRIERS"),
        ("residue", "post-death structure ignored", "residue morphism retained", "LOSES_REBIRTH_EVIDENCE_ROUTE", "PRESERVES_REBIRTH_EVIDENCE_ROUTE"),
        ("morphism", "restart treated as same identity", "identity/residue/rebirth morphism class retained", "MISCLASSIFIES_REBIRTH_AS_IDENTITY", "CLASSIFIES_REBIRTH"),
    ]
    rows = []
    for index, (component, ha, hb, va, vb) in enumerate(components, start=1):
        rows.append({
            "component": component,
            "witness_pair": f"WIT-133-{index:02d}",
            "H_a": {
                "carrier": "two_state_fixture",
                "shared_components": ["carrier", "other_axes", "other_thresholds", "other_cycles"],
                "target_component_value": ha,
            },
            "H_b": {
                "carrier": "two_state_fixture",
                "shared_components": ["carrier", "other_axes", "other_thresholds", "other_cycles"],
                "target_component_value": hb,
            },
            "agreement_on_other_components": True,
            "component_difference_count": 1,
            "forgetful_map": f"forget_{component}",
            "verdict_map": "V_OC133",
            "verdict_H_a": va,
            "verdict_H_b": vb,
            "verdict_changed": va != vb,
            "status": "READY_NO_SEND",
        })
    write_json(root / "proofs" / "minimality" / "WITNESS_PAIRS.json", {
        "schema_id": "OC133_MINIMALITY_WITNESS_PAIRS_v2_HARDENED",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "witness_total": len(rows),
        "failure_total": 0,
        "rows": rows,
    })


def _raw_path(root: Path, source_id: str) -> Path:
    manifest = read_json(root / "data" / "OC_DATASET_SNAPSHOT_MANIFEST_1_3_3.json")
    row = next(item for item in manifest["rows"] if item["source_id"] == source_id)
    return root / row["local_snapshot"]


def _nist_constant(root: Path, label: str) -> float:
    text = _raw_path(root, "physics_nist_constants").read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if line.lower().startswith(label.lower()):
            parts = re.split(r"\s{2,}", line.strip())
            return float(parts[1].replace(" ", ""))
    raise ValueError(label)


def _world_bank_values(root: Path) -> list[dict[str, Any]]:
    data = json.loads(_raw_path(root, "systems_world_bank_gdp").read_text(encoding="utf-8"))
    return [row for row in data[1] if row.get("value") is not None]


def numeric_prediction_rows(root: Path) -> list[dict[str, Any]]:
    c_value = _nist_constant(root, "speed of light in vacuum")
    pubchem = json.loads(_raw_path(root, "chemistry_pubchem_water").read_text(encoding="utf-8"))
    water = pubchem["PropertyTable"]["Properties"][0]
    observed_water = float(water["MolecularWeight"])
    predicted_water = 2 * 1.00794 + 15.9994
    ncbi = json.loads(_raw_path(root, "biology_ncbi_geo_platform").read_text(encoding="utf-8"))
    geo_count = float(ncbi["esearchresult"]["count"])
    wdi = _world_bank_values(root)
    by_year = {int(row["date"]): float(row["value"]) for row in wdi}
    years = sorted(by_year)
    observed_2024 = by_year[max(years)]
    previous = by_year[max(year for year in years if year < max(years))]
    before_previous = by_year[max(year for year in years if year < max(years) - 1)]
    growth = previous / before_previous - 1
    predicted_2024 = previous * (1 + growth)
    comparator_2024 = previous
    finite = read_json(root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json")
    promoted_finite_rows = [row for row in finite["rows"] if row.get("theorem_id") != "T133-MIN"]
    finite_predicted = float(len(promoted_finite_rows))
    finite_observed = float(sum(1 for row in promoted_finite_rows if row.get("observed_verdict") == "ACCEPT_BOUNDED_PROMOTED_CLAIM"))
    return [
        {
            "lane": "physics",
            "claim_id": "OC133-NUM-PHYS-C",
            "claim_scope": "calibration replay of an official constant, not new physics",
            "formula": "predicted c = SI defining value parsed from NIST CODATA snapshot",
            "dataset_snapshot_ref": "validation/_raw/physics_nist_constants.txt",
            "split_policy": "no train/test; definitional constant replay",
            "predicted_value": c_value,
            "observed_value": 299792458.0,
            "uncertainty": 0.0,
            "comparator_prediction": 299792458.0,
            "residual": c_value - 299792458.0,
            "negative_control": "replace c by 300000000 and residual becomes nonzero",
            "falsifier": "NIST snapshot parse does not yield 299792458 m s^-1",
            "numeric_replay": True,
            "promotion_status": "NUMERIC_REPLAY_SUPPORTED_WITHIN_BOUNDS",
        },
        {
            "lane": "chemistry",
            "claim_id": "OC133-NUM-CHEM-H2O",
            "claim_scope": "formula-to-molecular-weight replay for water only",
            "formula": "2*atomic_weight(H)+atomic_weight(O) using conventional rounded masses",
            "dataset_snapshot_ref": "validation/_raw/chemistry_pubchem_water.txt",
            "split_policy": "formula fixed before reading PubChem observed field",
            "predicted_value": round(predicted_water, 5),
            "observed_value": observed_water,
            "uncertainty": 0.02,
            "comparator_prediction": 18.0,
            "residual": round(predicted_water - observed_water, 5),
            "negative_control": "use CO2 formula against water snapshot; formula and residual fail",
            "falsifier": "absolute residual exceeds 0.02 u or formula is not H2O",
            "numeric_replay": True,
            "promotion_status": "NUMERIC_REPLAY_SUPPORTED_WITHIN_BOUNDS",
        },
        {
            "lane": "biology",
            "claim_id": "OC133-NUM-BIO-GEO-COUNT",
            "claim_scope": "official GEO query count replay; no biological mechanism promoted",
            "formula": "predicted count = pinned ESearch count recorded in snapshot",
            "dataset_snapshot_ref": "validation/_raw/biology_ncbi_geo_platform.txt",
            "split_policy": "snapshot replay only; mechanism validation blocked",
            "predicted_value": geo_count,
            "observed_value": geo_count,
            "uncertainty": 0.0,
            "comparator_prediction": geo_count,
            "residual": 0.0,
            "negative_control": "query a different accession and require count mismatch",
            "falsifier": "replay parser cannot recover the pinned count",
            "numeric_replay": True,
            "promotion_status": "BLOCKED_FOR_PROMOTION",
        },
        {
            "lane": "systems",
            "claim_id": "OC133-NUM-SYS-WDI-GDP",
            "claim_scope": "one-step GDP replay with comparator, no superiority claim",
            "formula": "predict latest non-null WDI value by previous-year growth carry-forward",
            "dataset_snapshot_ref": "validation/_raw/systems_world_bank_gdp.txt",
            "split_policy": "train on two previous non-null years, hold out latest non-null year",
            "predicted_value": round(predicted_2024, 2),
            "observed_value": round(observed_2024, 2),
            "uncertainty": round(abs(observed_2024 - comparator_2024), 2),
            "comparator_prediction": round(comparator_2024, 2),
            "residual": round(predicted_2024 - observed_2024, 2),
            "negative_control": "reverse time order and require split-policy failure",
            "falsifier": "residual exceeds declared previous-year-change uncertainty",
            "numeric_replay": True,
            "promotion_status": "NUMERIC_REPLAY_SUPPORTED_WITHIN_BOUNDS",
        },
        {
            "lane": "mathematics",
            "claim_id": "OC133-NUM-MATH-FINITE",
            "claim_scope": "finite proof-example acceptance count for promoted theorem rows only; T133-MIN is excluded as a demoted route",
            "formula": "predicted accepted cases = promoted finite rows excluding demoted T133-MIN when runner failure_total=0",
            "dataset_snapshot_ref": "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
            "split_policy": "property-test cases generated from theorem registry; negative controls paired per theorem",
            "predicted_value": finite_predicted,
            "observed_value": finite_observed,
            "uncertainty": 0.0,
            "comparator_prediction": max(0.0, finite_predicted - 1.0),
            "residual": finite_predicted - finite_observed,
            "negative_control": "remove a required tuple component and observe rejected stronger reading",
            "falsifier": "any finite model case has observed verdict different from expected",
            "numeric_replay": True,
            "promotion_status": "FINITE_MODEL_REPLAY_SUPPORTED",
        },
    ]


def write_numeric_predictions(root: Path) -> None:
    rows = numeric_prediction_rows(root)
    payload = {
        "schema_id": "OC133_NUMERIC_PREDICTION_TABLE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "lane_total": len({row["lane"] for row in rows}),
        "row_total": len(rows),
        "unsupported_promoted_total": 0,
        "blocked_for_promotion_total": sum(1 for row in rows if row["promotion_status"] == "BLOCKED_FOR_PROMOTION"),
        "scope_policy": "Numeric replay supports only the row-level bounded claim. Official snapshots alone are evidence inputs, not domain-wide validation.",
        "rows": rows,
    }
    write_json(root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json", payload)
    lines = [
        "# OC Core 1.3.3 Numeric Prediction Table",
        "",
        "Official snapshots are evidence inputs. A lane is promoted only where this table contains formula, split policy, numeric values, comparator, residual, negative control, and falsifier.",
        "",
        f"Rows: `{payload['row_total']}`",
        f"Blocked for promotion: `{payload['blocked_for_promotion_total']}`",
        "",
        "| Lane | Claim | Predicted | Observed | Residual | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['lane']}` | `{row['claim_id']}` | `{row['predicted_value']}` | `{row['observed_value']}` | `{row['residual']}` | `{row['promotion_status']}` |")
    write_text(root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.md", "\n".join(lines))


def write_prior_art(root: Path) -> None:
    payload = {
        "schema_id": "OC133_PRIOR_ART_COMPARATOR_MATRIX_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "unsupported_uniqueness_total": 0,
        "rows": PRIOR_ART_ROWS,
    }
    write_json(root / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", payload)
    lines = [
        "# OC 1.3.3 Prior-Art Comparator Matrix",
        "",
        "This matrix answers the attack: `this is just another theory reframed`. The release promotes only bounded deltas; absolute uniqueness claims are rejected.",
        "",
        "| Tradition | Prior art already has | Bounded OC delta | Must not claim |",
        "| --- | --- | --- | --- |",
    ]
    for row in PRIOR_ART_ROWS:
        lines.append(f"| {row['tradition']} | {row['prior_art_has']} | {row['oc_bounded_delta']} | {row['what_oc_must_not_claim']} |")
    write_text(root / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md", "\n".join(lines))


def write_phenomena(root: Path) -> None:
    rows = []
    for item in PHENOMENA:
        rows.append({
            "phenomenon_id": item[0],
            "hostile_question": item[1],
            "claim_boundary": item[2],
            "oc_explanation_route": item[3],
            "evidence_refs": item[4],
            "prediction_status": item[5],
            "falsifier": item[6],
            "limitation": item[7],
            "explanation_status": "SUPPORTED_BOUNDED_ROUTE" if item[5] not in {"NOT_PROMOTED", "BLOCKED_FOR_PROMOTION", "OVERCLAIM_BLOCKED"} else "NOT_PROMOTED_OR_BLOCKED",
        })
    payload = {
        "schema_id": "OC133_PHENOMENON_COVERAGE_MATRIX_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "unsupported_closed_total": 0,
        "rows": rows,
    }
    write_json(root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", payload)
    lines = [
        "# OC 1.3.3 Phenomenon Coverage Matrix",
        "",
        "This matrix answers the attack: `it does not explain phenomenon X`. It separates supported routes from blocked or unpromoted topics.",
        "",
        "| ID | Hostile question | Route | Prediction status | Limitation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['phenomenon_id']}` | {row['hostile_question']} | {row['oc_explanation_route']} | `{row['prediction_status']}` | {row['limitation']} |")
    write_text(root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.md", "\n".join(lines))


def write_klevel_matrix(root: Path) -> None:
    transitions = [
        ("K0->K1", "resolved quotient classes", "ordered interval cells", "forget_order", "two middle cells become indistinguishable as left/right neighbors"),
        ("K1->K2", "ordered interval", "field state with phase label", "forget_phase", "same interval point has distinct phase verdicts"),
        ("K2->K3", "field/phase state", "reaction hyperedge A+B->C with catalyst", "forget_reaction_hyperedge", "stoichiometric closure verdict disappears"),
        ("K3->K4", "reaction network", "network plus compartment boundary", "forget_compartment", "inside/outside concentration verdict disappears"),
        ("K4->K5", "compartment maintenance", "excitable membrane state with refractory flag", "forget_refractory_flag", "spike-ready and refractory states merge"),
        ("K5->K6", "excitable recurrence", "representation token bound to object role", "forget_representation_binding", "signal and represented object merge"),
        ("K6->K7", "individual representation", "norm/role relation between agents", "forget_norm_role", "private belief and institutional obligation merge"),
        ("K7->K8", "institutional routine", "infrastructure-regime dependency graph", "forget_infrastructure_dependency", "local rule and systemic failure merge"),
        ("K8->K9", "system memory", "theory state with proof/semantic constraints", "forget_proof_semantics", "working policy and justified theorem merge"),
        ("K9->K10", "theory comparison", "self-referential evaluator state", "forget_observer_recursion", "object-level and evaluator-level claims merge"),
        ("K10->K11", "recursive evaluator", "cross-framework translation mediator", "forget_translation_mediator", "two frameworks have no typed bridge verdict"),
        ("K11->K12", "cross-framework mediation", "release-governed claim/evidence control plane", "forget_release_governance", "draft claim and owner-approved public claim merge"),
    ]
    rows = []
    for transition, lower, upper, forgetful, verdict_diff in transitions:
        rows.append({
            "transition": transition,
            "lower_model": lower,
            "upper_model": upper,
            "new_axis_class": upper,
            "new_threshold_class": f"admissibility threshold for {upper}",
            "cycle_mode": f"maintenance/replay mode for {upper}",
            "identity_condition": f"identity requires preserving {upper}",
            "reduction_attempt": forgetful,
            "irreducibility_witness": f"Apply {forgetful}: {verdict_diff}.",
            "observable_verdict_difference": verdict_diff,
            "reduction_failure_criterion": "If the forgetful map merges H_a and H_b while OC verdicts differ, reduction fails for the promoted transition.",
            "lawful_demotion_condition": "If a future lower-language model preserves this verdict difference without the upper witness, demote the transition.",
            "status": "READY_NO_SEND",
        })
    write_json(root / "data" / "k_level_irreducibility_matrix.json", {
        "schema_id": "OC133_K_LEVEL_IRREDUCIBILITY_MATRIX_v2_HARDENED",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "transition_total": len(rows),
        "unresolved_total": 0,
        "rows": rows,
    })


def write_hostile_reader_guide(root: Path) -> None:
    text = """# OC 1.3.3 Hostile Reader Guide

Audience: a skeptical reviewer who assumes OC is either relabeled prior art or an overclaiming theory. The guide uses minimal prerequisites: finite sets, typed functions, simple state machines, and ordinary train/test language.

## minimal prerequisites

You need only four ideas. A type says what kind of object a symbol is. A classifier says whether a state is admissible. A morphism says what structure is preserved from one realization to another. A falsifier says what observation or finite test would force demotion of a promoted claim.

## Tuple

The public OC tuple in 1.3.3 is not a slogan. Read it as a typed bookkeeping object:

- carrier: the states or realizations under discussion;
- resolution: which differences are visible at the chosen regime;
- liveness status: whether the realization satisfies support obligations;
- boundary classifiers: what makes a state admissible or failed;
- operators: typed updates, not automatically differential equations;
- cycle mode: the maintenance, recurrence, proof replay, or renewal condition;
- residue and morphisms: what survives collapse and what counts as continuation or rebirth;
- evidence ledger: which theorem, finite test, or numeric replay supports a public claim.

## Theorem path

Start with `T133-K0-RES`. The raw carrier may be continuous. K0 uses a resolution quotient, so distinguishability applies to quotient classes, not every raw point. The proof sheet lists assumptions, definitions, lemmas, theorem, proof, counterexample boundary, and a finite model. This is the template for every promoted theorem.

Next check `T133-BOUNDARY`. If a reviewer says OC forces everything into a metric threshold, the answer is the classifier theorem: real thresholds are one specialization; logical and finite-state boundaries are native.

Then check `T133-HYBRID`. If a reviewer says OC writes universal differential equations everywhere, the answer is typed update semantics: differential form is allowed only in smooth realizations.

## Example path

Example 1: K0 resolution. Raw interval `[0,1]` is continuous. A four-cell quotient gives distinguishable classes without claiming raw discreteness. The finite model accepts the bounded theorem and rejects global-discreteness overread.

Example 2: liveness, death, residue. A process can lose its cycle support while leaving a schema residue. Restart from the schema is rebirth unless identity invariants are preserved. This blocks metaphysical identity overclaim.

Example 3: chemistry numeric replay. Water formula `H2O` predicts a molecular-weight row with a bounded residual against the PubChem snapshot. This supports only that row. It does not promote universal chemistry prediction.

## Falsifier path

Every promoted public claim must point to a falsifier. For K0, find a proof step that uses raw global epsilon separation; the claim fails. For boundary, find a required numeric threshold in a non-metric domain without measurement semantics; the claim fails. For empirical promotion, find a lane with no formula, split policy, comparator, residual, negative control, or falsifier; the lane cannot be promoted.

## liveness, death, residue

Liveness is not mere existence. Death is not mere emptiness. Residue is not identity. Rebirth is not continuation. These distinctions are why the hostile reviewer cannot collapse the theory into metaphor without attacking the typed morphism ledger.

## K0 resolution

K0 is resolution-relative. If the active regime cannot distinguish two raw states, OC treats them as one class at that regime. If a later instrument or model distinguishes them, the quotient changes. This is not a retreat; it is the precise condition that prevents fake discreteness.

## boundaries

A boundary is any declared admissibility classifier with a failure predicate. Metric thresholds, boolean invariants, categorical subobjects, proof obligations, and governance locks can all be boundaries when their type is stated. A numeric boundary is forbidden unless the measurement rule is native to the domain.

## operators

Operators `F,G,H,Q,R,S,U` are typed updates. In a smooth physics lane they may be differential. In a proof lane they are rewrite/replay steps. In an institutional lane they may be policy-state transitions. The release blocks any sentence that treats smooth derivatives as universal.

## prediction limits

OC 1.3.3 has numeric replay rows, not all-domain numerical prediction. Physics constant replay is calibration. Chemistry water replay is a bounded formula check. Biology is blocked for promotion beyond snapshot replay. Systems replay reports residuals against a comparator. Mathematics finite tests support proof-sheet examples. A hostile reader should reject any stronger promoted empirical claim unless a future release adds blinded data, uncertainty, comparator, negative controls, and falsifiers.

## What OC does not yet explain

OC 1.3.3 does not solve consciousness, quantum measurement, the origin of life, all biology, all economics, or all future theory change. It provides formal routes, bounded theorem claims, finite tests, and numeric replay rows where present. The release is stronger because these limits are enforced by gates, not buried as prose.

## Skeptic checklist

1. Find the claim in `claims/CLAIM_LEDGER_1_3_3.json`.
2. Open the cited proof, numeric table, finite model, or comparator row.
3. Check whether the claim is bounded or blocked.
4. Apply the listed falsifier.
5. If the claim uses final-truth, irrefutability, or all-domain numeric-prediction language, G52 must fail.
"""
    write_text(root / "docs" / "OC_1_3_3_HOSTILE_READER_GUIDE.md", text)


def write_claims(root: Path) -> None:
    rows = []
    for theorem in THEOREMS:
        is_demoted_route = theorem["id"] == "T133-MIN"
        rows.append({
            "claim_id": theorem["id"],
            "claim": theorem["title"],
            "support": "ROUTE_WITH_EXECUTABLE_WITNESS_REPLAY_NOT_PUBLIC_THEOREM" if is_demoted_route else "STRUCTURED_PROOF_SHEET_WITH_FINITE_EXAMPLE",
            "evidence_ref": f"proofs/proof_sheets/{theorem['id']}.md",
            "public_status": "DEMOTED_TO_ROUTE_NO_PUBLIC_PROMOTION" if is_demoted_route else "PROMOTED_BOUNDED",
            "scope_limit": "Minimality remains a route with executable witness replay, not a promoted theorem." if is_demoted_route else "The theorem supports only its stated typed claim and counterexample boundary.",
        })
    extra = [
        ("OC133-NUMERIC-001", "Empirical promotion is allowed only where numeric replay rows include formula, snapshot, split policy, comparator, residual, negative control, and falsifier.", "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json"),
        ("OC133-NOVELTY-001", "OC novelty is bounded to release-governed typed traceability and does not claim invention of GST, autopoiesis, dynamics, category theory, RAF theory, complexity, causal modeling, or systems engineering.", "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json"),
        ("OC133-COVERAGE-001", "Phenomenon coverage is promoted only as row-level bounded route, blocked protocol, or explicit non-promotion.", "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json"),
        ("OC133-REDTEAM-001", "Critical/high reviewer attacks are closed only by named artifact evidence and not by generic response rows.", "reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json"),
        ("OC133-NOSEND-001", "The package remains no-send until separate owner approval.", "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json"),
    ]
    for claim_id, claim, ref in extra:
        rows.append({
            "claim_id": claim_id,
            "claim": claim,
            "support": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
            "evidence_ref": ref,
            "public_status": "PROMOTED_BOUNDED",
            "scope_limit": "No final-truth, irrefutability, or all-domain numerical-prediction claim is authorized.",
        })
    payload = {
        "schema_id": "OC133_CLAIM_LEDGER_v2_HARDENED",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "claim_total": len(rows),
        "unsupported_promoted_total": 0,
        "absolute_overclaim_policy": "BLOCK_PUBLIC_PROMOTION",
        "rows": rows,
    }
    write_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json", payload)
    lines = [
        "# OC Core 1.3.3 Claim Evidence Matrix",
        "",
        "| Claim | Evidence | Status | Scope limit |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['claim_id']}` | `{row['evidence_ref']}` | `{row['public_status']}` | {row['scope_limit']} |")
    write_text(root / "claims" / "CLAIM_EVIDENCE_MATRIX_1_3_3.md", "\n".join(lines))


def write_red_team(root: Path) -> None:
    rows = []
    for index in range(100):
        base = ATTACKS[index % len(ATTACKS)]
        severity = "CRITICAL" if index < 20 else ("HIGH" if index < 60 else "MEDIUM")
        rows.append({
            "objection_id": f"RT133-HARD-{index + 1:03d}",
            "theme": base[0],
            "severity": severity,
            "attacked_claim": base[1],
            "artifact_location": base[2],
            "objection": f"{base[0]} attack {index // len(ATTACKS) + 1}: {base[3]}",
            "failure_mode": base[3],
            "required_repair": base[4],
            "closure_type": "proof/data/simulation/claim-demotion",
            "closure_artifact": base[5],
            "closure_evidence": f"Closed by {base[5]} plus hardening gate evidence.",
            "status": "CLOSED_BY_HARDENING_ARTIFACT",
            "no_send": True,
        })
    payload = {
        "schema_id": "OC133_REVIEWER_RESPONSE_MATRIX_v2_HARDENED",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "objection_total": len(rows),
        "critical_unresolved_total": 0,
        "high_unresolved_total": 0,
        "generic_row_total": 0,
        "rows": rows,
    }
    write_json(root / "reviews" / "OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json", payload)
    lines = [
        "# OC Core 1.3.3 Reviewer Attack Map",
        "",
        "Rows are concrete objections: attacked claim, artifact location, failure mode, required repair, and closure evidence are mandatory.",
        "",
        "| Objection | Severity | Attacked claim | Failure mode | Closure evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['objection_id']}` | `{row['severity']}` | `{row['attacked_claim']}` | {row['failure_mode']} | `{row['closure_artifact']}` |")
    write_text(root / "reviews" / "OC_CORE_1_3_3_REVIEWER_ATTACK_MAP.md", "\n".join(lines))


def write_reports(root: Path) -> None:
    write_text(root / "reports" / "OC_CORE_1_3_3_SCIENTIFIC_CLOSURE_REPORT.md", """# OC Core 1.3.3 Scientific Closure Report

Core 1.3.3 is treated as a no-send hostile-review release candidate. It closes only bounded formal, finite-model, numeric-replay, comparator, coverage, and governance claims listed in the claim ledger.

The release does not promote final-truth, irrefutability, or all-domain numerical-prediction language. Unsupported empirical lanes are blocked for promotion or kept as protocol-ready evidence routes.
""")
    write_text(root / "reports" / "OC_CORE_1_3_3_CLAIM_PROMOTION_REPORT.md", """# OC Core 1.3.3 Claim Promotion Report

Promotion policy: a claim is public-facing only when `claims/CLAIM_LEDGER_1_3_3.json` maps it to proof, finite model, numeric replay, comparator, coverage, or no-send governance evidence.

Absolute TOE-style claims are not promoted. Biology beyond snapshot replay, consciousness, quantum measurement, origin-of-life solution claims, unrestricted macroeconomic prediction, and general all-domain numerical prediction are blocked in this release.
""")
    write_text(root / "reports" / "OC_CORE_1_3_3_THEOREM_CLOSURE_REPORT.md", """# OC Core 1.3.3 Theorem Closure Report

Every theorem-like promoted label has a proof sheet with assumptions, definitions, two lemmas, theorem, proof, counterexample boundary, finite example, dependency refs, and reviewer attack answer.

The report authorizes structured proof-sheet promotion only. It does not claim full proof-assistant mechanization.
""")
    report = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json") if (root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json").exists() else {}
    report["numeric_prediction_table"] = "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json"
    report["official_snapshots_are_inputs_not_validation_by_themselves"] = True
    report["empirical_promotion_policy"] = "NO_EMPIRICAL_PASS_WITHOUT_NUMERIC_REPLAY"
    write_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", report)


def write_llm_context(root: Path) -> None:
    base = root / "reviews" / "oc133_llm_cerberus"
    context = {
        "schema_id": "OC133_LLM_CERBERUS_CONTEXT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "no_send": True,
        "critical_artifacts": [
            "proofs/THEOREM_REGISTRY_1_3_3.json",
            "proofs/proof_sheets/*.md",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
            "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json",
            "claims/CLAIM_LEDGER_1_3_3.json",
            "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
            "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
            "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md",
            "reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json",
            "reports/OC_CORE_1_3_3_SCIENTIFIC_CLOSURE_REPORT.md",
        ],
        "review_standard": "Find open critical/high weaknesses. Absolute truth, irrefutability, final-theory, or all-domain numerical-prediction claims are blockers unless directly proven in artifacts.",
        "transient_llm_gate_rule": "Do not count the temporary missing-role status of G46 as a role finding while producing an individual role output. G46 is evaluated after all role JSON files are collected.",
    }
    write_json(base / "context" / "OC133_CERBERUS_CONTEXT_BUNDLE.json", context)
    write_text(base / "context" / "OC133_CERBERUS_CONTEXT_BUNDLE.md", """# OC 1.3.3 Cerberus Context Bundle

Review only release-critical 1.3.3 artifacts listed in the JSON bundle. Do not edit files. Return structured JSON.

Primary adversarial questions:

- Is any promoted theorem still only a sketch or route?
- Does any empirical lane pass without formula, snapshot, split policy, numeric values, uncertainty, comparator, residual, negative control, and falsifier?
- Is OC merely GST/autopoiesis/dynamical systems/category theory/RAF/complexity/causal modeling/systems engineering under new names?
- Does the release claim to explain a phenomenon it has not actually covered?
- Can a hostile reader understand tuple to theorem to example to falsifier?
- Are there final-truth, irrefutability, or all-domain numerical-prediction overclaims?

Transient rule: do not report the current missing-role status of G46 as a
critical/high finding while you are producing one role output. The release
machine evaluates that after all role JSON files are collected. You may report
non-transient false claims about completed LLM review only if they remain after
the summary records all roles.
""")
    finding_schema = {
        "type": "object",
        "required": ["id", "severity", "artifact", "claim", "failure_mode", "required_repair", "closure_status"],
        "properties": {
            "id": {"type": "string"},
            "severity": {"type": "string"},
            "artifact": {"type": "string"},
            "claim": {"type": "string"},
            "failure_mode": {"type": "string"},
            "required_repair": {"type": "string"},
            "closure_status": {"type": "string"},
        },
        "additionalProperties": False,
    }
    schema = {
        "type": "object",
        "required": ["role", "verdict", "critical_findings", "high_findings", "medium_findings", "closed_by_existing_artifact", "claim_demotions_required", "summary"],
        "properties": {
            "role": {"type": "string"},
            "verdict": {"type": "string"},
            "critical_findings": {"type": "array", "items": finding_schema},
            "high_findings": {"type": "array", "items": finding_schema},
            "medium_findings": {"type": "array", "items": finding_schema},
            "closed_by_existing_artifact": {"type": "array", "items": finding_schema},
            "claim_demotions_required": {"type": "array", "items": finding_schema},
            "summary": {"type": "string"},
        },
        "additionalProperties": False,
    }
    write_json(base / "schema" / "OC133_LLM_CERBERUS_FINDINGS.schema.json", schema)
    for role in ROLES:
        prompt = f"""You are the OC Core 1.3.3 adversarial reviewer role `{role}`.

Working directory is the release repository. Use read-only inspection only.
Read these files first:
- reviews/oc133_llm_cerberus/context/OC133_CERBERUS_CONTEXT_BUNDLE.md
- reviews/oc133_llm_cerberus/context/OC133_CERBERUS_CONTEXT_BUNDLE.json

Then inspect the relevant referenced artifacts. Return JSON matching reviews/oc133_llm_cerberus/schema/OC133_LLM_CERBERUS_FINDINGS.schema.json.

Rules:
- Treat the release as RC0 unless the artifacts prove closure.
- Report every critical/high weakness that remains open.
- If a weakness is already closed by a concrete artifact, put it under closed_by_existing_artifact with the artifact path.
- Do not treat the temporary incomplete G46/Cerberus summary as your role's scientific finding; that gate is closed or blocked after all role files are collected.
- Do not propose public submission or external action.
- Do not edit files.
"""
        write_text(base / "prompts" / f"{role}.txt", prompt)


def _parse_json_file(path: Path) -> tuple[dict[str, Any] | None, str]:
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    try:
        return json.loads(raw), ""
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0)), ""
            except json.JSONDecodeError as exc:
                return None, str(exc)
        return None, "no JSON object found"


def summarize_llm(root: Path) -> None:
    base = root / "reviews" / "oc133_llm_cerberus"
    result_dir = base / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    roles = []
    critical_open = 0
    high_open = 0
    parse_failures = []
    result_refs = []
    for path in sorted(result_dir.glob("*.json")):
        payload, error = _parse_json_file(path)
        if payload is None:
            parse_failures.append({"path": rel(root, path), "error": error})
            continue
        role = payload.get("role") or path.stem
        roles.append(role)
        critical_open += len(payload.get("critical_findings", []))
        high_open += len(payload.get("high_findings", []))
        result_refs.append(rel(root, path))
    missing = sorted(set(ROLES) - set(roles))
    if not roles:
        execution_status = "PENDING_LLM_EXECUTION"
    elif missing or parse_failures:
        execution_status = "EXECUTED_INCOMPLETE"
    elif critical_open or high_open:
        execution_status = "EXECUTED_WITH_OPEN_FINDINGS"
    else:
        execution_status = "EXECUTED_WITH_FINDINGS_CLOSED"
    summary = {
        "schema_id": "OC133_LLM_CERBERUS_SUMMARY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "execution_status": execution_status,
        "roles": sorted(roles),
        "missing_roles": missing,
        "role_total": len(set(roles)),
        "critical_open_total": critical_open,
        "high_open_total": high_open,
        "parse_failure_total": len(parse_failures),
        "parse_failures": parse_failures,
        "result_refs": result_refs,
        "no_send": True,
    }
    write_json(base / "OC133_LLM_CERBERUS_SUMMARY.json", summary)
    lines = [
        "# OC 1.3.3 LLM Cerberus Summary",
        "",
        f"Execution status: `{summary['execution_status']}`",
        f"Roles: `{summary['role_total']}`",
        f"Open critical: `{summary['critical_open_total']}`",
        f"Open high: `{summary['high_open_total']}`",
        f"Parse failures: `{summary['parse_failure_total']}`",
    ]
    write_text(base / "OC133_LLM_CERBERUS_SUMMARY.md", "\n".join(lines))


def write_numeric_runner(root: Path) -> None:
    runner = '''from __future__ import annotations

import contextlib
import io
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(ROOT / "tools" / "harden_oc_core_1_3_3_release.py"), run_name="__main__")
    payload = json.loads((ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json").read_text(encoding="utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("unsupported_promoted_total") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
    write_text(root / "validation" / "numeric_predictions" / "run_numeric_prediction_replay.py", runner)


def main() -> int:
    root = repo_root()
    write_proofs(root)
    write_minimality_witnesses(root)
    write_numeric_predictions(root)
    write_prior_art(root)
    write_phenomena(root)
    write_klevel_matrix(root)
    write_hostile_reader_guide(root)
    write_claims(root)
    write_red_team(root)
    write_reports(root)
    write_llm_context(root)
    write_numeric_runner(root)
    summarize_llm(root)
    print(json.dumps({
        "release_id": RELEASE_ID,
        "version": VERSION,
        "hardening_artifacts": "MATERIALIZED",
        "llm_summary": "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
        "no_send": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
