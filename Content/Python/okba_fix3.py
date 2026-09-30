# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\okba_fix3.py
"""OldKoreanBuildingA: 머티리얼 컴파일 실패 수정 + 장식물 충돌 정리.

    import okba_fix3
    다시:  import importlib, okba_fix3; importlib.reload(okba_fix3)

fix2 로 UCX 14/14 는 해결됐다. 남은 문제 두 가지.

1) 벽이 아직 체크무늬인 진짜 이유 — 텍스처가 아니라 셰이더 컴파일 실패
   fix2 로그:
     M_Brick: Failed to compile Material ... Default Material will be used
     (Node TextureSample) Sampler type is Linear Color, should be Masks
                          for T_Brick_Roughness
   Roughness 텍스처는 TC_MASKS 로 임포트해 놓고 TextureSample 노드의
   sampler_type 은 LINEAR_COLOR 로 줬다. 둘이 어긋나면 머티리얼이 컴파일되지
   않고, 언리얼이 그 자리에 엔진 기본 머티리얼(회색 체크무늬)을 물린다.
   즉 텍스처는 처음부터 제대로 붙어 있었고(BaseColor=ok), 셰이더가 없었던 것.
   -> sampler_type 을 SAMPLERTYPE_MASKS 로 맞춘다.

2) 장식물에 생긴 불필요한 충돌체
   레거시 임포터가 UCX 없는 모듈에도 훌을 하나씩 만들었다. 대부분 무해하지만
   어닝은 z=1.68~2.10m 에 0.87m 튀어나와 있어서, 캡슐 높이 1.76m 인 기본
   캐릭터의 머리가 상가 입구에서 걸린다. 통행에 걸릴 이유가 없는 장식 6종은
   충돌을 지운다. 드럼통/양동이/화분/실외기/계량기함/손수레/파고라는 물리적
   장애물이 맞으니 그대로 둔다.
"""
import traceback
import unreal

DEST = "/Game/Constellation/Environments/KoreanBuildings/BuildingA"
MESH_DIR = DEST + "/Meshes"
TEX_DIR = DEST + "/Textures"
MAT_DIR = DEST + "/Materials"

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
P = unreal.log

# 텍스처 세트를 쓰는 머티리얼만 다시 만든다. 단색 머티리얼은 멀쩡하므로 건드리지 않는다.
TEXTURED = {
    "MI_Brick":            ("Brick",     None,                0.0),
    "MI_Concrete":         ("Concrete",  None,                0.0),
    "MI_Plaster":          ("Plaster",   None,                0.0),
    "MI_Tile":             ("Tile",      None,                0.0),
    "MI_Wood":             ("Wood",      None,                0.0),
    "MI_Trim":             ("Wood",      (0.45, 0.34, 0.24),  0.0),
    "MI_Metal_DarkGrey":   ("Metal",     (0.35, 0.35, 0.38),  0.85),
    "MI_Metal_DarkGrey2":  ("Metal",     (0.45, 0.45, 0.48),  0.7),
    "MI_Metal_Galvanized": ("Metal",     (1.60, 1.62, 1.65),  0.9),
}

# 통행에 걸리면 안 되는 장식물 — 충돌을 지운다
NO_COLLISION = (
    "Deco_Awning_200",       # 입구 위 1.68~2.10m, 캡슐 1.76m 와 부딪힌다
    "Deco_Gutter_200",
    "Deco_GasPipe_200",
    "Deco_Curtain_100",
    "Deco_Floor_Tile_100",
    "SM_Window_Frame",
)

# 이름 -> 슬롯이 참조할 머티리얼
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


def tex(setname, kind):
    return EAL.load_asset("%s/T_%s_%s" % (TEX_DIR, setname, kind))


def rebuild(slot_name, spec):
    tex_set, tint, metallic = spec
    mat_name = "M_" + slot_name.replace("MI_", "")
    mat_path = "%s/%s" % (MAT_DIR, mat_name)
    if EAL.does_asset_exist(mat_path):
        EAL.delete_asset(mat_path)
    mat = AT.create_asset(mat_name, MAT_DIR, unreal.Material,
                          unreal.MaterialFactoryNew())

    # BaseColor — sRGB, 기본 COLOR 샘플러
    base = MEL.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -820, 0)
    base.texture = tex(tex_set, "BaseColor")
    if tint:
        mul = MEL.create_material_expression(
            mat, unreal.MaterialExpressionMultiply, -520, 0)
        const = MEL.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -700, 160)
        const.constant = unreal.LinearColor(tint[0], tint[1], tint[2], 1.0)
        MEL.connect_material_expressions(base, "RGB", mul, "A")
        MEL.connect_material_expressions(const, "", mul, "B")
        MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        MEL.connect_material_property(base, "RGB",
                                      unreal.MaterialProperty.MP_BASE_COLOR)

    # Roughness — 텍스처가 TC_MASKS 로 임포트돼 있으므로 샘플러도 MASKS 여야 한다.
    # 여기가 어긋나 있어서 지금까지 머티리얼이 통째로 컴파일 실패했다.
    rough = MEL.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -820, 300)
    rough.texture = tex(tex_set, "Roughness")
    rough.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    MEL.connect_material_property(rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    # Normal — TC_NORMALMAP + NORMAL 샘플러 (이건 원래 맞았다)
    nrm = MEL.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -820, 600)
    nrm.texture = tex(tex_set, "Normal")
    nrm.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    MEL.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)

    if metallic:
        m = MEL.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -520, 380)
        m.r = metallic
        MEL.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)

    MEL.recompile_material(mat)
    EAL.save_asset(mat_path)
    return mat_path


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
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        sub.remove_collisions(mesh)
        return True
    except Exception:
        pass
    try:
        unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
        return True
    except Exception:
        return False


def run():
    P("=" * 74)

    # ---- 1. 텍스처 머티리얼 재빌드 --------------------------------------
    P("[FIX3] --- 1. rebuild textured materials (sampler = Masks) ---")
    for slot, spec in sorted(TEXTURED.items()):
        try:
            rebuild(slot, spec)
            P("[FIX3]   %-22s rebuilt" % slot)
        except Exception:
            P("[FIX3]   %-22s !! %s"
              % (slot, traceback.format_exc().strip().splitlines()[-1]))
    P("[FIX3] 위 블록에 'Failed to compile Material' 경고가 없으면 성공이다.")

    # ---- 2. 슬롯 재연결 + 장식물 충돌 정리 -------------------------------
    P("[FIX3] --- 2. reassign slots / tidy collision ---")
    P("[FIX3] %-30s %-6s %-8s %s" % ("mesh", "UCX", "action", "slots"))
    P("[FIX3] " + "-" * 62)
    assets = sorted(EAL.list_assets(MESH_DIR, recursive=False))
    n_mat = n_strip = 0
    for path in assets:
        try:
            mesh = EAL.load_asset(path)
            if not isinstance(mesh, unreal.StaticMesh):
                continue
            name = mesh.get_name()

            slots = mesh.get_editor_property("static_materials")
            new = []
            changed = 0
            for slot in slots:
                key = base_slot_name(slot.get_editor_property("material_slot_name"))
                ns = unreal.StaticMaterial()
                ns.set_editor_property(
                    "material_slot_name",
                    slot.get_editor_property("material_slot_name"))
                try:
                    ns.set_editor_property(
                        "imported_material_slot_name",
                        slot.get_editor_property("imported_material_slot_name"))
                except Exception:
                    pass
                target = SLOT_TO_MAT.get(key)
                mat = (EAL.load_asset(MAT_DIR + "/" + target)
                       if target and EAL.does_asset_exist(MAT_DIR + "/" + target)
                       else None)
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
                n_mat += 1

            action = "-"
            if name in NO_COLLISION:
                action = "stripped" if strip_collision(mesh) else "STRIP FAILED"
                if action == "stripped":
                    n_strip += 1

            EAL.save_asset(path)
            P("[FIX3] %-30s %-6d %-8s %d/%d"
              % (name, hulls(mesh), action, changed, len(new)))
        except Exception:
            P("[FIX3] %-30s !! %s"
              % (path, traceback.format_exc().strip().splitlines()[-1]))

    P("[FIX3] " + "-" * 62)
    P("[FIX3] materials reassigned: %d meshes,  collision stripped: %d/%d"
      % (n_mat, n_strip, len(NO_COLLISION)))
    P("[FIX3] 뷰포트에서 벽돌/콘크리트/회벽 텍스처가 보이면 끝이다.")
    P("=" * 74)


run()
