"""Create missing named S0 review props only; preserve existing authored props; keep authored director graph intact."""
import unreal as u,time
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve();SRC=ROOT/'ArtSource/SchoolOpening';OUT=ROOT/'Saved/S0Opening'
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=A.get_all_level_actors();stage=next(a for a in actors if a.get_actor_label()=='S0_OpeningStage');girl=next(a for a in actors if a.get_actor_label()=='S0_LittleGirl_Blocking');stage.set_editor_property('girl',girl)
AT=u.AssetToolsHelpers.get_asset_tools();DIR='/Game/SceneDirector/School/S0'
def import_file(name):
 path=SRC/name;target=DIR+'/'+path.stem
 if not u.EditorAssetLibrary.does_asset_exist(target):
  task=u.AssetImportTask();task.set_editor_property('filename',str(path));task.set_editor_property('destination_path',DIR);task.set_editor_property('automated',True);task.set_editor_property('save',True);AT.import_asset_tasks([task])
 return u.load_asset(target)
def mat(name,color=None,texture=None):
 path=DIR+'/'+name
 if u.EditorAssetLibrary.does_asset_exist(path):return u.load_asset(path)
 m=AT.create_asset(name,DIR,u.Material,u.MaterialFactoryNew());m.set_editor_property('two_sided',True)
 if texture:
  expr=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionTextureSample);expr.set_editor_property('texture',texture)
 else:
  expr=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector);expr.set_editor_property('constant',u.LinearColor(*color))
 u.MaterialEditingLibrary.connect_material_property(expr,'RGB' if texture else '',u.MaterialProperty.MP_BASE_COLOR)
 mult=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionMultiply);mult.set_editor_property('const_b',.025 if texture else .05);u.MaterialEditingLibrary.connect_material_expressions(expr,'RGB' if texture else '',mult,'A');u.MaterialEditingLibrary.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m,False);return m
photo=mat('M_MemoryPhoto_Draft',texture=import_file('Photo_Memory_Draft.png'));stars=mat('M_ConstellationCard',texture=import_file('Card_Constellation.png'));note=mat('M_StarNote',texture=import_file('Note_Stars.png'))
cream=mat('M_CharmCream',(.7,.57,.42));pink=mat('M_CharmPink',(.35,.12,.2));gold=mat('M_CharmGold',(.55,.33,.08))
def mesh(label,path,pos,rot,scale,material):
 a=next((a for a in A.get_all_level_actors() if a.get_actor_label()==label),None)
 if a:return a
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),rot);a.set_actor_label(label);a.set_folder_path('S0 Opening/Props')
 a.set_actor_location(u.Vector(*pos),False,True);a.set_actor_rotation(rot,False);a.set_actor_scale3d(u.Vector(*scale));c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(u.load_asset(path));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_material(0,material);return a
plane='/Engine/BasicShapes/Plane';sphere='/Engine/BasicShapes/Sphere';cylinder='/Engine/BasicShapes/Cylinder'
mesh('S0_MemoryPhoto',plane,(3154,-20,168),u.Rotator(roll=90,yaw=-90),(.19,.25,1),photo)
mesh('S0_StarCard',plane,(3154,21,173),u.Rotator(roll=90,yaw=-90),(.16,.22,1),stars)
mesh('S0_Note',plane,(3154,20,149),u.Rotator(roll=90,yaw=-90),(.12,.12,1),note)
mesh('S0_Charm_Body',sphere,(3156,0,137),u.Rotator(),(.07,.07,.095),cream)
mesh('S0_Charm_Head',sphere,(3156,0,145),u.Rotator(),(.09,.085,.08),cream)
for y in [-3,3]:mesh('S0_Charm_Ear_'+str(y),sphere,(3156,y,151),u.Rotator(),(.025,.025,.065),pink)
mesh('S0_Charm_String',cylinder,(3156,0,159),u.Rotator(),(.004,.004,.12),gold)
light=next((a for a in actors if a.get_actor_label()=='S0_InteriorFill'),None)
if not light:light=A.spawn_actor_from_class(u.PointLight,u.Vector(3187,0,211));light.set_actor_label('S0_InteriorFill');light.set_folder_path('S0 Opening/Props')
light.point_light_component.set_mobility(u.ComponentMobility.MOVABLE);light.point_light_component.set_intensity(.2);light.point_light_component.set_attenuation_radius(135);light.point_light_component.set_light_color(u.LinearColor(1,.82,.6))
for prop,file in [('girl_song','Guide_Twinkle_Melody.wav'),('door_sound','Guide_Door_Creak.wav'),('fall_sound','Guide_Fall_Thud.wav')]:stage.set_editor_property(prop,import_file(file))
door=next(a for a in actors if a.get_actor_label()=='S0_LockerDoor')
for a in A.get_all_level_actors():
 if a.get_actor_label() in ['S0_MemoryPhoto','S0_StarCard','S0_Note'] or a.get_actor_label().startswith('S0_Charm_'):
  a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);a.attach_to_actor(door,'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
u.SystemLibrary.quit_editor()
