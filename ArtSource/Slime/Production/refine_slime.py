"""Revision 07: saturated layered gel and constant-size rigid droplet.
Run against the maintained source using tools/run-blender.ps1.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3-2*t)

def spline(points,u):
    x=min(max(u,0),1)*(len(points)-1)
    i=min(int(x),len(points)-2);t=x-i
    a,b,c,d=[points[min(max(j,0),len(points)-1)] for j in (i-1,i,i+1,i+2)]
    return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)

def refine(scene,out):
    scene.frame_set(1)
    body=bpy.data.objects['Slime_Body'];rig=bpy.data.objects['Slime_Liquid_Rig']
    gel=bpy.data.materials['M_Slime_IndigoGel']
    gel.diffuse_color=(.006,.0002,.022,1)
    gp=next(n for n in gel.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    gp.inputs['Base Color'].default_value=(.11,.002,.27,1)
    ramp=next(n for n in gel.node_tree.nodes if n.type=='VALTORGB')
    ramp.color_ramp.elements[0].position=.25
    ramp.color_ramp.elements[0].color=(.12,.008,.70,1)
    ramp.color_ramp.elements[1].position=.83
    ramp.color_ramp.elements[1].color=(.012,.0008,.055,1)
    ramp.color_ramp.interpolation='EASE'
    # Rest-space height darkens the crest without sliding during deformation.
    nodes=gel.node_tree.nodes;links=gel.node_tree.links
    for n in list(nodes):
        if n.name.startswith('Core_'):nodes.remove(n)
    geometry=nodes.new('ShaderNodeNewGeometry');geometry.name='Core_ViewGeometry'
    dot=nodes.new('ShaderNodeVectorMath');dot.name='Core_ViewDot';dot.operation='DOT_PRODUCT'
    absolute=nodes.new('ShaderNodeMath');absolute.name='Core_ViewFacing';absolute.operation='ABSOLUTE'
    links.new(geometry.outputs['Normal'],dot.inputs[0]);links.new(geometry.outputs['Incoming'],dot.inputs[1])
    links.new(dot.outputs['Value'],absolute.inputs[0]);links.new(absolute.outputs[0],ramp.inputs[0])
    tex=nodes.new('ShaderNodeTexCoord');tex.name='Core_RestCoordinates'
    sep=nodes.new('ShaderNodeSeparateXYZ');sep.name='Core_Height'
    height=nodes.new('ShaderNodeMapRange');height.name='Core_CrestDensity'
    height.inputs['From Min'].default_value=.45;height.inputs['From Max'].default_value=.9
    height.inputs['To Min'].default_value=1;height.inputs['To Max'].default_value=.80
    height.clamp=True
    tint=nodes.new('ShaderNodeMixRGB');tint.name='Core_DensityTint';tint.blend_type='MULTIPLY'
    tint.inputs[0].default_value=1
    links.new(tex.outputs['Generated'],sep.inputs[0]);links.new(sep.outputs['Z'],height.inputs['Value'])
    links.new(ramp.outputs['Color'],tint.inputs[1]);links.new(height.outputs['Result'],tint.inputs[2])
    links.new(tint.outputs[0],gp.inputs['Base Color'])
    noise=nodes.new('ShaderNodeTexNoise');noise.name='Core_InternalLayers'
    noise.inputs['Scale'].default_value=8;noise.inputs['Detail'].default_value=3
    noise.inputs['Roughness'].default_value=.65
    links.new(tex.outputs['Generated'],noise.inputs['Vector'])
    density=nodes.new('ShaderNodeMapRange');density.name='Core_LayerDensity'
    density.inputs['To Min'].default_value=.45;density.inputs['To Max'].default_value=1.55
    links.new(noise.outputs['Fac'],density.inputs[0])
    layered=nodes.new('ShaderNodeMixRGB');layered.name='Core_LayeredColor';layered.blend_type='MULTIPLY';layered.inputs[0].default_value=.7
    links.new(tint.outputs[0],layered.inputs[1]);links.new(density.outputs[0],layered.inputs[2])
    links.new(layered.outputs[0],gp.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.name='Core_LiquidSurface'
    bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.018
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],gp.inputs['Normal'])
    gp.inputs['Roughness'].default_value=.14
    gp.inputs['Coat Roughness'].default_value=.10
    gp.inputs['Specular IOR Level'].default_value=.30
    for name,size in [('Key',1.4),('Fill',1.1),('Rim',1.4)]:
        bpy.data.objects[name].data.size=size
    for name,loc in [('Key',(-3,-1,5)),('Fill',(3,0,3.5))]:
        light=bpy.data.objects[name];light.location=loc
        light.rotation_euler=(Vector((0,0,.7))-light.location).to_track_quat('-Z','Y').to_euler()
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene.view_settings.exposure=-.65
    body.data.materials.clear();body.data.materials.append(gel)
    old=bpy.data.materials.get('M_Slime_SkinEyes')
    if old and old.users==0:bpy.data.materials.remove(old)
    uv=body.data.uv_layers.get('EyeProjection')
    if uv:body.data.uv_layers.remove(uv)
    for name in ['Eye_L','Eye_R']:
        o=bpy.data.objects.get(name)
        if o:bpy.data.objects.remove(o,do_unlink=True)
    eye_mat=bpy.data.materials.get('M_Slime_EyeCream') or bpy.data.materials.new('M_Slime_EyeCream')
    eye_mat.use_nodes=True;eye_mat.diffuse_color=(.96,.88,.65,1)
    ep=next(n for n in eye_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    ep.inputs['Base Color'].default_value=(.96,.88,.65,1)
    ep.inputs['Roughness'].default_value=.25
    ep.inputs['Emission Color'].default_value=(.96,.88,.68,1)
    ep.inputs['Emission Strength'].default_value=.65
    body.data.calc_loop_triangles()
    triangles=[list(t.vertices) for t in body.data.loop_triangles]
    tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],triangles,all_triangles=True)
    def front(x,z):
        hit=tree.ray_cast(Vector((x,-3,z)),Vector((0,1,0)),6)[0]
        assert hit is not None,('Eye projection missed body',x,z)
        return hit.y
    # Restore original circular dimensions, centers and cream shader.
    for sign in (-1,1):
        ev=[];ef=[];ex=sign*.27;ez=.65;rx=.114;rz=.114
        ev.append((ex,front(ex,ez)-.009,ez))
        for k in range(1,7):
            r=k/6
            for j in range(64):
                a=j*math.tau/64;x=ex+rx*r*math.cos(a);z=ez+rz*r*math.sin(a)
                ev.append((x,front(x,z)-.008-.003*(1-r*r),z))
        for j in range(64):ef.append((0,1+j,1+(j+1)%64))
        for k in range(5):
            for j in range(64):
                a=1+k*64+j;b=1+k*64+(j+1)%64
                ef.append((a,a+64,b+64,b))
        d=bpy.data.meshes.new('Eye_L' if sign<0 else 'Eye_R');d.from_pydata(ev,[],ef);d.update()
        o=bpy.data.objects.new('Eye_L' if sign<0 else 'Eye_R',d);scene.collection.objects.link(o);d.materials.append(eye_mat)
        for p in d.polygons:p.use_smooth=True
        groups={n:o.vertex_groups.new(name=n) for n in ['root','center','top','crest','crest_tip']}
        for v in d.vertices:
            x,y,z=v.co;wc=smooth(.94,1.30,z)
            tip=wc*smooth(.12,.36,x)*smooth(-.10,-.30,y);cr=wc-tip
            top=(1-wc)*smooth(.62,1.05,z)*.70;root=1-smooth(.04,.34,z)
            vals={'root':root,'center':max(0,1-root-top-cr-tip),'top':top,'crest':cr,'crest_tip':tip}
            total=sum(vals.values())
            for name,w in vals.items():
                if w>0:groups[name].add([v.index],w/total,'REPLACE')
        mod=o.modifiers.new('Liquid deformation','ARMATURE');mod.object=rig;o.parent=rig

    # Project the annotated path using the original review camera.
    cam=scene.camera
    corners=cam.data.view_frame(scene=scene)
    left=min(p.x for p in corners);right=max(p.x for p in corners)
    bottom=min(p.y for p in corners);top=max(p.y for p in corners)
    direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
    def screen_hit(pixel):
        x,y=pixel
        origin=cam.matrix_world@Vector((left+(right-left)*x/548,top-(top-bottom)*y/502,0))
        loc,n,face,dist=tree.ray_cast(origin,direction,100)
        assert loc is not None,('User route left silhouette',list(pixel))
        return loc,n,face
    tip_hit=screen_hit((320,177))
    pixels=[Vector(p) for p in [(333,207),(341,230),(351,255),(362,285),
                                (374,325),(379,356),(377,380),(374,392)]]
    route=[screen_hit(spline(pixels,i/240)) for i in range(241)]
    rest_vertices=[v.co.copy() for v in body.data.vertices]
    def attached(hit,deformed):
        loc,normal,index=hit
        ids=triangles[index]
        a,b,c=[rest_vertices[i] for i in ids];A,B,C=[deformed[i] for i in ids]
        p=barycentric_transform(loc,a,b,c,A,B,C)
        rest_t=Matrix(((b-a),(c-a),(b-a).cross(c-a))).transposed()
        pose_t=Matrix(((B-A),(C-A),(B-A).cross(C-A))).transposed()
        weights=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        n=sum((body.data.vertices[i].normal*weights[j] for j,i in enumerate(ids)),Vector()).normalized()
        n=(pose_t@rest_t.inverted()@n).normalized()
        return p,n
    def flow_sample(u,deformed):
        index=min(239,max(0,int(u*240)));t=min(1,max(0,u*240-index))
        a,na=attached(route[index],deformed);b,nb=attached(route[index+1],deformed)
        return a.lerp(b,t),na.lerp(nb,t).normalized()
    rest=rig.data.bones['drop'].head_local.copy()
    basis=rig.data.bones['drop'].matrix_local.to_3x3()
    # The user's screenshot corresponds to the upper-body pose around 1.83 s.
    # Preserve that authored tilt once, then reuse it throughout every loop.
    if 'drop_fixed_rotation_v05' not in rig:
        scene.frame_set(45)
        rig['drop_fixed_rotation_v05']=list(rig.pose.bones['drop'].rotation_quaternion)
    fixed_rotation=rig['drop_fixed_rotation_v05'][:]
    import sys
    if str(out) not in sys.path:sys.path.insert(0,str(out))
    from puddle_idle import animate_puddle
    animate_puddle(scene,body,rig)
    drop=bpy.data.objects['Slime_Droplet']
    rigid=(basis@Quaternion(fixed_rotation).to_matrix())
    # All mesh offsets are fixed; use their support distance to prevent changing
    # silhouettes caused by a thin droplet slicing into the curved body.
    # Apply the authored bone-local dimensions exactly once to each offset.
    local_scale=Matrix.Diagonal(Vector((.62,1,.24)))
    offsets=[rigid@local_scale@basis.inverted()@(drop.matrix_world@v.co-rest) for v in drop.data.vertices]
    def clearance(n):return max(-n.dot(v) for v in offsets)+.006
    first_pose=None;track=[]
    for f in range(1,98):
        scene.frame_set(f);q=(f-1)/96
        dep=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dep);me=ev.to_mesh()
        deformed=[v.co.copy() for v in me.vertices];ev.to_mesh_clear()
        tip,tip_normal=attached(tip_hit,deformed)
        entry,entry_normal=flow_sample(0,deformed)
        if q<.14:
            u=smooth(0,.14,q);pos=tip+tip_normal*(-.15+(clearance(tip_normal)+.15)*u)
            normal=tip_normal;up=Vector((0,0,1));scale=Vector((.62,.24,1))
        elif q<.28:
            u=smooth(.14,.28,q)
            a=tip+tip_normal*clearance(tip_normal);d=entry+entry_normal*clearance(entry_normal)
            next_point,_=flow_sample(.008,deformed)
            b=a+Vector((.025,0,-.065));c=d+(entry-next_point).normalized()*.075
            pos=(1-u)**3*a+3*(1-u)**2*u*b+3*(1-u)*u*u*c+u**3*d
            normal=tip_normal.lerp(entry_normal,u).normalized()
            up=-(3*(1-u)**2*(b-a)+6*(1-u)*u*(c-b)+3*u*u*(d-c)).normalized()
            scale=Vector((.62,.24,1.0))
        elif q<.84:
            u=smooth(.28,.84,q);p,normal=flow_sample(u,deformed)
            lo,_=flow_sample(max(0,u-.008),deformed);hi,_=flow_sample(min(1,u+.008),deformed)
            up=(lo-hi).normalized();pos=p+normal*clearance(normal);scale=Vector((.62,.24,1.0))
        elif q<.96:
            u=smooth(.84,.94,q);p,normal=flow_sample(1,deformed)
            previous,_=flow_sample(.99,deformed);up=(previous-p).normalized()
            # Carry the full-size bead into the thick inner edge of the puddle.
            # The skin occludes it before any reset or scale change occurs.
            inward=Vector((-p.x,-p.y,0)).normalized()
            pos=p+normal*clearance(normal)+inward*(.30*u)+Vector((0,0,.025*u))
            scale=Vector((.62,.24,1.0))
        else:
            p,normal=flow_sample(1,deformed);inward=Vector((-p.x,-p.y,0)).normalized()
            a=p+normal*clearance(normal)+inward*.30+Vector((0,0,.025))
            d=tip-tip_normal*.15
            # Follow the filled crest spine, not the hollow underside of the curl.
            hidden=[a,Vector((.05,0,.60)),Vector((0,.04,1.27)),Vector((.19,-.16,1.53)),d]
            u=max(0,min(4,(f-93)));i=min(3,int(u))
            pos=hidden[i].lerp(hidden[i+1],u-i)
            up=Vector((0,0,1));scale=Vector((.62,.24,1))
        up=(up-normal*up.dot(normal)).normalized()
        if up.length<.1:up=Vector((0,0,1))
        side=up.cross(normal).normalized();up=normal.cross(side).normalized()
        rotation=Matrix((side,up,normal)).transposed()
        pb=rig.pose.bones['drop'];pb.rotation_mode='QUATERNION'
        pb.location=basis.inverted()@(pos-rest)
        pb.rotation_quaternion=fixed_rotation
        pb.scale=(scale.x,scale.z,scale.y)
        for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group='drop')
        if first_pose is None:first_pose=(pos.copy(),normal.copy(),up.copy())
        track.append({'frame':f,'position':list(pos),'skin_offset_m':.01 if .28<=q<.84 else None})
    for layer in rig.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if 'drop' in fc.data_path:
                        for k in fc.keyframe_points:k.interpolation='LINEAR'
    scene.frame_set(1)
    scene['revision']='07: saturated layered gel; rigid droplet with internal return'
    (out/'revision-07.json').write_text(json.dumps({'revision':7,'eye_width_m':.228,
        'drop_fixed_rotation_wxyz':fixed_rotation,'rotation_reference_frame':45,
        'eye_height_m':.228,'eye_center_distance_m':.54,'eye_width_ratio_to_original':1,
        'route_reference':'References/user-flow-route.png','route_pixels':[list(p) for p in pixels],
        'tip_pixel':[320,177],'skin_following':'barycentric coordinates on evaluated animated triangles',
        'track':track},indent=2),encoding='utf8')
    models=[body,bpy.data.objects['Slime_Droplet'],bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]
    (out/'build-report.json').write_text(json.dumps({'blender':bpy.app.version_string,'revision':7,
        'fps':24,'frames':[1,97],'duration_seconds':4,'rig_bones':list(rig.data.bones.keys()),
        'units':'meters','forward':'-Y','pivot':'floor','meshes':{o.name:{'vertices':len(o.data.vertices),
        'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in models}},indent=2),encoding='utf8')

def export_and_render(out):
    s=bpy.context.scene;s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Slime_Liquid.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for name in ['Slime_Liquid_Rig','Slime_Body','Slime_Droplet','Eye_L','Eye_R']:bpy.data.objects[name].select_set(True)
    if bpy.data.objects.get('Slime_InnerGel'):bpy.data.objects['Slime_InnerGel'].select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects['Slime_Liquid_Rig']
    bpy.ops.export_scene.fbx(filepath=str(out/'SK_Slime_Liquid_Idle.fbx'),use_selection=True,
        object_types={'ARMATURE','MESH'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',
        apply_unit_scale=True,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,mesh_smooth_type='FACE',use_mesh_modifiers=True)
    if str(s.get('revision',''))[:2] in ('08','09','10'):
        from gel_flow_v08 import render_setup
        render_setup(s)
    else:s.render.engine='BLENDER_EEVEE'
    s.render.resolution_x=1100;s.render.resolution_y=1000
    for name,loc in [('three-quarter',(3,-6,2.65)),('front',(0,-6,2.25)),('side',(6,0,1.6))]:
        s.camera.location=loc;s.camera.rotation_euler=(Vector((0,0,.76))-s.camera.location).to_track_quat('-Z','Y').to_euler()
        s.render.filepath=str(out/'Preview'/f'{name}.png');bpy.ops.render.render(write_still=True)

if __name__=='__main__':
    folder=Path(__file__).resolve().parent
    refine(bpy.context.scene,folder);export_and_render(folder)
