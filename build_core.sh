#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------
#  Ontology of Continua — Core Build Script (Full Replacement)
#  Features:
#     • YAML → .tex generation
#     • Structure validation
#     • Auto-input generation
#     • Full XeLaTeX + biber pipeline
#     • Bibliography mirroring (fixes biber path issues)
# ---------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "===[1/4] Generate missing .tex from YAML ====================="
python tools/generate_core_from_yaml.py master_core_structure.yaml

echo "===[2/4] Validate structure =================================="
if ! python tools/validate_core_structure.py; then
    echo "[WARN] Validator reported issues (missing files)."
    echo "       Продолжаю сборку, но лучше проверить лог."
fi

echo "===[2.5/4] Fix math in headings/captions ====================="
python tools/fix_math_in_headings.py

echo "===[3/4] Generate auto include file =========================="
python tools/generate_auto_inputs.py \
    --yaml master_core_structure.yaml \
    --output content/_auto_core_inputs.tex

echo "===[4/4] Build PDF (manual XeLaTeX + biber) =================="

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
    echo "[bib] WARNING: No .bib files found in bib/ directory"
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
    echo "[WARN] build/main.bcf not found – skipping biber!"
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

echo "==============================================================="
echo " Build finished successfully!"
echo " Output PDF: build/main.pdf"
echo "==============================================================="
