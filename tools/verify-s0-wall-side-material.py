"""Fresh saved-map validation and actual rendered captures; never save the map."""
import unreal as u,json,re,time,traceback,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WallSideMaterial_20261023'
def norm(x):return re.sub(r'0x[0-9a-fA-F]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
actual={}
for a in A.get_all_level_actors():
 actual[a.get_name()]={'label':a.get_actor_label(),'transform':str(a.get_actor_transform()),'collision':a.get_actor_enable_collision(),'meshes':[{'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else '', 'materials':[m.get_path_name() if m else '' for m in c.get_materials()]} for c in a.get_components_by_class(u.StaticMeshComponent)]}
expected=json.loads((O/'after.json').read_text())
(O/'reloaded-actors.json').write_text(json.dumps(actual,indent=2))
(O/'reload-differences.json').write_text(json.dumps({'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected)),'changed':{n:{'expected':expected[n],'actual':actual[n]} for n in set(actual)&set(expected) if norm(actual[n])!=norm(expected[n])}},indent=2))
assert norm(actual)==norm(expected),'Saved actor rows differ from rendered candidate'
assert set(actual)==set(expected)
component_differences={}
for n,v in expected.items():
 assert all(norm(v[k])==norm(actual[n][k]) for k in ('label','transform','collision')),n
 if norm(v['meshes'])!=norm(actual[n]['meshes']):
  assert not v['meshes'] and n.startswith(('BP_Vine_C_','BP_Glass_C_','BP_Break_Floor_C_')),n
  component_differences[n]=actual[n]['meshes']
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('S0_Art_RearCrown_'):
  mesh=a.static_mesh_component.static_mesh
  assert mesh.get_name().startswith('SM_S0_FittedTransition_V28_')
  d=u.DynamicMesh();result=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1]);assert u.GeometryScript_MeshQueries.get_is_closed_mesh(d)
before=json.loads((O/'before.json').read_text())
assert all(norm(v)==norm(actual[n]) for n,v in before.items() if n!='StaticMeshActor_797')
crowns=[a for a in A.get_all_level_actors() if a.get_actor_label().startswith('S0_Art_RearCrown_')]
assert len(crowns)==2 and all(not a.get_actor_enable_collision() for a in crowns)
assert all(a.get_actor_bounds(False)[0].y-a.get_actor_bounds(False)[1].y>1850 for a in crowns)
contacts=[a for a in A.get_all_level_actors() if a.get_actor_label().startswith('S0_Art_RearRockContact_')]
assert len(contacts)==6 and all(not a.get_actor_enable_collision() for a in contacts)
assert all(a.get_actor_bounds(False)[0].y-a.get_actor_bounds(False)[1].y>1780 for a in contacts)
protected=json.loads((R/'ArtSource/SchoolOpening/WetFloor/PROTECTED_LAYOUT.json').read_text())
actors={a.get_name():a for a in A.get_all_level_actors()}
for row in protected['actors']:
 p=actors[row['name']].get_actor_location()
 assert all(abs(v-e)<.1 for v,e in zip([p.x,p.y,p.z],row['position_cm']))
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
sha=hashlib.sha256(mapfile.read_bytes()).hexdigest()
(O/'reload.json').write_text(json.dumps({'actor_labels_transforms_collision_match':True,'preserved_actor_placements':len(before),'component_differences':component_differences,'component_difference_note':'Exact full snapshot parity required against render-editor candidate.','contacts':6,'no_collision':True,'outside_ramp_volumes':True,'sha256':sha},indent=2))
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True)
cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
shots=[('final-concept',(2900,900,700),(-20,-138)),('final-backwall',(1700,400,300),(5,90)),('final-oblique',(600,400,300),(10,65))]
state={'i':0,'t':time.monotonic(),'sent':False,'busy':False}
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  if state['i']>=len(shots):
   assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==sha
   (O/'captures-complete.json').write_text(json.dumps({'map_unchanged':True,'images':[s[0]+'.png' for s in shots]}))
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name,p,r=shots[state['i']];path=O/(name+'.png')
  if state['sent'] and path.exists() and path.stat().st_size>0:
   state.update(i=state['i']+1,t=time.monotonic(),sent=False);return
  if time.monotonic()-state['t']>180:raise RuntimeError('Capture timeout')
  if not state['sent']:
   cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
   if time.monotonic()-state['t']>25:
    assert not path.exists(),'Use fresh output captures'
    state['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
 except Exception:
  (O/'verify-error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick)
