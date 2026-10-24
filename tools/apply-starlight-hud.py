import unreal as u
from pathlib import Path
import shutil
r=Path(u.Paths.project_dir());out=r/'Saved/PlayerHUD'
paths=['/Game/Constellation/UI/Widgets/WBP_PlayerHUD','/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine','/Game/Constellation/Gameplay/Combat/Components/Ac_Stats']
for path in paths:
 src=r/'Content'/(path.removeprefix('/Game/')+'.uasset');bak=out/(src.stem+'-before.uasset')
 if not bak.exists():shutil.copy2(src,bak)
a,b,c=map(u.load_asset,paths)
before=u.ResourceRecoveryLibrary.export_blueprint_graphs(a)
r=u.PlayerHUDStyleEditorLibrary.apply_starlight_hud(a,b,c);assert r is not None and not r,str(r)
assert before==u.ResourceRecoveryLibrary.export_blueprint_graphs(a),'Other HUD functionality changed'
for asset in [a,b,c]:assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
u.log('STARLIGHT_HUD_APPLIED')
