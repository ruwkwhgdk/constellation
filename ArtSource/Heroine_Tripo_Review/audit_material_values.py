import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'NeutralExpression/Heroine_NeutralExpression.blend'))
a={}
for name in ['M_Shoes','M_Stockings','M_Skin','M_Hair','M_Cardigan']:
 m=bpy.data.materials[name];p=m.node_tree.nodes.get('Principled BSDF');a[name]={n:("linked" if p.inputs[n].is_linked else p.inputs[n].default_value) for n in ['Metallic','Roughness','Specular IOR Level','Coat Weight','Subsurface Weight']}
(R/'NeutralInspection/material_audit.json').write_text(json.dumps(a,indent=2));print(json.dumps(a))
