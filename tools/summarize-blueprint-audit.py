"""Condense exported graph text for review without interpreting strings as code."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'Saved/ProjectAudit/20261001'
rows = []
for file in (root / 'graphs').rglob('*.txt'):
    graphs = []
    for section in file.read_text(encoding='utf-8').split('\nGRAPH ')[1:]:
        name, _, body = section.partition('\n')
        nodes = []
        for block in re.findall(r'^Begin Object Class=.*?^End Object', body, re.M | re.S):
            head = re.match(r'Begin Object Class=(\S+) Name="([^"]+)"', block)
            if not head:
                continue
            cls, node_name = head.groups()
            title = re.search(r'(?:FunctionReference|VariableReference|EventReference)=.*?MemberName="([^"]+)"', block)
            special = re.search(r'(?:CustomFunctionName|TimelineName)="?([^"\r\n]+)', block)
            node = {'id': node_name, 'type': cls.rsplit('.', 1)[-1],
                    'name': title[1] if title else special[1] if special else '', 'pins': []}
            for line in block.splitlines():
                if 'CustomProperties Pin (' not in line:
                    continue
                def field(key):
                    m = re.search(re.escape(key) + r'="([^"]*)"', line)
                    return m[1] if m else ''
                links = re.search(r'LinkedTo=\((.*?)\)', line)
                pin = {'name': field('PinName'), 'type': field('PinType.PinCategory'),
                       'out': 'Direction="EGPD_Output"' in line}
                if links:
                    pin['links'] = links[1].rstrip(',').split(',')
                default = field('DefaultValue') or field('DefaultObject')
                if default:
                    pin['default'] = default
                if 'bOrphanedPin=True' in line:
                    pin['orphan'] = True
                node['pins'].append(pin)
            nodes.append(node)
        graphs.append({'name': name, 'nodes': nodes})
    row = {'asset': str(file.relative_to(root / 'graphs')), 'graphs': graphs}
    rows.append(row)
(root / 'compact-graphs.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
counts = [(sum(len(g['nodes']) for g in r['graphs']), r['asset']) for r in rows]
print('Assets', len(rows), 'Graphs', sum(len(r['graphs']) for r in rows), 'Nodes', sum(c[0] for c in counts))
for count, name in sorted(counts, reverse=True)[:35]:
    print(count, name)
orphans = [(r['asset'], g['name'], n['id'], p['name']) for r in rows for g in r['graphs'] for n in g['nodes'] for p in n['pins'] if p.get('orphan')]
print('Orphan pins:', len(orphans))
for item in orphans[:25]:
    print(item)
