import unreal,json
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/Player_Heroine/Animation'
m=unreal.load_asset(B+'/AM_Sword_Attack_Horizontal');a=unreal.load_asset(B+'/Sword_Attack_Horizontal')
assert m and a
report={'montage':m.get_path_name(),'sequence':a.get_path_name(),'length':a.sequence_length,'skeleton':a.get_editor_property('skeleton').get_path_name(),'montage_length':m.sequence_length}
for obj,label in [(m,'montage'),(a,'sequence')]:
 for key in ['rate_scale','blend_in','blend_out','slot_anim_tracks','composite_sections','notifies','enable_root_motion','root_motion_root_lock']:
  try:report[label+'_'+key]=str(obj.get_editor_property(key))
  except Exception:pass
report['sequence_api']=[n for n in dir(unreal.AnimationLibrary) if any(s in n for s in ['notify','section','bone','track'])]
task=unreal.AssetExportTask();task.object=a;task.filename=str(P/'Reference_Attack01.fbx');task.automated=True;task.prompt=False;task.replace_identical=True;task.options=unreal.FbxExportOption()
report['export_ok']=unreal.Exporter.run_asset_export_task(task)
report['montage_api']=[n for n in dir(m) if any(s in n for s in ['section','slot','notify'])]
(P/'reference_unreal.json').write_text(json.dumps(report,indent=2));print('ATTACK_REFERENCE',json.dumps(report))
