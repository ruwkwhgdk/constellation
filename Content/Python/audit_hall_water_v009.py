import unreal as u,json
from pathlib import Path
OUT=Path(u.Paths.project_dir())/'ArtSource/OvergrownHall/TripoReplacement/v009'
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull')
report={}
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    n=a.get_actor_label()
    if n=='OH_SM_OH_Blockout_21' or n.startswith('OH_FULL_13_'):
        p=a.get_actor_location();b,e=a.get_actor_bounds(False);r=a.get_actor_rotation()
        report[n]=dict(location=[p.x,p.y,p.z],bounds=[b.x,b.y,b.z,e.x,e.y,e.z],rotation=[r.pitch,r.yaw,r.roll])
(OUT/'water_audit.json').write_text(json.dumps(report,indent=2));u.SystemLibrary.quit_editor()
