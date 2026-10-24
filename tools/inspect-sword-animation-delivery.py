import unreal as u,json,traceback
from pathlib import Path
o=Path(u.Paths.project_dir()).resolve()/'Saved/SwordAcquisition/AnimationIntegration';o.mkdir(parents=True,exist_ok=True)
try:
 u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 sword=next(a for a in actors if a.get_name()=='BP_Sword_Stuck_At_Ground_C_1')
 rows=[]
 for c in sword.get_components_by_class(u.StaticMeshComponent):
  rows.append(dict(name=c.get_name(),mesh=str(c.static_mesh),relative=str(c.get_relative_transform()),world=str(c.get_world_transform()),bounds=str(c.static_mesh.get_bounding_box()) if c.static_mesh else ''))
 hero=u.get_default_object(u.EditorAssetLibrary.load_blueprint_class('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine'))
 (o/'inspection.json').write_text(json.dumps(dict(sword_transform=str(sword.get_actor_transform()),components=rows,hero_mesh=str(hero.mesh.get_relative_transform()),anim=str(hero.mesh.get_editor_property('anim_class'))),indent=2))
 stage=next(a for a in actors if isinstance(a,u.SwordAcquisitionStage))
 try:
  assert stage.get_editor_property('animation_set'),'Animation set missing'
  (o/'contract-red.json').write_text(json.dumps({'passed':True}))
 except Exception as e:(o/'contract-red.json').write_text(json.dumps({'passed':False,'error':str(e)}))
except:(o/'inspection-error.txt').write_text(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
