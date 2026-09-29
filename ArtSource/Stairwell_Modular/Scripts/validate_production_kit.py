"""Independently measure final Blender mesh surfaces and rail cap interfaces."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Production/v001'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'stairwell_kit_review_v001.blend'))
manifest=json.loads((OUT/'reports/asset_manifest.json').read_text())
results={'status':'pass','assets':[],'rails':[],'tiles':[]}
def components(o):
    adj=[set() for v in o.data.vertices]
    for e in o.data.edges:
        a,b=e.vertices; adj[a].add(b); adj[b].add(a)
    left=set(range(len(adj))); groups=[]
    while left:
        todo=[left.pop()]; group=[]
        while todo:
            i=todo.pop(); group.append(i)
            for j in adj[i]:
                if j in left: left.remove(j); todo.append(j)
        groups.append([o.data.vertices[i].co for i in group])
    return groups
for row in manifest['assets']:
    o=bpy.data.objects[row['name']]; o.data.calc_loop_triangles(); tri=len(o.data.loop_triangles)
    assert tri==row['triangles'] and tri<=row['budget'],row['name']
    assert len(o.data.uv_layers)>0,row['name']
    assert (OUT/'renders'/(row['name']+'.png')).exists(),row['name']
    results['assets'].append({'name':row['name'],'triangles':tri,'uv':True})
    if row['id'] in ['06','20']:
        side_tiles=[]
        for g in components(o):
            dims=[max(v[k] for v in g)-min(v[k] for v in g) for k in range(3)]
            if abs(dims[0]-.006)<1e-5 and abs(dims[1]-.097)<1e-5:
                side_tiles.append(sum(g,Vector())/len(g))
        assert len(side_tiles)==144,(row['name'],len(side_tiles))
        inner=row['id']=='06'
        assert all((c.y<0 if inner else c.y>0) and abs(c.x-(.003 if inner else -.003))<1e-5 for c in side_tiles),('Corner finish facing',row['name'])
    if row['id'] in ['02','03','04']:
        top=[g for g in components(o) if abs(max(v.z for v in g))<1e-5 and abs(min(v.z for v in g)+.01)<1e-5]
        assert top,row['name']
        sizes=[]; centers=[]
        for g in top:
            dims=[max(v[k] for v in g)-min(v[k] for v in g) for k in range(3)]
            assert abs(dims[1]-.297)<1e-5,(row['name'],dims)
            assert abs(dims[0]-.297)<1e-5 or (row['name'].endswith('140') and abs(dims[0]-.097)<1e-5),(row['name'],dims)
            sizes.append([round(d*100,3) for d in dims]); centers.append(sum((v for v in g),Vector())/len(g))
        ys=sorted(set(round(p.y,5) for p in centers)); assert all(abs(b-a-.3)<1e-5 for a,b in zip(ys,ys[1:]))
        results['tiles'].append({'name':row['name'],'count':len(top),'measured_y_pitch_cm':30,'tile_body_sizes_cm':sorted(set(tuple(s) for s in sizes))})
    if row['id'] in ['09','10','11','12','17','18','19']:
        caps=[]
        for p in o.data.polygons:
            if len(p.vertices)!=12: continue
            vs=[o.data.vertices[i].co for i in p.vertices]; c=sum(vs,Vector())/12
            radius=sum((v-c).length for v in vs)/12
            if abs(radius-.02)<1e-5: caps.append((c,p.normal.copy()))
        assert len(caps)==4,(row['name'],len(caps))
        note=row['notes']; positions=[]
        for end in ['start','end']:
            expected=Vector(note[end]); tangent=Vector(note.get(end+'_tangent',note.get('tangent'))).normalized()
            for z in [0,.25]:
                pos=expected+Vector((0,0,z)); c,n=min(caps,key=lambda q:(q[0]-pos).length)
                gap=(c-pos).length*100; angle=math.degrees(math.acos(min(1,abs(n.normalized().dot(tangent)))))
                assert gap<.01 and angle<.1,(row['name'],gap,angle)
                positions.append({'end':end,'upper':z>0,'gap_cm':gap,'normal_error_deg':angle})
        results['rails'].append({'name':row['name'],'diameter_cm':4,'vertical_spacing_cm':25,'interfaces':positions})
assert {r['id'] for r in manifest['assets']}=={f'{i:02d}' for i in range(1,23)}
results['asset_count']=len(results['assets']); results['adopted_id_count']=22
(OUT/'reports/geometry_verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('KIT_GEOMETRY_VERIFIED',len(results['assets']),len(results['rails']),'rail variants')
