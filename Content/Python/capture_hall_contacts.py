import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v017';report=json.loads((OUT/'applied.json').read_text())
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for row in report['contacts']:
    a=actors[row['label']];p=a.get_actor_location();assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],row['position']))<.01
    c,e=a.get_actor_bounds(False);pc,pe=actors[row['parent']].get_actor_bounds(False)
    assert all(abs(v-w)<ve+we for v,w,ve,we in zip([c.x,c.y,c.z],[pc.x,pc.y,pc.z],[e.x,e.y,e.z],[pe.x,pe.y,pe.z])),row
    assert a.static_mesh_component.get_collision_profile_name()=='NoCollision'
slab=actors[report['slab']];assert slab.static_mesh_component.static_mesh.get_path_name()==report['slab_mesh']
assert slab.static_mesh_component.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
base=json.loads((OUT/'baseline.json').read_text())[report['slab']];p=slab.get_actor_location();assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],base['position']))<.01
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
for n in json.loads((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_name()=='M_OH_WaterSoft'
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,attached_leaf_bounds=len(report['contacts']),slab_collision=True,slab_position_preserved=True,roof_water_birds_preserved=True,rear_trees_absent=True,playtest='user'),indent=2));u.log('HALL_CONTACTS_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v017').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_contacts.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_contacts','exec'),globals())
