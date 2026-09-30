import bpy,json,itertools
from pathlib import Path
from mathutils.kdtree import KDTree
p=Path(__file__).parent;data=json.loads((p/'placement_target.json').read_text(encoding='utf-8-sig'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(p/'existing_dummy.fbx'))
vs=[o.matrix_world@v.co*100 for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('UCX') for v in o.data.vertices]
raw=data.pop('native_vertices_cm');kd=KDTree(len(raw))
for i,v in enumerate(raw):kd.insert(v,i)
kd.balance();scores=[]
for swap,sx,sy in itertools.product([False,True],[-1,1],[-1,1]):
    errs=[]
    for v in vs[::max(1,len(vs)//1000)]:
        xyz=(v[1]*sx,v[0]*sy,v[2]) if swap else (v[0]*sx,v[1]*sy,v[2])
        errs.append(kd.find(xyz)[2])
    scores.append(dict(swap_xy=swap,x_sign=sx,y_sign=sy,mean_error_cm=sum(errs)/len(errs)))
scores.sort(key=lambda x:x['mean_error_cm']);best=scores[0]
assert best['mean_error_cm']<.01,scores
data['blender_to_unreal_axis_check']=best
data['opening_outward_unreal_local']=[-best['x_sign'],0,0] if best['swap_xy'] else [0,-best['y_sign'],0]
data['direction_evidence']='FBX front/back renders show opening toward Blender -Y; coordinate transform matched against native Unreal vertices.'
(p/'placement_target.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
(p/'axis_check.json').write_text(json.dumps(scores,indent=2),encoding='utf-8')
print('AXIS_OK',best,data['opening_outward_unreal_local'])
