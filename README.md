# Ontology of Continua — Core 1.1

This repository contains the LaTeX sources and reproducible build
pipeline for the **Ontology of Continua — Core 1.1** publication shell
(“Whitepaper 1.1”). It is designed as a stable template for all future
Core versions and domain–specific preprints.

> **Goal:** provide a minimal, robust and fully automated LaTeX
> infrastructure so that future scientific work can focus on content,
> not tooling.

---

## 🔧 Build Status

GitHub Actions automatically compile the PDF on every push to `main`:

![Build LaTeX PDF](https://github.com/alexanderyashin/ontology-of-continua-core-main/actions/workflows/build-pdf.yml/badge.svg)

---

## 📄 What this repository provides

- A **XeLaTeX–based LaTeX pipeline** with Unicode support  
- A modular document structure with section placeholders:
  - introduction, background, model, results, discussion, conclusion
- Ready–to–use **figure and table placeholders**
- A **GitHub Actions** workflow for automatic PDF builds
- A `.zenodo.json` file with metadata for Zenodo integration
- A structure that can be reused as a **template** for:
  - Core 1.2+
  - Physics / Chemistry / Biology preprints
  - K0–K12 level extensions

The current version focuses on the *infrastructure*. Scientific content
will be added in later releases.

---

## 📁 Repository structure

```text
/ (root)
├── README.md              # This file
├── LICENSE                # CC-BY 4.0 license
├── .gitignore
├── .zenodo.json           # Zenodo metadata for releases
├── main.tex               # Main document file
├── preamble.tex           # Stable LaTeX preamble (XeLaTeX)
├── bib/
│   └── references.bib     # Bibliography database (dummy entry)
├── build/                 # Build output (created by latexmk / CI)
│   ├── logs/
│   │   └── compile.log    # LaTeX build log (optional)
│   └── (generated *.pdf etc.)
├── content/
│   ├── frontmatter.tex    # Title, abstract, metadata
│   ├── 01_intro.tex
│   ├── 02_background.tex
│   ├── 03_model.tex
│   ├── 04_results.tex
│   ├── 05_discussion.tex
│   ├── 06_conclusion.tex
│   └── placeholders/
│       ├── fig_placeholder.pdf
│       ├── section_template.tex
│       └── table_placeholder.tex
├── figures/
│   └── placeholder.txt    # Keeps the directory under version control
└── .github/
    └── workflows/
        └── build-pdf.yml  # GitHub Actions workflow for PDF builds
