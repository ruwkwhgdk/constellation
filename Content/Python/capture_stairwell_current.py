"""Read-only retained-map audit and best-effort screenshot; never rebuilds the map."""
import unreal as u, json, time
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=ROOT/'ArtSource/Stairwell_Modular/Scene/v002'
E=u.EditorAssetLibrary; A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
R=u.AssetRegistryHelpers.get_asset_registry(); R.scan_paths_synchronous(['/Game/Environment/StairwellModular','/Game/Blueprints/Character/PC/CameraBackups'],True)
audit=json.loads((ROOT/'ArtSource/Stairwell_Modular/Workflow/asset_cleanup.json').read_text())
for p in audit['deleted']: assert not E.does_asset_exist(p),p
maps=['/Game/Environment/StairwellModular/ReviewKit/Maps/L_Stairwell_KitReview','/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_Reference','/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_PlayScale2']
report=dict(status='pass',deleted_packages_absent=True,maps=[],playtest='not_run')
for path in maps:
    assert L.load_level(path),path
    meshes=[]
    for a in A.get_all_level_actors():
        if not isinstance(a,u.StaticMeshActor): continue
        c=a.static_mesh_component
        assert c.static_mesh, a.get_actor_label()
        for i in range(c.get_num_materials()): assert c.get_material(i), (a.get_actor_label(),i)
        meshes.append(a.get_actor_label())
    report['maps'].append(dict(path=path,mesh_actors=len(meshes),missing_meshes_or_materials=0))
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
assert not any(n.startswith('SWScale2_DoorInfill') for n in actors)
for name in ['SWScene_MainStairsNear','SWScene_MainStairsFar','SWScene_NextStairsNear','SWScene_NextStairsFar']:
    center,extent=actors[name].get_actor_bounds(False); assert abs(extent.y*2-480)<.1
report.update(stair_width_cm=480,door_infill_absent=True,current_map=maps[-1])
(OUT/'current_verification.json').write_text(json.dumps(report,indent=2))
cam=actors['SWScene_ReferenceCamera']; world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for cmd in ['r.ScreenPercentage 100','r.AntiAliasingMethod 2','r.TemporalAA.Upsampling 0']: u.SystemLibrary.execute_console_command(world,cmd)
u.EditorPythonScripting.set_keep_python_script_alive(True); started=time.time(); requested=False
def tick(dt):
    global requested
    if time.time()-started>35 and not requested:
        requested=True; u.AutomationLibrary.take_high_res_screenshot(1080,1579,str(OUT/'scale2_reference.png'),camera=cam,delay=2)
    if time.time()-started>50:
        shot=OUT/'scale2_reference.png'
        report['screenshot_refreshed']=shot.exists() and shot.stat().st_mtime>started
        (OUT/'current_verification.json').write_text(json.dumps(report,indent=2))
        u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
