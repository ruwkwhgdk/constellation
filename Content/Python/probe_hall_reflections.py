"""Read-only saved-level reflection diagnosis; temporary mirror is never saved."""
import unreal as u,json,time
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v006'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull')
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};cam=actors['OH_ReferenceCamera'];water=actors['OH_SM_OH_Blockout_21'];pc=actors['OH_WaterPlanarReflection'].get_component_by_class(u.PlanarReflectionComponent)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
flags={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ['ShowFlag.Translucency','ShowFlag.PlanarReflections','ShowFlag.ReflectionEnvironment','r.AllowGlobalClipPlane','r.ReflectionEnvironment','r.SSR.Quality']}
flags['plane_location']=str(pc.get_world_location());flags['plane_up']=str(pc.get_up_vector());flags['plane_visible']=pc.get_editor_property('visible');flags['plane_hidden']=pc.get_editor_property('hidden_in_game')
(OUT/'reflection_probe.json').write_text(json.dumps(flags,indent=2))
u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())
u.EditorLevelLibrary.pilot_level_actor(cam)
for command in ['ShowFlag.Translucency 1','ShowFlag.PlanarReflections 1','ShowFlag.ReflectionEnvironment 1']:u.SystemLibrary.execute_console_command(world,command)
mat=u.new_object(u.Material);ML=u.MaterialEditingLibrary
for cls,value,p in [(u.MaterialExpressionConstant3Vector,(.65,.65,.65),u.MaterialProperty.MP_BASE_COLOR),(u.MaterialExpressionConstant,1,u.MaterialProperty.MP_METALLIC),(u.MaterialExpressionConstant,.01,u.MaterialProperty.MP_ROUGHNESS)]:
    n=ML.create_material_expression(mat,cls)
    if isinstance(value,tuple):n.constant=u.LinearColor(*value,1)
    else:n.r=value
    ML.connect_material_property(n,'',p)
ML.recompile_material(mat)
started=time.time();stage=0;u.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
    global stage
    elapsed=time.time()-started
    if stage==0 and elapsed>35:
        u.AutomationLibrary.take_high_res_screenshot(1200,640,str(OUT/'probe_water.png'),camera=cam,delay=2);stage=1
    elif stage==1 and elapsed>48:
        water.static_mesh_component.set_material(0,mat);stage=2
    elif stage==2 and elapsed>68:
        u.AutomationLibrary.take_high_res_screenshot(1200,640,str(OUT/'probe_mirror.png'),camera=cam,delay=2);stage=3
    elif elapsed>85:
        u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
