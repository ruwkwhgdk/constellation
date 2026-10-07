"""Migrate audited school cinematics, preserving original assets and live callbacks."""
import unreal as u
from pathlib import Path
from urllib.parse import unquote
import json,shutil,re,hashlib
root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/SceneEventIntegration';backup=out/'Backup'
level='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
assert u.EditorLoadingAndSavingUtils.load_map(level)
sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=sub.get_all_level_actors();by_name={a.get_name():a for a in actors}
def preserve(pkg,ext='.uasset'):
 src=root/'Content'/(pkg.removeprefix('/Game/')+ext);dst=backup/(pkg.removeprefix('/Game/')+ext);dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copy2(src,dst)
preserve(level,'.umap');manifest=[]
for suffix,label in [('Appear_Slime_Event','슬라임 등장'),('Dump_Slime_Star_Obj_Get_Event','슬라임 능력 획득'),('Little_Girl_Event_Mushroom_Cave','버섯 동굴 소녀')]:
 src='/Game/Constellation/Gameplay/Sequences/LevelSequences/LS_AbandonedSchool_'+suffix
 target='/Game/SceneDirector/School/DA_'+suffix;visual='/Game/SceneDirector/School/Visual/LS_'+suffix+'_Visual'
 source=u.load_asset(src);text=u.SceneDirectorLibrary.inspect_legacy_sequence(source,u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world());bindings={}
 for block in re.split(r'(?=BIND )',text):
  match=re.match(r'BIND ([A-F0-9]+)',block);loc=re.search(r'locator uobj://actor\?payload0=(\S+)',block)
  if match and loc:
   path=unquote(loc[1]);name=path.split('PersistentLevel.')[-1]
   assert name in by_name,('Missing source actor',name)
   bindings[match[1]]=by_name[name]
 if u.EditorAssetLibrary.does_asset_exist(target):
  asset=u.load_asset(target);assert not asset.get_editor_property('needs_compile'),target
 else:
  layer=u.load_asset(visual) if u.EditorAssetLibrary.does_asset_exist(visual) else u.EditorAssetLibrary.duplicate_asset(src,visual)
  result=u.SceneDirectorLibrary.create_school_performance(source,layer,bindings,target)
  asset,report=result;assert asset,report;u.log(report)
  assert u.EditorAssetLibrary.save_loaded_asset(layer,False)
  assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
 existing=[a for a in actors if isinstance(a,u.SceneEventBinding) and a.get_editor_property('original_sequence')==source]
 assert len(existing)<=1
 b=existing[0] if existing else sub.spawn_actor_from_class(u.SceneEventBinding,u.Vector())
 b.set_actor_label('연출_'+label);b.set_editor_property('trigger',u.SceneEventTrigger.LEGACY_SEQUENCE);b.set_editor_property('original_sequence',source);b.set_editor_property('director',asset);b.set_editor_property('origin',u.SceneEventOrigin.AUTHORED)
 # Original interaction/volume eligibility remains authoritative during staged migration.
 b.set_editor_property('repeat',u.SceneEventRepeat.EVERY_TIME)
 if 'Little_Girl' in suffix:
  b.set_editor_property('trigger',u.SceneEventTrigger.VOLUME);b.set_editor_property('source',by_name['TriggerVolume_0']);b.set_editor_property('repeat',u.SceneEventRepeat.ONCE_PER_VISIT)
  r=u.SceneDirectorLibrary.disconnect_legacy_volume(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),source);assert r is not None,r
 assert u.SceneDirectorLibrary.set_gameplay_return_duration(asset,1.5) is not None
 assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
 objects={}
 for o in asset.get_editor_property('objects'):
  tag=str(o.get_editor_property('actor_tag'));name=tag.removeprefix('SceneDirector.School.');a=by_name[name];tags=list(a.get_editor_property('tags'))
  if tag not in [str(t) for t in tags]:tags.append(tag);a.set_editor_property('tags',tags)
  objects[o.get_editor_property('key')]=a
 b.set_editor_property('objects',objects)
 manifest.append({'source':src,'director':target,'visual':visual,'binding':b.get_path_name(),'objects':{str(k):v.get_path_name() for k,v in objects.items()}})
p='/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence';preserve(p);star=u.load_asset(p);r=u.SceneDirectorLibrary.connect_mapped_interaction(star);assert r is not None,r;assert u.EditorAssetLibrary.save_loaded_asset(star,False)
(out/'BP_Star_Object_Sequence.connected.txt').write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(star),encoding='utf-8')
assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,False)
for record in json.loads((out/'sequences.json').read_text(encoding='utf-8')):
 file=root/'Content'/(record['path'].removeprefix('/Game/')+'.uasset');assert hashlib.sha256(file.read_bytes()).hexdigest()==record['sha256'],record['path']
(out/'migration.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('SCENE_SCHOOL_MIGRATION_INSTALLED '+str(len(manifest)))
