# Formal Dossier for HOSTILE::EXCLUDED_LIFT_FIREWALL

- Challenge: No excluded lift-heavy theorem family may be smuggled into the positive bounded argument.
- Current status: `PASS`
- Current resolution state: `PASS_LOCKED`
- Resolution if pass: `CLEAR_HOSTILE_REVIEW_BLOCKER_AND_LOCK_CLOSED_CORE_ROUTE`
- Resolution if fail: `KEEP_FAIL_CLOSED_AND_REBUILD_AFFECTED_CLOSED_CORE_ROUTE`
- Resolution outcome: `PASS`
- Exit criterion: An exclusion ledger proves that forbidden theorem families and forbidden branches do not enter the core proof path.

## Exact Theorem Route Under Attack

- Axiom 3.2 route to Source Theorem 3
- Lemma 1
- Lemma 2
- Theorem A

## Premises

- OBLIGATION::SOURCE_THEOREM_3
- OBLIGATION::LEMMA_1
- OBLIGATION::LEMMA_2
- OBLIGATION::THEOREM_A

## Forbidden Shortcuts

- No excluded lift-heavy family may enter the positive bounded argument.
- No extension branch or bridge-only packet may masquerade as theorem support.

## Formal Argument Body

- The firewall exists to keep the closed core route from silently importing excluded theorem families, extension branches, or bridge-only evidence as proof support.
- The obligation chain from Source Theorem 3 through Theorem A explicitly names excluded dependencies; the firewall dossier must therefore be an auditable exclusion ledger rather than a prose assurance.
- Any leak from excluded lift-heavy material back into the core route invalidates the current promotion surface immediately.
- The dossier is now locked as a passed formal review under the exact source route and may be reopened only by a surviving falsifier.

## Falsifier Conditions

- Identify an excluded branch identifier inside any core proof path.
- Show that Lemma 2 or Theorem A requires extension or bridge-only support.

Refs:
- `releases/oc_core_1_3/editorial/science_sources/public_review_limits/hostile_excluded_lift_firewall.json`
- `content/20_oc_core_1_3_theorem_roadmap.tex`
- `content/21_oc_core_1_3_worked_examples.tex`
- `content/19_oc_core_1_3_foundational_consistency.tex`
