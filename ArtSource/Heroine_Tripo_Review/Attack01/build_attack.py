"""Reference-driven first horizontal cut; creates an isolated editable action."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'RunSoft/Heroine_Run_Soft.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene;o=bpy.data.objects['Heroine_DetailFinish2'];factor=r.scale.x
r.animation_data.action=None
for p in r.pose.bones:
 p.matrix_basis.identity()
 if 'IK_FK' in p:p['IK_FK']=1.0
 if 'IK_Stretch' in p:p['IK_Stretch']=0.0
for i in range(8):
 p=r.pose.bones[f'MCH-garment_follow_{i:02}']
 for c in p.constraints:c.influence=0
 for axis in range(3):p.driver_remove('location',axis)
 p.location=(0,0,0)
bpy.context.view_layer.update()
rest={n:p.matrix.copy() for n,p in r.pose.bones.items()}
d=json.loads((P/'reference_motion.json').read_text());rows=d['samples']
# UE animation FBX bakes the first animated pose into the imported bind pose.
# Use the preserved neutral skeleton, otherwise the first-frame twist is cancelled.
canonical=json.loads((P.parent/'AnimationWorkflow/ReferenceMotion/source_rest_canonical.json').read_text())['rest']
sr={n:Matrix(m).to_quaternion() for n,m in canonical.items()}
mapping={'spine_fk':'Spine','spine_fk.001':'Spine1','spine_fk.002':'Spine1','spine_fk.003':'Spine2','neck':'Neck','head':'Head'}
for side,word in [('L','Left'),('R','Right')]:
 for dest,source in [('shoulder','Shoulder'),('upper_arm_fk','Arm'),('forearm_fk','ForeArm'),('hand_fk','Hand'),('thigh_fk','UpLeg'),('shin_fk','Leg'),('foot_fk','Foot'),('toe_fk','ToeBase')]:mapping[dest+'.'+side]=word+source
 for finger in ['f_index','f_middle','f_ring','f_pinky','thumb']:
  for j in [1,2,3]:mapping[f'{finger}.{j:02}.{side}']=word+'Hand'+('Thumb' if finger=='thumb' else 'Index')+str(j)
cal={}
for n,s in mapping.items():
 t=rest[n].to_quaternion();swing=(sr[s]@Vector((0,1,0))).rotation_difference(t@Vector((0,1,0)))
 cal[n]=sr[s].inverted()@swing.inverted()@t
def sample(u):
 x=min(72.,u*72);i=min(int(x),71);v=x-i
 return {n:{'head':Vector(b['head']).lerp(Vector(rows[i+1]['bones'][n]['head']),v),'q':Matrix(b['matrix']).to_quaternion().slerp(Matrix(rows[i+1]['bones'][n]['matrix']).to_quaternion(),v)} for n,b in rows[i]['bones'].items()}
def orient(n,q):
 p=r.pose.bones[n];p.rotation_mode='QUATERNION';p.matrix=Matrix.LocRotScale(p.matrix.translation,q,Vector((1,1,1)));bpy.context.view_layer.update()
first=sample(0);hip0=(first['LeftUpLeg']['head']+first['RightUpLeg']['head'])/2
sleg=sum((first['Left'+a]['head']-first['Left'+b]['head']).length for a,b in [('UpLeg','Leg'),('Leg','Foot')])
ratio=sum(r.data.bones[n+'.L'].length for n in ['thigh_fk','shin_fk'])*factor/sleg
shoe={}
for side in ['L','R']:
 gs={g.index for g in o.vertex_groups if g.name in ['DEF-foot.'+side,'DEF-toe.'+side]}
 shoe[side]=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in gs)>.7]
controls=list(mapping)+['torso','hips']+[f'{n}_parent.{s}' for n in ['thigh','upper_arm'] for s in ['L','R']]+[f'skirt_{i:02}.{j:02}' for i in range(8) for j in [1,2]]
sc.render.fps=60;sc.frame_start=1;sc.frame_end=61
prior={};report=[]
for frame in range(1,62):
 sc.frame_set(frame)
 for n in controls:r.pose.bones[n].matrix_basis.identity()
 bpy.context.view_layer.update();data=sample((frame-1)/60)
 hip=(data['LeftUpLeg']['head']+data['RightUpLeg']['head'])/2
 p=r.pose.bones['torso'];m=rest['torso'].copy();m.translation+=(hip-hip0)*ratio/factor;p.matrix=m;bpy.context.view_layer.update()
 x=(data['LeftUpLeg']['head']-data['RightUpLeg']['head']).normalized();z=(data['Spine']['head']-hip).normalized();y=z.cross(x).normalized();z=x.cross(y).normalized()
 orient('hips',Matrix((x,y,z)).transposed().to_quaternion()@rest['hips'].to_quaternion())
 for n,s in sorted(mapping.items(),key=lambda item:len(r.pose.bones[item[0]].parent_recursive)):orient(n,data[s]['q']@cal[n])
 # Grounding the reference stance; no artificial lift or synthetic leg path.
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low={s:min((o.matrix_world@me.vertices[j].co).z for j in ids) for s,ids in shoe.items()};ev.to_mesh_clear()
 m=r.pose.bones['torso'].matrix.copy();m.translation+=r.matrix_world.inverted().to_3x3()@Vector((0,0,.001-min(low.values())));r.pose.bones['torso'].matrix=m;bpy.context.view_layer.update()
 for i in range(8):
  theta=i*math.pi/4;axis=Vector((-math.cos(theta),-math.sin(theta),0))
  for j in [1,2]:
   n=f'skirt_{i:02}.{j:02}';p=r.pose.bones[n];p.rotation_mode='QUATERNION';q=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=q.inverted()@Quaternion(axis,math.radians(4 if j==1 else 2))@q
 for n in controls:
  p=r.pose.bones[n]
  if p.rotation_mode=='QUATERNION':
   if n in prior and p.rotation_quaternion.dot(prior[n])<0:p.rotation_quaternion.negate()
   prior[n]=p.rotation_quaternion.copy()
  for field in ['location','rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:p.keyframe_insert(field,frame=frame,group=n)
  for prop in ['IK_FK','IK_Stretch']:
   if prop in p:p.keyframe_insert('['+json.dumps(prop)+']',frame=frame,group=n)
 report.append({'frame':frame,'source_phase':(frame-1)/60,'raw_sole_m':low,'ground_offset_m':.001-min(low.values()),'torso_z_m':(r.matrix_world@r.pose.bones['torso'].head).z})
r.animation_data.action.name='Sword_Attack_01_Horizontal'
for layer in r.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
sc.frame_set(23)
(P/'retarget_report.json').write_text(json.dumps({'reference_ratio':ratio,'frames':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
print('ATTACK_BUILT',factor,ratio)
