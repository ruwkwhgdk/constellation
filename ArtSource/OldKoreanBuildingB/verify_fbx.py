"""Independently import exported FBXs and compare against saved Blender meshes."""
import bpy, json, bmesh
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'OldKoreanBuildingB_Blockout.blend'))
lib=next(c for c in bpy.data.collections if c.name.startswith('MODULE_LIBRARY'))
expected={o.name:tuple(o.dimensions) for o in lib.objects}
bpy.context.view_layer.update()
assembly_bounds={o.name:[o.matrix_world@Vector(c) for c in o.bound_box] for o in bpy.data.objects if 'module' in o}
for c in bpy.data.collections: c.hide_viewport=False
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
results=[]
for name,dims in expected.items():
    bpy.ops.import_scene.fbx(filepath=str(root/'Modules'/(name+'.fbx')))
    objects=list(bpy.context.selected_objects)
    mesh=next(o for o in objects if o.name==name)
    assert all(abs(a-b)<.0001 for a,b in zip(mesh.dimensions,dims)),(name,tuple(mesh.dimensions),dims)
    assert mesh.data.uv_layers, name+' UV missing'
    hulls=[o for o in objects if o.name.startswith('UCX_')]
    for hull in hulls:
        bm=bmesh.new();bm.from_mesh(hull.data)
        assert all(e.is_manifold for e in bm.edges),hull.name+' not closed'
        assert bm.calc_volume()>0,hull.name+' incorrect winding'
        bm.free()
    results.append({'module':name,'dimensions_m':list(dims),'closed_collision_hulls':len(hulls)})
    bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(root/'OldKoreanBuildingB_Assembly.fbx'))
manifest=json.loads((root/'assembly.json').read_text())
meshes={o.name:o for o in bpy.context.selected_objects if not o.name.startswith('UCX_')}
assert len(meshes)==len(manifest['placements'])
for p in manifest['placements']:
    ob=meshes[p['name']]
    assert (ob.location-Vector(p['location_m'])).length<.0001, p['name']+' location changed'
    actual=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    original=assembly_bounds[p['name']]
    for axis in range(3):
        assert abs(min(v[axis] for v in actual)-min(v[axis] for v in original))<.0001, p['name']+' min bounds'
        assert abs(max(v[axis] for v in actual)-max(v[axis] for v in original))<.0001, p['name']+' max bounds'
report={'passed':True,'modules':len(results),'assembly_instances':len(meshes),'module_results':results,
        'checks':['FBX import succeeds','Module dimensions match saved source in metres','UV layer retained','UCX hulls closed and positive-volume','Assembly placement translations retained'],
        'unreal_import_verified':False}
(root/'fbx_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FBX_VERIFIED',len(results),'modules',len(meshes),'instances')
