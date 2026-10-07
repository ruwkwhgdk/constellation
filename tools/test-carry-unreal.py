import json
from pathlib import Path
import unreal as u
root = Path(u.Paths.project_dir())/'Saved/CarryReview'
base = u.load_asset('/Game/Constellation/Characters/Heroine/Base/Player_Heroine_Skeleton')
new = u.load_asset('/Game/Constellation/Characters/Heroine/Refined/SKEL_player_heroine_new')
for name, obj in [('base',base),('refined',new)]:
    (root/('skeleton-'+name+'.txt')).write_text(u.CarryEditorLibrary.inspect_carry_skeleton(obj),encoding='utf-8')
bp=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
cdo=u.get_default_object(bp.generated_class()); mesh=cdo.get_editor_property('mesh')
u.log('CARRY_MESH_TRANSFORM '+str(mesh.get_editor_property('relative_location'))+' '+str(mesh.get_editor_property('relative_rotation'))+' '+str(mesh.get_editor_property('relative_scale3d')))
u.log('CARRY_BASE_BOUNDS '+str(mesh.get_editor_property('skeletal_mesh_asset').get_bounds()))
