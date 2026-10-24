"""Run only in the isolated review editor. Never saves maps or unrelated assets."""
import unreal as u, time, json, traceback
from pathlib import Path
P=Path(__file__).parent
O=P/("Runtime_"+time.strftime("%Y%m%d_%H%M%S"));O.mkdir(exist_ok=False)
assert "PhoneMenu/TestProject03" in Path(u.Paths.project_dir()).as_posix()
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
                u.SystemLibrary.quit_editor()
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
            comp.set_editor_properties({"camera_local":u.Vector(5,-28,42),"camera_rotation":u.Rotator(pitch=-45,yaw=80,roll=0)})
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
            assert action,"Esc mapping was not installed"
            u.WidgetLibrary.set_focus_to_game_viewport()
            assert u.CarryEditorLibrary.inject_carry_review_input(action.get_path_name(),u.Vector(1,0,0))
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
                u.CarryEditorLibrary.inject_carry_review_input(action.get_path_name(),u.Vector(1,0,0))
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
            assert u.get_default_object(u.SlateInspectorToolset).call_method("PressKey",("Escape",))
            S.update(phase="closing",at=now)
        elif S["phase"]=="hold" and S["cycles"]==0 and now-S["at"]>.25 and not S.get("selected"):
            inspector=u.get_default_object(u.SlateInspectorToolset)
            assert inspector.call_method("PressKey",("Enter",))
            S.update(selected="pending",selected_at=now)
        elif S["phase"]=="hold" and S.get("selected")=="pending" and now-S["selected_at"]>.2:
            inspector=u.get_default_object(u.SlateInspectorToolset)
            tree=inspector.call_method("Snapshot",("",60,False))
            (O/"menu-ui.txt").write_text(tree,encoding="utf-8")
            assert "메뉴 01 선택됨" in tree,"Placeholder button did not receive Enter"
            assert inspector.call_method("PressKey",("Tab",))
            assert inspector.call_method("PressKey",("Enter",))
            S.update(selected="tab_pending",selected_at=now)
        elif S["phase"]=="hold" and S.get("selected")=="tab_pending" and now-S["selected_at"]>.2:
            tree=u.get_default_object(u.SlateInspectorToolset).call_method("Snapshot",("",60,False))
            (O/"menu-ui-tab.txt").write_text(tree,encoding="utf-8")
            assert "메뉴 02 선택됨" in tree,"Tab did not move to the second button"
            S["selected"]="verified";S["checks"].append("placeholder selections via Enter/Tab/Enter")
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


