# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_fix2.py
"""OldKoreanBuildingA: 텍스처/머티리얼 복구 + UCX 충돌체 복구 (v1).

    import okba_fix2
    다시:  import importlib, okba_fix2; importlib.reload(okba_fix2)

배치는 이제 맞다. 남은 두 가지를 잡는다.

1) 벽이 회색 체크무늬로 보이는 이유
   M_Brick / M_Concrete / M_Plaster ... 는 TextureSample 노드로 배선돼 있는데,
   그 노드의 texture 가 None 이면 언리얼이 엔진 기본 체크무늬 텍스처를 대신
   물린다. 색만 상수로 넣은 머티리얼(어닝, 이발소 간판, 화분)은 멀쩡하게
   나오는데 벽만 체크무늬인 게 정확히 그 증상이다.
   -> 텍스처 18장을 확인/재임포트하고, 머티리얼을 다시 만들면서 각 노드에
      실제 텍스처가 물렸는지 한 장씩 검증해서 찍는다.

2) UCX 가 0개인 이유 (추정, 이 스크립트로 검증한다)
   FBX 안에는 UCX 노드가 확실히 들어있다(블렌더에서 바이너리로 확인함).
   그런데 UE 5.8 은 Interchange 로 FBX 를 읽고, AssetImportTask 에 넘긴
   FbxImportUI 옵션(one_convex_hull_per_ucx 등)은 Interchange 경로에서
   무시된다. -> 레거시 FBX 임포터로 되돌린 뒤 다시 임포트해 본다.
   되돌리기는 콘솔 변수 하나(Interchange.FeatureFlags.Import.FBX 0)이고,
   이 스크립트가 끝나면서 원래 값으로 돌려놓는다.
"""
import os
import traceback
import unreal

SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA"
DEST = "/Game/Constellation/Environments/KoreanBuildings/BuildingA"
MESH_DIR = DEST + "/Meshes"
TEX_DIR = DEST + "/Textures"
MAT_DIR = DEST + "/Materials"

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
P = unreal.log

TEXTURE_SETS = ("Brick", "Concrete", "Plaster", "Metal", "Wood", "Tile")
KINDS = ("BaseColor", "Normal", "Roughness")

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

EXPECT_UCX = {
    "SM_Wall_Straight_200": 1, "SM_Wall_Corner_200": 2, "SM_Wall_Window_200": 1,
    "SM_Wall_Door_200": 3, "SM_Shopfront_Door_200": 3,
    "SM_Wall_Partition_200": 1, "SM_Wall_Partition_Door_200": 3,
    "SM_Slab_Straight_200": 1, "SM_Slab_Corner_200": 3,
    "SM_Stair_Interior_300": 3, "Furn_Stair_Steel_300": 1,
    "Furn_Stair_Steel_600": 1, "SM_Door_Leaf_100": 1, "Furn_Railing_200": 1,
}


def base_slot_name(name):
    s = str(name)
    while len(s) > 4 and s[-4] == "_" and s[-3:].isdigit():
        s = s[:-4]
    return s


# ---------------------------------------------------------------- textures
def tex_path(setname, kind):
    return "%s/T_%s_%s" % (TEX_DIR, setname, kind)


def fix_textures():
    P("[FIX2] --- 1. textures ---")
    missing = [(s, k) for s in TEXTURE_SETS for k in KINDS
               if not EAL.does_asset_exist(tex_path(s, k))]
    P("[FIX2] expected 18, missing %d" % len(missing))
    if missing:
        P("[FIX2] missing: %s" % ["T_%s_%s" % (s, k) for s, k in missing])

    tex_src = os.path.join(SRC, "textures")
    if not os.path.isdir(tex_src):
        P("[FIX2] !! texture source folder not found: %s" % tex_src)
        return
    files = [os.path.join(tex_src, f) for f in sorted(os.listdir(tex_src))
             if f.lower().endswith(".png") and not f.startswith("_")]
    P("[FIX2] importing %d png from disk" % len(files))
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = TEX_DIR
        t.automated = True
        t.replace_existing = True
        t.save = True
        tasks.append(t)
    AT.import_asset_tasks(tasks)

    ok = 0
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        path = "%s/%s" % (TEX_DIR, name)
        tex = EAL.load_asset(path)
        if tex is None:
            P("[FIX2]   FAILED to import %s" % name)
            continue
        if name.endswith("_Normal"):
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif name.endswith("_Roughness"):
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_MASKS)
        EAL.save_asset(path)
        ok += 1
    P("[FIX2] textures present: %d / %d" % (ok, len(files)))


# --------------------------------------------------------------- materials
def build_material(slot_name, spec):
    tex_set, tint, metallic, roughness = spec
    mat_name = "M_" + slot_name.replace("MI_", "")
    mat_path = "%s/%s" % (MAT_DIR, mat_name)
    if EAL.does_asset_exist(mat_path):
        EAL.delete_asset(mat_path)
    mat = AT.create_asset(mat_name, MAT_DIR, unreal.Material,
                          unreal.MaterialFactoryNew())
    bound = []
    if tex_set:
        for kind, y, prop, chan, sampler in (
                ("BaseColor", 0, unreal.MaterialProperty.MP_BASE_COLOR, "RGB", None),
                ("Roughness", 300, unreal.MaterialProperty.MP_ROUGHNESS, "R",
                 unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR),
                ("Normal", 600, unreal.MaterialProperty.MP_NORMAL, "RGB",
                 unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)):
            node = MEL.create_material_expression(
                mat, unreal.MaterialExpressionTextureSample, -820, y)
            t = EAL.load_asset(tex_path(tex_set, kind))
            if t is None:
                bound.append("%s=MISSING" % kind)
                continue
            node.texture = t
            if sampler is not None:
                node.sampler_type = sampler
            bound.append("%s=ok" % kind)
            if kind == "BaseColor" and tint:
                mul = MEL.create_material_expression(
                    mat, unreal.MaterialExpressionMultiply, -520, 0)
                const = MEL.create_material_expression(
                    mat, unreal.MaterialExpressionConstant3Vector, -700, 160)
                const.constant = unreal.LinearColor(tint[0], tint[1], tint[2], 1.0)
                MEL.connect_material_expressions(node, "RGB", mul, "A")
                MEL.connect_material_expressions(const, "", mul, "B")
                MEL.connect_material_property(mul, "", prop)
                continue
            MEL.connect_material_property(node, chan, prop)
    else:
        col = MEL.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -520, 0)
        col.constant = unreal.LinearColor(tint[0], tint[1], tint[2], 1.0)
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        r = MEL.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -520, 200)
        r.r = roughness if roughness is not None else 0.8
        MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
        bound.append("solid colour")
    if metallic:
        m = MEL.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -520, 380)
        m.r = metallic
        MEL.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.recompile_material(mat)
    EAL.save_asset(mat_path)
    return mat_path, bound


def fix_materials():
    P("[FIX2] --- 2. materials ---")
    made = {}
    for slot, spec in sorted(MATERIAL_MAP.items()):
        try:
            path, bound = build_material(slot, spec)
            made[slot] = path
            P("[FIX2]   %-22s %s" % (slot, ", ".join(bound)))
        except Exception:
            P("[FIX2]   %-22s !! %s"
              % (slot, traceback.format_exc().strip().splitlines()[-1]))
    P("[FIX2] materials built: %d / %d" % (len(made), len(MATERIAL_MAP)))
    return made


# --------------------------------------------------------------- collision
def collision_report(mesh):
    """(has_body_setup, convex_count, simple_count) — 0 과 None 을 구분한다."""
    try:
        bs = mesh.get_editor_property("body_setup")
    except Exception:
        return ("bodysetup?", -1, -1)
    if bs is None:
        return ("no body_setup", 0, 0)
    try:
        agg = bs.get_editor_property("agg_geom")
        n_convex = len(agg.get_editor_property("convex_elems"))
        n_box = len(agg.get_editor_property("box_elems"))
        n_sph = len(agg.get_editor_property("sphere_elems"))
        return ("ok", n_convex, n_box + n_sph)
    except Exception:
        return ("agg_geom?", -1, -1)


def legacy_options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("mesh_type_to_import",
                           unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.static_mesh_import_data
    d.set_editor_property("combine_meshes", False)
    d.set_editor_property("auto_generate_collision", False)
    d.set_editor_property("one_convex_hull_per_ucx", True)
    d.set_editor_property("remove_degenerates", True)
    d.set_editor_property("generate_lightmap_u_vs", False)
    d.set_editor_property("import_uniform_scale", 1.0)
    d.set_editor_property("normal_import_method",
                          unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    return ui


def cvar(cmd):
    try:
        unreal.SystemLibrary.execute_console_command(None, cmd)
        P("[FIX2]   console: %s" % cmd)
        return True
    except Exception:
        P("[FIX2]   console FAILED: %s" % cmd)
        return False


def fix_collision(files):
    P("[FIX2] --- 3. collision ---")
    m = EAL.load_asset("%s/SM_Wall_Straight_200" % MESH_DIR)
    if m is not None:
        P("[FIX2] before: SM_Wall_Straight_200 %s convex=%d simple=%d"
          % collision_report(m))

    # 레거시 FBX 임포터로 전환 -> FbxImportUI 옵션이 실제로 먹는다
    cvar("Interchange.FeatureFlags.Import.FBX 0")

    ui = legacy_options()
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = os.path.join(SRC, "fbx", f)
        t.destination_path = MESH_DIR
        t.automated = True
        t.replace_existing = True
        t.save = True
        t.options = ui
        tasks.append(t)
    AT.import_asset_tasks(tasks)

    cvar("Interchange.FeatureFlags.Import.FBX 1")   # 원래대로 되돌린다
    P("[FIX2] re-imported %d fbx through the legacy importer" % len(files))


# ------------------------------------------------------------------- meshes
def assign_and_verify(files, made):
    P("[FIX2] --- 4. meshes ---")
    P("[FIX2] %-30s %-9s %-8s %s" % ("mesh", "UCX", "want", "materials"))
    P("[FIX2] " + "-" * 66)
    ucx_ok = ucx_bad = 0
    mat_ok = 0
    for f in files:
        name = os.path.splitext(f)[0]
        path = "%s/%s" % (MESH_DIR, name)
        try:
            mesh = EAL.load_asset(path)
            if not isinstance(mesh, unreal.StaticMesh):
                P("[FIX2] %-30s NOT A STATIC MESH" % name)
                continue
            slots = mesh.get_editor_property("static_materials")
            new = []
            changed = 0
            for slot in slots:
                key = base_slot_name(slot.get_editor_property("material_slot_name"))
                ns = unreal.StaticMaterial()
                ns.set_editor_property("material_slot_name",
                                       slot.get_editor_property("material_slot_name"))
                try:
                    ns.set_editor_property(
                        "imported_material_slot_name",
                        slot.get_editor_property("imported_material_slot_name"))
                except Exception:
                    pass
                target = made.get(key)
                mat = EAL.load_asset(target) if (target and EAL.does_asset_exist(target)) else None
                if mat is not None:
                    ns.set_editor_property("material_interface", mat)
                    changed += 1
                else:
                    ns.set_editor_property(
                        "material_interface",
                        slot.get_editor_property("material_interface"))
                new.append(ns)
            if changed:
                mesh.set_editor_property("static_materials", new)
                try:
                    mesh.set_editor_property("light_map_coordinate_index", 1)
                except Exception:
                    pass
                mat_ok += 1
            EAL.save_asset(path)

            state, n_convex, n_simple = collision_report(mesh)
            want = EXPECT_UCX.get(name, 0)
            if want:
                if n_convex == want:
                    ucx_ok += 1
                else:
                    ucx_bad += 1
            P("[FIX2] %-30s %-9s %-8s %d/%d slots"
              % (name, "%d (%s)" % (n_convex, state), want, changed, len(new)))
        except Exception:
            P("[FIX2] %-30s !! %s"
              % (name, traceback.format_exc().strip().splitlines()[-1]))
    P("[FIX2] " + "-" * 66)
    P("[FIX2] UCX matching expected: %d / %d   (mismatch %d)"
      % (ucx_ok, len(EXPECT_UCX), ucx_bad))
    P("[FIX2] meshes with materials assigned: %d / %d" % (mat_ok, len(files)))


def run():
    P("=" * 78)
    files = sorted(f for f in os.listdir(os.path.join(SRC, "fbx"))
                   if f.lower().endswith(".fbx"))
    fix_textures()
    made = fix_materials()
    fix_collision(files)
    assign_and_verify(files, made)
    P("[FIX2] done. 뷰포트에서 벽 텍스처를 확인하고, 충돌은 메시 에디터의")
    P("[FIX2] Collision 표시나 PIE 로 걸어 들어가서 확인하면 된다.")
    P("=" * 78)


run()
