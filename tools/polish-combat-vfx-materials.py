import unreal as u
from pathlib import Path
import json
A=u.EditorAssetLibrary;L=u.MaterialEditingLibrary;T=u.AssetToolsHelpers.get_asset_tools();base='/Game/Constellation/VFX/Materials'
def node(m,c,**kw):
 x=L.create_material_expression(m,c)
 for k,v in kw.items():x.set_editor_property(k,v)
 return x
def link(a,ap,b,bp):assert L.connect_material_expressions(a,ap,b,bp)
def prop(a,ap,p):assert L.connect_material_property(a,ap,p)
def make(name,shape):
 path=base+'/'+name
 m=u.load_asset(path) if A.does_asset_exist(path) else T.create_asset(name,base,u.Material,u.MaterialFactoryNew())
 L.delete_all_material_expressions(m);m.set_editor_property('two_sided',True);m.set_editor_property('used_with_instanced_static_meshes',shape!='ribbon')
 m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT if shape=='gel' else u.MaterialShadingModel.MSM_UNLIT)
 tint=node(m,u.MaterialExpressionVectorParameter,parameter_name='Tint',default_value=u.LinearColor(.8,.88,1,1));alpha=node(m,u.MaterialExpressionVertexColor) if shape=='ribbon' else node(m,u.MaterialExpressionPerInstanceCustomData,data_index=0,const_default_value=1.)
 alpha_output='A' if shape=='ribbon' else ''
 opacity=alpha
 if shape in ('slash','ribbon','cut','star'):
  uv=node(m,u.MaterialExpressionTextureCoordinate)
  code={'ribbon':'float2 p=UV*2-1; float cap=smoothstep(0.0,0.22,UV.x)*smoothstep(0.0,0.12,1-UV.x); return pow(saturate(1-abs(p.y)),2.5)*cap*0.7;', 'slash':'float2 p=UV*2-1; float cap=smoothstep(0.0,0.25,1-abs(p.x)); return pow(saturate(1-abs(p.y)),2.5)*cap*0.7;', 'cut':'float2 p=UV*2-1; float core=exp(-abs(p.y)*15)*pow(saturate(1-abs(p.x)),0.65); float flecks=0.2*exp(-abs(p.y+0.15*sin(p.x*7))*25)*saturate(1-abs(p.x));return saturate(core+flecks);', 'star':'float2 p=UV*2-1;float a=exp(-abs(p.x)*35)*saturate(1-abs(p.y));float b=exp(-abs(p.y)*35)*saturate(1-abs(p.x));float core=exp(-dot(p,p)*100);return saturate(a+b+core);'}[shape]
  mask=node(m,u.MaterialExpressionCustom,output_type=u.CustomMaterialOutputType.CMOT_FLOAT1);inp=u.CustomInput();inp.set_editor_property('input_name','UV');mask.set_editor_property('inputs',[inp]);mask.set_editor_property('code',code);link(uv,'',mask,'UV')
  opacity=node(m,u.MaterialExpressionMultiply);link(alpha,alpha_output,opacity,'A');link(mask,'',opacity,'B')
 fade=node(m,u.MaterialExpressionScalarParameter,parameter_name='EffectOpacity',default_value=1.);faded=node(m,u.MaterialExpressionMultiply);link(opacity,'',faded,'A');link(fade,'',faded,'B');opacity=faded
 op=node(m,u.MaterialExpressionMultiply);link(opacity,'',op,'A');link(tint,'A',op,'B');prop(op,'',u.MaterialProperty.MP_OPACITY)
 if shape=='gel':
  prop(tint,'',u.MaterialProperty.MP_BASE_COLOR)
  rough=node(m,u.MaterialExpressionConstant,r=.18);prop(rough,'',u.MaterialProperty.MP_ROUGHNESS)
  spec=node(m,u.MaterialExpressionConstant,r=.75);prop(spec,'',u.MaterialProperty.MP_SPECULAR)
  mode=getattr(u.TranslucencyLightingMode,'TLM_SURFACE_PER_PIXEL_LIGHTING',None)
  if mode is not None:m.set_editor_property('translucency_lighting_mode',mode)
  gain=.35
 else:gain=0.9 if shape in ('slash','ribbon') else 4.0
 g=node(m,u.MaterialExpressionConstant,r=gain);em=node(m,u.MaterialExpressionMultiply);link(tint,'',em,'A');link(g,'',em,'B');prop(em,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 L.recompile_material(m);assert A.save_loaded_asset(m),path
 return path
names=[('M_FX_Slash','slash'),('M_FX_Impact','impact'),('M_FX_Cut','cut'),('M_FX_ImpactStar','star'),('M_FX_GelImpact','gel'),('M_FX_SwordRibbon','ribbon')]
if '-OnlySwordRibbon' in u.SystemLibrary.get_command_line():names=[('M_FX_SwordRibbon','ribbon')]
paths=[make(n,s) for n,s in names]
root=Path(u.Paths.project_dir()).resolve();(root/'Saved/VFXImplementation/combat-polish-materials.json').write_text(json.dumps(paths,indent=2))
u.log('COMBAT_POLISH_MATERIALS_READY')
