import unreal as u,time,json,runpy
from pathlib import Path
root=Path(u.Paths.project_dir()); out=root/'ArtSource/OvergrownHall/Scene/v001'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
cam=next(a for a in actors if a.get_actor_label()=='OH_ReferenceCamera')
pp=next(a for a in actors if a.get_actor_label()=='OH_Exposure')
s=pp.get_editor_property('settings')
assert abs(s.auto_exposure_min_brightness-1024)<.01 and s.auto_exposure_bias==0
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'r.ScreenPercentage 100')
u.EditorPythonScripting.set_keep_python_script_alive(True)
started=time.time(); requested=False
def tick(dt):
    global requested
    elapsed=time.time()-started
    if elapsed>45 and not requested:
        requested=True
        u.AutomationLibrary.take_high_res_screenshot(1200,640,str(out/'unreal_exposure_fixed.png'),camera=cam,delay=2)
    shot=out/'unreal_exposure_fixed.png'
    if (elapsed>65 and shot.exists() and shot.stat().st_mtime>started) or elapsed>110:
        (out/'exposure_render_verification.json').write_text(json.dumps(dict(saved_exposure_verified=True,screenshot=shot.exists() and shot.stat().st_mtime>started,playtest=False),indent=2))
        u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
