import bpy,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
pose=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'relaxed'
view=sys.argv[sys.argv.index('--')+2] if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+2 else 'front'
bpy.ops.wm.open_mainfile(filepath=str(P/'comparison_aligned.blend'))
for o in list(bpy.context.scene.objects):
 if o.type not in ['LIGHT','CAMERA']:bpy.data.objects.remove(o,do_unlink=True)
scene=bpy.context.scene
spacing=.95 if pose=='relaxed' else 1.4
for label,x in [('reference',-spacing),('before',0),('after',spacing)]:
 with bpy.data.libraries.load(str(P/f'snapshot_{label}_{pose}.blend')) as (s,d):d.objects=s.objects
 for o in d.objects:
  scene.collection.objects.link(o)
  if view!='front':o.data.transform(Matrix.Rotation(math.pi/2 if view=='side' else math.pi,4,'Z'))
  o.location.x+=x
 curve=bpy.data.curves.new(label,'FONT');curve.body=label.upper();curve.align_x='CENTER';curve.size=.06;o=bpy.data.objects.new(label,curve);scene.collection.objects.link(o);o.location=(x,-.3,1.72);o.rotation_euler=(math.pi/2,0,0)
scene.camera.data.ortho_scale=3.3 if pose=='relaxed' else 4.35;scene.camera.location=(0,-5,.86)
scene.camera.rotation_euler=(Vector((0,0,.86))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1650;scene.render.resolution_y=1000;scene.cycles.samples=32
suffix=pose if view=='front' else pose+'_'+view
scene.render.filepath=str(P/f'comparison_{suffix}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/f'comparison_{suffix}.blend'))
