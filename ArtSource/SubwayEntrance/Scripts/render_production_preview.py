import bpy,json
from pathlib import Path
O=Path(__file__).resolve().parents[1]/'Production/v001'
bpy.ops.wm.open_mainfile(filepath=str(O/'entrance_kit.blend'))
for name in ['Stone','Soffit','WarmTile']:
    noise=next(n for n in bpy.data.materials[name].node_tree.nodes if n.type=='TEX_NOISE')
    assert abs(noise.inputs['Scale'].default_value-.4)<.0001
s=bpy.context.scene;s.camera=bpy.data.objects['exterior'];s.render.filepath=str(O/'exterior.png');bpy.ops.render.render(write_still=True)
(O/'source_validation.json').write_text(json.dumps(dict(blend_reopened=True,soft_materials=True,preview_refreshed=True)),encoding='utf-8')
print('PRODUCTION_SOURCE_VERIFIED')
