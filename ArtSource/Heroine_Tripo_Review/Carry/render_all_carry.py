import bpy
from pathlib import Path
folder=Path(__file__).resolve().parent
code=compile((folder/'render_carry.py').read_text(encoding='utf-8'),str(folder/'render_carry.py'),'exec')
for clip in ('Place','Throw','Hold','Aim'):
    bpy.ops.wm.open_mainfile(filepath=str(folder/f'Heroine_Carry_{clip}.blend'))
    exec(code,{'__file__':str(folder/'render_carry.py'),'__name__':'__main__'})
