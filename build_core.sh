#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------
#  Ontology of Continua — Core 1.4 public PDF build script
#  This public review payload contains pre-materialized TeX sources.
#  Only pre-materialized public sources are part of this review branch.
# ---------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

for required_cmd in python xelatex biber; do
    if ! command -v "$required_cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command not found in PATH: $required_cmd"
        exit 1
    fi
done

echo "===[1/1] Build PDF (manual XeLaTeX + biber) =================="

# ---------------------------------------------------------------
# Prepare build environment
# ---------------------------------------------------------------

mkdir -p build
mkdir -p build/bib

# Mirror bibliography files so that biber sees them correctly
if ls bib/*.bib >/dev/null 2>&1; then
    cp bib/*.bib build/bib/
    echo "[bib] Copied bibliography files into build/bib/"
else
    echo "ERROR: No .bib files found in bib/ directory"
    exit 1
fi

# Clean old auxiliary files
rm -f build/main.{aux,bcf,blg,bbl,log,run.xml} || true


# ---------------------------------------------------------------
# XeLaTeX pass 1 — generate .bcf
# ---------------------------------------------------------------
echo "---- [4a] First XeLaTeX run ----------------------------------"
xelatex \
    -interaction=nonstopmode \
    -halt-on-error \
    -file-line-error \
    -output-directory=build \
    main.tex


# ---------------------------------------------------------------
# Biber pass — build bibliography
# ---------------------------------------------------------------
if [ -f build/main.bcf ]; then
    echo "---- [4b] Run biber ------------------------------------------"
    (
        cd build
        biber main
    )
else
    echo "ERROR: build/main.bcf not found after first XeLaTeX pass"
    exit 1
fi


# ---------------------------------------------------------------
# XeLaTeX pass 2 — resolve citations, references
# ---------------------------------------------------------------
echo "---- [4c] Second XeLaTeX run ---------------------------------"
xelatex \
    -interaction=nonstopmode \
    -halt-on-error \
    -file-line-error \
    -output-directory=build \
    main.tex


# ---------------------------------------------------------------
# XeLaTeX pass 3 — stabilize TOC, crossrefs, links
# ---------------------------------------------------------------
echo "---- [4d] Third XeLaTeX run (stabilize TOC/refs) -------------"
xelatex \
    -interaction=nonstopmode \
    -halt-on-error \
    -file-line-error \
    -output-directory=build \
    main.tex

if [ ! -f build/main.pdf ]; then
    echo "ERROR: build/main.pdf was not produced"
    exit 1
fi

echo "==============================================================="
echo " Build finished successfully!"
echo " Output PDF: build/main.pdf"
echo "==============================================================="
