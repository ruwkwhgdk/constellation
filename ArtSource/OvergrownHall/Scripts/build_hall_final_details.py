"""v013: source-derived rear wall, window and beam breaks with closed fracture faces."""
import bpy,bmesh,json
from pathlib import Path
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall')
OUT=ROOT/'TripoReplacement/v013';OUT.mkdir(exist_ok=True)
specs=[('05','Wall',[(.90,1.48,.58),(1.42,.90,.25)]),('06','WindowLower',[(.88,3.91,.76),(-.18,2.68,.42)]),('07','WindowArch',[(.93,.94,.57)]),('09','Beam',[(1.87,.18,.58)])]
rows=[]
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for key,name,cuts in specs:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'TripoReplacement/v005/{key}_{name}/clean.blend'))
    o=next(o for o in bpy.context.scene.objects if o.type=='MESH');active(o)
    for i,(x,z,r) in enumerate(cuts):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=(x,0,z));cut=bpy.context.object;cut.scale=(1,4,1.12);cut.rotation_euler=(0,.19,.25+i*.63)
        active(o);mod=o.modifiers.new('Open weathered break','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);boundary=sum(e.is_boundary for e in bm.edges);bm.free();assert bad==0,(key,bad)
    active(o);o.name='SM_OH_RearBroken_'+key;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(o.name+'.blend')))
    rows.append(dict(id=key,mesh=o.name,triangles=sum(len(p.vertices)-2 for p in o.data.polygons),boundary_edges=boundary,nonmanifold_edges=bad,dimensions_m=list(o.dimensions)))
(OUT/'assets.json').write_text(json.dumps(rows,indent=2));print('FINAL_DETAIL_ASSETS',rows)
