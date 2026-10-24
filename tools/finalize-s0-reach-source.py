import unreal as u
from pathlib import Path
f=Path(u.Paths.project_dir())/'ArtSource/SchoolOpening/ReachPose/AS_Locker_ExitFall_Reach.fbx';assert f.exists()
a=u.load_asset('/Game/Constellation/Characters/Heroine/GamePilot/Locker/AS_Locker_ExitFall_Reach')
a.get_editor_property('asset_import_data').scripted_add_filename(str(f),0,'');assert u.EditorAssetLibrary.save_loaded_asset(a,False)
