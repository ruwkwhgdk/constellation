import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;source=Path('C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/Heroine_Sword_Final03.blend')
before=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
r=next(o for o in s.objects if o.type=='ARMATURE' and 'hand_r' in o.pose.bones)
names=[n for n in r.pose.bones.keys() if any(n.startswith(k) for k in ['upperarm','lowerarm','hand_'])]
rows=[]
for f in range(1,740):
 s.frame_set(f);row={'frame':f,'bones':{}}
 for n in names:
  b=r.pose.bones[n];q=b.matrix_basis.to_quaternion();swing,twist=q.to_swing_twist('Y')
  row['bones'][n]={'q':list(q),'twist':math.degrees(twist),'swing':math.degrees(swing.angle),'parent':b.parent.name if b.parent else None}
 rows.append(row)
(P/'original-local-joints.json').write_text(json.dumps(rows))
