# Ontology of Continua — Core 1.1

Stable publication shell for the **Ontology of Continua — Core 1.1**
(whitepaper infrastructure release).

This repository provides a **reproducible LaTeX pipeline** and a
clean structure for publishing the Core as a scientific article and
for reusing the same setup for future versions (Core 1.2+, Physics,
Chemistry, Biology, K0–K12 extensions).

---

## Zenodo DOI

Current concept DOI for the Ontology of Continua Core series:

**DOI:** `10.5281/zenodo.17699894`  

Future releases of this repository (tags like `v1.1`, `v1.2`, …) will
be mirrored to Zenodo and appear as new versions under this concept
DOI via GitHub–Zenodo integration.

---

## Building the PDF locally

### Requirements

- TeX Live (recommended: full installation)
- `latexmk`
- Perl (usually comes with TeX Live on Linux/macOS; on Windows use
  TeX Live or MiKTeX with `latexmk` support)

### Minimal commands

From the repository root:

```bash
latexmk -pdf main.tex -interaction=nonstopmode -output-directory=build
