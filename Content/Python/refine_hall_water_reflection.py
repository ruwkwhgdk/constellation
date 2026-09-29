"""Shallow water with dynamic planar reflections for the maintained hall."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v006'
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
cvars={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ['r.ReflectionMethod','r.DynamicGlobalIlluminationMethod','r.GenerateMeshDistanceFields','r.AllowGlobalClipPlane','r.Water.SingleLayer.Reflection']}
(OUT/'reflection_diagnostic.json').write_text(json.dumps(cvars,indent=2))
assert cvars['r.AllowGlobalClipPlane']==1,'Planar reflection requires engine restart with r.AllowGlobalClipPlane=1'
name='M_OH_PlanarWater';dest=D+'/GrowthMaterials';path=dest+'/'+name
mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew())
mat.modify();ML.delete_all_material_expressions(mat)
mat.set_editor_property('blend_mode',u.BlendMode.BLEND_OPAQUE)
mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT)
mat.set_editor_property('translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
mat.set_editor_property('use_planar_forward_reflections',True)
mat.set_editor_property('use_hq_forward_reflections',True)
mat.set_editor_property('two_sided',True)
def n(cls):return ML.create_material_expression(mat,cls)
def c(v):
    a=n(u.MaterialExpressionConstant);a.r=v;return a
def color(v):
    a=n(u.MaterialExpressionConstant3Vector);a.constant=u.LinearColor(*v,1);return a
def wire(a,b,pin='',out=''):assert ML.connect_material_expressions(a,out,b,pin),(type(b).__name__,pin)
def prop(a,p):assert ML.connect_material_property(a,'',p)
def op(cls,a,b):
    v=n(cls);wire(a,v,'A');wire(b,v,'B');return v
def mul(a,b):return op(u.MaterialExpressionMultiply,a,b)
def add(a,b):return op(u.MaterialExpressionAdd,a,b)
prop(color((.17,.32,.29)),u.MaterialProperty.MP_BASE_COLOR)
prop(c(.045),u.MaterialProperty.MP_ROUGHNESS);prop(c(.80),u.MaterialProperty.MP_SPECULAR)
# Artistic reflective puddle: opaque, intentionally no fabricated transparency.
prop(c(.80),u.MaterialProperty.MP_METALLIC)
pos=n(u.MaterialExpressionWorldPosition);time=n(u.MaterialExpressionTime);waves=[]
for channel,freq,speed,amplitude in [(0,.012,.045,.009),(1,.018,-.032,.006)]:
    mask=n(u.MaterialExpressionComponentMask)
    for i,p in enumerate(['r','g','b','a']):mask.set_editor_property(p,i==channel)
    wire(pos,mask);phase=add(mul(mask,c(freq)),mul(time,c(speed)));sine=n(u.MaterialExpressionSine);wire(phase,sine);waves.append(mul(sine,c(amplitude)))
prop(op(u.MaterialExpressionAppendVector,op(u.MaterialExpressionAppendVector,*waves),c(1)),u.MaterialProperty.MP_NORMAL)
ML.recompile_material(mat);assert E.save_loaded_asset(mat,only_if_is_dirty=False)
w=actors['OH_SM_OH_Blockout_21'];w.modify();w.static_mesh_component.set_material(0,mat);w.static_mesh_component.set_collision_profile_name('NoCollision')
# Preserve the 2.2 cm water level; raised slabs remain visible above it.
w.set_actor_location(u.Vector(0,0,0),False,False)
reflection=actors.get('OH_WaterPlanarReflection') or A.spawn_actor_from_class(u.PlanarReflection,u.Vector(13,690,2.2),u.Rotator())
reflection.set_actor_label('OH_WaterPlanarReflection');reflection.modify();reflection.set_actor_location(u.Vector(13,690,2.2),False,False);reflection.set_actor_scale3d(u.Vector(16,10,1))
pc=reflection.get_component_by_class(u.PlanarReflectionComponent)
for key,value in [('normal_distortion_strength',.25),('prefilter_roughness',.035),('screen_percentage',75),('distance_from_plane_fadeout_start',10.0),('distance_from_plane_fadeout_end',40.0),('show_preview_plane',False),('capture_every_frame',True),('max_view_distance_override',4500.0)]:pc.set_editor_property(key,value)
# Water is single-sided; its backface is culled from the reflected view.
pp=actors['OH_Exposure'];pp.modify();s=pp.get_editor_property('settings')
s.set_editor_property('override_reflection_method',True);s.set_editor_property('reflection_method',u.ReflectionMethod.SCREEN_SPACE)
s.set_editor_property('override_screen_space_reflection_quality',True);s.set_editor_property('screen_space_reflection_quality',100.0)
pp.set_editor_property('settings',s)
assert L.save_current_level()
report=json.loads((OUT/'applied.json').read_text());report.update(water_material=mat.get_path_name(),water_model='Stylized opaque puddle + dynamic planar reflection',water_roughness=.045,water_level_cm=2.2,reflection_screen_percentage=75,physical_transmission=False,interactive_water=False)
(OUT/'applied.json').write_text(json.dumps(report,indent=2))
runpy.run_path(str(ROOT/'Content/Python/verify_hall_growth_water.py'))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v006').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP).replace('unreal_exposure_fixed.png','unreal_growth_water.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next")
script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_reflective_water','exec'),globals())
