# Logion Incident Control Cockpit

- authority: `Strategy HQ / K6`
- incidents: `1`
- P0 incidents: `1`
- active incidents: `1`
- manual repair allowed: `false`
- queue hash: `6dddefb227dff0399e0ed455817b6b3f9adf9a36acd8477e8f71040ab1206fe8`

## Active Queue

- `INC_OC133_PUBLIC_RELEASE_MONOGRAPH_SURROGATE_20260501` severity=`P0` signal=`bad_public_release_record` state=`CLOSED_READY_FOR_PUBLIC_REPLACEMENT` next=`controlled_public_replacement`

## Routing Rules

- `bad_public_release_record` -> `P0` `StrategyHQ/IncidentCommand`
- `service_boundary_confusion` -> `P1` `ServiceArchitecture/Router`
- `function_product_confusion` -> `P1` `ServiceArchitecture/Router`
- `science_to_manuscript_projection_gap` -> `P1` `Research/ManuscriptIntegration`
- `public_payload_role_semantics_gap` -> `P1` `IT/ReleaseAutomation`
- `approval_scope_contract_conflict` -> `P1` `IT/ReleaseAutomation`
- `source_certificate_binding_drift` -> `P1` `IT/ReleaseAutomation`
- `background_science_evidence_gap` -> `P2` `Research/EmpiricalScience`
- `self_dirtying_verification` -> `P3` `IT/ReleaseAutomation`
