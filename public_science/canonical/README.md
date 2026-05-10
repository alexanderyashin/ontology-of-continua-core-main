# Canonical Scientific Graph

This directory is the public, science-only verification surface for the canonical scientific graph.
Current source edition: OC Core 1.3.3.
It exposes graph-shaped scientific artifacts, not private project machinery.

## Verify

```bash
python tools/build_canonical_scientific_graph.py --verify-only
```

The verifier checks LF-normalized source artifact hashes, graph status, gate status, theorem/proof/Lean/evidence connectivity, and absence of private workspace path leaks.

## Graphs

- Theorem graph: `public_science/canonical/THEOREM_GRAPH.json`
- Proof graph: `public_science/canonical/PROOF_GRAPH.json`
- Evidence graph: `public_science/canonical/EVIDENCE_GRAPH.json`
- Manifest: `public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_MANIFEST.json`
- Reviewer glossary: `public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_GLOSSARY.md`
- Internal-to-public graph mapping: `public_science/canonical/INTERNAL_TO_PUBLIC_GRAPH_MAPPING.json`

## Closure Counts

- Theorems: 11
- Scientific-promotion theorem rows: 11
- Lean theorem refs: 18 missing 0
- Finite-model cases: 151 failures 0
- Selected empirical evidence packs: 4 across 4 domains
- Science SPOT closure verdict: PASS
- Hostile-review blockers: 0

## Boundary

This is a public scientific graph. Publication/release-review authorization is a separate gate.
