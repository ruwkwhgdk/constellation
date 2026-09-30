import unreal as u,runpy
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve()
runpy.run_path(str(R/'Content/Python/polish_subway_tunnel_shading.py'))
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
guide_path='/Game/Constellation/Environments/SubwayEntrance/Materials/M_SE_TunnelGuide'
guide=E.load_asset(guide_path) if E.does_asset_exist(guide_path) else AT.create_asset('M_SE_TunnelGuide','/Game/Constellation/Environments/SubwayEntrance/Materials',u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(guide);guide.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
color=M.create_material_expression(guide,u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(200,165,100,1);M.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(guide);E.save_loaded_asset(guide)
ext_path='/Game/Constellation/Environments/SubwayEntrance/Materials/M_SE_TunnelGuide_Exterior'
exguide=E.load_asset(ext_path) if E.does_asset_exist(ext_path) else AT.create_asset('M_SE_TunnelGuide_Exterior','/Game/Constellation/Environments/SubwayEntrance/Materials',u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(exguide);exguide.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
color=M.create_material_expression(exguide,u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(12000,9900,6000,1);M.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR);M.recompile_material(exguide);E.save_loaded_asset(exguide)
for path in ['/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland','/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2']:
 assert L.load_level(path)
 d={a.get_actor_label():a for a in A.get_all_level_actors()};pp=d['SE_DarkExposure'].get_editor_property('post_process');s=pp.get_editor_property('settings')
 for key,value in [('override_auto_exposure_method',False),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',-16.0),('override_auto_exposure_apply_physical_camera_exposure',False),('auto_exposure_apply_physical_camera_exposure',False),('override_auto_exposure_min_brightness',False),('override_auto_exposure_max_brightness',False)]:s.set_editor_property(key,value)
 pp.set_editor_property('settings',s)
 # Bidirectional floor cues show the bend before the fully dark handoff section.
 cues=[((3910,-20410,9641),(4,240,1)),((4060,-20530,9641),(300,4,1))] if path.endswith('L_StartIsland') else [((-1250,50,361),(500,4,1)),((-1500,-160,361),(4,420,1))]
 for i,(pos,size) in enumerate(cues):
  label='SE_TunnelGuide_%02d'%i;a=d.get(label)
  if not a:a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos));a.set_actor_label(label);a.set_folder_path('SubwayEntrance/DarkConnection')
  a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cube'));a.set_actor_scale3d(u.Vector(*[v/100 for v in size]));a.static_mesh_component.set_material(0,exguide if path.endswith('L_StartIsland') else guide)
  a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.static_mesh_component.set_cast_shadow(False)
 assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),path)
runpy.run_path(str(R/'Content/Python/capture_subway_dark_connection.py'))

