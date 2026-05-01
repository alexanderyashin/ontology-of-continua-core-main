# Grand Science Heldout Evidence

This directory is reserved for prospective or target-blind evidence packs for the grand empirical gate.

The registry intentionally starts empty. Existing OC133 target-blind reconstruction rows are imported by the gate as bounded baseline evidence only; they do not allow broad domain validation or grand TOE support.

`validation/grand_science/run_grand_empirical_gate.py` now runs the evidence-pack factory before scoring. It reads `benchmarks/grand_science/domain_requirements.json`, scans the configured candidate roots, validates any candidate pack against the strict source-separation/N/residual/comparator/uncertainty/negative-control/falsifier contract, and writes:

- `validation/heldout/OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json`
- `validation/heldout/OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json`
- `reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json`

The sample pack under `validation/heldout/samples/` is deliberately excluded from discovery and keeps `grand_toe_support_allowed=false`; it is a shape example, not evidence and not a registry candidate.
