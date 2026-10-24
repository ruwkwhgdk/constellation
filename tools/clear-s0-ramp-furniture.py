"""Approved clear player routes: relocate six furniture actors, never delete."""
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/RampFurniture_20261018';O.mkdir(parents=True,exist_ok=True)
A=u.get_editor_subsystem(u.EditorActorSubsystem)
placements={
 'BP_AbandonedSchool_Desk_C_48':(1800,-2600,400),
 'BP_AbandonedSchool_Desk_C_49':(2100,-2600,400),
 'BP_AbandonedSchool_Chair_C_21':(1800,-2460,400),
 'BP_AbandonedSchool_Chair_C_51':(2100,-2460,400),
 'BP_AbandonedSchool_Chair_C_52':(1800,-2740,430),
 'BP_AbandonedSchool_Chair_C_53':(2100,-2740,400),
}
actors={a.get_name():a for a in A.get_all_level_actors()};report=[]
for name,position in placements.items():
 a=actors[name];p=a.get_actor_location()
 assert 1200<p.x<1400 and -2550<p.y<-2000,(name,str(p))
 report.append(dict(name=name,label=a.get_actor_label(),before=[p.x,p.y,p.z],after=list(position)))
for row in report:actors[row['name']].set_actor_location(u.Vector(*row['after']),False,True)
(O/'moves.json').write_text(json.dumps(report,indent=2))
