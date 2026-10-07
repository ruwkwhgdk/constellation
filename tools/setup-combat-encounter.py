"""Dedicated navigation arena; preserves the existing combat core arena."""
import json
from pathlib import Path
import unreal as u
base="/Game/Constellation/Review/CombatCore"
assets=u.EditorAssetLibrary
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
path=base+"/L_CombatEncounter"
new_map=not assets.does_asset_exist(path)
if new_map:
    assert assets.duplicate_asset(base+"/L_CombatCore",path), "Could not duplicate core review map"
assert levels.load_level(path)
profile_path=base+"/DA_SlimeEncounter"
profile=u.load_asset(profile_path) if assets.does_asset_exist(profile_path) else None
if not profile:
    factory=u.DataAssetFactory()
    factory.set_editor_property("data_asset_class",u.CombatEncounterProfile)
    profile=u.AssetToolsHelpers.get_asset_tools().create_asset("DA_SlimeEncounter",base,u.CombatEncounterProfile,factory)
    assets.save_loaded_asset(profile)
for actor in actors.get_all_level_actors():
    if not isinstance(actor,u.CombatLabCharacter):
        continue
    if actor.get_editor_property("training_enemy"):
        if not actor.get_editor_property("encounter_profile"):
            actor.set_editor_property("encounter_profile",profile)
        if new_map:
            actor.set_actor_location(u.Vector(100,0,100),False,False)
            actor.set_actor_rotation(u.Rotator(pitch=0,yaw=180,roll=0),False)
    elif new_map:
        actor.set_actor_location(u.Vector(-500,0,100),False,False)
if new_map:
    cube=u.load_asset("/Engine/BasicShapes/Cube")
    wall=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(-200,0,30))
    wall.set_actor_label("Navigation detour obstacle")
    wall.static_mesh_component.set_static_mesh(cube)
    wall.set_actor_scale3d(u.Vector(1,4.4,.6))
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert u.CombatLabEditorLibrary.build_encounter_navigation(world), "Navigation build or projection failed"
levels.save_current_level()
report={"passed":True,"map":path,"profile":profile.get_path_name(),"created_map":new_map}
out=Path(u.Paths.project_dir())/"Saved/CombatAudit/20261004/encounter-setup.json"
out.write_text(json.dumps(report,indent=2),encoding="utf-8")
u.log("COMBAT_ENCOUNTER_SETUP "+json.dumps(report))
