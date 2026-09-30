# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_fix5.py
"""OldKoreanBuildingA: 스케일 확정 + 충돌 정리 + 배치 복구.

    import okba_fix5
    다시:  import importlib, okba_fix5; importlib.reload(okba_fix5)

fix4 로그에서 확정된 사실
  레거시 FBX 임포터의 배율은 100 / UnitScaleFactor 로 움직인다.
      정점 2.0,   UnitScaleFactor=100  ->  2 uu
      정점 200.0, UnitScaleFactor=1    ->  20000 uu
  파일 쪽 단위 의미를 맞추려는 시도를 두 번 했고 둘 다 빗나갔다. 그래서 이번엔
  임포터에 배율을 직접 준다. 지금 파일이 20000 으로 들어오는 것은 측정된 값이니
  import_uniform_scale = 0.01 이면 정확히 200 이다. 추론이 아니라 산수다.

같이 고치는 것
  1) 소품 충돌 누적 — UCX 가 없는 모듈은 재임포트할 때마다 자동 훌이 하나씩
     쌓이고 있었다(1 -> 2). 정책을 명시한다:
       * 작성된 UCX 가 있는 14종 : 임포트된 그대로 두고 개수만 검증
       * 통행에 걸리면 안 되는 장식 6종 : 충돌 제거
       * 나머지 소품 9종 : 충돌을 지우고 박스 하나만 새로 붙인다
  2) 액터가 통째로 밀린 것 — 84개를 선택한 채 기즈모를 잡으면 전부 같이 끌린다.
     placements.json 기준으로 위치/회전을 다시 써서 되돌리고, 없어진 액터는
     다시 스폰한다. 원점(0,0,0) 기준으로 복구하므로, 건물을 다른 자리에 두려면
     복구 후에 아웃라이너에서 폴더째 선택해 한 번에 옮기면 된다.
"""
from resource_paths import loads as load_current_json, load as load_current_json_file
import json
import os
import traceback
import unreal

SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA"
FBX_DIR = os.path.join(SRC, "fbx")
MANIFEST = os.path.join(SRC, "placements.json")
DEST = "/Game/Constellation/Environments/KoreanBuildings/BuildingA"
MESH_DIR = DEST + "/Meshes"
MAT_DIR = DEST + "/Materials"

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P = unreal.log

M_TO_CM = 100.0
MIRROR_Y = True

# 지금 FBX 는 20000 으로 들어온다. 0.01 을 곱해 200 으로 맞춘다.
UNIFORM_SCALE = 0.01

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

# 통행에 걸리면 안 되는 장식 — 충돌 없음
NO_COLLISION = ("Deco_Awning_200", "Deco_Gutter_200", "Deco_GasPipe_200",
                "Deco_Curtain_100", "Deco_Floor_Tile_100", "SM_Window_Frame")

# 물리적 장애물이 맞는 소품 — 박스 하나만
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


def sms():
    try:
        return unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception:
        return None


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


def strip_collision(mesh):
    sub = sms()
    try:
        if sub is not None:
            sub.remove_collisions(mesh)
        else:
            unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
        return True
    except Exception:
        return False


def add_box(mesh):
    sub = sms()
    try:
        if sub is not None:
            sub.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
        else:
            unreal.EditorStaticMeshLibrary.add_simple_collisions(
                mesh, unreal.ScriptCollisionShapeType.BOX)
        return True
    except Exception:
        return False


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


def cvar(cmd):
    try:
        unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception:
        P("[FIX5] console FAILED: %s" % cmd)


def reimport(files):
    P("[FIX5] --- 1. re-import (legacy, import_uniform_scale=%.2f) ---" % UNIFORM_SCALE)
    cvar("Interchange.FeatureFlags.Import.FBX 0")
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
    d.set_editor_property("import_uniform_scale", UNIFORM_SCALE)
    d.set_editor_property("normal_import_method",
                          unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = os.path.join(FBX_DIR, f)
        t.destination_path = MESH_DIR
        t.automated = True
        t.replace_existing = True
        t.save = True
        t.options = ui
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    cvar("Interchange.FeatureFlags.Import.FBX 1")


def fix_meshes(files):
    P("[FIX5] --- 2. verify size / collision policy / materials ---")
    P("[FIX5] %-28s %-20s %-12s %s" % ("mesh", "size uu", "UCX (want)", "policy"))
    P("[FIX5] " + "-" * 72)
    bad_size = bad_ucx = 0
    for f in files:
        name = os.path.splitext(f)[0]
        path = "%s/%s" % (MESH_DIR, name)
        try:
            m = EAL.load_asset(path)
            if not isinstance(m, unreal.StaticMesh):
                P("[FIX5] %-28s NOT A STATIC MESH" % name)
                continue
            assign(m)

            if name in NO_COLLISION:
                policy = "none"
                strip_collision(m)
                want_ucx = 0
            elif name in BOX_COLLISION:
                policy = "box"
                strip_collision(m)      # 재임포트마다 쌓이는 자동 훌을 먼저 지운다
                add_box(m)
                want_ucx = 1
            else:
                policy = "authored UCX"
                want_ucx = EXPECT.get(name, (None, 0))[1]

            EAL.save_asset(path)

            bb = m.get_bounding_box()
            got = (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)
            want_size = EXPECT.get(name, (None, 0))[0]
            h = hulls(m)
            size_ok = want_size is None or all(
                abs(got[i] - want_size[i]) < 3 for i in range(3))
            ucx_ok = (h == want_ucx)
            if not size_ok:
                bad_size += 1
            if not ucx_ok:
                bad_ucx += 1
            P("[FIX5] %-28s %-20s %-12s %s"
              % (name,
                 "%.0fx%.0fx%.0f%s" % (got + ("" if size_ok else "  !!",)),
                 "%d (%d)%s" % (h, want_ucx, "" if ucx_ok else " !!"),
                 policy))
        except Exception:
            P("[FIX5] %-28s !! %s"
              % (name, traceback.format_exc().strip().splitlines()[-1]))
    P("[FIX5] " + "-" * 72)
    P("[FIX5] size mismatches: %d / %d      collision mismatches: %d / %d"
      % (bad_size, len(files), bad_ucx, len(files)))
    return bad_size


def replace_actors():
    """placements.json 기준으로 액터 위치/회전을 다시 쓴다. 없으면 스폰한다."""
    P("[FIX5] --- 3. restore placement from placements.json ---")
    if not os.path.exists(MANIFEST):
        P("[FIX5]   manifest not found: %s" % MANIFEST)
        return
    with open(MANIFEST) as fh:
        placements = load_current_json_file(fh)["placements"]

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    have = {}
    for a in eas.get_all_level_actors():
        if str(a.get_folder_path()) == "OldKoreanBuildingA":
            have[a.get_actor_label()] = a

    moved = spawned = missing_mesh = 0
    for p in placements:
        x, y, z = p["loc_m"]
        sy = -1.0 if MIRROR_Y else 1.0
        loc = unreal.Vector(x * M_TO_CM, sy * y * M_TO_CM, z * M_TO_CM)
        yaw = -p["yaw_deg"] if MIRROR_Y else p["yaw_deg"]
        rot = unreal.Rotator(0.0, 0.0, yaw)
        a = have.get(p["instance"])
        if a is None:
            mesh = EAL.load_asset("%s/%s" % (MESH_DIR, p["module"]))
            if mesh is None:
                missing_mesh += 1
                continue
            a = eas.spawn_actor_from_object(mesh, loc, rot)
            if a is None:
                continue
            a.set_actor_label(p["instance"])
            a.set_folder_path("OldKoreanBuildingA")
            spawned += 1
        else:
            a.set_actor_location(loc, False, True)
            a.set_actor_rotation(rot, False)
            a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
            moved += 1
    P("[FIX5]   repositioned %d, spawned %d, missing mesh %d"
      % (moved, spawned, missing_mesh))

    acts = [a for a in eas.get_all_level_actors()
            if str(a.get_folder_path()) == "OldKoreanBuildingA"]
    mn = [1e18] * 3
    mx = [-1e18] * 3
    worst = []
    for a in acts:
        loc = a.get_actor_location()
        o, e = a.get_actor_bounds(False)
        worst.append((max(abs(o.x - loc.x), abs(o.y - loc.y), abs(o.z - loc.z)),
                      a.get_actor_label(), loc))
        for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            mn[i] = min(mn[i], oc - ec)
            mx[i] = max(mx[i], oc + ec)
    worst.sort(reverse=True)
    P("[FIX5]   actors=%d  bounds min=%s max=%s"
      % (len(acts), [round(v) for v in mn], [round(v) for v in mx]))
    P("[FIX5]   overall size = %s uu   (정상이면 약 [800, 400, 655])"
      % [round(mx[i] - mn[i]) for i in range(3)])
    for d, lab, loc in worst[:4]:
        P("[FIX5]     %-26s |centre-loc|=%5.0f loc=(%.0f,%.0f,%.0f)"
          % (lab, d, loc.x, loc.y, loc.z))


def run():
    P("=" * 80)
    files = sorted(f for f in os.listdir(FBX_DIR) if f.lower().endswith(".fbx"))
    reimport(files)
    if fix_meshes(files) == 0:
        replace_actors()
    else:
        P("[FIX5] 크기가 아직 맞지 않아 배치 복구는 건너뛴다.")
        P("[FIX5] 위 표의 size 열 실제값을 200 으로 나눈 값이 남은 배율 오차다.")
    P("=" * 80)


run()
