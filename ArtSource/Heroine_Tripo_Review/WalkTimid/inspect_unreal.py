import unreal,json
from pathlib import Path
P=Path(__file__).resolve().parent
a=unreal.load_asset('/Game/Constellation/Characters/Shared/Animations/Walk')
bs=unreal.load_asset('/Game/Constellation/Characters/Shared/Animations/BS_Move')
report={'walk':a.get_path_name(),'skeleton':a.get_editor_property('skeleton').get_path_name(),'length':a.sequence_length,'source':a.get_editor_property('asset_import_data').get_first_filename()}
registry=unreal.AssetRegistryHelpers.get_asset_registry()
opts=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)
report['abp_dependencies']=[str(x) for x in registry.get_dependencies('/Game/Constellation/Characters/Heroine/Blueprints/ABP_Player_Heroine',opts)]
report['blend_samples']=str(bs.get_editor_property('sample_data'))
task=unreal.AssetExportTask();task.object=a;task.filename=str(P/'Reference_Walk.fbx');task.automated=True;task.prompt=False;task.replace_identical=True;task.options=unreal.FbxExportOption()
report['export_ok']=unreal.Exporter.run_asset_export_task(task)
(P/'reference_unreal.json').write_text(json.dumps(report,indent=2))
print('WALK_INSPECT',report)
