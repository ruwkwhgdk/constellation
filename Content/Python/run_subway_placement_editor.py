"""Run placement in an editor world with physics initialized, never PIE."""
import unreal as u,runpy,time,traceback
from pathlib import Path
root=Path(u.Paths.project_dir());u.EditorPythonScripting.set_keep_python_script_alive(True)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland')
start=time.time()
def tick(dt):
    if time.time()-start<8:return
    u.unregister_slate_post_tick_callback(handle)
    try:runpy.run_path(str(root/'Content/Python/apply_subway_entrance.py'),run_name='__main__')
    except Exception:
        u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
