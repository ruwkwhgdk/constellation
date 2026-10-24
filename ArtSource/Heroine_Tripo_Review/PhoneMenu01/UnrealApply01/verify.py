import unreal as u, json, math
from pathlib import Path
P=Path(__file__).parent
d=json.loads((P/"motion.json").read_text())
B="/Game/Constellation/Characters/Heroine/GamePilot"
mesh=u.load_asset(B+"/SK_Heroine_GamePilot")
worst=0.;angle=0.;count=0
for name,(start,end) in d["clips"].items():
    a=u.load_asset(B+"/Phone/AS_Phone_"+name)
    m=u.load_asset(B+"/Phone/AM_Phone_"+name)
    assert a and m and a.get_skeleton()==mesh.skeleton
    assert abs(a.get_play_length()-(end-start)/30)<1e-5
    for f,row in enumerate(d["rows"][start-1:end]):
        pose=u.AnimPoseExtensions.get_anim_pose_at_frame(a,f,u.AnimPoseEvaluationOptions(should_retarget=False))
        for n,v in row.items():
            tr=u.AnimPoseExtensions.get_bone_pose(pose,n,u.AnimPoseSpaces.WORLD)
            t=tr.translation;q=tr.rotation
            worst=max(worst,math.dist([t.x,t.y,t.z],v["t"]))
            actual=[q.x,q.y,q.z,q.w];expected=v["q"]
            dot=abs(sum(x*y for x,y in zip(actual,expected)))/math.sqrt(sum(x*x for x in actual)*sum(x*x for x in expected))
            angle=max(angle,math.degrees(2*math.acos(min(1.,dot))));count+=1
    tracks=m.get_editor_property("slot_anim_tracks")
    assert str(tracks[0].get_editor_property("slot_name"))=="DefaultSlot"
assert worst<.05 and angle<.1,(worst,angle)
(P/"verified.json").write_text(json.dumps({"transforms":count,"max_position_error_cm":worst,"max_rotation_error_degrees":angle,"saved_reload_verified":True,"runtime_verified":False},indent=2))
u.log("PHONE_RELOAD_VERIFIED")
