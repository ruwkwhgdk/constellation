"""Read saved review map and measure actual actor placement, not planned positions."""
import unreal as u
import json
from pathlib import Path
SRC=Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular/Production/v001'
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert level.load_level('/Game/Environment/StairwellModular/ReviewKit/Maps/L_Stairwell_KitReview')
actors={str(a.get_actor_label()):a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
def bounds(a):
    c,e=a.get_actor_bounds(False); return c-e,c+e
slo,shi=bounds(actors['SWReview_Assembly_Stairs'])
llo,lhi=bounds(actors['SWReview_Assembly_Landing'])
assert abs(shi.x-llo.x)<.01 and abs(shi.z-lhi.z)<.01,('Stair landing seam',slo,shi,llo,lhi)
assert abs(slo.y-llo.y)<.01 and abs(shi.y-lhi.y)<.01,('Landing lateral alignment',slo,shi,llo,lhi)
rails=[a for n,a in actors.items() if n.startswith('SWReview_Assembly_Rail_')]
assert len(rails)==2
ys=sorted(a.get_actor_location().y for a in rails)
assert abs(ys[0]-(slo.y+8))<.01 and abs(ys[1]-(shi.y-8))<.01,('Rails outside stair',ys,slo,shi)
for a in rails:
    lo,hi=bounds(a); cy=a.get_actor_location().y
    if cy<(slo.y+shi.y)/2:
        assert abs(hi.y-(cy+2))<.05 and lo.y<cy-8,('Brackets face inward',a.get_actor_label())
    else:
        assert abs(lo.y-(cy-2))<.05 and hi.y>cy+8,('Brackets face inward',a.get_actor_label())
clearance=ys[1]-ys[0]-4
assert abs(clearance-120)<.01
result=dict(status='pass',stair_landing_join=True,rail_brackets_outward=True,rail_clearance_cm=clearance,axis='FBX Y reflected; assembly uses measured UE bounds',playtest='not_run')
(SRC/'reports/assembly_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
u.log('ASSEMBLY_VERIFIED '+json.dumps(result))
