"""Fresh-load validation and editor renders; no PIE or saved level changes."""
import unreal as u,json,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SubwayEntrance/Production/v001';L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.EditorAssetLibrary
EXT='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland';INT='/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2'
assert L.load_level(INT)
actors={a.get_actor_label():a for a in A.get_all_level_actors()};back=actors['SE_TravelToExterior'];assert back.get_class().get_name()=='SubwayTravelVolume'
assert L.load_level(EXT)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
assert 'subway_station' not in actors and 'subway_station2' in actors
assert actors['sky_island'].static_mesh_component.static_mesh.get_name()=='SM_SE_IslandWithStairwell'
assert actors['SE_TravelToInterior'].get_editor_property('maximum_foot_height')==9800
checks=[]
for i in range(1,14):
    a=actors['SE_E%02d'%i];c=a.static_mesh_component;assert c.static_mesh
    for j in range(c.get_num_materials()):assert c.get_material(j)
    checks.append(c.static_mesh.get_name())
report=dict(fresh_load=True,modules=checks,reciprocal_volumes_present=True,dummy_removed=True,other_dummy_preserved=True,play_tested=False,screenshots=[])
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
cameras=[]
for name,pos,target in [('unreal_exterior',(5100,-17980,10860),(3900,-19400,10120)),('unreal_descent',(3900,-18910,10210),(3900,-19620,9840))]:
    rot=u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*target));cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(*pos),rot);cam.camera_component.set_field_of_view(62);cameras.append((name,cam))
for cmd in ['r.ScreenPercentage 100','r.AntiAliasingMethod 2','r.TemporalAA.Upsampling 0']:u.SystemLibrary.execute_console_command(world,cmd)
u.EditorLevelLibrary.set_level_viewport_camera_info(cameras[0][1].get_actor_location(),cameras[0][1].get_actor_rotation())
u.EditorLevelLibrary.pilot_level_actor(cameras[0][1])
u.EditorPythonScripting.set_keep_python_script_alive(True);started=time.time();sent=set()
def tick(dt):
    elapsed=time.time()-started
    if elapsed>30 and 'fresh_collision_traces' not in report:
        results=[]
        for x,y,expected in [(3900,-19770,9760),(3900,-19520,9850.667),(4200,-19520,10000),(3900,-18800,10000)]:
            h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,10070),u.Vector(x,y,9600),u.TraceTypeQuery.ECC_VISIBILITY,False,[],u.DrawDebugTrace.NONE,True)
            z=h.to_tuple()[4].z if h else None
            results.append(dict(x=x,y=y,z=z,passed=z is not None and abs(z-expected)<5))
        report['fresh_collision_traces']=results
    for i,(name,cam) in enumerate(cameras):
        if elapsed>35+i*12 and name not in sent:
            sent.add(name)
            u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation());u.EditorLevelLibrary.pilot_level_actor(cam)
            u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(O/(name+'.png')),camera=cam,delay=2)
    if elapsed>65:
        for name,cam in cameras:
            f=O/(name+'.png');report['screenshots'].append(dict(name=name,refreshed=f.exists() and f.stat().st_mtime>started))
        (O/'fresh_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
