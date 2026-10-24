import bpy,json
from pathlib import Path
P=Path(__file__).parent
bpy.ops.import_scene.fbx(filepath=str(P/'Source/SM_GymDoorLeaf.fbx'))
report=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 slots=[]
 for i,m in enumerate(o.data.materials):
  faces=[p for p in o.data.polygons if p.material_index==i]
  coords=[o.data.vertices[v].co[:] for f in faces for v in f.vertices]
  slots.append({'index':i,'name':m.name,'faces':len(faces),'min':[min(v[k] for v in coords) for k in range(3)] if coords else [],'max':[max(v[k] for v in coords) for k in range(3)] if coords else []})
 report.append({'object':o.name,'transform':str(o.matrix_world),'verts':len(o.data.vertices),'faces':len(o.data.polygons),'uv':[x.name for x in o.data.uv_layers],'slots':slots})
(P/'Reports/blender-inspect.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Source/gym_door_original.blend'))
