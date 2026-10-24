import bpy
from pathlib import Path
R=Path(bpy.path.abspath('//'))
R=Path(r'C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/SchoolOpening/Decor')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for i,name in enumerate(['MoonPhoto','SaturnPhoto','NebulaPhoto','MoonSticker','StarSticker','PlanetSticker']):
 mesh=bpy.data.meshes.new('SM_S0_'+name);mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)]);mesh.update()
 ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(ob)
 uv=mesh.uv_layers.new(name='UVMap');col=i%3;row=i//3
 # Half-texel inset avoids neighbouring cards bleeding into the edge.
 lo=(col/3+1/1536,1-(row+1)/2+1/1024);hi=((col+1)/3-1/1536,1-row/2-1/1024)
 for loop,xy in zip(uv.data,[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]):loop.uv=xy
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(R/(mesh.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'LockerScrapbook.blend'))
