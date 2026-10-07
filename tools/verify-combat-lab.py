"""Read-only review asset checks, run with Unreal Python."""
import json
from pathlib import Path
import unreal as u
base="/Game/Constellation/Review/CombatCore"
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
levels.load_level(base+"/L_CombatCore")
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
mode=world.get_world_settings().get_editor_property("default_game_mode")
actors=[a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.CombatLabCharacter)]
rows=[]
for a in actors:
    component=a.get_editor_property("mesh")
    rotation=component.get_editor_property("relative_rotation")
    assert abs(rotation.pitch)<.01 and abs(rotation.roll)<.01, "Fighter mesh must stand upright"
    action=a.get_editor_property("action")
    mesh=a.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset")
    assert action and mesh, "Actor needs action and mesh: "+a.get_actor_label()
    montage=action.get_editor_property("montage")
    assert montage.get_editor_property("skeleton")==mesh.get_editor_property("skeleton"), "Skeleton mismatch"
    for prop in ["idle_animation", "move_animation"]:
        animation=a.get_editor_property(prop)
        assert animation, "Missing locomotion clip: "+prop
        assert animation.get_editor_property("skeleton")==mesh.get_editor_property("skeleton"), "Locomotion skeleton mismatch"
    rows.append({"label":a.get_actor_label(),"mesh":mesh.get_path_name(),"action":action.get_path_name(),"enemy":a.get_editor_property("training_enemy")})
assert len(actors)==2, "Expected exactly two review fighters"
assert mode==u.GameModeBase.static_class(), "Review map must isolate the production game mode"
result={"passed":True,"actors":rows,"game_mode":mode.get_path_name()}
enemy=next(a for a in actors if a.get_editor_property("training_enemy"))
profile=enemy.get_editor_property("pattern_profile")
assert profile, "Missing enemy pattern profile"
entries=profile.get_editor_property("patterns")
assert len(entries)>=2, "Default review expects multiple patterns"
ids=set()
for entry in entries:
    key=str(entry.get_editor_property("id"))
    assert key not in ids and key!="None", "Pattern IDs must be unique"
    ids.add(key)
    definition=entry.get_editor_property("action")
    assert definition and definition.get_editor_property("montage"), "Pattern action missing"
    assert definition.get_editor_property("montage").get_editor_property("skeleton")==enemy.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset").get_editor_property("skeleton")
result["enemy_patterns"]={"profile":profile.get_path_name(),"ids":sorted(ids)}

actor_sub=u.get_editor_subsystem(u.EditorActorSubsystem)
source=actor_sub.spawn_actor_from_class(u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine").generated_class(),u.Vector(0,0,1000))
try:
    player=next(a for a in actors if not a.get_editor_property("training_enemy"))
    stats_cls=u.load_asset("/Game/Constellation/Gameplay/Combat/Components/Ac_Stats").generated_class()
    project_speed=source.get_component_by_class(stats_cls).get_editor_property("Walk Speed")
    assert player.get_editor_property("character_movement").get_editor_property("max_walk_speed")==project_speed, "Project movement speed differs"
    source_arm=source.get_component_by_class(u.SpringArmComponent)
    for prop in ["target_arm_length","target_offset","socket_offset","relative_location","enable_camera_lag","camera_lag_speed","camera_lag_max_distance","enable_camera_rotation_lag","camera_rotation_lag_speed"]:
        assert player.get_editor_property("arm").get_editor_property(prop)==source_arm.get_editor_property(prop), "Project camera differs: "+prop
    pc=u.get_default_object(u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController").generated_class())
    assert player.get_editor_property("project_yaw_scale")==pc.get_deprecated_input_yaw_scale()
    assert player.get_editor_property("project_pitch_scale")==pc.get_deprecated_input_pitch_scale()
    assert player.get_editor_property("project_look_action")==u.load_asset("/Game/Constellation/Input/IA_Look")
    assert player.get_editor_property("project_input_context")==u.load_asset("/Game/Constellation/Input/IAC_Default")
    chain=[]
    current=player.get_editor_property("action")
    while current:
        assert current.get_path_name() not in chain, "Unexpected cycle in review chain"
        chain.append(current.get_path_name())
        montage=current.get_editor_property("montage")
        assert montage.get_editor_property("skeleton")==player.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset").get_editor_property("skeleton")
        following=current.get_editor_property("next_action")
        if following:
            assert 0 <= current.get_editor_property("input_window_start") < current.get_editor_property("input_window_end") <= montage.get_play_length()
        current=following
    assert len(chain)==3, "Default review fixture expects three attacks"
    result["follow_up_chain"]=chain
    result["project_controls"]={"matched":True,"walk_speed":project_speed,"camera_lag_speed":source_arm.get_editor_property("camera_lag_speed"),"yaw_scale":pc.get_deprecated_input_yaw_scale(),"pitch_scale":pc.get_deprecated_input_pitch_scale()}
finally:
    actor_sub.destroy_actor(source)

out=Path(u.Paths.project_dir())/"Saved/CombatAudit/20261004/lab-verification.json"
out.write_text(json.dumps(result,indent=2),encoding="utf-8")
u.log("COMBAT_LAB_VERIFIED "+json.dumps(result))
