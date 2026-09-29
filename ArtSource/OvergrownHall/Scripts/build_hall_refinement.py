"""Tripo-derived crowns, chipped architectural variants and a shallow water outline."""
import bpy,bmesh,math,random,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall');OUT=ROOT/'TripoReplacement/v009';OUT.mkdir(exist_ok=True)
rows=[]
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def export(o,name,kind):
    o.name=name;activate(o);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
    rows.append(dict(mesh=name,kind=kind,triangles=sum(len(f.vertices)-2 for f in o.data.polygons)))

# Reuse the approved Tripo canopy and its UV, with the conspicuous trunk removed.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'TripoReplacement/v008/19_Tree/soft.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');activate(o)
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<3.25],context='VERTS');bm.to_mesh(o.data);bm.free()
for v in o.data.vertices:v.co.z-=3.25
mod=o.modifiers.new('Distant crown budget','DECIMATE');mod.ratio=.65;bpy.ops.object.modifier_apply(modifier=mod.name)
export(o,'SM_OH_TripoCrown','crown')

for key,name in [('04','SideArch'),('05','Wall')]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'TripoReplacement/v005/{key}_{name}/clean.blend'))
    o=next(o for o in bpy.context.scene.objects if o.type=='MESH');activate(o)
    xs=[v.co.x for v in o.data.vertices];zs=[v.co.z for v in o.data.vertices];right=max(xs);top=max(zs)
    rng=random.Random(int(key)+9)
    # Actual missing chunks at selected outer edges, not damage on every repeated module.
    for i,(x,z,r) in enumerate([(right,top*.78,.24),(right-.10,top-.07,.30),(-right,top*.38,.16)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=(x,0,z));cut=bpy.context.object;cut.scale=(1,2.5,1.7);cut.rotation_euler=(.4,.2,i*.6)
        activate(o);m=o.modifiers.new('Missing stone chunk','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)
    export(o,'SM_OH_Chipped_'+key, 'chip'+key)

# An irregular shallow sheet, geometrically flat for the existing planar reflection.
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[(0,-7,.022)];edges=[]
for i in range(80):
    angle=2*math.pi*i/80
    x=6.25*math.cos(angle);y=7+8.6*math.sin(angle)
    x*=1+.025*math.sin(angle*11);y+=.18*math.sin(angle*13)
    # Existing scene exporter uses Blender -Y for Unreal +Y.
    verts.append((x,-y,.022))
faces=[(0,1+(i+1)%80,1+i) for i in range(80)]
mesh=bpy.data.meshes.new('WaterOutline');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Water',mesh);bpy.context.collection.objects.link(o)
export(o,'SM_OH_ShallowOutline','water')
(OUT/'assets.json').write_text(json.dumps(rows,indent=2));print('HALL_REFINEMENT_ASSETS',rows)
