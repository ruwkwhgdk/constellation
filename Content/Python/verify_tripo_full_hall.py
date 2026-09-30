from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy,math
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v002';D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(MAP)
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
rows=load_current_json((OUT/'kit_manifest.json').read_text());placements=load_current_json((OUT/'placements.json').read_text());counts={};dimensions={}
for row in rows:
    mesh=u.EditorAssetLibrary.load_asset(D+'/Meshes/'+row['mesh']);assert mesh
    b=mesh.get_bounds().box_extent*2;actual=[b.x,b.y,b.z]
    assert all(abs(actual[j]-row['dimensions_m'][j]*100)<.5 for j in range(3)),(row['id'],actual)
    assert mesh.get_material(0).get_path_name().startswith(D+'/Materials/')
    dimensions[row['id']]=actual
for i,r in enumerate(placements):
    id=r['id'];a=actors['OH_FULL_'+id+'_%04d'%i];c=a.static_mesh_component
    assert c.static_mesh and c.get_material(0)
    assert c.static_mesh.get_path_name().startswith(D+'/Meshes/') or (id=='02' and '/TripoReplacement/' in c.static_mesh.get_path_name())
    assert all(math.isfinite(x) for x in [a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z])
    if id in ['16','17','18']:assert c.get_collision_profile_name()=='NoCollision'
    else:assert c.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION
    counts[id]=counts.get(id,0)+1
assert len([n for n in actors if n.startswith('OH_Tripo_Tree_')])==19
assert not [n for n in actors if n.startswith('OH_SM_OH_Blockout_') and not n.endswith('_21')]
bench=next(a for n,a in actors.items() if n.startswith('OH_FULL_14_'));center,ext=bench.get_actor_bounds(False);assert abs(ext.x*2-180)<.5
cam=actors['OH_ReferenceCamera'];assert (center-cam.get_actor_location()).dot(cam.get_actor_right_vector())<0
floor=u.EditorAssetLibrary.load_asset(D+'/Meshes/SM_OH_T_13_Floor');assert floor.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX
assert u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(floor)>0
pp=actors['OH_Exposure'].get_editor_property('settings');assert pp.auto_exposure_min_brightness==1024 and pp.auto_exposure_bias==0
runpy.run_path(str(ROOT/'Content/Python/verify_overgrown_flock.py'),init_globals={'FLOCK_DEST':D,'FLOCK_MAP':'L_OvergrownHall_TripoFull','FLOCK_OUT':OUT/'Flock'})
(OUT/'verification.json').write_text(json.dumps(dict(status='fresh_saved_level_pass',map=MAP,dimensions_cm=dimensions,instances=counts,bench_width_cm=ext.x*2,old_visible_meshes=0,retained_water_effect=True,flock_verified=True,floor_simple_collision=True,playtest=False,performance_test=False),indent=2))
u.log('TRIPO_FULL_VERIFICATION_PASS')
