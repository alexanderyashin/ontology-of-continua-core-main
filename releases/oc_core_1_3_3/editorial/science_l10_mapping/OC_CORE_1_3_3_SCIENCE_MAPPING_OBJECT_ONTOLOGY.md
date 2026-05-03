# OC Core 1.3.3 Science Mapping Object Ontology

Status: ACTIVE_MAPPING_ONTOLOGY_V1_0
Artifact hash: `425ee15210be3857779c0c3a1f6cd154cb60f26eaeddb9c4f6c11935090e80bd`

## Object Classes

- science_source_family: A curated class of existing OC science artifacts that can support L10 slots. External surface: Not directly exposed; only sanitized source bindings may enter manuscripts.
- l10_terminal_slot: A frozen paragraph-slot obligation in the manuscript structure. External surface: Not exposed as prose; used to guide later drafting.
- binding_candidate: A possible source-family-to-L10 connection pending exact path binding in fill-control. External surface: Internal planning only.
- transformation_rule: A rule for turning science material into future prose without performing the transformation now. External surface: Internal editorial method unless later summarized.
- coverage_status: A reserved maturity value for future fill assessment. External surface: May be summarized only after fill assessment audit.

## Relations

- source_family_supports_l10_role: science_source_family -> l10_terminal_slot. Support is mediated by argument_role, not by accidental file proximity.
- binding_candidate_precedes_transformation: binding_candidate -> transformation_rule. Exact source binding must exist before any science-to-text transformation is executed.
- coverage_status_is_not_claim: coverage_status -> l10_terminal_slot. Coverage statuses guide work; they are not scientific claims.
