# OC Core 1.3.3 Grand Evidence Repair Router

Verdict: `REPAIR_ROUTE_BLOCKED_CAPABILITIES_MISSING`
Work orders: `17`
Missing capabilities: `6`
No-send: `True`

Routing does not close evidence blockers. A routed work order closes only after the preferred capability emits a strict valid evidence pack and the grand empirical gate re-audits it as valid.

| Work Order | Domain | Failure Class | Component | Status |
| --- | --- | --- | --- | --- |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-COMPARATOR_OR_RESIDUAL_FAILURE` | `biology` | `comparator_or_residual_failure` | `tools/oc133_grand_empirical_evidence_factory.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-GRAND_SUPPORT_NOT_AUTHORIZED` | `biology` | `grand_support_not_authorized` | `tools/oc133_biology_ncbi_batch_factory.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-INSUFFICIENT_SAMPLE_SIZE` | `biology` | `insufficient_sample_size` | `tools/oc133_biology_ncbi_batch_factory.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-SOURCE_SEPARATION_FAILURE` | `biology` | `source_separation_failure` | `tools/oc133_biology_ncbi_batch_factory.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-GRAND_SUPPORT_NOT_AUTHORIZED` | `chemistry` | `grand_support_not_authorized` | `tools/oc133_chemistry_pubchem_formula_batch_factory.py` | `BLOCKED_CAPABILITY_MISSING` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-INSUFFICIENT_SAMPLE_SIZE` | `chemistry` | `insufficient_sample_size` | `tools/oc133_chemistry_pubchem_formula_batch_factory.py` | `BLOCKED_CAPABILITY_MISSING` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-SOURCE_SEPARATION_FAILURE` | `chemistry` | `source_separation_failure` | `tools/oc133_chemistry_pubchem_formula_batch_factory.py` | `BLOCKED_CAPABILITY_MISSING` |
| `OC133-GRAND-EVIDENCE-REPAIR-MATHEMATICS-GRAND_SUPPORT_NOT_AUTHORIZED` | `mathematics` | `grand_support_not_authorized` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-MATHEMATICS-INSUFFICIENT_SAMPLE_SIZE` | `mathematics` | `insufficient_sample_size` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-PHYSICS-GRAND_SUPPORT_NOT_AUTHORIZED` | `physics` | `grand_support_not_authorized` | `tools/oc133_physics_chemistry_official_batch_factory.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-PHYSICS-INSUFFICIENT_SAMPLE_SIZE` | `physics` | `insufficient_sample_size` | `tools/oc133_official_readonly_acquisition_runner.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-PHYSICS-SOURCE_SEPARATION_FAILURE` | `physics` | `source_separation_failure` | `tools/oc133_physics_chemistry_official_batch_factory.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-COMPARATOR_OR_RESIDUAL_FAILURE` | `systems` | `comparator_or_residual_failure` | `tools/oc133_systems_wdi_predictive_search_v2_factory.py` | `BLOCKED_CAPABILITY_MISSING` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-GRAND_SUPPORT_NOT_AUTHORIZED` | `systems` | `grand_support_not_authorized` | `tools/oc133_systems_wdi_predictive_search_v2_factory.py` | `BLOCKED_CAPABILITY_MISSING` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-INSUFFICIENT_SAMPLE_SIZE` | `systems` | `insufficient_sample_size` | `tools/oc133_official_readonly_acquisition_runner.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-NEGATIVE_CONTROL_FAILURE` | `systems` | `negative_control_failure` | `tools/oc133_systems_wdi_predictive_search_v2_factory.py` | `BLOCKED_CAPABILITY_MISSING` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-SOURCE_SEPARATION_FAILURE` | `systems` | `source_separation_failure` | `tools/oc133_official_readonly_acquisition_runner.py` | `ROUTED_TO_AVAILABLE_CAPABILITY` |
