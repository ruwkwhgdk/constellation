"""Verify gravity/immersion, constant mesh dimensions, and render the physical gel."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from gel_flow_v08 import render_setup
S=bpy.context.scene;rig=bpy.data.objects['Slime_Liquid_Rig'];body=bpy.data.objects['Slime_Body'];drop=bpy.data.objects['Slime_Droplet']
def coords(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    p=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return p
meshes=[o for o in [body,drop,bpy.data.objects['Slime_InnerGel'],bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]]
S.frame_set(1);start={o.name:coords(o) for o in meshes}
S.frame_set(97);loop=max(max((a-b).length for a,b in zip(start[o.name],coords(o))) for o in meshes)
assert loop<1e-5,loop
dims0=None;dimerr=0;rot0=None;roterr=0;positions=[];floor=1e3;scales=[]
track=json.loads((OUT/'revision-10.json').read_text())['track'];tangent_error=0
for f in range(1,98):
    S.frame_set(f);p=coords(drop);pb=rig.pose.bones['drop']
    assert all(math.isfinite(c) for v in p for c in v)
    dims=Vector([(p[i]-p[0]).length for i in [100,300,500]])
    if dims0 is None:dims0=dims.copy();rot0=pb.rotation_quaternion.copy()
    dimerr=max(dimerr,(dims-dims0).length);roterr=max(roterr,rot0.rotation_difference(pb.rotation_quaternion).angle)
    up=(rig.matrix_world.to_3x3()@pb.matrix.to_3x3().col[1]).normalized()
    q=(f-1)/96
    if q<.24 or q>=.75:assert (up-Vector((0,0,1))).length<1e-5,('Not upright in free fall',f,list(up))
    if .32<=q<=.67:
        normal=Vector(track[f-1]['surface_normal'])
        tangent_error=max(tangent_error,abs(up.dot(normal)))
    positions.append(rig.matrix_world@pb.head);scales.append(list(pb.scale))
    floor=min(floor,min(v.z for v in coords(body)))
assert dimerr<1e-5 and tangent_error<1e-5,(dimerr,tangent_error)
assert floor>=-.001,floor
birth=positions[:24]
birthxy=max(Vector((p.x-birth[0].x,p.y-birth[0].y)).length for p in birth)
assert birthxy<1e-5,birthxy
assert all(b.z<a.z for a,b in zip(birth,birth[1:])), 'birth must descend'
fall_dist=birth[0].z-birth[-1].z
assert fall_dist>.2,fall_dist
sink=positions[72:81]
assert all(b.z<a.z for a,b in zip(sink,sink[1:])), 'immersion must descend'
assert sink[0].z-sink[-1].z>.20
sinkxy=max(Vector((p.x-sink[0].x,p.y-sink[0].y)).length for p in positions[72:91])
assert sinkxy<1e-5,('release drifts sideways',sinkxy)
for i in range(1,8):
    assert abs((sink[0].z-sink[i].z)-.5*9.81*(i/24)**2)<1e-5
assert max(v.z for v in coords(drop))>0 # loop ends inside crest, never at zero scale
gel=bpy.data.materials['M_Slime_IndigoGel'];nodes=gel.node_tree.nodes
surface=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
assert surface.inputs['Transmission Weight'].default_value>.9
assert any(n.type=='VOLUME_ABSORPTION' for n in nodes)
report={'passed':True,'loop_vertex_error_m':loop,'all_frame_drop_dimension_error_m':dimerr,
        'surface_tangent_dot_error':tangent_error,'max_rotation_from_upright_radians':roterr,'birth_horizontal_drift_m':birthxy,'birth_fall_m':fall_dist,
        'immersion_descent_m':sink[0].z-sink[-1].z,'release_horizontal_drift_m':sinkxy,'upright_axis_verified':True,'gravity_mps2':9.81,'body_floor_min_m':floor,
        'drop_scale_constant':scales[0],'transmission_weight':surface.inputs['Transmission Weight'].default_value,
        'render_engine':'CYCLES','duration_s':4,'unreal_validation':'not performed'}
(OUT/'verification-source.json').write_text(json.dumps(report,indent=2),encoding='utf8')
render_setup(S,16);S.render.resolution_x=560;S.render.resolution_y=504;S.render.resolution_percentage=100
S.cycles.volume_step_rate=4
S.render.use_persistent_data=False
render_start=1
if '--start-frame' in sys.argv:render_start=int(sys.argv[sys.argv.index('--start-frame')+1])
render_end=96
if '--end-frame' in sys.argv:render_end=int(sys.argv[sys.argv.index('--end-frame')+1])
for f in range(render_start,render_end+1):
    S.frame_set(f);S.render.filepath=str(OUT/'Preview'/'Frames'/f'{f-1:04d}.png');bpy.ops.render.render(write_still=True)
print('SOURCE_VERIFICATION_PASSED',json.dumps(report))
