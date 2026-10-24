import bpy,math,json
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection12.blend'));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton']
changes={'index':((0,0,-1),[-12,22,0]),'middle':((-1,0,0),[-12,22,-5]),'ring':((0,0,1),[-10,18,-4]),'pinky':((0,0,1),[-6,10,0])}
actions={r.animation_data.action.name:1}
for d in json.loads((P/'clips.json').read_text()).values():actions[d['action']]=d['range'][0]
for name,start in actions.items():
 act=bpy.data.actions[name];curves=[]
 for layer in act.layers:
  for strip in layer.strips:
   for slot in act.slots:
    bag=strip.channelbag(slot)
    if bag:curves.extend(bag.fcurves)
 for finger,(axis,degs) in changes.items():
  for digit,deg in enumerate(degs,1):
   path=f'pose.bones["{finger}_{digit:02}_r"].rotation_quaternion';cs=sorted([c for c in curves if c.data_path==path],key=lambda c:c.array_index)
   assert len(cs)==4,(name,path,len(cs))
   prev=None
   for i in range(len(cs[0].keyframe_points)):
    f=cs[0].keyframe_points[i].co.x;g=start+f-1;t=max(0,min(1,(g-1)/48));wt=t*t*(3-2*t);q=Quaternion(tuple(c.keyframe_points[i].co.y for c in cs));q=Quaternion(axis,math.radians(deg)*wt)@q
    if prev is not None and q.dot(prev)<0:q.negate()
    prev=q.copy()
    for c,v in zip(cs,q):c.keyframe_points[i].co.y=v
   for c in cs:c.update()
s.frame_set(100);bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection13.blend'));print('FINAL_FINGER_KEYS_SAVED')
