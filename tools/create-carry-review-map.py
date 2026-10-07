"""Create the isolated functional review map, leaving maintained environment maps alone."""
import json
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve(); out=root/'Saved/CarryReview'
assert (out/'assets.json').exists(),'Finish carry asset setup first'
tools=u.AssetToolsHelpers.get_asset_tools(); lib=u.EditorAssetLibrary
folder='/Game/Constellation/Review/Carry'; path=folder+'/Maps/L_Carry_Review'
hero=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
pc=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController')
gm=u.load_asset(folder+'/BP_CarryReviewGameMode')
if not gm:
    factory=u.BlueprintFactory(); factory.set_editor_property('parent_class',u.GameModeBase)
    gm=tools.create_asset('BP_CarryReviewGameMode',folder,u.Blueprint,factory)
u.BlueprintEditorLibrary.compile_blueprint(gm)
cdo=u.get_default_object(gm.generated_class()); cdo.set_editor_property('default_pawn_class',hero.generated_class())
cdo.set_editor_property('player_controller_class',pc.generated_class())
cdo.set_editor_property('hud_class',u.load_asset('/Game/Constellation/UI/Blueprints/BP_HUD').generated_class())
assert lib.save_loaded_asset(gm,False)
world=u.EditorLoadingAndSavingUtils.new_blank_map(False)
world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class())
actor_sub=u.get_editor_subsystem(u.EditorActorSubsystem)
cube=u.load_asset('/Engine/BasicShapes/Cube'); material=u.load_asset('/Engine/BasicShapes/BasicShapeMaterial')
def block(label,location,scale,rotation=u.Rotator()):
    actor=actor_sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*location),rotation)
    actor.set_actor_label(label); mesh=actor.get_component_by_class(u.StaticMeshComponent)
    mesh.set_static_mesh(cube); mesh.set_material(0,material); actor.set_actor_scale3d(u.Vector(*scale))
    mesh.set_collision_profile_name('BlockAll'); return actor
block('Carry_Floor',(400,0,-10),(24,16,.2))
block('Carry_BackWall',(800,0,150),(.2,12,3))
block('Carry_LowCeiling',(450,400,190),(4,3,.2))
block('Carry_CeilingWall',(450,550,100),(4,.2,2))
block('Carry_Slope',(350,-420,20),(4,2,.2),u.Rotator(0,0,15))
block('Carry_PlaceObstacle',(200,-150,35),(1,1,.7))
box_cls=u.load_asset('/Game/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox').generated_class()
items=[]
for label,kg,location in [('Carry_Box_5kg',5,(80,0,21)),('Carry_Box_9_99kg',9.99,(80,180,21)),
                          ('Carry_Box_10kg',10,(80,-180,21)),('Carry_Box_10_01kg',10.01,(80,-320,21)),
                          ('Carry_Box_Ceiling',5,(320,380,21))]:
    actor=actor_sub.spawn_actor_from_class(box_cls,u.Vector(*location)); actor.set_actor_label(label)
    component=actor.get_component_by_class(u.PhysicsPropComponent); component.set_editor_property('physics_row',u.DataTableRowHandle())
    actor.get_component_by_class(u.StaticMeshComponent).set_mass_override_in_kg('None',kg,True)
    items.append({'label':label,'kg':kg,'location':location})
start=actor_sub.spawn_actor_from_class(u.PlayerStart,u.Vector(0,0,100),u.Rotator(0,0,0)); start.set_actor_label('Carry_PlayerStart')
actor_sub.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(-45,-30,0))
actor_sub.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,400))
assert u.EditorLoadingAndSavingUtils.save_map(world,path)
(out/'review-map.json').write_text(json.dumps({'map':path,'items':items,'game_mode':gm.get_path_name()},indent=2),encoding='utf-8')
u.log('CARRY_REVIEW_MAP_SAVED '+path)
