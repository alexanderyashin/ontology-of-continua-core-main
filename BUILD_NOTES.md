# Build System Notes — Ontology of Continua Core 1.1

This document describes the canonical, frozen build pipeline for the
Ontology of Continua — Core 1.1 publication shell.  
It defines the only supported build entry point, dependency rules,
and CI execution model.

Any changes to the build system must be approved by OK Main HQ and
Core 1.1 Release HQ.

------------------------------------------------------------
1. Overview
------------------------------------------------------------

Core 1.1 uses a structured, reproducible build pipeline based on:

- a single entry script: build_core.sh  
- YAML-driven generation of section inputs  
- XeLaTeX as the only engine  
- latexmk as the PDF orchestrator  
- biber for bibliography  

The high-level flow is:

1. master_core_structure.yaml → auto-generate missing .tex files  
2. validate structure  
3. generate content/_auto_core_inputs.tex  
4. compile main.tex via XeLaTeX through latexmk

The user never edits auto-generated files.

------------------------------------------------------------
2. The Only Supported Build Command
------------------------------------------------------------

To build Core 1.1 you MUST use:

    ./build_core.sh

This script:

1. Generates missing section files from master_core_structure.yaml  
2. Validates the repository structure  
3. Regenerates content/_auto_core_inputs.tex  
4. Calls latexmk -xelatex with correct flags  
5. Writes final PDF to build/main.pdf  

Direct calls to:

- latexmk
- xelatex
- python generators
- manual editing of auto_core_inputs.tex

are NOT supported and may break the build.

------------------------------------------------------------
3. Local Dependencies
------------------------------------------------------------

Required:

- TeX Live 2023 or newer (full installation recommended)
- python3
- latexmk
- biber

Ubuntu / Debian:

    sudo apt-get update
    sudo apt-get install -y texlive-full latexmk biber python3

macOS:

    brew install --cask mactex
    brew install latexmk

Windows:

- Install TeX Live (full)
- Ensure xelatex, latexmk, biber are in PATH
- Ensure python3 is installed

------------------------------------------------------------
4. What build_core.sh does
------------------------------------------------------------

The script performs four steps:

(1) Generate missing .tex files  
    tools/generate_core_from_yaml.py

(2) Validate structure  
    tools/validate_core_structure.py  
    (Warnings do not stop the build.)

(3) Generate auto include file  
    tools/generate_auto_inputs.py  
    → writes content/_auto_core_inputs.tex

(4) Build the PDF  
    latexmk -xelatex -output-directory=build main.tex

Users must not modify these scripts unless instructed.

------------------------------------------------------------
5. CI Build Pipeline
------------------------------------------------------------

GitHub Actions runs the build via:

    ./build_core.sh

Workflow file:

    .github/workflows/build-core.yml

The CI performs:

1. Checkout repository  
2. Install TeX Live + latexmk  
3. Make build_core.sh executable  
4. Run build_core.sh  
5. Upload build/main.pdf as artifact  

There are NO other CI pipelines.  
All YAML generators are called only through build_core.sh.

------------------------------------------------------------
6. Generated Files
------------------------------------------------------------

The following files are auto-generated:

- content/_auto_core_inputs.tex  
- any .tex file created from YAML by tools/generate_core_from_yaml.py  

Rules:

- Do NOT edit these by hand  
- Do NOT commit changes to auto_core_inputs.tex  
- Always regenerate via ./build_core.sh

------------------------------------------------------------
7. build/ directory
------------------------------------------------------------

The build directory contains:

build/main.pdf  
build/main.log  
build/main.aux  
build/main.toc  
build/main.bbl  
build/main.xdv  
build/logs/compile.log  

The directory is ignored by git except for the placeholder in build/logs/.

------------------------------------------------------------
8. Bibliography System
------------------------------------------------------------

Core uses:

- biblatex
- biber

Rules:

- Edit only bib/references.bib  
- Never modify main.bbl  
- Biber is invoked automatically by latexmk

------------------------------------------------------------
9. Troubleshooting
------------------------------------------------------------

Undefined references:

    ./build_core.sh
    latexmk may run multiple times automatically

Biber errors:

- Check bib/references.bib for invalid entries
- Ensure UTF-8 encoding

Fontspec / engine errors:

- Ensure XeLaTeX is used (pdflatex is not supported)

Polyglossia language errors:

- Ensure TeX Live is complete (texlive-full)

------------------------------------------------------------
10. Do-Not-Touch Zones
------------------------------------------------------------

The following files are protected under ARCHITECTURE FREEZE:

preamble.tex  
main.tex  
master_core_structure.yaml  
tools/*.py  
build_core.sh  
content/_auto_core_inputs.tex (generated)  

Modifying these incorrectly can break:

- rebuilds
- section ordering
- YAML integration
- CI pipelines
- Zenodo DOI captures

------------------------------------------------------------
11. Release Checklist
------------------------------------------------------------

Before tagging Core 1.1:

- [ ] ./build_core.sh builds successfully  
- [ ] CI pipeline is green  
- [ ] No undefined references  
- [ ] Biber runs cleanly  
- [ ] PDF identical locally and in CI  
- [ ] README.md references build_core.sh  
- [ ] .zenodo.json metadata verified  
- [ ] master_core_structure.yaml validated

This ensures reproducibility and archival stability.
