# Logion Release Space Cockpit

- release: `oc_core_1_3_3` v`1.3.3`
- state: `PASS`
- failures: `0`
- release-space paths: `38`
- control-language hits: `0`
- root manifest public: `true`
- root Zenodo metadata: `true`

## Spaces

- `development`: Mutable science and engineering workbench.
- `verification`: Evidence, review, gates, incident control, scorecards, and approval contracts.
- `release`: Public-facing scientific artifacts and metadata only.

## Migrations

- `development_to_verification` `development` -> `verification` owner=`Research/ManuscriptIntegration + IT/ReleaseAutomation`
- `verification_to_release` `verification` -> `release` owner=`Publication/PublicRecords + IT/ReleaseAutomation`
- `release_to_public_records` `release` -> `GitHub + Zenodo` owner=`Publication/PublicRecords`
