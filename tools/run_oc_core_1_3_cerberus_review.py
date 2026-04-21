from __future__ import annotations

import argparse
import sys

from oc_core_1_3_cerberus_lib import REPO_ROOT, run_cerberus_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OC Core 1.3 Cerberus release-review swarm.")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip the mandatory Codex LLM panel. Useful only for deterministic dry runs while bootstrapping Cerberus.",
    )
    parser.add_argument(
        "--codex-binary",
        default="codex",
        help="Codex CLI binary to use for the mandatory LLM panel.",
    )
    parser.add_argument(
        "--codex-model",
        default="gpt-5.4-mini",
        help="Codex model to use for the mandatory LLM panel.",
    )
    parser.add_argument(
        "--llm-scope",
        choices=["full", "latest-findings", "refs"],
        default="full",
        help=(
            "LLM review scope. `full` is the only release-acceptance gate; "
            "`latest-findings` and `refs` are accelerated remediation loops."
        ),
    )
    parser.add_argument(
        "--llm-artifact-ref",
        action="append",
        default=[],
        help="Artifact ref to review when --llm-scope=refs. May be repeated.",
    )
    parser.add_argument(
        "--llm-workers",
        type=int,
        default=4,
        help="Maximum parallel Codex LLM review calls. The full gate remains mandatory; this only reduces wall time.",
    )
    parser.add_argument(
        "--llm-batch-max-chars",
        type=int,
        default=3200,
        help=(
            "Approximate maximum source-text budget per LLM batch. Smaller batches improve parallel remediation speed; "
            "the final full gate may raise this if a broader-context pass is desired."
        ),
    )
    parser.add_argument(
        "--build-mode",
        choices=["full", "skip"],
        default="full",
        help=(
            "Build policy for this run. `full` is required for release acceptance; "
            "`skip` is a fast, non-accepting remediation mode that still runs science and textual reviewers."
        ),
    )
    args = parser.parse_args()

    result = run_cerberus_review(
        REPO_ROOT,
        skip_llm=args.skip_llm,
        codex_binary=args.codex_binary,
        codex_model=args.codex_model,
        llm_scope=args.llm_scope,
        llm_artifact_refs=set(args.llm_artifact_ref),
        llm_workers=args.llm_workers,
        llm_batch_max_chars=args.llm_batch_max_chars,
        build_mode=args.build_mode,
    )
    acceptance = result["acceptance"]
    run_id = result["run_id"]
    print(f"Cerberus run id: {run_id}")
    print(f"Run directory: {result['run_dir']}")
    print(f"Acceptance status: {acceptance['status']}")
    print(f"LLM gate status: {acceptance['llm_gate_status']}")
    print(f"Open defect findings: {acceptance['open_findings_total']}")
    print(f"Duration seconds: {result['run']['summary'].get('duration_seconds', 'UNKNOWN')}")
    if acceptance["status"] != "PASS":
        print("Cerberus did not accept the release package.", file=sys.stderr)
        return 1
    print("Cerberus accepted the release package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
