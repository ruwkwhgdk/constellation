import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'ContourRepair';bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_Fitted.blend'));bpy.context.preferences.filepaths.save_version=0
ob=bpy.data.objects['Heroine_ContourRepair'];me=ob.data;normals={tuple(round(c,8) for c in me.vertices[l.vertex_index].co):me.corner_normals[i].vector.copy() for i,l in enumerate(me.loops)}
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);remove=[]
for p in me.polygons:
 if me.materials[p.material_index].name!='M_Skin':continue
 vs=[me.vertices[i].co for i in p.vertices];c=sum(vs,Vector())/len(vs)
 if not (-.0205<c.x<-.0125 and .893<c.z<.9002 and c.y<-.035):continue
 if any(v.x<-.023 or v.x>-.010 or v.z<.891 or v.z>.902 for v in vs):continue
 start=c+Vector((0,.00004,0));covered=False
 for j in range(8):
  h,n,i,dist=tree.ray_cast(start,Vector((0,1,0)),.012)
  if h is None or h.y>-.03:break
  if i!=p.index and n.y<-.25 and me.materials[me.polygons[i].material_index].name=='M_Skin':covered=True;break
  start=h+Vector((0,.00002,0))
 if covered:remove.append(p.index)
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES_ONLY');loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.to_mesh(me);bm.free();me.update();me.normals_split_custom_set([normals.get(tuple(round(c,8) for c in me.vertices[l.vertex_index].co),Vector((0,-1,0))) for l in me.loops])
(O/'overlap_removal.json').write_text(json.dumps({'redundant_faces_removed':len(remove),'face_indices':remove},indent=2))
sc=bpy.context.scene;sc.cycles.samples=24;sc.render.filepath=str(O/'renders/overlap_fixed.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_OverlapFixed.blend'));bpy.ops.render.render(write_still=True)
