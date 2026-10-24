"""Physical transmission/absorption gel and gravity-to-surface droplet motion."""
import bpy,math,json
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree

def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

def render_setup(s,samples=48):
    s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.use_denoising=True
    s.cycles.max_bounces=12;s.cycles.transmission_bounces=10;s.cycles.volume_bounces=2
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU'

def apply(s,out):
    body=bpy.data.objects['Slime_Body'];drop=bpy.data.objects['Slime_Droplet'];rig=bpy.data.objects['Slime_Liquid_Rig']
    gel=bpy.data.materials['M_Slime_IndigoGel'];gel.use_nodes=True
    nt=gel.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
    output=n.new('ShaderNodeOutputMaterial');surface=n.new('ShaderNodeBsdfPrincipled')
    surface.inputs['Base Color'].default_value=(.65,.18,.95,1)
    surface.inputs['Transmission Weight'].default_value=.94
    surface.inputs['Roughness'].default_value=.16;surface.inputs['IOR'].default_value=1.22
    surface.inputs['Coat Weight'].default_value=.16;surface.inputs['Coat Roughness'].default_value=.1
    l.new(surface.outputs['BSDF'],output.inputs['Surface'])
    coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=4.5;noise.inputs['Detail'].default_value=2.5
    l.new(coord.outputs['Generated'],noise.inputs['Vector'])
    density=n.new('ShaderNodeMapRange');density.inputs['To Min'].default_value=.8;density.inputs['To Max'].default_value=3
    l.new(noise.outputs['Fac'],density.inputs[0])
    absorption=n.new('ShaderNodeVolumeAbsorption');absorption.inputs['Color'].default_value=(.62,.018,.75,1)
    l.new(density.outputs[0],absorption.inputs['Density']);l.new(absorption.outputs[0],output.inputs['Volume'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.07;bump.inputs['Distance'].default_value=.018
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],surface.inputs['Normal'])
    gel.diffuse_color=(.25,.02,.7,1)
    # A separate skinned density volume gives a dark overlapping interior while
    # preserving a genuinely transmissive skin, including the thin skirt.
    old=bpy.data.objects.get('Slime_InnerGel')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    cv=[];cf=[];weights=[]
    for center,radii,group in [(Vector((0,.04,.58)),Vector((.80,.62,.49)),'center'),
                               (Vector((.19,-.15,1.46)),Vector((.135,.115,.11)),'crest_tip')]:
        base=len(cv);rings=24;segments=48
        for i in range(rings+1):
            v=i/rings*math.pi
            for j in range(segments):
                a=j/segments*math.tau
                wobble=1+.045*math.sin(3*a+2*v)*math.sin(v)
                local=Vector((math.sin(v)*math.cos(a)*radii.x,math.sin(v)*math.sin(a)*radii.y,math.cos(v)*radii.z))*wobble
                cv.append(center+local);weights.append(group)
        for i in range(rings):
            for j in range(segments):
                a=base+i*segments+j;b=base+i*segments+(j+1)%segments
                cf.append((a+segments,b+segments,b,a))
    mesh=bpy.data.meshes.new('Slime_InnerGel');mesh.from_pydata(cv,[],cf);mesh.update()
    core=bpy.data.objects.new('Slime_InnerGel',mesh);s.collection.objects.link(core);core.parent=rig
    for group in ['center','crest_tip']:
        vg=core.vertex_groups.new(name=group);vg.add([i for i,g in enumerate(weights) if g==group],1,'REPLACE')
    mod=core.modifiers.new('Internal liquid deformation','ARMATURE');mod.object=rig
    coremat=bpy.data.materials.get('M_Slime_InnerDensity') or bpy.data.materials.new('M_Slime_InnerDensity')
    coremat.use_nodes=True;cn=coremat.node_tree.nodes;cl=coremat.node_tree.links;cn.clear()
    co=cn.new('ShaderNodeOutputMaterial');ct=cn.new('ShaderNodeBsdfTransparent');cl.new(ct.outputs[0],co.inputs['Surface'])
    ca=cn.new('ShaderNodeVolumeAbsorption');ca.inputs['Color'].default_value=(.42,.006,.60,1)
    cc=cn.new('ShaderNodeTexCoord');noise2=cn.new('ShaderNodeTexNoise');noise2.inputs['Scale'].default_value=5;noise2.inputs['Detail'].default_value=3
    cl.new(cc.outputs['Generated'],noise2.inputs['Vector'])
    dr=cn.new('ShaderNodeMapRange');dr.inputs['To Min'].default_value=8;dr.inputs['To Max'].default_value=32
    cl.new(noise2.outputs['Fac'],dr.inputs[0]);cl.new(ca.outputs[0],co.inputs['Volume'])
    # Feather both density lobes to zero at their boundary; no solid inner ball.
    fades=[]
    for center,radius in [((0,.04,.58),(.80,.62,.49)),((.19,-.15,1.46),(.135,.115,.11))]:
        sub=cn.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=center
        div=cn.new('ShaderNodeVectorMath');div.operation='DIVIDE';div.inputs[1].default_value=radius
        length=cn.new('ShaderNodeVectorMath');length.operation='LENGTH'
        fade=cn.new('ShaderNodeMapRange');fade.inputs['From Min'].default_value=.55;fade.inputs['From Max'].default_value=1
        fade.inputs['To Min'].default_value=1;fade.inputs['To Max'].default_value=0;fade.clamp=True
        cl.new(cc.outputs['Object'],sub.inputs[0]);cl.new(sub.outputs[0],div.inputs[0]);cl.new(div.outputs[0],length.inputs[0]);cl.new(length.outputs['Value'],fade.inputs[0]);fades.append(fade)
    maximum=cn.new('ShaderNodeMath');maximum.operation='MAXIMUM';cl.new(fades[0].outputs[0],maximum.inputs[0]);cl.new(fades[1].outputs[0],maximum.inputs[1])
    mul=cn.new('ShaderNodeMath');mul.operation='MULTIPLY';cl.new(dr.outputs[0],mul.inputs[0]);cl.new(maximum.outputs[0],mul.inputs[1]);cl.new(mul.outputs[0],ca.inputs['Density'])
    core.data.materials.append(coremat)
    # A bead immersed in the same liquid has no additional air/gel boundary.
    # Suppress its artificial nested surface for transmitted rays, not for camera rays.
    mat=bpy.data.materials.get('M_Slime_DropGel')
    if mat:bpy.data.materials.remove(mat,do_unlink=True)
    mat=gel.copy();mat.name='M_Slime_DropGel';dn=mat.node_tree.nodes;dl=mat.node_tree.links
    do=next(x for x in dn if x.type=='OUTPUT_MATERIAL');ds=next(x for x in dn if x.type=='BSDF_PRINCIPLED')
    for link in list(do.inputs['Volume'].links):dl.remove(link)
    path=dn.new('ShaderNodeLightPath');transparent=dn.new('ShaderNodeBsdfTransparent');mix=dn.new('ShaderNodeMixShader')
    dl.new(path.outputs['Is Transmission Ray'],mix.inputs[0]);dl.new(ds.outputs[0],mix.inputs[1]);dl.new(transparent.outputs[0],mix.inputs[2]);dl.new(mix.outputs[0],do.inputs['Surface'])
    drop.data.materials.clear();drop.data.materials.append(mat)
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0
    # Softer neutral studio illumination keeps the transmitted lower rim readable.
    for name,energy in [('Key',650),('Fill',420),('Rim',950)]:bpy.data.objects[name].data.energy=energy
    render_setup(s)
    s.frame_set(1)
    basis=rig.data.bones['drop'].matrix_local.to_3x3();rest=rig.data.bones['drop'].head_local.copy()
    # Remove the inherited tilted pose AND the curved tail in the mesh itself.
    if not drop.get('upright_tail_v09'):
        for v in drop.data.vertices:
            if v.co.z>0:
                a=.035/(.08*.08)
                original_z=(-1+math.sqrt(1+4*a*v.co.z))/(2*a)
                v.co.y-=.02*(original_z/.08)**2
        drop['upright_tail_v09']=True
    rotation=Quaternion((1,0,0,0));rot=basis@rotation.to_matrix()
    fixed_scale=Vector((.62,1,.24))
    offsets=[rot@Matrix.Diagonal(fixed_scale)@basis.inverted()@(drop.matrix_world@v.co-rest) for v in drop.data.vertices]
    upright_offsets=[v.copy() for v in offsets]
    def support(normal):return max(-normal.dot(v) for v in offsets)+.002
    # Rest geometry surface route: entry below the crest; radial descent to skirt.
    body.data.calc_loop_triangles();triangles=[list(t.vertices) for t in body.data.loop_triangles]
    tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],triangles,all_triangles=True)
    xy=Vector((.37,-.34,0));theta=math.atan2(xy.y,xy.x)
    hit=tree.ray_cast(Vector((xy.x,xy.y,1.15)),Vector((0,0,-1)),2)[0]
    assert hit is not None
    entry_z=hit.z
    rest_route=[]
    for i in range(241):
        u=i/240;z=entry_z+(.16-entry_z)*u
        a=theta+(.19*smooth(0,1,u));radial=Vector((math.cos(a),math.sin(a),0))
        p,no,idx,_=tree.ray_cast(radial*3+Vector((0,0,z)),-radial,5)
        assert p is not None
        rest_route.append((p,no,idx))
    from mathutils.geometry import barycentric_transform
    verts=[v.co.copy() for v in body.data.vertices]
    def attach(h,deformed):
        p,n,idx=h;ids=triangles[idx];a,b,c=[verts[i] for i in ids];A,B,C=[deformed[i] for i in ids]
        pp=barycentric_transform(p,a,b,c,A,B,C)
        nn=(B-A).cross(C-A).normalized()
        return pp,nn
    def sample(u,deformed):
        t=max(0,min(240,u*240));i=min(239,int(t));t-=i
        a,na=attach(rest_route[i],deformed);b,nb=attach(rest_route[i+1],deformed)
        return a.lerp(b,t),na.lerp(nb,t).normalized()
    track=[];release=None
    for f in range(1,98):
        s.frame_set(f);q=(f-1)/96
        rotation=Quaternion((1,0,0,0));offsets=upright_offsets
        surface_normal=None
        dep=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dep);me=ev.to_mesh()
        deformed=[v.co.copy() for v in me.vertices];ev.to_mesh_clear()
        live=BVHTree.FromPolygons(deformed,triangles,all_triangles=True)
        # Contact height includes the full rigid droplet, so its silhouette does not clip.
        contact_z=-10
        for v in offsets[::8]:
            h=live.ray_cast(Vector((xy.x+v.x,xy.y+v.y,1.15)),Vector((0,0,-1)),2)[0]
            if h:contact_z=max(contact_z,h.z-v.z+.003)
        landing=Vector((xy.x,xy.y,contact_z))
        start=Vector((xy.x,xy.y,1.39))
        if q<.24:
            u=q/.24;pos=start.lerp(landing,u*u)
            phase='vertical_gravity'
        elif q<.75:
            u=smooth(.24,.75,q);p,normal=sample(u,deformed)
            # Average a short neighbourhood to avoid triangle-to-triangle rocking.
            before,nb=sample(max(0,u-.018),deformed)
            after,na=sample(min(1,u+.018),deformed)
            normal=(normal+nb+na).normalized();surface_normal=normal.copy()
            up=(before-after).normalized()
            up=(up-normal*up.dot(normal)).normalized()
            side=up.cross(normal).normalized();up=normal.cross(side).normalized()
            desired=Matrix((side,up,normal)).transposed()
            target=(basis.inverted()@desired).to_quaternion()
            blend=smooth(.24,.31,q)*(1-smooth(.68,.75,q))
            rotation=Quaternion((1,0,0,0)).slerp(target,blend)
            change=basis@rotation.to_matrix()@basis.inverted()
            offsets=[change@v for v in upright_offsets]
            p0,n0=sample(0,deformed)
            correction=landing-(p0+n0*support(n0))
            pos=p+normal*support(normal)+correction*(1-smooth(0,.2,u))
            phase='surface_flow'
        elif q<.94:
            if release is None:
                p,normal=sample(1,deformed);release=p+normal*support(normal)
            # Freeze world X/Y at detachment; no animated-skin drift afterwards.
            seconds=min(.32,(q-.75)*4)
            pos=release+Vector((0,0,-.5*9.81*seconds*seconds))
            phase='vertical_immersion'
        else:
            end=release-Vector((0,0,.5*9.81*.32*.32))
            hidden=[end,Vector((0,0,-.18)),Vector((0,.02,.65)),Vector((0,.04,1.27)),Vector((.19,-.16,1.53)),start]
            x=max(0,min(5,(f-91)/6*5));i=min(4,int(x));pos=hidden[i].lerp(hidden[i+1],x-i)
            phase='submerged_return'
        pb=rig.pose.bones['drop'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=rotation
        pb.location=basis.inverted()@(pos-rest);pb.scale=fixed_scale
        for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group='drop')
        track.append({'frame':f,'phase':phase,'position':list(pos),
            'rotation_wxyz':list(rotation),'surface_normal':list(surface_normal) if surface_normal else None})
    for layer in rig.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if 'drop' in fc.data_path:
                        for k in fc.keyframe_points:k.interpolation='LINEAR'
    s.frame_set(1);s['revision']='10: tangent-aligned surface flow with upright free fall'
    models=[body,drop,core,bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]
    (out/'build-report.json').write_text(json.dumps({'revision':10,'fps':24,'frames':[1,97],
        'rig_bones':list(rig.data.bones.keys()),'meshes':{o.name:{'vertices':len(o.data.vertices),
        'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in models}},indent=2),encoding='utf8')
    (out/'revision-10.json').write_text(json.dumps({'revision':10,'drop_scale':list(fixed_scale),'release':list(release),'gravity_mps2':9.81,'track':track},indent=2),encoding='utf8')

if __name__=='__main__':
    from pathlib import Path
    import sys
    out=Path(__file__).resolve().parent;sys.path.insert(0,str(out))
    apply(bpy.context.scene,out)
    from refine_slime import export_and_render
    export_and_render(out)
