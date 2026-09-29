"""Fresh-process saved map validation, separate from import."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=Path(globals().get('SOURCE_DIR',ROOT/'ArtSource/OvergrownHall/Blockout/v002'))
MAP=globals().get('MAP_PATH','/Game/Environment/OvergrownHall/Blockout/Maps/L_OvergrownHall_Blockout')
L=u.get_editor_subsystem(u.LevelEditorSubsystem); A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
rows=json.loads((OUT/'unreal_manifest.json').read_text())['assets']
for row in rows:
    a=actors['OH_'+row['name']]; c=a.static_mesh_component
    assert c.static_mesh
    for i in range(c.get_num_materials()): assert c.get_material(i)
    if row['collision']:
        assert c.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION
        assert c.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    else: assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION,(row['name'],str(c.get_collision_enabled()),str(c.get_collision_profile_name()))
bench=actors['OH_SM_OH_Blockout_14']; _,ext=bench.get_actor_bounds(False); assert abs(ext.x*2-180)<.2
ws=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_world_settings()
mode=ws.get_editor_property('default_game_mode'); assert mode
pawn_class=u.get_default_object(mode).get_editor_property('default_pawn_class'); assert pawn_class
pawn=u.get_default_object(pawn_class); capsule=pawn.get_component_by_class(u.CapsuleComponent); assert capsule
height=capsule.get_unscaled_capsule_half_height()
start=actors['OH_PlayerStart'].get_actor_location(); assert start.z>height+2,(start.z,height)
report=dict(status='saved_map_validation_pass',map=MAP,mesh_categories=len(rows),missing_meshes_or_materials=0,collision_settings_verified=True,bench_width_cm=ext.x*2,default_pawn=pawn_class.get_path_name(),capsule_half_height_cm=height,spawn_capsule_clearance_cm=start.z-height,playtest='not_run',render='Blender preview only; Unreal appearance not verified')
(OUT/'unreal_saved_verification.json').write_text(json.dumps(report,indent=2))
u.log('OVERGROWN_SAVED_MAP_PASS '+json.dumps(report))
