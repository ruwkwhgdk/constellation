"""Exercise the actual HUD tutorial entry point in a disposable PIE world."""
import unreal as u, time, json, traceback
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/TutorialAudit20261023'
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
s=dict(start=time.monotonic(),phase=0,rows=[])
u.EditorPythonScripting.set_keep_python_script_alive(True)
def widgets(w):return [x for x in u.WidgetLibrary.get_all_widgets_of_class(w,u.TutorialPromptWidget,False) if x.is_in_viewport()]
def snap(w,label):
    s['rows'].append(dict(label=label,widgets=[dict(text=str(x.get_instruction_text()),opacity=x.get_render_opacity(),visibility=str(x.get_visibility())) for x in widgets(w)]))
def finish(error=''):
    (out/'runtime-probe.json').write_text(json.dumps(dict(error=error,rows=s['rows']),ensure_ascii=False,indent=2),encoding='utf-8')
    u.unregister_slate_post_tick_callback(handle)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play()
    u.SystemLibrary.quit_editor()
def tick(dt):
    try:
        now=time.monotonic()
        if now-s['start']>90:raise RuntimeError('timeout')
        w=ed.get_game_world()
        if not w:return
        pc=u.GameplayStatics.get_player_controller(w,0)
        if not pc or not pc.get_controlled_pawn():return
        if s['phase']==0:
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.SchoolOpeningSceneActor):a.destroy_actor()
            for x in widgets(w):x.remove_from_parent()
            s.update(phase=1,at=now)
        elif s['phase']==1 and now-s['at']>1:
            hud=pc.get_hud()
            for texture,keys in [('Move',['W','A','S','D']),('Jump',['SpaceBar']),('Interact',['F']),('Transform',['Z'])]:
                kk=[]
                for name in keys:
                    key=u.Key();key.import_text(name);kk.append(key)
                hud.call_method('Event Request Show Tutorial UI',(kk,u.load_asset('/Game/Constellation/UI/Art/Tutorial_'+texture)))
            s.update(phase=2,at=now)
        elif s['phase']==2 and now-s['at']>1:
            snap(w,'four real HUD requests')
            for director in u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer):director.stop_director()
            for x in widgets(w):x.remove_from_parent()
            pc.set_ignore_move_input(True)
            s['blocked']=u.TutorialToastEditorLibrary.create_toast_review(w,1,1)
            s.update(phase=3,at=now)
        elif s['phase']==3 and now-s['at']>2:
            s['rows'].append(dict(label='jump hint during blocked player input',still_in_viewport=s['blocked'].is_in_viewport()))
            assert s['blocked'].is_in_viewport(),'Hint expired while input was blocked'
            pc.reset_ignore_move_input()
            pc.reset_ignore_look_input()
            s.update(phase=4,at=now)
        elif s['phase']==4 and now-s['at']>.6:
            snap(w,'jump hint after input restoration')
            assert s['blocked'].is_in_viewport() and s['blocked'].get_render_opacity()>.9
            s.update(phase=5,at=now)
        elif s['phase']==5 and now-s['at']>2:
            assert not s['blocked'].is_in_viewport(),'Hint failed to expire after visible hold time'
            s['rows'].append(dict(label='visible hint expires normally',passed=True))
            finish()
    except Exception:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
u.CarryEditorLibrary.start_carry_review_play()
