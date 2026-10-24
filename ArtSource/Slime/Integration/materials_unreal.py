import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Enemies/Slime_Liquid'
lib=u.MaterialEditingLibrary;at=u.AssetToolsHelpers.get_asset_tools()
def make(name,kind):
 m=u.load_asset(B+'/Materials/'+name) or at.create_asset(name,B+'/Materials',u.Material,u.MaterialFactoryNew())
 lib.delete_all_material_expressions(m)
 trans=kind!='eye'
 m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT if trans else u.BlendMode.BLEND_OPAQUE)
 if trans:m.set_editor_property('translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
 m.set_editor_property('two_sided',False)
 lib.set_material_usage(m,u.MaterialUsage.MATUSAGE_SKELETAL_MESH)
 def node(cls,**kw):
  n=lib.create_material_expression(m,cls)
  for k,v in kw.items():n.set_editor_property(k,v)
  return n
 def scalar(v):return node(u.MaterialExpressionConstant,r=v)
 def color(v):return node(u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*v,1))
 def custom(code,inputs,vector=False):
  custom_inputs=[]
  for k in inputs:
   entry=u.CustomInput();entry.set_editor_property('input_name',k);custom_inputs.append(entry)
  n=node(u.MaterialExpressionCustom,code=code,output_type=u.CustomMaterialOutputType.CMOT_FLOAT3 if vector else u.CustomMaterialOutputType.CMOT_FLOAT1,inputs=custom_inputs)
  for k,(src,out) in inputs.items():assert lib.connect_material_expressions(src,out,n,k)
  return n
 def output(n,prop):assert lib.connect_material_property(n,'',prop)
 if kind=='eye':
  output(color((.94,.86,.64)),u.MaterialProperty.MP_BASE_COLOR)
  output(color((.5,.43,.28)),u.MaterialProperty.MP_EMISSIVE_COLOR)
  output(scalar(.27),u.MaterialProperty.MP_ROUGHNESS)
 else:
  normal=node(u.MaterialExpressionPixelNormalWS);view=node(u.MaterialExpressionCameraVectorWS)
  inputs={'N':(normal,''),'V':(view,'')}
  light=node(u.MaterialExpressionVectorParameter,parameter_name='GelRimColor',default_value=u.LinearColor(.12,.022,.55,1))
  dark=node(u.MaterialExpressionVectorParameter,parameter_name='GelCoreColor',default_value=u.LinearColor(.024,.002,.075,1))
  inputs.update({'Rim':(light,''),'Core':(dark,'')})
  if kind=='inner':
   c=custom('return Core * 0.48;',inputs,True)
   opacity=custom('float f=saturate(dot(normalize(N),normalize(V))); return 0.88*pow(f,2.6);',inputs)
  else:
   c=custom('float f=pow(saturate(dot(normalize(N),normalize(V))),1.7); return lerp(Rim,Core,f*0.85);',inputs,True)
   if kind=='drop':
    world=node(u.MaterialExpressionWorldPosition)
    local=node(u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    assert lib.connect_material_expressions(world,'',local,'')
    inputs['P']=(local,'')
    opacity=custom('float3 p=(P-float3(-0.045048,-0.1236,-84.327904))/100.0; float body=length(float3(p.x/0.98,p.y/0.80,(p.z-0.12)/1.14)); float crest=length((p-float3(.20,.13,1.48))/float3(.18,.17,.20)); return .82*smoothstep(.025,.055,p.z)*smoothstep(.84,.95,body)*smoothstep(.70,.98,crest);',inputs)
   else:opacity=custom('float f=saturate(dot(normalize(N),normalize(V))); return lerp(.30,.68,pow(f,.8));',inputs)
  output(c,u.MaterialProperty.MP_BASE_COLOR)
  glow=node(u.MaterialExpressionMultiply,const_b=.12);lib.connect_material_expressions(c,'',glow,'A');output(glow,u.MaterialProperty.MP_EMISSIVE_COLOR)
  output(opacity,u.MaterialProperty.MP_OPACITY)
  output(scalar(.14 if kind!='inner' else .4),u.MaterialProperty.MP_ROUGHNESS)
  output(scalar(.08 if kind=='inner' else .65),u.MaterialProperty.MP_SPECULAR)
 lib.layout_material_expressions(m);lib.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m,False)
 return m
mats={k:make(n,k) for k,n in [('body','M_Slime_Gel'),('inner','M_Slime_InnerDensity'),('drop','M_Slime_Droplet'),('eye','M_Slime_Eyes')]}
mesh=u.load_asset(B+'/SKM_Slime_Liquid');slots=list(mesh.get_editor_property('materials'))
assign={}
for s in slots:
 name=str(s.material_slot_name)
 kind='eye' if 'Eye' in name else 'inner' if 'Inner' in name else 'drop' if 'Drop' in name else 'body'
 s.material_interface=mats[kind];assign[name]=mats[kind].get_path_name()
mesh.set_editor_property('materials',slots)
u.EditorAssetLibrary.save_loaded_asset(mesh,False)
sm=u.load_asset(B+'/SM_Slime_Liquid')
for i,s in enumerate(sm.get_editor_property('static_materials')):
 name=str(s.material_slot_name);kind='eye' if 'Eye' in name else 'inner' if 'Inner' in name else 'body'
 sm.set_material(i,mats[kind])
u.EditorAssetLibrary.save_loaded_asset(sm,False)
yellow=u.load_asset(B+'/Materials/MI_Slime_Gel_Yellow') or at.create_asset('MI_Slime_Gel_Yellow',B+'/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
lib.set_material_instance_parent(yellow,mats['body'])
lib.set_material_instance_vector_parameter_value(yellow,'GelRimColor',u.LinearColor(.7,.38,.035,1))
lib.set_material_instance_vector_parameter_value(yellow,'GelCoreColor',u.LinearColor(.11,.042,.001,1))
u.EditorAssetLibrary.save_loaded_asset(yellow,False)
(P/'materials-report.json').write_text(json.dumps(assign,indent=2))
