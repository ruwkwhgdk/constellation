"""Install the reversible SceneDirector statue route; preserve source BP/sequences."""
import unreal as u
from pathlib import Path
import hashlib, json, shutil
root=Path(u.Paths.project_dir()).resolve()
report=root/'Saved/DirectorIntegration'
report.mkdir(parents=True,exist_ok=True)
original=list((root/'Content/Constellation/Gameplay/Sequences/LevelSequences').glob('*Checkpoint*.uasset'))+[root/'Content/Constellation/Environments/School/Blueprints/BP_School_Girl_Statue.uasset']
def hashes(): return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in original}
before=hashes()
bp_result=u.SceneDirectorLibrary.create_statue_interaction_blueprint()
u.log('INTEGRATION_BP '+str(bp_result))
cls=u.EditorAssetLibrary.load_blueprint_class('/Game/SceneDirector/Statue/BP_StatueDirector')
assert cls, 'Statue child Blueprint generation failed'
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
assert world
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
existing=[a for a in actors.get_all_level_actors() if a.get_class()==cls]
if existing:
    assert len(existing)==1
    statue=existing[0]
else:
    old=[a for a in actors.get_all_level_actors() if a.get_class().get_name()=='BP_School_Girl_Statue_C']
    assert len(old)==1, 'Expected exactly one original statue'
    source=old[0]
    pose=source.get_actor_transform()
    label=source.get_actor_label()
    map_file=root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
    backup=report/'Backup/AbandonedSchool.umap'
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists(): shutil.copy2(map_file,backup)
    children=list(source.get_attached_actors())
    parent=source.get_attach_parent_actor()
    actors.convert_actors([source],cls,'')
    # Commandlets do not select actors, although conversion itself succeeds.
    converted=[a for a in actors.get_all_level_actors() if a.get_class()==cls]
    assert len(converted)==1
    statue=converted[0]
    assert statue.get_attach_parent_actor()==parent
    assert set(statue.get_attached_actors())==set(children)
    statue.set_actor_transform(pose,False,False)
    statue.set_actor_label(label)
component=statue.get_component_by_class(u.SceneDirectorInteractionComponent)
assert component
asset=u.load_asset('/Game/SceneDirector/Statue/DA_StatueInteraction')
# Coordinates used when the original performance was authored; constant on reruns.
u.SceneDirectorLibrary.set_director_authoring_origin(asset,u.Transform(location=u.Vector(-34550,-16750,1750),rotation=u.Rotator(pitch=0,yaw=90,roll=0),scale=u.Vector(1,1,1)))
assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
assert before==hashes(), 'Original BP/sequence changed unexpectedly'
result={'statue':statue.get_path_name(),'class':cls.get_path_name(),'component':component.get_path_name(),'original_hashes':before,'backup':str(report/'Backup/AbandonedSchool.umap')}
(report/'installation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('INTEGRATION_INSTALLED '+json.dumps(result,ensure_ascii=False))
