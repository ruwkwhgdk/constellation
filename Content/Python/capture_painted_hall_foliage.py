import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v010';D='/Game/Environment/OvergrownHall/TripoFull'
report=json.loads((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for row in report['changes']:
    c=actors[row['label']].static_mesh_component
    assert c.static_mesh.get_name()=='SM_OH_Painted'+row['kind']
    assert c.get_material(0).get_name()==('M_OH_LeafFar' if row['far'] else 'M_OH_LeafNear')
    assert c.get_material(0).get_editor_property('blend_mode')==u.BlendMode.BLEND_MASKED
    if row['kind']!='Crown':assert c.get_material(1).get_name()=='M_OH_Illustrated_'+('19' if row['kind']=='Tree' else '17')
    if row['kind']!='Tree':assert c.get_collision_profile_name()=='NoCollision'
tree=u.EditorAssetLibrary.load_asset(D+'/Meshes/SM_OH_PaintedTree');assert u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(tree)>0
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_name()=='M_OH_QuietWater'
assert abs(actors['OH_Sun'].get_actor_rotation().yaw+55)<.01
tex=u.EditorAssetLibrary.load_asset(D+'/FoliagePaint/T_OH_PaintedLeaves');assert tex.blueprint_get_size_x()==1024 and tex.get_editor_property('do_scale_mips_for_alpha_coverage')
(OUT/'verification.json').write_text(json.dumps(dict(saved_counts=report['counts'],material_slots_verified=True,tree_collision=True,nonblocking_foliage=True,alpha_coverage_mips=True,water_light_bird_count_preserved=True,playtest=False,performance_test=False),indent=2))
u.log('PAINTED_FOLIAGE_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v010').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_foliage.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next");script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_foliage','exec'),globals())
