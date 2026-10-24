import bpy,json
from pathlib import Path
p=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/Heroine_Tripo_Review/PhoneMenu01/UnrealApply01')
bpy.ops.wm.open_mainfile(filepath=str(p.parent/'OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend'))
bpy.context.scene.frame_set(80);bpy.context.view_layer.update()
r=bpy.data.objects['Heroine_Rebuild_GameSkeleton']
out={'bones':{b.name:{'pose':[list(v) for v in b.matrix],'rest':[list(v) for v in b.bone.matrix_local]} for b in r.pose.bones if 'hand_r'==b.name or ('_r' in b.name and any(x in b.name for x in ['index','thumb','middle']))},'meshes':{o.name:{'mods':[(m.name,m.type,m.object.name if m.type=='ARMATURE' and m.object else '') for m in o.modifiers],'hide':o.hide_render} for o in bpy.data.objects if o.type=='MESH'}}
(p/'finger-space.json').write_text(json.dumps(out))
