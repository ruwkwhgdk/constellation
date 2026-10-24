"""Measure the reported one-second discontinuity in the maintained source."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(__file__).resolve().parent
s=bpy.context.scene;rig=bpy.data.objects['Slime_Liquid_Rig'];body=bpy.data.objects['Slime_Body']
tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
rows=[];prev=None
for f in range(2,98):
    s.frame_set(f)
    p=rig.matrix_world@rig.pose.bones['drop'].head
    hit=tree.ray_cast(Vector((p.x,-3,p.z)),Vector((0,1,0)),6)[0]
    rows.append({'frame':f,'seconds':(f-1)/24,'position':list(p),
                 'step_m':(p-prev).length if prev is not None else 0,
                 'front_raycast_y':hit.y if hit is not None else None})
    prev=p.copy()
report={'around_one_second':[r for r in rows if 18<=r['frame']<=34],
        'largest_visible_steps':sorted([r for r in rows if r['frame']<88],key=lambda r:r['step_m'],reverse=True)[:8]}
(out/'drop-diagnosis-before.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
