# Public Release Dossier: OC Core v1.3.2

## Final verdict
`RELEASE_READY_NO_SEND`; publish_allowed=`false`; owner_approval_required=`true`.

## Release identity
- Version: 1.3.2
- DOI: TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED
- Previous canonical DOI: 10.5281/zenodo.19741958
- Concept DOI: 10.5281/zenodo.17899134
- GitHub tag: v1.3.2 prepared, not created

## Artifact inventory
- Artifacts: 378
- Research packets audited: 46

## Metadata status
- CITATION.cff, CodeMeta, Zenodo metadata, and RO-Crate pass local validation.
- Software Heritage: `owner_action_required`.

## Citation status
CITATION.cff records the pending v1.3.2 DOI policy and existing DOI lineage.

## Archival status
No external archive action has been performed. SWHID is owner-action gated unless already present.

## Reproducibility status
Simulation and data routes pass as bounded replay/support surfaces.

## Integrity status
manifest.json, checksums.txt, release-integrity-report.json, and the ZIP integrity gate pass.

## Boundary/leak status
No blocking public leak findings remain.

## Known limitations
The package is no-send and cannot be treated as externally published until owner approval and publication.

## Owner approval checklist
- Review this dossier.
- Confirm the artifact freeze hash in the publish manifest.
- Supply SWHID or owner exception.
- Approve GitHub/Zenodo/Software Heritage channels explicitly.

## Publication instructions
- GitHub release: create tag and draft release only after owner approval.
- Zenodo new version: use the existing concept DOI chain.
- Software Heritage: verify or create SWHID manually.
- DOI propagation: run postflight after publication.

## Post-release verification checklist
Run `python -m release_machine postflight --release oc_core_1_3_2 --channel zenodo --public-url <url>` after publication.
