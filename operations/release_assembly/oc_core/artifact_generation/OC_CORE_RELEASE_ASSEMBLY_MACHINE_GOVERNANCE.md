# OC Core Release Assembly Machine Governance

Status: `OC_CORE_ARTIFACT_GENERATION_RULES_READY`
Artifact hash: `2e9bda07a9e037e3bdd32366b113a41dba18bc0b8a50c398a856db5efa4e0446`

## Operating Directive

- primary_focus: validate the assembly and routing machine before trusting generated artifacts
- start_point: always begin cheap review at package TOC, artifact scopes, terminal contracts, and transitions
- error_handling: classify the highest machine layer that can prevent the error class, repair that layer top-down, then regenerate a new assembly revision
- delta_policy: repair only the minimal affected generation, routing, source-intake, or transition rule; do not hand-edit final artifacts
- growth_policy: every accepted repair becomes a static regression gate so the same class cannot recur silently

## Cheap-First Ladder

- `structure_and_toc_static_review` (cheap): node_total, accepted_source_total, rejected_source_total, route_gap_total
- `source_intake_and_contract_review` (cheap): blocked_terminal_total, non_english_source_total, control_route_total, missing_source_hash_total
- `transition_and_public_surface_review` (cheap): transition_record_total, forbidden_phrase_total, unicode_surface_warning_total, local_path_leak_total
- `pdf_and_package_smoke_review` (moderate): pdf_build_failure_total, pdf_missing_character_warning_total, manifest_missing_file_total
- `expensive_editorial_or_llm_review` (expensive): critical_finding_total, high_finding_total, regression_total

## Quantitative Regression Metrics

- `terminal_node_total`: nondecreasing_when_recovery_scope_same
- `accepted_source_total`: nondecreasing_unless_rejection_reason_recorded
- `rejected_source_total`: explainable_by_rejection_class
- `blocked_terminal_total`: zero
- `transition_record_coverage`: exact_terminal_minus_one
- `pdf_page_count_by_artifact`: no_baseline_regression_without_waiver
- `public_surface_leak_total`: zero
- `pdf_engine_warning_total`: zero
- `publication_action_total`: zero_in_review_space
