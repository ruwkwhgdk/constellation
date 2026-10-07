import unreal as u
from pathlib import Path
import json,hashlib
root=Path(u.Paths.project_dir()).resolve(); out=root/'Saved/SceneEventIntegration';out.mkdir(exist_ok=True)
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
rows=[]
for a in reg.get_assets_by_class(u.TopLevelAssetPath('/Script/LevelSequence','LevelSequence'),True):
    p=str(a.package_name)
    if not p.startswith('/Game/Constellation/'):continue
    seq=a.get_asset();tracks=[]
    def track(t, binding='MASTER'):
        sections=[]
        for s in t.get_sections():
            d={'class':s.get_class().get_name()}
            try:d.update(start=s.get_start_frame(),end=s.get_end_frame())
            except:pass
            try:d['animation']=str(s.get_editor_property('params').get_editor_property('animation').get_path_name())
            except:pass
            sections.append(d)
        return {'binding':binding,'class':t.get_class().get_name(),'name':str(t.get_display_name()),'sections':sections}
    for t in seq.get_tracks():tracks.append(track(t))
    for b in seq.get_bindings():
        for t in b.get_tracks():tracks.append(track(t,str(b.get_name())))
    refs=[str(r) for r in reg.get_referencers(a.package_name,u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True))]
    file=root/'Content'/Path(p.removeprefix('/Game/')+'.uasset')
    rows.append({'path':p,'fps':str(seq.get_display_rate()),'start':seq.get_playback_start(),'end':seq.get_playback_end(),'tracks':tracks,'referencers':refs,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    try:
        bp=u.SceneDirectorLibrary.get_sequence_director_blueprint(seq)
        if bp:(out/(p.split('/')[-1]+'.director.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
    except Exception as e:u.log_warning(str(e))
(out/'sequences.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
paths=['/Game/Constellation/Core/BP_GameMode','/Game/Constellation/Core/GI_System','/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController','/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine','/Game/Constellation/Gameplay/Combat/BP_BattleManager','/Game/Constellation/Gameplay/Interaction/Actors/BP_BattleZone','/Game/Constellation/Gameplay/Interaction/Actors/BP_BattleZone_GateAuto','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence_Combat','/Game/Constellation/Gameplay/Combat/Components/AC_QuestProgressOnBattleEnd']
for p in paths:
    bp=u.load_asset(p)
    if bp:(out/(p.split('/')[-1]+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(out/'AbandonedSchool.txt').write_text(u.ResourceRecoveryLibrary.export_level_blueprint_graphs(w),encoding='utf-8')
actors=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    n=a.get_class().get_name()
    if any(x in n for x in ['Battle','Sequence','SceneEvent','Trigger']):
        d={'path':a.get_path_name(),'class':a.get_class().get_path_name(),'label':a.get_actor_label()}
        if isinstance(a,u.LevelSequenceActor):d['sequence']=str(a.get_sequence().get_path_name()) if a.get_sequence() else None
        actors.append(d)
(out/'actors.json').write_text(json.dumps(actors,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('SCENE_INTEGRATION_AUDIT_COMPLETE '+str(len(rows)))
