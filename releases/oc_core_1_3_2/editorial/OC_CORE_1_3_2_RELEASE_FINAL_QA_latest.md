# OC Core 1.3.2 Release Final QA

- status: `PASS`
- release_id: `oc_core_1_3_2`
- release_machine_state: `RELEASE_READY_NO_SEND`
- master_verdict: `PASS`
- release_focus_status: `READY_FOR_OWNER_REVIEW_NO_SEND`
- next_24h_compute_policy: `RELEASE_FIRST_NO_LONG_RESEARCH`
- publication_allowed: `false`
- owner_approval_required: `true`
- substantive_pdf_total: `6`
- research_packet_total: `101`
- night_delta_work_order_total: `8`
- package_zip_present: `true`
- package_integrity_ref: `releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json`
- package_hash_policy: `recorded in the release-machine ZIP integrity surface after package build to avoid final-QA self-reference drift`
- next_lawful_action: `OWNER_REVIEW_NO_SEND_RELEASE_PACKET`

## Checks

- `PASS` `VERSION_IS_1_3_2` observed=`1.3.2`
- `PASS` `ZENODO_VERSION_IS_1_3_2` observed=`1.3.2`
- `PASS` `LRGEF_RELEASE_READY_NO_SEND` observed=`RELEASE_READY_NO_SEND`
- `PASS` `SUBSTANTIVE_PDFS` observed=`6`
- `PASS` `NIGHT_DELTA_PACKET_MERGED` observed=`8`
- `PASS` `PARFIT_CURRENT_AND_FORWARD_PASS` observed=`PASS`
- `PASS` `NO_SEND_LOCK` observed=`{'lrgef_publish_allowed': False, 'release_publish_allowed': False}`
- `PASS` `PACKAGE_ZIP_PRESENT` observed=`True`
- `PASS` `NIGHT_PACKET_LEAK_SCAN` observed=`0`

## External Publication Blockers

- `cosign`
- `syft`
- `slsa-verifier`
- `OWNER_APPROVAL_REQUIRED`
- `ZENODO_DOI_PENDING_UNTIL_PUBLICATION`

## No-Send Boundary

- `no_publication`: `true`
- `no_public_push`: `true`
- `no_zenodo`: `true`
- `no_doi_minting`: `true`
- `no_email_or_outbound`: `true`
- `canonical_promotion_allowed`: `false`
