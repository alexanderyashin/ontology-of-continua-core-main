# Ontology of Continua — Core 1.1
Stable LaTeX repository for Core whitepaper builds

This repository provides the canonical, deterministic, and reproducible LaTeX
environment for building the **Ontology of Continua — Core** whitepaper
(version 1.1).  
It serves as the reference template for:

- all future Core versions (1.2+),
- Physics, Chemistry, Biology preprints,
- K0–K12 level extensions,
- any domain-specific subprojects of the Ontology of Continua.

Everything needed for building the PDF is part of this repository:

- `main.tex` — single master document
- `preamble.tex` — global configuration (fonts, languages, packages)
- modular content structure inside `content/`
- “auto-inputs” mechanism via YAML → tools → `_auto_core_inputs.tex`
- GitHub Actions CI workflow
- Zenodo metadata (`.zenodo.json`)
- open-access license (CC BY 4.0)

This repository is under **ARCHITECTURE FREEZE**, ensuring stable builds.

------------------------------------------------------------
1. PDF build
------------------------------------------------------------

The PDF is built automatically on every push to the `main` branch.

Output file:

    build/main.pdf

Continuous Integration workflow:

    .github/workflows/build_pdf.yml

You can download the resulting PDF via:

- GitHub → Actions → “Build Core PDF” → Artifacts → **OK-Core-1.1-PDF**

------------------------------------------------------------
2. Local build instructions
------------------------------------------------------------

Requirements:

- TeX Live 2023+ (with xelatex + biber)
- latexmk (recommended)

### Recommended one-command build:

    ./build_core.sh

or manually:

    latexmk -xelatex -synctex=1 -interaction=nonstopmode \
      -output-directory=build main.tex

Result:

    build/main.pdf

### Cleanup:

    latexmk -C -output-directory=build

### Manual XeLaTeX sequence:

    xelatex -output-directory=build main.tex
    biber build/main
    xelatex -output-directory=build main.tex
    xelatex -output-directory=build main.tex

This reproduces latexmk’s logic (aux files → bibliography → repeated passes).

------------------------------------------------------------
3. Repository structure (short overview)
------------------------------------------------------------

Root level:

- `main.tex`        — master entry point  
- `preamble.tex`    — global LaTeX configuration  
- `build_core.sh`   — the **only allowed** build entry  
- `README.md`       — human-facing overview  
- `ARCHITECTURE.md` — canonical repo structure  
- `CONVENTIONS.md`  — style/naming standards  
- `BUILD_NOTES.md`  — build system specification  
- `.zenodo.json`    — metadata for Zenodo DOI integration  
- `.gitignore`      — ignores build directory and aux files  

Content directory (`content/`):

- `frontmatter.tex` — title, author, abstract  
- `01_intro.tex`  
- `02_background.tex`  
- `03_model.tex`  
- `04_results.tex`  
- `05_discussion.tex`  
- `06_conclusion.tex`  
- `_auto_core_inputs.tex` — auto-generated (never edit manually)

Placeholders:

- `content/placeholders/fig_placeholder.pdf`
- `content/placeholders/table_placeholder.tex`
- `content/placeholders/section_template.tex`

Figures:

- stored only in `figures/`
- not inside `content/`

Bibliography:

- `bib/references.bib`

Build directory:

- generated automatically by XeLaTeX/latexmk  
- contains `main.pdf`, logs, aux files  
- never committed to Git  

GitHub Actions:

- `.github/workflows/build_pdf.yml`  
- uses **only** `build_core.sh`  
- enforces XeLaTeX + biber reproducibility  

------------------------------------------------------------
4. Using this repository as a template
------------------------------------------------------------

To create Core 1.2 or a domain-specific preprint:

1. Clone or copy this repository.
2. Update title/abstract in `content/frontmatter.tex`.
3. Replace placeholder text in `content/*.tex` with real scientific content.
4. Add figures to `figures/` and reference them in the sections.
5. Add bibliography entries to `bib/references.bib`.
6. Update `.zenodo.json` for new versions/titles if creating a new Zenodo record.

**Do not modify:**
- `main.tex` (except top-level include order when explicitly required)
- `preamble.tex`
- YAML → auto-input generation pipeline
- build_core.sh

These files are part of the **frozen architecture**.

------------------------------------------------------------
5. License and metadata
------------------------------------------------------------

License:

- **Creative Commons Attribution 4.0 International (CC BY 4.0)**

Maintainer:

- **Alexander Yashin**

ORCID:

- **0009-0008-6166-0914**

------------------------------------------------------------

This README is the top-level guide to the repository.  
For detailed technical specifications, always refer to:

- **ARCHITECTURE.md**
- **CONVENTIONS.md**
- **BUILD_NOTES.md**

These three documents together form the stable foundation for all Core-level and extension-level work.
