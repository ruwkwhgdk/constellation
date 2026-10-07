import unreal as u
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Review/VFX/L_VFXGallery')
a=u.EditorAssetLibrary;t=u.AssetToolsHelpers.get_asset_tools();ml=u.MaterialEditingLibrary
path='/Game/Constellation/VFX/Materials/M_ReviewBackdrop';m=u.load_asset(path) if a.does_asset_exist(path) else t.create_asset('M_ReviewBackdrop','/Game/Constellation/VFX/Materials',u.Material,u.MaterialFactoryNew())
ml.delete_all_material_expressions(m)
c=ml.create_material_expression(m,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(.035,.045,.055,1);ml.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
r=ml.create_material_expression(m,u.MaterialExpressionConstant);r.r=.85;ml.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS);ml.recompile_material(m);a.save_loaded_asset(m)
for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 if actor.get_actor_label() in ['Review_Ground','Review_Backdrop']:actor.static_mesh_component.set_material(0,m)
 if isinstance(actor,u.PostProcessVolume):
  s=actor.settings;s.override_auto_exposure_method=True;s.auto_exposure_method=u.AutoExposureMethod.AEM_BASIC;s.override_auto_exposure_min_brightness=True;s.auto_exposure_min_brightness=1.;s.override_auto_exposure_max_brightness=True;s.auto_exposure_max_brightness=1.;s.override_auto_exposure_bias=True;s.auto_exposure_bias=-2.;actor.settings=s
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
u.log('VFX_GALLERY_LIGHTING_FIXED')
