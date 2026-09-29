import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parents[1]; OUT=Path(globals().get('FLOCK_OUT',BASE/'Bird/Flock_v001'))
bpy.ops.wm.open_mainfile(filepath=str(globals().get('HALL_BLEND',BASE/'Production/v001/overgrown_hall_detail.blend')))
scene=bpy.context.scene; bpy.context.preferences.filepaths.save_version=0
routes=json.loads((OUT/'routes.json').read_text())
# Check the real source architecture surfaces, beyond the coarse corridor limits.
vertices=[]; polygons=[]
for o in scene.objects:
    if o.type!='MESH' or o.name[:2] in ['16','17','18','19','20','21','24']: continue
    offset=len(vertices); vertices.extend([o.matrix_world@v.co for v in o.data.vertices])
    polygons.extend([tuple(offset+i for i in p.vertices) for p in o.data.polygons])
bvh=BVHTree.FromPolygons(vertices,polygons)
nearest=min(bvh.find_nearest(Vector(s['position_cm'])/100)[3] for row in routes['birds'] for s in row['samples'])
assert nearest>.5,nearest
with bpy.data.libraries.load(str(BASE/'Bird/Tripo_Rig_v001/pigeon_rig.blend'),link=False) as (src,dst):
    dst.objects=['RIG_OH_Pigeon_Tripo','SK_OH_Pigeon']
rig,mesh=dst.objects
for o in [rig,mesh]: scene.collection.objects.link(o)
for i,row in enumerate(routes['birds']):
    r=rig.copy(); r.data=rig.data.copy(); scene.collection.objects.link(r)
    m=mesh.copy(); scene.collection.objects.link(m); m.parent=r
    for mod in m.modifiers:
        if mod.type=='ARMATURE': mod.object=r
    action=rig.animation_data.action.copy(); r.animation_data_create(); r.animation_data.action=action
    s=row['samples'][0]; r.location=Vector(s['position_cm'])/100; r.rotation_euler.z=math.radians(s['rotation_xyz'][2]+180)
    # This still uses the same 0.5s fly loop; shift the action keys for phase.
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points: key.co.x-=row['phase_offset_frames']
                    fc.modifiers.new('CYCLES')
bpy.data.objects.remove(mesh,do_unlink=True); bpy.data.objects.remove(rig,do_unlink=True)
scene.frame_set(1); scene.camera=bpy.data.objects['ReferenceCamera']
scene.render.resolution_x=1200; scene.render.resolution_y=640; scene.render.resolution_percentage=100; scene.cycles.samples=20
scene.render.filepath=str(OUT/'reference.png'); bpy.ops.render.render(write_still=True)
(OUT/'spatial_verification.json').write_text(json.dumps(dict(minimum_architecture_surface_distance_m=nearest,samples=12*121,minimum_bird_center_distance_cm=routes['minimum_center_distance_cm'],scope='sampled paths against source architecture; not runtime collision avoidance'),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'flock_layout.blend'))
