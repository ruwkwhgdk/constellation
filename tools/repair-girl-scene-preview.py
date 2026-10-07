"""Repair the migrated girl scene's dangling heroine attachment; preserve the original sequence.
Run with UnrealEditor-Cmd -run=pythonscript -script=<this file> after closing the editor.
Verifies the level's intermediate parent has the same transform as the retained cave anchor.
Backs up and saves only the visual copy and its compiled SceneDirector DataAsset.
"""
import unreal as u,json,shutil,hashlib
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/SceneFlickerInvestigation'
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
a=u.load_asset('/Game/SceneDirector/School/DA_Little_Girl_Event_Mushroom_Cave')
s=u.load_asset('/Game/SceneDirector/School/Visual/LS_Little_Girl_Event_Mushroom_Cave_Visual')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
objects={str(e.get_editor_property('key')):next(x for x in actors if e.get_editor_property('actor_tag') in x.get_editor_property('tags')) for e in a.get_editor_property('objects')}
hero=objects['Heroine'];anchor=objects['cave_mushroom_jump']
parent=hero.get_attach_parent_actor()
assert parent.get_attach_parent_actor()==anchor
assert parent.get_actor_location().distance(anchor.get_actor_location())<.01
for field in ['pitch','yaw','roll']:
 assert abs(getattr(parent.get_actor_rotation(),field)-getattr(anchor.get_actor_rotation(),field))<.01
for field in ['x','y','z']:
 assert abs(getattr(parent.get_actor_scale3d(),field)-getattr(anchor.get_actor_scale3d(),field))<.001
byname={b.get_name():b for b in s.get_bindings()}
def attach(b):
 return next(sec for t in b.get_tracks() if isinstance(t,u.MovieScene3DAttachTrack) for sec in t.get_sections())
hero_attach=attach(byname['BP_NPC_Player_Heroine']);girl_attach=attach(byname['little_girl'])
for p in [a,s]:
 src=root/'Content'/(p.get_path_name().split('.')[0].removeprefix('/Game/')+'.uasset');dest=out/'Backup'/src.relative_to(root/'Content');dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():shutil.copy2(src,dest)
hero_attach.set_constraint_binding_id(girl_attach.get_constraint_binding_id())
result=u.SceneDirectorLibrary.compile_director(a)
assert not a.get_editor_property('needs_compile'),result
assert u.EditorAssetLibrary.save_loaded_asset(s,False)
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
(out/'attachment-repair.json').write_text(json.dumps({'hero':hero.get_path_name(),'verified_level_parent':anchor.get_path_name(),'repaired_visual':s.get_path_name(),'compile':str(result)},ensure_ascii=False,indent=2),encoding='utf-8')
