# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_fix1.py
"""OldKoreanBuildingA: 머티리얼 재할당 + 메시/액터 이상치 진단.

    import okba_fix1
    import importlib, okba_fix1; importlib.reload(okba_fix1)

1) 29개 메시 전부의 크기 / UCX 개수 / 슬롯 상태를 표로 찍는다.
2) 머티리얼을 제대로 재할당한다 (StaticMaterial 구조체를 새로 만들어 넣는다 —
   get_editor_property 로 받은 슬롯은 복사본이라 그 자리에서 고쳐봐야 반영 안 됨).
3) 건물 푸트프린트(가로 800 x 세로 400 uu)를 크게 벗어나는 액터를 찾아낸다.
"""
import traceback
import unreal

DEST = "/Game/Constellation/Environments/KoreanBuildings/BuildingA"
MESH_DIR = DEST + "/Meshes"
MAT_DIR = DEST + "/Materials"

EAL = unreal.EditorAssetLibrary
P = unreal.log

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


def mesh_size(mesh):
    try:
        bb = mesh.get_bounding_box()
        return (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)
    except Exception:
        try:
            e = mesh.get_bounds().box_extent
            return (e.x * 2.0, e.y * 2.0, e.z * 2.0)
        except Exception:
            return None


def hull_count(mesh):
    try:
        bs = mesh.get_editor_property("body_setup")
        if bs is None:
            return 0
        agg = bs.get_editor_property("agg_geom")
        return len(agg.get_editor_property("convex_elems"))
    except Exception:
        return -1


def fix_materials(mesh):
    """슬롯 구조체를 새로 만들어 통째로 교체한다."""
    slots = mesh.get_editor_property("static_materials")
    new = []
    changed = 0
    for slot in slots:
        name = str(slot.get_editor_property("material_slot_name"))
        target = SLOT_TO_MAT.get(name)
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
            ns.set_editor_property(
                "material_interface", slot.get_editor_property("material_interface"))
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
    assets = [a for a in EAL.list_assets(MESH_DIR, recursive=False)]
    P("[FIX] meshes found: %d" % len(assets))
    P("[FIX] %-30s %-22s %5s  %s" % ("mesh", "size uu", "UCX", "slots"))
    P("[FIX] " + "-" * 72)

    oversized = []
    total_fixed = 0
    for path in sorted(assets):
        try:
            m = EAL.load_asset(path)
            if not isinstance(m, unreal.StaticMesh):
                continue
            name = m.get_name()
            s = mesh_size(m)
            h = hull_count(m)
            n = fix_materials(m)
            total_fixed += 1 if n else 0
            if n:
                EAL.save_asset(path)
            slot_names = ",".join(
                str(sl.get_editor_property("material_slot_name"))
                for sl in m.get_editor_property("static_materials"))
            size_txt = ("%.0f x %.0f x %.0f" % s) if s else "??"
            P("[FIX] %-30s %-22s %5s  %s" % (name, size_txt, h, slot_names))
            # 어떤 모듈도 한 변이 10m(1000uu)를 넘지 않아야 한다
            if s and max(s) > 1000:
                oversized.append((name, s))
        except Exception:
            P("[FIX]   !! %s : %s" % (path, traceback.format_exc().strip().splitlines()[-1]))

    P("[FIX] " + "-" * 72)
    P("[FIX] materials reassigned on %d mesh(es)" % total_fixed)
    if oversized:
        P("[FIX] OVERSIZED MESHES (this is what scatters the building):")
        for name, s in oversized:
            P("[FIX]    %-30s %.0f x %.0f x %.0f uu" % (name, s[0], s[1], s[2]))
    else:
        P("[FIX] no oversized mesh assets")

    # ---- 액터 이상치 -----------------------------------------------------
    P("[FIX] actors far outside the 800 x 400 footprint:")
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        acts = [a for a in eas.get_all_level_actors()
                if str(a.get_folder_path()) == "OldKoreanBuildingA"]
        flagged = 0
        for a in acts:
            o, e = a.get_actor_bounds(False)
            if max(e.x, e.y, e.z) > 500 or o.x < -700 or o.x > 1500 or o.y < -1100 or o.y > 700:
                loc = a.get_actor_location()
                P("[FIX]    %-26s loc=(%.0f,%.0f,%.0f) extent=(%.0f,%.0f,%.0f)"
                  % (a.get_actor_label(), loc.x, loc.y, loc.z, e.x, e.y, e.z))
                flagged += 1
                if flagged >= 15:
                    P("[FIX]    ... (more)")
                    break
        if flagged == 0:
            P("[FIX]    none")
    except Exception:
        P("[FIX]   !! actor scan: %s" % traceback.format_exc().strip().splitlines()[-1])
    P("=" * 78)


run()
