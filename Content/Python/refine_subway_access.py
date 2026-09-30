"""User-requested rail reuse, readable approach lighting, and rear enclosure. No PIE."""
import unreal as u, json, datetime, shutil, runpy
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve(); O=R/'ArtSource/SubwayEntrance/Connection/v003'; O.mkdir(parents=True,exist_ok=True)
E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary; AT=u.AssetToolsHelpers.get_asset_tools()
A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
EXT='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland'; INT='/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2'
BACK=R/'Saved/SubwayEntranceRecovery'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_access'); BACK.mkdir(parents=True)
for p in [EXT,INT]: shutil.copy2(R/'Content'/(p.removeprefix('/Game/')+'.umap'),BACK/(p.rsplit('/',1)[-1]+'.umap'))
assert L.load_level(INT)
source=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='SWScale2_MainRail_-232_0')
rail_material=source.static_mesh_component.get_material(0)
report={'play_tested':False,'backup':str(BACK),'rail_material':rail_material.get_path_name(),'maps':[]}

def mat(name,color,unlit=False):
 path='/Game/Constellation/Environments/SubwayEntrance/Materials/'+name
 m=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,path.rsplit('/',1)[0],u.Material,u.MaterialFactoryNew())
 M.delete_all_material_expressions(m);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT if unlit else u.MaterialShadingModel.MSM_DEFAULT_LIT)
 c=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(*color,1)
 M.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR if unlit else u.MaterialProperty.MP_BASE_COLOR)
 if not unlit:
  for prop,v in [(u.MaterialProperty.MP_ROUGHNESS,.95),(u.MaterialProperty.MP_SPECULAR,0)]:
   n=M.create_material_expression(m,u.MaterialExpressionConstant);n.r=v;M.connect_material_property(n,'',prop)
 M.recompile_material(m);E.save_loaded_asset(m);return m

surface=mat('M_SE_TunnelApproach',(.055,.065,.06))
for region in ['Exterior','Interior']:
 mesh=E.load_asset('/Game/Constellation/Environments/SubwayEntrance/Meshes/SM_SE_'+region+'DarkTunnel')
 for i,s in enumerate(mesh.get_editor_property('static_materials')):
  if str(s.material_slot_name)=='TunnelDark':mesh.set_material(i,surface)
 E.save_loaded_asset(mesh)
guides={EXT:mat('M_SE_TunnelGuide_Exterior',(12000,9900,6000),True),INT:mat('M_SE_TunnelGuide',(200,165,100),True)}

def spawn(cls,name,pos,rot=None):
 a=next((v for v in A.get_all_level_actors() if v.get_actor_label()==name),None)
 if not a:a=A.spawn_actor_from_class(cls,u.Vector(*pos),rot or u.Rotator());a.set_actor_label(name)
 a.set_actor_location(u.Vector(*pos),False,False)
 if rot:a.set_actor_rotation(rot,False)
 a.set_folder_path('SubwayEntrance/AccessRefinement');return a

def mesh_actor(name,mesh,pos,scale,material,rot=None):
 a=spawn(u.StaticMeshActor,name,pos,rot);a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(u.Vector(*scale))
 for i in range(a.static_mesh_component.get_num_materials()):a.static_mesh_component.set_material(i,material)
 a.static_mesh_component.set_collision_profile_name('BlockAll');return a

for path in [EXT,INT]:
 assert L.load_level(path)
 d={a.get_actor_label():a for a in A.get_all_level_actors()}
 if path==EXT:
  if 'SE_E10' in d:A.destroy_actor(d['SE_E10'])
  kit='/Game/Constellation/Environments/Stairwell/ReviewKit/Meshes/SM_SW_'
  for side in [-1,1]:
   x=3900+side*202;offset=0
   for i,length in enumerate([120,120,120,120,60]):
    mesh=E.load_asset(kit+('10_RailSlope60' if length==60 else '10_RailSlope'));assert mesh
    mesh_actor('SE_KitRail_%s_%d'%(side,i),mesh,(x,-19690+offset,9825+offset*16/30),(1,side,16/15),rail_material,u.Rotator(yaw=90))
    offset+=length
   # Same kit wall-return pair, reversed at bottom; dual rails swap vertically.
   for label,pos,yaw,zscale,mirror in [('Top',(x,-19150,10113),90,16/15,side),('Bottom',(x,-19690,9825+25*16/15),270,-16/15,-side)]:
    mesh=E.load_asset(kit+'19_RailReturnSlopeRight');assert mesh
    mesh_actor('SE_KitRail_%s_%s'%(side,label),mesh,pos,(1,mirror,zscale),rail_material,u.Rotator(yaw=yaw))
  wallmat=E.load_asset('/Game/Constellation/Environments/SubwayEntrance/Materials/M_SE_WarmTile')
  mesh_actor('SE_RearClosure',E.load_asset('/Engine/BasicShapes/Cube'),(3900,-19920,10185),(4.6,.2,3.9),wallmat)
  ppactor=d['SE_DarkExposure'];ppactor.set_actor_location(u.Vector(4820,-20500,9780),False,False)
  ppactor.get_component_by_class(u.BoxComponent).set_box_extent(u.Vector(220,210,145))
  lights=[((3900,-20410,9760),2200),((4220,-20500,9760),1500)]
 else:
  ppactor=d['SE_DarkExposure'];ppactor.set_actor_location(u.Vector(-1500,-950,500),False,False)
  ppactor.get_component_by_class(u.BoxComponent).set_box_extent(u.Vector(210,240,145))
  lights=[((-1200,0,470),2200),((-1500,-260,470),1500)]
 ppactor.get_editor_property('post_process').set_editor_property('blend_radius',150)
 for i,(pos,intensity) in enumerate(lights):
  a=spawn(u.PointLight,'SE_ApproachLight_%02d'%i,pos);c=a.point_light_component
  c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.CANDELAS);c.set_intensity(intensity)
  c.set_light_color(u.LinearColor(1,.82,.57));c.set_editor_property('attenuation_radius',440);c.set_cast_shadows(True)
  c.set_editor_property('source_radius',20)
 for i in range(2):d['SE_TunnelGuide_%02d'%i].static_mesh_component.set_material(0,guides[path])
 assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),path)
 report['maps'].append({'map':path,'saved':True,'approach_lights':2})
(O/'applied.json').write_text(json.dumps(report,indent=2))
u.log('SUBWAY_ACCESS_APPLIED')
runpy.run_path(str(R/'Content/Python/capture_subway_access.py'))
