import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'ContourRepair'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_OverlapFixed.blend'))
bpy.data.objects['Lower_Lid_Skin_-1'].hide_render=True
sc=bpy.context.scene;sc.cycles.samples=16;sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=.60;sc.render.border_max_x=.74;sc.render.border_min_y=.35;sc.render.border_max_y=.53;sc.render.filepath=str(O/'renders/no_band_after.png');bpy.ops.render.render(write_still=True)
