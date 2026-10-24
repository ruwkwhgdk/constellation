"""Scoped S0 wood/cave floor and transparent standing water. No collision changes."""
import unreal as u,json,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/20261017'
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
def material(name):
 m=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else AT.create_asset(name,D,u.Material,u.MaterialFactoryNew())
 M.delete_all_material_expressions(m);m.set_editor_property('used_with_static_lighting',True);return m
class G:
 def __init__(self,m):self.m=m
 def n(self,c,**kw):
  n=M.create_material_expression(self.m,c)
  for k,v in kw.items():n.set_editor_property(k,v)
  return n
 def wire(self,a,b,p='',out=''):assert M.connect_material_expressions(a,out,b,p)
 def prop(self,a,p):assert M.connect_material_property(a,'',p)
 def c(self,v):return self.n(u.MaterialExpressionConstant,r=v)
 def col(self,v):return self.n(u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*v,1))
 def custom(self,code,inputs,typ=u.CustomMaterialOutputType.CMOT_FLOAT1):
  ii=[]
  for name in inputs:
   inp=u.CustomInput();inp.set_editor_property('input_name',name);ii.append(inp)
  n=self.n(u.MaterialExpressionCustom,code=code,inputs=ii,output_type=typ)
  for name,node in inputs.items():self.wire(node,n,name)
  return n
 def tex(self,path,uv,normal=False):
  t=E.load_asset(path);assert t,path
  n=self.n(u.MaterialExpressionTextureSample,texture=t,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else u.MaterialSamplerType.SAMPLERTYPE_COLOR)
  self.wire(uv,n,'UVs');return n
 def lerp(self,a,b,c):
  n=self.n(u.MaterialExpressionLinearInterpolate)
  for p,x in [('A',a),('B',b),('Alpha',c)]:self.wire(x,n,p)
  return n

# World coordinates keep grain scale and cave boundaries continuous across all eight tiles.
floor=material('M_S0_WoodCaveFloor');g=G(floor);pos=g.n(u.MaterialExpressionWorldPosition)
uv=g.custom('return P.xy / 300.0;',{'P':pos},u.CustomMaterialOutputType.CMOT_FLOAT2)
stoneuv=g.custom('return P.xy / 420.0;',{'P':pos},u.CustomMaterialOutputType.CMOT_FLOAT2)
edge=g.custom('float w=90*sin(P.y*.006)+45*sin(P.y*.017+1); float d=min(P.x-480-w, min(3120-P.x, 2490-abs(P.y)+100*sin(P.x*.008))); return 1-smoothstep(45,180,d);',{'P':pos})
wood=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_A',uv)
rock=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',stoneuv)
wood=g.custom('return C*.72;',{'C':wood},u.CustomMaterialOutputType.CMOT_FLOAT3)
base=g.lerp(wood,rock,edge);g.prop(base,u.MaterialProperty.MP_BASE_COLOR)
wn=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_N',uv,True)
rn=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',stoneuv,True)
g.prop(g.lerp(wn,rn,edge),u.MaterialProperty.MP_NORMAL)
g.prop(g.lerp(g.c(.46),g.c(.78),edge),u.MaterialProperty.MP_ROUGHNESS)
g.prop(g.c(.32),u.MaterialProperty.MP_SPECULAR)
M.recompile_material(floor);assert E.save_loaded_asset(floor,False)

water=material('M_S0_ShallowWater')
water.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED)
water.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT)
g=G(water);pos=g.n(u.MaterialExpressionWorldPosition);tm=g.n(u.MaterialExpressionTime)
wet=g.custom('float n=sin(P.x*.0035+sin(P.y*.0019)*1.7)+.55*cos(P.y*.0042-P.x*.0015)+.23*sin(P.y*.011+P.x*.007); float b=min(min(P.x-410,3190-P.x),2790-abs(P.y)); return saturate((n+1.05)*12)*saturate(b*.08);',{'P':pos})
g.prop(wet,u.MaterialProperty.MP_OPACITY_MASK)
# Thin-film approximation: identical world-projected substrate, no refractive distortion.
# Opaque deferred planar composition avoids the global forward planar shared by the remote mirror.
uv=g.custom('return P.xy / 300.0;',{'P':pos},u.CustomMaterialOutputType.CMOT_FLOAT2)
stoneuv=g.custom('return P.xy / 420.0;',{'P':pos},u.CustomMaterialOutputType.CMOT_FLOAT2)
edge=g.custom('float w=90*sin(P.y*.006)+45*sin(P.y*.017+1); float d=min(P.x-480-w, min(3120-P.x, 2490-abs(P.y)+100*sin(P.x*.008))); return 1-smoothstep(45,180,d);',{'P':pos})
wood=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_A',uv)
wood=g.custom('return C*.72;',{'C':wood},u.CustomMaterialOutputType.CMOT_FLOAT3)
rock=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',stoneuv)
g.prop(g.lerp(wood,rock,edge),u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.c(.025),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.8),u.MaterialProperty.MP_SPECULAR);g.prop(g.c(.45),u.MaterialProperty.MP_METALLIC)
normal=g.custom('return normalize(float3(.006*sin(P.x*.045+P.y*.018+T*.7),.004*cos(P.y*.036-P.x*.016-T*.5),1));',{'P':pos,'T':tm},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(normal,u.MaterialProperty.MP_NORMAL)
M.recompile_material(water);assert E.save_loaded_asset(water,False)

changed=[]
for i in range(1,9):
 a=actors['classroom_start_floor_'+str(i)];assert abs(a.get_actor_location().z)<.01
 a.modify();a.static_mesh_component.set_material(0,floor);changed.append(a.get_actor_label())
old=[]
for i in range(1,5):
 label='ART_SchoolCave_Puddle%02d'%i;a=actors.get(label)
 if not a:continue
 assert a.get_actor_location().z<3
 old.append(label);A.destroy_actor(a)
label='S0_WetFloor_ShallowWater';a=actors.get(label) or A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(1800,0,1.8))
a.set_actor_label(label);a.set_folder_path('classroom_start/WetFloor');a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Plane'))
a.set_actor_location(u.Vector(1800,0,1.8),False,True);a.set_actor_scale3d(u.Vector(28,56,1));a.static_mesh_component.set_material(0,water);a.set_actor_enable_collision(False)
a.static_mesh_component.set_editor_property('cast_shadow',False)
reflection=actors.get('S0_WetFloor_PlanarReflection') or A.spawn_actor_from_class(u.PlanarReflection,u.Vector(1800,0,1.8))
reflection.set_actor_label('S0_WetFloor_PlanarReflection');reflection.set_folder_path('classroom_start/WetFloor');reflection.set_actor_scale3d(u.Vector(.8,1.5,1))
pc=reflection.get_component_by_class(u.PlanarReflectionComponent)
for k,v in [('normal_distortion_strength',.05),('prefilter_roughness',.015),('distance_from_plane_fadeout_start',10.),('distance_from_plane_fadeout_end',100.),('screen_percentage',75),('show_preview_plane',False)]:pc.set_editor_property(k,v)
pp=actors.get('S0_WetFloor_ReflectionVolume') or A.spawn_actor_from_class(u.SubwayTunnelEnvironment,u.Vector(1800,0,1000))
pp.set_actor_label('S0_WetFloor_ReflectionVolume');pp.set_folder_path('classroom_start/WetFloor')
pp.get_component_by_class(u.BoxComponent).set_box_extent(u.Vector(1400,2800,1100),False)
post=pp.get_component_by_class(u.PostProcessComponent)
post.set_editor_property('unbound',False);post.set_editor_property('priority',100.);post.set_editor_property('blend_radius',100.)
# Reuse the existing bounds-only native actor, clearing its tunnel exposure overrides.
s=u.PostProcessSettings();s.set_editor_property('override_reflection_method',True);s.set_editor_property('reflection_method',u.ReflectionMethod.SCREEN_SPACE)
s.set_editor_property('override_screen_space_reflection_quality',True);s.set_editor_property('screen_space_reflection_quality',100.)
post.set_editor_property('settings',s)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(O/'applied.json').write_text(json.dumps(dict(map=MAP,floors=changed,replaced_puddles=old,water_actor=label,water_depth_cm=1.8,materials=[floor.get_path_name(),water.get_path_name()],preserved='All floor geometry, collision, furniture, gameplay, S0 sequences and props'),indent=2))
u.log('S0_WET_FLOOR_APPLIED')
