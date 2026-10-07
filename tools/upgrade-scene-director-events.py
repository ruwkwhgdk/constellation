import unreal as u
from pathlib import Path
import shutil,json,hashlib
root=Path(u.Paths.project_dir()).resolve()
backup=root/'Saved/DirectorRefactor/Backup'
for relative in ['Content/SceneDirector/Statue/DA_StatueInteraction.uasset','Content/SceneDirector/Statue/BP_StatueDirector.uasset','Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap']:
    p=root/relative; dest=backup/relative
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists(): shutil.copy2(p,dest)
r=u.SceneDirectorLibrary.upgrade_statue_interaction()
u.log('DIRECTOR_REFACTOR '+str(r))
assert r is not None,str(r)
asset=u.load_asset('/Game/SceneDirector/Statue/DA_StatueInteraction')
assert len(asset.get_editor_property('entry_conditions'))==1
assert any(str(v.get_editor_property('key'))=='HasInteracted' for v in asset.get_editor_property('bool_variables'))
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
statues=[a for a in actors.get_all_level_actors() if a.get_class().get_name()=='BP_StatueDirector_C']
assert len(statues)==1
c=statues[0].get_component_by_class(u.SceneDirectorInteractionComponent)
assert c and c.get_editor_property('director')
u.log('DIRECTOR_COMPONENT '+c.get_name())
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
manifest=json.loads((root/'Saved/DirectorIntegration/installation.json').read_text(encoding='utf-8-sig'))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in manifest['original_hashes'].items())
u.log('DIRECTOR_REFACTOR_SAVED')
