import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent/'RigReferenceFit/Delivery'
source=D/'export_game_rig.py'
sys.argv=['blender','--','--source',str(P/'Heroine_Walk_Timid.blend'),'--out',str(P/'AS_player_heroine_new_Walk_Timid.fbx'),'--bake','--start','1','--end','41','--action','Walk_Timid']
code=source.read_text().replace("object_types={'MESH','ARMATURE'}","object_types={'ARMATURE'}").replace('embed_textures=True','embed_textures=False')
scope={'__file__':str(source),'__name__':'__main__'}
exec(compile(code,str(source),'exec'),scope)
import json
from mathutils import Matrix
rig=scope['rig'];game=scope['game'];mapping=scope['mapping']
src=bpy.data.objects['Heroine_DetailFinish2'];dst=bpy.data.objects['Heroine_DetailFinish2_Game']
ids=json.loads((P/'garment_weight_fix.json').read_text())['vertex_ids']
for vid in ids:
 for g in list(dst.data.vertices[vid].groups):dst.vertex_groups[g.group].remove([vid])
 for g in src.data.vertices[vid].groups:
  n=mapping[src.vertex_groups[g.group].name];dst.vertex_groups[n].add([vid],g.weight,'REPLACE')
game.animation_data.action=None
for p in game.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
bpy.ops.export_scene.fbx(filepath=str(P/'SK_player_heroine_new_WalkPreview.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_armature_deform_only=True,bake_anim=False,path_mode='COPY',embed_textures=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',mesh_smooth_type='FACE')
print('WALK_PREVIEW_MESH_EXPORTED',len(ids))
