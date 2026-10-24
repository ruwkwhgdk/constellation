"""Phone motion review candidate only. Never exports or imports to Unreal."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).parent
assert (P/"Audit01/before_snapshot.json").exists()
out=P/"Candidate10";out.mkdir(exist_ok=False)
s=bpy.context.scene
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
s.frame_set(1);bpy.context.view_layer.update()
basis={b.name:b.matrix_basis.copy() for b in r.pose.bones}
r.animation_data_clear()
r.animation_data_create();r.animation_data.action=bpy.data.actions.new("Phone_DrawHoldStow_Review01")
for o in bpy.data.objects:
 if o.type=="MESH" and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:
   if k.name.startswith("CarryPickup"):k.value=0
bpy.data.objects["Chair"].hide_render=True
bpy.data.objects["Chair"].hide_set(True)
def pos(n):return r.matrix_world@r.pose.bones[n].head
def mat(n):return r.matrix_world@r.pose.bones[n].matrix
def setm(n,m):
 r.pose.bones[n].matrix=r.matrix_world.inverted()@m
 bpy.context.view_layer.update()
def swing(n,child,t):
 m=mat(n);p=pos(n)
 q=(pos(child)-p).normalized().rotation_difference((t-p).normalized())
 setm(n,Matrix.Translation(p)@q.to_matrix().to_4x4()@Matrix.Translation(-p)@m)
def ik(target,pole):
 a,b,c="upperarm_l","lowerarm_l","hand_l"
 h,k,w=pos(a),pos(b),pos(c);l1=(k-h).length;l2=(w-k).length
 v=target-h;d=min(v.length,l1+l2-.015);axis=v.normalized()
 bend=(pole-axis*pole.dot(axis)).normalized()
 x=(l1*l1-l2*l2+d*d)/(2*d)
 elbow=h+axis*x+bend*math.sqrt(max(0,l1*l1-x*x))
 swing(a,b,elbow);swing(b,c,h+axis*d)
 return max(0,v.length-d)
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
def rotation(finger,ulnar):
 x=Vector(finger).normalized();y=Vector(ulnar);y=(y-x*x.dot(y)).normalized();z=x.cross(y)
 return Matrix((x,y,z)).transposed().to_quaternion()
# World mapping of the rest hand's +X finger axis, +Y ulnar axis.
qdown=rotation((0,0,-1),(0,1,0))
qpocket=rotation((0,0,-1),(-1,0,0))
qhold=rotation((-.20,-.40,.90),(.98,0,.2))
rest=r.data.bones["hand_l"].matrix_local.to_quaternion()
bpy.ops.mesh.primitive_cube_add(size=1)
phone=bpy.context.object;phone.name="Phone_ReviewCube";phone.dimensions=(.07,.012,.14)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
material=bpy.data.materials.new("Phone_Placeholder_Dark");material.diffuse_color=(.035,.055,.085,1);phone.data.materials.append(material)
# Forearm/hand continuity: phone is rigid relative to hand; no independent wrist-only tracking.
phone_offset=Vector((.090,-.010,.024))
phone_rest_rotation=Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
metrics=[]
s.frame_start=1;s.frame_end=151;s.render.fps=30
previous={}
for f in range(1,152):
 s.frame_set(f)
 for b in r.pose.bones:b.matrix_basis=basis[b.name].copy()
 for n in ("spine_01","spine_02","spine_03","neck_01","neck_02","head"):
  r.pose.bones[n].rotation_mode="QUATERNION";r.pose.bones[n].rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
 # Separate approach, contact, lift, hold, lower and release; eased at every contact.
 t=min(f,46) if f<=91 else max(1,137-f)
 reach=smooth((t-1)/17);lift=smooth((t-23)/23)
 target=Vector((.22,-.015,.805)).lerp(Vector((.15,-.065,1.00)),reach)
 target=target.lerp(Vector((.20,-.30,1.18)),lift)
 q=qdown.slerp(qpocket,reach).slerp(qhold,lift)
 pocketpole=Vector((.5,.2,-1)).lerp(Vector((.6,.6,.3)),reach)
 err=ik(target,pocketpole.lerp(Vector((.5,.2,-1)),lift))
 # Keep wrist extension within a modest envelope by matching the full forearm axis.
 forward=(pos("hand_l")-pos("lowerarm_l")).normalized()
 finger=q@Vector((1,0,0));angle=finger.angle(forward)
 if angle>math.radians(23):
  correction=Quaternion().slerp(finger.rotation_difference(forward),(angle-math.radians(23))/angle)
  q=correction@q
 hm=Matrix.LocRotScale(pos("hand_l"),q@rest,Vector((1,1,1)));setm("hand_l",hm)
 grip=smooth((t-15)/10)
 # Different MCP/PIP/DIP flexions preserve an arched grip, not a uniform fist.
 for finger,angles in {"index":(7,2,1),"middle":(5,3,2),"ring":(7,3,2),"pinky":(8,5,3)}.items():
  for j,angle in enumerate(angles,1):
   name=f"{finger}_{j:02}_l"
   pb=r.pose.bones[name]
   axis=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,1,0))
   pb.rotation_mode="QUATERNION"
   pb.rotation_quaternion=Quaternion(axis,math.radians(-angle*(.20+.80*grip)))
   if j==1:
    spread={"index":6,"middle":0,"ring":-4,"pinky":-10}[finger]
    adduction=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
    pb.rotation_quaternion=Quaternion(adduction,math.radians(spread*grip))@pb.rotation_quaternion
 for j,angle in enumerate((0,45,20),1):
  pb=r.pose.bones[f"thumb_{j:02}_l"];pb.rotation_mode="QUATERNION"
  axis=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,1,0))
  pb.rotation_quaternion=Quaternion(axis,math.radians(-angle*grip))
  if j==1:
   abduction=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
   pb.rotation_quaternion=Quaternion(abduction,math.radians(-5*grip))@pb.rotation_quaternion
 for finger,angles in {"index":(6,12,7),"middle":(9,16,10),"ring":(12,19,12),"pinky":(15,22,14)}.items():
  for j,angle in enumerate(angles,1):
   pb=r.pose.bones[f"{finger}_{j:02}_r"];pb.rotation_mode="QUATERNION"
   axis=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,1,0))
   pb.rotation_quaternion=Quaternion(axis,math.radians(angle))
   if j==1:
    adduction=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
    pb.rotation_quaternion=Quaternion(adduction,math.radians({"index":-6,"middle":0,"ring":4,"pinky":10}[finger]))@pb.rotation_quaternion
 bpy.context.view_layer.update()
 # Opposed thumb wraps the side; solve connected joints in the prop frame.
 handrotation=(mat("hand_l").to_quaternion()@rest.inverted())
 pm=Matrix.LocRotScale(pos("hand_l")+handrotation@phone_offset,handrotation@phone_rest_rotation,Vector((1,1,1)))
 for bone,child,goal in [
  ("thumb_01_l","thumb_02_l",(-.037,-.018,-.073)),
  ("thumb_02_l","thumb_03_l",(-.043,.000,-.070))]:
  old=r.pose.bones[bone].rotation_quaternion.copy()
  swing(bone,child,pm@Vector(goal))
  solved=r.pose.bones[bone].rotation_quaternion.copy()
  r.pose.bones[bone].rotation_quaternion=old.slerp(solved,grip)
  bpy.context.view_layer.update()
 bone="thumb_03_l";pb=r.pose.bones[bone];m=mat(bone);p=pos(bone)
 delta=(r.matrix_world@pb.tail-p).rotation_difference(pm@Vector((-.034,.012,-.067))-p)
 old=pb.rotation_quaternion.copy()
 setm(bone,Matrix.Translation(p)@delta.to_matrix().to_4x4()@Matrix.Translation(-p)@m)
 pb.rotation_quaternion=old.slerp(pb.rotation_quaternion,grip)
 bpy.context.view_layer.update()
 # Soft neck inclination toward the raised phone, spread over neck and head.
 for name,deg in [("neck_01",4),("head",6)]:
  pb=r.pose.bones[name];pb.rotation_quaternion=Quaternion((1,0,0),math.radians(deg*lift))
 bpy.context.view_layer.update()
 for pb in r.pose.bones:
  pb.rotation_mode="QUATERNION"
  if pb.name in previous and pb.rotation_quaternion.dot(previous[pb.name])<0:pb.rotation_quaternion.negate()
  previous[pb.name]=pb.rotation_quaternion.copy()
  pb.keyframe_insert("rotation_quaternion",frame=f);pb.keyframe_insert("location",frame=f)
 handrotation=(mat("hand_l").to_quaternion()@rest.inverted())
 phone.matrix_world=Matrix.LocRotScale(pos("hand_l")+handrotation@phone_offset,handrotation@phone_rest_rotation,Vector((1,1,1)))
 phone.keyframe_insert("location",frame=f);phone.rotation_mode="QUATERNION";phone.keyframe_insert("rotation_quaternion",frame=f)
 phone.hide_render=t<22;phone.hide_viewport=phone.hide_render
 phone.keyframe_insert("hide_render",frame=f);phone.keyframe_insert("hide_viewport",frame=f)
 fingeraxis=(pos("middle_01_l")-pos("hand_l")).normalized()
 foreaxis=(pos("hand_l")-pos("lowerarm_l")).normalized()
 metrics.append({"frame":f,"hand":list(pos("hand_l")),"elbow":list(pos("lowerarm_l")),"reach_excess":err,"wrist_angle":math.degrees(fingeraxis.angle(foreaxis))})
for action in (r.animation_data.action,phone.animation_data.action):
 for slot in action.slots:
  for layer in action.layers:
   for strip in layer.strips:
    bag=strip.channelbag(slot)
    if bag:
     for curve in bag.fcurves:
      for key in curve.keyframe_points:key.interpolation="LINEAR"
s.render.engine="BLENDER_WORKBENCH";s.display.shading.color_type="TEXTURE";s.display.shading.light="STUDIO"
s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type="BOTH"
s.display.shading.background_type="WORLD";s.world.color=(.10,.11,.13)
s.render.resolution_x=720;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"
s.camera.data.type="ORTHO"
s.frame_set(61)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"Heroine_Phone_Review10.blend"))
(out/"motion_metrics.json").write_text(json.dumps(metrics,indent=2))
for f in (1,18,24,35,46,91,120,145):
 s.frame_set(f)
 for view,center,offset,scale in [
  ("front",(0,-.05,.85),(1,-4,1.2),1.9),
  ("side",(0,-.1,1),(4,-.2,.4),1.6),
  ("hand",(.13,-.29,1.1),(.45,-1,.6),.50)]:
  center=Vector(center);s.camera.location=center+Vector(offset)
  s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
  s.camera.data.ortho_scale=scale;s.render.filepath=str(out/f"{view}_{f:03}.png")
  bpy.ops.render.render(write_still=True)

