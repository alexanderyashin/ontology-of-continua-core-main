# OC Core 1.3.2 Release Scorecard

Release state: `REMEDIATION_REQUIRED`
Finding total: `1`
Publish allowed: `false`

| Gate | State | Severity | Summary |
| --- | --- | --- | --- |
| `G00` release_identity | `PASS` | `CRITICAL` | Release id, version file, and release directory checked. |
| `G01` source_tree_cleanliness | `PASS` | `INFO` | Worktree dirt is allowed during local no-send preparation only when generated release files are explicit. |
| `G02` version_consistency | `PASS` | `HIGH` | Version fields checked across manifest, publish manifest, and Zenodo metadata. |
| `G03` doi_consistency | `PASS` | `HIGH` | v1.3.2 DOI remains pending; previous canonical and concept DOI are explicit. |
| `G04` citation_cff | `PASS` | `HIGH` | CITATION.cff parsed by strict field checks. |
| `G05` codemeta | `PASS` | `HIGH` | CodeMeta metadata checked. |
| `G06` zenodo_metadata | `PASS` | `HIGH` | Zenodo metadata targets a new version under the concept DOI. |
| `G07` ro_crate | `PASS` | `HIGH` | RO-Crate JSON-LD structure checked. |
| `G08` software_heritage | `PASS` | `HIGH` | SWHID policy is Existing Only; missing SWHID is recorded as owner action and publish remains locked. |
| `G09` license | `PASS` | `HIGH` | License file checked. |
| `G10` manifest | `PASS` | `HIGH` | Bundle manifest source paths checked. |
| `G11` checksums | `PASS` | `HIGH` | Checksums file checked against manifest sample and control hash. |
| `G12` pdf_integrity | `PASS` | `HIGH` | Primary PDFs are substantive bound PDFs, not placeholder headers. |
| `G13` zip_integrity | `PASS` | `HIGH` | Release ZIP contents checked against manifest. |
| `G14` reproducibility_route | `PASS` | `HIGH` | Simulation and data reproducibility routes checked. |
| `G15` reviewer_route | `PASS` | `HIGH` | Reviewer route sections checked. |
| `G16` contribution_ledger | `PASS` | `HIGH` | Contribution ledger checked. |
| `G17` acknowledgements | `PASS` | `HIGH` | Acknowledgements checked. |
| `G18` boundary_leak_protection | `PASS` | `CRITICAL` | Public text, research packets, and claim ceilings scanned. |
| `G19` readme_completeness | `PASS` | `HIGH` | README release identity and reproducibility markers checked. |
| `G20` release_notes_changelog | `PASS` | `HIGH` | Release notes and changelog checked. |
| `G21` github_release_readiness | `PASS` | `CRITICAL` | GitHub readiness is dry-run only; tag must not exist. |
| `G22` zenodo_upload_readiness | `PASS` | `CRITICAL` | Zenodo package is ready for owner review only; upload remains locked. |
| `G23` post_release_verification | `PASS` | `HIGH` | Post-release verification is not applicable before publication and is recorded. |
| `G24` lrgef_freshness | `PASS` | `INFO` | LRGEF tracks source/view freshness; evaluation rewrites stale views before final verdict. |
| `G25` lrgef_pdf_source_binding | `PASS` | `HIGH` | Every v1.3.2 primary PDF is bound to a substantive source artifact. |
| `G26` lrgef_supply_chain_no_send_lock | `PASS` | `INFO` | Supply-chain/signing gaps are recorded as no-send external publication blockers, not silent PASS for public release. |
| `G27` parfitian_cerberus | `PASS` | `HIGH` | Parfitian Cerberus release-critical gate checked self-defeat, moral mathematics, Relation R, future stakeholders, transparency and evidence burden. |
| `G28` science_terminality_82 | `FAIL` | `CRITICAL` | OC Core 1.3.2 external publication is blocked until all 82 science gaps are terminal. |
