# Conventions and Style Guide — Ontology of Continua Core 1.1

This document defines all style rules, naming conventions, and workflow
principles used in this repository.
It is the single source of truth for LaTeX writing standards for all
Core releases and domain extensions.

Any change to conventions must also update this file.

------------------------------------------------------------
1. General Principles
------------------------------------------------------------

1. The repository must remain clean, predictable, and reproducible.
2. All scientific content lives inside `content/`.
3. Only two LaTeX files exist in the root:
      - main.tex
      - preamble.tex
4. Only XeLaTeX is supported.
5. The build pipeline is frozen and must not be altered:
      ./build_core.sh → latexmk → build/main.pdf
6. Auto-generated files must never be edited manually.
7. Placeholder elements must remain available for early drafts.

------------------------------------------------------------
2. File Naming Rules
------------------------------------------------------------

------------------------------------------------------------
2.1 Section files
------------------------------------------------------------

Section files follow the strict prefix rule:

    NN_section-name.tex

Examples:

    01_intro.tex
    02_background.tex
    03_model.tex
    04_results.tex
    05_discussion.tex
    06_conclusion.tex
    07_figures.tex

Rules:
- NN = two-digit numeric index
- lowercase names
- underscore `_` as the only separator
- one section = one file
- numbers must never be reused or reordered
- section numbers are defined in master_core_structure.yaml

------------------------------------------------------------
2.2 Placeholders
------------------------------------------------------------

Allow early drafting:

    fig_placeholder.pdf
    table_placeholder.tex
    section_template.tex

------------------------------------------------------------
2.3 Figures
------------------------------------------------------------

All real figures must be stored in:

    figures/

Allowed formats:
- pdf (preferred)
- png
- jpg

Naming pattern:

    fig_topic-name.pdf

------------------------------------------------------------
3. LaTeX Style Rules
------------------------------------------------------------

------------------------------------------------------------
3.1 Document Language
------------------------------------------------------------

- Default: Russian (polyglossia)
- Secondary: English

All language configuration is done ONLY in preamble.tex.

------------------------------------------------------------
3.2 Fonts
------------------------------------------------------------

Defined exclusively in preamble.tex:
- DejaVu Serif
- DejaVu Sans
- DejaVu Sans Mono

No section may redefine fonts.

------------------------------------------------------------
3.3 Packages
------------------------------------------------------------

All packages are declared ONLY in:

    preamble.tex

Prohibited inside section files:
- \usepackage
- new packages or global setup
- engine-specific commands

------------------------------------------------------------
3.4 Section Structure
------------------------------------------------------------

Every section file MUST start with:

    \section{Title}

Section files must contain only content.  
Forbidden inside sections:
- \documentclass
- \begin{document}, \end{document}
- global macros
- redefinitions
- package imports

------------------------------------------------------------
3.5 Theorems and Math
------------------------------------------------------------

Theorem-like environments are declared centrally in preamble.tex:

    theorem
    lemma
    definition
    remark

Usage example:

    \begin{theorem}
      ...
    \end{theorem}

No new theorem environments may be created in section files.

------------------------------------------------------------
3.6 Figures
------------------------------------------------------------

Standard structure:

    \begin{figure}[h]
      \centering
      \includegraphics[width=0.75\textwidth]{figures/fig_filename.pdf}
      \caption{Description.}
      \label{fig:label}
    \end{figure}

Rules:
- label required
- labels follow: fig:topic-name
- width typically 0.7–0.9\textwidth
- no inline SVG or external URLs

------------------------------------------------------------
3.7 Tables
------------------------------------------------------------

Use booktabs:

    \begin{table}[h]
      \centering
      \begin{tabular}{lll}
        \toprule
        ...
        \bottomrule
      \end{tabular}
      \caption{Description.}
      \label{tab:label}
    \end{table}

Rules:
- label required
- no vertical lines
- prefer meaningful captions

------------------------------------------------------------
3.8 References
------------------------------------------------------------

Internal references use cleveref:

    see \cref{fig:example}

Bibliographic references:

    \textcite{key}
    \parencite{key}

Never use plain \cite.

------------------------------------------------------------
4. Adding New Sections
------------------------------------------------------------

Steps:

1. Create file:

       content/NN_new-section.tex

2. Use the template:

       \section{Title}
       Placeholder text...

3. Add it to master_core_structure.yaml (DO NOT edit auto-inputs manually)

4. Run:

       ./build_core.sh

5. Commit with message:

       Add: section NN_new-section

------------------------------------------------------------
5. Working with Figures
------------------------------------------------------------

Rules:
- Figures ALWAYS go into figures/
- Never store images in content/
- Use descriptive filenames:

       fig_k2-phase-transition.pdf
       fig_core-architecture.pdf

- Never commit huge raw data dumps; compress before committing.

------------------------------------------------------------
6. Bibliography Rules
------------------------------------------------------------

- All entries must be placed exclusively in bib/references.bib
- The bibliography setup in preamble.tex must not be changed
- Never edit generated .bbl files
- Check Biber output if the build fails

------------------------------------------------------------
7. Commit Message Style
------------------------------------------------------------

Allowed patterns:

    Add: <component>
    Update: <component>
    Fix: <issue>
    Refactor: <component>
    Docs: <file>

Examples:

    Add: model section
    Fix: broken table label
    Update: conventions for figures

Forbidden:

- fix stuff
- misc
- temp
- final
- pls_work
- test
- cleanup (without description)

------------------------------------------------------------
8. Checklist for Alexander Yashin
------------------------------------------------------------

Before committing:
- No new packages added
- No global changes in section files
- Build locally:

      ./build_core.sh

- Check references and labels
- Ensure bibliography compiles cleanly
- Confirm YAML + auto-input generation works

For every structural change:
- Update ARCHITECTURE.md
- Update CONVENTIONS.md
- Update BUILD_NOTES.md

------------------------------------------------------------
9. Future Extensions Compatibility
------------------------------------------------------------

These conventions define the baseline for:

- Core 1.2+
- Physics Preprints (K2, K2.Q, K1 Dynamics)
- Chemistry U-series (U0.2, U0.3b, U-final)
- Biology U-series (K4→K5)
- Cognition K6-series
- Social Systems K7-series
- Civilization K8-series
- All K0–K12 structural exports

All extension repositories must inherit these rules unless explicitly overridden.

------------------------------------------------------------
End of file.
------------------------------------------------------------
