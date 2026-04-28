# OC Core 1.3.2 Release Quality Failure Analysis

## Root Cause

The previous green release state was mechanically strong but semantically under-gated: package integrity, no-send governance, Parfit/Cerberus, terminality and support-map checks passed, while human-facing prose and acknowledgement quality were not yet blocking release gates.

## Parfit/Cerberus Scope

Parfitian Cerberus G27 checks release ethics, no-send invariants, owner-waiver semantics, and Parfitian risk categories. It is not a prose-quality or acknowledgement-order checker.

## Failure Rows

| Issue | Why It Passed Before | Previous Gate | New Prevention |
| --- | --- | --- | --- |
| Human-facing overclaim or stale release wording could survive a mechanically green package. | G12 scanned only known PDF text patterns; G18 focused on leaks and claim-risk patterns; neither was a role-aware prose-quality gate. | `G12/G18` | G29 release_human_quality scans primary PDFs, release-spine sources, owner/release memos, PDF sources, and manifest roles for overclaiming and stale closure language. |
| Acknowledgements could be present but weak, incomplete, or unsorted. | G17 only checked that ACKNOWLEDGEMENTS.md existed and mentioned Alexander Yashin. | `G17` | G17 now validates the acknowledgement registry, exact requested public names, surname sorting, role notes, and no-endorsement/no-authorship flags. |
| Parfitian Cerberus passed while prose-quality defects remained. | G27 is an ethics/governance/no-send risk gate; it is not intended to judge release prose, acknowledgement order, or didactic polish. | `G27` | G29 is placed after Parfit/science terminality and before final verdict to block human-facing release-quality regressions. |
| Legacy source PDFs or thin synthetic-PDF generation paths could re-enter a release package. | Package composition excluded known journal/manuscript legacy PDFs but did not require explicit source-witness roles for all remaining legacy PDFs; legacy core.py still had thin synthetic PDF generation code. | `G13/package composition and legacy core.py` | Manifest role checks require source_witness_domain_packet for legacy/domain witness PDFs, and legacy core.py delegates primary PDF building to the complete release builder. |

## Recurrence Controls

- G29 release_human_quality
- Upgraded G17 acknowledgement registry validation
- Role-aware source-witness PDF manifest classification
- Deprecated legacy synthetic primary-PDF generation path
