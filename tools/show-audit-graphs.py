import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rows = json.loads((root / 'Saved/ProjectAudit/20261001/compact-graphs.json').read_text(encoding='utf-8'))
for row in rows:
    if not any(name.lower() in row['asset'].lower() for name in sys.argv[1:]):
        continue
    print('\nASSET', row['asset'])
    for graph in row['graphs']:
        print('GRAPH', graph['name'].split(':')[-1])
        for node in graph['nodes']:
            if node['type'] == 'K2Node_Knot':
                continue
            pins = [(p['name'], p.get('default'), [v.split()[0] for v in p.get('links', [])]) for p in node['pins']]
            print(node['id'], node['type'].removeprefix('K2Node_'), node['name'], pins)
