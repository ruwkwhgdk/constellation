"""Depth-dependent tunnel surface shading; no camera fade or global material changes."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SubwayEntrance/Connection/v002';D='/Game/Constellation/Environments/SubwayEntrance';E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
def asset(name):
 p=D+'/Materials/'+name;return E.load_asset(p) if E.does_asset_exist(p) else AT.create_asset(name,D+'/Materials',u.Material,u.MaterialFactoryNew())
def constant(m,v):
 n=M.create_material_expression(m,u.MaterialExpressionConstant);n.r=v;return n
def link(a,ap,b,bp):assert M.connect_material_expressions(a,ap,b,'' if bp=='Input' else bp),(str(b.get_class()),bp,list(M.get_material_expression_input_names(b)))
# A lightless deep surface remains dark even with daylight sky capture leakage.
m=asset('M_SE_TunnelDark');M.delete_all_material_expressions(m);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);M.connect_material_property(constant(m,0),'',u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(m);E.save_loaded_asset(m)
spec=load_current_json((R/'ArtSource/SubwayEntrance/Production/v001/materials.json').read_text())
for region,axis,start,length in [('Exterior','g',19865,405),('Interior','r',720,750)]:
 mesh=E.load_asset(D+'/Meshes/SM_SE_'+region+'DarkTunnel')
 for slot_id,slot in enumerate(mesh.get_editor_property('static_materials')):
  key=str(slot.material_slot_name)
  if key=='TunnelDark':continue
  m=asset('M_SE_Tunnel_'+region+'_'+key);M.delete_all_material_expressions(m)
  world=M.create_material_expression(m,u.MaterialExpressionWorldPosition);mask=M.create_material_expression(m,u.MaterialExpressionComponentMask);mask.set_editor_property('r',axis=='r');mask.set_editor_property('g',axis=='g');mask.set_editor_property('b',False);mask.set_editor_property('a',False);link(world,'',mask,'Input')
  neg=M.create_material_expression(m,u.MaterialExpressionMultiply);link(mask,'',neg,'A');link(constant(m,-1),'',neg,'B')
  sub=M.create_material_expression(m,u.MaterialExpressionSubtract);link(neg,'',sub,'A');link(constant(m,start),'',sub,'B')
  div=M.create_material_expression(m,u.MaterialExpressionDivide);link(sub,'',div,'A');link(constant(m,length),'',div,'B')
  clamp=M.create_material_expression(m,u.MaterialExpressionClamp);link(div,'',clamp,'Input')
  inverse=M.create_material_expression(m,u.MaterialExpressionOneMinus);link(clamp,'',inverse,'Input')
  power=M.create_material_expression(m,u.MaterialExpressionPower);link(inverse,'',power,'Base')
  color=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(*spec[key]['color'],1)
  shade=M.create_material_expression(m,u.MaterialExpressionMultiply);link(power,'',shade,'A');link(color,'',shade,'B');M.connect_material_property(shade,'',u.MaterialProperty.MP_BASE_COLOR)
  M.connect_material_property(constant(m,.95),'',u.MaterialProperty.MP_ROUGHNESS);M.connect_material_property(constant(m,0),'',u.MaterialProperty.MP_SPECULAR)
  M.recompile_material(m);E.save_loaded_asset(m);mesh.set_material(slot_id,m)
 E.save_loaded_asset(mesh)
print('SUBWAY_TUNNEL_SHADING_OK')



