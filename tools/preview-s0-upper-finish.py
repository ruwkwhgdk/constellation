E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
src=(R/'tools/apply-s0-wet-floor.py').read_text();exec(src[src.index('class G:'):src.index('# World coordinates')])
name='M_S0_UpperWood_V15';assert not E.does_asset_exist(D+'/'+name)
mat=AT.create_asset(name,D,u.Material,u.MaterialFactoryNew());assert mat
mat.set_editor_property('used_with_static_lighting',True)
g=G(mat);p=g.n(u.MaterialExpressionWorldPosition)
uv=g.custom('return P.xy/300.;',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT2)
wood=g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_A',uv)
color=g.custom('return lerp(C,dot(C,float3(.333,.333,.333)).xxx,.30)*float3(.29,.27,.23);',{'C':wood},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.tex('/Game/ModulAbandJPSchool/Textures/T_WoodPlanks2_N',uv,True),u.MaterialProperty.MP_NORMAL)
g.prop(g.c(.56),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.3),u.MaterialProperty.MP_SPECULAR)
M.recompile_material(mat);assert E.save_loaded_asset(mat,False)
bylabel={a.get_actor_label():a for a in A.get_all_level_actors()};changes=[]
for label in ['classroom_start_floor_13','classroom_start_floor_15']:
 a=bylabel[label];c=a.static_mesh_component
 changes.append(dict(name=a.get_name(),label=label,slot=0,old=c.get_material(0).get_path_name(),new=mat.get_path_name()))
 c.set_material(0,mat)
light=bylabel['S0_WetPolish_CoolCeilingBounce'];lc=light.get_component_by_class(u.LightComponent)
assert not lc.cast_shadows
lp=light.get_actor_location();before=dict(position=[lp.x,lp.y,lp.z],intensity=lc.intensity)
light.set_actor_location(u.Vector(1100,-1500,1750),False,True);lc.set_intensity(40)
(O/'changes.json').write_text(json.dumps(changes,indent=2))
(O/'light-change.json').write_text(json.dumps(dict(name=light.get_name(),label=light.get_actor_label(),before=before,after=dict(position=[1100,-1500,1750],intensity=40)),indent=2))
tag='art1';shots=[('concept',(2900,900,700),(-20,-138)),('reverse',(3050,-2650,1650),(-25,130)),('upper-route',(1400,-2300,900),(-10,180))];S.update(i=0,sent=False,t=time.monotonic())
