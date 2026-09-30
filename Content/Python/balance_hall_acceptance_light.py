"""v027: reduce competing hard side light while preserving the approved layout."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v027';OUT.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    rows={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation();rows[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll])
        if isinstance(a,u.StaticMeshActor):rows[n]['mesh']=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None
    (OUT/'baseline.json').write_text(json.dumps(rows,indent=2))
settings=[('OH_Sun',u.DirectionalLightComponent,dict(intensity=1700)),('OH_Sky',u.SkyLightComponent,dict(intensity=1.8)),('OH_Finish_FocalSun',u.SpotLightComponent,dict(intensity=2200000,inner_cone_angle=5,outer_cone_angle=8,volumetric_scattering_intensity=4)),('OH_Reference_LowerWindowShaft',u.SpotLightComponent,dict(intensity=450000,volumetric_scattering_intensity=6))]
for name,cls,values in settings:
    a=actors[name];a.modify();c=a.get_component_by_class(cls)
    for k,v in values.items():c.set_editor_property(k,v)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,lights={n:v for n,cls,v in settings},playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_acceptance_light.py'))
