from pathlib import Path
import sys
P=Path(__file__).resolve().parent;source=P.parent/'RigReferenceFit/Delivery/export_game_rig.py'
sys.argv=['blender','--','--source',str(P/'Heroine_Attack01.blend'),'--out',str(P/'AS_player_heroine_new_Attack01_Horizontal.fbx'),'--bake','--start','1','--end','61']
code=source.read_text().replace("object_types={'MESH','ARMATURE'}","object_types={'ARMATURE'}").replace('embed_textures=True','embed_textures=False')
exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
