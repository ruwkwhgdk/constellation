"""Verify the freshly built base DLL in the original project; never saves review maps."""
import unreal as u, time, json, traceback
from pathlib import Path
P=Path(__file__).parent
O=P/("BaseRuntime_"+time.strftime("%Y%m%d_%H%M%S"));O.mkdir(exist_ok=False)
assert Path(u.Paths.project_dir()).resolve()==Path("C:/Users/User/Documents/UnrealProjects/Constellation").resolve()
u.EditorLoadingAndSavingUtils.new_blank_map(False)
E=u.get_editor_subsystem(u.UnrealEditorSubsystem)
L=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
floor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-50))
floor.static_mesh_component.set_static_mesh(u.load_asset("/Engine/BasicShapes/Cube"))
floor.set_actor_scale3d(u.Vector(100,100,1))
actors.spawn_actor_from_class(u.PlayerStart,u.Vector(0,0,100))
sun=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,600),u.Rotator(pitch=-45,yaw=-40))
sun.light_component.set_intensity(4)
actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,300))
S=dict(start=time.monotonic(),phase="boot",cycles=0,checks=[],last_capture=0)
def finish(error=""):
    (O/"result.json").write_text(json.dumps(dict(error=error,cycles=S["cycles"],checks=S["checks"]),indent=2))
    S.update(phase="finish",at=time.monotonic())
    L.editor_request_end_play()
    if error:
        u.unregister_slate_post_tick_callback(handle)
def tick(dt):
    try:
        now=time.monotonic()
        if S["phase"]=="finish":
            if now-S["at"]>3:
                u.unregister_slate_post_tick_callback(handle)
                u.EditorLoadingAndSavingUtils.load_map("/Game/Constellation/Review/LittleGirl_v03/L_LittleGirl_v03_Review")
            return
        if now-S["start"]>180:raise RuntimeError("Timeout: "+S["phase"])
        w=E.get_game_world()
        if not w:return
        pc=u.GameplayStatics.get_player_controller(w,0)
        pawn=u.GameplayStatics.get_player_character(w,0)
        if not pc or not pawn:return
        comp=pawn.get_component_by_class(u.PhoneMenuComponent)
        if not comp:raise RuntimeError("Saved player has no phone component: "+pawn.get_class().get_path_name())
        if S["phase"]=="boot":
            if now-S["start"]<8:return
            S.update(phase="open",at=now,view=pc.get_view_target(),move=pc.is_move_input_ignored(),look=pc.is_look_input_ignored(),cursor=pc.get_editor_property("show_mouse_cursor"))
            u.SystemLibrary.execute_console_command(pawn,"t.MaxFPS 30")
            u.WidgetLibrary.set_focus_to_game_viewport()
            assert comp.get_editor_property("camera_local")==u.Vector(30,-25,35)
            diag={}
            for obj,names in [(comp,["camera_rotation","camera_local","animation_approved","gameplay_allows_menu","approved_phone_track","draw_montage","hold_montage","stow_montage","hand_socket"]),(pawn,["bIsBattleOn","bIsJumping","IsAttacking","IsPushing","IsClimbing","IsActiveSlime"]),(pc,["cinematic_mode"])]:
                for name in names:
                    try:diag[name]=str(obj.get_editor_property(name))
                    except Exception as error:diag[name]=str(error)
            diag["locks"]=[pc.is_move_input_ignored(),pc.is_look_input_ignored()]
            diag["static_meshes"]=[str((a.get_name(),a.is_visible(),a.get_editor_property("hidden_in_game"))) for a in pawn.get_components_by_class(u.StaticMeshComponent)]
            (O/"gates.json").write_text(json.dumps(diag,indent=2))
        if S["phase"]=="open":
            if now-S["at"]<.5:return
            action=next((a for a in u.ObjectIterator(u.InputAction) if a.get_outer()==comp),None)
            assert action,"Menu mapping was not installed"
            u.WidgetLibrary.set_focus_to_game_viewport()
            assert u.get_default_object(u.SlateInspectorToolset).call_method("PressKey",("Tilde",))
            S.update(phase="opening",at=now)
            return
        if S["cycles"]==0 and now-S["last_capture"]>1:
            S["last_capture"]=now
            u.CarryEditorLibrary.capture_carry_review(str(O/("frame_%04d.png"%int(S.get("frame",0)))),True)
            S["frame"]=S.get("frame",0)+1
        if S["phase"]=="opening":
            with (O/"trace.txt").open("a") as f:f.write(str((now-S["at"],comp.blocks_gameplay(),u.GameplayStatics.is_game_paused(w),str(pawn.mesh.get_anim_instance().get_current_active_montage())))+"\n")
        if S["phase"]=="opening":
            if now-S["at"]<2 and not comp.blocks_gameplay() and now-S.get("retry_at",0)>.3:
                action=next((a for a in u.ObjectIterator(u.InputAction) if a.get_outer()==comp),None)
                u.get_default_object(u.SlateInspectorToolset).call_method("PressKey",("Tilde",))
                S["retry_at"]=now
            if u.GameplayStatics.is_game_paused(w):
                assert comp.blocks_gameplay() and pc.is_move_input_ignored() and pc.is_look_input_ignored()
                assert pc.get_view_target()!=S["view"]
                assert pc.get_editor_property("show_mouse_cursor")
                phone=next((a for a in pawn.get_components_by_class(u.StaticMeshComponent) if a.static_mesh==u.load_asset("/Engine/BasicShapes/Cube")),None)
                assert phone and phone.is_visible()
                (O/"positions.txt").write_text(str({"configured_rotation":comp.get_editor_property("camera_rotation"),"pawn":pawn.get_actor_transform(),"phone":phone.get_world_transform(),"view":pc.get_view_target().get_actor_transform(),"hand":pawn.mesh.get_socket_transform("hand_r")}))
                u.CarryEditorLibrary.capture_carry_review(str(O/"menu-open.png"),True)
                if S["cycles"]==0:u.get_default_object(u.SlateInspectorToolset).call_method("Observe",("",60))
                S.update(phase="hold",at=now)
            elif now-S["at"]>7:
                raise RuntimeError("Menu failed to open; blocks="+str(comp.blocks_gameplay())+" grounded="+str(pawn.character_movement.is_moving_on_ground()))
        elif S["phase"]=="hold" and now-S["at"]>.8 and (S["cycles"]>0 or S.get("selected")=="verified"):
            assert u.get_default_object(u.SlateInspectorToolset).call_method("PressKey",("Tilde",))
            S.update(phase="closing",at=now)
        elif S["phase"]=="hold" and S["cycles"]==0 and now-S["at"]>.25 and not S.get("selected"):
            inspector=u.get_default_object(u.SlateInspectorToolset)
            assert inspector.call_method("PressKey",("Enter",))
            S.update(selected="pending",selected_at=now)
        elif S["phase"]=="hold" and S.get("selected")=="pending" and now-S["selected_at"]>.2:
            inspector=u.get_default_object(u.SlateInspectorToolset)
            tree=inspector.call_method("Snapshot",("",60,True))
            (O/"menu-ui.txt").write_text(tree,encoding="utf-8")
            assert "메뉴 01 선택됨" in tree,"Placeholder button did not receive Enter"
            assert inspector.call_method("PressKey",("Tab",))
            S.update(selected="tab_focus_pending",selected_at=now)
        elif S["phase"]=="hold" and S.get("selected")=="tab_focus_pending" and now-S["selected_at"]>.3:
            assert u.get_default_object(u.SlateInspectorToolset).call_method("PressKey",("Enter",))
            S.update(selected="tab_pending",selected_at=now)
        elif S["phase"]=="hold" and S.get("selected")=="tab_pending" and now-S["selected_at"]>.2:
            tree=u.get_default_object(u.SlateInspectorToolset).call_method("Snapshot",("",60,True))
            (O/"menu-ui-tab.txt").write_text(tree,encoding="utf-8")
            assert "메뉴 02 선택됨" in tree,"Tab did not move to the second button"
            S["selected"]="verified";S["checks"].append("backtick key opening and closing; placeholder selections via Enter/Tab/Enter")
        elif S["phase"]=="closing" and not comp.blocks_gameplay():
            assert not u.GameplayStatics.is_game_paused(w)
            assert pc.is_move_input_ignored()==S["move"] and pc.is_look_input_ignored()==S["look"]
            assert pc.get_view_target()==S["view"]
            assert pc.get_editor_property("show_mouse_cursor")==S["cursor"]
            S["cycles"]+=1;S["checks"].append("open/pause/phone/camera/close/input-restored "+str(S["cycles"]))
            if S["cycles"]==10:finish()
            else:S.update(phase="open",at=now)
    except Exception:finish(traceback.format_exc())
u.EditorPythonScripting.set_keep_python_script_alive(True)
handle=u.register_slate_post_tick_callback(tick)
L.editor_request_begin_play()


