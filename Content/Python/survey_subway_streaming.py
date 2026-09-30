import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());out={};L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
for path in ['/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland','/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2']:
    assert L.load_level(path)
    w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=w.get_world_settings()
    row={'settings':{},'special':[],'actors':[]}
    for p in ['default_game_mode','world_partition','enable_world_bounds_checks','kill_z']:
        try:row['settings'][p]=str(ws.get_editor_property(p))
        except Exception as e:row['settings'][p]=str(e)
    for a in A.get_all_level_actors():
        c=a.get_class().get_name();r={'label':a.get_actor_label(),'class':c,'location':str(a.get_actor_location())}
        row['actors'].append(r)
        if any(x in c.lower() for x in ['light','sky','fog','postprocess','levelscript','audio','sound','gamemode']):
            r['export']=a.get_path_name();row['special'].append(r)
    out[path]=row
(R/'ArtSource/SubwayEntrance/Design/streaming_survey.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('SUBWAY_STREAM_SURVEY_OK')
