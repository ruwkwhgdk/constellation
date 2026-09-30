# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\import_old_korean_building_a.py
"""OldKoreanBuildingA 모듈러 키트를 /Game/Constellation/Environments/KoreanBuildings/BuildingA 로 임포트한다.

언리얼 에디터 Python 콘솔에서:
    import import_old_korean_building_a
같은 세션에서 다시 돌릴 때 (모듈 캐시 때문에 재-import는 아무것도 안 함):
    import_old_korean_building_a.main()
레벨에 건물까지 조립하려면:
    import_old_korean_building_a.assemble()

임포트 설정의 핵심:
  - Auto Generate Collision = False. 이 키트는 UCX_ 충돌체를 FBX 안에 같이
    담고 있다. 언리얼이 자동으로 볼록 껍질을 씌우면 문/창 개구부가 막혀서
    플레이어가 상가 입구에서 튕겨나간다.
  - Generate Lightmap UVs = False. UV1을 이미 굽어서 내보냈다.
  - Import Materials = False. FBX가 실어오는 머티리얼 대신 여기서 UE
    머티리얼을 BaseColor/Normal/Roughness까지 직접 배선해 만든다.
"""
from resource_paths import loads as load_current_json, load as load_current_json_file

import json
import os
import unreal

# ---------------------------------------------------------------------------
SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA"
DEST = "/Game/Constellation/Environments/KoreanBuildings/BuildingA"
MESH_DIR = DEST + "/Meshes"
TEX_DIR = DEST + "/Textures"
MAT_DIR = DEST + "/Materials"

# Blender(오른손 Z-up) -> 언리얼(왼손 Z-up): Y를 뒤집고 yaw 부호를 뒤집는다.
# 건물이 좌우로 뒤집혀 보이면 이 값 하나만 False 로 바꾸면 된다.
MIRROR_Y = True
M_TO_CM = 100.0

# Blender 머티리얼 슬롯 이름 -> (텍스처 세트, 색 틴트, metallic, roughness)
# 텍스처 세트가 None 이면 단색 머티리얼로 만든다.
MATERIAL_MAP = {
    "MI_Brick":            ("Brick",     None,                   0.0, None),
    "MI_Concrete":         ("Concrete",  None,                   0.0, None),
    "MI_Plaster":          ("Plaster",   None,                   0.0, None),
    "MI_Tile":             ("Tile",      None,                   0.0, None),
    "MI_Wood":             ("Wood",      None,                   0.0, None),
    "MI_Trim":             ("Wood",      (0.45, 0.34, 0.24),     0.0, None),
    "MI_Metal_DarkGrey":   ("Metal",     (0.35, 0.35, 0.38),    0.85, None),
    "MI_Metal_DarkGrey2":  ("Metal",     (0.45, 0.45, 0.48),     0.7, None),
    "MI_Metal_Galvanized": ("Metal",     (1.60, 1.62, 1.65),     0.9, None),
    # 텍스처가 없는 소품 계열은 단색으로
    "MI_Glass":            (None, (0.55, 0.65, 0.60), 0.0, 0.08),
    "MI_Leaf_Green":       (None, (0.13, 0.35, 0.14), 0.0, 0.80),
    "MI_Terracotta":       (None, (0.55, 0.28, 0.18), 0.0, 0.85),
    "MI_Barber_Red":       (None, (0.65, 0.05, 0.05), 0.0, 0.30),
    "MI_Barber_White":     (None, (0.92, 0.90, 0.85), 0.0, 0.30),
    "MI_Barber_Blue":      (None, (0.05, 0.15, 0.55), 0.0, 0.30),
    "MI_Brass":            (None, (0.75, 0.60, 0.20), 0.9, 0.30),
    "MI_Gas_Yellow":       (None, (0.80, 0.62, 0.05), 0.2, 0.40),
    "MI_Awning_Green":     (None, (0.20, 0.45, 0.32), 0.0, 0.60),
    "MI_Plastic_Blue":     (None, (0.05, 0.35, 0.65), 0.0, 0.50),
    "MI_Plastic_Grey":     (None, (0.45, 0.45, 0.46), 0.0, 0.55),
    "MI_Fabric_Cream":     (None, (0.85, 0.82, 0.74), 0.0, 0.90),
    "MI_Soil":             (None, (0.22, 0.15, 0.10), 0.0, 1.00),
}

TEXTURE_SETS = ("Brick", "Concrete", "Plaster", "Metal", "Wood", "Tile")

_AT = unreal.AssetToolsHelpers.get_asset_tools()
_EAL = unreal.EditorAssetLibrary
_MEL = unreal.MaterialEditingLibrary


def log(msg):
    unreal.log("[OldKoreanBuildingA] " + str(msg))


# ---------------------------------------------------------------------------
# 1. textures
# ---------------------------------------------------------------------------

def import_textures():
    tex_src = os.path.join(SRC, "textures")
    files = [os.path.join(tex_src, f) for f in sorted(os.listdir(tex_src))
             if f.lower().endswith(".png") and not f.startswith("_")]
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = TEX_DIR
        t.automated = True
        t.replace_existing = True
        t.save = True
        tasks.append(t)
    _AT.import_asset_tasks(tasks)

    # Normal / Roughness 는 선형(Non-sRGB) 이어야 한다
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        path = "{}/{}".format(TEX_DIR, name)
        tex = _EAL.load_asset(path)
        if tex is None:
            continue
        if name.endswith("_Normal"):
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif name.endswith("_Roughness"):
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_MASKS)
        _EAL.save_asset(path)
    log("textures imported: {}".format(len(files)))
    return len(files)


# ---------------------------------------------------------------------------
# 2. materials
# ---------------------------------------------------------------------------

def _tex(setname, kind):
    return _EAL.load_asset("{}/T_{}_{}".format(TEX_DIR, setname, kind))


def build_material(slot_name, spec):
    tex_set, tint, metallic, roughness = spec
    mat_name = "M_" + slot_name.replace("MI_", "")
    mat_path = "{}/{}".format(MAT_DIR, mat_name)
    if _EAL.does_asset_exist(mat_path):
        _EAL.delete_asset(mat_path)
    mat = _AT.create_asset(mat_name, MAT_DIR, unreal.Material,
                           unreal.MaterialFactoryNew())

    if tex_set:
        base = _MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -820, 0)
        base.texture = _tex(tex_set, "BaseColor")
        out = base
        if tint:
            mul = _MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -520, 0)
            const = _MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, 160)
            const.constant = unreal.LinearColor(tint[0], tint[1], tint[2], 1.0)
            _MEL.connect_material_expressions(base, "RGB", mul, "A")
            _MEL.connect_material_expressions(const, "", mul, "B")
            out = mul
        _MEL.connect_material_property(out, "RGB" if out is base else "",
                                       unreal.MaterialProperty.MP_BASE_COLOR)

        rough = _MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -820, 300)
        rough.texture = _tex(tex_set, "Roughness")
        rough.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
        _MEL.connect_material_property(rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)

        nrm = _MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -820, 600)
        nrm.texture = _tex(tex_set, "Normal")
        nrm.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        _MEL.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    else:
        col = _MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -520, 0)
        col.constant = unreal.LinearColor(tint[0], tint[1], tint[2], 1.0)
        _MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        r = _MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -520, 200)
        r.r = roughness if roughness is not None else 0.8
        _MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)

    if metallic:
        m = _MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -520, 380)
        m.r = metallic
        _MEL.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)

    _MEL.recompile_material(mat)
    _EAL.save_asset(mat_path)
    return mat_path


def build_materials():
    made = {}
    for slot, spec in MATERIAL_MAP.items():
        try:
            made[slot] = build_material(slot, spec)
        except Exception as exc:
            log("material FAILED {}: {}".format(slot, exc))
    log("materials built: {}".format(len(made)))
    return made


# ---------------------------------------------------------------------------
# 3. static meshes
# ---------------------------------------------------------------------------

def _fbx_options():
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_materials", False)   # 머티리얼은 위에서 직접 만든다
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)

    smd = opts.static_mesh_import_data
    smd.set_editor_property("combine_meshes", True)
    smd.set_editor_property("auto_generate_collision", False)  # UCX 를 쓴다
    smd.set_editor_property("one_convex_hull_per_ucx", True)
    smd.set_editor_property("remove_degenerates", True)
    smd.set_editor_property("generate_lightmap_u_vs", False)   # UV1 을 이미 넣어둠
    smd.set_editor_property("import_translation", unreal.Vector(0.0, 0.0, 0.0))
    smd.set_editor_property("import_uniform_scale", 1.0)
    smd.set_editor_property("normal_import_method",
                            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    return opts


def import_meshes():
    fbx_src = os.path.join(SRC, "fbx")
    files = [os.path.join(fbx_src, f) for f in sorted(os.listdir(fbx_src))
             if f.lower().endswith(".fbx")]
    opts = _fbx_options()
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = MESH_DIR
        t.automated = True
        t.replace_existing = True
        t.save = True
        t.options = opts
        tasks.append(t)
    _AT.import_asset_tasks(tasks)
    log("meshes imported: {}".format(len(files)))
    return [os.path.splitext(os.path.basename(f))[0] for f in files]


def assign_materials(mesh_names, made):
    """FBX 슬롯 이름(MI_*)을 보고 위에서 만든 M_* 머티리얼을 꽂는다."""
    fixed = 0
    for name in mesh_names:
        path = "{}/{}".format(MESH_DIR, name)
        mesh = _EAL.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        slots = mesh.get_editor_property("static_materials")
        changed = False
        for i, slot in enumerate(slots):
            slot_name = str(slot.get_editor_property("material_slot_name"))
            target = made.get(slot_name)
            if target and _EAL.does_asset_exist(target):
                slot.set_editor_property("material_interface", _EAL.load_asset(target))
                changed = True
        if changed:
            mesh.set_editor_property("static_materials", slots)
            # UV1 을 라이트맵으로 쓰라고 지정
            mesh.set_editor_property("light_map_coordinate_index", 1)
            _EAL.save_asset(path)
            fixed += 1
    log("meshes with materials assigned: {}".format(fixed))


# ---------------------------------------------------------------------------
# 4. optional: rebuild the building in the current level
# ---------------------------------------------------------------------------

def assemble(origin=(0.0, 0.0, 0.0)):
    """placements.json 을 읽어 현재 레벨에 84개 액터를 배치한다."""
    manifest = os.path.join(SRC, "placements.json")
    with open(manifest, "r") as fh:
        data = load_current_json_file(fh)

    subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    spawned = 0
    for p in data["placements"]:
        mesh = _EAL.load_asset("{}/{}".format(MESH_DIR, p["module"]))
        if mesh is None:
            log("missing mesh, skipped: " + p["module"])
            continue
        x, y, z = p["loc_m"]
        sy = -1.0 if MIRROR_Y else 1.0
        loc = unreal.Vector(origin[0] + x * M_TO_CM,
                            origin[1] + sy * y * M_TO_CM,
                            origin[2] + z * M_TO_CM)
        yaw = -p["yaw_deg"] if MIRROR_Y else p["yaw_deg"]
        rot = unreal.Rotator(0.0, 0.0, yaw)
        actor = subsys.spawn_actor_from_object(mesh, loc, rot)
        if actor:
            actor.set_actor_label(p["instance"])
            actor.set_folder_path("OldKoreanBuildingA")
            spawned += 1
    log("actors spawned: {}".format(spawned))
    return spawned


# ---------------------------------------------------------------------------

def main(with_assemble=False):
    for d in (DEST, MESH_DIR, TEX_DIR, MAT_DIR):
        if not _EAL.does_directory_exist(d):
            _EAL.make_directory(d)
    log("importing from " + SRC)
    import_textures()
    made = build_materials()
    names = import_meshes()
    assign_materials(names, made)
    log("DONE -> " + DEST)
    if with_assemble:
        assemble()


main()
