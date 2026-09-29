"""Reload, verify geometry/material persistence and render v007."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v007'
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
rows={r['id']:r for r in json.loads((OUT.parent/'v005/shape_manifest.json').read_text())}
count=0;growth=0
for label,a in actors.items():
    key=label.split('_')[2] if label.startswith('OH_FULL_') else '19' if label.startswith('OH_Tripo_Tree_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if key in rows:
        c=a.static_mesh_component
        assert c.static_mesh.get_name()==rows[key]['mesh'],label
        assert c.get_material(0).get_name()=='M_OH_Illustrated_'+key,label
        count+=1
    if label.startswith('OH_Growth_'):
        c=a.static_mesh_component; key='18' if '_Vine_' in label else '17'
        assert c.get_collision_profile_name()=='NoCollision'
        assert c.get_material(0).get_name()=='M_OH_Illustrated_'+key
        growth+=1
assert count==532 and growth==53
w=actors['OH_SM_OH_Blockout_21'].static_mesh_component
assert w.get_material(0).get_name()=='M_OH_ReflectivePuddle'
assert w.get_collision_profile_name()=='NoCollision'
assert 'OH_WaterPlanarReflection' in actors
assert u.SystemLibrary.get_console_variable_int_value('r.AllowGlobalClipPlane')==1
tex=u.EditorAssetLibrary.load_asset('/Game/Environment/OvergrownHall/TripoFull/IllustratedTextures/T_OH_PaintedMineral')
assert tex.get_editor_property('resize_during_build_x')==1024 and tex.get_editor_property('resize_during_build_y')==1024
assert tex.get_editor_property('mip_gen_settings')==u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE
texture_size=[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()]
assert texture_size==[1024,1024],texture_size
(OUT/'verification.json').write_text(json.dumps(dict(saved_existing_meshes=count,attached_foliage=growth,material_overrides=count+growth,geometry_collision_and_flock='passed',reflective_water_preserved=True,texture_runtime_size=texture_size,averaged_mips=True,playtest=False),indent=2))
u.log('HALL_PIGMENT_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v007').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout','/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull').replace('unreal_exposure_fixed.png','unreal_pigment.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next")
script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_pigment','exec'),globals())
