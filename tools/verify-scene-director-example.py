import json
from pathlib import Path
import unreal as u
asset=u.load_asset('/Game/SceneDirector/Examples/DA_FirstScene')
assert asset, 'Saved graph missing'
sequence=asset.get_editor_property('generated_sequence')
assert sequence, 'Embedded Level Sequence did not reload'
assert not asset.get_editor_property('needs_compile'), 'Saved graph is stale'
bindings=sequence.get_bindings()
assert len(bindings)==2, 'Expected NPC and camera bindings'
assert sequence.get_playback_end()==150, 'Expected five second scene at 30 fps'
bp=u.load_asset('/Game/SceneDirector/Examples/BP_DirectorStandIn')
cdo=u.get_default_object(bp.generated_class())
assert cdo.static_mesh_component.get_editor_property('static_mesh'), 'Sample BP lost its visible mesh'
report={'asset':asset.get_path_name(),'sequence':sequence.get_path_name(),'bindings':len(bindings),'end_frame':sequence.get_playback_end(),'sample_mesh':cdo.static_mesh_component.get_editor_property('static_mesh').get_path_name()}
path=Path(u.Paths.project_saved_dir())/'SceneDirector-reload.json'
path.write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('SCENE_DIRECTOR_RELOAD_PASS '+str(report))
