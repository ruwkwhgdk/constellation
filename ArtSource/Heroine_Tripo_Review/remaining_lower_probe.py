import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'seams_stage.blend'));body=bpy.data.objects['Heroine_DetailFinish2'];band=bpy.data.objects['Lower_Lid_Skin_-1']
with bpy.data.libraries.load(str(O/'eyepatch_stage.blend'),link=False) as (a,b):b.objects=['Lower_Lid_Skin_-1','Heroine_DetailFinish2']
restoreband,restorebody=b.objects;band.data=restoreband.data
oldnorms=[n.vector.copy() for n in restorebody.data.corner_normals];norms=oldnorms+[n.vector.copy() for n in list(body.data.corner_normals)[len(oldnorms):]];body.data.normals_split_custom_set(norms)
bpy.data.objects.remove(restoreband);bpy.data.objects.remove(restorebody);me=body.data
polys=[p for p in me.polygons if me.materials[p.material_index].name.startswith('M_Skin')];tree=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in polys]);out=[]
for x in [-.025,-.022,-.019,-.016]:
 for z in [.887,.889,.891,.893]:
  origin=Vector((x,-1,z));layers=[]
  for k in range(8):
   h,n,i,d=tree.ray_cast(origin,Vector((0,1,0)))
   if h is None:break
   layers.append({'y':h.y,'normal':list(n),'face':polys[i].index});origin=h+Vector((0,.000015,0))
  out.append({'x':x,'z':z,'layers':layers})
(O/'lower_layers.json').write_text(json.dumps(out,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'restored_seams.blend'));print('RESTORED_LOWER',flush=True)
