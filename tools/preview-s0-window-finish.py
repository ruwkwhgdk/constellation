E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
src=(R/'tools/apply-s0-wet-floor.py').read_text();exec(src[src.index('class G:'):src.index('# World coordinates')])
src=(R/'tools/polish-s0-wet-floor.py').read_text();exec(src[src.index('NOISE='):src.index('floor=material')])
name='M_S0_WindowGlass_V16';assert not E.does_asset_exist(D+'/'+name)
mat=AT.create_asset(name,D,u.Material,u.MaterialFactoryNew());assert mat
mat.set_editor_property('two_sided',True)
g=G(mat);p=g.n(u.MaterialExpressionWorldPosition);origin=g.n(u.MaterialExpressionObjectPositionWS)
local=g.custom('return P-O;',{'P':p,'O':origin},u.CustomMaterialOutputType.CMOT_FLOAT3)
dirt=g.custom(NOISE+'''float edge=smoothstep(.6,1, max(abs(L.y)/180.,abs(L.z)/195.));float streak=n.fbm(P.yz/float2(18,300));return saturate(edge*.7+smoothstep(.57,.8,streak)*.3);''',{'P':p,'L':local})
color=g.custom(NOISE+'''float cloud=n.fbm(P.yz/150.);return lerp(lerp(float3(.008,.016,.019),float3(.017,.027,.029),cloud),float3(.026,.028,.025),D);''',{'P':p,'D':dirt},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
em=g.custom('return C*.18;',{'C':color},u.CustomMaterialOutputType.CMOT_FLOAT3);g.prop(em,u.MaterialProperty.MP_EMISSIVE_COLOR)
g.prop(g.lerp(g.c(.19),g.c(.58),dirt),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.65),u.MaterialProperty.MP_SPECULAR)
M.recompile_material(mat);assert E.save_loaded_asset(mat,False)
changes=[]
for a in A.get_all_level_actors():
 if not a.get_actor_label().startswith('ART3_WindowInfill'):continue
 c=a.static_mesh_component;changes.append(dict(name=a.get_name(),label=a.get_actor_label(),old=c.get_material(0).get_path_name(),new=mat.get_path_name()));c.set_material(0,mat)
assert len(changes)==5
(O/'changes.json').write_text(json.dumps(changes,indent=2))
tag='art1';S.update(i=0,sent=False,t=time.monotonic())
