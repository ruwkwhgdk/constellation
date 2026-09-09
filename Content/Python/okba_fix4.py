# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_fix4.py
"""OldKoreanBuildingA: 1/100 스케일 복구 + UCX + 머티리얼 (v1).

    import okba_fix4
    다시:  import importlib, okba_fix4; importlib.reload(okba_fix4)

무슨 일이 있었나
  fix2 에서 UCX 를 살리려고 레거시 FBX 임포터로 바꿨다. UCX 는 살았지만,
  블렌더가 내보낸 FBX 는 정점을 미터(2.00)로 저장하고 100배 환산을 파일
  헤더의 UnitScaleFactor 에만 넣어 두는 형식이었다. Interchange 는 그 값을
  읽지만 레거시 임포터는 무시한다 -> 메시가 1/100 로 들어왔다.
  액터 좌표는 미터 간격 그대로였으니, 작아진 조각들이 허공에 흩뿌려져 보였다.
  fix2 에서 크기 검증 컬럼을 뺐던 탓에 그 자리에서 못 잡았다.

무엇을 고쳤나
  블렌더에서 단위 환산을 지오메트리에 직접 구워 다시 내보냈다. 이제 FBX 안의
  정점이 문자 그대로 센티미터다(200.00 x 20.00 x 300.00, UnitScaleFactor=1.0).
  임포터가 어느 쪽이든 같은 크기로 읽는다.

이 스크립트가 하는 일
  1. 새 FBX 29개를 레거시 임포터로 다시 임포트 (UCX 를 위해)
  2. 크기와 UCX 개수를 둘 다 검증해서 표로 찍는다  <- 이번엔 크기를 뺀 채 넘어가지 않는다
  3. 머티리얼 재할당 (재임포트하면 슬롯이 초기화된다)
  4. 통행에 걸리면 안 되는 장식물 6종의 충돌 제거
  5. 레벨 액터의 위치 vs 실제 바운즈 대조
"""
import os
import traceback
import unreal

SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA\fbx"
DEST = "/Game/Environment/OldKoreanBuildingA"
MESH_DIR = DEST + "/Meshes"
MAT_DIR = DEST + "/Materials"

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P = unreal.log

# 이름 -> (기대 크기 uu, 기대 UCX 개수)
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
    d.set_editor_property("convert_scene", True)
    d.set_editor_property("normal_import_method",
                          unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    return ui


def hulls(mesh):
    try:
        bs = mesh.get_editor_property("body_setup")
        if bs is None:
            return 0
        return len(bs.get_editor_property("agg_geom")
                   .get_editor_property("convex_elems"))
    except Exception:
        return -1


def strip_collision(mesh):
    try:
        unreal.get_editor_subsystem(
            unreal.StaticMeshEditorSubsystem).remove_collisions(mesh)
        return True
    except Exception:
        pass
    try:
        unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
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
        P("[FIX4]   console FAILED: %s" % cmd)


def run():
    P("=" * 80)
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".fbx"))
    P("[FIX4] re-importing %d fbx through the legacy importer" % len(files))

    cvar("Interchange.FeatureFlags.Import.FBX 0")
    ui = legacy_options()
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
    cvar("Interchange.FeatureFlags.Import.FBX 1")

    P("[FIX4] %-28s %-22s %-16s %s" % ("mesh", "size uu (want)", "UCX (want)", "note"))
    P("[FIX4] " + "-" * 74)
    bad_size = bad_ucx = 0
    n_strip = 0
    for f in files:
        name = os.path.splitext(f)[0]
        path = "%s/%s" % (MESH_DIR, name)
        try:
            m = EAL.load_asset(path)
            if not isinstance(m, unreal.StaticMesh):
                P("[FIX4] %-28s NOT A STATIC MESH" % name)
                continue
            assign(m)
            note = ""
            if name in NO_COLLISION:
                note = "stripped" if strip_collision(m) else "STRIP FAILED"
                if note == "stripped":
                    n_strip += 1
            EAL.save_asset(path)

            bb = m.get_bounding_box()
            got = (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)
            want_size, want_ucx = EXPECT.get(name, (None, 0))
            h = hulls(m)
            if name in NO_COLLISION:
                want_ucx = 0
            size_ok = want_size is None or all(
                abs(got[i] - want_size[i]) < 3 for i in range(3))
            ucx_ok = (h == want_ucx)
            if not size_ok:
                bad_size += 1
            if not ucx_ok:
                bad_ucx += 1
            P("[FIX4] %-28s %-22s %-16s %s%s%s"
              % (name,
                 "%.0fx%.0fx%.0f" % got + ("" if size_ok else " !!"),
                 "%d (%d)%s" % (h, want_ucx, "" if ucx_ok else " !!"),
                 note,
                 "" if size_ok else "  SIZE WRONG",
                 "" if ucx_ok else "  UCX WRONG"))
        except Exception:
            P("[FIX4] %-28s !! %s"
              % (name, traceback.format_exc().strip().splitlines()[-1]))

    P("[FIX4] " + "-" * 74)
    P("[FIX4] size mismatches: %d / %d      UCX mismatches: %d / %d"
      % (bad_size, len(files), bad_ucx, len(files)))
    P("[FIX4] decorative collision stripped: %d / %d" % (n_strip, len(NO_COLLISION)))

    # ---- 레벨에서 실제로 어떻게 놓였나 -----------------------------------
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        acts = [a for a in eas.get_all_level_actors()
                if str(a.get_folder_path()) == "OldKoreanBuildingA"]
        mn = [1e18] * 3
        mx = [-1e18] * 3
        worst = []
        for a in acts:
            loc = a.get_actor_location()
            o, e = a.get_actor_bounds(False)
            worst.append((max(abs(o.x - loc.x), abs(o.y - loc.y), abs(o.z - loc.z)),
                          a.get_actor_label(), loc, o))
            for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
                mn[i] = min(mn[i], oc - ec)
                mx[i] = max(mx[i], oc + ec)
        worst.sort(reverse=True)
        P("[FIX4] actors=%d  bounds min=%s max=%s"
          % (len(acts), [round(v) for v in mn], [round(v) for v in mx]))
        P("[FIX4] overall size = %s uu   (정상이면 약 [800, 400, 655])"
          % [round(mx[i] - mn[i]) for i in range(3)])
        for d, lab, loc, o in worst[:5]:
            P("[FIX4]   %-26s |centre-loc|=%5.0f  loc=(%.0f,%.0f,%.0f)"
              % (lab, d, loc.x, loc.y, loc.z))
    except Exception:
        P("[FIX4] !! %s" % traceback.format_exc().strip().splitlines()[-1])
    P("=" * 80)


run()
