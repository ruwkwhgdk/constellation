"""Reference refinement. Dedicated materials, scoped overrides, unsaved preview."""
import unreal as u,json,math,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WaterPass_20261017'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem)
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
# Audit the currently loaded maintained map, not a previous turn's snapshot.
review=(R/'tools/review-s0-water.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2))
(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))

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

# Continuous wetness across the waterline: same substrate and hue on both sides.
WET=NOISE+'''float2 warp=float2(n.fbm(P.xy/130),n.fbm(P.yx/170+12))*120;
float f=.72*n.fbm((P.xy+warp)/float2(410,580)+float2(3.2,6.1))+.20*n.fbm(P.xy/65)+.08*n.noise(P.xy/float2(6,32));
float e=min(min(P.x-425,3170-P.x),2765-abs(P.y));
return smoothstep(.30,.45,f)*smoothstep(0,45,e);'''
for waterflag in [False,True]:
 mat=material('M_S0_ShallowWater_V7' if waterflag else 'M_S0_WoodCaveFloor_V7');g=G(mat)
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
  norm=g.custom(NOISE+'''float2 q=P.xy/22;float h=n.noise(q+T*.025);
float dx=(n.noise(q+float2(.08,0)+T*.025)-h)*.4;
float dy=(n.noise(q+float2(0,.08)+T*.025)-h)*.4;
return normalize(float3(dx+.012*sin(P.y*.095+T*.35),dy+.008*cos(P.x*.075-T*.23),1));''',{'P':p,'T':tm},u.CustomMaterialOutputType.CMOT_FLOAT3)
  g.prop(norm,u.MaterialProperty.MP_NORMAL);g.prop(g.custom(NOISE+'return lerp(.045,.105,n.fbm(P.xy/65));',{'P':p}),u.MaterialProperty.MP_ROUGHNESS)
  g.prop(g.c(.65),u.MaterialProperty.MP_SPECULAR);g.prop(g.c(0),u.MaterialProperty.MP_METALLIC)
 else:
  wn=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_N',uv,True);rn=g.tex('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',uv,True)
  g.prop(g.lerp(wn,rn,edge),u.MaterialProperty.MP_NORMAL)
  g.prop(g.lerp(g.c(.49),g.c(.13),wet),u.MaterialProperty.MP_ROUGHNESS)
 finish(mat)
 if waterflag:water=mat
 else:floor=mat

changes=[]
for label,new in [("classroom_start_floor_"+str(i),floor) for i in range(1,9)]+[("S0_WetFloor_ShallowWater",water)]:
 a=actors[label];c=a.static_mesh_component
 changes.append([a.get_name(),label,c.get_name(),0,c.get_material(0).get_path_name(),new.get_path_name()]);c.set_material(0,new)
(O/'allowed-material-changes.json').write_text(json.dumps(changes,indent=2))
rows=[];lights=[]
capture=(R/'tools/review-s0-water.py').read_text();exec(capture[capture.index('cmd=u.SystemLibrary'):])
