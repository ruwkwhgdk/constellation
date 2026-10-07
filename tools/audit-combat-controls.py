import unreal as u, json
from pathlib import Path
root=Path(u.Paths.project_dir())
out=root/"Saved/CombatAudit/20261004"
actor_sub=u.get_editor_subsystem(u.EditorActorSubsystem)
bp=u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine")
actor=actor_sub.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,200))
def props(obj,names):
    result={}
    for n in names:
        try: result[n]=str(obj.get_editor_property(n))
        except Exception as e: result[n]="UNAVAILABLE "+str(e)[:90]
    return result
report={"movement":props(actor.get_editor_property("character_movement"),["max_walk_speed","max_acceleration","braking_deceleration_walking","ground_friction","braking_friction_factor","rotation_rate","orient_rotation_to_movement"])}
stats=actor.get_component_by_class(u.load_asset("/Game/Constellation/Gameplay/Combat/Components/Ac_Stats").generated_class())
report["stats"]=props(stats,["Walk Speed","walk_speed"])
report["arms"]=[props(x,["target_arm_length","target_offset","socket_offset","relative_location","relative_rotation","enable_camera_lag","camera_lag_speed","camera_lag_max_distance","enable_camera_rotation_lag","camera_rotation_lag_speed","use_pawn_control_rotation","do_collision_test"]) for x in actor.get_components_by_class(u.SpringArmComponent)]
report["cameras"]=[props(x,["field_of_view","relative_location","relative_rotation"]) for x in actor.get_components_by_class(u.CameraComponent)]
pcbp=u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController")
pc=u.get_default_object(pcbp.generated_class())
report["controller"]={"yaw_scale":pc.get_deprecated_input_yaw_scale(),"pitch_scale":pc.get_deprecated_input_pitch_scale()}
pcm=pc.get_editor_property("player_camera_manager_class")
report["camera_manager"]=props(u.get_default_object(pcm or u.PlayerCameraManager),["view_pitch_min","view_pitch_max"])
reg=u.AssetRegistryHelpers.get_asset_registry()
report["input"]=[]
for a in reg.get_assets_by_path("/Game/Constellation/Input",recursive=True):
    obj=a.get_asset()
    row={"path":str(a.package_name),"class":obj.get_class().get_name()}
    if isinstance(obj,u.InputAction):
        row["modifiers"]=[{"class":x.get_class().get_name(),"values":props(x,["scalar","x","y","z","order"])} for x in obj.get_editor_property("modifiers")]
    if isinstance(obj,u.InputMappingContext):
        row["mappings"]=[]
        for m in obj.get_editor_property("default_key_mappings").get_editor_property("mappings"):
            if m.action and "Look" in m.action.get_path_name():
                row["mappings"].append({"action":str(m.action),"key":str(m.key),"modifiers":[{"class":x.get_class().get_name(),"values":props(x,["scalar","x","y","z","order"])} for x in m.modifiers]})
    report["input"].append(row)
actor_sub.destroy_actor(actor)
(out/"project-control-defaults.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
(out/"heroine-control-graph.txt").write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding="utf-8")
u.log("COMBAT_CONTROL_AUDIT "+json.dumps(report,ensure_ascii=False))
