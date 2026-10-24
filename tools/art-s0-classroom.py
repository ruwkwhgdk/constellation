"""Reference refinement. Dedicated materials, scoped overrides, unsaved preview."""
import unreal as u,json,math,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ArtPass_20261017'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem)
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
src=(R/'tools/apply-s0-wet-floor.py').read_text()
exec(src[src.index('class G:'):src.index('# World coordinates')])
src=(R/'tools/polish-s0-wet-floor.py').read_text()
exec(src[src.index('NOISE='):src.index('floor=material')])
NOISE=NOISE.replace('struct N {','struct S0Noise {').replace('}; N n;','}; S0Noise n;')
def material(name):
 m=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else AT.create_asset(name,D,u.Material,u.MaterialFactoryNew())
 for n in list(M.get_material_expressions(m)):M.delete_material_expression(m,n)
 assert M.get_num_material_expressions(m)==0
 m.set_editor_property('used_with_static_lighting',True)
 return m
def finish(m):
 M.recompile_material(m);assert E.save_loaded_asset(m,False)
def tri(g,p,normal,path,scale=220):
 uv=[g.custom('return P.'+axes+'/'+str(float(scale))+';',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2) for axes in ['yz','xz','xy']]
 t=[g.tex(path,v,normal) for v in uv]
 vn=g.n(u.MaterialExpressionVertexNormalWS)
 code='float3 w=pow(abs(N),4);w/=max(dot(w,1),.001);'
 if normal:code+='return normalize(float3(A.z*sign(N.x),A.x,A.y)*w.x+float3(B.x,B.z*sign(N.y),B.y)*w.y+float3(C.x,C.y,C.z*sign(N.z))*w.z);'
 else:code+='return A*w.x+B*w.y+C*w.z;'
 return g.custom(code,{'N':vn,'A':t[0],'B':t[1],'C':t[2]},u.CustomMaterialOutputType.CMOT_FLOAT3)

# Plaster: true texture scale, worn patches, restrained damp gradients.
plaster=material('M_S0_ArtPlaster');plaster.set_editor_property('tangent_space_normal',False)
g=G(plaster);p=g.n(u.MaterialExpressionWorldPosition)
clean=tri(g,p,False,'/Game/ModulAbandJPSchool/Textures/T_InPlaster_Clean_A',240)
worn=tri(g,p,False,'/Game/ModulAbandJPSchool/Textures/T_ExPlaster_Worn_A',240)
mask=g.custom(NOISE+'return smoothstep(.38,.68,n.fbm(P.xy/260+P.z/330));',{'P':p})
color=g.lerp(clean,worn,mask)
color=g.custom(NOISE+'''float damp=(1-smoothstep(30,210,P.z))*(.3+.7*n.noise(P.xy/180));
float v=.85+.15*n.fbm(float2(P.x+P.y,P.z)/500);
return C*float3(.52,.49,.42)*v*lerp(1,.55,damp);''',{'C':color,'P':p},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
g.prop(tri(g,p,True,'/Game/ModulAbandJPSchool/Textures/T_ExPlaster_Worn_N',240),u.MaterialProperty.MP_NORMAL)
g.prop(g.c(.82),u.MaterialProperty.MP_ROUGHNESS);finish(plaster)

rock=material('M_S0_ArtRock');rock.set_editor_property('tangent_space_normal',False)
g=G(rock);p=g.n(u.MaterialExpressionWorldPosition);vn=g.n(u.MaterialExpressionVertexNormalWS)
stone=tri(g,p,False,'/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',270)
moss=tri(g,p,False,'/Game/LuosCaves/Textures/Rock_Green_Moss3_Albedo',150)
mask=g.custom(NOISE+'return smoothstep(.43,.68,n.fbm(P.xy/350+P.z/470))*saturate(N.z+.15)*.6;',{'P':p,'N':vn})
base=g.lerp(stone,moss,mask)
g.prop(g.custom('return C*float3(.62,.64,.63);',{'C':base},u.CustomMaterialOutputType.CMOT_FLOAT3),u.MaterialProperty.MP_BASE_COLOR)
g.prop(tri(g,p,True,'/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',270),u.MaterialProperty.MP_NORMAL)
g.prop(g.c(.73),u.MaterialProperty.MP_ROUGHNESS);finish(rock)

# Continuous wetness across the waterline: same substrate and hue on both sides.
WET=NOISE+'''float f=.67*n.fbm(P.xy/480+float2(3.2,6.1))+.20*n.noise(P.xy/73)+.13*n.noise(P.xy/18);
float e=min(min(P.x-425,3170-P.x),2765-abs(P.y));
return smoothstep(.30,.48,f)*smoothstep(0,45,e);'''
for waterflag in [False,True]:
 mat=material('M_S0_ShallowWater_V3' if waterflag else 'M_S0_WoodCaveFloor_V3');g=G(mat)
 mat.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED if waterflag else u.BlendMode.BLEND_OPAQUE)
 p=g.n(u.MaterialExpressionWorldPosition);wet=g.custom(WET,{'P':p});edge=g.custom(EDGE,{'P':p})
 uv=g.custom('return P.xy/300.;',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2)
 wood=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_A',uv)
 wood=g.custom('return lerp(C,dot(C,float3(.333,.333,.333)).xxx,.30)*lerp(float3(.29,.27,.23),float3(.21,.27,.30),W)*lerp(1,.85,W);',{'C':wood,'W':wet},u.CustomMaterialOutputType.CMOT_FLOAT3)
 stone=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',uv)
 stone=g.custom('return C*float3(.40,.46,.46);',{'C':stone},u.CustomMaterialOutputType.CMOT_FLOAT3)
 g.prop(g.lerp(wood,stone,edge),u.MaterialProperty.MP_BASE_COLOR)
 if waterflag:
  g.prop(wet,u.MaterialProperty.MP_OPACITY_MASK)
  tm=g.n(u.MaterialExpressionTime)
  norm=g.custom(NOISE+'''float2 q=P.xy/28;float h=n.noise(q+T*.025);
float dx=(n.noise(q+float2(.08,0)+T*.025)-h)*.22;
float dy=(n.noise(q+float2(0,.08)+T*.025)-h)*.22;
return normalize(float3(dx,dy,1));''',{'P':p,'T':tm},u.CustomMaterialOutputType.CMOT_FLOAT3)
  g.prop(norm,u.MaterialProperty.MP_NORMAL);g.prop(g.c(.035),u.MaterialProperty.MP_ROUGHNESS)
  g.prop(g.c(.9),u.MaterialProperty.MP_SPECULAR);g.prop(g.c(.1),u.MaterialProperty.MP_METALLIC)
 else:
  wn=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_N',uv,True);rn=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',uv,True)
  g.prop(g.lerp(wn,rn,edge),u.MaterialProperty.MP_NORMAL)
  g.prop(g.lerp(g.c(.49),g.c(.13),wet),u.MaterialProperty.MP_ROUGHNESS)
 finish(mat)
 if waterflag:water=mat
 else:floor=mat

changes=[]
for a in actors.values():
 label=a.get_actor_label();pos=a.get_actor_location();center,extent=a.get_actor_bounds(False)
 if not(-850<=center.x<=3250 and abs(center.y)<=2850):continue
 for c in a.get_components_by_class(u.StaticMeshComponent):
  for i,m in enumerate(c.get_materials()):
   if not m:continue
   old=m.get_path_name();new=None
   if label in ['classroom_start_floor_'+str(j) for j in range(1,9)] and i==0:new=floor
   elif label=='S0_WetFloor_ShallowWater':new=water
   elif label.startswith('classroom_start_wall') and 'M_AgedPlaster' in old:new=plaster
   elif label in ['classroom_start_floor_'+str(j) for j in [14,16,17,18,21,22]] and i==0:new=plaster
   elif 'M_DetailedStone' in old and (label.startswith(('ART','SM_LCave','S0_WetPolish'))):new=rock
   if new:c.set_material(i,new);changes.append([a.get_name(),label,c.get_name(),i,old,new.get_path_name()])

# Reveal the textured wall with grazing warm light; the water carries its reflection.
label='S0_Art_WallGrazing'
a=actors.get(label) or A.spawn_actor_from_class(u.SpotLight,u.Vector(950,300,950),u.Rotator(pitch=-45,yaw=180))
a.set_actor_label(label);a.set_folder_path('classroom_start/ArtPass')
c=a.spot_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
c.set_editor_property('intensity_units',u.LightUnits.UNITLESS);c.set_editor_property('use_inverse_squared_falloff',False)
c.set_intensity(.7);c.set_attenuation_radius(1700);c.set_light_color(u.LinearColor(1,.78,.48));c.set_cast_shadows(True)
c.set_editor_property('inner_cone_angle',20.);c.set_editor_property('outer_cone_angle',60.);c.set_editor_property('source_radius',90.)
(O/'allowed-material-changes.json').write_text(json.dumps(changes,indent=2))
exec((R/'tools/detail-s0-art.py').read_text())
rows=[];lights=[]
capture=(R/'tools/review-s0-art.py').read_text()
exec(capture[capture.index('cmd=u.SystemLibrary'):])
