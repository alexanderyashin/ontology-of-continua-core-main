# Repository Architecture — Ontology of Continua Core 1.1

This document defines the canonical architecture of the repository.  
It serves as the stable reference for all future Core releases and domain-specific preprints.

The structure described here is **authoritative**.  
All updates to the repository must also update this file.

---

# 1. High-Level Structure

```
/
  main.tex
  preamble.tex
  README.md
  LICENSE
  .gitignore
  .zenodo.json

  content/
    frontmatter.tex
    01_intro.tex
    02_background.tex
    03_model.tex
    04_results.tex
    05_discussion.tex
    06_conclusion.tex

    placeholders/
      fig_placeholder.pdf
      table_placeholder.tex
      section_template.tex

  figures/
    placeholder.txt

  bib/
    references.bib

  build/
    (generated automatically)
    logs/
      (generated automatically)

  .github/
    workflows/
      build_pdf.yml
```

---

# 2. Core LaTeX Files

### **`main.tex`**
The *single entry point* for building the PDF.  
Defines the document structure and includes all sections.

### **`preamble.tex`**
Global LaTeX configuration layer:
- XeLaTeX engine  
- Fonts (DejaVu Serif/Sans/Mono)  
- Polyglossia language settings  
- biblatex + biber configuration  
- theorem environments  
- global packages  

This file must remain stable across all versions.

---

# 3. Content Directory (`content/`)

All logical sections of the Core document reside here.

### **frontmatter.tex**
Contains:
- title
- author
- abstract
- date

### numbered sections:
- **01_intro.tex** – Introduction  
- **02_background.tex** – Background & Motivation  
- **03_model.tex** – Ontological Structure  
- **04_results.tex** – Results & Consequences  
- **05_discussion.tex** – Discussion  
- **06_conclusion.tex** – Conclusion  

### placeholders/
Reusable dummy elements for early drafts:
- `fig_placeholder.pdf`
- `table_placeholder.tex`
- `section_template.tex`

---

# 4. Figures (`figures/`)
All external images must be stored here.

### file types allowed:
- `.pdf` (preferred)
- `.png`
- `.jpg`

No figures should be placed inside `content/`.

---

# 5. Bibliography (`bib/`)

### **`references.bib`**
The single BibLaTeX database used by biber during the build.

---

# 6. Build Directory (`build/`)

This directory is created automatically by latexmk during compilation.

Contains:
- `main.pdf`
- `.aux`, `.log`, `.toc`, `.bcf`, `.run.xml`, etc.
- `/logs/compile.log`

It must remain **untracked** in Git.

---

# 7. GitHub Actions (`.github/workflows/`)

### **`build_pdf.yml`**
Continuous integration pipeline:

1. Installs XeLaTeX + Biber  
2. Compiles document via:
   ```
   latexmk -xelatex -interaction=nonstopmode -output-directory=build main.tex
   ```
3. Uploads PDF as artifact  
4. Ensures reproducible build for every commit to `main`

---

# 8. Metadata (`.zenodo.json`)

Required for:
- DOI registration
- auto-updating Zenodo releases
- correct creators + ORCID
- open-access definition
- CC-BY-4.0 license metadata

---

# 9. Repository Conventions (short reference)

- All LaTeX sections go into `content/`, never in root.
- Filenames use numeric prefixes: `NN_section-name.tex`
- Figures go only into `figures/`.
- No build files in Git.
- All changes to structure → update this file.

---

# 10. Purpose

This architecture is designed to be:

- **Stable**
- **Predictable**
- **Reusable for all future releases**
- **CI-compatible**
- **Zenodo-compatible**
