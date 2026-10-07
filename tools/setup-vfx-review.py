"""Rebuild only the disposable, consolidated VFX gallery. Back up maps before invoking."""
import unreal as u,json
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/VFXImplementation'
a=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
base='/Game/Constellation/Review/VFX';path=base+'/L_VFXGallery'
assert levels.load_level(path)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name().split('.')[0]==path
for x in actors.get_all_level_actors():
 if not isinstance(x,(u.WorldSettings,u.LevelScriptActor)): actors.destroy_actor(x)
neutral=u.load_asset('/Game/Constellation/VFX/Materials/M_ReviewBackdrop');cube=u.load_asset('/Engine/BasicShapes/Cube')
def box(name,p,s):
 x=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*p));x.set_actor_label(name);x.static_mesh_component.set_static_mesh(cube);x.static_mesh_component.set_material(0,neutral);x.set_actor_scale3d(u.Vector(*s));return x
a.make_directory(base)
box('Gallery_Floor',(1300,500,-20),(40,27,.4))
names=['1 Sword swing','2 Sword impact','3 Sword block','4 Sword parry','5 Slime attack','6 Slime hit','7 Player hit','8 Glass break','9 Running dust','0 Cave ambience']
hero=u.load_asset('/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview');slime=u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Normal/SKM_Slime_Normal')
for i,name in enumerate(names):
 x=(i%5)*650;y=(i//5)*1000
 box('Backdrop_'+str(i),(x,y+180,155),(5,.15,3.5))
 box('Pad_'+str(i),(x,y,-2),(4.5,4,.08))
 fill=actors.spawn_actor_from_class(u.PointLight,u.Vector(x,y-240,240));fill.point_light_component.set_mobility(u.ComponentMobility.MOVABLE);fill.point_light_component.set_editor_property('intensity',300.);fill.point_light_component.set_editor_property('attenuation_radius',650.);fill.point_light_component.set_editor_property('cast_shadows',False)
 text=actors.spawn_actor_from_class(u.TextRenderActor,u.Vector(x-190,y+163,260),u.Rotator(pitch=0,yaw=-90,roll=0));c=text.text_render;c.set_text(name);c.set_world_size(23)
 if i in (1,4,5,6):
  target=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(x,y,0),u.Rotator(pitch=0,yaw=-90,roll=0));target.set_actor_label('Target_'+name);target.set_editor_property('tags',[u.Name('VFXTarget'+str(i))]);c=target.skeletal_mesh_component;c.set_skeletal_mesh_asset(hero if i==6 else slime);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
  # Normalize the display targets to a readable human/slime scale without changing source assets.
  bounds=target.get_actor_bounds(False);height=bounds[1].z*2
  scale=(175 if i==6 else 130)/max(height,1)
  target.set_actor_scale3d(u.Vector(scale,scale,scale));target.set_actor_location(u.Vector(x,y,-(bounds[0].z-bounds[1].z)*scale),False,False)
  if i==6:
   target.set_actor_scale3d(u.Vector(1,1,1));target.set_actor_location(u.Vector(x,y,0),False,False)
   c.override_animation_data(u.load_asset('/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_PreviewRelaxed'),False,False,0.2,1.0)
light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,600),u.Rotator(pitch=-40,yaw=-35,roll=0));light.light_component.set_editor_property('intensity',3.)
sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,400));sky.light_component.set_editor_property('intensity',.7)
light.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector());post.set_editor_property('unbound',True);s=post.get_editor_property('settings');s.override_auto_exposure_method=True;s.auto_exposure_method=u.AutoExposureMethod.AEM_BASIC;s.override_auto_exposure_min_brightness=True;s.auto_exposure_min_brightness=1.;s.override_auto_exposure_max_brightness=True;s.auto_exposure_max_brightness=1.;s.override_auto_exposure_bias=True;s.auto_exposure_bias=-2.;s.override_motion_blur_amount=True;s.motion_blur_amount=0.;post.set_editor_property('settings',s)
g=actors.spawn_actor_from_class(u.ConstellationGlass,u.Vector(1300,1000,115),u.Rotator(pitch=0,yaw=90,roll=0));g.set_actor_label('Reusable_Glass')
actors.spawn_actor_from_class(u.ConstellationFXGallery,u.Vector()).set_actor_label('Interactive_VFX_Gallery')
# Legacy diagnostics remain opt-in command-line helpers only.
actors.spawn_actor_from_class(u.ConstellationFXReview,u.Vector()).set_actor_label('Explicit_Capture_Only')
actors.spawn_actor_from_class(u.PlayerStart,u.Vector(220,-420,200))
world.get_world_settings().set_editor_property('default_game_mode',u.ConstellationFXGalleryMode.static_class())
assert levels.save_current_level()
# The two superseded review maps are backed up outside Content; never remove production maps.
for name in ['L_VFXCombat','L_VFXCave']:
 old=base+'/'+name
 if a.does_asset_exist(old):
  refs=[str(x) for x in a.find_package_referencers_for_asset(old,False) if str(x)!=old]
  assert not refs, str((old,refs))
  assert (out/'GalleryRevisionBefore'/(name+'.umap')).exists()
  assert a.delete_asset(old)
(out/'gallery-setup.json').write_text(json.dumps({'map':path,'stations':names,'free_flight':True,'removed':['L_VFXCombat','L_VFXCave']},indent=2),encoding='utf8')
u.log('VFX_GALLERY_SETUP_COMPLETE')
