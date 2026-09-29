"""Run with Blender in background; never overwrites the input .blend.
blender -b --enable-autoexec --python export_game_rig.py -- --source Heroine_AnimationRig.blend --out animation.fbx --bake --start 1 --end 60
Omit --bake for a bind-pose skeletal FBX. Files in this delivery folder are required.
"""
import bpy,argparse,json,sys,math
from pathlib import Path
from mathutils import Matrix
p=argparse.ArgumentParser();p.add_argument('--source');p.add_argument('--out',required=True);p.add_argument('--bake',action='store_true');p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=1);p.add_argument('--action')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);D=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(Path(args.source).resolve() if args.source else D/'Heroine_AnimationRig.blend'))
rig=bpy.data.objects['Heroine_AnimationRig'];mapping=json.loads((D/'bone_mapping.json').read_text());factor=rig.scale.x
if args.action:
 rig.animation_data_create();rig.animation_data.action=bpy.data.actions[args.action]
with bpy.data.libraries.load(str(D/'Heroine_GameSkeleton.blend')) as (src,dst):dst.objects=[n for n in src.objects if n=='Heroine_GameSkeleton' or n.endswith('_Game')]
for o in dst.objects:
 if o and o.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(o)
game=bpy.data.objects['Heroine_GameSkeleton'];R=Matrix.Rotation(math.pi/2,4,'Z')
if args.bake:
 assert args.end>=args.start
 for frame in range(args.start,args.end+1):
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  for src,dest in sorted(mapping.items(),key=lambda item:len(game.data.bones[item[1]].parent_recursive)):
   mat=R@rig.matrix_world@rig.pose.bones[src].matrix;loc,rot,scale=mat.decompose();pb=game.pose.bones[dest];pb.rotation_mode='QUATERNION';pb.matrix=Matrix.LocRotScale(loc,rot,scale/factor);bpy.context.view_layer.update()
   for field in ['location','rotation_quaternion','scale']:pb.keyframe_insert(field,frame=frame,group=dest)
 bpy.context.scene.frame_start=args.start;bpy.context.scene.frame_end=args.end
else:
 for pb in game.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT')
for o in dst.objects:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=game
bpy.ops.export_scene.fbx(filepath=str(Path(args.out).resolve()),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_armature_deform_only=True,bake_anim=args.bake,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.0,path_mode='COPY',embed_textures=True,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',mesh_smooth_type='FACE')
print('GAME_RIG_EXPORT_OK',args.out)
