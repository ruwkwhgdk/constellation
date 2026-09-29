import bpy,math
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'rig_bound.blend'))
a=bpy.data.objects['Heroine_AnimationRig'];bpy.context.view_layer.objects.active=a;a.hide_set(False);a.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for i in range(8):
 c=a.data.edit_bones[f'skirt_{i:02}.01'];side='L' if i<5 else 'R';t=a.data.edit_bones['ORG-thigh.'+side]
 b=a.data.edit_bones.new(f'MCH-garment_follow_{i:02}');b.matrix=t.matrix.copy();b.length=.025;b.head=c.head;b.tail=b.head+t.vector.normalized()*.025;b.parent=c.parent;b.use_deform=False;c.parent=b
bpy.ops.object.mode_set(mode='OBJECT')
for i in range(8):
 p=a.pose.bones[f'MCH-garment_follow_{i:02}'];side='L' if i<5 else 'R'
 c=p.constraints.new('COPY_ROTATION');c.name='Thigh follow - animator controls remain additive';c.target=a;c.subtarget='ORG-thigh.'+side;c.target_space='LOCAL';c.owner_space='LOCAL';c.influence=.90
 angle=i*math.pi/4
 outward=Vector((math.sin(angle)*.016,-math.cos(angle)*.026,0))
 local=p.bone.matrix_local.to_quaternion().inverted()@outward
 for axis in range(3):
  d=p.driver_add('location',axis).driver;v=d.variables.new();v.name='bend';v.type='TRANSFORMS';v.targets[0].id=a;v.targets[0].bone_target='ORG-thigh.'+side;v.targets[0].transform_type='ROT_X';v.targets[0].transform_space='LOCAL_SPACE';d.expression=f'{local[axis]:.9f}*min(abs(bend)/0.5,1.5)'
 a.data.collections['MCH'].assign(p.bone) if 'MCH' in a.data.collections else None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'rig_bound.blend'))
