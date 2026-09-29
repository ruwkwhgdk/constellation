import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Delivery/Heroine_AnimationRig.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];out={}
bpy.context.view_layer.update()
for side,s in [('L',1),('R',-1)]:
 r.pose.bones['upper_arm_parent.'+side]['IK_FK']=0.0
 p=r.pose.bones['hand_ik.'+side];mat=p.matrix.copy();mat.translation+=Vector((-.05*s,-.025,-.025));p.matrix=mat
 r.pose.bones['thigh_parent.'+side]['IK_FK']=0.0
 p=r.pose.bones['foot_ik.'+side];p.location=p.bone.matrix_local.to_quaternion().inverted()@Vector((.012*s,-.025,.03))
r.update_tag();bpy.context.scene.frame_set(2);bpy.context.view_layer.update()
for side in ['L','R']:
 for limb,goal in [('hand','hand_ik'),('foot','foot_ik')]:
  out[limb+'_'+side+'_IK_error_m']=(r.pose.bones['ORG-'+limb+'.'+side].head-r.pose.bones[goal+'.'+side].head).length*r.scale.x
out['invalid_drivers']=[c.data_path for c in r.animation_data.drivers if not c.driver.is_valid]
out['diagnostics']={n:{'head':list(r.pose.bones[n].head),'tail':list(r.pose.bones[n].tail),'rest_head':list(r.data.bones[n].head_local)} for n in ['ORG-hand.L','hand_ik.L','ORG-upper_arm.L','ORG-forearm.L','ORG-foot.L','foot_ik.L']}
out['endpoint_tolerance_m']=0.00025
out['pass']=max(v for k,v in out.items() if k.endswith('_IK_error_m'))<0.00025 and not out['invalid_drivers']
(P/'Delivery/control_validation.json').write_text(json.dumps(out,indent=2));print(out)
