from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MATERIALIZER = Path(__file__).with_name("oc133_ncbi_taxonomy_lca_materializer.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay the OC133 NCBI Taxonomy LCA scorer.")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [sys.executable, str(MATERIALIZER), "--check" if args.check else "--score"]
    if not args.check:
        command.append("--write-scoring")
    return int(subprocess.run(command).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
