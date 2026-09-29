import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'TripoReplacement/v024';OUT.mkdir(exist_ok=True);rows=[]
for variant in ['A','B']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'TripoReplacement/v005/05_Wall/clean.blend'));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    o.scale.x*=4/o.dimensions.x;o.scale.z*=4.4/o.dimensions.z;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    # Source is joined overlapping trim/body solids. Union them before subtracting fractures.
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
    parts=[p for p in bpy.context.scene.objects if p.type=='MESH'];o=max(parts,key=lambda p:p.dimensions.x*p.dimensions.y*p.dimensions.z)
    for p in parts:
        bm=bmesh.new();bm.from_mesh(p.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(p.data);bm.free()
    for part in parts:
        if part==o:continue
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Union source trim and wall','BOOLEAN');m.operation='UNION';m.solver='EXACT';m.object=part;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(part,do_unlink=True)
    for x,z,sx,sz in ([(-.30,-.15,1.65,.80)] if variant=='A' else [(.25,-.05,1.45,.95)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,0,z));cut=bpy.context.object;cut.scale=(sx,2,sz);cut.rotation_euler=(.04,.10,.15)
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Broken lower spandrel edge','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)
    bpy.context.view_layer.update();assert o.dimensions.z>4.2 and min(v.co.z for v in o.data.vertices)<.1,tuple(o.dimensions)
    bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);assert bad==0;bm.free();o.name='SM_OH_UpperWallInfill'+variant;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(o.name+'.blend')))
    rows.append(dict(mesh=o.name,triangles=sum(len(p.vertices)-2 for p in o.data.polygons),nonmanifold=bad))
(OUT/'upper_wall_assets.json').write_text(json.dumps(rows,indent=2));print(rows)
