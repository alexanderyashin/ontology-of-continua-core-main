# Logion Service Cockpit

- service total: `8`
- route total: `6`
- registry hash: `fdf936ebe6a54bba52ae1c0ea6ff508ae6692dc28cad37b70f3740bd451353a1`
- router hash: `01862ba38f363d50aad0c03ced1f8477d79fc8634155b0b2f9e891af948039ba`

## Services

- `strategy_hq`: Own portfolio priorities, resource policy, service activation, and cross-service arbitration.
- `incident_management`: Classify incidents, freeze unsafe downstream actions, assign service-owned work orders, and record RCA/postmortem.
- `research_science`: Develop OC model content, theorem obligations, proof/data artifacts, prediction lanes, novelty comparisons, and claim boundaries.
- `editorial_manuscript`: Project approved science into monographs, articles, guides, response maps, and journal-owner-review packets.
- `verification_review`: Run deterministic checks, Cerberus roles, evidence audits, owner-review audits, and closure verification.
- `release_engineering`: Build deterministic package outputs, manage release versioning, enforce development/verification/release space boundaries, and keep checks delta-stable.
- `publication_records`: Execute GitHub and Zenodo publication/replacement only after approval, exact file set, and postflight gates.
- `safety_governance`: Enforce approval scope, secret/local-path scans, journal/SWH/email locks, and private/public boundaries.

## Routes

- `bad_public_release_record` -> `incident_management`; downstream: release_engineering, editorial_manuscript, verification_review, publication_records
- `science_content_gap` -> `research_science`; downstream: verification_review, editorial_manuscript
- `manuscript_projection_gap` -> `editorial_manuscript`; downstream: research_science, verification_review, release_engineering
- `public_payload_or_metadata_gap` -> `release_engineering`; downstream: editorial_manuscript, safety_governance, verification_review
- `github_zenodo_execution_gap` -> `publication_records`; downstream: release_engineering, safety_governance, verification_review
- `approval_scope_or_secret_gap` -> `safety_governance`; downstream: release_engineering, publication_records
