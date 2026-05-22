"""Executable finite witnesses for OC 045 readiness gates."""


def no_send_gate(claim: dict) -> str:
    if claim.get("commercial") and not claim.get("external_evidence"):
        return "NO_SEND"
    if claim.get("empirical") and not claim.get("dataset_manifest"):
        return "NO_SEND"
    if claim.get("public") and claim.get("private_material"):
        return "NO_SEND"
    return "SEND_BOUNDED"


def main() -> None:
    cases = [
        ({"commercial": True, "external_evidence": False}, "NO_SEND"),
        ({"empirical": True, "dataset_manifest": False}, "NO_SEND"),
        ({"public": True, "private_material": True}, "NO_SEND"),
        ({"public": True, "private_material": False, "empirical": False}, "SEND_BOUNDED"),
    ]
    for case, expected in cases:
        got = no_send_gate(case)
        if got != expected:
            raise SystemExit(f"witness failed: {case} -> {got}, expected {expected}")
    print("OC 045 readiness witnesses: PASS")


if __name__ == "__main__":
    main()
