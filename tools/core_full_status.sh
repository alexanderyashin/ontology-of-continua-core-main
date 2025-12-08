#!/usr/bin/env bash
# Core 1.1 — Full Status Check
# EA Orchestrator: strukturelle + Build-Diagnose in einem Lauf.

set -u  # bewusst NICHT -e, damit wir alles sammeln und am Ende reporten

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR" || exit 1

echo "============================================================"
echo " OC Core 1.1 — FULL STATUS REPORT"
echo " Repo root: $ROOT_DIR"
echo " Timestamp: $(date)"
echo "============================================================"
echo

# -----------------------------
# 1. Basic environment
# -----------------------------
echo "[1] Environment"
echo "----------------------------------------"
echo "- Python:" "$(python --version 2>&1 || echo 'python not found')"
echo "- latexmk:" "$(latexmk -v 2>&1 | head -n1 || echo 'latexmk not found')"
echo

# -----------------------------
# 2. Key files & structure
# -----------------------------
echo "[2] Key files & structure"
echo "----------------------------------------"

for f in \
  master_core_structure.yaml \
  main.tex \
  preamble.tex \
  build_core.sh \
  tools/generate_core_from_yaml.py \
  tools/generate_auto_inputs.py \
  tools/validate_core_structure.py \
  tools/fix_math_in_headings.py
do
  if [ -e "$f" ]; then
    echo "  [OK]   $f"
  else
    echo "  [MISS] $f"
  fi
done
echo

# -----------------------------
# 3. YAML sanity & preview
# -----------------------------
echo "[3] YAML sanity check"
echo "----------------------------------------"
if [ -e master_core_structure.yaml ]; then
  echo "- Top of YAML:"
  head -n 40 master_core_structure.yaml || true
  echo

  echo "- Quick YAML parse via Python:"
  python - << 'PYEOF' || echo "[YAML] ERROR while parsing"
import yaml
with open("master_core_structure.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
if data is None:
    print("[YAML] master_core_structure.yaml is empty")
else:
    print("[YAML] type:", type(data))
    if isinstance(data, dict):
        print("[YAML] keys:", list(data.keys()))
        root = data.get("root")
        if isinstance(root, dict):
            sections = root.get("sections", [])
            print("[YAML] root.sections:", len(sections), "entries")
PYEOF
else
  echo "[YAML] master_core_structure.yaml not found."
fi
echo

# -----------------------------
# 4. Scan for known local bugs
# -----------------------------
echo "[4] Scan for known LaTeX pitfalls"
echo "----------------------------------------"

echo "- Search for stray '</itemize' (HTML artefact):"
grep -R --line-number "</itemize" content || echo "  [OK] no '</itemize' found"
echo

echo "- Search for 'sec:k3-collapse' label/refs:"
grep -R --line-number "sec:k3-collapse" content || echo "  [INFO] no 'sec:k3-collapse' in content/"
echo

# -----------------------------
# 5. Regenerate structure (YAML → .tex)
# -----------------------------
echo "[5] Regenerate placeholders from YAML"
echo "----------------------------------------"
python tools/generate_core_from_yaml.py master_core_structure.yaml || echo "[WARN] generate_core_from_yaml.py reported an error"
echo

# -----------------------------
# 6. Validate structure
# -----------------------------
echo "[6] Validate core structure"
echo "----------------------------------------"
python tools/validate_core_structure.py || echo "[WARN] validate_core_structure.py reported issues"
echo

# -----------------------------
# 7. Regenerate auto inputs
# -----------------------------
echo "[7] Regenerate _auto_core_inputs.tex"
echo "----------------------------------------"
python tools/generate_auto_inputs.py --yaml master_core_structure.yaml --output content/_auto_core_inputs.tex || echo "[WARN] generate_auto_inputs.py reported an error"
echo

echo "- Preview of content/_auto_core_inputs.tex (first 40 lines):"
if [ -e content/_auto_core_inputs.tex ]; then
  head -n 40 content/_auto_core_inputs.tex || true
else
  echo "  [MISS] content/_auto_core_inputs.tex"
fi
echo

# -----------------------------
# 8. Full build via build_core.sh
# -----------------------------
echo "[8] Full build via build_core.sh"
echo "----------------------------------------"

if [ -x build_core.sh ]; then
  ./build_core.sh || echo "[WARN] build_core.sh returned non-zero exit code"
else
  echo "[MISS] build_core.sh not executable or not found"
fi
echo

echo "============================================================"
echo " FULL STATUS CHECK FINISHED"
echo " (Warnings above do NOT necessarily mean fatal errors.)"
echo "============================================================"
