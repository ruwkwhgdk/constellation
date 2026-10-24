"""User-approved camera/QTE blockout. No asset/map saves or item grants."""
import unreal as u, json, time, traceback, hashlib
from pathlib import Path
R=Path(u.Paths.project_dir()); O=R/'Saved/SwordAcquisition/EnginePreview09';O.mkdir(parents=True,exist_ok=True)
MAP=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
before=hashlib.sha256(MAP.read_bytes()).hexdigest()
def prop(obj,**kw):
    for k,v in kw.items():obj.set_editor_property(k,v)
    return obj
def pose(loc,target):
    v=u.Vector(*loc);return u.Transform(location=v,rotation=u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)))
S={'start':time.monotonic(),'phase':'startup','frames':[]}
def finish(error=None):
    if error:(O/'error.txt').write_text(error,encoding='utf8')
    (O/'recording.json').write_text(json.dumps(S['frames']),encoding='utf8')
    (O/'result.json').write_text(json.dumps({'error':error,'map_unchanged':before==hashlib.sha256(MAP.read_bytes()).hexdigest(),'qte':S.get('qte_result'),'frames':len(S['frames']),'animation':'not integrated; idle placeholder','inventory':'not granted; presentation placeholder','normal_interaction_tested':False,'qte_physical_input_tested':False,'qte_outcome_injected_for_review':True},indent=2),encoding='utf8')
    if 'handle' in globals():u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.quit_editor()
try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
    A=u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in list(A.get_all_level_actors()):
        if isinstance(a,u.SceneEventBinding):a.set_editor_property('enabled',False)
        if isinstance(a,u.SchoolOpeningSceneActor):A.destroy_actor(a)
        if isinstance(a,u.PlayerStart):a.set_actor_location(u.Vector(-10810,0,1030),False,True);a.set_actor_rotation(u.Rotator(yaw=180),False)
    graph=u.new_object(u.SceneDirectorAsset)
    graph.set_editor_property('dialogue_character_interval',.015)
    views={'A':pose((-10490,-350,1190),(-10865,0,1050)),
           'B':pose((-11160,-310,1125),(-10865,0,1040)),
           'C':pose((-11170,-360,1090),(-10845,0,1130))}
    graph.set_editor_property('cameras',[prop(u.DirectorCameraEntry(),key=k,transform=v,field_of_view=48.) for k,v in views.items()])
    N=u.DirectorNodeType; steps=[]
    def node(kind,**kw):
        s=u.SceneDirectorLibrary.make_director_step(kind);prop(s,duration=.1,editor_position=u.Vector2D(len(steps)*250,0),**kw);steps.append(s);return s
    def wait(t):
        s=u.SceneDirectorLibrary.make_director_step(N.WAIT);prop(s,duration=t,editor_position=u.Vector2D(len(steps)*250,0));steps.append(s);return s
    def say(text,t):
        s=u.SceneDirectorLibrary.make_director_step(N.DIALOGUE);prop(s,dialogue_text=text,dialogue_advance=u.DirectorDialogueAdvance.TIMED,duration=t,editor_position=u.Vector2D(len(steps)*250,0));steps.append(s);return s
    def shot(k):
        s=node(N.CAMERA_SWITCH,camera_key=k,blend_seconds=.6,wait_for_completion=False);s.set_editor_property('duration',{'A':3.,'B':6.,'C':12.}[k]);return s
    node(N.START);node(N.INPUT_LOCK,lock_input=True);node(N.HUD_HIDDEN,hide_hud=True)
    shot('A');say('검 획득 · 임시 엔진 시안\n카메라 / QTE 검수 · 애니메이션 미연결',3.)
    shot('B');say('양손 그립 → 힘주어 버티기\n[승인 애니메이션 전달 대기]',3.);node(N.CLOSE_DIALOGUE)
    q=node(N.QTE,qte=prop(u.DirectorQTESettings(),type=u.DirectorQTEType.DIRECTION_DRAG,timed=False,drag_direction=u.Vector2D(0,-1),drag_distance=160.,screen_position=u.Vector2D(.78,.72),scene_policy=u.DirectorQTEScenePolicy.HOLD))
    after=say('QTE 성공 → 검 뽑기 → 균형 회복\n[동작 미연결 · 검은 원위치 유지]',3.)
    shot('C');say('한 손으로 높이 들기 → 자세 유지\n[검 끝 여백 / 획득 UI 자리 검수]',3.)
    say('아이템 획득 UI 표시 구간\n[실제 아이템 지급 / UI 연결 예정]',4.)
    say('검 내리기\n[승인 애니메이션 전달 대기]',2.)
    say('녹슨 검을 얻었습니다.',3.);node(N.CLOSE_DIALOGUE)
    node(N.CAMERA_RETURN);node(N.INPUT_LOCK,lock_input=False);node(N.HUD_HIDDEN,hide_hud=False);node(N.END)
    for a,b in zip(steps,steps[1:]):a.set_editor_property('next_nodes',[b.id])
    q.set_editor_property('next_nodes',[]);q.set_editor_property('choice_targets',{u.Name('Success'):after.id,u.Name('Failure'):after.id})
    graph.set_editor_property('steps',steps)
    result=u.SceneDirectorLibrary.compile_director(graph)
    (O/'graph.txt').write_text(str(result)+'\n'+str([(str(s.get_editor_property('type')),str(s.id)) for s in steps]),encoding='utf8')
    assert not graph.get_editor_property('needs_compile'),str(result)
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    editor_runner=A.spawn_actor_from_class(u.SceneDirectorPlayer,u.Vector())
    prop(editor_runner,auto_play=False,director=graph)
    editor_runner.set_actor_label('SwordPreviewRunner')
    u.CarryEditorLibrary.start_carry_review_play()
except:finish(traceback.format_exc());raise
def tick(dt):
    try:
        now=time.monotonic()
        if now-S['start']>240:raise RuntimeError('Preview timeout')
        pawn=u.CarryEditorLibrary.get_carry_review_pawn()
        if not pawn:return
        w=pawn.get_world();pc=u.GameplayStatics.get_player_controller(w,0)
        if S['phase']=='startup':
            if now-S['start']<12:return
            pawn.set_actor_location(u.Vector(-10810,0,1030),False,True);pawn.set_actor_rotation(u.Rotator(yaw=180),False)
            pc.set_control_rotation(u.Rotator(pitch=-10,yaw=180))
            for a in u.GameplayStatics.get_all_actors_of_class(w,u.Actor):
                if a.get_name()=='BP_Sword_Stuck_At_Ground_C_1':
                    for c in a.get_components_by_class(u.StaticMeshComponent):
                        if c.static_mesh and 'Star_Object' in c.static_mesh.get_path_name():c.set_visibility(False,True)
                    a.set_actor_enable_collision(False)
            S.update(phase='settle',ready=now);return
        if S['phase']=='settle':
            if now-S['ready']<4:return
            u.SystemLibrary.execute_console_command(w,'SceneDirector.SkipCinematics 0')
            u.SystemLibrary.execute_console_command(w,'DisableAllScreenMessages')
            runner=next(a for a in u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer) if a.get_name()==editor_runner.get_name())
            prop(runner,auto_play=False,director=graph)
            foot=pawn.get_actor_location().z-pawn.get_component_by_class(u.CapsuleComponent).get_scaled_capsule_half_height()
            adjusted={'A':pose((-10490,-350,foot+220),(-10865,0,foot+85)),'B':pose((-11160,-310,foot+170),(-10865,0,foot+85)),'C':pose((-11170,-360,foot+160),(-10845,0,foot+150))}
            graph.set_editor_property('cameras',[prop(u.DirectorCameraEntry(),key=k,transform=v,field_of_view=48.) for k,v in adjusted.items()])
            u.SceneDirectorLibrary.compile_director(graph)
            (O/'placement.json').write_text(json.dumps({'foot':foot,'pawn':str(pawn.get_actor_location())}))
            assert runner.play_director(),str(runner.last_error)
            S.update(phase='running',runner=runner,run_start=now,last_capture=0)
        runner=S['runner']
        control=O/'control.py'
        if control.exists():
            code=control.read_text(encoding='utf8');control.rename(O/('executed-'+str(time.time_ns())+'.py'));exec(code,globals(),locals())
        if runner.is_waiting_for_qte():
            if 'qte_started' not in S:S['qte_started']=now;(O/'qte-ready.txt').write_text('Background review: simulated outcome after hold; physical input not tested')
            if now-S['qte_started']>4:
                assert u.SceneDirectorLibrary.resolve_qte_for_review(runner,True),'Review result injection failed'
        elif 'qte_started' in S:S['qte_result']=str(runner.get_last_qte_outcome())
        if now-S['last_capture']>=.1:
            i=len(S['frames']);u.CarryEditorLibrary.capture_carry_review(str(O/('frame-%05d.png'%i)),True);ok=True
            if ok:S['frames'].append({'t':now-S['run_start'],'game':u.GameplayStatics.get_time_seconds(w),'ui':runner.is_waiting_for_qte(),'dialogue':str(runner.current_dialogue)})
            S['last_capture']=now
            if i%10==0:
                (O/'live-status.json').write_text(json.dumps({'qte':runner.is_waiting_for_qte(),'outcome':str(runner.get_last_qte_outcome()),'dialogue':str(runner.current_dialogue)}),encoding='utf8')
                (O/'recording.json').write_text(json.dumps(S['frames']),encoding='utf8')
        if not runner.is_director_playing() and now-S['run_start']>2:
            assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Input restoration failed'
            finish()
    except:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)












