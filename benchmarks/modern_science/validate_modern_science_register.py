from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "comparators" / "OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES = REPO_ROOT / "benchmarks" / "modern_science" / "OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
REPORT = REPO_ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(path: Path) -> str:
    data = path.read_text(encoding="utf-8").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    errors: list[str] = []
    register = load_json(REGISTER)
    lanes = load_json(LANES)
    report = load_json(REPORT)

    if register.get("superiority_certified_total") != 0:
        errors.append("register certifies superiority")
    if report.get("release_promotion_allowed") is not False:
        errors.append("report allows release promotion")
    if "BLOCKED" not in str(register.get("current_release_state", "")):
        errors.append("register current release state is not blocked")
    if "BLOCKED" not in str(report.get("verdict", "")):
        errors.append("report verdict is not blocked")
    if lanes.get("certified_superiority_lane_total") != 0:
        errors.append("benchmark lanes certify superiority")

    lane_by_id = {row["lane_id"]: row for row in lanes.get("lanes", [])}
    if register.get("row_total") != len(register.get("rows", [])):
        errors.append("register row_total mismatch")
    if lanes.get("lane_total") != len(lanes.get("lanes", [])):
        errors.append("lanes lane_total mismatch")

    for row in register.get("rows", []):
        row_id = row.get("row_id", "<missing>")
        if row.get("superiority_claim_status") != "NOT_CERTIFIED":
            errors.append(f"{row_id} has non-blocked superiority status")
        if row.get("release_effect") != "BLOCK_RELEASE_PROMOTION_FOR_SUPERIORITY":
            errors.append(f"{row_id} does not block release promotion")
        if not row.get("source_refs"):
            errors.append(f"{row_id} has no source refs")
        if not row.get("blocking_predicates"):
            errors.append(f"{row_id} has no blocking predicates")

        lane_id = row.get("lane_id")
        lane = lane_by_id.get(lane_id)
        if lane is None:
            errors.append(f"{row_id} references missing lane {lane_id}")
        elif lane.get("current_verdict") != "BLOCKED_NO_SUPERIORITY_CERTIFIED":
            errors.append(f"{lane_id} lane verdict is not blocked")

        for source in row.get("source_refs", []):
            ref = source.get("local_source_capsule_ref")
            if not ref:
                errors.append(f"{row_id} source ref missing local capsule")
                continue
            path = REPO_ROOT / ref
            if not path.exists():
                errors.append(f"{row_id} source capsule missing: {ref}")
                continue
            expected_hash = source.get("local_source_capsule_sha256")
            if expected_hash and expected_hash != sha256_text(path):
                errors.append(f"{row_id} source capsule hash mismatch: {ref}")

    for lane in lanes.get("lanes", []):
        lane_id = lane.get("lane_id", "<missing>")
        statuses = lane.get("current_predicate_status", {})
        if not statuses:
            errors.append(f"{lane_id} has no predicate status map")
        if all(statuses.values()):
            errors.append(f"{lane_id} has all predicates true despite blocked verdict")
        if not lane.get("blocked_by"):
            errors.append(f"{lane_id} has no blocked_by predicates")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern science superiority register remains source-backed and blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

