import unreal as u,json,runpy
from pathlib import Path
root=Path(u.Paths.project_dir()); out=root/'ArtSource/OvergrownHall/TripoReplacement/v001'
D='/Game/Constellation/Environments/OvergrownHall/TripoReplacement'; MAP=D+'/Maps/L_OvergrownHall_TripoReview'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(MAP)
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
assert len([n for n in actors if n.startswith('OH_Tripo_Pillar_')])==30
assert len([n for n in actors if n.startswith('OH_Tripo_Tree_')])==19
assert 'OH_SM_OH_Blockout_19' not in actors
measurements={}
for kind,expected in [('Pillar',(65,65,300)),('Tree',(521.034,457.169,600))]:
    mesh=u.EditorAssetLibrary.load_asset(D+'/Meshes/SM_OH_Tripo_'+kind)
    bounds=mesh.get_bounds(); dims=bounds.box_extent*2
    actual=[dims.x,dims.y,dims.z]
    assert all(abs(a-b)<1 for a,b in zip(actual,expected)),(kind,actual)
    assert mesh.get_material(0).get_path_name().startswith(D+'/Materials/')
    measurements[kind]=actual
assert actors['OH_SM_OH_Blockout_02'].static_mesh_component.static_mesh.get_name()=='SM_OH_RemainingPiers'
runpy.run_path(str(root/'Content/Python/verify_overgrown_flock.py'),init_globals={'FLOCK_DEST':D,'FLOCK_MAP':'L_OvergrownHall_TripoReview','FLOCK_OUT':out/'Flock'})
(out/'verification.json').write_text(json.dumps(dict(map=MAP,dimensions_cm=measurements,pillars=30,trees=19,flock_verified=True,playtest=False),indent=2))
u.log('TRIPO_REPLACEMENT_VERIFIED')
