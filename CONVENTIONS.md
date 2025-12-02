# Conventions and Style Guide — Ontology of Continua Core

This document defines all style rules, naming conventions, and workflow principles  
used in this repository.  
It is the **single source of truth** for LaTeX writing standards for all Core releases  
and domain extensions.

Any change to conventions requires updating this file.

---

# 1. General Principles

1. The repository must remain **clean**, **predictable**, and **reproducible**.
2. All scientific content lives inside `content/`.
3. No LaTeX code is placed in the root directory except:
   - `main.tex`
   - `preamble.tex`
4. Only XeLaTeX is supported.
5. Every section must compile independently when included into the master.
6. Placeholder elements must remain available for early drafts.

---

# 2. File Naming Rules

## 2.1 Section files

Sections follow the strict prefix rule:

```
NN_section-name.tex
```

Examples:

```
01_intro.tex
02_background.tex
03_model.tex
04_results.tex
05_discussion.tex
06_conclusion.tex
```

Rules:

- `NN` — two-digit numeric index.
- lowercase only.
- underscore `_` as separator.
- one section = one file.
- never reuse numbers.

## 2.2 Placeholders

```
fig_placeholder.pdf
table_placeholder.tex
section_template.tex
```

## 2.3 Figures

Stored in `figures/`.

Allowed formats:

- `.pdf` (preferred)
- `.png`
- `.jpg`

Naming:

```
fig_topic-name.pdf
```

---

# 3. LaTeX Style Rules

## 3.1 Document Language

- Default: **Russian** (Polyglossia)
- Secondary: English

## 3.2 Fonts

Defined in `preamble.tex`:

- DejaVu Serif  
- DejaVu Sans  
- DejaVu Sans Mono  

## 3.3 Packages

All packages are declared **only** in:

```
preamble.tex
```

No additional `\usepackage{...}` inside sections.

## 3.4 Sections

Every section:

- begins with `\section{Title}`
- contains only content, no structural definitions.

Forbidden inside section files:

- `\documentclass`
- `\begin{document}`
- `\end{document}`
- global macros/packages

## 3.5 Theorems and Math

Theorem environments defined centrally in `preamble.tex`:

```
theorem
lemma
definition
remark
```

Usage:

```latex
\begin{theorem}
  ...
\end{theorem}
```

## 3.6 Figures

Figures must use this standard structure:

```latex
\begin{figure}[h]
  \centering
  \includegraphics[width=0.75\textwidth]{figures/fig_filename.pdf}
  \caption{Description.}
  \label{fig:label}
\end{figure}
```

Rules:

- Always include `\label`.
- Labels follow pattern `fig:topic`.
- No inline images or SVG.

## 3.7 Tables

Use `booktabs` formatting:

```latex
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
```

## 3.8 References

Internal refs use `cleveref`:

```
see \cref{fig:example}
```

Bibliographic citations:

```
\textcite{key}
\parencite{key}
```

---

# 4. Adding New Sections

1. Create file:

```
content/NN_new-section.tex
```

2. Use the template:

```latex
\section{Title}
Placeholder text...
```

3. Include in main:

```latex
\input{content/NN_new-section}
```

4. Commit with message:

```
Add section NN_new-section
```

---

# 5. Working with Figures

Rules:

- Figures *never* live inside `content/`.
- All figures go into `figures/`.
- Use descriptive filenames:

```
fig_k2-phase-transition.pdf
fig_core-architecture.pdf
```

---

# 6. Bibliography Rules

- All entries go into `bib/references.bib`.
- No manual numbering.
- Do not modify biblatex setup in `preamble.tex`.

---

# 7. Commit Message Style

Allowed:

```
Add: model section
Update: background placeholders
Fix: broken ref
Refactor: frontmatter structure
```

Forbidden:

- fix stuff
- misc
- temp
- update
- final

---

# 8. Checklist for Alexander Yashin

Before committing:

- No extra packages.
- No global structure changes inside sections.
- Validate build locally:

```
latexmk -xelatex main.tex
```

- Check references.
- Ensure bibliography compiles.

---

# 9. Future Extensions Compatibility

This repo defines the baseline for:

- Core 1.2 and above
- Physics Preprints
- Chemistry U-series
- Biology U-series
- All K0–K12 extensions

All rules apply unless explicitly overridden.

---

