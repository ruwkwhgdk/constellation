import unreal as u,json
from pathlib import Path
L=u.get_editor_subsystem(u.LevelEditorSubsystem); A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout')
out={'extended_luminance':u.SystemLibrary.get_console_variable_int_value('r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange'),'actors':[]}
for a in A.get_all_level_actors():
    if isinstance(a,u.PostProcessVolume):
        s=a.get_editor_property('settings')
        out['actors'].append(dict(name=a.get_actor_label(),unbound=a.get_editor_property('unbound'),**{k:str(s.get_editor_property(k)) for k in ['auto_exposure_method','auto_exposure_min_brightness','auto_exposure_max_brightness','auto_exposure_bias','override_auto_exposure_bias','override_auto_exposure_min_brightness','override_auto_exposure_max_brightness']}))
    for cls in [u.DirectionalLightComponent,u.SkyLightComponent]:
        c=a.get_component_by_class(cls)
        if c: out['actors'].append(dict(name=a.get_actor_label(),intensity=c.get_editor_property('intensity')))
folder=Path(u.Paths.project_dir())/'ArtSource/OvergrownHall/Scene/v001'
(folder/'exposure_audit.json').write_text(json.dumps(out,indent=2))
u.log('EXPOSURE_AUDIT '+json.dumps(out))
