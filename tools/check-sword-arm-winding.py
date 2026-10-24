"""Flag near-complete local axial turns; this is not an anatomy acceptance test."""
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
rows = json.loads(p.read_text())
report = {}
errors = []
for name in rows[0]['bones']:
    raw = [r['bones'][name]['twist'] for r in rows]
    turns = [raw[0]]
    for a, b in zip(raw, raw[1:]):
        turns.append(turns[-1] + (b-a+180) % 360 - 180)
    low, high = min(turns), max(turns)
    report[name] = {
        'unwrapped_range_degrees': high-low,
        'min_degrees': low, 'max_degrees': high,
        'min_frame': rows[turns.index(low)]['frame'],
        'max_frame': rows[turns.index(high)]['frame'],
    }
    if high-low > 300:
        errors.append(f'{name}: near-complete axial turn ({high-low:.2f} degrees)')
result = {'passed': not errors, 'errors': errors, 'bones': report,
          'scope': 'gross winding regression only; signed bends, fingers and actual mesh require visual review'}
p.with_name(p.stem+'-winding.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
sys.exit(bool(errors))
