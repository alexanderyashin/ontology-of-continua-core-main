# OC Core 1.3.2 Release Scorecard

Release state: `RELEASE_READY_NO_SEND`
Critical findings: `0`
High findings: `0`
Publish allowed: `false`

| Gate | State | Severity | Summary |
| --- | --- | --- | --- |
| `gate_00_intake` | `PASS` | `INFO` | Release id, version, and release directory checked. |
| `gate_01_channel_policy` | `PASS` | `INFO` | Channel policy files checked. |
| `gate_02_artifact_inventory` | `PASS` | `INFO` | Artifact inventory is present and assembled. |
| `gate_03_build_reproducibility` | `PASS` | `INFO` | Package and simulation report checked. |
| `gate_04_pdf_document_quality` | `PASS` | `INFO` | Primary PDF artifacts are present and have a PDF header. |
| `gate_05_claim_evidence_ceiling` | `PASS` | `INFO` | Full claim ledger and support ceilings checked. |
| `gate_06_strong_statement_linter` | `PASS` | `INFO` | Outward-facing surfaces checked for unsafe public rhetoric. |
| `gate_07_simulation_data_validation` | `PASS` | `INFO` | Simulation assertions and dataset claim ceilings checked. |
| `gate_08_citation_doi_metadata` | `PASS` | `INFO` | DOI metadata uses pending v1.3.2 DOI and historical DOI references. |
| `gate_09_public_surface_parity` | `PASS` | `INFO` | Tracked v1.3.2 public surfaces agree on version, DOI state, and no-send state. |
| `gate_10_security_privacy_secrets` | `PASS` | `INFO` | Release surfaces checked for local paths and obvious secret patterns. |
| `gate_11_ci_release_workflow` | `PASS` | `INFO` | Dry-run, candidate, safe tag, and postflight workflows checked. |
| `gate_12_owner_approval` | `PASS` | `INFO` | Owner approval is required and publish remains locked. |
| `gate_13_publish_preflight` | `PASS` | `INFO` | No v1.3.2 tag is present and no-send publish policy is active. |
| `gate_14_post_release_audit` | `NOT_APPLICABLE` | `INFO` | Postflight is not applicable before publication. |
