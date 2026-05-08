from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MATERIALIZER = Path(__file__).with_name("oc133_openfda_pharmacology_materializer.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay the OC133 openFDA pharmacology/toxicology scorer.")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [sys.executable, str(MATERIALIZER), "--check" if args.check else "--score"]
    if not args.check:
        command.append("--write-scoring")
    completed = subprocess.run(command)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
