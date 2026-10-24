import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
out={}
for label,file in [('old',P/'OldSlimeReference.fbx'),('new',P.parent/'Production/SK_Slime_Liquid_Idle.fbx')]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(file))
 out[label]=[]
 for o in bpy.context.scene.objects:
  row={'name':o.name,'type':o.type,'matrix':[list(x) for x in o.matrix_world],'dimensions':list(o.dimensions)}
  if o.type=='ARMATURE':row['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'matrix':[list(x) for x in b.matrix_local],'head':list(b.head_local),'tail':list(b.tail_local)} for b in o.data.bones]
  if o.type=='MESH':row['bounds']=[[min((o.matrix_world@v.co)[i] for v in o.data.vertices),max((o.matrix_world@v.co)[i] for v in o.data.vertices)] for i in range(3)]
  out[label].append(row)
(P/'bind-inspection.json').write_text(json.dumps(out,indent=2))
