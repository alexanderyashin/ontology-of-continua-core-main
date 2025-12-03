#!/usr/bin/env bash
set -euo pipefail

# Определяем корень репозитория (папка, где лежит этот скрипт)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "===[1/4] Generate missing .tex from YAML ====================="
python tools/generate_core_from_yaml.py

echo "===[2/4] Validate structure =================================="
# Если валидатор упадёт, сборку можно либо останавливать, либо продолжать.
# Сейчас: только предупреждаем, но НЕ роняем билд.
if ! python tools/validate_core_structure.py; then
    echo "[WARN] Validator reported issues (missing or extra files)."
    echo "       Продолжаю сборку, но лучше посмотреть лог выше."
fi

echo "===[3/4] Generate auto include file =========================="
python tools/generate_auto_inputs.py

echo "===[4/4] Build PDF via latexmk ==============================="

# Гарантируем, что каталог для билда существует
mkdir -p build

# Проверяем, установлен ли latexmk (локально в Codespaces может отсутствовать)
if ! command -v latexmk >/dev/null 2>&1; then
    echo "ERROR: 'latexmk' не найден в PATH."
    echo "  Варианты:"
    echo "    • Локально / Codespaces: установить latexmk + TeX, напр.:"
    echo "        sudo apt-get update && sudo apt-get install -y latexmk texlive-full"
    echo "    • Или не трогать локальный билд и собирать PDF через GitHub Actions."
    exit 1
fi

# ВАЖНО: используем xelatex, а не pdflatex, из-за fontspec в preamble.tex
latexmk \
  -xelatex \
  -interaction=nonstopmode \
  -halt-on-error \
  -file-line-error \
  -output-directory="build" \
  main.tex

echo
echo "Готово. Если ошибок нет, PDF лежит здесь: build/main.pdf"
