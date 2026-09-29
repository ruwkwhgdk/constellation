"""Warm, low-frequency painted material pass on the maintained Tripo hall.

Reapply after refine_tripo_hall_structure.py. Source textures and mesh slots
remain intact; the maintained level receives explicit material overrides.
"""
import unreal as u
import json, runpy
from pathlib import Path

ROOT = Path(u.Paths.project_dir())
OUT = ROOT/'ArtSource/OvergrownHall/TripoReplacement/v004'
OUT.mkdir(parents=True, exist_ok=True)
D = '/Game/Environment/OvergrownHall/TripoFull'
MAP = D+'/Maps/L_OvergrownHall_TripoFull'
DEST = D+'/PaintedMaterials'
E = u.EditorAssetLibrary
ML = u.MaterialEditingLibrary
AT = u.AssetToolsHelpers.get_asset_tools()
L = u.get_editor_subsystem(u.LevelEditorSubsystem)
A = u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)

ids = [r['id'] for r in json.loads((OUT.parent/'v002/kit_manifest.json').read_text())]+['02','19']
materials = {}
settings = {}
for key in ids:
    foliage = key in ['16','17','18','19']
    metal = key in ['06','07','08','10','25']
    wood = key == '14'
    tint = (.30,.44,.12) if foliage else (.18,.25,.24) if metal else (.34,.28,.16) if wood else (.48,.44,.32)
    blend = .38 if foliage else .32 if metal or wood else .42
    normal_strength = .10 if foliage else .16
    bias = 2
    name = 'M_OH_Painted_'+key
    path = DEST+'/'+name
    mat = E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,DEST,u.Material,u.MaterialFactoryNew())
    mat.modify()
    mat.set_editor_property('two_sided',foliage)
    ML.delete_all_material_expressions(mat)

    def node(cls):
        return ML.create_material_expression(mat,cls)
    def scalar(value):
        n = node(u.MaterialExpressionConstant); n.r = value; return n
    def color(value):
        n = node(u.MaterialExpressionConstant3Vector); n.constant = u.LinearColor(*value,1); return n
    def wire(a,output,b,input):
        assert ML.connect_material_expressions(a,output,b,input)
    def prop(n,output,p):
        assert ML.connect_material_property(n,output,p)
    def sample(suffix):
        if key in ['02','19']:
            stem = 'Pillar' if key == '02' else 'Tree'
            texpath = '/Game/Environment/OvergrownHall/TripoReplacement/Textures/T_'+stem+'_'+suffix
        else:
            texpath = D+'/Textures/T_OH_'+key+'_'+suffix
        tex = E.load_asset(texpath); assert tex,texpath
        n = node(u.MaterialExpressionTextureSample)
        n.texture = tex
        n.sampler_type = u.MaterialSamplerType.SAMPLERTYPE_NORMAL if suffix == 'normal' else u.MaterialSamplerType.SAMPLERTYPE_COLOR
        n.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_BIAS)
        n.set_editor_property('const_mip_value',bias)
        return n

    base = sample('basecolor')
    desat = node(u.MaterialExpressionDesaturation)
    wire(base,'RGB',desat,''); wire(scalar(.18),'',desat,'Fraction')
    pigment = node(u.MaterialExpressionLinearInterpolate)
    wire(desat,'',pigment,'A'); wire(color(tint),'',pigment,'B'); wire(scalar(blend),'',pigment,'Alpha')
    prop(pigment,'',u.MaterialProperty.MP_BASE_COLOR)
    normal = node(u.MaterialExpressionLinearInterpolate)
    wire(color((0,0,1)),'',normal,'A'); wire(sample('normal'),'RGB',normal,'B'); wire(scalar(normal_strength),'',normal,'Alpha')
    prop(normal,'',u.MaterialProperty.MP_NORMAL)
    prop(scalar(.87 if not metal else .76),'',u.MaterialProperty.MP_ROUGHNESS)
    prop(scalar(.05 if metal else 0),'',u.MaterialProperty.MP_METALLIC)
    prop(scalar(.20),'',u.MaterialProperty.MP_SPECULAR)
    ML.recompile_material(mat)
    assert E.save_loaded_asset(mat,only_if_is_dirty=False)
    materials[key] = mat
    settings[key] = dict(material=path,tint=tint,pigment_blend=blend,normal_strength=normal_strength,mip_bias=bias)

counts = {}
for actor in A.get_all_level_actors():
    label = actor.get_actor_label()
    key = label.split('_')[2] if label.startswith('OH_FULL_') else '19' if label.startswith('OH_Tripo_Tree_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if key in materials:
        actor.modify()
        actor.static_mesh_component.set_material(0,materials[key])
        counts[key] = counts.get(key,0)+1
    if label == 'OH_Sun':
        c = actor.get_component_by_class(u.DirectionalLightComponent)
        c.set_editor_property('light_source_angle',10.0)
        c.set_editor_property('intensity',16000.0)
        c.set_light_color(u.LinearColor(1,.84,.60,1))
    if label == 'OH_Sky':
        actor.get_component_by_class(u.SkyLightComponent).set_editor_property('intensity',2.2)
    if label == 'OH_Exposure':
        actor.modify()
        pp = actor.get_editor_property('settings')
        for field,value in [('color_contrast',u.Vector4(.90,.90,.90,1)),('color_gamma',u.Vector4(1.06,1.06,1.06,1)),('color_gain',u.Vector4(1.04,1.03,.98,1)),('ambient_occlusion_intensity',.35)]:
            pp.set_editor_property('override_'+field,True)
            pp.set_editor_property(field,value)
        actor.set_editor_property('settings',pp)

assert sum(counts.values()) == 532,counts
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,materials=settings,actors=counts,total=sum(counts.values()),sun_intensity=16000,sun_angle=10,sun_color=[1,.84,.60],sky_intensity=2.2,color_contrast=.90,color_gamma=1.06,color_gain=[1.04,1.03,.98],ambient_occlusion_intensity=.35,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
# Load the saved map again and verify that overrides persisted.
assert L.load_level(MAP)
verified = 0
for actor in A.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith(('OH_FULL_','OH_Tripo_Tree_','OH_STRUCTURE_Roof_')):
        assert actor.static_mesh_component.get_material(0).get_path_name().startswith(DEST+'/'),label
        verified += 1
assert verified == 532
(OUT/'verification.json').write_text(json.dumps(dict(saved_material_overrides=verified,geometry_and_collision_checks='passed',playtest=False),indent=2))
u.log('PAINTED_HALL_VERIFIED')
script = (ROOT/'Content/Python/capture_hall_exposure.py').read_text()
script = script.replace("out=root/'ArtSource/OvergrownHall/Scene/v001'","out=root/'ArtSource/OvergrownHall/TripoReplacement/v004'")
script = script.replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP)
script = script.replace('unreal_exposure_fixed.png','unreal_painted.png')
exec(compile(script,'capture_painted_hall','exec'),globals())
