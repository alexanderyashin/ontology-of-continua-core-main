# OC Core 1.3.3 Local Editorial LLM Capability Report

Status: `LOCAL_EDITORIAL_CAPABILITY_BOUNDARY_IDENTIFIED`

## Safe Execution Result

- The governed r009 editorial queue processed `38/38` packets through the common Logion LLM service.
- The writer/checker workbench processed the full L10 reader-facing surface twice.
- `write_check_v2_timeout_fixed`: writer `32/32`, checker `32/32`, actual governed invocations `64`, unmanaged Ollama calls `0`.
- `write_check_v3_strict_extractive`: writer `32/32`, checker `32/32`, actual governed invocations `64`, unmanaged Ollama calls `0`.
- Host safety remained within safe bands during the observed runs; no direct unmanaged Ollama path was used.

## Quality Boundary

- Standard writer profile: average checker score `62.19/100`, minimum `5`, blocker total `54`, low-score rows `23`.
- Strict extractive writer profile: average checker score `68.19/100`, minimum `5`, blocker total `52`, low-score rows `19`.
- The strict profile improved safety slightly but did not remove the main blocker classes.

## Main Blocker Classes

- Candidate rewrites can lose formal, evidence, or figure anchors.
- Candidate rewrites can introduce unsupported or fabricated technical claims.
- Candidate rewrites can confuse internal vocabulary, public vocabulary, and source-level anchors.
- Some packets are too dense for the local model to rewrite into finished publication prose without stronger source segmentation.

## Operational Conclusion

The local Ollama stack is now useful as a governed lower-level editorial service: packet inspection, draft proposals, checker scoring, blocker extraction, source-gap detection, and regression-class discovery. It is not yet safe as an autonomous final prose author for the master scientific monograph. The next release-quality loop should use these findings to create deterministic source-gap tasks, smaller source-grounded rewrite packets, and promotion gates that require zero blocker rows before any generated prose can enter a reader-facing PDF.
