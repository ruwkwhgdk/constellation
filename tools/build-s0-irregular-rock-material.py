"""New scoped material: continuous irregular coordinates, dual-scale blending."""
import unreal as u
from pathlib import Path
R=Path(u.Paths.project_dir());E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
name='M_S0_IrregularRock_V24'
assert not E.does_asset_exist(D+'/'+name),'Preserve prior candidate'
source=(R/'tools/apply-s0-wet-floor.py').read_text()
exec(source[source.index('class G:'):source.index('# World coordinates')])
source=(R/'tools/polish-s0-wet-floor.py').read_text()
exec(source[source.index('NOISE='):source.index('WET=')])
NOISE=NOISE.replace('struct N {','struct S0Noise {').replace('}; N n;','}; S0Noise n;')
mat=u.AssetToolsHelpers.get_asset_tools().create_asset(name,D,u.Material,u.MaterialFactoryNew())
mat.set_editor_property('tangent_space_normal',False)
g=G(mat);p=g.n(u.MaterialExpressionWorldPosition);vn=g.n(u.MaterialExpressionVertexNormalWS)
blend=g.custom(NOISE+'return smoothstep(.35,.64,n.fbm(float2(P.x+P.y*.61,P.z+P.y*.27)/370.0));',{'P':p})
def tri(path,normal=False):
 samples=[]
 for axes in ['yz','xz','xy']:
  q=g.custom(NOISE+'float2 q=P.'+axes+';float2 w=float2(n.fbm(q/480.0+11),n.fbm(q.yx/510.0+37))-.5;return q+w*190.0;',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2)
  layers=[]
  for scale,cs,sn,ox,oy in [(260,.7986355,.601815,2.31,5.74),(437,.9205049,-.3907311,9.17,3.46)]:
   uv=g.custom(f'return float2(Q.x*{cs}-Q.y*{sn},Q.x*{sn}+Q.y*{cs})/{scale}.0+float2({ox},{oy});',{'Q':q},u.CustomMaterialOutputType.CMOT_FLOAT2)
   t=g.tex(path,uv,normal)
   if normal:t=g.custom(f'return normalize(float3(T.x*{cs}+T.y*{sn},-T.x*{sn}+T.y*{cs},T.z));',{'T':t},u.CustomMaterialOutputType.CMOT_FLOAT3)
   layers.append(t)
  samples.append(g.lerp(layers[0],layers[1],blend))
 code='float3 w=pow(abs(N),4);w/=max(dot(w,1),.001);'
 code+=('return normalize(float3(A.z*sign(N.x),A.x,A.y)*w.x+float3(B.x,B.z*sign(N.y),B.y)*w.y+float3(C.x,C.y,C.z*sign(N.z))*w.z);' if normal else 'return A*w.x+B*w.y+C*w.z;')
 return g.custom(code,{'N':vn,'A':samples[0],'B':samples[1],'C':samples[2]},u.CustomMaterialOutputType.CMOT_FLOAT3)
stone=tri('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo')
moss=tri('/Game/LuosCaves/Textures/Rock_Green_Moss3_Albedo')
mask=g.custom(NOISE+'float f=n.fbm(float2(P.x+P.y*.7,P.z)/310.0+5);return smoothstep(.49,.72,f)*(.15+.55*saturate(N.z+.15));',{'P':p,'N':vn})
base=g.lerp(stone,moss,mask)
damp=g.custom(NOISE+'return (1-smoothstep(0,150,P.z))*(.25+.65*n.fbm(P.xy/170.0));',{'P':p})
color=g.custom(NOISE+'float macro=n.fbm(float2(P.x+P.y*.57,P.z)/650.0);return C*float3(.39,.41,.39)*lerp(.72,1.12,macro)*lerp(1,.82,W);',{'P':p,'C':base,'W':damp},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
normal=tri('/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',True)
g.prop(g.custom('return normalize(lerp(V,N,.4));',{'V':vn,'N':normal},u.CustomMaterialOutputType.CMOT_FLOAT3),u.MaterialProperty.MP_NORMAL)
g.prop(g.custom(NOISE+'return lerp(.72,.87,n.fbm(float2(P.x+P.y,P.z)/290.0))-W*.12;',{'P':p,'W':damp}),u.MaterialProperty.MP_ROUGHNESS)
M.recompile_material(mat);assert E.save_loaded_asset(mat,False)
