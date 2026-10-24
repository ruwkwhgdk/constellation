import unreal as u,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Enemies/Slime_Liquid';OLD='/Game/Constellation/Characters/Enemies/Slime_Normal'
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
u.EditorLoadingAndSavingUtils.new_blank_map(False)
mesh=u.load_asset(B+'/SKM_Slime_Liquid');sk=mesh.get_editor_property('skeleton')
assert len(sk.get_reference_pose().get_bone_names())==14
assert 160<mesh.get_bounds().box_extent.z*2<175
assert all(x.material_interface for x in mesh.get_editor_property('materials'))
report={'blueprints':[],'clips':[],'drop':[]}
paths=['/Game/Constellation/Characters/Enemies/Blueprints/'+n for n in ['BP_Slime_Base','BP_Slime_Patrol','BP_Slime_Boss','BP_Slime_Yellow']]+['/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Slime','/Game/Constellation/Characters/NPC/Blueprints/BP_NPC_Slime']
for path in paths:
 bp=u.load_asset(path);u.BlueprintEditorLibrary.compile_blueprint(bp)
 actor=actors.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,300))
 components=actor.get_components_by_class(u.SkeletalMeshComponent)
 used=[c for c in components if c.get_editor_property('skeletal_mesh_asset')]
 assert used,(path,'No visible skeletal mesh')
 assert all(c.get_editor_property('skeletal_mesh_asset')==mesh for c in used),(path,[str(c.get_editor_property('skeletal_mesh_asset')) for c in used])
 report['blueprints'].append({'path':path,'components':[{'name':c.get_name(),'transform':str(c.get_relative_transform()),'materials':[str(c.get_material(i)) for i in range(c.get_num_materials())]} for c in used]})
 actors.destroy_actor(actor)
for name in ['Idle','Move','Attack','Damaged','Dead','Jump']:
 a=u.load_asset(OLD+'/Animation/AS_Slime_'+name);assert a.get_editor_property('skeleton')==sk
 if name=='Idle':assert abs(a.get_play_length()-4)<.001
 report['clips'].append({'name':name,'duration':a.get_play_length()})
a=u.load_asset(OLD+'/Animation/AS_Slime_Idle')
positions=[];scales=[]
for f in range(97):
 t=f/24
 r=u.AnimationLibrary.get_bone_pose_for_time(a,'Root',t,False)
 d=u.AnimationLibrary.get_bone_pose_for_time(a,'drop',t,False)
 p=d.translation+r.translation;positions.append(p);scales.append(d.scale3d)
 report['drop'].append({'frame':f,'position':[p.x,p.y,p.z],'scale':[d.scale3d.x,d.scale3d.y,d.scale3d.z]})
assert (positions[0]-positions[-1]).length()<.01,'Idle loop mismatch'
assert max((v-scales[0]).length() for v in scales)<.001,'Drop scale changes'
assert max(abs(p.x-positions[0].x)+abs(p.y-positions[0].y) for p in positions[:23])<.05,'Initial drop is not vertical'
assert max(abs(p.x-positions[73].x)+abs(p.y-positions[73].y) for p in positions[73:89])<.05,'Released drop drifts sideways'
report['success']=True
(P/'asset-verification.json').write_text(json.dumps(report,indent=2))
