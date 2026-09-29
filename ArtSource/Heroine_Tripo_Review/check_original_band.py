import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'ContourRepair';bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_Checked.blend'))
band=bpy.data.objects['Lower_Lid_Skin_-1'];skin=band.data.materials[0]
with bpy.data.libraries.load(str(R/'BoundaryLocal/Heroine_BoundaryLocal.blend'),link=False) as (src,dst):dst.objects=['Lower_Lid_Skin_-1']
source=dst.objects[0];band.data=source.data.copy();band.data.materials.clear();band.data.materials.append(skin);bpy.data.objects.remove(source,do_unlink=True)
sc=bpy.context.scene;sc.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_BandRestored.blend'));sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=.58;sc.render.border_max_x=.75;sc.render.border_min_y=.34;sc.render.border_max_y=.56;sc.render.filepath=str(O/'renders/original_band.png');bpy.ops.render.render(write_still=True)
