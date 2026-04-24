# Logion Release Machine

The Logion Release Machine is a repo-local external release quality system. Every outward release unit must pass channel policy, artifact inventory, build/reproducibility, document quality, claim/evidence ceilings, public-surface parity, security/privacy, owner approval, publish preflight, and postflight gates.

The hard rule is no false PASS. A gate that did not run cannot be PASS. A credential or channel blockage is BLOCKED, not PASS. Critical or high findings make publication impossible.
