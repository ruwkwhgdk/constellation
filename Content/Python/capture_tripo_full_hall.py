from pathlib import Path
import runpy
import unreal as u
# Finalize convex floor collision through the live editor subsystem unavailable to commandlets.
floor=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/OvergrownHall/TripoFull/Meshes/SM_OH_T_13_Floor')
sm=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
if sm.get_simple_collision_count(floor)==0:
    sm.add_simple_collisions(floor,u.ScriptingCollisionShapeType.BOX)
    floor.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    assert u.EditorAssetLibrary.save_loaded_asset(floor,only_if_is_dirty=False)
runpy.run_path(str(Path(__file__).with_name('verify_tripo_full_hall.py')))
script=Path(__file__).with_name('capture_hall_exposure.py')
source=script.read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v002').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout','/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull').replace('unreal_exposure_fixed.png','unreal_full.png')
exec(compile(source,str(script),'exec'))
