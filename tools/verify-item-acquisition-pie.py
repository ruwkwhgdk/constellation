"""Test-owned PIE only: real chest sprite; text is explicitly QA-only, no grants."""
import unreal as u
import time,json,traceback
from pathlib import Path
from datetime import datetime
root=Path(u.Paths.project_dir())
assert 'ItemAcquisition/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
out=root/'Saved/ItemAcquisition'/('review-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
out.mkdir(parents=True)
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
state=dict(start=time.monotonic(),phase=0)
def finish(error=''):
    results=u.ItemAcquisitionReviewLibrary.review_results()
    (out/'result.json').write_text(json.dumps(dict(success=not error,error=error,results=results),ensure_ascii=False,indent=2),encoding='utf8')
    u.unregister_slate_post_tick_callback(handle)
    level.editor_request_end_play()
    u.SystemLibrary.quit_editor()
def shot(world,name):
    u.SystemLibrary.execute_console_command(world,'Shot showui filename='+(out/name).as_posix())
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>150: raise RuntimeError('PIE review timed out: '+str(state))
        world=editor.get_game_world()
        if not world or u.GameplayStatics.get_time_seconds(world)<3:return
        pc=u.GameplayStatics.get_player_controller(world,0)
        sub=next(o for o in u.ObjectIterator(u.ItemAcquisitionSubsystem) if o.get_outer()==world)
        if state['phase']==0:
            for a in u.GameplayStatics.get_all_actors_of_class(world,u.SchoolOpeningSceneActor):a.call_method('DirectorStopped',(False,))
            for w in u.ObjectIterator(u.UserWidget):
                if w.is_in_viewport() and w.get_class().get_name() in ('WBP_Fade_C','WBP_Tutorial_C'):w.remove_from_parent()
            pc.player_camera_manager.stop_camera_fade()
            state['cursor']=pc.get_editor_property('show_mouse_cursor')
            state['move']=pc.is_move_input_ignored()
            state['look']=pc.is_look_input_ignored()
            currency=next(o for o in u.ObjectIterator(u.CurrencySubsystem) if o.get_outer()==u.GameplayStatics.get_game_instance(world))
            state['currency']=currency
            state['balances']=[currency.get_gold(),currency.get_star_coin(),currency.get_dummy_item_count()]
            tex=u.load_asset('/Game/Constellation/UI/Art/coin_icon')
            u.ItemAcquisitionReviewLibrary.show_review_card(world,tex,'UI 표시 검증','실제 상자 이미지를 사용한 검증 화면입니다.\n표시 전용이며 아이템을 지급하지 않습니다.',1)
            u.ItemAcquisitionReviewLibrary.show_review_card(world,tex,'순차 표시 검증','긴 한글 설명의 줄바꿈과 스크롤을 확인합니다. '+('이 문장은 표시 기능을 검사하기 위한 테스트 문장입니다. '*35),2)
            state.update(phase=1,at=now)
        elif state['phase']==1 and sub.is_presenting():
            state['key']=sub.current_confirm_key()
            u.ItemAcquisitionReviewLibrary.send_review_key(state['key'],True)
            state.update(phase=2,at=now)
        elif state['phase']==2 and now-state['at']>1.2:
            assert sub.get_pending_count()==2,'Early held interaction dismissed card'
            shot(world,'card-normal')
            u.ItemAcquisitionReviewLibrary.send_review_key(state['key'],False)
            state.update(phase=3,at=now)
        elif state['phase']==3 and now-state['at']>.4:
            u.ItemAcquisitionReviewLibrary.send_review_key(state['key'],True)
            u.ItemAcquisitionReviewLibrary.send_review_key(state['key'],False)
            state.update(phase=4,at=now)
        elif state['phase']==4 and now-state['at']>1.2:
            assert sub.get_pending_count()==1,'First card did not confirm or queue collapsed'
            shot(world,'card-long-korean')
            state.update(phase=40,at=now)
        elif state['phase']==40 and now-state['at']>.5:
            scrollkey=u.Key()
            scrollkey.set_editor_property('key_name','PageDown')
            u.ItemAcquisitionReviewLibrary.send_review_key(scrollkey,True)
            u.ItemAcquisitionReviewLibrary.send_review_key(scrollkey,False)
            state.update(phase=5,at=now)
        elif state['phase']==5 and now-state['at']>.5:
            shot(world,'card-scrolled')
            state.update(phase=50,at=now)
        elif state['phase']==50 and now-state['at']>.5:
            sub.cancel_all()
            state.update(phase=6,at=now)
        elif state['phase']==6 and now-state['at']>.5:
            assert sub.get_pending_count()==0 and not sub.is_presenting()
            assert pc.is_move_input_ignored()==state['move']
            assert pc.is_look_input_ignored()==state['look']
            assert pc.get_editor_property('show_mouse_cursor')==state['cursor']
            c=state['currency']
            assert [c.get_gold(),c.get_star_coin(),c.get_dummy_item_count()]==state['balances'],'Presentation changed inventory'
            results=u.ItemAcquisitionReviewLibrary.review_results().splitlines()
            assert len(results)==2 and results[0].endswith(':confirmed') and results[1].endswith(':cancelled'),results
            finish()
    except Exception:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
play=u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'))
play.set_editor_property('NewWindowWidth',1920)
play.set_editor_property('NewWindowHeight',1080)
u.CarryEditorLibrary.start_carry_review_play()
