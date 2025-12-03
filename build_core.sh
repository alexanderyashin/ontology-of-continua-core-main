#!/usr/bin/env bash
set -euo pipefail

# Определяем корень репозитория (папка, где лежит этот скрипт)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "===[1/4] Generate missing .tex from YAML ====================="
python tools/generate_core_from_yaml.py

echo "===[2/4] Validate structure =================================="
# Если валидатор упадёт, сборку можно либо останавливать, либо продолжать.
# Сейчас: только предупреждаем, но не роняем билд.
if ! python tools/validate_core_structure.py; then
    echo "[WARN] Validator reported issues (missing files)."
    echo "       Продолжаю сборку, но лучше посмотреть выше."
fi

echo "===[3/4] Generate auto include file =========================="
python tools/generate_inputs_from_yaml.py

echo "===[4/4] Build PDF via latexmk ==============================="
mkdir -p build
latexmk -pdf -interaction=nonstopmode -halt-on-error -output-directory=build main.tex

echo
echo "==============================================================="
echo " Core build finished."
echo " PDF: build/main.pdf"
echo "==============================================================="
