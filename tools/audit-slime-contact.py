import unreal as u,json
from pathlib import Path
rows=[]
def v(x):return [x.x,x.y,x.z]
for map in ['/Game/Constellation/Review/CombatCore/L_CombatCore','/Game/Constellation/Review/VFX/L_VFXGallery']:
 u.EditorLoadingAndSavingUtils.load_map(map)
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  for m in a.get_components_by_class(u.SkeletalMeshComponent):
   sk=m.get_editor_property('skeletal_mesh_asset')
   if not sk:continue
   if 'Slime' not in sk.get_name():continue
   row={'map':map,'actor':a.get_actor_label(),'mesh':sk.get_path_name(),'actor_location':v(a.get_actor_location()),'actor_scale':v(a.get_actor_scale3d()),'mesh_transform':str(m.get_relative_transform()),'world_bounds':str(a.get_actor_bounds(False)),'imported_bounds':str(sk.get_bounds())}
   cap=a.get_component_by_class(u.CapsuleComponent)
   if cap:row['capsule']=[cap.get_scaled_capsule_radius(),cap.get_scaled_capsule_half_height()]
   rows.append(row)
Path(u.Paths.project_dir(),'Saved/VFXImplementation/slime-contact-audit.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
u.log('SLIME_AUDIT_DONE '+str(rows))

animations=[]
for path in ['/Game/Constellation/Characters/Shared/Animations/Damaged','/Game/Constellation/Characters/Shared/Animations/Sword_Damaged','/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Damaged','/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_PreviewRelaxed']:
 asset=u.load_asset(path)
 animations.append({'asset':path,'skeleton':str(asset.get_editor_property('skeleton')),'duration':asset.get_play_length(),'tracks':str(u.AnimationLibrary.get_animation_track_names(asset))})
Path(u.Paths.project_dir(),'Saved/VFXImplementation/hit-animation-audit.json').write_text(json.dumps(animations,indent=2),encoding='utf8')
