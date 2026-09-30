import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'Production/v001'
bpy.ops.wm.open_mainfile(filepath=str(O/'entrance_kit.blend'))
s=bpy.context.scene
manifest=json.loads((O/'manifest.json').read_text())
for name in [r['name'] for r in manifest['assets']]+['SM_SE_IslandWithStairwell']:
    bpy.ops.object.select_all(action='DESELECT')
    group=[o for o in s.objects if o.name==name or o.name.startswith('UCX_'+name+'_')]
    for o in group:
        o.hide_viewport=False;o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=group[0]
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    mesh=bpy.data.objects[name]
    for row in manifest['assets']:
        if row['name']==name:row['dimensions_cm']=[100*(max(v.co[j] for v in mesh.data.vertices)-min(v.co[j] for v in mesh.data.vertices)) for j in range(3)]
    for o in group:
        for v in o.data.vertices:v.co*=100
        o.location*=100
        o.data.update()
    bpy.context.view_layer.update()
    s.unit_settings.scale_length=.01
    bpy.ops.export_scene.fbx(filepath=str(O/'FBX'/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    for o in group:
        for v in o.data.vertices:v.co/=100
        o.location/=100
        o.data.update()
    s.unit_settings.scale_length=1
    bpy.context.view_layer.update()
(O/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('REEXPORT_CM_OK')
