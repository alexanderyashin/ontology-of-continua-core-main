from __future__ import annotations

import json
from pathlib import Path


def load_claims(path: str = "claims/CLAIM_LEDGER_FULL.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["claims"]
