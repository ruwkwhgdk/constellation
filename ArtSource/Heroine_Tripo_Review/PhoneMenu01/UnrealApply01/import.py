"""Create separate phone assets; never replace the player's mesh or other motions."""
import unreal as u, json
from pathlib import Path
P = Path(__file__).parent
d = json.loads((P / "motion.json").read_text())
B = "/Game/Constellation/Characters/Heroine/GamePilot"
F = B + "/Phone"
L = u.EditorAssetLibrary
T = u.AssetToolsHelpers.get_asset_tools()
mesh = u.load_asset(B + "/SK_Heroine_GamePilot")
sk = mesh.skeleton

def mul(a, b):
    x,y,z,w = a; X,Y,Z,W = b
    return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def inv(q): return [-q[0],-q[1],-q[2],q[3]]
def local(v, p):
    t = mul(mul(inv(p["q"]), [*[a-b for a,b in zip(v["t"],p["t"])],0]),p["q"])[:3]
    return {"t":[a/b for a,b in zip(t,p["s"])],"q":mul(inv(p["q"]),v["q"]),"s":[a/b for a,b in zip(v["s"],p["s"])]}

report = []
for name, (start, end) in d["clips"].items():
    path = F + "/AS_Phone_" + name
    assert not L.does_asset_exist(path), "Refuse overwriting existing delivery: " + path
    a = L.duplicate_asset(B + "/AnimationBlueprint/GP_Idle", path)
    assert a
    u.AnimationLibrary.remove_all_animation_notify_tracks(a)
    for n in u.AnimationLibrary.get_animation_curve_names(a,u.RawCurveTrackTypes.RCT_FLOAT):
        u.AnimationLibrary.remove_curve(a,n,False)
    rows = d["rows"][start-1:end]
    co = a.get_editor_property("controller")
    co.open_bracket("Approved free Mixamo phone motion",False)
    co.set_frame_rate(u.FrameRate(numerator=30,denominator=1),False)
    co.set_number_of_frames(u.FrameNumber(value=len(rows)-1),False)
    for n,parent in d["parents"].items():
        poses = [local(row[n],row[parent]) if parent else row[n] for row in rows]
        assert co.set_bone_track_keys(n,[u.Vector(*v["t"]) for v in poses],[u.Quat(*v["q"]) for v in poses],[u.Vector(*v["s"]) for v in poses],False), n
    co.close_bracket(False)
    a.set_preview_skeletal_mesh(mesh)
    a.set_editor_property("enable_root_motion",False)
    a.set_editor_property("force_root_lock",False)
    a.set_editor_property("rate_scale",1.)
    assert L.save_loaded_asset(a,False)
    fac = u.AnimMontageFactory()
    fac.target_skeleton = sk; fac.source_animation = a
    m = T.create_asset("AM_Phone_"+name,F,u.AnimMontage,fac)
    assert m
    tracks = m.get_editor_property("slot_anim_tracks")
    tr = tracks[0]; tr.set_editor_property("slot_name","DefaultSlot")
    at = tr.get_editor_property("anim_track"); segs = at.get_editor_property("anim_segments")
    sg = segs[0]
    for k,v in {"anim_reference":a,"anim_start_time":0.,"anim_end_time":a.get_play_length(),"anim_play_rate":1.}.items():
        sg.set_editor_property(k,v)
    segs[0]=sg; at.set_editor_property("anim_segments",segs)
    tr.set_editor_property("anim_track",at); tracks[0]=tr
    m.set_editor_property("slot_anim_tracks",tracks)
    for prop in ["blend_in","blend_out"]:
        bl=m.get_editor_property(prop);bl.set_editor_property("blend_time",.15);m.set_editor_property(prop,bl)
    m.set_editor_property("enable_auto_blend_out",False)
    m.set_preview_skeletal_mesh(mesh)
    assert L.save_loaded_asset(m,False)
    report.append({"sequence":a.get_path_name(),"montage":m.get_path_name(),"length":a.get_play_length(),"frames":[start,end]})
(P/"imported.json").write_text(json.dumps(report,indent=2))
u.log("PHONE_IMPORT_COMPLETE")
