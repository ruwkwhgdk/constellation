import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'ContourRepair'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_Final.blend'))
bpy.data.objects['Lower_Lid_Skin_-1'].hide_render=True
sc=bpy.context.scene;sc.cycles.samples=16;sc.render.filepath=str(O/'renders/no_band.png');bpy.ops.render.render(write_still=True)
