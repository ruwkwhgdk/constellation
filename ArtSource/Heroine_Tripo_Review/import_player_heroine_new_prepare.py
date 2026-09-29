import bpy,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;O=P/'UnrealImport_player_heroine_new';O.mkdir(exist_ok=True);(O/'textures').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'RigContourFix/Delivery/Heroine_GameSkeleton.blend'))
materials=set(m for o in bpy.context.scene.objects if o.type=='MESH' for m in o.data.materials if m)
out={'materials':{},'textures':{}}
def clean(n):return re.sub('[^A-Za-z0-9_]+','_',n).strip('_')
for m in sorted(materials,key=lambda m:m.name):
 bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
 if not bs:continue
 d={'material_name':m.name,'base_color':list(bs.inputs['Base Color'].default_value),'roughness':bs.inputs['Roughness'].default_value,'metallic':bs.inputs['Metallic'].default_value,'specular':bs.inputs['Specular IOR Level'].default_value,'two_sided':not m.use_backface_culling,'links':{}}
 for key in ['Base Color','Roughness','Metallic','Normal']:
  socket=bs.inputs[key]
  if socket.is_linked:
   node=socket.links[0].from_node
   if node.type=='TEX_IMAGE' and node.image:
    im=node.image;name='T_player_heroine_new_'+clean(im.name.removeprefix('T_'))+('_BC' if key=='Base Color' else '')
    path=O/'textures'/(name+'.png');im.filepath_raw=str(path);im.file_format='PNG';im.save()
    out['textures'][name]={'path':str(path),'srgb':key=='Base Color'};d['links'][key]=name
   else:d['links'][key]={'node':node.type}
 out['materials'][m.name]=d
(O/'materials.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
