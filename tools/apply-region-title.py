import unreal as u
from pathlib import Path
import shutil
r=Path(u.Paths.project_dir());out=r/'Saved/RegionTitle'
paths=['/Game/Constellation/UI/Widgets/WBP_RegionTitle','/Game/Constellation/Gameplay/Interaction/Actors/BP_RegionTrigger']
for path in paths:
 src=r/'Content'/(path.removeprefix('/Game/')+'.uasset');bak=out/(src.stem+'-before.uasset')
 if not bak.exists():shutil.copy2(src,bak)
a,b=map(u.load_asset,paths);result=u.RegionTitleEditorLibrary.apply_region_title(a,b);assert result is not None and not result,str(result)
for asset in [a,b]:assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
u.log('REGION_TITLE_APPLIED')
