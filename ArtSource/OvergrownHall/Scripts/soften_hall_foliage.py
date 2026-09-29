"""Small leaf-selective smoothing of accepted Tripo meshes; UV/topology preserved."""
import bpy,numpy as np,json
from pathlib import Path
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall')
OUT=ROOT/'TripoReplacement/v008'; OUT.mkdir(parents=True,exist_ok=True)
report=[]
for key,name,limit in [('17','Shrub',.028),('18','Vine',.016),('19','Tree',.055)]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'TripoReplacement/v005/{key}_{name}/clean.blend'))
    bpy.context.preferences.filepaths.save_version=0
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('UCX'))
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    before=np.array([v.co[:] for v in obj.data.vertices]); uv=obj.data.uv_layers.active; assert uv
    path=ROOT/(f'TripoReplacement/v001/Tree/basecolor.png' if key=='19' else f'TripoReplacement/v002/{key}_{name}/basecolor.png')
    img=bpy.data.images.load(str(path),check_existing=True);w,h=img.size
    pixels=np.array(img.pixels[:],dtype=np.float32).reshape(h,w,4)
    weights=np.zeros(len(before));counts=np.zeros(len(before))
    for loop in obj.data.loops:
        v=uv.data[loop.index].uv;rgb=pixels[int(v.y*h)%h,int(v.x*w)%w,:3]
        weight=float(np.clip((rgb[1]-max(rgb[0],rgb[2]))*14+.12,0,1))
        weights[loop.vertex_index]+=weight;counts[loop.vertex_index]+=1
    weights/=np.maximum(counts,1)
    # Preserve lower tree trunk regardless of baked texture color.
    if key=='19':weights*=np.clip((before[:,2]-.65)/1.2,0,1)
    vg=obj.vertex_groups.new(name='LeafPigmentMask')
    for i,value in enumerate(weights):vg.add([i],float(value),'REPLACE')
    mod=obj.modifiers.new('Round leaf tips','SMOOTH');mod.factor=.62;mod.iterations=6;mod.vertex_group=vg.name
    bpy.ops.object.modifier_apply(modifier=mod.name)
    after=np.array([v.co[:] for v in obj.data.vertices]);delta=after-before
    length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,limit/np.maximum(length,1e-9))[:,None]
    after=before+delta
    for v,co in zip(obj.data.vertices,after):v.co=co
    for f in obj.data.polygons:f.use_smooth=True
    obj.data.update();obj.name=f'SM_OH_Soft_{key}_{name}'
    folder=OUT/(key+'_'+name);folder.mkdir(exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(folder/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'soft.blend'))
    assert np.isfinite(after).all()
    report.append(dict(id=key,name=name,mesh=obj.name,vertices=len(after),triangles=sum(len(p.vertices)-2 for p in obj.data.polygons),max_displacement_cm=float(np.linalg.norm(delta,axis=1).max()*100),mean_displacement_cm=float(np.linalg.norm(delta,axis=1).mean()*100),uv_preserved=True,topology_preserved=True,dimensions_m=(after.max(0)-after.min(0)).tolist()))
(OUT/'foliage_shapes.json').write_text(json.dumps(report,indent=2))
print('FOLIAGE_SOFTENED',report)
