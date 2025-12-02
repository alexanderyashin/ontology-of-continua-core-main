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

🧪 How to build the PDF locally

The repository is optimised for XeLaTeX with latexmk.

Requirements

TeX Live 2023+ (or equivalent full LaTeX distribution)

latexmk command available in your PATH

Linux / macOS
latexmk -xelatex main.tex -interaction=nonstopmode -output-directory=build


The compiled PDF will be located at:

build/main.pdf

Windows (MiKTeX / TeX Live)

Use a terminal (PowerShell or cmd) with latexmk available and run the
same command:

latexmk -xelatex main.tex -interaction=nonstopmode -output-directory=build


If your distribution does not ship latexmk by default, install it via
your package manager or the distribution’s package GUI.

🤖 Continuous integration (GitHub Actions)

The workflow file:

.github/workflows/build-pdf.yml


does the following on every push to main and on pull requests:

Checks out the repository

Installs TeX Live and latexmk

Runs latexmk -xelatex with build/ as the output directory

Uploads build/main.pdf as a build artefact

You can always download the latest PDF from the Actions tab of the
repository.

🧩 Using this repository as a template

To use this repository as a starting point for a new document:

Clone or fork the repository.

Update content/frontmatter.tex:

title, subtitle, abstract

version string in \date{...}

Replace the placeholder content in:

01_intro.tex, 02_background.tex, 03_model.tex,
04_results.tex, 05_discussion.tex, 06_conclusion.tex

Add real figures under figures/ and update figure includes.

Extend bib/references.bib with your bibliography entries.

Adapt .zenodo.json if you plan to publish via Zenodo
(title, description, version, creators, etc.).

The goal is to keep the build pipeline unchanged so future work can
reuse it without extra setup.

📚 Zenodo integration

The file .zenodo.json contains metadata for automated deposition to
Zenodo when a GitHub Release is created.

After the first release has been archived on Zenodo, you may add a
DOI badge here, e.g.:

[![DOI](https://doi.org/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)


Replace XXXXXXX with the actual Zenodo record number.

⚖️ License

The contents of this repository are licensed under:

Creative Commons Attribution 4.0 International (CC BY 4.0)

See the LICENSE file for details.

You are free to share and adapt the material, provided that appropriate
credit is given.

👤 Maintainer

Alexander Yashin

ORCID: 0009-0008-6166-0914

For questions, please use the issue tracker of this repository.
