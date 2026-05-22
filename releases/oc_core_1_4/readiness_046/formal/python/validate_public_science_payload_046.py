"""Validate the public-safe OC 046 science/readiness payload."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO = next(p for p in [ROOT, *ROOT.parents] if (p / ".git").exists())
MANIFEST = ROOT / "PUBLIC_SCIENCE_PAYLOAD_MANIFEST_046.json"

FORBIDDEN = [
    "private_business_plan",
    "business_plan_master",
    "client",
    "counsel",
    "legal_opinion",
    "owner_decision_logs_private",
    "external_llm_review_dossiers",
    "full_dataset",
]


def main() -> None:
    if not MANIFEST.exists():
        raise SystemExit("missing public 046 manifest")
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = payload.get("files", [])
    if not files:
        raise SystemExit("public 046 manifest has no files")
    for rel in files:
        low = rel.lower()
        if any(term in low for term in FORBIDDEN):
            raise SystemExit(f"forbidden public path: {rel}")
        path = REPO / rel if (REPO / rel).exists() else ROOT / Path(rel).relative_to("logion/k7/release_missions/oc_core_current/packages/oc_core_1_4/046/world_readiness_blocker_burndown")
        if not path.exists():
            raise SystemExit(f"missing public file: {rel}")
        if path.stat().st_size > 100 * 1024 * 1024:
            raise SystemExit(f"oversized public file: {rel}")
    packet = (ROOT / "OC_046_PUBLIC_SCIENCE_PACKET.md").read_text(encoding="utf-8")
    forbidden_claims = [
        "legal advice is provided",
        "client ROI proven",
        "external user validation complete",
        "FTO opinion complete",
    ]
    for phrase in forbidden_claims:
        if phrase.lower() in packet.lower():
            raise SystemExit(f"public packet contains forbidden claim phrase: {phrase}")
    print("OC 046 public science payload validator: PASS")
    print(f"files={len(files)}")


if __name__ == "__main__":
    main()
