# OC Core v1.3.2 Release Notes

## Release identity
- Version: 1.3.2
- DOI: TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED
- Previous canonical DOI: 10.5281/zenodo.19741958
- Concept DOI: 10.5281/zenodo.17899134
- GitHub tag: v1.3.2 prepared, not created
- Zenodo record: 19741958 is the previous canonical record; v1.3.2 requires owner-approved new version
- Date: 2026-04-28
- Status: RELEASE_READY_NO_SEND

## What changed since v1.3.1
OC Core v1.3.2 is a release-quality and reviewer-route release candidate. It tightens public metadata, claim support boundaries, reproducibility surfaces, research packet routing, and release governance.

## Fixed release-quality issues
The release now carries explicit no-send owner approval, deterministic package integrity, public boundary checks, DOI lineage, and release-machine gates.

## Metadata improvements
- CITATION.cff records version 1.3.2 and the pending DOI policy.
- RO-Crate describes the release bundle and bounded research packet evidence.
- CodeMeta records the repository, license, language, and version.
- Zenodo metadata targets a new version under the existing concept DOI.
- SWHID is an owner action unless an existing resolvable identifier is supplied.

## Reproducibility package
The bundle includes simulation reports, dataset manifests, checksums, and reproducibility instructions. Simulations remain illustration and replay checks, not empirical validation.

## Reviewer route
Use REVIEWER_ROUTE.md for 30-minute, 2-hour, and technical-audit reading paths.

## Known limitations
The v1.3.2 DOI is pending until owner-approved Zenodo publication. Research packets are support/frontier material and do not widen canonical claims.

## Superseded records and version lineage
v1.3.2 is prepared as a new version in the concept DOI chain 10.5281/zenodo.17899134; the existing record 10.5281/zenodo.19741958 remains the previous canonical public record until publication.

## How to cite
Before publication, cite the current canonical Zenodo record and mention that v1.3.2 is a no-send release candidate. After owner-approved publication, use the DOI assigned by Zenodo for v1.3.2.

## Integrity verification
Verify manifest.json, checksums.txt, release-integrity-report.json, and the SHA256 entry for releases/oc_core_1_3_2/artifacts/oc_core_1_3_2_zenodo_release.zip.
