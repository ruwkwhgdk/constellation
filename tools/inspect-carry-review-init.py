from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview/graphs'
for path in ('/Game/Constellation/Core/BP_GameMode','/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController'):
    asset=u.load_asset(path)
    (out/(asset.get_name()+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(asset),encoding='utf-8')
