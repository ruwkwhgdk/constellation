"""Chip the approved floor module at its perimeter, keeping the central support surface."""
import bpy,bmesh,json
from pathlib import Path
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall')
OUT=ROOT/'TripoReplacement/v012';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'TripoReplacement/v005/13_Floor/clean.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for i,(x,y,r) in enumerate([(-.98,-.93,.20),(.96,.98,.19),(-.38,-1.02,.105),(.65,-1.02,.12)]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=(x,y,.07));cut=bpy.context.object;cut.scale=(1,1.2,5);cut.rotation_euler.z=.37+i*.41
    active(o);mod=o.modifiers.new('Weathered shoreline perimeter','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bm=bmesh.new();bm.from_mesh(o.data);boundary=sum(e.is_boundary for e in bm.edges);bad=sum(not e.is_manifold for e in bm.edges);bm.free();assert bad==0
active(o);o.name='SM_OH_ShoreSlab';bpy.context.preferences.filepaths.save_version=0
bpy.ops.export_scene.fbx(filepath=str(OUT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(o.name+'.blend')))
(OUT/'shore_mesh.json').write_text(json.dumps(dict(mesh=o.name,triangles=sum(len(p.vertices)-2 for p in o.data.polygons),boundary_edges=boundary,nonmanifold_edges=bad,dimensions_m=list(o.dimensions)),indent=2))
