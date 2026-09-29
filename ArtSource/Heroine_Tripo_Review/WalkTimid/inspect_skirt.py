import bpy,json
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Walk_Timid.blend'))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
r=bpy.data.objects['Heroine_AnimationRig'];out={}
for i in range(8):
 n=f'DEF-skirt_{i:02}.02';p=r.pose.bones[n];out[n]={'head':list(r.matrix_world@p.head),'tail':list(r.matrix_world@p.tail)}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.name.startswith('WGT'):continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();verts=[o.matrix_world@v.co for v in m.vertices]
 for slot in o.material_slots:
  if slot.material: print(o.name,slot.material.name)
 for mi,slot in enumerate(o.material_slots):
  if not slot.material or ('Skirt' not in slot.material.name and 'Skin' not in slot.material.name):continue
  ids={i for p in m.polygons if p.material_index==mi for i in p.vertices}
  if slot.material.name=='M_Skirt':print('SKIRT_COORDS',min(o.data.vertices[i].co.z for i in ids),max(o.data.vertices[i].co.z for i in ids),'MATRIX',o.matrix_world)
  rows={}
  for z in [.76,.78,.8,.82,.84,.86]:
   vs=[verts[i] for i in ids if abs(verts[i].z-z)<.01]
   if vs:rows[str(z)]={'x':[min(v.x for v in vs),max(v.x for v in vs)],'y':[min(v.y for v in vs),max(v.y for v in vs)]}
  out[o.name+'/'+slot.material.name]=rows
 if o.name=='Heroine_DetailFinish2':
  skirtid=next(i for i,s in enumerate(o.material_slots) if s.material.name=='M_Skirt')
  skinid=next(i for i,s in enumerate(o.material_slots) if s.material.name=='M_Skin')
  skirtpolys=[tuple(p.vertices) for p in m.polygons if p.material_index==skirtid]
  tree=BVHTree.FromPolygons(verts,skirtpolys)
  ids={i for p in m.polygons if p.material_index==skinid for i in p.vertices}
  bad=[]
  for i in ids:
   v=verts[i]
   if abs(v.x)>.14 or not .79<v.z<.87:continue
   loc,normal,face,dist=tree.find_nearest(v)
   signed=(v-loc).dot(normal) * (1 if normal.x*loc.x+normal.y*loc.y>0 else -1)
   if signed>.002:bad.append({'index':i,'pos':list(v),'closest':list(loc),'signed':signed,'groups':[(o.vertex_groups[g.group].name,g.weight) for g in o.data.vertices[i].groups],'cloth_weights':[[(o.vertex_groups[g.group].name,g.weight) for g in o.data.vertices[j].groups] for j in skirtpolys[face]]})
  out['outside_skin']=sorted(bad,key=lambda x:-x['signed'])[:20]
 ev.to_mesh_clear()
(P/'skirt_inspection.json').write_text(json.dumps(out,indent=2))
