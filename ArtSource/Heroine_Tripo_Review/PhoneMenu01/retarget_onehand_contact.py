import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).parent/'OneHandRetarget02';P.mkdir(exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'OneHandSourceEdit01/Mixamo_OneHand_SourceEdit01.blend'));s=bpy.context.scene;src=next(o for o in s.objects if o.type=='ARMATURE')
rest={b.name.removeprefix('mixamorig:'):src.matrix_world@b.matrix_local for b in src.data.bones};poses={}
for f in range(1,286):
 s.frame_set(f);poses[f]={b.name.removeprefix('mixamorig:'):src.matrix_world@b.matrix for b in src.pose.bones}
bpy.ops.wm.open_mainfile(filepath=str(Path('C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/CarryPickupD01/Attempt06/Heroine_Pickup_Chair.blend')));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];s.frame_set(1)
tr={b.name:r.matrix_world@b.matrix_local for b in r.data.bones};base={b.name:b.matrix_basis.copy() for b in r.pose.bones}
visibility={o:o.hide_get() for o in s.objects if o.type=="MESH"}
for o in visibility:o.hide_set(True)
for o in s.objects:
 if o.type=='MESH' and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:k.value=0
r.animation_data_clear();r.animation_data_create();r.animation_data.action=bpy.data.actions.new('Heroine_Mixamo_OneHand_Contact02')
def world(n):return r.matrix_world@r.pose.bones[n].matrix
def orient(n,q):
 old=world(n);r.pose.bones[n].matrix=r.matrix_world.inverted()@Matrix.LocRotScale(old.translation,q,old.to_scale());bpy.context.view_layer.update()
def basis(d,a,b,c):
 y=(d[b].translation-d[a].translation).normalized();x=d[c[0]].translation-d[c[1]].translation;x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized();return Matrix((x,y,z)).transposed().to_quaternion()
def segment(tn,tc,sn,sc,sp):
 td=(tr[tc].translation-tr[tn].translation).normalized();sd=(rest[sc].translation-rest[sn].translation).normalized();orient(tn,sp[sn].to_quaternion()@rest[sn].to_quaternion().inverted()@td.rotation_difference(sd)@tr[tn].to_quaternion())
def swing(n,child,goal):
 m=world(n);p=m.translation
 q=(world(child).translation-p).rotation_difference(goal-p)
 r.pose.bones[n].matrix=r.matrix_world.inverted()@Matrix.Translation(p)@q.to_matrix().to_4x4()@Matrix.Translation(-p)@m
 bpy.context.view_layer.update()
def match_hand_contact(side,sideName,sp):
 a,b,c=[x+"_"+side for x in ("upperarm","lowerarm","hand")]
 h,k,w=[world(x).translation for x in (a,b,c)]
 goal=world("pelvis").translation+(sp[sideName+"Hand"].translation-sp["Hips"].translation)*ratio
 l1=(k-h).length;l2=(w-k).length;v=goal-h
 d=min(max(v.length,abs(l1-l2)+.001),l1+l2-.001);axis=v.normalized()
 pole=(sp[sideName+"ForeArm"].translation-sp[sideName+"Arm"].translation).normalized()
 bend=pole-axis*pole.dot(axis)
 if bend.length<.001:bend=k-h-axis*(k-h).dot(axis)
 bend.normalize();x=(l1*l1-l2*l2+d*d)/(2*d)
 elbow=h+axis*x+bend*math.sqrt(max(0,l1*l1-x*x))
 swing(a,b,elbow);swing(b,c,h+axis*d)
body=[('spine_01','spine_02','Spine','Spine1'),('spine_02','spine_03','Spine1','Spine2'),('spine_03','neck_01','Spine2','Neck'),('neck_01','head','Neck','Head')]
ratio=tr['pelvis'].translation.z/rest['Hips'].translation.z
anchor=world('pelvis').translation-poses[1]['Hips'].translation*ratio;rows=[]
for f in range(1,286):
 s.frame_set(f)
 for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
 r.pose.bones['root'].matrix_basis=base['root'];bpy.context.view_layer.update()
 pelvis=r.pose.bones['pelvis'];p=world('pelvis')
 sp=poses[f];desired=sp['Hips'].translation*ratio+anchor
 q=sp['Hips'].to_quaternion()@rest['Hips'].to_quaternion().inverted()@tr['pelvis'].to_quaternion()
 pelvis.matrix=r.matrix_world.inverted()@Matrix.LocRotScale(desired,q,p.to_scale());bpy.context.view_layer.update()
 for args in body:segment(*args,sp)
 orient('head',sp['Head'].to_quaternion()@rest['Head'].to_quaternion().inverted()@tr['head'].to_quaternion())
 for side,sideName in [('r','Right'),('l','Left')]:
  for tn,tc,sn,sc in [('clavicle','upperarm','Shoulder','Arm'),('upperarm','lowerarm','Arm','ForeArm'),('lowerarm','hand','ForeArm','Hand'),('thigh','calf','UpLeg','Leg'),('calf','foot','Leg','Foot'),('foot','ball','Foot','ToeBase')]:
   segment(tn+'_'+side,tc+'_'+side,sideName+sn,sideName+sc,sp)
  match_hand_contact(side,sideName,sp)
  hn='hand_'+side;hp=basis(sp,sideName+'Hand',sideName+'HandMiddle1',(sideName+'HandIndex1',sideName+'HandPinky1'));tp=basis(tr,hn,'middle_01_'+side,('index_01_'+side,'pinky_01_'+side));orient(hn,hp@tp.inverted()@tr[hn].to_quaternion())
  for tf,sf in [('thumb','Thumb'),('index','Index'),('middle','Middle'),('ring','Ring'),('pinky','Pinky')]:
   for i in range(1,4):
    tn=f'{tf}_{i:02d}_{side}';sn=f'{sideName}Hand{sf}{i}';sc=f'{sideName}Hand{sf}{i+1}';td=(r.data.bones[tn].tail_local-r.data.bones[tn].head_local).normalized();sd=(rest[sc].translation-rest[sn].translation).normalized();orient(tn,sp[sn].to_quaternion()@rest[sn].to_quaternion().inverted()@td.rotation_difference(sd)@tr[tn].to_quaternion())
 for b in r.pose.bones:
  b.rotation_mode='QUATERNION';b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f);b.keyframe_insert('scale',frame=f)
 a,k,w=[world(n).translation for n in ['upperarm_r','lowerarm_r','hand_r']];sa,sk,sw=[sp[n].translation for n in ['RightArm','RightForeArm','RightHand']]
 rows.append({'frame':f,'source_elbow_flex':180-math.degrees((sa-sk).angle(sw-sk)),'target_elbow_flex':180-math.degrees((a-k).angle(w-k)),'finger_axis_error_deg':math.degrees((world('middle_01_r').translation-w).angle(sp['RightHandMiddle1'].translation-sw))})
 if f%60==0:print("RETARGET_FRAME",f,flush=True)
for layer in r.animation_data.action.layers:
 for strip in layer.strips:
  for slot in r.animation_data.action.slots:
   bag=strip.channelbag(slot)
   if bag:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
for o,hidden in visibility.items():o.hide_set(hidden)
for o in s.objects:
 if o.type=='MESH' and ('Gate' in o.name or o.name.startswith('UCX') or o.name=='Chair'):o.hide_render=True
s.frame_start=1;s.frame_end=285;s.render.fps=30;s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Mixamo_OneHand02.blend'));(P/'retarget_full_metrics.json').write_text(json.dumps(rows,indent=2))



