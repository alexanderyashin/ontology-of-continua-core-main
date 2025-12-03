#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root (in case script is called from subdirs)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

echo "===[1/4] Generate missing .tex from YAML ====================="
python tools/generate_core_from_yaml.py

echo "===[2/4] Validate structure =================================="
python tools/validate_core_structure.py

echo "===[3/4] Generate auto include file =========================="
python tools/generate_auto_inputs.py

echo "===[4/4] Build PDF via latexmk ==============================="

# Ensure build directory exists
mkdir -p build

# ВАЖНО: используем xelatex, а не pdflatex, из-за fontspec
latexmk \
  -xelatex \
  -interaction=nonstopmode \
  -halt-on-error \
  -file-line-error \
  -output-directory="build" \
  main.tex
