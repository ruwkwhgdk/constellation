import bpy,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'TripoReplacement/v001'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'Scene/v001/overgrown_hall_layout.blend'))
verts=[]; faces=[]; indices=[]; mats=[]; placements=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH' or not o.name.startswith('02_'): continue
    if o.name.startswith('02_Shaft'):
        ps=[o.matrix_world@v.co for v in o.data.vertices]
        x=(min(p.x for p in ps)+max(p.x for p in ps))/2
        y=(min(p.y for p in ps)+max(p.y for p in ps))/2
        z=min(p.z for p in ps)
        for j in range(3): placements.append([-100*x,100*y,100*(z+j*3)])
        continue
    offset=len(verts)
    for v in o.data.vertices:
        p=o.matrix_world@v.co; verts.append((-p.x,-p.y,p.z))
    for p in o.data.polygons:
        mat=o.data.materials[p.material_index]
        if mat not in mats:mats.append(mat)
        faces.append(tuple(offset+i for i in p.vertices)); indices.append(mats.index(mat))
mesh=bpy.data.meshes.new('SM_OH_RemainingPiers'); mesh.from_pydata(verts,[],faces); mesh.update()
for m in mats:mesh.materials.append(m)
for p,i in zip(mesh.polygons,indices):p.material_index=i
o=bpy.data.objects.new(mesh.name,mesh); bpy.context.scene.collection.objects.link(o)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(OUT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False)
(OUT/'placements.json').write_text(json.dumps(dict(pillar_segments=placements,remaining_materials=[m.name for m in mats]),indent=2))
