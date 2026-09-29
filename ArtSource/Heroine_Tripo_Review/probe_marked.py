import bpy
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import barycentric_transform
import numpy as np
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'DetailPreserved/Heroine_DetailPreserved.blend'));o=bpy.data.objects['Heroine_DetailPreserved'];tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
im=next(n.image for n in o.data.materials['M_Hair'].node_tree.nodes if n.type=='TEX_IMAGE');pixels=np.array(im.pixels[:]).reshape(im.size[1],im.size[0],4)
for px,py in [(209,848),(220,879),(296,945),(200,799),(824,519),(752,598)]:
 x=-.034+(px/1100-.5)*.1;z=.902+(.5-py/1100)*.1;h,n,idx,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 print(px,py,'CO',list(h) if h else None,'MAT',o.data.materials[o.data.polygons[idx].material_index].name if h else None,'FACE',idx)

 if h:
  p=o.data.polygons[idx];lis=list(p.loop_indices)[:3];cs=[o.data.vertices[o.data.loops[l].vertex_index].co for l in lis];uvs=[Vector((*o.data.uv_layers.active.data[l].uv,0)) for l in lis];uv=barycentric_transform(h,*cs,*uvs);print('COLOR',pixels[int(uv.y*im.size[1])%im.size[1],int(uv.x*im.size[0])%im.size[0]])
