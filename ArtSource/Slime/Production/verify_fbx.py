"""Reimport delivery FBX into an empty Blender process; inspect deformation."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(OUT/'SK_Slime_Liquid_Idle.fbx'),use_anim=True)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==5
assert set(rig.data.bones.keys())=={'root','center','top','crest','crest_tip','drop'}|{f'puddle_{i:02}' for i in range(8)}
assert rig.animation_data and rig.animation_data.action
action=rig.animation_data.action
start,end=action.frame_range
assert abs((end-start)-96)<.001

def points(o,f):
    bpy.context.scene.frame_set(int(f));d=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(d)
    m=ev.to_mesh();c=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return c

info={}
for o in meshes:
    a=points(o,start);b=points(o,end);c=points(o,start+48)
    error=max((x-y).length for x,y in zip(a,b))
    motion=max((x-y).length for x,y in zip(a,c))
    assert error<.0001,(o.name,error)
    assert all(math.isfinite(v) for p in a+c for v in p)
    info[o.name]={'vertices':len(a),'loop_error_m':error,'midcycle_motion_m':motion,
                  'bounds_m':[[min(p[i] for p in a),max(p[i] for p in a)] for i in range(3)],
                  'material_slots':[m.name for m in o.data.materials],
                  'uv_layers':list(o.data.uv_layers.keys())}
body=next(v for n,v in info.items() if n=='Slime_Body')
height=body['bounds_m'][2][1]-body['bounds_m'][2][0]
assert 1.6<height<1.75,height
assert info['Slime_Droplet']['midcycle_motion_m']>.2
assert len(info['Slime_Body']['uv_layers'])==1
drop=next(o for o in meshes if o.name=='Slime_Droplet')
reference_dimensions=None;dimension_error=0
for f in range(int(start),int(end)+1):
    pts=points(drop,f);dims=Vector([(pts[i]-pts[0]).length for i in [100,300,500]])
    if reference_dimensions is None:reference_dimensions=dims.copy()
    dimension_error=max(dimension_error,(dims-reference_dimensions).length)
assert dimension_error<1e-5,dimension_error
previous=None;steps=[];fixed_axis=None;rotation_error=0
for f in range(int(start),int(end)+1):
    bpy.context.scene.frame_set(f);pb=rig.pose.bones['drop'];pos=rig.matrix_world@pb.head
    visible=(f-start)/96<.94
    if visible and ((f-start)/96<.24 or (f-start)/96>=.75):
        axis=(rig.matrix_world.to_3x3()@pb.matrix.to_3x3().col[1]).normalized()
        if fixed_axis is None:fixed_axis=axis.copy()
        rotation_error=max(rotation_error,(axis-fixed_axis).length)
    if previous and visible and previous[1]:steps.append((pos-previous[0]).length)
    previous=(pos.copy(),visible)
# At 9.81 m/s² the final free-fall step is up to 13.1 cm at 24fps.
assert max(steps)<.14,max(steps)
assert rotation_error<1e-5,rotation_error
fall=[]
for f in range(int(start)+72,int(start)+81):
    bpy.context.scene.frame_set(f)
    pb=rig.pose.bones['drop'];fall.append(rig.matrix_world@pb.head)
    up=(rig.matrix_world.to_3x3()@pb.matrix.to_3x3().col[1]).normalized()
    assert (up-Vector((0,0,1))).length<1e-5
release_xy=max(Vector((p.x-fall[0].x,p.y-fall[0].y)).length for p in fall)
assert release_xy<1e-5,release_xy
for i in range(1,8):assert abs((fall[0].z-fall[i].z)-.5*9.81*(i/24)**2)<1e-5
track=json.loads((OUT/'revision-10.json').read_text())['track'];tangent_error=0
for row in track:
    q=(row['frame']-1)/96
    if .32<=q<=.67:
        bpy.context.scene.frame_set(int(start)+row['frame']-1)
        pb=rig.pose.bones['drop'];up=(rig.matrix_world.to_3x3()@pb.matrix.to_3x3().col[1]).normalized()
        tangent_error=max(tangent_error,abs(up.dot(Vector(row['surface_normal']))))
assert tangent_error<1e-5,tangent_error
report={'passed':True,'surface_tangent_dot_error':tangent_error,'release_horizontal_drift_m':release_xy,'upright_and_gravity_verified':True,'all_frame_drop_dimension_error_m':dimension_error,'imported_fps':bpy.context.scene.render.fps,'frame_range':[start,end],
        'bones':list(rig.data.bones.keys()),'meshes':info,
        'max_visible_drop_step_m':max(steps),'fixed_drop_world_axis_error':rotation_error,
        'limitation':'Blender FBX round trip; Unreal importer and old animation compatibility not tested.'}
(OUT/'verification-fbx.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('FBX_ROUNDTRIP_PASSED',json.dumps(report))
