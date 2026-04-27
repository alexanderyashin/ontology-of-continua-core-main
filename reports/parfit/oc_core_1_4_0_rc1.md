# Parfitian Cerberus Audit: oc_core_1_4_0_rc1

Status: `FAIL_BLOCKING`
Release-ready no-send allowed: `false`
High+ findings: `1`
Blockers: `0`

## No-Send Invariant
Publication, Zenodo, DOI minting, GitHub push and outbound sending remain `false` unless a separate owner/governance unlock exists.

## Findings
### candidate_bundle_missing_candidate_bundle_970647
- Pass: `candidate_bundle`
- Category: `missing_candidate_bundle`
- Severity: `high`
- Blocking: `true`
- Summary: The release candidate lacks the artifacts or claim inputs required for blocking Parfitian release review.
- Affected refs: releases/oc_core_1_4_0_rc1/artifacts
- Required fixes: Materialize a complete candidate bundle before claiming release-ready no-send.
