"""Final reference pass: preserve geometry, soften nosing aliasing and localize dirt."""
import unreal as u
def apply_finish():
    E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary; A=u.get_editor_subsystem(u.EditorActorSubsystem); AT=u.AssetToolsHelpers.get_asset_tools()
    dest='/Game/Environment/StairwellModular/Scene/Materials/Finish'
    def node(mat,cls): return M.create_material_expression(mat,cls)
    def scalar(mat,value):
        n=node(mat,u.MaterialExpressionConstant); n.r=value; return n
    def color(mat,value):
        n=node(mat,u.MaterialExpressionConstant3Vector); n.constant=u.LinearColor(*value,1); return n
    def conn(a,b,p): assert M.connect_material_expressions(a,'',b,p)
    def clone(source,key,mode):
        path=dest+'/'+key
        if E.does_asset_exist(path): return E.load_asset(path)
        assert E.duplicate_asset(source,path); mat=E.load_asset(path)
        base=M.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR)
        output=M.get_material_property_input_node_output_name(mat,u.MaterialProperty.MP_BASE_COLOR)
        if mode=='door':
            lerp=node(mat,u.MaterialExpressionLinearInterpolate); assert M.connect_material_expressions(base,output,lerp,'A'); conn(color(mat,[.52,.55,.53]),lerp,'B'); conn(scalar(mat,.65),lerp,'Alpha'); base=lerp; output=''
        dirt=node(mat,u.MaterialExpressionCustom); inp=u.CustomInput(); inp.set_editor_property('input_name','P'); dirt.set_editor_property('inputs',[inp]); dirt.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
        if mode=='ceiling':
            code='float2 q=P.xy; float a=exp(-dot((q-float2(95,-70))/float2(45,20),(q-float2(95,-70))/float2(45,20))); float b=exp(-dot((q-float2(-30,65))/float2(60,30),(q-float2(-30,65))/float2(60,30))); return 1-(0.4*a+0.28*b)*float3(0.9,0.85,0.8);'
        elif mode=='floor':
            code='float2 q=P.xy; float a=exp(-dot((q-float2(220,-80))/float2(32,22),(q-float2(220,-80))/float2(32,22))); float b=exp(-dot((q-float2(310,90))/float2(40,18),(q-float2(310,90))/float2(40,18))); return 1-(0.28*a+0.22*b)*float3(0.9,0.82,0.68);'
        else:
            code='float q=P.x+P.y*0.63; float a=exp(-pow((q-340)/18,2))*saturate((220-P.z)/160)*saturate((P.z+20)/80); float b=exp(-pow((q-100)/28,2))*saturate((190-P.z)/180); float foot=0.12*exp(-abs(P.z-8)/23); return 1-(0.23*a+0.18*b+foot)*float3(0.85,0.8,0.66);'
        dirt.set_editor_property('code',code); conn(node(mat,u.MaterialExpressionWorldPosition),dirt,'P')
        mul=node(mat,u.MaterialExpressionMultiply); assert M.connect_material_expressions(base,output,mul,'A'); conn(dirt,mul,'B'); M.connect_material_property(mul,'',u.MaterialProperty.MP_BASE_COLOR)
        if mode=='door': M.connect_material_property(scalar(mat,.7),'',u.MaterialProperty.MP_ROUGHNESS)
        M.recompile_material(mat); assert E.save_loaded_asset(mat); return mat
    weather='/Game/Environment/StairwellModular/Scene/Materials/Weathered/'
    replacements={}
    for key,mode in [('M_Kit_WallTile_Weathered','wall'),('M_CeilingAggregate_Weathered','ceiling'),('M_LandingTurn30','floor'),('M_Kit_MetalPaint_Weathered','wall')]:
        replacements[key]=clone(weather+key,key+'_Finish',mode)
    door_mat=clone('/Game/Environment/StairwellModular/Materials/M_Stairwell_DoorPaint','M_DoorReferenceFinish','door')
    path=dest+'/M_NosingStable'
    if E.does_asset_exist(path): nosing=E.load_asset(path)
    else:
        nosing=AT.create_asset('M_NosingStable',dest,u.Material,u.MaterialFactoryNew())
        M.connect_material_property(color(nosing,[.045,.055,.058]),'',u.MaterialProperty.MP_BASE_COLOR)
        M.connect_material_property(scalar(nosing,.58),'',u.MaterialProperty.MP_ROUGHNESS)
        M.connect_material_property(scalar(nosing,.25),'',u.MaterialProperty.MP_METALLIC)
        M.recompile_material(nosing); E.save_loaded_asset(nosing)
    count=0
    for a in A.get_all_level_actors():
        label=a.get_actor_label()
        if not isinstance(a,u.StaticMeshActor) or not label.startswith('SWScene_'): continue
        c=a.static_mesh_component
        for i in range(c.get_num_materials()):
            old=c.get_material(i)
            if not old: continue
            if 'Nosing' in label: c.set_material(i,nosing); count+=1
            elif label=='SWScene_DoorLeaf': c.set_material(i,door_mat); count+=1
            elif old.get_name() in replacements: c.set_material(i,replacements[old.get_name()]); count+=1
    # Local light for the rear passage, separate from foreground stair illumination.
    light=next((a for a in A.get_all_level_actors() if a.get_actor_label()=='SWScene_Finish_RearBounce'),None)
    if not light:
        light=A.spawn_actor_from_class(u.PointLight,u.Vector(445,240,115),u.Rotator()); light.set_actor_label('SWScene_Finish_RearBounce')
    c=light.get_component_by_class(u.PointLightComponent); c.set_mobility(u.ComponentMobility.MOVABLE); c.set_intensity(650); c.set_light_color(u.LinearColor(.65,.82,.9,1)); c.set_editor_property('attenuation_radius',300); c.set_editor_property('source_radius',25)
    return dict(material_slots_updated=count,nosing='uniform rough metal on original groove geometry',door='original texture blended with light grey paint',localized_stains=True,rear_bounce_intensity=650)
