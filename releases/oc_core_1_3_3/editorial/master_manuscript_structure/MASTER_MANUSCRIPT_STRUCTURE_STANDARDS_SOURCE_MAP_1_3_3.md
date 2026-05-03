# OC Core 1.3.3 Manuscript Structure Standards Source Map

Status: ACTIVE_STRUCTURE_STANDARD_SOURCE_MAP
Version: 1.3.3
Artifact hash: `7a520a92734e6fb6311bea5af0cccb980020486c9301686f64861d93fa0b7f22`

Structure-standard source map only. It records the standards used by L02-L10 companions; it is not manuscript prose.

## Sources

- NATURE_REPORTING_REPRODUCIBILITY: reporting, reproducibility, data, code, material, and protocol availability are planned before manuscript prose (https://www.nature.com/ncomms/editorial-policies/reporting-standards)
- ICMJE_RECOMMENDATIONS: authorship, contribution, accountability, manuscript preparation, and publication responsibility are explicit (https://www.icmje.org/recommendations/)
- TOP_GUIDELINES: transparency, openness, preregisterable claims, data/code/material availability, and analytic reproducibility are structurally represented (https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/)
- LOGION_TOE_GRADE_POSITIVE_GATE: the structure must positively plan claim, model, proof, evidence, falsifier, limits, reviewer response, reproducibility, and synthesis routes (internal://logion/scientific-editorial-standard)

## Requirements

- NATURE_REPORTING_REQUIREMENTS [NATURE_REPORTING_REPRODUCIBILITY / Reporting requirements]: Plan transparent reporting and reproducibility obligations before manuscript prose is drafted. (https://www.nature.com/ncomms/editorial-policies/reporting-standards)
- NATURE_DATA_AVAILABILITY [NATURE_REPORTING_REPRODUCIBILITY / Availability of data]: Plan a data availability route that exposes the minimum dataset needed to interpret, verify, and extend claims. (https://www.nature.com/ncomms/editorial-policies/reporting-standards)
- NATURE_CODE_ALGORITHM_AVAILABILITY [NATURE_REPORTING_REPRODUCIBILITY / Availability and peer review of computer code and algorithm]: Plan code, algorithm, and replay availability for computational results central to claims. (https://www.nature.com/ncomms/editorial-policies/reporting-standards)
- NATURE_PROTOCOLS_MATERIALS [NATURE_REPORTING_REPRODUCIBILITY / Availability of materials / Experimental protocols]: Plan material, protocol, source, and artifact traceability where results require them. (https://www.nature.com/ncomms/editorial-policies/reporting-standards)
- ICMJE_AUTHOR_CONTRIBUTOR_ACCOUNTABILITY [ICMJE_RECOMMENDATIONS / II.A Defining the Role of Authors and Contributors]: Plan authorship, instrument, method, contribution, and accountability statements explicitly. (https://www.icmje.org/recommendations/)
- ICMJE_MANUSCRIPT_PREPARATION [ICMJE_RECOMMENDATIONS / IV.A Preparing a Manuscript for Submission to a Medical Journal]: Plan manuscript sections so a reviewer can find purpose, method, results/evidence, limits, references, and disclosures. (https://www.icmje.org/recommendations/)
- ICMJE_AI_USE_BOUNDARY [ICMJE_RECOMMENDATIONS / V. Use of Artificial Intelligence in Publishing]: Plan explicit AI assistance boundaries and keep responsibility with accountable humans. (https://www.icmje.org/recommendations/)
- ICMJE_VERSION_CORRECTION_RESPONSIBILITY [ICMJE_RECOMMENDATIONS / III.A Corrections and Version Control]: Plan version, correction, and incident lessons as part of publication governance. (https://www.icmje.org/recommendations/)
- TOP_TRANSPARENCY_POLICY_SET [TOP_GUIDELINES / 8 policy recommendations / Disclosure, Requirement, Verification]: Plan transparency criteria at verification level, not merely disclosure level. (https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/)
- TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION [TOP_GUIDELINES / TOP modular standards]: Plan citation, data, code, materials, design/analysis, preregistration, analysis-plan, and replication/replay slots. (https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/)
- LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE [LOGION_TOE_GRADE_POSITIVE_GATE / Internal TOE-grade positive gate]: Every TOE-relevant theme must have a planned path through claim, model, proof, evidence, falsifier, limits, and synthesis. (internal://logion/scientific-editorial-standard)
- LOGION_CORPUS_COMPLETENESS_AND_FILL_HOOKS [LOGION_TOE_GRADE_POSITIVE_GATE / Internal corpus and fill-control gate]: Every terminal branch must expose later fill-control hooks and corpus-coverage obligations without assessing fill in this phase. (internal://logion/scientific-editorial-standard)

## Positive Criteria

- CRITERION_REPRODUCIBILITY_ARCHITECTURE: The structure must reserve explicit reporting, reproducibility, replay, and verification architecture. (sources: NATURE_REPORTING_REQUIREMENTS, TOP_TRANSPARENCY_POLICY_SET)
- CRITERION_DATA_EVIDENCE_AVAILABILITY: The structure must reserve data/evidence availability and minimum-evidence interpretation routes. (sources: NATURE_DATA_AVAILABILITY, TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION)
- CRITERION_CODE_ALGORITHM_REPLAY: The structure must reserve code, algorithm, finite-model, simulation, and replay obligations. (sources: NATURE_CODE_ALGORITHM_AVAILABILITY, TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION)
- CRITERION_PROTOCOL_MATERIAL_TRACEABILITY: The structure must reserve protocol, source, artifact, and corpus traceability. (sources: NATURE_PROTOCOLS_MATERIALS, LOGION_CORPUS_COMPLETENESS_AND_FILL_HOOKS)
- CRITERION_AUTHOR_INSTRUMENT_METHOD_ACCOUNTABILITY: The structure must distinguish author, instrument, method, contribution, and accountability. (sources: ICMJE_AUTHOR_CONTRIBUTOR_ACCOUNTABILITY, ICMJE_AI_USE_BOUNDARY)
- CRITERION_MANUSCRIPT_READER_NAVIGATION: The structure must make the reader path and manuscript preparation logic explicit. (sources: ICMJE_MANUSCRIPT_PREPARATION, NATURE_REPORTING_REQUIREMENTS)
- CRITERION_CLAIM_TRACEABILITY: The structure must route every promoted claim through model, proof/data evidence, boundary, and synthesis. (sources: LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE, TOP_TRANSPARENCY_POLICY_SET)
- CRITERION_FALSIFICATION_NEGATIVE_CONTROL: The structure must reserve falsifier, negative control, counterexample, demotion, and failure-mode slots. (sources: LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE, TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION)
- CRITERION_PRIOR_ART_NOVELTY_POSITIONING: The structure must reserve prior-art, comparator, novelty, non-equivalence, and residual-delta positioning. (sources: ICMJE_MANUSCRIPT_PREPARATION, LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE)
- CRITERION_VERSION_INCIDENT_RELEASE_GOVERNANCE: The structure must reserve version, correction, incident, known-error, citation, and external-use governance. (sources: ICMJE_VERSION_CORRECTION_RESPONSIBILITY, LOGION_CORPUS_COMPLETENESS_AND_FILL_HOOKS)
