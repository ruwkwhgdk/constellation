import unreal as u,json
from pathlib import Path
r=Path(u.Paths.project_dir()).resolve();out=r/'Saved/VFXImplementation'
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 label=a.get_actor_label();cls=a.get_class().get_name()
 if any(s in (label+' '+cls).lower() for s in ['cave','mushroom','glass','window','cache','destroy','break']):
  loc=a.get_actor_location();rows.append({'label':label,'class':cls,'path':a.get_path_name(),'location':[loc.x,loc.y,loc.z],'bounds':str(a.get_actor_bounds(False))})
(out/'school-effects-targets.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf8')
# Source sword mesh and skeleton socket information.
mesh=u.load_asset('/Game/Constellation/Characters/Shared/Equipment/SM_Weapon_Sword')
info={'bounds':str(mesh.get_bounds())}
for path in ['/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview']:
 sk=u.load_asset(path)
 if sk:
  info['socket_methods']=[s for s in dir(sk) if 'socket' in s]
  try:info['weapon_socket']=str(sk.find_socket('WeaponSocket'))
  except Exception as e:info['socket_error']=str(e)
(out/'sword-geometry.json').write_text(json.dumps(info,indent=2),encoding='utf8')
u.log('VFX_TARGETS_AUDITED')
