import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Scene/v001/FBX/SM_OH_Blockout_21.fbx'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');o.data.update()
normals=[(o.matrix_world.to_3x3()@p.normal).normalized().z for p in o.data.polygons]
report=dict(faces=len(normals),min_normal_z=min(normals),max_normal_z=max(normals),matrix=[list(v) for v in o.matrix_world])
(ROOT/'TripoReplacement/v006/water_geometry.json').write_text(json.dumps(report,indent=2));print('WATER_NORMALS',report)
