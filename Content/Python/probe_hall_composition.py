"""Unsaved camera-only composition candidates; preserve the playable geometry."""
import unreal as u,json,time
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v018';OUT.mkdir(exist_ok=True)
MAP='/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull';L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level(MAP)
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};cam=actors['OH_ReferenceCamera'];cc=cam.get_component_by_class(u.CameraComponent)
p=cam.get_actor_location();r=cam.get_actor_rotation()
baseline=dict(position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],fov=cc.field_of_view,actor_count=len(actors))
(OUT/'baseline.json').write_text(json.dumps(baseline,indent=2))
candidates=[dict(name='height',position=[0,200,115],pitch=r.pitch,fov=cc.field_of_view),dict(name='balanced',position=[0,100,120],pitch=r.pitch,fov=72.7)]
(OUT/'candidates.json').write_text(json.dumps(candidates,indent=2))
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();u.SystemLibrary.execute_console_command(world,'ShowFlag.ReflectionEnvironment 1')
u.EditorPythonScripting.set_keep_python_script_alive(True);started=time.time();index=0;shot=False
def setup(row):
    cam.set_actor_location(u.Vector(*row['position']),False,False);cam.set_actor_rotation(u.Rotator(pitch=row['pitch'],yaw=90,roll=0),False);cc.set_field_of_view(row['fov'])
    u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation());u.EditorLevelLibrary.pilot_level_actor(cam)
setup(candidates[0])
def tick(dt):
    global index,shot,started
    elapsed=time.time()-started
    if elapsed>25 and not shot:
        shot=True;u.AutomationLibrary.take_high_res_screenshot(1200,640,str(OUT/(candidates[index]['name']+'.png')),camera=cam,delay=2)
    if elapsed>35:
        if index==0:index=1;shot=False;started=time.time();setup(candidates[1])
        else:
            u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
