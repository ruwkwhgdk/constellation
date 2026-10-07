import unreal as u,json
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/VFXImplementation'
m=u.load_asset('/Game/Constellation/VFX/Meshes/SM_GlassShard')
r={'nanite':str(m.get_editor_property('nanite_settings')),'bounds':str(m.get_bounds()),'bbox':str(m.get_bounding_box()),'materials':[str(x.material_interface) for x in m.static_materials]}
(out/'shard-audit.json').write_text(json.dumps(r,indent=2))
u.log(str(r))
