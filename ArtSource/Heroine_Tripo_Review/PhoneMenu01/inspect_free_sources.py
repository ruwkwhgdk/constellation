"""Read official downloaded FBX motions without altering their poses."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).parent/"FreeSources01"
for fbx in sorted(root.glob("*.fbx")):
 out=root/fbx.stem
 if out.exists():continue
 out.mkdir()
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(fbx))
 rig=next(o for o in bpy.data.objects if o.type=="ARMATURE")
 action=rig.animation_data.action
 lo,hi=map(int,action.frame_range)
 s=bpy.context.scene;s.render.fps=30;s.frame_start=lo;s.frame_end=hi
 names=[b.name for b in rig.pose.bones]
 rows=[]
 for frame in range(lo,hi+1):
  s.frame_set(frame)
  rows.append({"frame":frame,**{n:list(rig.matrix_world@rig.pose.bones[n].head) for n in names if n.endswith(("LeftHand","RightHand","Hips"))}})
 (out/"audit.json").write_text(json.dumps({"source":str(fbx),"bones":names,"frames":[lo,hi],"positions":rows},indent=2))
 bpy.ops.object.camera_add(location=(2,-4,1.4))
 cam=bpy.context.object;s.camera=cam
 # FBX is Z-up, forward -Y after importer conversion. Verify using actual render.
 center=Vector((0,0,.95))
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.type="ORTHO";cam.data.ortho_scale=2.1
 s.render.engine="BLENDER_WORKBENCH";s.display.shading.color_type="MATERIAL"
 s.display.shading.light="STUDIO";s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
 s.world=bpy.data.worlds.new("ReviewWorld");s.world.color=(.12,.12,.12)
 s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
 s.render.image_settings.file_format="PNG"
 s.frame_set(lo);bpy.ops.wm.save_as_mainfile(filepath=str(out/(fbx.stem+"_Raw.blend")))
 for frame in sorted(set([lo,lo+15,lo+30,lo+60,(lo+hi)//2,hi-60,hi-30,hi])):
  s.frame_set(max(lo,frame));s.render.filepath=str(out/f"{frame:04}.png");bpy.ops.render.render(write_still=True)
 print("SOURCE_DONE",fbx.name,lo,hi,flush=True)
