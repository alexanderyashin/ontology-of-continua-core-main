from __future__ import annotations
import argparse
import json
import random
from pathlib import Path

CONTRACT_PATH = Path(__file__).with_name('simulation_contract.json')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run deterministic OC Core 1.3.1 toy simulation.')
    parser.add_argument('--seed', type=int, default=1103)
    parser.add_argument('--step-count', type=int, default=48)
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    rng = random.Random(args.seed)
    values = []
    state = 0.25
    for _ in range(args.step_count):
        state = max(0.0, min(1.0, state + (rng.random() - 0.5) * 0.08))
        values.append(round(state, 6))
    payload = {
        'simulation_id': contract['simulation_id'],
        'seed': args.seed,
        'trace_points': values,
        'stability_score': round(sum(values[-8:]) / max(1, len(values[-8:])), 6),
        'boundary_crossed': any(value > 0.92 or value < 0.08 for value in values),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
