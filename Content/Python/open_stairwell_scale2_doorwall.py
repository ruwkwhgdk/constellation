"""Restore architecture-sized doorway; remove added door-sized infill per user."""
import unreal as u, time
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=ROOT/'ArtSource/Stairwell_Modular/Scene/v002'
SOURCE_MAP='/Game/Constellation/Review/Stairwell/Maps/L_Stairwell_Reference'
PLAY_MAP='/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2'
L=u.get_editor_subsystem(u.LevelEditorSubsystem); A=u.get_editor_subsystem(u.EditorActorSubsystem); E=u.EditorAssetLibrary
assert L.load_level(SOURCE_MAP)
records=[]
for a in A.get_all_level_actors():
    n=a.get_actor_label().removeprefix('SWScene_')
    if not n.startswith(('DoorWall','DoorSideTrim')): continue
    c=a.static_mesh_component
    records.append((a.get_actor_label(),a.get_actor_location()*2,a.get_actor_rotation(),a.get_actor_scale3d()*2,c.static_mesh.get_path_name(),[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]))
assert L.load_level(PLAY_MAP)
for a in A.get_all_level_actors():
    if a.get_actor_label().startswith(('SWScale2_DoorInfill','SWScene_DoorWall','SWScene_DoorSideTrim')): A.destroy_actor(a)
for name,pos,rot,scale,mesh,materials in records:
    a=A.spawn_actor_from_class(u.StaticMeshActor,pos,rot); a.set_actor_label(name); a.set_actor_scale3d(scale); a.static_mesh_component.set_static_mesh(E.load_asset(mesh))
    for i,mat in enumerate(materials):
        if mat: a.static_mesh_component.set_material(i,E.load_asset(mat))
assert L.save_current_level()
u.log('SCALE2_DOOR_SIZED_INFILL_REMOVED')
cam=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='SWScene_ReferenceCamera')
u.EditorPythonScripting.set_keep_python_script_alive(True); started=time.time(); requested=False
def tick(dt):
    global requested
    if time.time()-started>30 and not requested:
        requested=True; u.AutomationLibrary.take_high_res_screenshot(1080,1579,str(OUT/'scale2_reference.png'),camera=cam,delay=2)
    if time.time()-started>45:
        u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
