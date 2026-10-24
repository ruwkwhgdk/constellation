"""S0 scoped look-development. Trial never saves map; use guarded save after review."""
import unreal as u,json,math,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/Polish_20261017';O.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
# Reuse only graph-builder definitions, not the previous generation/apply code.
src=(R/'tools/apply-s0-wet-floor.py').read_text(encoding='utf8')
exec(src[src.index('def material('):src.index('# World coordinates')])
def material(name):
 m=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else AT.create_asset(name,D,u.Material,u.MaterialFactoryNew())
 # Copy first: UE 5.8 DeleteAll iterates the array that Delete removes from.
 for expression in list(M.get_material_expressions(m)):M.delete_material_expression(m,expression)
 assert M.get_num_material_expressions(m)==0
 m.set_editor_property('used_with_static_lighting',True)
 return m
NOISE='''struct N {
 float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}
 float fbm(float2 p){return .57*noise(p)+.27*noise(p*2.07+12.1)+.11*noise(p*4.13+3.4)+.05*noise(p*8.3+9.7);}
}; N n;
'''
WET=NOISE+'''float f=.68*n.fbm(P.xy/600.0+float2(3.2,6.1))+.23*n.noise(P.xy/85.0)+.09*n.noise(P.xy/22.0);
float e=min(min(P.x-425,3170-P.x),2765-abs(P.y));
return smoothstep(.30,.42,f)*smoothstep(0,35,e);'''
EDGE=NOISE+'''float w=(n.fbm(P.xy/370.0)-.5)*360;
float d=min(P.x-480-w,min(3120-P.x-w*.4,2600-abs(P.y)-w));
return 1-smoothstep(60,300,d);'''
floor=material('M_S0_WoodCaveFloor_V2');g=G(floor);p=g.n(u.MaterialExpressionWorldPosition)
uv=g.custom('return P.xy/360.0;',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2)
ruv=g.custom('return P.xy/360.0;',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2)
wet=g.custom(WET,{'P':p});edge=g.custom(EDGE,{'P':p})
wood=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_A',uv)
wood=g.custom('return C*float3(.23,.24,.23)*lerp(1,.80,W);',{'C':wood,'W':wet},u.CustomMaterialOutputType.CMOT_FLOAT3)
rock=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',ruv)
rock=g.custom('return C*float3(.40,.48,.48);',{'C':rock},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(g.lerp(wood,rock,edge),u.MaterialProperty.MP_BASE_COLOR)
wn=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_N',uv,True);rn=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',ruv,True)
g.prop(g.lerp(wn,rn,edge),u.MaterialProperty.MP_NORMAL)
g.prop(g.lerp(g.c(.52),g.c(.22),wet),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.35),u.MaterialProperty.MP_SPECULAR)
M.recompile_material(floor);assert E.save_loaded_asset(floor,False)
water=material('M_S0_ShallowWater_V2');water.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
water.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT)
g=G(water);p=g.n(u.MaterialExpressionWorldPosition);tm=g.n(u.MaterialExpressionTime);wet=g.custom(WET,{'P':p})
g.prop(wet,u.MaterialProperty.MP_OPACITY_MASK)
uv=g.custom('return P.xy/360.0;',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2)
edge=g.custom(EDGE,{'P':p})
wood=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_A',uv)
wood=g.custom('return lerp(C,dot(C,float3(.333,.333,.333)).xxx,.65)*float3(.11,.22,.32);',{'C':wood},u.CustomMaterialOutputType.CMOT_FLOAT3)
rock=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',uv)
rock=g.custom('return C*float3(.34,.42,.44);',{'C':rock},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(g.lerp(wood,rock,edge),u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.c(.035),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.65),u.MaterialProperty.MP_SPECULAR)
g.prop(g.c(.30),u.MaterialProperty.MP_METALLIC)

normal=g.custom('return normalize(float3(.018*sin(P.x*.065+P.y*.024+T*.38),.012*cos(P.y*.075-P.x*.019-T*.29),1));',{'P':p,'T':tm},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(normal,u.MaterialProperty.MP_NORMAL)
M.recompile_material(water);assert E.save_loaded_asset(water,False)
assert not any(isinstance(n,u.MaterialExpressionSingleLayerWaterMaterialOutput) for n in M.get_material_expressions(water))
for i in range(1,9):actors['classroom_start_floor_'+str(i)].static_mesh_component.set_material(0,floor)
actors['S0_WetFloor_ShallowWater'].static_mesh_component.set_material(0,water)
post=actors['S0_WetFloor_ReflectionVolume'].get_component_by_class(u.PostProcessComponent)
s=post.get_editor_property('settings');s.set_editor_property('reflection_method',u.ReflectionMethod.SCREEN_SPACE);post.set_editor_property('settings',s)
s.set_editor_property('override_lumen_scene_detail',False)
s.set_editor_property('override_lumen_reflection_quality',False)
post.set_editor_property('settings',s)
key=actors['ART_SchoolCave_CeilingKey'].get_component_by_class(u.SpotLightComponent)
key.set_intensity(2.0);key.set_light_color(u.LinearColor(1,.84,.66));key.set_cast_shadows(True)
key.set_editor_property('source_radius',100.0)
fill=actors.get('S0_WetPolish_CaveBounce') or A.spawn_actor_from_class(u.SpotLight,u.Vector(2400,-2200,1000),u.Rotator(pitch=-35,yaw=110))
fill.set_actor_label('S0_WetPolish_CaveBounce');fill.set_folder_path('classroom_start/WetFloor')
c=fill.spot_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
c.set_editor_property('intensity_units',u.LightUnits.UNITLESS);c.set_editor_property('use_inverse_squared_falloff',False)
c.set_intensity(.65);c.set_attenuation_radius(2800);c.set_light_color(u.LinearColor(.22,.65,1));c.set_cast_shadows(True)
c.set_editor_property('inner_cone_angle',24.0);c.set_editor_property('outer_cone_angle',58.0);c.set_editor_property('source_radius',120.0)
exec((R/'tools/finish-s0-wet-polish.py').read_text(encoding='utf8'))
# Capture in-memory trial; save only with save-s0-wet-polish.py after review.
rows=[];lights=[]
capture=(R/'tools/review-s0-wet-polish.py').read_text(encoding='utf8')
exec(capture[capture.index('cmd=u.SystemLibrary'):])





