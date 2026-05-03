# OC Core Quality Metric Catalog

Status: `OC_CORE_QUALITY_METRIC_CATALOG_READY`
Artifact hash: `c3fbdeba0fcb872e12d83e9c8f6a07696d219f29f24cfbcd47b3b2a7d27a9f81`
Metric total: `15`

Canonical storage is JSON/MD. SQLite is generated only as a deterministic query cache.

## Standard Sources

- `nature_reporting_data_code_protocols` Nature Communications reporting standards and availability of data, materials, code and protocols: https://www.nature.com/ncomms/editorial-policies/reporting-standards
- `icmje_recommendations` ICMJE Recommendations: https://www.icmje.org/recommendations/
- `top_guidelines` Transparency and Openness Promotion Guidelines: https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/
- `logion_toe_grade_internal_standard` Logion TOE-grade positive and negative release-quality standard: internal://logion/release_assembly/oc_core/text_fill_rules

## Metrics

### `coverage.target_obligation` Target obligation coverage

- Family: `scientific_validity`
- Polarity: `positive`
- Default mode: `auto_plus_manual`
- Scorer: `l10_coverage_status_scorer`
- Full coverage: The L10 obligation has complete, partial, planned, missing, or not_assessed status with reason and source route.
- Parameterization: Map aggregator coverage_status and mapping-quality row to a numeric coverage score; not_assessed remains unscored.

### `trace.exact_source_binding` Exact source and provenance binding

- Family: `claim_evidence_trace`
- Polarity: `positive`
- Default mode: `auto`
- Scorer: `source_family_binding_scorer`
- Full coverage: Every claim-bearing or explanatory slot has exact source family candidates and later exact artifact paths.
- Parameterization: Score source_family_ids, extraction_rule, integration_rule, and verification_rule completeness.

### `claim.boundary_discipline` Claim boundary discipline

- Family: `claim_evidence_trace`
- Polarity: `negative_guard`
- Default mode: `auto_plus_manual`
- Scorer: `claim_boundary_scorer`
- Full coverage: The node states what may and may not be claimed from its support route.
- Parameterization: Score claim_boundary specificity and scan generated artifact text for stronger language than supported.

### `formal.proof_binding` Formal theorem/proof binding

- Family: `formal_proof`
- Polarity: `positive`
- Default mode: `auto_plus_manual`
- Scorer: `formal_artifact_binding_scorer`
- Full coverage: Formal claims cite theorem/proof/Lean/finite-model evidence or are explicitly demoted.
- Parameterization: Require theorem/proof artifact references for proof-bearing nodes; waive for non-formal nodes.

### `empirical.protocol_support` Empirical or computational protocol support

- Family: `empirical_support`
- Polarity: `positive`
- Default mode: `auto_plus_manual`
- Scorer: `empirical_protocol_scorer`
- Full coverage: Empirical nodes declare formula, comparator, uncertainty/residual, negative control, falsifier, and replay hash when promoted.
- Parameterization: Score protocol fields when empirical support is required; otherwise waive with reason.

### `didactic.reader_task_payoff` Reader task and payoff

- Family: `didactics`
- Polarity: `positive`
- Default mode: `auto_plus_manual`
- Scorer: `reader_task_scorer`
- Full coverage: The node tells the reader what to understand or do and why it matters in the argument.
- Parameterization: Score reader_task presence, specificity, and downstream paragraph payoff.

### `style.publication_grade_prose` Publication-grade prose and terminology

- Family: `style`
- Polarity: `negative_guard`
- Default mode: `auto_plus_llm`
- Scorer: `publication_grade_text_scorer`
- Full coverage: Generated prose is coherent, edited, terminology-stable, and not raw ledger/control text.
- Parameterization: Scan generated text for placeholders, repeated boilerplate, control-plane language, malformed notation, and rough style.

### `structure.sequence_transition` Argument sequence and transition quality

- Family: `structure`
- Polarity: `positive`
- Default mode: `auto_plus_manual`
- Scorer: `sequence_transition_scorer`
- Full coverage: The node preserves the frozen top-down sequence and has an explicit handoff where needed.
- Parameterization: Score order_path consistency and transition role against surrounding nodes.

### `visual.figure_table_operationalization` Figure/table operationalization

- Family: `figures_tables`
- Polarity: `positive`
- Default mode: `manual_or_auto`
- Scorer: `figure_table_need_scorer`
- Full coverage: Visual/table-bearing nodes declare the intended operation, reader use, caption role, and source binding.
- Parameterization: Apply to figure/table/atlas/matrix nodes; waive for prose-only nodes.

### `bibliography.prior_art_depth` Prior-art and literature depth

- Family: `bibliography_prior_art`
- Polarity: `positive`
- Default mode: `auto_plus_manual`
- Scorer: `prior_art_depth_scorer`
- Full coverage: Prior-art nodes cite current scientific context, comparator method, overlap, residual delta, and limits.
- Parameterization: Apply to prior-art/comparator/bibliography nodes; waive for frontmatter and purely formal nodes.

### `artifact.role_hygiene` Artifact role and file hygiene

- Family: `artifact_hygiene`
- Polarity: `negative_guard`
- Default mode: `auto`
- Scorer: `artifact_role_hygiene_scorer`
- Full coverage: Each release artifact matches its role, exists, hashes cleanly, and has no stale/local/secret/control leakage.
- Parameterization: Apply to package artifact rows, not prose-only L10 nodes.

### `public.no_overclaim_surface` No-overclaim and public-surface safety

- Family: `public_surface_safety`
- Polarity: `negative_guard`
- Default mode: `auto_plus_llm`
- Scorer: `public_surface_safety_scorer`
- Full coverage: Public surfaces do not claim final TOE/all-domain superiority unless the evidence literally supports it.
- Parameterization: Scan claim_boundary and generated text; route broad unsupported claims to research obligations.

### `repro.replay_trace` Reproducibility and replay trace

- Family: `reproducibility`
- Polarity: `positive`
- Default mode: `auto`
- Scorer: `reproducibility_trace_scorer`
- Full coverage: Reproducibility nodes expose build/replay inputs, expected outputs, hashes, and failure interpretation.
- Parameterization: Apply to reproducibility/data/software/artifact nodes; waive elsewhere with reason.

### `review.resilience_response` Reviewer resilience and objection closure

- Family: `reviewer_resilience`
- Polarity: `positive`
- Default mode: `auto_plus_llm`
- Scorer: `reviewer_resilience_scorer`
- Full coverage: Reviewer-facing nodes state objection, threatened claim, evidence answer, residual risk, and reopening condition.
- Parameterization: Apply to review/limits/falsifier nodes; waive for title metadata and purely definitional slots.

### `metadata.identity_citation` Identity, citation, authorship, instrument, and method metadata

- Family: `metadata_identity`
- Polarity: `positive`
- Default mode: `auto`
- Scorer: `metadata_identity_scorer`
- Full coverage: Identity nodes and metadata artifacts distinguish author, instrument, method, release version, citation, and license.
- Parameterization: Apply to frontmatter/metadata nodes and citation artifacts; waive for scientific body paragraphs.
