import unreal as u
from pathlib import Path
import shutil,json
root=Path(u.Paths.project_dir());out=root/'Saved/TutorialToast';out.mkdir(parents=True,exist_ok=True)
paths=['/Game/Constellation/UI/Blueprints/BP_HUD','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object','/Game/Constellation/Gameplay/Interaction/Actors/BP_Sword_Pickup','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence_Transform']
for path in paths:
 src=root/'Content'/(path.removeprefix('/Game/')+'.uasset');backup=out/(src.stem+'-before-toast.uasset')
 if not backup.exists():shutil.copy2(src,backup)
 bp=u.load_asset(path);assert bp
 result=u.TutorialToastEditorLibrary.prepare_toast_caller(bp);assert result is not None and not result,str(result)
 assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
 u.log('TOAST_CALLER_UPDATED '+path)
(out/'migration.json').write_text(json.dumps({'success':True,'paths':paths},indent=2),encoding='utf8')

