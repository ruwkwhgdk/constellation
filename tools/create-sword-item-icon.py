"""Render the actual equipment mesh for the existing item UI, without model edits."""
import unreal as u,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/SwordAcquisition/ItemIcon';O.mkdir(parents=True,exist_ok=True)
u.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
mesh=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector());mesh.static_mesh_component.set_static_mesh(u.load_asset('/Game/Constellation/Characters/Shared/Equipment/SM_Weapon_Sword'))
mesh.static_mesh_component.set_editor_property('disallow_nanite',True)
mat=u.load_asset('/Game/Constellation/UI/ItemAcquisition/M_SwordIcon')
if not mat:
 mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_SwordIcon','/Game/Constellation/UI/ItemAcquisition',u.Material,u.MaterialFactoryNew())
 mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
 texture=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionTextureSample,-200,0);texture.set_editor_property('texture',u.load_asset('/Game/Constellation/Characters/Shared/Equipment/T_Weapon_Sword'))
 u.MaterialEditingLibrary.connect_material_property(texture,'RGB',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat,False)
mesh.static_mesh_component.set_material(0,mat)
center,extent=mesh.get_actor_bounds(False)
light=A.spawn_actor_from_class(u.DirectionalLight,center+u.Vector(200,-300,300));light.set_actor_rotation(u.Rotator(pitch=-35,yaw=35),False);light.light_component.set_intensity(6)
fill=A.spawn_actor_from_class(u.DirectionalLight,center+u.Vector(-200,0,100));fill.set_actor_rotation(u.Rotator(pitch=-20,yaw=140),False);fill.light_component.set_intensity(2)
capture=A.spawn_actor_from_class(u.SceneCapture2D,center+u.Vector(200,-600,40));capture.set_actor_rotation(u.MathLibrary.find_look_at_rotation(capture.get_actor_location(),center),False)
c=capture.get_component_by_class(u.SceneCaptureComponent2D);rt=u.RenderingLibrary.create_render_target2d(world,512,512,u.TextureRenderTargetFormat.RTF_RGBA8)
c.set_editor_property('texture_target',rt);c.set_editor_property('projection_type',u.CameraProjectionMode.ORTHOGRAPHIC);c.set_editor_property('ortho_width',max(extent.x,extent.y,extent.z)*2.45)
c.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);c.set_editor_property('primitive_render_mode',u.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST);c.show_only_actor_components(mesh)
c.set_editor_property('capture_every_frame',True)
start=time.monotonic();u.EditorPythonScripting.set_keep_python_script_alive(True)
capture_requested=None
def tick(dt):
 global capture_requested
 if time.monotonic()-start<15:return
 if capture_requested is None:
  c.capture_scene();capture_requested=time.monotonic();return
 if time.monotonic()-capture_requested<2:return
 try:
  u.RenderingLibrary.export_render_target(world,rt,str(O),'SwordIcon.png')
  task=u.AssetImportTask();task.set_editor_property('filename',str(O/'SwordIcon.png'));task.set_editor_property('destination_path','/Game/Constellation/UI/ItemAcquisition');task.set_editor_property('destination_name','T_RustySword');task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',True)
  u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert u.load_asset('/Game/Constellation/UI/ItemAcquisition/T_RustySword')
  (O/'result.txt').write_text('Rendered actual SM_Weapon_Sword and imported T_RustySword')
 except:(O/'error.txt').write_text(traceback.format_exc())
 finally:
  u.unregister_slate_post_tick_callback(handle);c.set_editor_property('capture_every_frame',False);c.set_editor_property('texture_target',None)
  for actor in [capture,mesh,light,fill]:A.destroy_actor(actor)
  if '-SwordReview' in u.SystemLibrary.get_command_line():exec((R/'tools/setup-sword-acquisition.py').read_text(encoding='utf8'),{'__name__':'__main__'})
  else:u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)


