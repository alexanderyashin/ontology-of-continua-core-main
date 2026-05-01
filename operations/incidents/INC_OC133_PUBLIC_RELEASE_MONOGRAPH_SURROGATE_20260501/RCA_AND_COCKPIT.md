# INC_OC133_PUBLIC_RELEASE_MONOGRAPH_SURROGATE_20260501

- state: `CLOSED_READY_FOR_PUBLIC_REPLACEMENT`
- release: `oc_core_1_3_3` v`1.3.3`
- master pages: `706`
- monolith audit: `PASS`
- release scorecard: `PASS`
- open work orders: `1`

## Root Causes
- `RC-001` `Publication/ReleaseEngineering`: The public payload builder allowed the MASTER_MONOGRAPH role to be generated from compact Markdown.
- `RC-002` `Research/ManuscriptIntegration`: There was no explicit science-to-manuscript corpus ledger proving all promoted 1.3.3 science surfaces entered the manuscript.
- `RC-003` `IT/ReleaseAutomation`: Presentation gates checked metadata formatting but not role semantics, source provenance, or primary-PDF substance.
- `RC-004` `StrategyHQ/IncidentManagement`: The failed publication path did not auto-open an incident, assign capability work orders, and block replacement until RCA closure.
- `RC-005` `IT/ReleaseAutomation`: The same root metadata files were used as verification/no-outbound controls and as public release artifacts.
- `RC-006` `ServiceArchitecture/Router`: The first repair design treated incident, editorial, research, verification, release, and publication as one case pipeline instead of independent Logion services.

## Work Orders
- `OC133-INC-WO-001` `ServiceArchitecture/Router` `CLOSED`: Define independent Logion services and route the 1.3.3 publication incident through service contracts
- `OC133-INC-WO-002` `Research/ManuscriptIntegration` `CLOSED`: Build OC Core 1.3.3 science monolith from full corpus plus 1.3.3 delta
- `OC133-INC-WO-003` `IT/ReleaseAutomation` `CLOSED`: Prevent surrogate PDFs and control packets from occupying public scientific roles
- `OC133-INC-WO-004` `Review/Cerberus` `CLOSED`: Re-run release gates after monolith integration and reopen any scientific or public-surface blockers
- `OC133-INC-WO-005` `IT/ReleaseAutomation` `CLOSED`: Separate development, verification, and release spaces so public artifacts contain no verification-control vocabulary
- `OC133-INC-WO-006` `Publication/PublicRecords` `PENDING_LOCAL_GATES`: Replace bad GitHub and Zenodo public records only after local incident closure

## Self-Repair Classes
- `SERVICE_ARCHITECTURE_ROUTER` `ServiceArchitecture/Router` -> `tools/logion_service_architecture.py`
- `SOURCE_CERTIFICATE_REBIND` `IT/ReleaseAutomation` -> `tools/materialize_oc_core_1_3_3_v12_closure.py`
- `SCIENCE_TO_MANUSCRIPT_PROJECTION` `Research/ManuscriptIntegration` -> `release_machine.science_monolith`
- `PUBLIC_PAYLOAD_ROLE_SEMANTICS` `IT/ReleaseAutomation` -> `tools/oc133_public_release_payload.py`
- `RELEASE_SPACE_SEPARATION` `IT/ReleaseAutomation` -> `tools/logion_release_spaces.py`
- `FUNCTION_PRODUCT_SEPARATION` `ServiceArchitecture/Router` -> `tools/logion_function_product_separation.py`
- `APPROVAL_MODE_CONTRACT` `IT/ReleaseAutomation` -> `finite-runner approval-mode policy plus personal release audit scope policy`
- `PUBLIC_RECORD_REPLACEMENT` `Publication/PublicRecords` -> `release_machine.publish-replace`
