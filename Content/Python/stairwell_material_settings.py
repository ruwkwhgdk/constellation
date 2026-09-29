"""Non-destructive scene material revision, world-space dirt and aggregate."""
import unreal as u, json
from pathlib import Path
def apply_materials():
    E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary; AT=u.AssetToolsHelpers.get_asset_tools()
    dest='/Game/Environment/StairwellModular/Scene/Materials/Weathered'
    # Linear albedo, roughness, metal, fine variation, broad variation.
    specs={
        'M_Kit_Concrete':([.24,.28,.29],.9,0,.35,.24),
        'M_Kit_Grout':([.065,.078,.077],.96,0,.16,.18),
        'M_Kit_FloorTile':([.28,.34,.35],.64,0,.14,.2),
        'M_Kit_WallTile':([.53,.57,.54],.48,0,.07,.16),
        'M_Kit_Tactile':([.47,.39,.045],.73,0,.13,.25),
        'M_Kit_RailSteel':([.32,.38,.4],.43,.88,.08,.12),
        'M_Kit_DarkTrim':([.028,.038,.04],.8,.2,.12,.2),
        'M_Kit_MetalPaint':([.2,.24,.25],.78,.05,.14,.23),
        'M_CeilingAggregate':([.64,.67,.65],.94,0,.68,.28)}
    materials={}
    for name,(color,rough,metal,fine,broad) in specs.items():
        asset_name=name+'_Weathered'; path=dest+'/'+asset_name
        mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(asset_name,dest,u.Material,u.MaterialFactoryNew())
        M.delete_all_material_expressions(mat)
        def node(cls): return M.create_material_expression(mat,cls)
        def scalar(v):
            n=node(u.MaterialExpressionConstant); n.r=v; return n
        def connect(a,b,p): assert M.connect_material_expressions(a,'',b,p)
        def binary(cls,a,b):
            n=node(cls); connect(a,n,'A'); connect(b,n,'B'); return n
        def noise(scale):
            n=node(u.MaterialExpressionNoise); n.set_editor_property('scale',scale); n.set_editor_property('levels',2)
            n.set_editor_property('output_min',0); n.set_editor_property('output_max',1); return n
        fine_noise=noise(1.8 if name=='M_CeilingAggregate' else .85)
        broad_noise=noise(.025)
        variation=binary(u.MaterialExpressionAdd,scalar(1-fine-broad),binary(u.MaterialExpressionAdd,binary(u.MaterialExpressionMultiply,fine_noise,scalar(fine)),binary(u.MaterialExpressionMultiply,broad_noise,scalar(broad))))
        base=node(u.MaterialExpressionConstant3Vector); base.constant=u.LinearColor(*color,1)
        tinted=binary(u.MaterialExpressionMultiply,base,variation)
        if name in ['M_Kit_WallTile','M_Kit_FloorTile','M_Kit_Tactile']:
            pitch=10 if name=='M_Kit_WallTile' else 30
            grid=node(u.MaterialExpressionCustom)
            grid.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1)
            inputs=[]
            for input_name in ['P','N']:
                inp=u.CustomInput(); inp.set_editor_property('input_name',input_name); inputs.append(inp)
            grid.set_editor_property('inputs',inputs)
            grid.set_editor_property('code',f'float2 q = abs(N.z)>0.7 ? P.xy : (abs(N.x)>abs(N.y) ? P.yz : P.xz); float2 d=abs(frac(q/{pitch}.0+0.5)-0.5)*{pitch}.0; float2 aa=max(fwidth(q)*0.5,0.025); float2 v=smoothstep(0.18-aa,0.18+aa,d); return min(v.x,v.y);')
            connect(node(u.MaterialExpressionWorldPosition),grid,'P')
            connect(node(u.MaterialExpressionVertexNormalWS),grid,'N')
            grout=node(u.MaterialExpressionConstant3Vector); grout.constant=u.LinearColor(.05,.065,.063,1)
            lerp=node(u.MaterialExpressionLinearInterpolate); connect(grout,lerp,'A'); connect(tinted,lerp,'B'); connect(grid,lerp,'Alpha'); tinted=lerp
        M.connect_material_property(tinted,'',u.MaterialProperty.MP_BASE_COLOR)
        rough_node=binary(u.MaterialExpressionAdd,scalar(rough-.08),binary(u.MaterialExpressionMultiply,broad_noise,scalar(.12)))
        M.connect_material_property(rough_node,'',u.MaterialProperty.MP_ROUGHNESS)
        M.connect_material_property(scalar(metal),'',u.MaterialProperty.MP_METALLIC)
        M.recompile_material(mat); assert E.save_loaded_asset(mat); materials[name]=mat
    assignments=[]
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(a,u.StaticMeshActor) or not a.get_actor_label().startswith('SWScene_'): continue
        component=a.static_mesh_component
        for i in range(component.get_num_materials()):
            old=component.get_material(i)
            if not old: continue
            key=old.get_name().removesuffix('_Weathered')
            if a.get_actor_label().startswith('SWScene_Ceiling_'): key='M_CeilingAggregate'
            if key in materials:
                component.set_material(i,materials[key]); assignments.append([a.get_actor_label(),i,materials[key].get_path_name()])
    return dict(materials={k:v.get_path_name() for k,v in materials.items()},assignments=assignments,specs=specs)
