import unreal,json
from pathlib import Path
P=Path(__file__).resolve().parent
w=unreal.load_asset('/Game/Resources/Weapons/SM_Weapon_Sword');m=unreal.load_asset('/Game/Resources/Characters/PC/Player_Heroine/Animation/AM_Sword_Attack_Horizontal')
task=unreal.AssetExportTask();task.object=w;task.filename=str(P/'Reference_Sword.fbx');task.automated=True;task.prompt=False;task.replace_identical=True;task.options=unreal.FbxExportOption()
report={'export_ok':unreal.Exporter.run_asset_export_task(task),'bounds':str(w.get_bounds()),'notifies':[]}
for n in unreal.AnimationLibrary.get_animation_notify_events(m):
 row={'time':unreal.AnimationLibrary.get_anim_notify_event_trigger_time(n),'duration':unreal.AnimationLibrary.get_anim_notify_event_duration(n)}
 for k in ['notify_name','notify','notify_state_class']:
  try:row[k]=str(n.get_editor_property(k))
  except:pass
 report['notifies'].append(row)
report['sections']=[str(m.get_section_name(i)) for i in range(m.get_num_sections())]
report['blend_in']=m.get_editor_property('blend_in').get_editor_property('blend_time');report['blend_out']=m.get_editor_property('blend_out').get_editor_property('blend_time')
(P/'reference_combat.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
