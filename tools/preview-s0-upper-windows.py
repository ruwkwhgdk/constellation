E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
src=(R/'tools/apply-s0-wet-floor.py').read_text();exec(src[src.index('class G:'):src.index('# World coordinates')])
src=(R/'tools/polish-s0-wet-floor.py').read_text();exec(src[src.index('NOISE='):src.index('floor=material')])
name='M_S0_UpperWindowBacking_V19';assert not E.does_asset_exist(D+'/'+name)
mat=AT.create_asset(name,D,u.Material,u.MaterialFactoryNew());assert mat
mat.set_editor_property('two_sided',True)
g=G(mat);p=g.n(u.MaterialExpressionWorldPosition)
color=g.custom(NOISE+'''float2 q=float2(P.x+P.y,P.z);
float cloud=n.fbm(q/170.);float streak=smoothstep(.5,.8,n.fbm(q/float2(25,350)));
return lerp(lerp(float3(.009,.017,.020),float3(.021,.030,.032),cloud),float3(.027,.029,.026),streak*.3);''',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.custom('return C*.18;',{'C':color},u.CustomMaterialOutputType.CMOT_FLOAT3),u.MaterialProperty.MP_EMISSIVE_COLOR)
g.prop(g.c(.42),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.45),u.MaterialProperty.MP_SPECULAR)
M.recompile_material(mat);assert E.save_loaded_asset(mat,False)
changes=[]
for a in A.get_all_level_actors():
 if not a.get_actor_label().startswith('ClassroomStart_ExteriorWindowBlackout_') or a.get_actor_location().z<1000:continue
 c=a.static_mesh_component;old=c.get_material(0)
 assert old.get_name()=='M_ClassroomStart_WindowBlackout'
 changes.append(dict(name=a.get_name(),label=a.get_actor_label(),old=old.get_path_name(),new=mat.get_path_name()))
 c.set_material(0,mat)
assert 20<=len(changes)<=30,len(changes)
(O/'changes.json').write_text(json.dumps(changes,indent=2))
tag='art1';shots=[('upper',(1400,-2300,1300),(5,180)),('reverse',(3050,-2650,1650),(-25,130)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
