M=u.MaterialEditingLibrary
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
mat=u.EditorAssetLibrary.load_asset(D+'/M_S0_ShallowRock_V18') or u.EditorAssetLibrary.duplicate_asset(D+'/M_S0_Rock_V9',D+'/M_S0_ShallowRock_V18')
assert mat
normal=next(n for n in M.get_material_expressions(mat) if isinstance(n,u.MaterialExpressionCustom) and 'return normalize(float3(A.z' in str(n.get_editor_property('code')))
nodes=list(M.get_material_expressions(mat))
vn=next((n for n in nodes if isinstance(n,u.MaterialExpressionVertexNormalWS)),None)
assert vn
blend=next((n for n in nodes if isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('desc')=='S0_ShallowRock_GeometryNormalBlend'),None)
if blend is None:blend=M.create_material_expression(mat,u.MaterialExpressionCustom)
blend.set_editor_property('desc','S0_ShallowRock_GeometryNormalBlend')
blend.set_editor_property('code','return normalize(lerp(V,N,0.4));');blend.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
inputs=[]
for name in ['V','N']:
 i=u.CustomInput();i.set_editor_property('input_name',name);inputs.append(i)
blend.set_editor_property('inputs',inputs)
assert M.connect_material_expressions(vn,'',blend,'V')
assert M.connect_material_expressions(normal,'',blend,'N')
assert M.connect_material_property(blend,'',u.MaterialProperty.MP_NORMAL)
M.recompile_material(mat);assert u.EditorAssetLibrary.save_loaded_asset(mat,False)
for a in A.get_all_level_actors():
 if a.get_name() in ['StaticMeshActor_831','StaticMeshActor_833']:a.static_mesh_component.set_material(0,mat)
(O/'normal-preview.json').write_text(json.dumps(dict(material=mat.get_path_name(),geometry_weight=.6,texture_weight=.4,source_material_unchanged=True),indent=2))
tag='art3';S.update(i=0,sent=False,t=time.monotonic())

