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

### 2.1 Section files
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

### 2.2 Placeholders
```
fig_placeholder.pdf
table_placeholder.tex
section_template.tex
```

### 2.3 Figures
Stored in `figures/`:

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

### 3.1 Document Language
- Default: **Russian** (Polyglossia)
- Secondary: English

### 3.2 Fonts
Defined in `preamble.tex`:
- DejaVu Serif
- DejaVu Sans
- DejaVu Sans Mono

### 3.3 Packages
All packages are declared only in:
```
preamble.tex
```
No additional `\usepackage{...}` inside sections.

### 3.4 Sections
Every section:
- begins with `\section{Title}`
- contains only content, no structural definitions.

Forbidden inside section files:
- `\documentclass`
- `\begin{document}`
- `\end{document}`
- global macros/packages

### 3.5 Theorems and Math
Theorem environments defined centrally in `preamble.tex`:
```
theorem
lemma
definition
remark
```

Usage inside sections:
```
\begin{theorem}
  ...
\end{theorem}
```

### 3.6 Figures
Figures must use this standard placeholder structure:

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
- Labels follow pattern: `fig:topic`.
- No inline images via base64 or SVG.

### 3.7 Tables
Tables use `booktabs`:

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

### 3.8 References
Internal references use `cleveref`:
```
see \cref{fig:example}
```

Bibliography is generated via:
```
\textcite{key}
\parencite{key}
```

---

# 4. Adding New Sections

To add a new scientific section:

1. Create file:
   ```
   content/NN_new-section.tex
   ```
2. Use the template structure:
   ```latex
   \section{Title}
   Placeholder text...
   ```
3. Add section to `main.tex`:
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
- All figures go to `figures/`.
- Use descriptive and stable filenames:
  ```
  fig_k2-phase-transition.pdf
  fig_core-architecture.pdf
  ```

---

# 6. Bibliography Rules

- All citations must be properly entered into `bib/references.bib`.
- Cite using LaTeX commands — no manual numbering.
- Do not modify biblatex setup in `preamble.tex`.

---

# 7. Commit Messages

Commit messages should be clear and structured:

Examples:
```
Add: new placeholder figure
Update: Background section structure
Fix: broken reference in model section
Refactor: reorganize frontmatter
```

Forbidden:
- “fix”
- “stuff”
- “update”
- “misc”

---

# 8. Client (Alexander Yashin) Checklist

### When editing content:
- Add only text, not packages.
- Keep mathematics clean and consistent.
- Avoid overfull hboxes — break long formulas.

### When editing structure:
- Update this file and `ARCHITECTURE.md`.

### Before commit:
- Ensure compile locally:
  ```
  latexmk -xelatex main.tex
  ```
- Validate references.
- Validate bibliography.

---

# 9. Future Extensions Compatibility

This repository is a template for:

- Core 1.2
- Physics Preprints
- Chemistry U0.x
- Biology U0.x
- K0–K12 Extension Papers

All rules in this file apply equally to all future repositories unless explicitly overridden.

---
