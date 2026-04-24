# OC Core 1.3.1 Corporate Projection Pack

This folder is a tracked supplementary governance layer for OC Core 1.3.1.
It is not a new public release asset and does not mutate the GitHub or Zenodo
release channels.

The pack answers one bounded question: how can the released science be projected
into corporate-facing instrument, tooling, product, business, and publication
surfaces without inflating the claims beyond the canonical science and release
gates?

## Files

- `OC_CORE_1_3_1_CORPORATE_PROJECTION_ATLAS_latest.json` is the source of truth.
- `OC_CORE_1_3_1_CORPORATE_PROJECTION_ATLAS.md` is the reviewer-facing summary.
- `OC_CORE_1_3_1_CORPORATE_PROJECTION_APPENDIX.tex` is a future manuscript
  appendix source. It is intentionally not wired into the already published
  v1.3.1 release artifacts.

## Guardrails

- Product and business rows are bounded operating surfaces, not claims of
  shipped software, revenue, investment value, or institutional endorsement.
- Every usable row must trace to existing repository sources.
- Publication rows must point to the existing OC Core 1.3.1 release PDFs or
  tracked release audits.
- The canonical public DOI remains `10.5281/zenodo.19741958`; the standalone
  Zenodo record `10.5281/zenodo.19741582` remains superseded.

Run:

```powershell
python tools\validate_oc_corporate_projection_pack_v1.py
```
