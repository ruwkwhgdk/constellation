"""Clone maintained shallow water; grade roughness at its existing masked shoreline."""
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
source=u.load_asset(D+'/M_S0_ShallowWater_V7');assert source
assert not E.does_asset_exist(D+'/M_S0_ShallowWater_Edge_V32')
material=E.duplicate_asset(source.get_path_name(),D+'/M_S0_ShallowWater_Edge_V32');assert material
customs=[n for n in M.get_material_expressions(material) if isinstance(n,u.MaterialExpressionCustom)]
wet=next(n for n in customs if 'return smoothstep(.30,.45,f)*smoothstep(0,45,e);' in n.get_editor_property('code'))
rough=next(n for n in customs if 'return lerp(.045,.105,n.fbm(P.xy/65));' in n.get_editor_property('code'))
old=rough.get_editor_property('code')
code=wet.get_editor_property('code').replace('return smoothstep(.30,.45,f)*smoothstep(0,45,e);','float wet=smoothstep(.30,.45,f)*smoothstep(0,45,e);\nreturn lerp(.37,lerp(.045,.105,n.fbm(P.xy/65)),smoothstep(.333,.82,wet));')
rough.set_editor_property('code',code)
M.recompile_material(material);assert E.save_loaded_asset(material,False)
(O/'material-audit.json').write_text(json.dumps({'source':source.get_path_name(),'candidate':material.get_path_name(),'old_roughness_code':old,'new_roughness_code':code,'scope':'Only one Custom expression code: roughness. Existing mask/color/normals/coverage preserved.'},indent=2))
