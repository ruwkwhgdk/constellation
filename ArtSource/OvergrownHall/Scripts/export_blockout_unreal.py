"""Export category meshes with explicit UE axis reflection and measured bounds."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
detail=bool(globals().get('DETAIL_MODE',False))
OUT=Path(globals().get('SOURCE_DIR',ROOT/('Production/v001' if detail else 'Blockout/v002'))); FBX=OUT/'FBX'; FBX.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/globals().get('SOURCE_BLEND','overgrown_hall_detail.blend' if detail else 'overgrown_hall_blockout.blend')))
sources=[o for o in bpy.context.scene.objects if o.type=='MESH']
materials={m.name:dict(color=list(m.diffuse_color[:3]),roughness=m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value,metallic=m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value) for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')}
rows=[]
mirror_x=bool(globals().get('MATCH_CAMERA_HANDEDNESS',False))
for name,s in materials.items():
    s['surface_detail']=bpy.data.materials[name].get('surface_detail','')
    s['two_sided']=bool(bpy.data.materials[name].get('two_sided',False))
for category in sorted({o.name[:2] for o in sources}):
    group=[o for o in sources if o.name[:2]==category]
    vertices=[]; faces=[]; indices=[]; slots=[]; real=[]
    for o in group:
        offset=len(vertices)
        for v in o.data.vertices:
            p=o.matrix_world@v.co
            x=-p.x if mirror_x else p.x
            real.append([x*100,p.y*100,p.z*100]); vertices.append((x,-p.y,p.z))
        for poly in o.data.polygons:
            mat=o.data.materials[poly.material_index]
            if mat not in slots: slots.append(mat)
            order=poly.vertices if mirror_x else reversed(poly.vertices)
            faces.append(tuple(offset+i for i in order)); indices.append(slots.index(mat))
    name='SM_OH_Blockout_'+category
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],faces); mesh.update()
    for m in slots: mesh.materials.append(m)
    for p,i in zip(mesh.polygons,indices): p.material_index=i
    obj=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(FBX/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    lo=[min(v[i] for v in real) for i in range(3)]; hi=[max(v[i] for v in real) for i in range(3)]
    rows.append(dict(name=name,category=category,bounds_min_cm=lo,bounds_max_cm=hi,materials=[m.name for m in slots],collision=category not in ['16','17','18','19','21']))
    bpy.data.objects.remove(obj,do_unlink=True)
(OUT/'unreal_manifest.json').write_text(json.dumps(dict(assets=rows,materials=materials),indent=2))
print('HALL_FBX_EXPORTED',len(rows))
