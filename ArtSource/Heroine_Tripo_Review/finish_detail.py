import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent; O=R/'DetailFinish'; O.mkdir(exist_ok=True); (O/'renders').mkdir(exist_ok=True); (O/'textures').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'NeutralExpression/Heroine_NeutralExpression.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_NeutralExpression']; me=body.data
orig=[v.co.copy() for v in me.vertices]; norms=[n.vector.copy() for n in me.corner_normals]
adj=[set() for v in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
skinverts=set(i for p in me.polygons if me.materials[p.material_index].name=='M_Skin' for i in p.vertices)
weights={}
for v in me.vertices:
 x,y,z=v.co
 # Thin skin ridge above original upper lash; do not move the lash or brow.
 if v.index in skinverts and -.050<x<-.019 and y<-.037 and .905<z<.909:
  weights[v.index]=.22*max(0,1-abs(z-.907)/.002)*min(1,(x+.050)/.003,(-.019-x)/.003)
for iteration in range(3):
 pos=[v.co.copy() for v in me.vertices]
 for i,w in weights.items():
  if adj[i]:
   d=sum((pos[j] for j in adj[i]),Vector())/len(adj[i])-pos[i]
   if d.length>.00035:d*=.00035/d.length
   me.vertices[i].co+=d*w
me.update();me.normals_split_custom_set(norms)
# Blend only bottom edge of lower skin strip into the existing cheek depth.
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in me.polygons if me.materials[p.material_index].name=='M_Skin'])
band=bpy.data.objects['Lower_Lid_Skin_-1']; bandchanges=0
for v in band.data.vertices:
 row,k=divmod(v.index,4)
 if k<2 or row>35:continue
 hit,n,idx,dist=tree.ray_cast(Vector((v.co.x,-1,v.co.z)),Vector((0,1,0)))
 if hit is not None and -.07<hit.y<-.03 and abs(hit.y-v.co.y)<.005:
  v.co.y+=(hit.y+.00003-v.co.y)*(.40 if k==2 else 1);bandchanges+=1
band.data.update()
# Diagnostic cross-sections used to fit bracelet to actual wrist surface.
sections={}
for x in [-.363,-.358,-.353,-.348,-.343]:
 pts=[v.co for v in me.vertices if abs(v.co.x-x)<.0012 and v.index in skinverts]
 if pts:sections[str(x)]=[[min(p[j] for p in pts),max(p[j] for p in pts)] for j in [1,2]]
report={'skin_ridge_vertices':len(weights),'lower_band_vertices':bandchanges,'wrist_sections':sections}
(O/'stage1.json').write_text(json.dumps(report,indent=2))
body.name='Heroine_DetailFinish'
sc=bpy.context.scene;sc.cycles.samples=20;sc.render.use_border=False;sc.render.use_crop_to_border=False
def render(name,loc,target,scale,res=1000):
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=res;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage1.blend'))
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
print('STAGE1_DONE',json.dumps(report),flush=True)
