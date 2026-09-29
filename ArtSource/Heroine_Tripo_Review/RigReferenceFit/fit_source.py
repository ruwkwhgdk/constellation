import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from shape_fit import warp_point
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'RigContourFix/shoulder_source.blend'))
ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids']
report={'vertices':{},'textures':{}}
for image in bpy.data.images:
 if image.packed_file:report['textures'][image.name]=hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 inv=o.matrix_world.inverted();worst=0.;face_affine_error=0.
 for v in o.data.vertices:
  p=o.matrix_world@v.co;hair=o.name=='Heroine_DetailFinish2' and ids[v.index] in [12,24,25,33,34]
  q=warp_point(p,cloth=o.name=='Heroine_DetailFinish2' and ids[v.index]==4,hair=hair)
  worst=max(worst,(q-p).length)
  if p.z>=.84 and not hair:
   expected=p.copy();expected.x*=.89;expected.y*=.89;expected.z=1-(1-p.z)*.89
   face_affine_error=max(face_affine_error,(q-expected).length)
  v.co=inv@q
 o.data.update();report['vertices'][o.name]={'count':len(o.data.vertices),'max_move':worst,'head_uniform_scale_error':face_affine_error}
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'shoulder_source.blend'))
(P/'fit_source_report.json').write_text(json.dumps(report,indent=2))
