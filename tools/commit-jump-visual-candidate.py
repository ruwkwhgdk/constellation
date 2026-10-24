"""Run only after user approves the recorded visual candidate."""
import unreal as u,traceback,shutil,json
from pathlib import Path
from datetime import datetime
R=Path(u.Paths.project_dir());out=R/'Saved/JumpAcquisition'/datetime.now().strftime('VisualCommit_%Y%m%d_%H%M%S');out.mkdir(parents=True)
try:
 for rel in ['Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap','SceneDirector/School/DA_JumpAcquisition.uasset']:
  src=R/'Content'/rel;dst=out/'Backup'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 world=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 JUMP_REVIEW_DIR=out
 exec((R/'tools/preview-jump-visual-candidate.py').read_text(encoding='utf8'),globals())
 graph,stage,star=apply_jump_visual_candidate()
 assert u.EditorAssetLibrary.save_loaded_asset(graph,False)
 assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 u.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 reloaded_stage=next(a for a in actors if isinstance(a,u.JumpAcquisitionStage))
 reloaded_star=reloaded_stage.get_editor_property('star')
 mesh=reloaded_star.get_component_by_class(u.StaticMeshComponent)
 assert abs(mesh.get_editor_property('relative_scale3d').x-.28)<.001
 assert mesh.get_material(0).get_name()=='M_StarSurface_Review'
 (out/'saved.json').write_text(json.dumps({'map_saved':True,'graph_saved':True,'map_reload_verified':True,'preview':'VisualCandidate_20261018_211446_699984','star_scale':.28}),encoding='utf8')
except:(out/'error.txt').write_text(traceback.format_exc(),encoding='utf8');u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
