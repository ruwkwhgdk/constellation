"""Create a review arena once. Existing review assets are reused, never overwritten."""
import json
from pathlib import Path
import unreal as u
BASE = "/Game/Constellation/Review/CombatCore"
root = Path(u.Paths.project_dir()).resolve()
report = {"created": [], "reused": []}
assets = u.EditorAssetLibrary
assets.make_directory(BASE)
def action(name, source, begin, end, cost):
    path = BASE + "/" + name
    montage_path = BASE + "/AM_" + name
    montage = u.load_asset(montage_path) if assets.does_asset_exist(montage_path) else None
    if not montage:
        montage = assets.duplicate_asset(source, montage_path)
        if not montage or not u.CombatLabEditorLibrary.configure_review_montage(montage, begin, end):
            raise RuntimeError("Invalid review montage: " + montage_path)
        assets.save_loaded_asset(montage)
        report["created"].append(montage_path)
    else:
        report["reused"].append(montage_path)
    if assets.does_asset_exist(path):
        report["reused"].append(path)
        return u.load_asset(path)
    factory = u.DataAssetFactory()
    factory.set_editor_property("data_asset_class", u.CombatActionDefinition)
    obj = u.AssetToolsHelpers.get_asset_tools().create_asset(name, BASE, u.CombatActionDefinition, factory)
    obj.set_editor_property("display_name", name)
    obj.set_editor_property("montage", montage)
    obj.set_editor_property("stamina_cost", cost)
    obj.set_editor_property("damage", 15.0 if cost == 0 else 20.0)
    obj.set_editor_property("cooldown", 1.2 if cost == 0 else .2)
    assets.save_loaded_asset(obj)
    report["created"].append(path)
    return obj
hero = action("DA_PlayerSlash", "/Game/Constellation/Characters/Heroine/Refined/Animations/AM_player_heroine_new_Attack01_Horizontal", .35, .50, 10.)

# Mechanical three-step chain; steps 2/3 temporarily reuse Attack01, not authored combo motion.
follow2 = action("DA_PlayerFollowUp02", "/Game/Constellation/Characters/Heroine/Refined/Animations/AM_player_heroine_new_Attack01_Horizontal", .35, .50, 10.)
follow3 = action("DA_PlayerFollowUp03", "/Game/Constellation/Characters/Heroine/Refined/Animations/AM_player_heroine_new_Attack01_Horizontal", .35, .50, 10.)
for current, following in [(hero, follow2), (follow2, follow3)]:
    if assets.get_metadata_tag(current, "CombatFollowUpInitialized") != "1":
        if not current.get_editor_property("next_action"):
            current.set_editor_property("next_action", following)
        assets.set_metadata_tag(current, "CombatFollowUpInitialized", "1")
        assets.save_loaded_asset(current)

enemy_source = "/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AM_Slime_Attack"
source = u.load_asset(enemy_source)
length = source.get_play_length()
enemy = action("DA_EnemyStrike", enemy_source, length * .4, length * .55, 0.)
# Pattern prototypes reuse the slime attack; no newly authored heavy animation.
heavy_path = BASE + "/DA_EnemyHeavy"
new_heavy = not assets.does_asset_exist(heavy_path)
heavy = action("DA_EnemyHeavy", enemy_source, length * .4, length * .55, 0.)
if new_heavy:
    heavy.set_editor_property("damage", 25.)
    heavy.set_editor_property("cooldown", 2.5)
    heavy.set_editor_property("play_rate", .65)
    assets.save_loaded_asset(heavy)
profile_path = BASE + "/DA_SlimePatterns"
profile = u.load_asset(profile_path) if assets.does_asset_exist(profile_path) else None
if not profile:
    factory = u.DataAssetFactory()
    factory.set_editor_property("data_asset_class", u.CombatPatternProfile)
    profile = u.AssetToolsHelpers.get_asset_tools().create_asset("DA_SlimePatterns", BASE, u.CombatPatternProfile, factory)
    light_entry = u.CombatPatternEntry()
    for prop, value in {"id":"Light", "action":enemy, "weight":3., "max_distance":180., "max_angle":80., "max_consecutive":2}.items():
        light_entry.set_editor_property(prop, value)
    heavy_entry = u.CombatPatternEntry()
    for prop, value in {"id":"Heavy", "action":heavy, "weight":1., "max_distance":150., "max_angle":70., "max_consecutive":1}.items():
        heavy_entry.set_editor_property(prop, value)
    profile.set_editor_property("patterns", [light_entry, heavy_entry])
    assets.save_loaded_asset(profile)
map_path = BASE + "/L_CombatCore"
if not assets.does_asset_exist(map_path):
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    if not levels.new_level(map_path):
        raise RuntimeError("Unable to create combat review map")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    floor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0,0,-25))
    floor.set_actor_label("Combat floor")
    floor.static_mesh_component.set_static_mesh(u.load_asset("/Engine/BasicShapes/Cube"))
    floor.set_actor_scale3d(u.Vector(20,20,.5))
    light = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0,0,800), u.Rotator(pitch=-45, yaw=-30, roll=0))
    light.light_component.set_editor_property("intensity", 5.)
    sky = actors.spawn_actor_from_class(u.SkyLight, u.Vector(0,0,500))
    sky.light_component.set_editor_property("intensity", 1.)
    def character(label, location, definition, mesh, transform, is_enemy):
        actor = actors.spawn_actor_from_class(u.CombatLabCharacter, location)
        actor.set_actor_label(label)
        actor.set_editor_property("action", definition)
        actor.set_editor_property("training_enemy", is_enemy)
        component = actor.get_editor_property("mesh")
        component.set_skeletal_mesh_asset(mesh)
        component.set_relative_transform(transform, False, True)
        actor.set_editor_property("auto_possess_player", u.AutoReceiveInput.DISABLED if is_enemy else u.AutoReceiveInput.PLAYER0)
        return actor
    mesh = u.load_asset("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview")
    character("Player GAS slash", u.Vector(-180,0,100), hero, mesh,
              u.Transform(u.Vector(0,0,-88), u.Rotator(pitch=0, yaw=0, roll=0), u.Vector(1,1,1)), False)
    bp = u.load_asset("/Game/Constellation/Characters/Enemies/Blueprints/BP_Slime_Base")
    cdo = u.get_default_object(bp.generated_class())
    srcmesh = cdo.get_editor_property("mesh")
    monster = character("Enemy GAS strike", u.Vector(100,0,100), enemy, srcmesh.get_editor_property("skeletal_mesh_asset"),
                        srcmesh.get_relative_transform(), True)
    levels.save_current_level()
    report["created"].append(map_path)
else:
    report["reused"].append(map_path)
# The review world must not inherit the production respawn/player blueprint.
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
levels.load_level(map_path)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
settings = world.get_world_settings()
mode = settings.get_editor_property("default_game_mode")
if mode is None:
    settings.set_editor_property("default_game_mode", u.GameModeBase)
elif mode != u.GameModeBase.static_class():
    raise RuntimeError("Existing custom review game mode preserved; inspect before changing it")
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
if not any(isinstance(a, u.PlayerStart) for a in actors.get_all_level_actors()):
    actors.spawn_actor_from_class(u.PlayerStart, u.Vector(-180, 0, 100))
# Repair only an absent mesh in the generated review enemy; preserve populated meshes.
for actor in actors.get_all_level_actors():
    if isinstance(actor, u.DirectionalLight) or isinstance(actor, u.SkyLight):
        actor.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    if isinstance(actor, u.CombatLabCharacter) and not actor.get_editor_property("training_enemy"):
        component = actor.get_editor_property("mesh")
        rotation = component.get_editor_property("relative_rotation")
        if abs(rotation.pitch + 90) < .01 and abs(rotation.yaw) < .01 and abs(rotation.roll) < .01:
            component.set_relative_rotation(u.Rotator(pitch=0, yaw=0, roll=0), False, True)
    if isinstance(actor, u.CombatLabCharacter) and actor.get_editor_property("training_enemy"):
        component = actor.get_editor_property("mesh")
        if not component.get_editor_property("skeletal_mesh_asset"):
            bp = u.load_asset("/Game/Constellation/Characters/Enemies/Blueprints/BP_Slime_Base")
            srcmesh = u.get_default_object(bp.generated_class()).get_editor_property("mesh")
            mesh = srcmesh.get_editor_property("skeletal_mesh_asset")
            if not mesh:
                raise RuntimeError("Slime template has no mesh")
            component.set_skeletal_mesh_asset(mesh)
            component.set_relative_transform(srcmesh.get_relative_transform(), False, True)

# Populate locomotion only when absent; keep designer-authored animation choices.
for actor in actors.get_all_level_actors():
    if not isinstance(actor, u.CombatLabCharacter):
        continue
    enemy_actor = actor.get_editor_property("training_enemy")
    if enemy_actor and not actor.get_editor_property("pattern_profile"):
        actor.set_editor_property("pattern_profile", profile)
    animation_base = "/Game/Constellation/Characters/Enemies/Slime_Normal/Animation" if enemy_actor else "/Game/Constellation/Characters/Heroine/Refined/Animations"
    idle = "AS_Slime_Idle" if enemy_actor else "AS_player_heroine_new_PreviewRelaxed"
    move = "AS_Slime_Move" if enemy_actor else "AS_player_heroine_new_Run_Soft"
    for prop, name in [("idle_animation", idle), ("move_animation", move)]:
        if not actor.get_editor_property(prop):
            actor.set_editor_property(prop, u.load_asset(animation_base + "/" + name))
    movement = actor.get_editor_property("character_movement")
    if not enemy_actor and abs(movement.get_editor_property("max_walk_speed") - 250.) < .01:
        movement.set_editor_property("max_walk_speed", 168.)


# Explicit project-default synchronization requested by the user.
source_bp=u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine")
source_actor=actors.spawn_actor_from_class(source_bp.generated_class(),u.Vector(0,0,1000))
try:
    source_movement=source_actor.get_editor_property("character_movement")
    source_arm=source_actor.get_component_by_class(u.SpringArmComponent)
    source_camera=source_actor.get_component_by_class(u.CameraComponent)
    stats_class=u.load_asset("/Game/Constellation/Gameplay/Combat/Components/Ac_Stats").generated_class()
    speed=source_actor.get_component_by_class(stats_class).get_editor_property("Walk Speed")
    pc=u.get_default_object(u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController").generated_class())
    manager=u.get_default_object(pc.get_editor_property("player_camera_manager_class") or u.PlayerCameraManager)
    for actor in actors.get_all_level_actors():
        if not isinstance(actor,u.CombatLabCharacter) or actor.get_editor_property("training_enemy"):
            continue
        movement=actor.get_editor_property("character_movement")
        movement.set_editor_property("max_walk_speed",speed)
        for prop in ["max_acceleration","braking_deceleration_walking","ground_friction","braking_friction_factor","rotation_rate","orient_rotation_to_movement"]:
            movement.set_editor_property(prop,source_movement.get_editor_property(prop))
        arm=actor.get_editor_property("arm")
        for prop in ["target_arm_length","target_offset","socket_offset","relative_location","enable_camera_lag","camera_lag_speed","camera_lag_max_distance","enable_camera_rotation_lag","camera_rotation_lag_speed","use_pawn_control_rotation","do_collision_test"]:
            arm.set_editor_property(prop,source_arm.get_editor_property(prop))
        actor.get_editor_property("camera").set_editor_property("field_of_view",source_camera.get_editor_property("field_of_view"))
        actor.set_editor_property("project_yaw_scale",pc.get_deprecated_input_yaw_scale())
        actor.set_editor_property("project_pitch_scale",pc.get_deprecated_input_pitch_scale())
        actor.set_editor_property("project_pitch_min",manager.get_editor_property("view_pitch_min"))
        actor.set_editor_property("project_pitch_max",manager.get_editor_property("view_pitch_max"))
        actor.set_editor_property("project_look_action",u.load_asset("/Game/Constellation/Input/IA_Look"))
        actor.set_editor_property("project_input_context",u.load_asset("/Game/Constellation/Input/IAC_Default"))
finally:
    actors.destroy_actor(source_actor)

levels.save_current_level()

out = root / "Saved/CombatAudit/20261004"
out.mkdir(parents=True, exist_ok=True)
(out / "lab-setup.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
u.log("COMBAT_LAB_CREATED " + json.dumps(report))
