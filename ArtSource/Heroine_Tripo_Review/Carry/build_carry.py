"""Create editable carry actions on the maintained rig, preserving character geometry."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

P=Path(__file__).resolve().parent
rig=bpy.data.objects['Heroine_AnimationRig']; scene=bpy.context.scene; scale=rig.scale.x
rig.animation_data.action=None  # Keep Rigify's IK drivers; clearing animation_data deletes them.
for track in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(track)
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
controls=[b for b in rig.pose.bones if not b.name.startswith(('DEF-','MCH-','ORG-','WGT-','VIS_'))]
scene.render.fps=30
for pb in rig.pose.bones:
    if 'IK_FK' in pb: pb['IK_FK']=1.0 if pb.name.startswith('thigh_parent') else 0.0
    if 'IK_Stretch' in pb: pb['IK_Stretch']=0.0

def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)

def hand(side, sign, xyz, curl):
    pb=rig.pose.bones['hand_ik.'+side]
    q=Quaternion(Vector((0,0,1)), -sign*math.pi/2)@rest[pb.name].to_quaternion()
    pb.matrix=Matrix.LocRotScale(Vector(xyz)/scale,q,Vector((1,1,1)))
    pole=rig.pose.bones['upper_arm_ik_target.'+side]
    m=rest[pole.name].copy(); m.translation=Vector((sign*.38,-.08,.95))/scale; pole.matrix=m
    # Individual local flexion axes, retaining each finger's own rest orientation.
    for finger in ['f_index','f_middle','f_ring','f_pinky']:
        for joint,deg in [(1,20),(2,35),(3,20)]:
            name=f'{finger}.{joint:02}.{side}'
            if name in rig.pose.bones:
                b=rig.pose.bones[name]; b.rotation_mode='XYZ'; b.rotation_euler.x=math.radians(deg*curl)

def leg(side,sign):
    upper=rig.pose.bones['thigh_fk.'+side]; lower=rig.pose.bones['shin_fk.'+side]
    foot=rig.pose.bones['foot_fk.'+side]
    a=upper.head.copy(); target=rest[foot.name].translation+Vector((sign*.065/scale,0,0))
    delta=target-a; distance=delta.length; axis=delta.normalized()
    l1=rig.data.bones[upper.name].length; l2=rig.data.bones[lower.name].length
    distance=min(distance,l1+l2-.001)
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    bend=Vector((0,-1,0)); bend=(bend-axis*bend.dot(axis)).normalized()
    knee=a+axis*along+bend*math.sqrt(max(0,l1*l1-along*along))
    def orient(pb,desired):
        q=rest[pb.name].to_quaternion(); original=q@Vector((0,1,0))
        rotation=original.rotation_difference(desired.normalized())@q
        pb.matrix=Matrix.LocRotScale(pb.head.copy(),rotation,Vector((1,1,1)))
        bpy.context.view_layer.update()
    orient(upper,knee-a); orient(lower,target-lower.head)
    foot.matrix=Matrix.LocRotScale(target,rest[foot.name].to_quaternion(),Vector((1,1,1)))
    bpy.context.view_layer.update()

def pose(lower, forward, height, spread=.18, lean=0, curl=1):
    for b in rig.pose.bones: b.matrix_basis.identity()
    bpy.context.view_layer.update()
    torso=rig.pose.bones['torso']; m=rest['torso'].copy(); m.translation.z-=lower/scale; torso.matrix=m
    spine=rig.pose.bones['spine_fk.002']; spine.rotation_mode='XYZ'; spine.rotation_euler.x=math.radians(lean)
    bpy.context.view_layer.update()  # Evaluate lowered pelvis before reading hip positions for the leg solve.
    # Solve the existing thigh/shin lengths to fixed feet, with knees facing forward.
    # FK baking avoids the maintained run rig's automatic IK pole flipping in a deep squat.
    leg('L',1); leg('R',-1)
    bpy.context.view_layer.update()
    hand('L',1,(spread,-forward,height),curl); hand('R',-1,(-spread,-forward,height),curl)
    # Fan the existing garment controls during the deep squat; no mesh/weight edits.
    for i in range(8):
        for j in [1,2]:
            name=f'skirt_{i:02}.{j:02}'
            if name in rig.pose.bones:
                b=rig.pose.bones[name]; b.rotation_mode='QUATERNION'
                axis=Vector((-math.cos(i*math.pi/4),-math.sin(i*math.pi/4),0))
                q=b.bone.matrix_local.to_quaternion()
                b.rotation_quaternion=q.inverted()@Quaternion(axis,math.radians(4+lower*35 if j==1 else 2+lower*20))@q
    bpy.context.view_layer.update()

clips={'Pickup':(1.4,.55),'Place':(1.4,.85),'Throw':(.9,.38),'Hold':(1.2,None),'Aim':(1.2,None)}
report=[]
for name,(duration,contact) in clips.items():
    rig.animation_data_create(); action=bpy.data.actions.new('Carry_'+name); rig.animation_data.action=action
    end=round(duration*30)+1; scene.frame_start=1; scene.frame_end=end
    measurements=[]
    for frame in range(1,end+1):
        scene.frame_set(frame)
        t=(frame-1)/30
        if name=='Pickup':
            reach=smooth(t/.55); rise=smooth((t-.55)/.65)
            lower=.55*reach*(1-rise); forward=.12+.16*reach; height=1.03-.70*reach*(1-rise); curl=reach
            pose(lower,forward,height,.18,12*reach*(1-rise),curl)
        elif name=='Place':
            bend=smooth(t/.85); rise=smooth((t-.85)/.45)
            pose(.55*bend*(1-rise),.28,1.03-.70*bend*(1-rise),.18,12*bend*(1-rise),1-rise)
        elif name=='Throw':
            wind=smooth(t/.2); push=smooth((t-.2)/.18); recover=smooth((t-.45)/.45)
            pose(.025*wind*(1-recover),.28-.08*wind+.22*push*(1-recover),1.03+.12*wind*(1-recover),.18,6*push*(1-recover),1-push*(1-recover))
        else:
            breath=.003*math.sin(2*math.pi*t/duration)
            pose(0,.28 if name=='Hold' else .22,1.03+breath if name=='Hold' else 1.12+breath,.18,0,1)
        for b in controls:
            for field in ['location','rotation_quaternion' if b.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:
                b.keyframe_insert(field,frame=frame,group=b.name)
        for b in rig.pose.bones:
            for prop in ['IK_FK','IK_Stretch']:
                if prop in b: b.keyframe_insert(f'["{prop}"]',frame=frame,group=b.name)
        measurements.append({'frame':frame,'left_hand':list(rig.matrix_world@rig.pose.bones['DEF-hand.L'].head),
            'right_hand':list(rig.matrix_world@rig.pose.bones['DEF-hand.R'].head),
            'left_foot':list(rig.matrix_world@rig.pose.bones['DEF-foot.L'].head),
            'right_foot':list(rig.matrix_world@rig.pose.bones['DEF-foot.R'].head)})
    action.use_fake_user=True
    scene.frame_set(round((contact or .3)*30)+1)
    bpy.ops.wm.save_as_mainfile(filepath=str(P/f'Heroine_Carry_{name}.blend'))
    report.append({'clip':name,'fps':30,'duration':duration,'contact_seconds':contact,'samples':measurements})
(P/'motion_samples.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CARRY_ACTIONS_CREATED', len(report))
