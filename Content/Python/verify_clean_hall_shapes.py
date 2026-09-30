from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v005'
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
rows=load_current_json((OUT/'shape_manifest.json').read_text());expected={r['id']:r for r in rows}
E=u.EditorAssetLibrary;SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
for row in rows:
    mesh=E.load_asset(D+'/Meshes/'+row['mesh']);extent=mesh.get_bounds().box_extent*2
    assert all(abs(a-b*100)<.6 for a,b in zip([extent.x,extent.y,extent.z],row['dimensions_m'])),row['id']
    if row['id'] in ['13','19']:assert SM.get_simple_collision_count(mesh)>0
count=0
for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    label=actor.get_actor_label()
    key=label.split('_')[2] if label.startswith('OH_FULL_') else '19' if label.startswith('OH_Tripo_Tree_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if key in expected:
        c=actor.static_mesh_component
        assert c.static_mesh.get_name()==expected[key]['mesh'],label
        prefix='M_OH_Painted_' if expected[key]['organic'] else 'M_OH_Clean_'
        assert c.get_material(0).get_name()==prefix+key,label
        count+=1
assert count==532
(OUT/'verification.json').write_text(json.dumps(dict(saved_instances=count,all_21_mesh_dimensions_pass=True,correct_materials=True,floor_and_tree_simple_collision=True,flock_verified=True,playtest=False),indent=2))
u.log('CLEAN_SHAPES_VERIFIED')
