import unreal as u
from pathlib import Path
import json
out=Path(u.Paths.project_dir())/'Saved/S0Opening';out.mkdir(exist_ok=True)
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
sub=u.get_editor_subsystem(u.EditorActorSubsystem)
rows=[]
for a in sub.get_all_level_actors():
 name=a.get_name(); label=a.get_actor_label(); cls=a.get_class().get_name()
 if any(s in (name+' '+label+' '+cls).lower() for s in ['playerstart','locker','blackboard','girl','scenedirector','sceneevent','chalk']):
  loc=a.get_actor_location();rot=a.get_actor_rotation();center,ext=a.get_actor_bounds(False)
  rows.append(dict(name=name,label=label,cls=cls,location=[loc.x,loc.y,loc.z],rotation=[rot.pitch,rot.yaw,rot.roll],bounds=[ext.x,ext.y,ext.z]))
(out/'actors.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for path in ['/Game/Constellation/UI/Widgets/WBP_RegionTitle','/Game/Constellation/Environments/School/Blueprints/BP_School_Locker','/Game/Constellation/Characters/NPC/Blueprints/BP_NPC_Little_Girl','/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController']:
 obj=u.load_asset(path)
 if obj:
  try:(out/(path.split('/')[-1]+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(obj),encoding='utf8')
  except Exception as e:u.log_warning(str(e))
(out/'level-bp.txt').write_text(u.ResourceRecoveryLibrary.export_level_blueprint_graphs(w),encoding='utf8')
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True);anims=[]
for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine','AnimSequence'),True):
 p=str(a.package_name)
 if p.startswith('/Game/Constellation/Characters/'):
  obj=a.get_asset();anims.append(dict(path=p,skeleton=str(obj.get_editor_property('skeleton').get_path_name()),length=obj.get_editor_property('sequence_length')))
(out/'animations.json').write_text(json.dumps(anims,ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_AUDIT_COMPLETE')
