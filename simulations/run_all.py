from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = []
for runner in sorted(ROOT.glob('*/run_simulation.py')):
    proc = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True, check=False, timeout=120)
    payload = {'runner': str(runner.relative_to(ROOT)), 'returncode': proc.returncode}
    try:
        payload['stdout_json'] = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except Exception:
        payload['stdout_json'] = {'raw_stdout': proc.stdout.strip()}
    payload['stderr'] = proc.stderr.strip()
    RESULTS.append(payload)
print(json.dumps({'simulation_total': len(RESULTS), 'results': RESULTS}, ensure_ascii=False, indent=2))
