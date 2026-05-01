# OC Core 1.3.3 Grand Evidence Registry Sync

Verdict: `REGISTRY_SYNC_BLOCKED_PENDING_VALID_PACKS`
Candidate packs: `16`
Valid candidates: `0`
New valid refs registered: `0`
Blocked domains after sync: `5`
Open repair work orders: `18`
No-send: `True`

The sync factory only registers evidence packs already accepted by the strict grand empirical validator. It never edits packs or upgrades grand_toe_support_allowed.

## Failure Classes

- `comparator_or_residual_failure`: `7`
- `grand_support_not_authorized`: `16`
- `insufficient_sample_size`: `10`
- `negative_control_failure`: `40`
- `source_separation_failure`: `25`

## Repair Work Orders

| Work Order | Domain | Failure Class | Owner | Candidate Refs |
| --- | --- | --- | --- | --- |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-COMPARATOR_OR_RESIDUAL_FAILURE` | `biology` | `comparator_or_residual_failure` | `Research/EmpiricalScience` | `validation/heldout/acquisition_plans/biology_systems/biology_candidate_pack_template.json`, `validation/heldout/grand_science/biology/ncbi_batch/OC133_BIOLOGY_NCBI_BATCH_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology/ncbi_benchmark/OC133_BIOLOGY_NCBI_BENCHMARK_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology_systems/biology_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-GRAND_SUPPORT_NOT_AUTHORIZED` | `biology` | `grand_support_not_authorized` | `Review/ClaimBoundary` | `validation/heldout/acquisition_plans/biology_systems/biology_candidate_pack_template.json`, `validation/heldout/grand_science/biology/ncbi_batch/OC133_BIOLOGY_NCBI_BATCH_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology/ncbi_benchmark/OC133_BIOLOGY_NCBI_BENCHMARK_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology_systems/biology_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-INSUFFICIENT_SAMPLE_SIZE` | `biology` | `insufficient_sample_size` | `Research/EmpiricalScience` | `validation/heldout/acquisition_plans/biology_systems/biology_candidate_pack_template.json`, `validation/heldout/grand_science/biology/ncbi_benchmark/OC133_BIOLOGY_NCBI_BENCHMARK_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology_systems/biology_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-BIOLOGY-SOURCE_SEPARATION_FAILURE` | `biology` | `source_separation_failure` | `Research/EmpiricalScience` | `validation/heldout/acquisition_plans/biology_systems/biology_candidate_pack_template.json`, `validation/heldout/grand_science/biology/ncbi_batch/OC133_BIOLOGY_NCBI_BATCH_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology/ncbi_benchmark/OC133_BIOLOGY_NCBI_BENCHMARK_CANDIDATE_PACK.json`, `validation/heldout/grand_science/biology_systems/biology_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-COMPARATOR_OR_RESIDUAL_FAILURE` | `chemistry` | `comparator_or_residual_failure` | `Research/EmpiricalScience` | `validation/heldout/grand_science/chemistry/pubchem_formula_batch/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_CANDIDATE_PACK.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-GRAND_SUPPORT_NOT_AUTHORIZED` | `chemistry` | `grand_support_not_authorized` | `Review/ClaimBoundary` | `validation/heldout/grand_science/chemistry/pubchem_formula_batch/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_CANDIDATE_PACK.json`, `validation/heldout/grand_science/physics_chemistry/chemistry_candidate_evidence_pack.json`, `validation/heldout/grand_science/physics_chemistry/official_batch/chemistry_official_batch_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-INSUFFICIENT_SAMPLE_SIZE` | `chemistry` | `insufficient_sample_size` | `Research/EmpiricalScience` | `validation/heldout/grand_science/physics_chemistry/chemistry_candidate_evidence_pack.json`, `validation/heldout/grand_science/physics_chemistry/official_batch/chemistry_official_batch_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-CHEMISTRY-SOURCE_SEPARATION_FAILURE` | `chemistry` | `source_separation_failure` | `Research/EmpiricalScience` | `validation/heldout/grand_science/chemistry/pubchem_formula_batch/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_CANDIDATE_PACK.json`, `validation/heldout/grand_science/physics_chemistry/official_batch/chemistry_official_batch_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-MATHEMATICS-GRAND_SUPPORT_NOT_AUTHORIZED` | `mathematics` | `grand_support_not_authorized` | `Review/ClaimBoundary` | `validation/heldout/grand_science/mathematics/mathematics_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-MATHEMATICS-INSUFFICIENT_SAMPLE_SIZE` | `mathematics` | `insufficient_sample_size` | `Research/EmpiricalScience` | `validation/heldout/grand_science/mathematics/mathematics_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-PHYSICS-GRAND_SUPPORT_NOT_AUTHORIZED` | `physics` | `grand_support_not_authorized` | `Review/ClaimBoundary` | `validation/heldout/grand_science/physics_chemistry/official_batch/physics_official_batch_candidate_evidence_pack.json`, `validation/heldout/grand_science/physics_chemistry/physics_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-PHYSICS-INSUFFICIENT_SAMPLE_SIZE` | `physics` | `insufficient_sample_size` | `Research/EmpiricalScience` | `validation/heldout/grand_science/physics_chemistry/physics_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-PHYSICS-SOURCE_SEPARATION_FAILURE` | `physics` | `source_separation_failure` | `Research/EmpiricalScience` | `validation/heldout/grand_science/physics_chemistry/official_batch/physics_official_batch_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-COMPARATOR_OR_RESIDUAL_FAILURE` | `systems` | `comparator_or_residual_failure` | `Research/EmpiricalScience` | `validation/heldout/acquisition_plans/biology_systems/systems_candidate_pack_template.json`, `validation/heldout/grand_science/biology_systems/systems_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-GRAND_SUPPORT_NOT_AUTHORIZED` | `systems` | `grand_support_not_authorized` | `Review/ClaimBoundary` | `validation/heldout/acquisition_plans/biology_systems/systems_candidate_pack_template.json`, `validation/heldout/grand_science/biology_systems/systems_candidate_evidence_pack.json`, `validation/heldout/grand_science/systems/harvested/systems_candidate_evidence_pack.json`, `validation/heldout/grand_science/systems/wdi_benchmark/systems_wdi_benchmark_candidate_evidence_pack.json`, `validation/heldout/grand_science/systems/wdi_model_search/OC133_SYSTEMS_WDI_MODEL_SEARCH_CANDIDATE_PACK.json`, `validation/heldout/grand_science/systems/wdi_predictive_search_v2/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_CANDIDATE_PACK.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-INSUFFICIENT_SAMPLE_SIZE` | `systems` | `insufficient_sample_size` | `Research/EmpiricalScience` | `validation/heldout/acquisition_plans/biology_systems/systems_candidate_pack_template.json`, `validation/heldout/grand_science/biology_systems/systems_candidate_evidence_pack.json`, `validation/heldout/grand_science/systems/wdi_benchmark/systems_wdi_benchmark_candidate_evidence_pack.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-NEGATIVE_CONTROL_FAILURE` | `systems` | `negative_control_failure` | `Review/ClaimBoundary` | `validation/heldout/grand_science/systems/harvested/systems_candidate_evidence_pack.json`, `validation/heldout/grand_science/systems/wdi_model_search/OC133_SYSTEMS_WDI_MODEL_SEARCH_CANDIDATE_PACK.json` |
| `OC133-GRAND-EVIDENCE-REPAIR-SYSTEMS-SOURCE_SEPARATION_FAILURE` | `systems` | `source_separation_failure` | `Research/EmpiricalScience` | `validation/heldout/acquisition_plans/biology_systems/systems_candidate_pack_template.json`, `validation/heldout/grand_science/biology_systems/systems_candidate_evidence_pack.json`, `validation/heldout/grand_science/systems/wdi_benchmark/systems_wdi_benchmark_candidate_evidence_pack.json` |
