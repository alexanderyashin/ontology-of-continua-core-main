# Reviewer Route

## For a 30-minute review
Read README.md, RELEASE_NOTES.md, CLAIMS.md, and releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md.

## For a 2-hour review
Add REVIEWER_ROUTE.md, REPRODUCIBILITY.md, DATA_MANIFEST.md, SIMULATIONS.md, and the public research packet audit.

## For a technical audit
Run `python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode pre_publish`, inspect manifest.json, checksums.txt, release-integrity-report.json, and verify the ZIP.

## Primary claims
Primary claims remain in claims/CLAIM_LEDGER_FULL.json. Research packets do not promote new canonical claims.

## Evidence map
Use claims/CLAIM_EVIDENCE_MATRIX.md and releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json.

## Reproducibility
Run RUN_ALL.md and simulations/run_all.py where a Python environment is available.

## Citation and metadata
Check CITATION.cff, .zenodo.json, .codemeta.json, and ro-crate-metadata.jsonld.

## Known limitations
v1.3.2 is prepared for owner review only. Publication is locked until owner approval.

## How to report issues
Open a GitHub issue or use the owner review route. Do not treat the no-send package as an externally published release.
