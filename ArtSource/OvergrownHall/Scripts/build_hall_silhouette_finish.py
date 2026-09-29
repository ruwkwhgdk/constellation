"""Large asymmetric breaks in maintained Tripo-derived side arches and roof trusses."""
import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'TripoReplacement/v021';OUT.mkdir(exist_ok=True);rows=[]
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for variant in ['A','B','C','Truss']:
    folder='10_RoofTruss' if variant=='Truss' else '04_SideArch'
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'TripoReplacement/v005'/folder/'clean.blend'))
    o=next(o for o in bpy.context.scene.objects if o.type=='MESH');active(o)
    if variant=='Truss':cuts=[(.25,0,.14,4.3,1,.40)]
    elif variant=='A':cuts=[(.70,0,6.05,1.25,3,1.18), (1.35,0,4.82,.60,3,.7)]
    elif variant=='B':cuts=[(-.65,0,6.18,1.35,3,1.03),(-1.40,0,4.9,.52,3,.65)]
    else:cuts=[(0,0,6.68,1.28,3,.70),(.90,0,5.90,.5,3,.65)]
    for i,(x,y,z,sx,sy,sz) in enumerate(cuts):
        if variant=='Truss':bpy.ops.mesh.primitive_cube_add(size=2,location=(x,y,z))
        else:bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z))
        cut=bpy.context.object;cut.scale=(sx,sy,sz)
        if variant!='Truss':cut.rotation_euler=(.08,.13,.24+i*.5)
        active(o);mod=o.modifiers.new('Large asymmetric fracture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    bpy.context.view_layer.update()
    if variant=='Truss':assert o.dimensions.y<.3 and o.dimensions.z<2.1,list(o.dimensions)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free();assert bad==0,(variant,bad)
    active(o);o.name='SM_OH_Fractured'+('RoofTruss' if variant=='Truss' else 'SideArch'+variant);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(o.name+'.blend')))
    rows.append(dict(mesh=o.name,kind='truss' if variant=='Truss' else 'arch',triangles=sum(len(p.vertices)-2 for p in o.data.polygons),nonmanifold=bad,dimensions_m=list(o.dimensions)))
(OUT/'assets.json').write_text(json.dumps(rows,indent=2));print('HALL_SILHOUETTE_MESHES',rows)
