import unreal as u
from pathlib import Path
import hashlib,json
root=Path(u.Paths.project_dir()); original=list((root/'Content/Constellation/Gameplay/Sequences/LevelSequences').glob('*Checkpoint*.uasset'))+[root/'Content/Constellation/Environments/School/Blueprints/BP_School_Girl_Statue.uasset']
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in original}
world=None if u.EditorAssetLibrary.does_asset_exist('/Game/SceneDirector/Statue/DA_StatueInteraction') else u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
result=u.SceneDirectorLibrary.create_statue_performance(world)
u.log('STATUE_RESULT '+str(result))
assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in original}
(root/'Saved/StatueDirector/original-hashes.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
assert u.load_asset('/Game/SceneDirector/Statue/DA_StatueInteraction'),str(result)

a=u.load_asset('/Game/SceneDirector/Statue/DA_StatueInteraction')
u.SceneDirectorLibrary.arrange_director_graph(a)
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
u.log('STATUE_LAYOUT_SAVED')
