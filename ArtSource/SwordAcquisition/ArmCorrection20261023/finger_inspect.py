import bpy,json
from pathlib import Path
P=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Pose09.blend'));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy'];s.frame_set(523);M=sw.matrix_world.inverted()@r.matrix_world
print('PROP',sw.type,[(o.name,list(o.dimensions)) for o in s.objects if 'Sword' in o.name])
for b in r.pose.bones:
 if b.name.endswith('_r') and any(b.name.startswith(n) for n in ['thumb','index','middle','ring','pinky']):print(b.name,'q',list(b.rotation_quaternion),'head',list(M@b.head),'tail',list(M@b.tail))
