import unreal as u,json,shutil
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/VFXImplementation';a=u.EditorAssetLibrary;levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
source='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool';src=root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap';backup=out/'Before/AbandonedSchool.umap'
if not backup.exists():shutil.copy2(src,backup)
assert levels.load_level(source)
existing={x.get_actor_label():x for x in actors.get_all_level_actors()};placements=[]
for key in ['cave_start','cave_slope_slime','cave_mushroom_jump','cave_slime','large_cave_passage']:
 anchor=existing.get(key)
 if not anchor:continue
 name='VFX_Ambience_'+key
 actor=existing.get(name) or actors.spawn_actor_from_class(u.ConstellationCaveFX,anchor.get_actor_location()+u.Vector(0,0,30))
 actor.set_actor_label(name);actor.set_folder_path('Constellation/VFX/Cave')
 actor.set_editor_property('radius',300.);actor.set_editor_property('ceiling_height',260.);actor.set_editor_property('spores','mushroom' in key);actor.set_editor_property('active_distance',1800.)
 placements.append({'label':name,'location':str(actor.get_actor_location())})
relay=existing.get('VFX_GlassFractureRelay') or actors.spawn_actor_from_class(u.ConstellationGlassRelay,u.Vector());relay.set_actor_label('VFX_GlassFractureRelay');relay.set_folder_path('Constellation/VFX/Glass')
assert levels.save_current_level()
# Opt in current maintained battle previews without changing their recipes, animations or statistics.
combat=[]
for path in ['/Game/Constellation/Review/CombatCore/L_CombatCore','/Game/Constellation/Review/CombatCore/L_CombatEncounter','/Game/Constellation/Review/CombatRecipes/SlimeScout_v2/L_Preview']:
 if not a.does_asset_exist(path):continue
 f=root/('Content/'+path.removeprefix('/Game/')+'.umap');b=out/'Before'/f.name.replace('.umap','_'+path.split('/')[-2]+'.umap')
 if not b.exists():shutil.copy2(f,b)
 assert levels.load_level(path)
 count=0
 for actor in actors.get_all_level_actors():
  if isinstance(actor,u.CombatLabCharacter):actor.get_editor_property('combat_vfx').set_editor_property('presentation_enabled',True);count+=1
 assert levels.save_current_level();combat.append({'map':path,'actors':count})
(out/'integration.json').write_text(json.dumps({'school_map':source,'cave':placements,'glass_relay':True,'combat_maps':combat},indent=2),encoding='utf8')
u.log('VFX_INTEGRATION_COMPLETE')
