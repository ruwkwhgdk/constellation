import unreal as u,json
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve(); out=root/'Saved/VFXImplementation';out.mkdir(exist_ok=True)
a=u.EditorAssetLibrary;t=u.AssetToolsHelpers.get_asset_tools();ml=u.MaterialEditingLibrary
base='/Game/Constellation/VFX/Materials';a.make_directory(base)
def expr(m,cls,**kw):
 e=ml.create_material_expression(m,cls)
 for k,v in kw.items():e.set_editor_property(k,v)
 return e
def link(x,xpin,y,ypin):
 assert ml.connect_material_expressions(x,xpin,y,ypin), (x.get_class().get_name(),xpin,y.get_class().get_name(),ypin)
def prop(x,pin,p):ml.connect_material_property(x,pin,p)
def mat(name,kind):
 path=base+'/'+name
 m=u.load_asset(path) if a.does_asset_exist(path) else t.create_asset(name,base,u.Material,u.MaterialFactoryNew())
 ml.delete_all_material_expressions(m)
 m.set_editor_property('two_sided',True)
 m.set_editor_property('used_with_instanced_static_meshes',True)
 m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT if kind not in ['gel'] else u.BlendMode.BLEND_MASKED)
 m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
 tint=expr(m,u.MaterialExpressionVectorParameter,parameter_name='Tint',default_value=u.LinearColor(.55,.85,1,1))
 alpha=expr(m,u.MaterialExpressionPerInstanceCustomData,data_index=0,const_default_value=1.)
 if kind in ['soft','dust','ring']:
  uv=expr(m,u.MaterialExpressionTextureCoordinate)
  custom=expr(m,u.MaterialExpressionCustom,output_type=u.CustomMaterialOutputType.CMOT_FLOAT1)
  inp=u.CustomInput();inp.set_editor_property('input_name','UV');custom.set_editor_property('inputs',[inp]);link(uv,'',custom,'UV')
  code={'soft':'float r=length(UV-0.5)*2; return pow(saturate(1-r),2.5);','ring':'float r=length(UV-0.5)*2; return smoothstep(0.55,0.68,r)*(1-smoothstep(0.73,0.88,r));','dust':'float2 p=UV*6; float n=0.55+0.18*sin(p.x*3.3+sin(p.y*2.1))+0.13*sin(p.y*4.7+p.x); float r=length((UV-0.5)*2); return pow(saturate(1-r),1.7)*saturate(n)*1.2;'}[kind]
  custom.set_editor_property('code',code)
  mul=expr(m,u.MaterialExpressionMultiply);link(custom,'',mul,'A');link(alpha,'',mul,'B')
  op=expr(m,u.MaterialExpressionMultiply);link(mul,'',op,'A');link(tint,'A',op,'B');prop(op,'',u.MaterialProperty.MP_OPACITY)
  gain=expr(m,u.MaterialExpressionScalarParameter,parameter_name='Brightness',default_value=.5 if kind=='dust' else 2.)
  em=expr(m,u.MaterialExpressionMultiply);link(tint,'',em,'A');link(gain,'',em,'B');prop(em,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 elif kind=='gel':
  prop(alpha,'',u.MaterialProperty.MP_OPACITY_MASK)
  fres=expr(m,u.MaterialExpressionFresnel,exponent=2.)
  bias=expr(m,u.MaterialExpressionAdd,const_b=.3);link(fres,'',bias,'A')
  glow=expr(m,u.MaterialExpressionMultiply);link(tint,'',glow,'A');link(bias,'',glow,'B');prop(glow,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 elif kind in ['glass','pane']:
  prop(tint,'',u.MaterialProperty.MP_BASE_COLOR)
  r=expr(m,u.MaterialExpressionConstant,r=.12);prop(r,'',u.MaterialProperty.MP_ROUGHNESS)
  opacity=expr(m,u.MaterialExpressionConstant,r=.18 if kind=='pane' else .8)
  mul=expr(m,u.MaterialExpressionMultiply);link(alpha,'',mul,'A');link(opacity,'',mul,'B');prop(mul,'',u.MaterialProperty.MP_OPACITY)
  fres=expr(m,u.MaterialExpressionFresnel,exponent=3.)
  edge=expr(m,u.MaterialExpressionAdd,const_b=.08 if kind=='pane' else .55);link(fres,'',edge,'A')
  em=expr(m,u.MaterialExpressionMultiply);link(edge,'',em,'A');link(tint,'',em,'B');prop(em,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 else:
  gain=expr(m,u.MaterialExpressionConstant,r=.8 if name=='M_FX_Glass' else 5.);em=expr(m,u.MaterialExpressionMultiply);link(tint,'',em,'A');link(gain,'',em,'B');prop(em,'',u.MaterialProperty.MP_EMISSIVE_COLOR);prop(alpha,'',u.MaterialProperty.MP_OPACITY)
 ml.recompile_material(m);assert a.save_loaded_asset(m), "Cannot save "+path;return path
result={'materials':[mat(n,k) for n,k in [('M_FX_Glow','glow'),('M_FX_Gel','gel'),('M_FX_Glass','glow'),('M_GlassPane','pane'),('M_FX_Soft','soft'),('M_FX_Dust','dust'),('M_FX_Ring','ring')]]}
trail=u.load_asset('/Game/Constellation/VFX/NS_SwordTrail');result['trail_class']=trail.get_class().get_name() if trail else None
result['trail_methods']=[x for x in dir(trail) if 'param' in x.lower() or 'expos' in x.lower()] if trail else []
# Inspect populated source BP components via a temporary editor actor, never save its world.
reg=u.AssetRegistryHelpers.get_asset_registry(); rows=reg.get_assets_by_path('/Game/Constellation/Characters/Heroine',True)
result['blueprints']=[r.package_name for r in rows if 'BP_Player' in str(r.asset_name)]
actorSub=u.get_editor_subsystem(u.EditorActorSubsystem)
for r in rows:
 if str(r.asset_name)=='BP_Player_Heroine':
  bp=u.load_asset(str(r.object_path)) if hasattr(r,'object_path') else a.load_asset(str(r.package_name))
  c=a.load_blueprint_class(str(r.package_name));actor=actorSub.spawn_actor_from_class(c,u.Vector(0,0,-10000))
  result['sword_components']=[]
  for comp in actor.get_components_by_class(u.SceneComponent):
   if 'sword' in comp.get_name().lower():
    d={'name':comp.get_name(),'relative_location':str(comp.relative_location),'relative_rotation':str(comp.relative_rotation),'relative_scale':str(comp.relative_scale3d),'socket':str(comp.get_attach_socket_name())}
    if isinstance(comp,u.StaticMeshComponent):d['mesh']=comp.static_mesh.get_path_name() if comp.static_mesh else None
    result['sword_components'].append(d)
  actorSub.destroy_actor(actor)
result['maps']=[str(r.package_name) for r in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/Engine','World'),True) if str(r.package_name).startswith('/Game/') and any(s in str(r.package_name).lower() for s in ['school','cave','preview'])]
(out/'asset-inspection.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf8')
u.log('VFX_MATERIALS_AND_INSPECTION_COMPLETE')
