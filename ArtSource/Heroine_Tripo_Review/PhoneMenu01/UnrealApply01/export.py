"""Export approved saved motion through the established GamePilot coordinate map."""
import bpy, json, numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

P = Path(__file__).parent
source = P.parent / "OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend"
bpy.ops.wm.open_mainfile(filepath=str(source))
s = bpy.context.scene
r = bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
cube = bpy.data.objects["Phone_Portrait_ReviewCube"]
Q = Path("C:/Users/User/Documents/Constellation_ArtWorkspace/ArtSource/Heroine_Rebuild/GamePilot/Revision01")
ref = json.loads((Q / "motion_delivery_dump.json").read_text())["reference"]
fit = np.array(json.loads((Q / "geometry_info.json").read_text())["fit"])
ar = np.eye(4)
ar[:3] = fit.T
A = Matrix(ar.tolist())
Ai = A.inverted()
idle = Path("C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/GateOpen01/Sync04/idle.json")

def unpack(v):
    q = v["q"]
    m = Quaternion((q[3], *q[:3])).to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= v["s"][j]
    m.translation = Vector(v["t"])
    return m

def pack(m):
    t, q, z = m.decompose()
    return {"t": list(t), "q": [q.x, q.y, q.z, q.w], "s": list(z)}

rest = {b.name: b.matrix_local.copy() for b in r.data.bones}
rows, props = [], []
for f in range(1, 286):
    s.frame_set(f)
    row = {b.name: A @ b.matrix @ rest[b.name].inverted() @ Ai @ unpack(ref[b.name]) for b in r.pose.bones}
    if f == 1:
        shift = row["pelvis"].translation - Vector(json.loads(idle.read_text())["world"]["pelvis"]["t"])
        shift.z = 0
    for n in row:
        if n != "root":
            row[n].translation -= shift
    # A has a reflection; use a second reflection on the symmetric cube's local X
    # to retain a proper rotation while matching its actual surface in the preview.
    world = A @ r.matrix_world.inverted() @ cube.matrix_world @ Matrix.Diagonal((-1, 1, 1, 1))
    world.translation -= shift
    relative = row["hand_r"].inverted() @ world
    props.append(pack(relative))
    rows.append({n: pack(m) for n, m in row.items()})

result = {
    "source": str(source), "fps": 30,
    "parents": {b.name: b.parent.name if b.parent else None for b in r.data.bones},
    "clips": {"Draw": [1, 73], "Hold": [73, 207], "Stow": [207, 285]},
    "rows": rows, "prop_relative_hand_r": props,
    "cube_dimensions_m": list(cube.dimensions),
    "visible_frames": [31, 245],
    "approval": "User approved proceeding with known minor hand/phone alignment error.",
}
(P / "motion.json").write_text(json.dumps(result), encoding="utf-8")
print("PHONE_EXPORT_COMPLETE", len(rows), len(rows[0]), cube.dimensions[:])
