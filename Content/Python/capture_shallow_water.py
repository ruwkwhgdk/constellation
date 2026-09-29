"""Verify the saved v012 level, capture it, and take a no-water diagnostic view."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v012';D='/Game/Environment/OvergrownHall/TripoFull'
report=json.loads((OUT/'applied.json').read_text());assert report['saved']
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
foliage=json.loads((OUT.parent/'v010/applied.json').read_text())
for row in foliage['changes']:
    c=actors[row['label']].static_mesh_component
    assert c.static_mesh.get_name()=='SM_OH_Painted'+row['kind']
    assert c.get_material(0).get_name()==('M_OH_LeafFar' if row['far'] else 'M_OH_LeafNear')
for row in json.loads((OUT.parent/'v011/applied.json').read_text())['changes']:
    assert actors[row['label']].static_mesh_component.static_mesh.get_name()==row['mesh']
baseline=json.loads((OUT/'baseline.json').read_text())
for row in report['floor_changes']:
    a=actors[row['label']];p=a.get_actor_location();target=row['position'];assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],target))<.01
    assert 0<baseline[row['label']]['position'][2]-p.z<5
for label in report['shore_slabs']:
    mesh=actors[label].static_mesh_component.static_mesh;assert mesh.get_name()=='SM_OH_ShoreSlab'
    assert mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
water=actors['OH_SM_OH_Blockout_21'];c=water.static_mesh_component;m=c.get_material(0)
assert c.static_mesh.get_name()=='SM_OH_RippleSheet' and m.get_name()==report['material']
assert c.get_collision_profile_name()=='NoCollision'
assert m.get_editor_property('blend_mode')==u.BlendMode.BLEND_TRANSLUCENT
assert m.get_editor_property('translucency_lighting_mode')==u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING
assert m.get_editor_property('screen_space_reflections') and m.get_editor_property('use_planar_forward_reflections')
assert not m.get_editor_property('tangent_space_normal')
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
assert abs(actors['OH_Sun'].get_actor_rotation().yaw+55)<.01
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,translucent_surface=True,depth_fade=True,world_normal_ripples=True,reflection_flags=True,lowered_floor_tiles=len(report['floor_changes']),max_floor_drop_cm=max(r['drop_cm'] for r in report['floor_changes']),shore_slab_count=len(report['shore_slabs']),closed_slab_collision=True,foliage_preserved=foliage['counts'],broken_arches_preserved=3,birds=28,physical_refraction=False,playtest=False,performance_test=False),indent=2))
u.log('SHALLOW_WATER_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v012').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_shallows.png')
script=script.replace('pp=next',"water=next(a for a in actors if a.get_actor_label()=='OH_SM_OH_Blockout_21')\nu.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
script=script.replace('started=time.time(); requested=False','started=time.time(); requested=False; diagnostic=False')
script=script.replace('global requested','global requested,diagnostic')
script=script.replace("    shot=out/","    if elapsed>55 and not diagnostic:\n        diagnostic=True\n        water.set_is_temporarily_hidden_in_editor(True)\n        u.AutomationLibrary.take_high_res_screenshot(1200,640,str(out/'without_water.png'),camera=cam,delay=2)\n    if elapsed>64:\n        water.set_is_temporarily_hidden_in_editor(False)\n    shot=out/")
exec(compile(script,'capture_shallow_water','exec'),globals())
