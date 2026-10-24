"""Owned editor only: fresh baseline, scoped placement, guarded save."""
import unreal as u,json,hashlib,re,traceback,shutil
from pathlib import Path
R=Path(u.Paths.project_dir())
OUT=R/'Saved/S0WetFloor/RearContactsApply_20261022'
OUT.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
def snapshot():
 result={}
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  result[a.get_name()]={'label':a.get_actor_label(),'transform':str(a.get_actor_transform()),'collision':a.get_actor_enable_collision(),'meshes':[{'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else '', 'materials':[m.get_path_name() if m else '' for m in c.get_materials()]} for c in a.get_components_by_class(u.StaticMeshComponent)]}
 return result
def norm(x):return re.sub(r'0x[0-9a-fA-F]+','PTR',json.dumps(x,sort_keys=True))
try:
 original=hashlib.sha256(mapfile.read_bytes()).hexdigest()
 assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 before=snapshot();(OUT/'before.json').write_text(json.dumps(before,indent=2))
 exec(compile((R/'tools/apply-s0-rear-rock-contacts.py').read_text(encoding='utf-8-sig'),'apply-rear-contacts','exec'),globals())
 after=snapshot()
 assert all(n in after and norm(v)==norm(after[n]) for n,v in before.items()),'Existing actor changed'
 added={n:v for n,v in after.items() if n not in before}
 assert len(added)==6 and all(v['label'].startswith('S0_Art_RearRockContact_') and not v['collision'] for v in added.values())
 assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==original,'Concurrent map change'
 shutil.copy2(mapfile,OUT/'AbandonedSchool.before.umap')
 assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 (OUT/'after.json').write_text(json.dumps(after,indent=2))
 (OUT/'saved.json').write_text(json.dumps({'original_sha':original,'saved_sha':hashlib.sha256(mapfile.read_bytes()).hexdigest(),'preserved_actors':len(before),'added':added},indent=2))
except Exception:
 (OUT/'error.txt').write_text(traceback.format_exc())
finally:
 u.SystemLibrary.quit_editor()
