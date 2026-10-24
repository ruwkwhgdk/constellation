import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
base='/Game/Constellation/Characters/Enemies/Slime_Liquid'
source=u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Idle')
factory=u.AnimMontageFactory();factory.target_skeleton=source.get_editor_property('skeleton');factory.source_animation=source
a=u.load_asset(base+'/AM_Slime_Liquid_Idle') or u.AssetToolsHelpers.get_asset_tools().create_asset('AM_Slime_Liquid_Idle',base,u.AnimMontage,factory)
u.EditorAssetLibrary.save_loaded_asset(a,False)
assert abs(a.get_play_length()-4)<.001
(P/'idle-montage-fix.json').write_text(json.dumps({'asset':a.get_path_name(),'duration':a.get_play_length(),'slots':str(a.get_editor_property('slot_anim_tracks'))},indent=2))
