#!/usr/bin/env bash
set -euo pipefail

# Определяем корень репозитория (папка, где лежит этот скрипт)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "===[1/4] Generate missing .tex from YAML ====================="
python tools/generate_core_from_yaml.py master_core_structure.yaml

echo "===[2/4] Validate structure =================================="
# Если валидатор упадёт, сборку можно либо останавливать, либо продолжать.
# Сейчас: только предупреждаем, но не роняем билд.
if ! python tools/validate_core_structure.py; then
    echo "[WARN] Validator reported issues (missing files)."
    echo "       Продолжаю сборку, но лучше посмотреть выше."
fi

echo "===[2.5/4] Fix math in headings/captions ====================="
python tools/fix_math_in_headings.py

echo "===[3/4] Generate auto include file =========================="
python tools/generate_auto_inputs.py --yaml master_core_structure.yaml --output content/_auto_core_inputs.tex

echo "===[4/4] Build PDF via latexmk ==============================="

# Убедиться, что каталог build существует
mkdir -p build

# ВАЖНО: используем xelatex, а не pdflatex, из-за fontspec
latexmk \
  -g \
  -xelatex \
  -interaction=nonstopmode \
  -halt-on-error \
  -file-line-error \
  -output-directory="build" \
  main.tex
