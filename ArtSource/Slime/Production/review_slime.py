"""Fresh-process artifact verification and complete 24 fps review renders."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
S=bpy.context.scene
meshes=[bpy.data.objects[n] for n in ['Slime_Body','Slime_Droplet','Eye_L','Eye_R']]

def coords(o):
    dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep)
    m=ev.to_mesh();a=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return a

S.frame_set(1);start={o.name:coords(o) for o in meshes}
S.frame_set(97);end={o.name:coords(o) for o in meshes}
err={n:max((a-b).length for a,b in zip(v,end[n])) for n,v in start.items()}
assert max(err.values())<1e-5,err
samples=[]
for f in [1,9,16,17,25,33,41,49,57,58,65,70,73,81,89,96,97]:
    S.frame_set(f)
    c=coords(meshes[0]);d=coords(meshes[1])
    assert all(math.isfinite(x) for p in c+d for x in p)
    low=min(p.z for p in c)
    assert low>=-.001,(f,low)
    assert min(p.z for p in d)>=-.005,(f,'droplet penetrates floor',min(p.z for p in d))
    samples.append({'frame':f,'body_floor_m':low,'body_height_m':max(p.z for p in c)-low,
                    'drop_center_m':list(sum(d,Vector())/len(d)),
                    'drop_bounds_m':[[min(p[i] for p in d),max(p[i] for p in d)] for i in range(3)]})
report={'loop_vertex_error_m':err,'source_duration_s':(S.frame_end-S.frame_start)/S.render.fps,
        'samples':samples,'checks':'finite vertices, floor contact, 1/97 identical evaluated mesh',
        'unreal_validation':'not performed; source-model review only'}
# 120Hz regression scan catches between-key motion and the old 1.04s teleport.
rig=bpy.data.objects['Slime_Liquid_Rig'];steps=[];previous=None
fixed_axis=None;rotation_error=0
for i in range(481):
    frame=1+i/5
    S.frame_set(int(frame),subframe=frame-int(frame))
    pb=rig.pose.bones['drop'];pos=rig.matrix_world@pb.head
    visible=(frame-1)/96<.94
    if visible:
        axis=(rig.matrix_world.to_3x3()@pb.matrix.to_3x3().col[1]).normalized()
        if fixed_axis is None:fixed_axis=axis.copy()
        rotation_error=max(rotation_error,(axis-fixed_axis).length)
    if previous and visible and previous[1]:
        steps.append({'time':i/120,'speed_mps':(pos-previous[0]).length*120})
    previous=(pos.copy(),visible)
peak=max(steps,key=lambda x:x['speed_mps'])
one_sec=max(x['speed_mps'] for x in steps if .8<=x['time']<=1.25)
assert peak['speed_mps']<1.8,peak
assert one_sec<1.8,one_sec
report['droplet_continuity_120hz']={'peak':peak,'one_second_peak_mps':one_sec,'passed':True}
assert rotation_error<1e-5,('Droplet rotates',rotation_error)
report['fixed_drop_world_axis_error']=rotation_error
from mathutils.bvhtree import BVHTree
# The evaluated mesh must stay rigid throughout the entire loop, including return.
reference_dimensions=None;dimension_error=0
for f in range(1,98):
    S.frame_set(f)
    assert (rig.pose.bones['drop'].scale-Vector((.62,1,.24))).length<1e-5
    pts=coords(meshes[1]);dims=Vector([max(v[i] for v in pts)-min(v[i] for v in pts) for i in range(3)])
    if reference_dimensions is None:reference_dimensions=dims.copy()
    dimension_error=max(dimension_error,(dims-reference_dimensions).length)
assert dimension_error<1e-5,dimension_error
report['all_frame_drop_dimension_error_m']=dimension_error
signed=[]
for f in [1]+[92+i/5 for i in range(26)]:
    S.frame_set(int(f),subframe=f-int(f))
    dep=bpy.context.evaluated_depsgraph_get();tree=BVHTree.FromObject(meshes[0],dep)
    for p in coords(meshes[1]):
        hit,n,_,_=tree.find_nearest(p)
        signed.append((p-hit).dot(n))
assert max(signed)<0,('Absorbed bead still outside body',max(signed))
report['absorbed_drop_max_signed_surface_distance_m']=max(signed)
S.frame_set(1);skirt0=coords(meshes[0])
S.frame_set(25);skirt1=coords(meshes[0])
skirt_motion=max((a-b).length for a,b in zip(skirt0,skirt1) if a.z<.15)
assert skirt_motion>.008,skirt_motion
report['puddle_motion_m']=skirt_motion
eye_measurements=[]
for name in ['Eye_L','Eye_R']:
    eye=bpy.data.objects[name]
    width=max(v.co.x for v in eye.data.vertices)-min(v.co.x for v in eye.data.vertices)
    height=max(v.co.z for v in eye.data.vertices)-min(v.co.z for v in eye.data.vertices)
    assert abs(width-.228)<1e-5 and abs(height-.228)<1e-5,(width,height)
    eye_measurements.append({'name':name,'width_m':width,'height_m':height})
assert len(bpy.data.objects['Slime_Body'].data.uv_layers)==1
report['eyes_original_style_restored']=eye_measurements
(OUT/'verification-source.json').write_text(json.dumps(report,indent=2),encoding='utf8')
S.frame_set(1)
if True:
    S.render.engine='BLENDER_EEVEE'
    S.render.resolution_x=800;S.render.resolution_y=720
    S.render.resolution_percentage=100
    # Saved review camera is three-quarter. Frames are exactly four seconds at 24 fps.
    folder=OUT/'Preview'/'Frames';folder.mkdir(exist_ok=True)
    for f in range(1,97):
        S.frame_set(f);S.render.filepath=str(folder/f'{f-1:04}.png')
        bpy.ops.render.render(write_still=True)
print('SOURCE_VERIFICATION_PASSED',json.dumps(report))
