import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parent;D=P.parent/'RigReferenceFit/Delivery'
bpy.ops.wm.open_mainfile(filepath=str(D/'Heroine_AnimationRig.blend'))
rig=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene;factor=rig.scale.x
# Local garment skinning correction in this animation-preview copy only.
body=bpy.data.objects['Heroine_DetailFinish2'];mi=next(i for i,s in enumerate(body.material_slots) if s.material.name=='M_Skirt')
skirt_ids={i for p in body.data.polygons if p.material_index==mi for i in p.vertices};weight_report=[]
for vid in skirt_ids:
 v=body.data.vertices[vid];z=v.co.z
 if z>=.563:continue
 # Keep waistband attached; progressively let the garment chains own the hem.
 blend=max(0,min(1,(.563-z)/.036));blend=blend*blend*(3-2*blend)
 theta=(math.atan2(v.co.x,-v.co.y)%(2*math.pi))/(math.pi/4);i=int(theta)%8;j=(i+1)%8;u=theta-int(theta)
 segment=max(0,min(1,(.555-z)/.050))
 ws={'DEF-spine':1-blend}
 for panel,pw in [(i,1-u),(j,u)]:
  for seg,sw in [(1,1-segment),(2,segment)]:ws[f'DEF-skirt_{panel:02}.{seg:02}']=blend*pw*sw
 ws=dict(sorted(ws.items(),key=lambda p:-p[1])[:4]);total=sum(ws.values())
 for g in list(v.groups):body.vertex_groups[g.group].remove([vid])
 for n,w in ws.items():
  if w>1e-6:body.vertex_groups[n].add([vid],w/total,'REPLACE')
 weight_report.append(vid)
(P/'garment_weight_fix.json').write_text(json.dumps({'changed_vertices':len(weight_report),'material':'M_Skirt','scope':'preview mesh copy only; UV, positions and materials unchanged','vertex_ids':weight_report},indent=2))
if rig.animation_data:rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis.identity()
for p in rig.pose.bones:
 if 'IK_FK' in p:p['IK_FK']=1.0
 if 'IK_Stretch' in p:p['IK_Stretch']=0.0
for side in ['L','R']:rig.pose.bones['thigh_parent.'+side]['IK_FK']=0.0
# The static pose garment follower copies thigh rotation too aggressively during a step.
# This clip uses explicit, baked skirt clearance on the additive controls instead.
for i in range(8):
 p=rig.pose.bones[f'MCH-garment_follow_{i:02}']
 for c in p.constraints:c.influence=0
 for axis in range(3):p.driver_remove('location',axis)
 p.location=(0,0,0)
bpy.context.view_layer.update()
reference=json.loads((P/'reference_motion.json').read_text())['samples'][:29]
def sample(n,phase):
 f=(phase%1)*29;i=int(f);a=Vector(reference[i]['bones'][n]['head']);b=Vector(reference[(i+1)%29]['bones'][n]['head']);return a.lerp(b,f-i)
def signal(n,axis,phase):
 mean=sum(s['bones'][n]['head'][axis] for s in reference)/29
 return sample(n,phase)[axis]-mean
def rotate(n,axis,deg):
 p=rig.pose.bones[n];p.rotation_mode='QUATERNION';q=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=q.inverted()@Quaternion(Vector(axis),math.radians(deg))@q
def locate(n,v):
 p=rig.pose.bones[n];p.location=p.bone.matrix_local.to_quaternion().inverted()@Vector(v)
controls=['torso','hips','chest','head','neck']
controls += [f'skirt_{i:02}.{j:02}' for i in range(8) for j in [1,2]]
for side in ['L','R']:
 controls+=['foot_ik.'+side,'thigh_parent.'+side,'upper_arm_fk.'+side,'forearm_fk.'+side,'hand_fk.'+side,'shoulder.'+side]
 controls += [f'{finger}.{j:02}.{side}' for finger in ['f_index','f_middle','f_ring','f_pinky','thumb'] for j in [1,2,3]]
controls=[n for n in controls if n in rig.pose.bones]
feet={s:rig.pose.bones['foot_ik.'+s].matrix.copy() for s in ['L','R']}
sc.render.fps=30;sc.frame_start=1;sc.frame_end=41
stride=.64;duration=40/30;stance=.60;speed=stride/duration
sc['walk_speed_cm_s']=speed*100
sc['walk_design']='Small careful steps; reduced reference upper-body rhythm; slight downward gaze; in-place 1.333 second loop'
feet_report=[]
for frame in range(1,42):
 t=(frame-1)/40;sc.frame_set(frame)
 # Reference phase ~7/29 is left heel strike. Preserve its secondary rhythm at reduced amplitude.
 refphase=t+7/29
 sway=signal('Head',0,refphase)*.25
 bob=signal('Head',2,refphase)*.15
 locate('torso',(sway/factor,0,(-.025+bob)/factor))
 rotate('hips',(0,0,1),1.6*math.sin(2*math.pi*t))
 rotate('chest',(1,0,0),3.0)
 rotate('neck',(1,0,0),1.0)
 rotate('head',(1,0,0),2.5)
 for i in range(8):
  theta=i*math.pi/4;axis=(-math.cos(theta),-math.sin(theta),0)
  clearance=2+abs(math.cos(theta))*math.sin(2*math.pi*t)**2
  rotate(f'skirt_{i:02}.01',axis,clearance)
  rotate(f'skirt_{i:02}.02',axis,2)
  locate(f'skirt_{i:02}.01',(math.sin(theta)*.014/factor,-math.cos(theta)*.040/factor,0))
 bpy.context.view_layer.update()
 row={'frame':frame,'feet':{}}
 for side,sign,offset in [('L',1,0),('R',-1,.5)]:
  phase=(t+offset)%1
  # Fixed-speed stance trajectory; cosine-speed swing joins stance with equal velocity.
  if phase<stance:
   y=-stride*stance/2+stride*phase
   lift=0.0
   pitch=-4*max(0,1-phase/.1)+10*max(0,(phase-.48)/.12)**2
  else:
   u=(phase-stance)/(1-stance)
   # Cubic Hermite swing with stance-matched endpoint slopes.
   h00=2*u**3-3*u*u+1;h10=u**3-2*u*u+u;h01=-2*u**3+3*u*u;h11=u**3-u*u
   y=h00*(stride*stance/2)+h10*stride*(1-stance)+h01*(-stride*stance/2)+h11*stride*(1-stance)
   lift=.024*math.sin(math.pi*u)**2
   pitch=10*(1-u)-4*u
  # Rest ankle height plus support correction for the sole under foot pitch.
  angle=math.radians(pitch)
  foot=rig.pose.bones['foot_ik.'+side]
  mat=feet[side].copy();mat.translation=feet[side].translation+Vector(((-sign*.006+sway*.08)/factor,y/factor,lift/factor))
  rot=Quaternion((1,0,0),angle)
  mat=Matrix.LocRotScale(mat.translation,rot@feet[side].to_quaternion(),Vector((1,1,1)))
  foot.matrix=mat
  # Arm swing comes from the real clip, with most amplitude removed.
  arm_delta=sample(('Left' if side=='L' else 'Right')+'Hand',refphase)-sample(('Left' if side=='L' else 'Right')+'Arm',refphase)
  swing=max(-5,min(5,arm_delta.y*35))
  rotate('upper_arm_fk.'+side,(0,1,0),sign*74)
  p=rig.pose.bones['upper_arm_fk.'+side];q=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=(q.inverted()@Quaternion((1,0,0),math.radians(swing))@q)@p.rotation_quaternion
  rotate('forearm_fk.'+side,(0,0,1),-sign*(7+1.5*math.sin(2*math.pi*(t+offset))))
  for finger in ['f_index','f_middle','f_ring','f_pinky']:
   for j,deg in [(1,12),(2,18),(3,9)]:rotate(f'{finger}.{j:02}.{side}',(0,1,0),sign*deg)
  for j,deg in [(1,5),(2,8),(3,6)]:rotate(f'thumb.{j:02}.{side}',(0,1,0),sign*deg)
  bpy.context.view_layer.update()
  # Align shoe sole to the support plane using actual deformed shoe vertices.
  sole=[]
  for obj in sc.objects:
   if obj.type!='MESH' or obj.name.startswith('WGT-'):continue
   groups={g.index for g in obj.vertex_groups if g.name in ['DEF-foot.'+side,'DEF-toe.'+side]}
   if not groups:continue
   ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
   sole.extend((obj.matrix_world@m.vertices[v.index].co).z for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.7)
   ev.to_mesh_clear()
  if sole:
   adjustment=(lift-min(sole))/factor
   mat=foot.matrix.copy();mat.translation.z+=adjustment;foot.matrix=mat
  bpy.context.view_layer.update()
  row['feet'][side]={'phase':phase,'stance':phase<stance,'target_y_m':y,'lift_m':lift,'ankle':list(rig.matrix_world@rig.pose.bones['DEF-foot.'+side].head),'knee':list(rig.matrix_world@rig.pose.bones['DEF-shin.'+side].head)}
 # Re-solve both IK chains after all controls changed; correct the residual sole error.
 for iteration in range(4):
  bpy.context.view_layer.update()
  for side in ['L','R']:
   sole=[]
   for obj in sc.objects:
    if obj.type!='MESH' or obj.name.startswith('WGT-'):continue
    groups={g.index for g in obj.vertex_groups if g.name in ['DEF-foot.'+side,'DEF-toe.'+side]}
    if not groups:continue
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    sole.extend((obj.matrix_world@m.vertices[v.index].co).z for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.7)
    ev.to_mesh_clear()
   foot=rig.pose.bones['foot_ik.'+side];mat=foot.matrix.copy();mat.translation.z+=(row['feet'][side]['lift_m']+.0005-min(sole))/factor;foot.matrix=mat
   bpy.context.view_layer.update()
 for name in controls:
  p=rig.pose.bones[name]
  for prop in ['location','rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:p.keyframe_insert(prop,frame=frame,group=name)
  if 'IK_FK' in p:p.keyframe_insert('["IK_FK"]',frame=frame,group=name)
 feet_report.append(row)
action=rig.animation_data.action;action.name='Walk_Timid';action.use_fake_user=True
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Walk_Timid.blend'))
(P/'motion_design.json').write_text(json.dumps({'duration_s':duration,'fps':30,'frames':[1,41],'stride_m':stride,'speed_cm_s':speed*100,'stance_fraction':stance,'reference_asset':'/Game/Resources/Characters/CommonAnimation/Walk','foot_samples':feet_report},indent=2))
print('TIMID_WALK_CREATED',speed)
