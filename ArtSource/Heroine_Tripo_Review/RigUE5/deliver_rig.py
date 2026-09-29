import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;D=P/'Delivery';D.mkdir(exist_ok=True)
S=P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend'
source_hash=hashlib.sha256(S.read_bytes()).hexdigest()
exec((P/'test_poses.py').read_text().split('poses=sys.argv')[0])
reset();bpy.context.view_layer.update()
meshes=[o for o in sc.objects if o.type=='MESH' and not o.name.startswith('WGT-')]
body=bpy.data.objects['Heroine_DetailFinish2']
height=max((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)-min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)
factor=1.6/height
report={'height_m':1.6,'scale_factor':factor,'source_sha256':source_hash,'skin_weights':{},'rest_deformation_max':{},'pose_transfer_max_m':{}}
for o in meshes:
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 report['rest_deformation_max'][o.name]=max((m.vertices[i].co-v.co).length for i,v in enumerate(o.data.vertices));ev.to_mesh_clear()
 counts=[len(v.groups) for v in o.data.vertices];sums=[sum(g.weight for g in v.groups) for v in o.data.vertices]
 report['skin_weights'][o.name]={'vertices':len(counts),'max_influences':max(counts),'unweighted':sum(n==0 for n in counts),'max_normalization_error':max(abs(w-1) for w in sums)}
# Persist named, static QA poses on the artist rig. They are inspection aids, not production clips.
for label in ['relaxed','bend','squat']:
 if rig.animation_data:rig.animation_data.action=None
 pose(label)
 for p in rig.pose.bones:
  if p.name.startswith(('ORG-','MCH-','DEF-','VIS_')):continue
  p.keyframe_insert('location',frame=1,group=p.name);p.keyframe_insert('rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler',frame=1,group=p.name);p.keyframe_insert('scale',frame=1,group=p.name)
  if 'IK_FK' in p:p.keyframe_insert('["IK_FK"]',frame=1,group=p.name)
 rig.animation_data.action.name='QA_'+label;rig.animation_data.action.use_fake_user=True
 # Preserve drivers: clear only the active Action, never animation_data_clear on a generated rig.
 rig.animation_data.action=None
# Reload the bound rig to retain its original drivers after QA action creation.
qa_actions=[a for a in bpy.data.actions if a.name.startswith('QA_')]
for a in qa_actions:a.use_fake_user=True
# Driver-safe source reload is done through library append of the QA Actions after saving.
bpy.data.libraries.write(str(P/'qa_actions.blend'),set(qa_actions),fake_user=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'rig_bound.blend'))
rig=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene;meshes=[o for o in sc.objects if o.type=='MESH' and not o.name.startswith('WGT-')]
with bpy.data.libraries.load(str(P/'qa_actions.blend')) as (src,dst):dst.actions=[n for n in src.actions if n.startswith('QA_')]
for a in dst.actions:
 if a:a.use_fake_user=True
rig.scale=(factor,)*3
meta=bpy.data.objects.get('Heroine_Metarig')
if meta:meta.scale=(factor,)*3
for o in sc.objects:
 if o.type in ['CAMERA','LIGHT']:
  o.location*=factor
  if o.type=='CAMERA':o.data.ortho_scale*=factor
  elif o.data.type=='AREA':o.data.size*=factor;o.data.energy*=factor*factor
sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1.0
cam=sc.camera;cam.location=Vector((.8,-3,.53))*factor;cam.rotation_euler=(Vector((0,0,.51))*factor-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.12*factor
rig['character_height_cm']=160.0;rig['rig_purpose']='Animation controls; export deforms via export_game_rig.py'
rig['secondary_motion']='Skirt thigh follow + clearance; hair FK. Runtime physics is not installed.'
for p in rig.pose.bones:
 if 'IK_FK' in p:p['IK_FK']=1.0
 if 'IK_Stretch' in p:p['IK_Stretch']=0.0
bpy.context.view_layer.update()
# Generated UI is kept packed; do not change the user's global script security preference.
for t in bpy.data.texts:
 if t.name.endswith('_ui.py'):t.use_module=True
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Heroine_AnimationRig.blend'))

def game_name(n):
 if n=='root':return n
 n=n.removeprefix('DEF-')
 spine={'spine':'pelvis','spine.001':'spine_01','spine.002':'spine_02','spine.003':'spine_03','spine.004':'neck_01','spine.005':'neck_02','spine.006':'head'}
 if n in spine:return spine[n]
 for side in ['L','R']:
  if n.endswith('.'+side+'.001'):return n.split('.')[0].replace('upper_arm','upperarm').replace('forearm','lowerarm').replace('shin','calf')+'_twist_01_'+side.lower()
  if n.endswith('.'+side):
   base=n[:-2].replace('upper_arm','upperarm').replace('forearm','lowerarm').replace('shin','calf').replace('shoulder','clavicle').replace('toe','ball').replace('f_','')
   return base.replace('.','_')+'_'+side.lower()
 return n.replace('.','_').lower()
defs=[b for b in rig.data.bones if b.use_deform];mapping={b.name:game_name(b.name) for b in defs};mapping['root']='root'
def parent_name(b):
 p=b.parent
 while p:
  if p.name in mapping and p.name!=b.name:return mapping[p.name]
  if p.name.startswith('ORG-') and 'DEF-'+p.name[4:] in mapping and 'DEF-'+p.name[4:]!=b.name:return mapping['DEF-'+p.name[4:]]
  p=p.parent
 return 'root'
armdata=bpy.data.armatures.new('Heroine_GameSkeleton');game=bpy.data.objects.new('Heroine_GameSkeleton',armdata);sc.collection.objects.link(game)
bpy.ops.object.select_all(action='DESELECT');game.select_set(True);bpy.context.view_layer.objects.active=game;bpy.ops.object.mode_set(mode='EDIT')
root=armdata.edit_bones.new('root');rb=rig.data.bones['root'];root.head=rb.head_local*factor;root.tail=rb.tail_local*factor;root.align_roll(rb.matrix_local.to_3x3()@Vector((0,0,1)))
for b in defs:
 e=armdata.edit_bones.new(mapping[b.name]);e.head=b.head_local*factor;e.tail=b.tail_local*factor;e.align_roll(b.matrix_local.to_3x3()@Vector((0,0,1)));e.use_deform=True
for b in defs:armdata.edit_bones[mapping[b.name]].parent=armdata.edit_bones[parent_name(b)]
bpy.ops.object.mode_set(mode='OBJECT')
export_meshes=[]
for o in meshes:
 cp=o.copy();cp.data=o.data.copy();sc.collection.objects.link(cp);cp.name=o.name+'_Game';cp.parent=None;cp.matrix_world.identity();cp.data.transform(o.matrix_world)
 for m in list(cp.modifiers):cp.modifiers.remove(m)
 for g in cp.vertex_groups:g.name=mapping[g.name]
 m=cp.modifiers.new('Game Skinning','ARMATURE');m.object=game;cp.parent=game;export_meshes.append(cp)
def match_pose():
 bpy.context.view_layer.update()
 for src,dest in sorted(mapping.items(),key=lambda item:len(game.data.bones[item[1]].parent_recursive)):
  mat=rig.matrix_world@rig.pose.bones[src].matrix
  loc,rot,scale=mat.decompose();game.pose.bones[dest].matrix=Matrix.LocRotScale(loc,rot,scale/factor)
  bpy.context.view_layer.update()
for label in ['rest','relaxed','bend','squat']:
 pose(label);match_pose();dg=bpy.context.evaluated_depsgraph_get();worst=0.0
 for orig,cp in zip(meshes,export_meshes):
  a=orig.evaluated_get(dg);b=cp.evaluated_get(dg);ma=a.to_mesh();mb=b.to_mesh()
  worst=max(worst,max(((a.matrix_world@x.co)-(b.matrix_world@y.co)).length for x,y in zip(ma.vertices,mb.vertices)));a.to_mesh_clear();b.to_mesh_clear()
 report['pose_transfer_max_m'][label]=worst
 if label=='squat':
  errors=[]
  for src,dest in mapping.items():
   mat=rig.matrix_world@rig.pose.bones[src].matrix;loc,rot,scale=mat.decompose();target=Matrix.LocRotScale(loc,rot,scale/factor);actual=game.pose.bones[dest].matrix
   errors.append((dest,max(abs(target[i][j]-actual[i][j]) for i in range(4) for j in range(4)),list(scale/factor)))
  report['bone_pose_errors']=sorted(errors,key=lambda x:-x[1])[:12]
pose('rest');match_pose()
for p in game.pose.bones:p.matrix_basis.identity()
# Game asset faces +X with +Z up. Rotate rest skeleton and surface together.
R=Matrix.Rotation(math.pi/2,4,'Z')
game.data.transform(R)
for o in export_meshes:o.data.transform(R)
for o in sc.objects:
 if o.type in ['CAMERA','LIGHT']:o.matrix_world=R@o.matrix_world
for o in list(sc.objects):
 if o not in export_meshes+[game] and o.type not in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
game.select_set(True)
for o in export_meshes:o.select_set(True)
bpy.context.view_layer.objects.active=game
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Heroine_GameSkeleton.blend'))
bpy.ops.export_scene.fbx(filepath=str(D/'Heroine_Skeletal.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_armature_deform_only=True,bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',mesh_smooth_type='FACE')
report['export_bones']=len(game.data.bones);report['triangles']=sum(len(p.vertices)-2 for o in export_meshes for p in o.data.polygons)
report['skeleton']=[{'name':b.name,'parent':b.parent.name if b.parent else None} for b in game.data.bones]
(D/'bone_mapping.json').write_text(json.dumps(mapping,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(D/'Heroine_Skeletal.fbx'))
imported=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');im=[o for o in bpy.context.scene.objects if o.type=='MESH']
report['fbx_bones']=len(imported.data.bones);report['fbx_root_bones']=[b.name for b in imported.data.bones if b.parent is None];report['fbx_triangles']=sum(len(p.vertices)-2 for o in im for p in o.data.polygons)
zs=[(o.matrix_world@v.co).z for o in im for v in o.data.vertices];report['fbx_height_m']=max(zs)-min(zs)
report['fbx_missing_images']=[i.name for i in bpy.data.images if i.source=='FILE' and i.size[0]==0]
report['source_unchanged']=hashlib.sha256(S.read_bytes()).hexdigest()==source_hash
report['pass']=report['source_unchanged'] and report['triangles']==report['fbx_triangles']==70030 and report['fbx_root_bones']==['root'] and abs(report['fbx_height_m']-1.6)<1e-4 and max(report['rest_deformation_max'].values())<1e-5 and max(report['pose_transfer_max_m'].values())<1e-4 and not report['fbx_missing_images']
(D/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATION',json.dumps({k:v for k,v in report.items() if k!='skeleton'}),flush=True)
