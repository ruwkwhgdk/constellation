"""v006: masonry moss, attached Tripo foliage, shallow reflective water."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,random,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v006';OUT.mkdir(parents=True,exist_ok=True)
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
settings=load_current_json((OUT.parent/'v004/applied.json').read_text())['materials']

def material(name):
    path=D+'/GrowthMaterials/'+name
    m=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,D+'/GrowthMaterials',u.Material,u.MaterialFactoryNew())
    m.modify();ML.delete_all_material_expressions(m);return m

class Graph:
    def __init__(self,mat):self.m=mat
    def n(self,cls):return ML.create_material_expression(self.m,cls)
    def c(self,value):
        n=self.n(u.MaterialExpressionConstant);n.r=value;return n
    def color(self,value):
        n=self.n(u.MaterialExpressionConstant3Vector);n.constant=u.LinearColor(*value,1);return n
    def wire(self,a,b,pin='',out=''):
        assert ML.connect_material_expressions(a,out,b,pin),(type(a).__name__,type(b).__name__,pin)
    def prop(self,a,prop,out=''):assert ML.connect_material_property(a,out,prop)
    def op(self,cls,a,b):
        n=self.n(cls);self.wire(a,n,'A');self.wire(b,n,'B');return n
    def mul(self,a,b):return self.op(u.MaterialExpressionMultiply,a,b)
    def add(self,a,b):return self.op(u.MaterialExpressionAdd,a,b)
    def sub(self,a,b):return self.op(u.MaterialExpressionSubtract,a,b)
    def clamp(self,a):
        n=self.n(u.MaterialExpressionClamp);self.wire(a,n);return n
    def mask(self,a,channel):
        n=self.n(u.MaterialExpressionComponentMask)
        for i,p in enumerate(['r','g','b','a']):n.set_editor_property(p,i==channel)
        self.wire(a,n);return n
    def lerp(self,a,b,alpha):
        n=self.n(u.MaterialExpressionLinearInterpolate);self.wire(a,n,'A');self.wire(b,n,'B');self.wire(alpha,n,'Alpha');return n
    def noise(self,pos,scale):
        n=self.n(u.MaterialExpressionNoise);n.set_editor_property('scale',scale);n.set_editor_property('levels',2);n.set_editor_property('output_min',0.0);n.set_editor_property('output_max',1.0);self.wire(pos,n);return n

moss_keys=['01','02','03','04','05','09','12','13','26'];moss={}
for key in moss_keys:
    mat=material('M_OH_Moss_'+key);g=Graph(mat)
    sample=g.n(u.MaterialExpressionTextureSample);sample.texture=E.load_asset(D+'/CleanTextures/T_OH_Clean_'+key);assert sample.texture
    sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
    base=g.lerp(sample,g.color(settings[key]['tint']),g.c(.58))
    pos=g.n(u.MaterialExpressionWorldPosition)
    broad=g.noise(pos,.009);detail=g.noise(pos,.05)
    patch=g.clamp(g.mul(g.sub(g.add(broad,g.mul(detail,g.c(.20))),g.c(.45)),g.c(3.5)))
    z=g.mask(pos,2)
    low=g.clamp(g.sub(g.c(1.0),g.mul(z,g.c(1/260))))
    density=g.add(g.c(.45),g.mul(low,g.c(.50)))
    amount=g.mul(patch,g.mul(density,g.c(.56 if key=='13' else .85)))
    mosscolor=g.lerp(g.color((.055,.125,.025)),g.color((.19,.31,.055)),detail)
    g.prop(g.lerp(base,mosscolor,amount),u.MaterialProperty.MP_BASE_COLOR)
    g.prop(g.lerp(g.c(.82),g.c(.97),amount),u.MaterialProperty.MP_ROUGHNESS)
    g.prop(g.c(.12),u.MaterialProperty.MP_SPECULAR)
    ML.recompile_material(mat);assert E.save_loaded_asset(mat,only_if_is_dirty=False);moss[key]=mat

water=material('M_OH_ShallowWater');water.set_editor_property('shading_model',u.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
g=Graph(water)
g.prop(g.color((.025,.075,.065)),u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.c(.06),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.50),u.MaterialProperty.MP_SPECULAR);g.prop(g.c(.03),u.MaterialProperty.MP_OPACITY)
volume=g.n(u.MaterialExpressionSingleLayerWaterMaterialOutput)
g.wire(g.color((.003,.008,.006)),volume,'ScatteringCoefficients')
g.wire(g.color((.035,.010,.006)),volume,'AbsorptionCoefficients')
g.wire(g.c(.15),volume,'PhaseG');g.wire(g.color((.93,.98,.93)),volume,'ColorScaleBehindWater')
pos=g.n(u.MaterialExpressionWorldPosition);time=g.n(u.MaterialExpressionTime)
waves=[]
for channel,freq,speed,amplitude in [(0,.012,.045,.012),(1,.018,-.032,.008)]:
    phase=g.add(g.mul(g.mask(pos,channel),g.c(freq)),g.mul(time,g.c(speed)))
    sine=g.n(u.MaterialExpressionSine);g.wire(phase,sine);waves.append(g.mul(sine,g.c(amplitude)))
xy=g.op(u.MaterialExpressionAppendVector,*waves);xyz=g.op(u.MaterialExpressionAppendVector,xy,g.c(1));g.prop(xyz,u.MaterialProperty.MP_NORMAL)
ML.recompile_material(water);assert E.save_loaded_asset(water,only_if_is_dirty=False)

actors=list(A.get_all_level_actors());changed={}
for actor in actors:
    label=actor.get_actor_label()
    if label.startswith('OH_Growth_'):A.destroy_actor(actor);continue
    key=label.split('_')[2] if label.startswith('OH_FULL_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if key in moss:
        actor.modify();actor.static_mesh_component.set_material(0,moss[key]);changed[key]=changed.get(key,0)+1
    if label=='OH_SM_OH_Blockout_21':
        actor.modify();actor.static_mesh_component.set_material(0,water);actor.static_mesh_component.set_collision_profile_name('NoCollision')

# Keep the clean structural silhouettes; irregular foliage patches sit on faces.
rng=random.Random(926);vine=E.load_asset(D+'/Meshes/SM_OH_Clean_18_Vine');leaf=E.load_asset(D+'/Meshes/SM_OH_Clean_17_Shrub')
vmat=E.load_asset(D+'/PaintedMaterials/M_OH_Painted_18');lmat=E.load_asset(D+'/PaintedMaterials/M_OH_Painted_17')
placements=[]
def place(kind,position,scale,yaw=0):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*position),u.Rotator(pitch=0,yaw=yaw,roll=0));a.set_actor_label('OH_Growth_'+kind+'_%03d'%len(placements));a.set_actor_scale3d(u.Vector(*scale))
    a.static_mesh_component.set_static_mesh(vine if kind=='Vine' else leaf);a.static_mesh_component.set_material(0,vmat if kind=='Vine' else lmat);a.static_mesh_component.set_collision_profile_name('NoCollision')
    placements.append(dict(label=a.get_actor_label(),kind=kind,position=position,scale=scale,yaw=yaw))

# Major side column runs, with different coverage on the two sides.
for side in [-1,1]:
    for j,y in enumerate([600,1000,1400,1800]):
        if (side,j) in [(1,0),(-1,2)]:continue
        x=side*602
        for k,z in enumerate([90,310,530]):
            if k==2 and j%2:continue
            place('Vine',(x,y+rng.uniform(-12,12),z+rng.uniform(-30,25)),(rng.uniform(.8,1.35),.60,rng.uniform(.9,1.45)),90)
        place('Leaf',(side*593,y,45),(.40,.40,.50),rng.uniform(-25,25))

# Broad uneven hanging ribbons below the rear window sill, not isolated strings.
for i,x in enumerate([-485,-405,-325,-215,-110,35,145,280,400,490]):
    h=rng.uniform(.48,1.0)
    place('Vine',(x,1918,260-200*h),(rng.uniform(1.15,1.75),.65,h))
    place('Leaf',(x,1910,248),(.38,.24,.28),rng.uniform(-12,12))
# A few vertical climbing patches on rear piers, leaving window openings clear.
for x in [-500,-262,262,500]:
    for z in [365,735]:
        if x==262 and z==365:continue
        place('Vine',(x,1938,z),(.48,.6,.92))
# Ivy carried along the inner side cornice, trailing down from its ledge.
for side in [-1,1]:
    for y in [720,1330,1690]:
        place('Vine',(side*603,y,630),(1.6,.6,.84),90)

assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,moss_instances=changed,foliage=placements,added_foliage=len(placements),water_material=water.get_path_name(),water_model='SingleLayerWater',water_roughness=.06,water_collision='NoCollision',interactive_water=False,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/verify_hall_growth_water.py'))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v006').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP).replace('unreal_exposure_fixed.png','unreal_growth_water.png')
exec(compile(script,'capture_growth_water','exec'),globals())
