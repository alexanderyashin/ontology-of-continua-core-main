# OC Core 1.3.3 Science To Text Transformation Rules

Status: ACTIVE_TRANSFORMATION_RULES_NO_TRANSFORMATION_EXECUTED
Artifact hash: `7d599a90a607ce8d534c716aeaf7b62df4fdfc5d660c504af4a58d2ae375592f`

These are rules for later transformation. They do not execute transformation and contain no manuscript prose.

## Rules

- TRANSFORM_DEFINITION_MODEL [definition_model]: Turn definitions, model objects, assumptions, and notation anchors into reader-facing explanatory prose with explicit scope boundaries.
- TRANSFORM_PROOF_EVIDENCE [proof_evidence]: Turn proof/data/simulation evidence into claim-support prose that identifies source, method, result type, and limitation.
- TRANSFORM_LIMITS_FALSIFIER [limits_falsifier]: Turn failures, caveats, negative controls, and demotion rules into explicit limits and falsification prose.
- TRANSFORM_SYNTHESIS_TRANSITION [synthesis_transition]: Turn local results into synthesis and next-step prose that closes the chapter obligation and hands off to the next node.
