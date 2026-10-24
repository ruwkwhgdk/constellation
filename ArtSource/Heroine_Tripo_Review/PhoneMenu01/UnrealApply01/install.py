import unreal as u, json, shutil, hashlib
from pathlib import Path
P = Path(__file__).parent
root = P.parents[3]
d = json.loads((P/"motion.json").read_text())
path = "/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine"
disk = root/("Content/"+path.removeprefix("/Game/")+".uasset")
backup = P/"BP_Player_Heroine.before.uasset"
if backup.exists():
    assert hashlib.sha256(backup.read_bytes()).digest()==hashlib.sha256(disk.read_bytes()).digest(), "Original changed since backup; inspect before retry"
else:
    shutil.copy2(disk,backup)
bp = u.load_asset(path)
before = u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
(P/"before-graph.txt").write_text(before,encoding="utf-8")
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
handles=sub.k2_gather_subobject_data_for_blueprint(bp)
objects=[fn.get_object_for_blueprint(fn.get_data(h),bp) for h in handles]
assert not any(isinstance(o,u.PhoneMenuComponent) for o in objects)
handle,reason=sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=handles[0],new_class=u.PhoneMenuComponent,blueprint_context=bp))
assert fn.is_handle_valid(handle),str(reason)
assert sub.rename_subobject(handle,"PhoneMenu")
comp=fn.get_object_for_blueprint(fn.get_data(handle),bp)
for k,v in {
    "animation_approved":True,
    "gameplay_allows_menu":True,
    "hand_socket":"hand_r",
    "camera_local":u.Vector(7,-15,47),
    "camera_rotation":u.Rotator(pitch=-57,yaw=28,roll=0),
    "camera_fov":65.,
}.items():
    comp.set_editor_property(k,v)
for name in d["clips"]:
    comp.set_editor_property(name.lower()+"_montage",u.load_asset("/Game/Constellation/Characters/Heroine/GamePilot/Phone/AM_Phone_"+name))
track=[]
for v in d["prop_relative_hand_r"]:
    tr=u.Transform()
    tr.translation=u.Vector(*v["t"])
    tr.rotation=u.Quat(*v["q"])
    tr.scale3d=u.Vector(*[s*dim/100 for s,dim in zip(v["s"],d["cube_dimensions_m"])])
    track.append(tr)
comp.set_editor_property("approved_phone_track",track)
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
(P/"installed.json").write_text(json.dumps({"blueprint":path,"component":comp.get_path_name(),"phone_frames":len(track),"accepted_alignment_issue":True},indent=2))
u.log("PHONE_INSTALLED")
