"""Source-only edit: original Mixamo samples and two 12-frame crossfades."""
import bpy, json
from pathlib import Path
from mathutils import Matrix

root = Path(__file__).parent
out = root / "OneHandSourceEdit01"
out.mkdir(exist_ok=False)
samples = {}
for label, stem in (("cell", "Talking_On_A_Cell_Phone"), ("text", "Texting")):
    bpy.ops.wm.open_mainfile(filepath=str(root / "FreeSources01" / stem / (stem + "_Raw.blend")))
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    samples[label] = {}
    for frame in range(1, scene.frame_end + 1):
        scene.frame_set(frame)
        samples[label][frame] = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}

# Texting is the last loaded file; the two downloads use the same X Bot rig.
rig.animation_data_clear()
rig.animation_data_create()
rig.animation_data.action = bpy.data.actions.new("Mixamo_OneHand_SourceEdit01")
timeline = []
timeline += [("cell", f, None, None, 0) for f in range(1, 61)]
timeline += [("cell", 61+i, "text", 35+i, (i+1)/12) for i in range(12)]
timeline += [("text", f, None, None, 0) for f in range(47, 181)]
timeline += [("text", 181+i, "cell", 1040+i, (i+1)/12) for i in range(12)]
timeline += [("cell", f, None, None, 0) for f in range(1052, 1119)]
previous = {}
for frame, (a, fa, b, fb, weight) in enumerate(timeline, 1):
    scene.frame_set(frame)
    for bone in rig.pose.bones:
        loc, rot, scale = samples[a][fa][bone.name].decompose()
        if b:
            loc2, rot2, scale2 = samples[b][fb][bone.name].decompose()
            loc, rot, scale = loc.lerp(loc2, weight), rot.slerp(rot2, weight), scale.lerp(scale2, weight)
        if bone.name in previous and rot.dot(previous[bone.name]) < 0:
            rot.negate()
        previous[bone.name] = rot.copy()
        bone.rotation_mode = "QUATERNION"
        bone.location, bone.rotation_quaternion, bone.scale = loc, rot, scale
        for channel in ("location", "rotation_quaternion", "scale"):
            bone.keyframe_insert(channel, frame=frame)
action = rig.animation_data.action
for layer in action.layers:
    for strip in layer.strips:
        for slot in action.slots:
            bag = strip.channelbag(slot)
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = "LINEAR"
scene.frame_start, scene.frame_end, scene.render.fps = 1, len(timeline), 30
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out / "Mixamo_OneHand_SourceEdit01.blend"))
(out / "source_frames.json").write_text(json.dumps({
    "status": "Review only; no Unreal import",
    "method": "Unmodified local source poses except two 12-frame quaternion crossfades; no authored draw/stow poses",
    "sources": {"cell": "Talking_On_A_Cell_Phone", "text": "Texting"},
    "timeline": [{"output": n, "source": a, "frame": fa, "blend_source": b, "blend_frame": fb, "weight": w}
                 for n, (a, fa, b, fb, w) in enumerate(timeline, 1)]
}, indent=2))
