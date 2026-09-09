# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_check.py
"""OldKoreanBuildingA 현재 상태 진단 — 읽기 전용. 아무것도 바꾸지 않는다.

    import okba_check
    다시:  import importlib, okba_check; importlib.reload(okba_check)

건물이 분해돼 보이는 원인 후보를 한 번에 구분해서 찍는다.
  A) 액터 위치가 틀어졌나          -> loc 목록과 전체 바운즈
  B) 메시 원점이 다시 밀렸나        -> |boundsCentre - loc| (0 에 가까워야 정상)
  C) 메시 자체가 커졌나/작아졌나    -> 에셋 로컬 바운즈 크기
  D) 액터가 메시를 잃었나           -> static mesh = None 인 액터
  E) 배치 매니페스트와 어긋났나      -> placements.json 기대값과 대조
"""
import json
import os
import traceback
import unreal

SRC = r"C:\Users\User\Documents\UnrealProjects\Constellation\ArtSource\OldKoreanBuildingA"
DEST = "/Game/Environment/OldKoreanBuildingA"
MESH_DIR = DEST + "/Meshes"
MANIFEST = os.path.join(SRC, "placements.json")

EAL = unreal.EditorAssetLibrary
P = unreal.log

EXPECT_SIZE = {          # 언리얼 단위(cm) 기준 기대 크기
    "SM_Wall_Straight_200":  (200, 20, 300),
    "SM_Wall_Corner_200":    (200, 200, 300),
    "SM_Wall_Window_200":    (200, 22, 300),
    "SM_Wall_Door_200":      (200, 22, 305),
    "SM_Slab_Straight_200":  (200, 200, 20),
    "SM_Slab_Corner_200":    (200, 200, 30),
    "SM_Stair_Interior_300": (102, 390, 395),
}


def mesh_of(actor):
    try:
        comp = actor.static_mesh_component
    except Exception:
        try:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        except Exception:
            return None
    if comp is None:
        return None
    try:
        return comp.static_mesh
    except Exception:
        return comp.get_editor_property("static_mesh")


def run():
    P("=" * 76)

    # ---- C) 메시 에셋 크기 ------------------------------------------------
    P("[CHK] --- mesh asset local size (uu) ---")
    for name, want in sorted(EXPECT_SIZE.items()):
        path = "%s/%s" % (MESH_DIR, name)
        try:
            m = EAL.load_asset(path)
            if m is None:
                P("[CHK]   %-24s MISSING ASSET" % name)
                continue
            bb = m.get_bounding_box()
            got = (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)
            ok = all(abs(got[i] - want[i]) < 3 for i in range(3))
            P("[CHK]   %-24s %6.0f x %6.0f x %6.0f   want %s  %s"
              % (name, got[0], got[1], got[2], want, "ok" if ok else "<<< WRONG"))
            P("[CHK]     local bounds min=(%.0f,%.0f,%.0f) max=(%.0f,%.0f,%.0f)"
              % (bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z))
        except Exception:
            P("[CHK]   %-24s !! %s"
              % (name, traceback.format_exc().strip().splitlines()[-1]))

    # ---- 액터 수집 --------------------------------------------------------
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        acts = [a for a in eas.get_all_level_actors()
                if str(a.get_folder_path()) == "OldKoreanBuildingA"]
    except Exception:
        P("[CHK] !! actor list: %s" % traceback.format_exc().strip().splitlines()[-1])
        return
    P("[CHK] --- actors in folder OldKoreanBuildingA: %d ---" % len(acts))

    # ---- D) 메시 잃은 액터 ------------------------------------------------
    orphan = [a.get_actor_label() for a in acts if mesh_of(a) is None]
    P("[CHK] actors with no static mesh: %d %s"
      % (len(orphan), orphan[:10] if orphan else ""))

    # ---- A/B) 위치와 바운즈 ------------------------------------------------
    rows = []
    mn = [1e18] * 3
    mx = [-1e18] * 3
    for a in acts:
        loc = a.get_actor_location()
        o, e = a.get_actor_bounds(False)
        d = max(abs(o.x - loc.x), abs(o.y - loc.y), abs(o.z - loc.z))
        m = mesh_of(a)
        rows.append((d, a.get_actor_label(), m.get_name() if m else "NONE",
                     loc, o, e, a.get_actor_scale3d(), a.get_actor_rotation().yaw))
        for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            mn[i] = min(mn[i], oc - ec)
            mx[i] = max(mx[i], oc + ec)

    P("[CHK] building bounds min=%s max=%s" % ([round(v) for v in mn],
                                               [round(v) for v in mx]))
    P("[CHK] overall size = %s uu   (정상이면 약 [800, 400, 655])"
      % [round(mx[i] - mn[i]) for i in range(3)])

    rows.sort(reverse=True)
    P("[CHK] --- worst |boundsCentre - loc| (0 에 가까워야 정상) ---")
    for d, lab, mesh, loc, o, e, s, yaw in rows[:10]:
        P("[CHK]   %-26s d=%6.0f mesh=%-24s loc=(%.0f,%.0f,%.0f) scale=(%.2f,%.2f,%.2f) yaw=%.0f"
          % (lab, d, mesh, loc.x, loc.y, loc.z, s.x, s.y, s.z, yaw))

    # ---- E) 매니페스트 대조 ------------------------------------------------
    P("[CHK] --- actual vs placements.json ---")
    if not os.path.exists(MANIFEST):
        P("[CHK]   manifest not found: %s" % MANIFEST)
    else:
        with open(MANIFEST) as fh:
            want = {p["instance"]: p for p in json.load(fh)["placements"]}
        bad = 0
        checked = 0
        for a in acts:
            w = want.get(a.get_actor_label())
            if not w:
                continue
            checked += 1
            loc = a.get_actor_location()
            ex = (w["loc_m"][0] * 100, -w["loc_m"][1] * 100, w["loc_m"][2] * 100)
            eyaw = -w["yaw_deg"]
            dl = max(abs(loc.x - ex[0]), abs(loc.y - ex[1]), abs(loc.z - ex[2]))
            dy = abs(((a.get_actor_rotation().yaw - eyaw) + 180) % 360 - 180)
            if dl > 1.0 or dy > 1.0:
                bad += 1
                if bad <= 10:
                    P("[CHK]   %-26s loc=(%.0f,%.0f,%.0f) expect=(%.0f,%.0f,%.0f) "
                      "yaw=%.0f expect=%.0f"
                      % (a.get_actor_label(), loc.x, loc.y, loc.z,
                         ex[0], ex[1], ex[2], a.get_actor_rotation().yaw, eyaw))
        P("[CHK]   compared %d actors, mismatched %d" % (checked, bad))
        missing = [k for k in want if k not in {a.get_actor_label() for a in acts}]
        if missing:
            P("[CHK]   in manifest but not in level (%d): %s"
              % (len(missing), missing[:10]))

    P("=" * 76)


run()
