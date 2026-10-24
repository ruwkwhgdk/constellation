import unreal as u,json,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());P=R/'ArtSource/SchoolGymDoor/Polish_v002'
report=json.loads((P/'Reports/applied.json').read_text())
for path,expected in report['protected_hashes'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==expected,path
mat=u.load_asset(report['material']);M=u.MaterialEditingLibrary
customs=[x for x in u.ObjectIterator(u.MaterialExpressionCustom) if x.get_outer()==mat]
surface=next(x for x in customs if 'PaintColor' in [str(i.get_editor_property('input_name')) for i in x.get_editor_property('inputs')])
normal=next(x for x in customs if [str(i.get_editor_property('input_name')) for i in x.get_editor_property('inputs')]==['P','W','N'])
assert surface.get_editor_property('code')==(P/'weathering.hlsl').read_text()
assert normal.get_editor_property('code')==(P/'surface_normal.hlsl').read_text()
assert not mat.get_editor_property('tangent_space_normal')
assert M.get_material_property_input_node(mat,u.MaterialProperty.MP_NORMAL)==normal
assert M.get_material_property_input_node(mat,u.MaterialProperty.MP_WORLD_POSITION_OFFSET) is None
result={'passed':True,'saved_surface_code_verified':True,'world_normal_connected':True,'no_displacement':True,'mesh_blueprint_map_byte_identical':True,'material':report['material']}
(P/'Reports/saved-verification.json').write_text(json.dumps(result,indent=2));u.log('GYM_SURFACE_V002_VERIFIED')

