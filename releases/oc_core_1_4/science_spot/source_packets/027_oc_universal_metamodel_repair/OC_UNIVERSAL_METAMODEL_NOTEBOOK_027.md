# OC Universal Metamodel Notebook 027

## Scientific Repair

The old fork was false because it ignored existing repair. OC-U repairs the
model by making absorption and underdetermination first-class outcomes.

## Theorem Chain

| Claim id | Claim | Status | Artifact |
| --- | --- | --- | --- |
| `OCU-027-T001` | Articulated descriptions can be represented by OC-U primitives | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-T002` | Absorption follows when an existing same-description operator resolves pressure | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-T003` | Extension/new-axis follows when no same repair exists but an extension repair exists | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-T004` | Collapse follows when repair/extension fail and invariant failure is declared | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-T005` | Underdetermination follows when evidence binding is absent or invariant failure is not established | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-T006` | The four-response taxonomy is total for the classifier | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-T007` | Core projection signature alone cannot inflate into domain validation | `PROVED_UNIVERSAL_METAMODEL_THEOREM` | `formal/OCUniversal/Basic.lean` |
| `OCU-027-R001` | Old two-outcome universal fork is incomplete | `REFUTED_OLD_FORMULATION` | `formal/ocu_python_witnesses.py` |
| `OCU-027-D001` | Real-domain truth requires local instantiation evidence | `DOMAIN_INSTANTIATION_REQUIRED` | `formal/ocu_python_witnesses.py` |

## Result

OC-U is restored as a universal metamodel, not as a universal event law. It can
classify any articulated description, including cases where the honest result
is that the domain has not yet supplied enough structure.

## Integrity Closeout

Formal checks:

- `lake build` passes in `formal/`;
- `python formal/ocu_python_witnesses.py` passes.

SQLite proof ledger:

- `PROVED_UNIVERSAL_METAMODEL_THEOREM`: 7 rows;
- `REFUTED_OLD_FORMULATION`: 1 row;
- `DOMAIN_INSTANTIATION_REQUIRED`: 1 row;
- bad final statuses: 0.

Root-cause result:

Earlier Lean/TOE surfaces did not prove OC as a universal metamodel. They
proved conditional or governance surfaces while the authoritative TOE program
remained `FAIL_CLOSED` / `REPAIR_METAMODEL`. 027 is the first package in this
series that makes the universal metamodel claim itself the object of a Lean
theorem chain.

Scientific status:

OC-U may now honestly claim universal metamodel status over articulated
descriptions of system dynamics. It may not claim automatic empirical truth of
every real-world projection without local instantiation.
