# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_diag.py
"""OldKoreanBuildingA 임포트/배치 진단 (v2).

에디터 Python 콘솔에서 한 줄로:
    import okba_diag
다시 돌릴 때:
    import importlib; importlib.reload(okba_diag)

각 항목을 개별 try 로 감싸서, API 이름이 하나 틀려도 나머지 진단은 계속 나온다.
"""
import json
import os
import traceback
import unreal

DEST = "/Game/Environment/OldKoreanBuildingA"
MESH_DIR = DEST + "/Meshes"
MAT_DIR = DEST + "/Materials"
MANIFEST = (r"C:\Users\User\Documents\UnrealProjects\Constellation"
            r"\ArtSource\OldKoreanBuildingA\placements.json")

EAL = unreal.EditorAssetLibrary
P = unreal.log


def _err(where):
    P("[DIAG]   !! %s failed: %s" % (where, traceback.format_exc().strip().splitlines()[-1]))


def mesh_size(mesh):
    """StaticMesh 의 로컬 바운즈 크기를 여러 API 중 되는 것으로 구한다."""
    try:
        bb = mesh.get_bounding_box()
        return (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)
    except Exception:
        pass
    try:
        b = mesh.get_bounds()                       # unreal.BoxSphereBounds
        e = b.box_extent
        return (e.x * 2.0, e.y * 2.0, e.z * 2.0)
    except Exception:
        pass
    return None


def run():
    P("=" * 64)

    # ---- 1. 메시 스케일 --------------------------------------------------
    P("[DIAG] 1. mesh asset scale")
    m = None
    try:
        m = EAL.load_asset(MESH_DIR + "/SM_Wall_Straight_200")
        if m is None:
            P("[DIAG]   SM_Wall_Straight_200 MISSING")
        else:
            s = mesh_size(m)
            if s is None:
                P("[DIAG]   could not read bounds by any API")
            else:
                P("[DIAG]   SM_Wall_Straight_200 = %.1f x %.1f x %.1f uu" % s)
                P("[DIAG]   expected 200 x 20 x 300  ->  ratio %.3f" % (s[0] / 200.0))
    except Exception:
        _err("mesh scale")

    # ---- 2. 충돌체 ------------------------------------------------------
    P("[DIAG] 2. collision (UCX)")
    try:
        if m is not None:
            bs = m.get_editor_property("body_setup")
            if bs is None:
                P("[DIAG]   body_setup = None  -> NO collision imported")
            else:
                agg = bs.get_editor_property("agg_geom")
                P("[DIAG]   convex hulls = %d  (expected 1 for this mesh)"
                  % len(agg.get_editor_property("convex_elems")))
    except Exception:
        _err("collision")

    # ---- 3. 머티리얼 ----------------------------------------------------
    P("[DIAG] 3. materials")
    try:
        for name in ("M_Brick", "M_Concrete", "M_Plaster", "M_Metal_DarkGrey"):
            P("[DIAG]   %-18s exists=%s"
              % (name, EAL.does_asset_exist(MAT_DIR + "/" + name)))
    except Exception:
        _err("material existence")
    try:
        if m is not None:
            slots = m.get_editor_property("static_materials")
            P("[DIAG]   SM_Wall_Straight_200 has %d slot(s)" % len(slots))
            for i, slot in enumerate(slots):
                mi = slot.get_editor_property("material_interface")
                P("[DIAG]     slot %d  name=%-22s material=%s"
                  % (i, slot.get_editor_property("material_slot_name"),
                     mi.get_name() if mi else "None"))
    except Exception:
        _err("material slots")

    # ---- 4. 스폰된 액터 --------------------------------------------------
    P("[DIAG] 4. spawned actors")
    acts = []
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        acts = [a for a in eas.get_all_level_actors()
                if str(a.get_folder_path()) == "OldKoreanBuildingA"]
        P("[DIAG]   actors in folder 'OldKoreanBuildingA' = %d" % len(acts))
    except Exception:
        _err("actor list")

    if acts:
        try:
            mn = [1e18] * 3
            mx = [-1e18] * 3
            for a in acts:
                o, e = a.get_actor_bounds(False)
                for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
                    mn[i] = min(mn[i], oc - ec)
                    mx[i] = max(mx[i], oc + ec)
            P("[DIAG]   bounds min  = %s" % [round(v) for v in mn])
            P("[DIAG]   bounds max  = %s" % [round(v) for v in mx])
            P("[DIAG]   overall size= %s uu   (expected about [800, 400, 655])"
              % [round(mx[i] - mn[i]) for i in range(3)])
        except Exception:
            _err("actor bounds")

        # ---- 5. 실제 배치 vs 매니페스트 기대값 --------------------------
        P("[DIAG] 5. actual vs expected placement")
        try:
            want = {}
            if os.path.exists(MANIFEST):
                with open(MANIFEST) as fh:
                    for p in json.load(fh)["placements"]:
                        want[p["instance"]] = p
            else:
                P("[DIAG]   manifest not found: " + MANIFEST)
            for a in acts[:5]:
                lab = a.get_actor_label()
                loc = a.get_actor_location()
                scl = a.get_actor_scale3d()
                yaw = a.get_actor_rotation().yaw
                w = want.get(lab)
                if w:
                    exp = "expect (%.0f, %.0f, %.0f) yaw %.0f" % (
                        w["loc_m"][0] * 100, -w["loc_m"][1] * 100,
                        w["loc_m"][2] * 100, -w["yaw_deg"])
                else:
                    exp = "no manifest entry for this label"
                P("[DIAG]   %-26s loc=(%.0f, %.0f, %.0f) scale=(%.2f,%.2f,%.2f) yaw=%.0f | %s"
                  % (lab, loc.x, loc.y, loc.z, scl.x, scl.y, scl.z, yaw, exp))
        except Exception:
            _err("placement compare")

    P("=" * 64)


run()
