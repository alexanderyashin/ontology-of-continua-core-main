# Ontology of Continua — Core 1.1
Stable LaTeX repository for Core whitepaper builds

This repository provides the canonical, deterministic and reproducible LaTeX
environment for building the "Ontology of Continua — Core" whitepaper
(version 1.1). It serves as the reference template for all future Core
versions and for domain-specific preprints (Physics, Chemistry, Biology,
K0–K12 Extensions).

Everything needed for building the PDF is part of this repository:
- master LaTeX file (main.tex),
- stable global preamble (preamble.tex),
- modular content structure in content/,
- placeholders for figures and tables,
- GitHub Actions workflow for CI builds,
- Zenodo metadata (.zenodo.json),
- open license (CC BY 4.0).

------------------------------------------------------------
1. PDF build
------------------------------------------------------------

The PDF is built automatically on every push to the main branch.

Output file:
- build/main.pdf

Continuous integration:
- .github/workflows/build_pdf.yml

You can download the latest artifact from:
- GitHub → Actions → Build PDF → Artifacts → OK-Core-1.1-PDF

------------------------------------------------------------
2. Local build instructions
------------------------------------------------------------

Requirements:

- TeX Live (2023 or newer) with:
  - xelatex
  - biber
- latexmk (recommended)

Recommended one-command build (from repository root):

    latexmk -xelatex -synctex=1 -interaction=nonstopmode -output-directory=build main.tex

The resulting PDF will be written to:

    build/main.pdf

Cleaning auxiliary files:

    latexmk -C -output-directory=build

Manual XeLaTeX build (if latexmk is not available):

    xelatex -output-directory=build main.tex
    biber build/main
    xelatex -output-directory=build main.tex
    xelatex -output-directory=build main.tex

This sequence reproduces what latexmk normally does: generate auxiliary files,
run biber for bibliography and re-run XeLaTeX to stabilise references and TOC.

------------------------------------------------------------
3. Repository structure (short overview)
------------------------------------------------------------

Root level:

- main.tex        – master document and single entry point
- preamble.tex    – global LaTeX configuration (fonts, languages, packages)
- README.md       – this file
- LICENSE         – CC BY 4.0 license text
- .gitignore      – ignores build/ and auxiliary files
- .zenodo.json    – metadata for Zenodo DOI integration

Content directory (logical sections of the paper):

- content/frontmatter.tex   – title, author, abstract
- content/01_intro.tex      – introduction
- content/02_background.tex – background and motivation
- content/03_model.tex      – core model structure
- content/04_results.tex    – results and consequences
- content/05_discussion.tex – discussion and limitations
- content/06_conclusion.tex – conclusion and outlook

Placeholders:

- content/placeholders/fig_placeholder.pdf   – dummy figure
- content/placeholders/table_placeholder.tex – dummy table environment
- content/placeholders/section_template.tex  – template for new sections

Additional documentation:

- ARCHITECTURE.md – full repository layout and file roles
- CONVENTIONS.md  – LaTeX and naming conventions
- BUILD_NOTES.md  – build system description and troubleshooting

These three documents are the canonical technical reference for working with
this repository.

------------------------------------------------------------
4. Using this repository as a template
------------------------------------------------------------

To create a new project (for example Core 1.2 or a domain preprint):

1. Clone or copy this repository.
2. Update the title, author and abstract in content/frontmatter.tex.
3. Replace placeholder text in content/*.tex with real scientific content.
4. Add real figures to the figures/ directory and update figure references
   in the sections.
5. Maintain all new references inside bib/references.bib.
6. If required, adjust .zenodo.json (title, description, version) for the
   new Zenodo record.

The overall structure (files, directories, CI workflow) should remain unchanged
to keep builds reproducible across all future releases.

------------------------------------------------------------
5. License and metadata
------------------------------------------------------------

License:
- Creative Commons Attribution 4.0 International (CC BY 4.0)

Maintainer:
- Alexander Yashin

ORCID:
- 0009-0008-6166-0914

This README is the human-facing overview of the repository. For detailed
technical information always refer to ARCHITECTURE.md, CONVENTIONS.md and
BUILD_NOTES.md.
