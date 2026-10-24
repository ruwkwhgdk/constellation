"""V9 dedicated plaster and layered rock surfaces. No shared material edits."""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/SurfacePass_20261017'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);AT=u.AssetToolsHelpers.get_asset_tools()
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
review=(R/'tools/review-s0-surface.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2));(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))
source=(R/'tools/art-s0-classroom.py').read_text()
exec(source[source.index("src=(R/'tools/apply-s0-wet-floor.py')"):source.index('# Plaster:')])
plaster=material('M_S0_Plaster_V9');plaster.set_editor_property('tangent_space_normal',False)
g=G(plaster);p=g.n(u.MaterialExpressionWorldPosition)
clean=tri(g,p,False,'/Game/ModulAbandJPSchool/Textures/T_InPlaster_Clean_A',210)
worn=tri(g,p,False,'/Game/ModulAbandJPSchool/Textures/T_ExPlaster_Worn_A',275)
color=g.custom(NOISE+'''float2 q=float2(P.x+P.y,P.z);
float2 warp=float2(n.fbm(q/190),n.fbm(q.yx/260+18))-.5;
float h=n.fbm((q+warp*230)/float2(230,390))+.045*(n.noise(q/12)-.5);
float paint=smoothstep(.34,.38,h);
float drip=smoothstep(.55,.75,n.fbm(q/float2(45,550)));
float damp=(1-smoothstep(0,170,P.z))*.25+drip*.12;
float3 base=lerp(W*float3(.43,.42,.36),C*float3(.60,.56,.47),paint);
return base*lerp(1,.62,damp)*lerp(.9,1.04,n.fbm(q/750));''',{'P':p,'C':clean,'W':worn},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
normal=tri(g,p,True,'/Game/ModulAbandJPSchool/Textures/T_ExPlaster_Worn_N',210)
vn=g.n(u.MaterialExpressionVertexNormalWS)
g.prop(g.custom('return normalize(lerp(V,N,.6));',{'V':vn,'N':normal},u.CustomMaterialOutputType.CMOT_FLOAT3),u.MaterialProperty.MP_NORMAL)
g.prop(g.c(.83),u.MaterialProperty.MP_ROUGHNESS);finish(plaster)
rock=material('M_S0_Rock_V9');rock.set_editor_property('tangent_space_normal',False)
g=G(rock);p=g.n(u.MaterialExpressionWorldPosition);vn=g.n(u.MaterialExpressionVertexNormalWS)
stone=tri(g,p,False,'/Game/LuosCaves/Textures/Rock_Dark_Brown1_Albedo',180)
moss=tri(g,p,False,'/Game/LuosCaves/Textures/Rock_Green_Moss3_Albedo',110)
mask=g.custom(NOISE+'return smoothstep(.43,.66,n.fbm(P.xy/240+P.z/390))*saturate(N.z+.18)*.72;',{'P':p,'N':vn})
base=g.lerp(stone,moss,mask)
color=g.custom(NOISE+'''float macro=n.fbm(float2(P.x+P.y,P.z)/420);
float strata=sin(P.z*.035+n.fbm(P.xy/270)*5);
return C*float3(.39,.41,.39)*lerp(.72,1.12,macro)*lerp(.80,1.,smoothstep(-.7,.2,strata));''',{'P':p,'C':base},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
g.prop(tri(g,p,True,'/Game/LuosCaves/Textures/Rock_Dark_Brown1_Normal',180),u.MaterialProperty.MP_NORMAL)
g.prop(g.c(.78),u.MaterialProperty.MP_ROUGHNESS);finish(rock)
changes=[];local=[]
for a in A.get_all_level_actors():
    p=a.get_actor_location()
    for c in a.get_components_by_class(u.StaticMeshComponent):
        for i,m in enumerate(c.get_materials()):
            if not m:continue
            new=plaster if m.get_path_name()==D+'/M_S0_PeelingPlaster_V6.M_S0_PeelingPlaster_V6' else rock if m.get_path_name()==D+'/M_S0_ArtRock.M_S0_ArtRock' else None
            if new:
                changes.append([a.get_name(),a.get_actor_label(),c.get_name(),i,m.get_path_name(),new.get_path_name()]);c.set_material(i,new)
        if -1000<p.x<4000 and -3000<p.y<3000 and c.static_mesh:
            center,extent=a.get_actor_bounds(False)
            local.append(dict(label=a.get_actor_label(),mesh=c.static_mesh.get_path_name(),center=[center.x,center.y,center.z],extent=[extent.x,extent.y,extent.z],collision=a.get_actor_enable_collision()))
(O/'allowed-material-changes.json').write_text(json.dumps(changes,indent=2));(O/'local-meshes.json').write_text(json.dumps(local,indent=2))
rows=[];lights=[]
exec(review[review.index('cmd=u.SystemLibrary'):])
