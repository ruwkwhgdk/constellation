"""Match the packed ORM sample to its Masks texture compression setting."""
import unreal as u
P='/Game/Constellation/Environments/Stairwell/ReviewKit'
E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary
mat=E.load_asset(P+'/Materials/M_Kit_TripoLight'); assert mat
M.delete_all_material_expressions(mat)
suffix='4aa20774-e697-4117-a168-527ce0f5a17f'
for prefix,sampler,prop,pin in [('Color_',u.MaterialSamplerType.SAMPLERTYPE_COLOR,u.MaterialProperty.MP_BASE_COLOR,'RGB'),('ORM_',u.MaterialSamplerType.SAMPLERTYPE_MASKS,u.MaterialProperty.MP_ROUGHNESS,'G'),('NormalGL_',u.MaterialSamplerType.SAMPLERTYPE_NORMAL,u.MaterialProperty.MP_NORMAL,'RGB')]:
    tex=E.load_asset(P+'/Textures/'+prefix+suffix); assert tex
    n=M.create_material_expression(mat,u.MaterialExpressionTextureSample); n.texture=tex; n.sampler_type=sampler
    assert M.connect_material_property(n,pin,prop)
    if prefix=='ORM_':
        assert M.connect_material_property(n,'R',u.MaterialProperty.MP_AMBIENT_OCCLUSION)
        assert M.connect_material_property(n,'B',u.MaterialProperty.MP_METALLIC)
M.recompile_material(mat); assert E.save_loaded_asset(mat)
u.log('LIGHT_ORM_SAMPLER_FIXED_MASKS')
