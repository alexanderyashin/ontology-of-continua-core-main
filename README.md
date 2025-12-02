# Ontology of Continua — Core 1.1 (Whitepaper Shell)

This repository provides a stable, fully reproducible LaTeX build pipeline and publication shell for **Ontology of Continua — Core 1.1**, intended as the canonical structure for all future Core releases and domain-specific extensions (Physics, Chemistry, Biology, Cognition, Society, Civilization, Meta-theory).

The goal of this repository is to ensure:
- reproducible PDF builds (local and CI),
- clean modular LaTeX structure,
- long-term maintainability,
- Zenodo auto-publishing with versioned DOIs,
- a universal template for future Ontology of Continua publications.

---

## 📘 Contents

```
/ (root)
├── main.tex
├── preamble.tex
├── README.md
├── LICENSE
├── .gitignore
├── .zenodo.json
├── content/
│   ├── frontmatter.tex
│   ├── 01_intro.tex
│   ├── 02_background.tex
│   ├── 03_model.tex
│   ├── 04_results.tex
│   ├── 05_discussion.tex
│   ├── 06_conclusion.tex
│   └── placeholders/
│       ├── fig_placeholder.pdf
│       ├── table_placeholder.tex
│       └── section_template.tex
├── build/
│   ├── .gitkeep
│   └── logs/
│       └── .gitkeep
└── .github/
    └── workflows/
        └── build-pdf.yml
```

---

## 📄 Project Description

**Ontology of Continua (OC)** is a unified theoretical framework describing the emergence, structure, and evolution of continua across physical, chemical, biological, cognitive, social, civilizational, and meta-theoretical domains.

**Core 1.1** represents the first stable, consolidated version of the foundational layer of the theory, formatted as **Whitepaper 1.1**.

This repository contains:
- the LaTeX implementation of Core 1.1,
- publication-ready modular structure,
- figure/table/section placeholders,
- CI/CD configuration for automated PDF builds.

---

## 🔗 DOI (Zenodo)

**DOI:** will be attached automatically after creating a GitHub Release  
Zenodo will auto-archive this repository and assign a versioned DOI using `.zenodo.json`.

---

## 🛠️ Building the PDF (Local)

### Requirements
- **TeX Live (recommended: full installation)**
- **latexmk**
- Perl (included on most systems)

### Build commands
```bash
latexmk -xelatex -interaction=nonstopmode -output-directory=build main.tex
```

To clean generated files:
```bash
latexmk -C
```

---

## ⚙️ Continuous Integration (GitHub Actions)

Every push to `main` triggers:
- installation of TeX Live (full),
- XeLaTeX build of `main.tex`,
- upload of `main.pdf` as a workflow artifact.

Workflow file:  
`.github/workflows/build-pdf.yml`

---

## 🧩 Using This Repository as a Template

This structure is intended to serve as the official template for:

- Ontology of Continua Core versions (1.2, 1.3, …)
- Physics Preprint Series
- Chemistry U0.x Series
- Biology U0.x Series
- Cognitive Theory K6/K7 expansions
- Social and Civilizational continua (K7–K8)
- Meta-theory (K9–K10)
- Meta-metatheory (K11–K12)

To create a new release:
1. Copy the repository.
2. Replace the section `.tex` files with real content.
3. Update `.zenodo.json` (title, description, version).
4. Create a GitHub Release — Zenodo will publish automatically.

---

## 📚 Dependencies

Recommended environment:

- **TeX Live 2023 or newer**
- `latexmk`
- `xelatex`
- Packages included:
  - `fontspec`
  - `geometry`
  - `hyperref`
  - `biblatex`
  - `csquotes`
  - and all standard TeX Live components

---

## 👤 Maintainer

**Alexander Yashin**  
ORCID: **0009-0008-6166-0914**

---

## 📄 License

This project is released under the **Creative Commons Attribution 4.0 International (CC-BY-4.0)** license.

