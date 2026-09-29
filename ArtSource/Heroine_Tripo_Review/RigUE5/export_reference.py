import unreal
from pathlib import Path
out=Path(__file__).resolve().parent
mesh=unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple')
assert mesh
task=unreal.AssetExportTask()
task.object=mesh
task.filename=str(out/'Quinn_Reference.fbx')
task.automated=True
task.prompt=False
task.replace_identical=True
task.options=unreal.FbxExportOption()
task.options.set_editor_property('level_of_detail',False)
assert unreal.Exporter.run_asset_export_task(task)
print('REFERENCE_EXPORTED',task.filename)
