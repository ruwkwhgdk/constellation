import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent/'RigReferenceFit/Delivery'
source=D/'export_game_rig.py'
sys.argv=['blender','--','--source',str(P/'Heroine_Run_Soft.blend'),'--out',str(P/'AS_player_heroine_new_Run_Soft.fbx'),'--bake','--start','1','--end','31']
code=source.read_text().replace("object_types={'MESH','ARMATURE'}","object_types={'ARMATURE'}").replace('embed_textures=True','embed_textures=False')
scope={'__file__':str(source),'__name__':'__main__'}
exec(compile(code,str(source),'exec'),scope)
