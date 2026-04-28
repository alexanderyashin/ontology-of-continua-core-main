from pathlib import Path
import json

packet = json.loads((Path(__file__).with_name('VALIDATION_PACKET.json')).read_text(encoding='utf-8'))
print(json.dumps({'lane': packet['lane'], 'result_verdict': packet['result_verdict'], 'remaining_blocker': packet['remaining_blocker']}, indent=2))
