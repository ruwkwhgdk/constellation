"""Run only after user approves the recorded visual candidate."""
import unreal as u,traceback,shutil,json,hashlib
from pathlib import Path
from datetime import datetime
R=Path(u.Paths.project_dir());out=R/'Saved/JumpAcquisition'/datetime.now().strftime('AnimationCommit_%Y%m%d_%H%M%S');out.mkdir(parents=True)
try:
 files=list((R/'Content/Constellation/Characters/Heroine/GamePilot/Interaction').glob('*Star_*.uasset'))+list((R/'Content/Constellation/Characters/Heroine/GamePilot/Interaction').glob('*ReachTouch_Right.uasset'))
 source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 for rel in ['Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap','SceneDirector/School/DA_JumpAcquisition.uasset']:
  src=R/'Content'/rel;dst=out/'Backup'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 world=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 JUMP_REVIEW_DIR=out
 exec((R/'tools/integrate-jump-animations.py').read_text(encoding='utf8'),globals())
 graph,stage,lengths=integrate_jump_animations()
 assert u.EditorAssetLibrary.save_loaded_asset(graph,False)
 assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 u.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 reloaded_stage=next(a for a in actors if isinstance(a,u.JumpAcquisitionStage))
 reloaded_star=reloaded_stage.get_editor_property('star')
 mesh=reloaded_star.get_component_by_class(u.StaticMeshComponent)
 assert len(reloaded_stage.get_editor_property('animation_montages'))==6
 assert mesh.get_material(0).get_name()=='M_StarSurface_Review'
 assert (mesh.get_world_location()-u.Vector(-13713.18454,-2444.458988,-670.310328)).length()<.01
 expected={'skeleton_13':(-13963.18454,-2424.458988,-792),'skeleton_12':(-13713.18454,-2144.458988,-792),'skeleton_14':(-13463.18454,-2424.458988,-792),'skeleton_1':(-13713.18454,-2744.458988,-792)}
 for label,xyz in expected.items():
  actor=next(a for a in actors if a.get_actor_label()==label);assert (actor.get_actor_location()-u.Vector(*xyz)).length()<.01
 assert source_hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 (out/'source-hashes.json').write_text(json.dumps(source_hashes,indent=2))
 (out/'saved.json').write_text(json.dumps({'map_saved':True,'graph_saved':True,'map_reload_verified':True,'animation_lengths':lengths,'source_assets_modified':False}),encoding='utf8')
except:(out/'error.txt').write_text(traceback.format_exc(),encoding='utf8');u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
