from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v008';D='/Game/Constellation/Environments/OvergrownHall/TripoFull'
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
expected={r['id']:r['mesh'] for r in load_current_json((OUT.parent/'v005/shape_manifest.json').read_text())}
expected.update({r['id']:r['mesh'] for r in load_current_json((OUT/'foliage_shapes.json').read_text())})
report=load_current_json((OUT/'applied.json').read_text());actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
existing=growth=moss=0
for name,a in actors.items():
    key=name.split('_')[2] if name.startswith('OH_FULL_') else '19' if name.startswith('OH_Tripo_Tree_') else '26' if name.startswith('OH_STRUCTURE_Roof_') else None
    if key:existing+=1
    if name.startswith('OH_Growth_'):key='18' if '_Vine_' in name else '17';growth+=1;assert a.static_mesh_component.get_collision_profile_name()=='NoCollision'
    if key:
        assert a.static_mesh_component.static_mesh.get_name()==expected[key],name
        mat='M_OH_Weathered_' if key in report['moss_material_instances'] else 'M_OH_Illustrated_'
        assert a.static_mesh_component.get_material(0).get_name()==mat+key,name
        if mat=='M_OH_Weathered_':moss+=1
assert existing==532 and growth==53
for p in report['growth']:
    a=actors[p['label']];s=a.get_actor_scale3d();loc=a.get_actor_location()
    assert all(abs(v-e)<.01 for v,e in zip([s.x,s.y,s.z],p['scale']))
    assert all(abs(v-e)<.01 for v,e in zip([loc.x,loc.y,loc.z],p['position']))
water=actors['OH_SM_OH_Blockout_21'].static_mesh_component;assert water.get_material(0).get_name()=='M_OH_ReflectivePuddle'
assert water.get_collision_profile_name()=='NoCollision' and 'OH_WaterPlanarReflection' in actors
tree=u.EditorAssetLibrary.load_asset(D+'/Meshes/SM_OH_Soft_19_Tree');assert u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(tree)>0
sun=actors['OH_Sun'];rot=sun.get_actor_rotation();light=sun.get_component_by_class(u.DirectionalLightComponent)
assert abs(rot.pitch+32)<.01 and abs(rot.yaw+125)<.01
assert abs(light.get_editor_property('intensity')-21000)<.1
assert abs(actors['OH_Sky'].get_component_by_class(u.SkyLightComponent).get_editor_property('intensity')-1.15)<.001
assert len(report['growth'])==77
(OUT/'verification.json').write_text(json.dumps(dict(existing_instances=existing,growth_instances=growth,varied_placements=len(report['growth']),moss_instances=moss,foliage_shapes=3,tree_collision=True,water_preserved=True,flock='passed',saved_lighting_verified=True,playtest=False),indent=2))
u.log('HALL_ATMOSPHERE_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v008').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout','/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull').replace('unreal_exposure_fixed.png','unreal_atmosphere.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next")
script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_atmosphere','exec'),globals())
