# OC Core Terminal Text Generation Rules

Status: `OC_CORE_ARTIFACT_GENERATION_RULES_READY`
Artifact hash: `2ece72a7f709e8bf54894970198c40341ec4e7f767799c645745b0a68298b1cf`

## Terminal Contract Fields

- `aggregator_node_id`
- `target_node_id`
- `reader_task`
- `argument_role`
- `claim_boundary`
- `source_refs`
- `source_hashes`
- `transformation_rule`
- `transition_in`
- `transition_out`
- `quality_scorer_hooks`

## Role Contracts

### `definition_model`
- paragraph_purpose: define the local object, vocabulary, or reader task before claims are promoted
- required_source_use: use source bindings as explanatory support, not as a raw inventory
- claim_boundary: may introduce terms and scope; may not promote empirical or universal strength

### `proof_evidence`
- paragraph_purpose: bind the local claim to proof, evidence, replay, example, or source support
- required_source_use: name the support route in prose and keep exact paths in the source trace
- claim_boundary: may promote only the exact bounded claim supported by the named route

### `limits_falsifier`
- paragraph_purpose: state limits, falsifiers, negative controls, or reopening conditions
- required_source_use: turn reviewer and failure-mode sources into explicit scientific boundaries
- claim_boundary: must prevent unsupported TOE, all-domain, or superiority inflation

### `synthesis_transition`
- paragraph_purpose: synthesize the local route and hand the reader to the next obligation
- required_source_use: summarize only established local support and state the next reading move
- claim_boundary: may connect results; may not add new unsupported claims
