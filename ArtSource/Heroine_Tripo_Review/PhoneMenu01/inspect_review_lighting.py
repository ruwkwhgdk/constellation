import bpy
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene
s.frame_set(91)
s.render.engine="BLENDER_WORKBENCH"
s.display.shading.color_type="SINGLE"
s.display.shading.single_color=(.63,.65,.68)
s.display.shading.show_shadows=False
s.display.shading.show_cavity=True
center=Vector((0,0,.85))
s.camera.location=center+Vector((.3,-4,.3))
s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
s.camera.data.type="ORTHO"
s.camera.data.ortho_scale=1.9
s.render.resolution_x=s.render.resolution_y=640
s.render.resolution_percentage=100
s.render.filepath=str(Path(bpy.data.filepath).parent/"lighting_check.png")
bpy.ops.render.render(write_still=True)
deps=bpy.context.evaluated_depsgraph_get()
for o in s.objects:
    if o.type=="MESH" and "Hair" in o.name:
        ev=o.evaluated_get(deps);me=ev.to_mesh()
        print("HAIR_MAX_EDGE",max(((me.vertices[e.vertices[0]].co-me.vertices[e.vertices[1]].co).length for e in me.edges),default=0),flush=True)
        ev.to_mesh_clear()
