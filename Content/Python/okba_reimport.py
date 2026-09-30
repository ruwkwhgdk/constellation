# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_reimport.py
"""OldKoreanBuildingA 재임포트 (v3).

    import okba_reimport
    다시 돌릴 때:  import importlib, okba_reimport; importlib.reload(okba_reimport)

v2 에서 못 고친 두 가지를 블렌더 쪽에서 잡고 FBX 를 새로 뽑았다.

  1) 건물이 흩어진 원인
     마스터 blend 는 29개 모듈을 5m 간격 진열대(contact sheet)로 늘어놓고
     저장돼 있었고, FBX 를 그 blend 에서 뽑았기 때문에 진열 오프셋이 오브젝트
     트랜스폼째로 FBX 에 구워졌다. 액터 loc 은 맞는데 실제 메시가 최대 32m 씩
     밀려 있었던 이유. -> 익스포트 직전에 모든 모듈을 자기 원점으로 되돌린다.

  2) 충돌체가 0개였던 원인
     UCX 헐이 들어있는 Collision 컬렉션이 뷰포트에서 숨김 상태였고,
     블렌더의 context.selected_objects 는 숨겨진 오브젝트를 빼고 준다.
     use_selection 익스포트가 UCX 를 통째로 빼먹었다 — 즉 FBX 안에 애초에
     충돌체가 없었다. 임포터 옵션 문제가 아니었다. -> 숨김 해제 후 재익스포트.
     이제 13개 모듈에 UCX 총 25개가 들어있다 (나머지 16개는 소품이라 없는 게 정상).

이 스크립트는 새 FBX 를 덮어쓰기 임포트하고, 머티리얼을 다시 붙이고,
액터의 loc 과 실제 바운즈 중심이 일치하는지(=흩어짐이 잡혔는지) 검증한다.
"""
import os
import traceback
import unreal

SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA\fbx"
DEST = "/Game/Constellation/Environments/KoreanBuildings/BuildingA"
MESH_DIR = DEST + "/Meshes"
MAT_DIR = DEST + "/Materials"

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P = unreal.log

# 예전 임포트가 만든 진열대 통짜 메시. 이제 안 쓰므로 지운다.
STALE = ("ModularKit_Core", "ModularKit_Props", "ModularKit_Pass3")

# UCX 를 가진 13개 모듈 -> 기대 헐 개수. 검증용.
EXPECT_UCX = {
    "SM_Wall_Straight_200": 1, "SM_Wall_Corner_200": 2, "SM_Wall_Window_200": 1,
    "SM_Wall_Door_200": 3, "SM_Shopfront_Door_200": 3,
    "SM_Wall_Partition_200": 1, "SM_Wall_Partition_Door_200": 3,
    "SM_Slab_Straight_200": 1, "SM_Slab_Corner_200": 3,
    "SM_Stair_Interior_300": 3, "Furn_Stair_Steel_300": 1,
    "Furn_Stair_Steel_600": 1, "SM_Door_Leaf_100": 1, "Furn_Railing_200": 1,
}

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
    """재임포트 때 붙는 _001 / _002 접미사를 떼어 매핑 키로 되돌린다."""
    s = str(name)
    while len(s) > 4 and s[-4] == "_" and s[-3:].isdigit():
        s = s[:-4]
    return s


def options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
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


def hulls(mesh):
    try:
        bs = mesh.get_editor_property("body_setup")
        if bs is None:
            return 0
        return len(bs.get_editor_property("agg_geom").get_editor_property("convex_elems"))
    except Exception:
        return -1


def assign_materials(mesh):
    slots = mesh.get_editor_property("static_materials")
    new = []
    changed = 0
    for slot in slots:
        key = base_slot_name(slot.get_editor_property("material_slot_name"))
        target = SLOT_TO_MAT.get(key)
        ns = unreal.StaticMaterial()
        ns.set_editor_property("material_slot_name",
                               slot.get_editor_property("material_slot_name"))
        try:
            ns.set_editor_property(
                "imported_material_slot_name",
                slot.get_editor_property("imported_material_slot_name"))
        except Exception:
            pass
        mat = None
        if target and EAL.does_asset_exist(MAT_DIR + "/" + target):
            mat = EAL.load_asset(MAT_DIR + "/" + target)
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


def run():
    P("=" * 78)

    # ---- 0. 옛 진열대 통짜 메시 정리 -------------------------------------
    for s in STALE:
        p = "%s/%s" % (MESH_DIR, s)
        if EAL.does_asset_exist(p):
            try:
                EAL.delete_asset(p)
                P("[REIMPORT] deleted stale asset %s" % s)
            except Exception:
                P("[REIMPORT] could not delete %s (아마 레벨에서 참조 중)" % s)

    files = sorted(f for f in os.listdir(SRC)
                   if f.lower().endswith(".fbx")
                   and os.path.splitext(f)[0] not in STALE)
    P("[REIMPORT] %d fbx" % len(files))

    ui = options()
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = os.path.join(SRC, f)
        t.destination_path = MESH_DIR
        t.automated = True
        t.replace_existing = True
        t.save = True
        t.options = ui
        tasks.append(t)
    AT.import_asset_tasks(tasks)

    P("[REIMPORT] %-30s %-18s %-9s %s" % ("mesh", "size uu", "UCX", "materials"))
    P("[REIMPORT] " + "-" * 66)
    ucx_ok = ucx_bad = 0
    for f in files:
        name = os.path.splitext(f)[0]
        path = "%s/%s" % (MESH_DIR, name)
        try:
            m = EAL.load_asset(path)
            if not isinstance(m, unreal.StaticMesh):
                P("[REIMPORT] %-30s  NOT A STATIC MESH" % name)
                continue
            n = assign_materials(m)
            EAL.save_asset(path)
            h = hulls(m)
            want = EXPECT_UCX.get(name, 0)
            mark = "ok" if h == want else "WANT %d" % want
            if want:
                if h == want:
                    ucx_ok += 1
                else:
                    ucx_bad += 1
            bb = m.get_bounding_box()
            size = "%.0fx%.0fx%.0f" % (bb.max.x - bb.min.x,
                                       bb.max.y - bb.min.y,
                                       bb.max.z - bb.min.z)
            P("[REIMPORT] %-30s %-18s %d %-7s %d" % (name, size, h, mark, n))
        except Exception:
            P("[REIMPORT] %-30s !! %s"
              % (name, traceback.format_exc().strip().splitlines()[-1]))
    P("[REIMPORT] " + "-" * 66)
    P("[REIMPORT] UCX: %d/%d modules match the expected hull count (bad %d)"
      % (ucx_ok, len(EXPECT_UCX), ucx_bad))

    # ---- 흩어짐 검증: 액터 loc 과 바운즈 중심이 붙어 있어야 한다 ----------
    P("[REIMPORT] scatter check — |boundsCentre - loc| per actor:")
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        acts = [a for a in eas.get_all_level_actors()
                if str(a.get_folder_path()) == "OldKoreanBuildingA"]
        rows = []
        mn = [1e18] * 3
        mx = [-1e18] * 3
        for a in acts:
            o, e = a.get_actor_bounds(False)
            loc = a.get_actor_location()
            d = max(abs(o.x - loc.x), abs(o.y - loc.y), abs(o.z - loc.z))
            rows.append((d, a.get_actor_label(), loc, o))
            for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
                mn[i] = min(mn[i], oc - ec)
                mx[i] = max(mx[i], oc + ec)
        rows.sort(reverse=True)
        P("[REIMPORT]   actors=%d   worst offsets:" % len(acts))
        for d, lab, loc, o in rows[:6]:
            P("[REIMPORT]     %-26s d=%6.0f uu  loc=(%.0f,%.0f,%.0f) centre=(%.0f,%.0f,%.0f)"
              % (lab, d, loc.x, loc.y, loc.z, o.x, o.y, o.z))
        P("[REIMPORT]   building bounds  min=%s  max=%s"
          % ([round(v) for v in mn], [round(v) for v in mx]))
        P("[REIMPORT]   overall size = %s uu   (기대 약 [800, 400, 655])"
          % [round(mx[i] - mn[i]) for i in range(3)])
    except Exception:
        P("[REIMPORT]   !! %s" % traceback.format_exc().strip().splitlines()[-1])
    P("=" * 78)


run()
