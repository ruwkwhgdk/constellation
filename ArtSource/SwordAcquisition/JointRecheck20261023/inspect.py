import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;source=P.parent/'GripRevision20261023/Heroine_Sword_RightUpper06.blend'
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
(P/'local-joints.json').write_text(json.dumps(rows))
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
cam=s.camera;cam.data.type='ORTHO';cam.data.ortho_scale=.40
for f in [100,355,457,490]:
 s.frame_set(f);center=r.matrix_world@r.pose.bones['hand_r'].head
 for label,offset in [('palm',(.5,-2,.25)),('back',(-.5,2,.25))]:
  cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(P/f'{f:03d}-{label}.png');bpy.ops.render.render(write_still=True)
assert before==hashlib.sha256(source.read_bytes()).hexdigest();(P/'inspection.json').write_text(json.dumps({'source':str(source),'source_unchanged':True,'sha256':before,'bones':names},indent=2))
