import bpy,json
from pathlib import Path
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall');rows=[]
for path in [ROOT/'Scene/v001/FBX/SM_OH_Blockout_21.fbx',ROOT/'TripoReplacement/v009/SM_OH_ShallowOutline.fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path))
    o=next(o for o in bpy.context.scene.objects if o.type=='MESH');o.data.update()
    co=[o.matrix_world@v.co for v in o.data.vertices]
    rows.append(dict(file=str(path),min=[min(v[i] for v in co) for i in range(3)],max=[max(v[i] for v in co) for i in range(3)],normal_z=[min((o.matrix_world.to_3x3()@p.normal).normalized().z for p in o.data.polygons),max((o.matrix_world.to_3x3()@p.normal).normalized().z for p in o.data.polygons)]))
(ROOT/'TripoReplacement/v009/water_source_audit.json').write_text(json.dumps(rows,indent=2));print(rows)
