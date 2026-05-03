from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oc133_manuscript_structure_transfer_lib import run_transfer_cli


if __name__ == "__main__":
    raise SystemExit(run_transfer_cli(8))
