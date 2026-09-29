import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
src='C:/Users/User/Desktop/Portfolio/Project Constellation/modeling/player_heroine/Player_Heroine.fbx'
bpy.ops.import_scene.fbx(filepath=src,use_anim=False)
ref=list(bpy.context.scene.objects)
def describe(objects):
 out=[]
 for o in objects:
  d={'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler)}
  if o.type=='MESH':
   pts=[o.matrix_world@v.co for v in o.data.vertices]
   d.update(vertices=len(pts),bounds=[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)],materials=[m.name if m else None for m in o.data.materials],modifiers=[(m.name,m.type) for m in o.modifiers])
  if o.type=='ARMATURE':d['bones']={b.name:{'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local)} for b in o.data.bones}
  out.append(d)
 return out
report={'reference':describe(ref)}
for o in ref:o.name='REF_'+o.name
with bpy.data.libraries.load(str(P.parent/'RigContourFix/Delivery/Heroine_GameSkeleton.blend')) as (s,d):d.objects=[n for n in s.objects if n=='Heroine_GameSkeleton' or n.endswith('_Game')]
for o in d.objects:bpy.context.scene.collection.objects.link(o)
report['new']=describe(d.objects)
(P/'model_inspection.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'comparison_source.blend'))
