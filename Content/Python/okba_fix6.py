# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_fix6.py
"""OldKoreanBuildingA: 깨끗한 신규 임포트 + 배율 자동 측정 + 배치 재생성.

    import okba_fix6
    다시:  import importlib, okba_fix6; importlib.reload(okba_fix6)

fix5 에서 밝혀진 것
    LogEditorFactories: Performing atomic reimport of [...]
  에셋이 이미 있으면 언리얼은 재임포트 경로를 타고, 그때는 에셋에 저장된
  임포트 설정을 쓴다. AssetImportTask 에 넘긴 FbxImportUI 는 무시된다.
  fix2 이후 내가 넘긴 옵션(import_uniform_scale 포함)은 전부 효과가 없었고,
  fix4 에서 크기가 바뀐 것도 옵션이 아니라 FBX 파일 내용이 바뀌어서였다.

이 스크립트의 방식
  1) 배율을 추측하지 않고 측정한다.
     벽 하나를 임시 폴더에 '신규' 임포트해서(에셋이 없으니 옵션이 먹는다)
     실제 크기를 잰다. 기대 200 uu 대비 비율이 곧 필요한 보정 배율이다.
  2) 액터 84개와 메시 에셋 29개를 지운다. 지워야 다음 임포트가 신규가 된다.
  3) 측정된 배율로 29개를 신규 임포트한다.
  4) 크기/충돌/머티리얼을 검증하고, placements.json 으로 84개를 다시 배치한다.

액터를 지우고 다시 만드는 이유: 에셋을 지우면 액터의 메시 참조가 끊긴다.
배치는 placements.json 에 전부 남아 있으므로 손실은 없다. 배치 원점은
(0,0,0) 이니, 건물을 다른 자리로 옮기려면 끝난 뒤 아웃라이너에서
OldKoreanBuildingA 폴더를 통째로 선택해 옮기면 된다.
"""
import json
import os
import traceback
import unreal

SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA"
FBX_DIR = os.path.join(SRC, "fbx")
MANIFEST = os.path.join(SRC, "placements.json")
DEST = "/Game/Environment/OldKoreanBuildingA"
MESH_DIR = DEST + "/Meshes"
MAT_DIR = DEST + "/Materials"
PROBE_DIR = DEST + "/_scale_probe"

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P = unreal.log

M_TO_CM = 100.0
MIRROR_Y = True
FOLDER = "OldKoreanBuildingA"

PROBE_MESH = "SM_Wall_Straight_200"
PROBE_WANT_X = 200.0

EXPECT = {
    "Deco_Awning_200":            ((200, 87, 42),    0),
    "Deco_Barber_Pole":           ((21, 22, 139),    0),
    "Deco_Curtain_100":           ((112, 6, 124),    0),
    "Deco_Floor_Tile_100":        ((100, 100, 5),    0),
    "Deco_GasPipe_200":           ((203, 8, 143),    0),
    "Deco_Gutter_200":            ((200, 10, 310),   0),
    "Furn_Pergola_200":           ((189, 189, 236),  0),
    "Furn_Railing_200":           ((205, 5, 100),    1),
    "Furn_Sandbox_Planter":       ((140, 100, 28),   0),
    "Furn_Stair_Steel_300":       ((92, 390, 390),   1),
    "Furn_Stair_Steel_600":       ((94, 780, 655),   1),
    "Prop_AC_Unit":               ((80, 31, 63),     0),
    "Prop_Bucket":                ((28, 28, 45),     0),
    "Prop_Drum_Barrel":           ((60, 60, 90),     0),
    "Prop_HandTruck":             ((56, 44, 132),    0),
    "Prop_MeterBox":              ((40, 22, 55),     0),
    "SM_Door_Leaf_100":           ((96, 16, 206),    1),
    "SM_Shopfront_Door_200":      ((200, 22, 300),   3),
    "SM_Slab_Corner_200":         ((200, 200, 30),   3),
    "SM_Slab_Straight_200":       ((200, 200, 20),   1),
    "SM_Stair_Interior_300":      ((102, 390, 395),  3),
    "SM_Wall_Corner_200":         ((200, 200, 300),  2),
    "SM_Wall_Door_200":           ((200, 22, 305),   3),
    "SM_Wall_Partition_200":      ((200, 11, 300),   1),
    "SM_Wall_Partition_Door_200": ((200, 12, 300),   3),
    "SM_Wall_Straight_200":       ((200, 20, 300),   1),
    "SM_Wall_Window_200":         ((200, 22, 300),   1),
    "SM_Window_Frame":            ((110, 6, 140),    0),
    "Veg_Potted_Plant_Round":     ((57, 60, 81),     0),
}

NO_COLLISION = ("Deco_Awning_200", "Deco_Gutter_200", "Deco_GasPipe_200",
                "Deco_Curtain_100", "Deco_Floor_Tile_100", "SM_Window_Frame")
BOX_COLLISION = ("Deco_Barber_Pole", "Furn_Pergola_200", "Furn_Sandbox_Planter",
                 "Prop_AC_Unit", "Prop_Bucket", "Prop_Drum_Barrel",
                 "Prop_HandTruck", "Prop_MeterBox", "Veg_Potted_Plant_Round")

SLOT_TO_MAT = {
    "MI_Brick": "M_Brick", "MI_Concrete": "M_Concrete", "MI_Plaster": "M_Plaster",
    "MI_Tile": "M_Tile", "MI_Wood": "M_Wood", "MI_Trim": "M_Trim",
    "MI_Metal_DarkGrey": "M_Metal_DarkGrey", "MI_Metal_DarkGrey2": "M_Metal_DarkGrey2",
    "MI_Metal_Galvanized": "M_Metal_Galvanized", "MI_Glass": "M_Glass",
    "MI_Leaf_Green": "M_Leaf_Green", "MI_Terracotta": "M_Terracotta",
    "MI_Barber_Red": "M_Barber_Red", "MI_Barber_White": "M_Barber_White",
    "MI_Barber_Blue": "M_Barber_Blue", "MI_Brass": "M_Brass",
    "MI_Gas_Yellow": "M_Gas_Yellow", "MI_Awning_Green": "M_Awning_Green",
    "MI_Plastic_Blue": "M_Plastic_Blue", "MI_Plastic_Grey": "M_Plastic_Grey",
    "MI_Fabric_Cream": "M_Fabric_Cream", "MI_Soil": "M_Soil",
}


def base_slot_name(name):
    s = str(name)
    while len(s) > 4 and s[-4] == "_" and s[-3:].isdigit():
        s = s[:-4]
    return s


def cvar(cmd):
    try:
        unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception:
        P("[FIX6] console FAILED: %s" % cmd)


def options(uniform):
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
    d.set_editor_property("import_uniform_scale", uniform)
    d.set_editor_property("normal_import_method",
                          unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    return ui


def do_import(files, dest, uniform):
    ui = options(uniform)
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = os.path.join(FBX_DIR, f)
        t.destination_path = dest
        t.automated = True
        t.replace_existing = True
        t.save = True
        t.options = ui
        tasks.append(t)
    AT.import_asset_tasks(tasks)


def size_of(mesh):
    bb = mesh.get_bounding_box()
    return (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)


def hulls(mesh):
    try:
        bs = mesh.get_editor_property("body_setup")
        if bs is None:
            return 0
        agg = bs.get_editor_property("agg_geom")
        return (len(agg.get_editor_property("convex_elems"))
                + len(agg.get_editor_property("box_elems")))
    except Exception:
        return -1


def sms():
    try:
        return unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception:
        return None


def strip_collision(mesh):
    try:
        sub = sms()
        if sub is not None:
            sub.remove_collisions(mesh)
        else:
            unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
    except Exception:
        pass


def add_box(mesh):
    try:
        sub = sms()
        if sub is not None:
            sub.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
        else:
            unreal.EditorStaticMeshLibrary.add_simple_collisions(
                mesh, unreal.ScriptCollisionShapeType.BOX)
    except Exception:
        pass


def assign(mesh):
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
        target = SLOT_TO_MAT.get(key)
        mat = (EAL.load_asset(MAT_DIR + "/" + target)
               if target and EAL.does_asset_exist(MAT_DIR + "/" + target) else None)
        if mat is not None:
            ns.set_editor_property("material_interface", mat)
            changed += 1
        else:
            ns.set_editor_property("material_interface",
                                   slot.get_editor_property("material_interface"))
        new.append(ns)
    if changed:
        mesh.set_editor_property("static_materials", new)
        try:
            mesh.set_editor_property("light_map_coordinate_index", 1)
        except Exception:
            pass
    return changed


# --------------------------------------------------------------------------
def measure_scale():
    """벽 하나를 임시 폴더에 신규 임포트해서 실제 배율을 잰다."""
    P("[FIX6] --- 1. measure the importer's actual scale ---")
    if EAL.does_directory_exist(PROBE_DIR):
        EAL.delete_directory(PROBE_DIR)
    do_import(["%s.fbx" % PROBE_MESH], PROBE_DIR, 1.0)
    m = EAL.load_asset("%s/%s" % (PROBE_DIR, PROBE_MESH))
    if m is None:
        P("[FIX6]   probe import FAILED — 배율을 잴 수 없다. 중단한다.")
        return None
    got = size_of(m)
    P("[FIX6]   probe %s imported at %.0f x %.0f x %.0f uu (uniform_scale=1.0)"
      % (PROBE_MESH, got[0], got[1], got[2]))
    if got[0] <= 0.0:
        P("[FIX6]   probe width is zero — 중단한다.")
        return None
    factor = PROBE_WANT_X / got[0]
    P("[FIX6]   want %.0f uu wide  ->  import_uniform_scale = %g"
      % (PROBE_WANT_X, factor))
    EAL.delete_directory(PROBE_DIR)
    return factor


def wipe():
    """액터와 메시 에셋을 지운다. 지워야 다음 임포트가 '신규' 가 된다."""
    P("[FIX6] --- 2. delete actors and mesh assets ---")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    killed = 0
    for a in list(eas.get_all_level_actors()):
        try:
            if str(a.get_folder_path()) == FOLDER:
                eas.destroy_actor(a)
                killed += 1
        except Exception:
            pass
    P("[FIX6]   actors destroyed: %d" % killed)

    gone = failed = 0
    for path in list(EAL.list_assets(MESH_DIR, recursive=True)):
        try:
            if EAL.delete_asset(path.split(".")[0]):
                gone += 1
            else:
                failed += 1
        except Exception:
            failed += 1
    P("[FIX6]   mesh assets deleted: %d (failed %d)" % (gone, failed))
    return failed


def verify_and_fix(files):
    P("[FIX6] --- 4. verify size / collision / materials ---")
    P("[FIX6] %-28s %-22s %-12s %s" % ("mesh", "size uu", "coll (want)", "policy"))
    P("[FIX6] " + "-" * 74)
    bad_size = bad_coll = 0
    for f in files:
        name = os.path.splitext(f)[0]
        path = "%s/%s" % (MESH_DIR, name)
        try:
            m = EAL.load_asset(path)
            if not isinstance(m, unreal.StaticMesh):
                P("[FIX6] %-28s MISSING" % name)
                bad_size += 1
                continue
            assign(m)
            if name in NO_COLLISION:
                policy, want_c = "none", 0
                strip_collision(m)
            elif name in BOX_COLLISION:
                policy, want_c = "box", 1
                strip_collision(m)
                add_box(m)
            else:
                policy = "authored UCX"
                want_c = EXPECT.get(name, (None, 0))[1]
            EAL.save_asset(path)

            got = size_of(m)
            want_size = EXPECT.get(name, (None, 0))[0]
            h = hulls(m)
            size_ok = want_size is None or all(
                abs(got[i] - want_size[i]) < 3 for i in range(3))
            coll_ok = (h == want_c)
            if not size_ok:
                bad_size += 1
            if not coll_ok:
                bad_coll += 1
            P("[FIX6] %-28s %-22s %-12s %s"
              % (name,
                 "%.0fx%.0fx%.0f%s" % (got + ("" if size_ok else "  !!",)),
                 "%d (%d)%s" % (h, want_c, "" if coll_ok else " !!"),
                 policy))
        except Exception:
            P("[FIX6] %-28s !! %s"
              % (name, traceback.format_exc().strip().splitlines()[-1]))
    P("[FIX6] " + "-" * 74)
    P("[FIX6] size mismatches: %d / %d      collision mismatches: %d / %d"
      % (bad_size, len(files), bad_coll, len(files)))
    return bad_size


def rebuild_actors():
    P("[FIX6] --- 5. rebuild placement from placements.json ---")
    if not os.path.exists(MANIFEST):
        P("[FIX6]   manifest not found: %s" % MANIFEST)
        return
    with open(MANIFEST) as fh:
        placements = json.load(fh)["placements"]
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    spawned = missing = 0
    for p in placements:
        mesh = EAL.load_asset("%s/%s" % (MESH_DIR, p["module"]))
        if mesh is None:
            missing += 1
            continue
        x, y, z = p["loc_m"]
        sy = -1.0 if MIRROR_Y else 1.0
        loc = unreal.Vector(x * M_TO_CM, sy * y * M_TO_CM, z * M_TO_CM)
        yaw = -p["yaw_deg"] if MIRROR_Y else p["yaw_deg"]
        a = eas.spawn_actor_from_object(mesh, loc, unreal.Rotator(0.0, 0.0, yaw))
        if a is None:
            continue
        a.set_actor_label(p["instance"])
        a.set_folder_path(FOLDER)
        spawned += 1
    P("[FIX6]   spawned %d / %d  (missing mesh %d)"
      % (spawned, len(placements), missing))

    acts = [a for a in eas.get_all_level_actors()
            if str(a.get_folder_path()) == FOLDER]
    mn = [1e18] * 3
    mx = [-1e18] * 3
    for a in acts:
        o, e = a.get_actor_bounds(False)
        for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            mn[i] = min(mn[i], oc - ec)
            mx[i] = max(mx[i], oc + ec)
    P("[FIX6]   actors=%d  bounds min=%s max=%s"
      % (len(acts), [round(v) for v in mn], [round(v) for v in mx]))
    P("[FIX6]   overall size = %s uu   (정상이면 약 [800, 400, 655])"
      % [round(mx[i] - mn[i]) for i in range(3)])


def run():
    P("=" * 80)
    files = sorted(f for f in os.listdir(FBX_DIR) if f.lower().endswith(".fbx"))
    cvar("Interchange.FeatureFlags.Import.FBX 0")
    try:
        factor = measure_scale()
        if factor is None:
            return
        if wipe() > 0:
            P("[FIX6] 일부 메시를 지우지 못했다. 그 메시는 재임포트가 되어")
            P("[FIX6] 옵션이 무시되므로, 남은 참조를 정리하고 다시 실행해야 한다.")
        P("[FIX6] --- 3. fresh import of %d fbx (uniform_scale=%g) ---"
          % (len(files), factor))
        do_import(files, MESH_DIR, factor)
        if verify_and_fix(files) == 0:
            rebuild_actors()
        else:
            P("[FIX6] 크기가 아직 맞지 않아 배치는 건너뛴다.")
    finally:
        cvar("Interchange.FeatureFlags.Import.FBX 1")
    P("=" * 80)


run()
