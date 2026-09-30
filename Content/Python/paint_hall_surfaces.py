"""v007 authored mineral pigment and restrained foliage value pass. Run after v006."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u, json, runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v007'
D='/Game/Constellation/Environments/OvergrownHall/TripoFull'; MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary; ML=u.MaterialEditingLibrary; AT=u.AssetToolsHelpers.get_asset_tools()
A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
# Reuse only the pure graph helper definition, not the v006 scene mutation.
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text()
exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
task=u.AssetImportTask(); task.filename=str(OUT/'Textures/painted_mineral.png')
task.destination_path=D+'/IllustratedTextures'; task.destination_name='T_OH_PaintedMineral'
task.automated=True; task.replace_existing=True; task.save=True
AT.import_asset_tasks([task]); tex=E.load_asset(D+'/IllustratedTextures/T_OH_PaintedMineral'); assert tex
tex.set_editor_property('srgb',True)
tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
tex.set_editor_property('resize_during_build_x',1024); tex.set_editor_property('resize_during_build_y',1024)
tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT)
tex.set_editor_property('compression_no_alpha',True)
tex.set_editor_property('never_stream',False)
E.save_loaded_asset(tex)
rows=load_current_json((OUT.parent/'v005/shape_manifest.json').read_text())
stone={'01','02','03','04','05','09','11','12','13','26'}
foliage={'16','17','18','19'}
materials={}
def sample(g,texture,uv=None,bias=1):
    n=g.n(u.MaterialExpressionTextureSample); n.texture=texture
    n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
    n.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_BIAS)
    n.set_editor_property('const_mip_value',bias)
    if uv is not None:g.wire(uv,n)
    return n
def pair(g,node,c1,c2):
    return g.op(u.MaterialExpressionAppendVector,g.mask(node,c1),g.mask(node,c2))
def divide(g,a,b):return g.op(u.MaterialExpressionDivide,a,b)
for row in rows:
    key=row['id']; name='M_OH_Illustrated_'+key; path=D+'/IllustratedMaterials'
    mat=E.load_asset(path+'/'+name) if E.does_asset_exist(path+'/'+name) else AT.create_asset(name,path,u.Material,u.MaterialFactoryNew())
    mat.modify(); ML.delete_all_material_expressions(mat); mat.set_editor_property('two_sided',key in foliage)
    g=Graph(mat); pos=g.n(u.MaterialExpressionWorldPosition)
    if key in stone:
        # Continuous physical texture scale, independent of the rebaked atlas islands.
        p=g.mul(pos,g.c(1/330 if key!='13' else 1/240))
        normal=g.n(u.MaterialExpressionVertexNormalWS); absolute=g.n(u.MaterialExpressionAbs); g.wire(normal,absolute)
        sharp=g.mul(absolute,absolute); sharp=g.mul(sharp,sharp)
        weights=[g.mask(sharp,i) for i in range(3)]
        total=g.add(g.add(weights[0],weights[1]),g.add(weights[2],g.c(.0001)))
        planes=[pair(g,p,1,2),pair(g,p,0,2),pair(g,p,0,1)]
        layers=[g.mul(sample(g,tex,uv,1),divide(g,w,total)) for uv,w in zip(planes,weights)]
        pigment=g.add(g.add(layers[0],layers[1]),layers[2])
        base=g.mul(pigment,g.color((.70,.83,.88)))
        # Moss concentrates near wet bases and horizontal ledges; upper shafts stay legible.
        broad=g.noise(pos,.0035); fine=g.noise(pos,.016)
        patch=g.clamp(g.mul(g.sub(g.add(broad,g.mul(fine,g.c(.14))),g.c(.58)),g.c(4)))
        low=g.clamp(g.sub(g.c(1),g.mul(g.mask(pos,2),g.c(1/320))))
        upward=g.clamp(g.mask(normal,2))
        density=g.clamp(g.add(g.c(.10),g.add(g.mul(low,g.c(.64)),g.mul(upward,g.c(.20)))))
        amount=g.mul(patch,density)
        moss=g.lerp(g.color((.08,.15,.06)),g.color((.21,.29,.10)),fine)
        base=g.lerp(base,moss,amount)
    else:
        texturepath=(D+'/CleanTextures/T_OH_Clean_'+key) if key not in foliage and key!='15' else ('/Game/Constellation/Environments/OvergrownHall/TripoReplacement/Textures/T_Tree_basecolor' if key=='19' else D+'/Textures/T_OH_'+key+'_basecolor')
        original=E.load_asset(texturepath); assert original,texturepath
        color=sample(g,original,bias=2.5 if key in foliage else 1)
        if key in foliage:
            desat=g.n(u.MaterialExpressionDesaturation); g.wire(color,desat); g.wire(g.c(1),desat,'Fraction')
            value=g.clamp(g.add(g.mul(desat,g.c(.80)),g.c(.12)))
            leafy=g.lerp(g.color((.055,.15,.085)),g.color((.36,.51,.15)),value)
            # Original green content selects leaves, preserving gray/brown Tripo trunk pigment.
            green=g.clamp(g.add(g.mul(g.sub(g.mask(color,1),g.mask(color,0)),g.c(12)),g.c(.12)))
            trunk=g.lerp(color,g.color((.24,.25,.18)),g.c(.40))
            base=g.lerp(trunk,leafy,green)
            g.prop(g.mul(base,g.c(.075)),u.MaterialProperty.MP_EMISSIVE_COLOR)
        else:
            tint=(.23,.29,.28) if key in {'06','07','08','10','25'} else (.30,.30,.23)
            base=g.lerp(color,g.color(tint),g.c(.48))
    g.prop(base,u.MaterialProperty.MP_BASE_COLOR)
    g.prop(g.c(.93 if key in stone or key in foliage else .85),u.MaterialProperty.MP_ROUGHNESS)
    g.prop(g.c(.10),u.MaterialProperty.MP_SPECULAR)
    # Geometric normals retain clean edges; photographic normal-map grain is omitted.
    ML.recompile_material(mat); assert E.save_loaded_asset(mat,only_if_is_dirty=False)
    materials[key]=mat
counts={}; growth=0
for actor in A.get_all_level_actors():
    label=actor.get_actor_label()
    key=label.split('_')[2] if label.startswith('OH_FULL_') else '19' if label.startswith('OH_Tripo_Tree_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if label.startswith('OH_Growth_'):key='18' if '_Vine_' in label else '17'; growth+=1
    if key in materials:
        actor.modify(); actor.static_mesh_component.set_material(0,materials[key]); counts[key]=counts.get(key,0)+1
assert sum(counts.values())==585 and growth==53,counts
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,materials={k:v.get_path_name() for k,v in materials.items()},instances=counts,total=585,added_foliage=53,mineral_repeat_cm=330,floor_repeat_cm=240,geometry_changed=False,lighting_changed=False,water_changed=False,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_pigment.py'))
