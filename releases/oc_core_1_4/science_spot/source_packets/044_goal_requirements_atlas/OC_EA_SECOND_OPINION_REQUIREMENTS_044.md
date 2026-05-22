# OC 044 Enterprise Architecture Second Opinion Requirements

EA Second Opinion readiness means OC can produce a bounded, client-safe architecture second-opinion packet over the recovered EAQ surface.

| id | requirement | status | acceptance criterion | blocker |
| --- | --- | --- | --- | --- |
| EA2O-001 | Complete target customer question atlas | SATISFIED_WITH_ARTIFACTS | The EA target question surface is represented exactly once with tiers, clusters, failure modes, mechanisms, data refs, and readiness. | none |
| EA2O-002 | Behavior classes that matter to the CTO/EA audience | SATISFIED_WITH_ARTIFACTS | Question atlas covers load survivability, hidden dependencies, boundary collapse, retry storms, failover state corruption, observability, migration risk, portfolio priority, governance, AI/automation, and safe standardization. | none |
| EA2O-003 | Data intake, replay, and report packet | SATISFIED_WITH_ARTIFACTS | Second Opinion has required data package, case/replay refs, and a client/report deliverable template. | none |
| EA2O-004 | Close in-progress EAQ chains | FAILED_NEEDS_REPAIR | EAQ_101, EAQ_102, and EAQ_103 must have complete science/client/product/publication chains before full EA2O readiness. | Close 3 in-progress EAQ chains. |
| EA2O-005 | Client-safe and external validation boundary | BLOCKED_BY_EXTERNAL_EVIDENCE | Client-safe claims require external client proof and owner approval beyond internal simulations. | External client evidence and owner gate required. |

## Mandatory Behavior Question Families

- Load survivability and destructive dynamics.
- Hidden dependency blast radius.
- Security/privilege boundary collapse.
- Retry, timeout, queue, and feedback storms.
- Failover availability versus state corruption.
- Observability and telemetry usefulness.
- Migration and transformation readiness risk.
- Portfolio intervention priority.
- Governance and decision-trace bottlenecks.
- AI/automation readiness and safe standardization.
