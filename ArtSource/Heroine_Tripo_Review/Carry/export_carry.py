import sys, json
from pathlib import Path
P=Path(__file__).resolve().parent; source=P.parent/'RigReferenceFit/Delivery/export_game_rig.py'
code=source.read_text(encoding='utf-8').replace("object_types={'MESH','ARMATURE'}","object_types={'ARMATURE'}").replace('embed_textures=True','embed_textures=False')
rows=json.loads((P/'motion_samples.json').read_text(encoding='utf-8'))
for row in rows:
    name=row['clip']; end=round(row['duration']*30)+1
    sys.argv=['blender','--','--source',str(P/f'Heroine_Carry_{name}.blend'),'--out',str(P/f'AS_Heroine_Carry_{name}.fbx'),'--bake','--start','1','--end',str(end)]
    exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
print('CARRY_EXPORTS_COMPLETE')
