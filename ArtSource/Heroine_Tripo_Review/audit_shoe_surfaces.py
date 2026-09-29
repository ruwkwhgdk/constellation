import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'NeutralExpression/Heroine_NeutralExpression.blend'));d=bpy.context.evaluated_depsgraph_get();out=[]
for px,py in [(310,665),(298,530),(720,538),(704,666),(303,710),(322,592)]:
 x=(px/1000-.5)*.24;z=.067+(.5-py/1000)*.24;hit,pos,n,idx,ob,mat=bpy.context.scene.ray_cast(d,Vector((x,-1,z)),Vector((0,1,0)))
 if hit:
  m=ob.data.materials[ob.data.polygons[idx].material_index];p=m.node_tree.nodes.get('Principled BSDF');out.append({'pixel':[px,py],'material':m.name,'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,'specular':p.inputs['Specular IOR Level'].default_value})
(R/'NeutralInspection/shoe_surface_probe.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
