import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v006'
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
rows=json.loads((OUT.parent/'v005/shape_manifest.json').read_text());expected={r['id']:r for r in rows}
report=json.loads((OUT/'applied.json').read_text());actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
count=0;moss=0
for label,actor in actors.items():
    key=label.split('_')[2] if label.startswith('OH_FULL_') else '19' if label.startswith('OH_Tripo_Tree_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if key in expected:
        assert actor.static_mesh_component.static_mesh.get_name()==expected[key]['mesh'],label
        if key in report['moss_instances']:
            assert actor.static_mesh_component.get_material(0).get_name()=='M_OH_Moss_'+key;moss+=1
        count+=1
for p in report['foliage']:
    c=actors[p['label']].static_mesh_component;assert c.static_mesh and c.get_collision_profile_name()=='NoCollision'
assert len([n for n in actors if n.startswith('OH_Growth_')])==report['added_foliage']
w=actors['OH_SM_OH_Blockout_21'].static_mesh_component
if report['water_model']=='SingleLayerWater':
    assert w.get_material(0).get_editor_property('shading_model')==u.MaterialShadingModel.MSM_SINGLE_LAYER_WATER
else:
    assert w.get_material(0).get_editor_property('blend_mode')==u.BlendMode.BLEND_OPAQUE
    assert 'OH_WaterPlanarReflection' in actors
    assert u.SystemLibrary.get_console_variable_int_value('r.AllowGlobalClipPlane')==1
assert w.get_collision_profile_name()=='NoCollision'
assert count==532 and moss==sum(report['moss_instances'].values())
(OUT/'verification.json').write_text(json.dumps(dict(saved_existing_meshes=count,moss_instances=moss,attached_foliage=report['added_foliage'],water_model=report['water_model'],nonblocking_water_and_foliage=True,existing_flock_and_collision_checks='passed',playtest=False),indent=2))
u.log('HALL_GROWTH_WATER_VERIFIED')
