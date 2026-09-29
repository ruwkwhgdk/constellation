import bpy, json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]/'Models'/'14_Door'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'door14_review_v001.blend'))
rows=[]
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    adj=[set() for v in o.data.vertices]
    for e in o.data.edges:
        a,b=e.vertices; adj[a].add(b); adj[b].add(a)
    unseen=set(range(len(adj)))
    while unseen:
        stack=[unseen.pop()]; group=[]
        while stack:
            i=stack.pop(); group.append(i)
            for j in adj[i]:
                if j in unseen: unseen.remove(j); stack.append(j)
        pts=[o.matrix_world@o.data.vertices[i].co for i in group]
        low=[min(p[k] for p in pts)*100 for k in range(3)]
        high=[max(p[k] for p in pts)*100 for k in range(3)]
        rows.append(dict(vertices=len(group),min_cm=low,max_cm=high))
(OUT/'parts_audit.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
