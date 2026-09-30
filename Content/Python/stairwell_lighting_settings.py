from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u, json, math
from pathlib import Path
def apply_lighting():
    config=load_current_json((Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular/Scene/v001/lighting_revision.json').read_text())
    actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    for name,c in config['fixtures'].items():
        p=c['position']; yaw=c['yaw']; scale=c['length_scale']; angle=math.radians(yaw)
        pitch=c.get('pitch',0); pr=math.radians(pitch); depth=c.get('depth_scale',1); height=c.get('height_scale',1)
        lamp=actors['SWScene_Lamp_'+name]
        lamp.set_actor_location(u.Vector(*p),False,False)
        lamp.set_actor_scale3d(u.Vector(scale,depth,height))
        roll=c.get('roll',0)
        lamp.set_actor_rotation(u.Rotator(pitch=pitch,yaw=yaw,roll=roll),False)
        for side in [-1,1]:
            strip=actors['SWScene_LuminousStrip_'+name+str(side)]
            dz=-10.7*height
            strip.set_actor_location(lamp.get_actor_location()+lamp.get_actor_right_vector()*(side*5.5*depth)+lamp.get_actor_up_vector()*dz,False,False)
            strip.set_actor_rotation(lamp.get_actor_rotation(),False)
            strip.set_actor_scale3d(u.Vector(1.04*scale,.026,.006))
        light=actors['SWScene_Light_'+name]
        light.set_actor_location(lamp.get_actor_location()-lamp.get_actor_up_vector()*15,False,False)
        direction=-lamp.get_actor_up_vector()
        light.set_actor_rotation(u.Rotator(pitch=math.degrees(math.atan2(direction.z,math.hypot(direction.x,direction.y))),yaw=math.degrees(math.atan2(direction.y,direction.x)),roll=0),False)
        component=light.get_component_by_class(u.RectLightComponent)
        component.set_intensity(c['intensity']); component.set_editor_property('source_width',110*scale)
    actors['SWScene_LandingBounce'].get_component_by_class(u.PointLightComponent).set_intensity(config['landing_fill'])
    return config
