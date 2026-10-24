import unreal as u,json,shutil
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SchoolOpening/ReachPose';d=json.loads((O/'reach-tracks.json').read_text())
folder='/Game/Constellation/Characters/Heroine/GamePilot/Locker/'
L=u.EditorAssetLibrary;src=u.load_asset(folder+'AS_Locker_ExitFall');dest=folder+'AS_Locker_ExitFall_Reach'
out=u.load_asset(dest) or L.duplicate_asset(folder+'AS_Locker_ExitFall',dest)
co=out.get_editor_property('controller');co.open_bracket('S0 early right arm reach',False)
for n,keys in d['tracks'].items():
 assert co.set_bone_track_keys(n,[u.Vector(*v['t']) for v in keys],[u.Quat(*v['q']) for v in keys],[u.Vector(*v['s']) for v in keys],False)
co.close_bracket(False);assert L.save_loaded_asset(out,False)
mf=R/'Content/Constellation/Characters/Heroine/GamePilot/Locker/AM_Locker_Event.uasset';backup=O/'AM_Locker_Event.before.uasset'
if not backup.exists():shutil.copy2(mf,backup)
m=u.load_asset(folder+'AM_Locker_Event');assert u.LockerAnimationEditorLibrary.configure_locker_montage(m,out,u.load_asset(folder+'AS_Locker_ProneHold'),u.load_asset(folder+'AS_Locker_GetUp'));assert L.save_loaded_asset(m,False)
task=u.AssetExportTask();task.object=out;task.filename=str(O/'AS_Locker_ExitFall_Reach.fbx');task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=u.AnimSequenceExporterFBX();task.options=u.FbxExportOption();assert u.Exporter.run_asset_export_task(task)
out.get_editor_property('asset_import_data').scripted_add_filename(task.filename,0,'');assert L.save_loaded_asset(out,False)
u.log('S0_REACH_IMPORTED '+str(out.get_play_length()))
