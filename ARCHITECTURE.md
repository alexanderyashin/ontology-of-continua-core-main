# Ontology of Continua — Core 1.1  
## Repository Architecture

This repository is the **publication shell** and **LaTeX build pipeline** for the
_“Ontology of Continua — Core 1.1”_ whitepaper.  
The goal is to keep the structure stable and reusable for future Core versions
and domain-specific preprints.

---

## 1. Top-level layout

```text
/ (repository root)
├── ARCHITECTURE.md        ← human-readable repo structure (this file)
├── CONVENTIONS.md         ← LaTeX & content conventions
├── BUILD_NOTES.md         ← build system and CI notes
├── README.md              ← short project description & quickstart
├── LICENSE                ← CC BY 4.0 for text and repo content
├── .gitignore             ← ignores build artefacts etc.
├── .zenodo.json           ← metadata template for Zenodo auto-updates
├── main.tex               ← master LaTeX file (entry point)
├── preamble.tex           ← stable LaTeX preamble (fonts, packages, theorem envs)
├── content/               ← all logical sections of the paper
│   ├── frontmatter.tex    ← title, author, abstract (in English)
│   ├── 01_intro.tex       ← introduction
│   ├── 02_background.tex  ← background & motivation
│   ├── 03_model.tex       ← core model structure
│   ├── 04_results.tex     ← consequences & results
│   ├── 05_discussion.tex  ← discussion and limitations
│   ├── 06_conclusion.tex  ← conclusion & outlook
│   └── placeholders/      ← reusable content placeholders
│       ├── fig_placeholder.pdf
│       ├── section_template.tex
│       └── table_placeholder.tex
├── figures/               ← all figures used in the paper
│   └── placeholder.txt    ← dummy file to keep the directory tracked
├── bib/                   ← bibliography resources
│   └── references.bib     ← BibLaTeX database
├── build/                 ← build artefacts (created by latexmk / CI)
│   ├── logs/
│   │   └── .gitkeep       ← keeps the logs directory in Git
│   └── .gitkeep           ← keeps the build directory in Git
└── .github/
    └── workflows/
        └── build-pdf.yml  ← GitHub Actions workflow for automated PDF builds
