import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'restored_seams.blend'));bpy.context.preferences.filepaths.save_version=0;body=bpy.data.objects['Heroine_DetailFinish2'];me=body.data;cid=json.loads((O/'components.json').read_text())['ids']
coords=[v.co.copy() for v in me.vertices];normmap={tuple(p.vertices):[me.corner_normals[l].vector.copy() for l in p.loop_indices] for p in me.polygons};skin=[p for p in me.polygons if cid[p.vertices[0]]==14];tree=BVHTree.FromPolygons(coords,[p.vertices[:] for p in skin]);remove=[]
for p in skin:
 c=p.center
 if not(-.025<c.x<-.0135 and .8855<c.z<.8945 and c.y<-.035):continue
 if not all(-.029<coords[i].x<-.011 and .883<coords[i].z<.897 for i in p.vertices):continue
 h,n,i,d=tree.ray_cast(c+Vector((0,.00003,0)),Vector((0,1,0)),.006)
 if h is not None and n.y<-.3 and h.y<-.035:remove.append(p.index)
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES_ONLY');bm.to_mesh(me);bm.free();me.update();norms=[]
for p in me.polygons:norms.extend(normmap.get(tuple(p.vertices),[p.normal.copy() for l in p.loop_indices]))
me.normals_split_custom_set(norms)
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in me.polygons if cid[p.vertices[0]]==14]);band=bpy.data.objects['Lower_Lid_Skin_-1'];bc=0
for v in band.data.vertices:
 row,k=divmod(v.index,4)
 if row<31 or k==0:continue
 h,n,i,d=tree.ray_cast(Vector((v.co.x,-1,v.co.z)),Vector((0,1,0)))
 if h is not None and -.065<h.y<-.035 and v.co.y<h.y+.00004:
  v.co.y+=(h.y+.00004-v.co.y)*(k/3);bc+=1
# Flatten the isolated small rear facet using nearby outer hair surface samples.
cx,cz=.044,.921;vs=[v for v in me.vertices if cid[v.index]==12 and v.co.y>.035];distance=lambda v:((v.co.x-cx)/.008)**2+((v.co.z-cz)/.010)**2
ring=sorted([v for v in vs if distance(v)>1],key=distance)[:16];A=np.array([[1,v.co.x-cx,v.co.z-cz] for v in ring]);b=np.array([v.co.y for v in ring]);fit=np.linalg.lstsq(A,b,rcond=None)[0];changed=[]
for v in vs:
 r2=distance(v)
 if r2<1:
  target=float(np.dot([1,v.co.x-cx,v.co.z-cz],fit));d=max(-.0015,min(.0015,target-v.co.y))*(1-r2);v.co.y+=d;changed.append(v.index)
me.update();ns=[n.vector.copy() for n in me.corner_normals]
for i,l in enumerate(me.loops):
 if l.vertex_index in changed:ns[i]=Vector((-fit[1],1,-fit[2])).normalized()
me.normals_split_custom_set(ns)
(O/'fold_changes.json').write_text(json.dumps({'removed_redundant_skin_faces':remove,'band_vertices_fit':bc,'rear_facet_vertices':changed},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/'fold_stage.blend'))
sc=bpy.context.scene;sc.cycles.samples=24
for name,loc,target,scale in [('eye_fold',(-.034,-3,.902),(-.034,0,.902),.10),('back_fold',(0,3,.89),(0,0,.89),.28),('angle',(-.9,-3,.878),(0,0,.878),.25)]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('FOLD_DONE',len(remove),bc,len(changed),flush=True)
