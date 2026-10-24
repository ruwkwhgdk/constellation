import unreal as u,json,re,hashlib,shutil,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WaterEdge_20261023'
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
FILE=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
def norm(v):return re.sub(r'0x[0-9a-fA-F]+','PTR',json.dumps(v,sort_keys=True)).replace('-0.000000','0.000000')
import time
assert u.EditorLoadingAndSavingUtils.load_map(MAP)
u.EditorPythonScripting.set_keep_python_script_alive(True)
started=time.monotonic()
def tick(dt):
 if time.monotonic()-started<25:return
 u.unregister_slate_post_tick_callback(handle)
 perform()
def perform():
 try:
  sha=hashlib.sha256(FILE.read_bytes()).hexdigest()
  assert sha==json.loads((O/'ready.json').read_text())['original_sha']
  A=u.get_editor_subsystem(u.EditorActorSubsystem)
  actual={a.get_name():{'label':a.get_actor_label(),'transform':str(a.get_actor_transform()),'collision':a.get_actor_enable_collision(),'meshes':[{'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else '', 'materials':[m.get_path_name() if m else '' for m in c.get_materials()]} for c in a.get_components_by_class(u.StaticMeshComponent)]} for a in A.get_all_level_actors()}
  assert norm(actual)==norm(json.loads((O/'before.json').read_text()))
  a=next(a for a in A.get_all_level_actors() if a.get_name()=='StaticMeshActor_1962')
  mat=u.load_asset(json.loads((O/'material-audit.json').read_text())['candidate']);assert mat
  a.static_mesh_component.set_material(0,mat)
  assert hashlib.sha256(FILE.read_bytes()).hexdigest()==sha
  shutil.copy2(FILE,O/'AbandonedSchool.before.umap')
  assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),MAP)
  (O/'saved.json').write_text(json.dumps({'before_sha':sha,'after_sha':hashlib.sha256(FILE.read_bytes()).hexdigest(),'material_only_actor':a.get_name()},indent=2))
 except Exception:(O/'apply-error.txt').write_text(traceback.format_exc())
 u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
