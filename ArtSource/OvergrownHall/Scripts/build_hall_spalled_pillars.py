"""Two broad shallow chips on approved square Tripo-derived shafts; keep module extents."""
import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'TripoReplacement/v019';OUT.mkdir(exist_ok=True)
rows=[]
for variant in ['A','B']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'TripoReplacement/v005/02_Pillar/clean.blend'))
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    cuts=[(-.345,-.10,1.05,.085,.17,.55),(.08,-.345,2.25,.19,.075,.37)] if variant=='A' else [(.345,.02,1.90,.080,.22,.46),(-.09,-.345,.60,.16,.07,.32)]
    for x,y,z,sx,sy,sz in cuts:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z));cut=bpy.context.object;cut.scale=(sx,sy,sz)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Broad shallow mineral spall','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    bm=bmesh.new();bm.from_mesh(obj.data);bad=sum(not e.is_manifold for e in bm.edges);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();assert bad==0
    obj.name='SM_OH_SpalledPillar'+variant;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(obj.name+'.blend')))
    rows.append(dict(mesh=obj.name,triangles=sum(len(p.vertices)-2 for p in obj.data.polygons),nonmanifold=bad,dimensions_m=list(obj.dimensions)))
(OUT/'pillar_meshes.json').write_text(json.dumps(rows,indent=2))
