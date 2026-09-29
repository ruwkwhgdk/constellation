"""Fresh v014 saved mesh/material/collision checks, matched render and active-viewport CSV."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v014';D='/Game/Environment/OvergrownHall/TripoFull'
report=json.loads((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};assert len(actors)==report['actor_count']
base=json.loads((OUT/'baseline.json').read_text());SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
for row in report['changed']:
    a=actors[row['label']];c=a.static_mesh_component;assert c.static_mesh.get_name()==row['mesh'];assert SM.get_lod_count(c.static_mesh)==3
    assert c.get_material(0).get_name()=='M_OH_LeafWind'+('Far' if row['far'] else 'Near');assert c.get_material(0).get_editor_property('blend_mode')==u.BlendMode.BLEND_MASKED
    p=a.get_actor_location();assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],base[row['label']]['position']))<.01
    if row['kind']=='Tree':assert SM.get_simple_collision_count(c.static_mesh)>0;assert c.get_material(1).get_name()=='M_OH_Illustrated_19'
    elif row['kind']=='Shrub':assert c.get_material(1).get_name()=='M_OH_Illustrated_17';assert c.get_collision_profile_name()=='NoCollision'
for name in report['shadow_disabled']:assert not actors[name].static_mesh_component.get_editor_property('cast_shadow')
assert not actors['OH_Finish_FocalSun'].get_component_by_class(u.SpotLightComponent).get_editor_property('cast_shadows')
assert actors['OH_Sun'].get_component_by_class(u.DirectionalLightComponent).get_editor_property('cast_shadows')
reflection=actors['OH_WaterPlanarReflection'].get_component_by_class(u.PlanarReflectionComponent)
assert reflection.get_editor_property('screen_percentage')==60 and reflection.get_editor_property('capture_every_frame')
for row in report['lods']:
    mesh=u.EditorAssetLibrary.load_asset(D+'/FoliageRuntime/'+row['mesh']);assert [mesh.get_num_triangles(i) for i in range(3)]==row['triangles']
for row in json.loads((OUT.parent/'v013/applied.json').read_text())['architecture']:assert actors[row['label']].static_mesh_component.static_mesh.get_name()==row['mesh']
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_name()=='M_OH_ShallowTransmission'
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,lod0_preserved=True,lods_verified=True,leaf_material_slots=True,positions_preserved=True,tree_collision=True,architecture_water_birds_preserved=True,shadow_disabled=len(report['shadow_disabled']),playtest='user'),indent=2));u.log('HALL_RUNTIME_VERIFIED')
# Keep exactly the v013 reference-camera capture / CSV timing for a qualified comparison.
source=(ROOT/'Content/Python/capture_hall_final_art.py').read_text();capture=source[source.index('script=(ROOT/'):]
capture=capture.replace('TripoReplacement/v013','TripoReplacement/v014').replace('unreal_final_art.png','unreal_runtime.png').replace('Hall_v013.csv','Hall_v014.csv')
exec(compile(capture,'capture_runtime','exec'),globals())
