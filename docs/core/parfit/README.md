# Parfitian Cerberus Layer

The Parfitian Cerberus Layer is an operational release-governance gate for OC release candidates. It checks whether a package is self-defeating, evidentially debt-shifting, identity-breaking, future-stakeholder hostile, or volume-inflated.

It is not a claim that OC solves Parfitian ethics. It is a blocking quality-control layer for publication readiness.

## Release Rule

- High, critical, or blocker findings prevent `RELEASE_READY_NO_SEND`.
- Blocker findings are not waivable.
- Publication, outbound sending, GitHub push, Zenodo upload and DOI minting remain false unless a separate owner/governance unlock exists.
- A pass means only that the Parfitian gate found no High+ blocker for a no-send release candidate.

## Passes

- Self-defeat.
- Moral mathematics and small-effect aggregation.
- Five-part decision matrix.
- Relation R release continuity.
- Future stakeholders.
- Repugnant output.
- Transparency.
- Evidence burden.

## Current Targets

- `oc_core_1_3_2`: current no-send baseline candidate.
- `oc_core_1_4_0_rc1`: forward gate; incomplete inputs are explicit findings, not fake passes.
