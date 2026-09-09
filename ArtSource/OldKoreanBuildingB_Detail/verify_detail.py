import bpy,json,bmesh
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'OldKoreanBuildingB_Detail.blend'))
bpy.context.view_layer.update()
lib=next(c for c in bpy.data.collections if c.name.startswith('MODULE_LIBRARY'))
expected={o.name:tuple(o.dimensions) for o in lib.objects}
source_bounds={o.name:[o.matrix_world@Vector(v) for v in o.bound_box] for o in bpy.data.objects if 'module' in o}
images=[]
for img in bpy.data.images:
    if img.name.startswith('T_KB_'):
        path=Path(bpy.path.abspath(img.filepath))
        assert path.is_file(),str(path)
        assert tuple(img.size)==(1024,1024),img.name
        images.append(path.name)
for c in bpy.data.collections:c.hide_viewport=False
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name,dims in expected.items():
    bpy.ops.import_scene.fbx(filepath=str(root/'Modules'/(name+'.fbx')))
    objects=list(bpy.context.selected_objects);ob=next(o for o in objects if o.name==name)
    assert all(abs(a-b)<.001 for a,b in zip(ob.dimensions,dims)),name
    for c in objects:
        if c.name.startswith('UCX_'):
            bm=bmesh.new();bm.from_mesh(c.data)
            assert all(e.is_manifold for e in bm.edges),c.name
            assert bm.calc_volume()>0,c.name
            bm.free()
    bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(root/'OldKoreanBuildingB_Detail_Assembly.fbx'))
meshes={o.name:o for o in bpy.context.selected_objects if not o.name.startswith('UCX_')}
assert len(meshes)==len(source_bounds)
for name,bounds in source_bounds.items():
    ob=meshes[name];actual=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    for axis in range(3):
        assert abs(min(v[axis] for v in bounds)-min(v[axis] for v in actual))<.001,name
        assert abs(max(v[axis] for v in bounds)-max(v[axis] for v in actual))<.001,name
report={'passed':True,'modules':len(expected),'assembly_instances':len(meshes),'texture_maps':images,
        'checks':['all texture files present at 1024x1024','all FBX modules reimport','dimensions retained','collision hulls closed','assembly world bounds retained'],
        'unreal_import':'Not performed for this detail review milestone'}
(root/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DETAIL_VERIFIED',len(expected),len(meshes),len(images))
