"""Independent art candidate. Does not import into UE or modify the playable map."""
import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ArtSource/SchoolOpening/WetFloor/WallBreakCandidate"
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / "WallBreak.blend").exists(), "Preserve earlier review."
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"

def material(name, color, roughness, bump):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    bs = n.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = roughness
    tex = n.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 19
    tex.inputs["Detail"].default_value = 3
    b = n.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = .35
    b.inputs["Distance"].default_value = bump
    m.node_tree.links.new(tex.outputs["Fac"], b.inputs["Height"])
    m.node_tree.links.new(b.outputs["Normal"], bs.inputs["Normal"])
    return m

rock = material("Review_CoolFracturedStone", (.105, .14, .145), .82, .035)
plaster = material("Review_AgedSchoolPlaster", (.42, .39, .32), .9, .009)
core = material("Review_PlasterBrokenCore", (.23, .205, .155), .95, .018)
report = []

def prism(name, polygon, front, back, mat, bevel=0):
    # X/Z outline, Y depth; closed, deliberate angular fracture silhouette.
    count = len(polygon)
    verts = [(x, front, z) for x, z in polygon] + [(x, back, z) for x, z in polygon]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces += [(i, (i+1) % count, (i+1) % count + count, i+count) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    bpy.context.view_layer.objects.active = obj
    if bevel:
        mod = obj.modifiers.new("Small fractured edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    uv = mesh.uv_layers.new(name="MetreUV")
    for p in mesh.polygons:
        axis = max(range(3), key=lambda i: abs(p.normal[i]))
        for li in p.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (co.y, co.z) if axis == 0 else ((co.x, co.z) if axis == 1 else (co.x, co.y))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    mesh.calc_loop_triangles()
    row = dict(name=name, triangles=len(mesh.loop_triangles),
               nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),
               signed_volume_m3=bm.calc_volume(signed=True))
    bm.free()
    assert row["nonmanifold_edges"] == 0 and row["signed_volume_m3"] > 0
    report.append(row)
    return obj

# Layered diagonal fracture planes. No cylindrical/radial deformation or scattered rocks.
outlines = [
    [(-.78,0),(.82,0),(.70,.55),(.94,.83),(.55,1.15),(-.65,.88),(-.9,.42)],
    [(-.65,.9),(.55,1.17),(.86,1.5),(.62,1.88),(-.45,1.67),(-.84,1.29)],
    [(-.45,1.69),(.61,1.9),(.75,2.34),(.48,2.62),(-.68,2.35),(-.78,1.98)],
    [(-.68,2.37),(.48,2.64),(.62,3.04),(.34,3.39),(-.53,3.18),(-.85,2.8)],
    [(-.53,3.2),(.34,3.41),(.57,3.8),(.3,4.15),(-.67,4.02),(-.8,3.6)],
]
parts = [prism("RockStratum_%02d" % i, p, -.14-(i%3)*.045, .18, rock, .012)
         for i, p in enumerate(outlines)]
# Plaster lips stay close to the original wall plane. Jagged edges reveal masonry core.
left = [(-1.35,0),(-.74,0),(-.89,.42),(-.66,.85),(-.84,1.24),
        (-.46,1.7),(-.8,1.96),(-.68,2.38),(-.86,2.8),(-.55,3.2),
        (-.81,3.6),(-.68,4.05),(-1.35,4.2)]
right = [( .86,0),(1.35,0),(1.35,4.2),(.3,4.15),(.58,3.78),
         (.34,3.4),(.64,3.03),(.48,2.63),(.77,2.32),(.63,1.89),
         (.87,1.49),(.56,1.16),(.96,.82),(.72,.54)]
for name, polygon in [("LeftLip", left), ("RightLip", right)]:
    parts.append(prism(name+"_Core", polygon, -.105, .24, core))
    parts.append(prism(name+"_Finish", polygon, -.12, -.104, plaster))

bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/"SM_S0_WallBreak_Candidate.fbx"),
                         use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                         axis_forward="-Y", axis_up="Z", add_leaf_bones=False)
bpy.ops.object.camera_add(location=(4,-9,4.3))
camera = bpy.context.object
camera.rotation_euler = (Vector((0,0,2))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 5.4
scene.camera = camera
for location, energy, size in [((-3,-4,6),750,4),((3,-2,3),240,3)]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector((0,0,2))-light.location).to_track_quat("-Z","Y").to_euler()
scene.world.color = (.08,.08,.08)
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.filepath = str(OUT/"BlenderPreview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"WallBreak.blend"))
(OUT/"audit.json").write_text(json.dumps(dict(status="candidate_not_applied",
    units="metres", parts=report, collision="Not assigned; decorative candidate only",
    unreal_verified=False), indent=2))
bpy.ops.render.render(write_still=True)
