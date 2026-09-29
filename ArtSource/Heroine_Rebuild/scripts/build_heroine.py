"""Art-directed hybrid rebuild. Source garment topology is retained and reduced;
head, eyes, hair and accessories are authored as separate editable meshes."""
import bpy, bmesh, math, json, shutil, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.kdtree import KDTree
from math import sin,cos,pi,exp,sqrt
ROOT=Path(__file__).resolve().parents[1]
bpy.context.preferences.filepaths.save_version=0
for d in ['textures','renders']: (ROOT/d).mkdir(exist_ok=True)
SRC='C:/Users/User/Desktop/Portfolio/Project Constellation/modeling/player_heroine/Player_Heroine.fbx'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=SRC)
body=next(o for o in bpy.context.scene.objects if o.type=='MESH'); body.name='Legs_Loafers_SourceRetained'
source_tree=KDTree(len(body.data.vertices))
source_weights=[]
for v in body.data.vertices:
    source_tree.insert(v.co,v.index);source_weights.append([(body.vertex_groups[g.group].name,g.weight) for g in v.groups])
source_tree.balance()
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE'); rig.name='Heroine_OriginalSkeleton'
rig.animation_data_clear()
for p in rig.pose.bones: p.matrix_basis.identity()
base=body.data.materials[0]; base.name='M_Garments_OriginalAtlas'
shader=next(n for n in base.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
shader.inputs['Roughness'].default_value=.88
shader.inputs['Specular IOR Level'].default_value=.18
shader.inputs['Emission Strength'].default_value=.06
baseimage=next(l.from_node for l in base.node_tree.links if l.to_socket.name=='Base Color')
base.node_tree.links.new(baseimage.outputs['Color'],shader.inputs['Emission Color'])
shader.inputs['Emission Strength'].default_value=.22
normal=next(n for n in base.node_tree.nodes if n.type=='NORMAL_MAP'); normal.inputs['Strength'].default_value=.025
for n in base.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
        old=Path(n.image.filepath); target=ROOT/'textures'/('Source_'+old.name)
        shutil.copy2(old,target); n.image.filepath=str(target)

# Keep only the source hands and lower legs. Garments are rebuilt as clean surfaces.
tex=next(l.from_node.image for l in base.node_tree.links if l.to_socket.name=='Base Color')
pixels=np.array(tex.pixels[:],dtype=np.float32).reshape(tex.size[1],tex.size[0],4)
bm=bmesh.new(); bm.from_mesh(body.data); uv=bm.loops.layers.uv.active
remove=[]
for f in bm.faces:
    c=f.calc_center_median()
    is_hair=False;is_skirt=False
    if c.z>.605 or -.05<c.z<.18:
        tc=sum((l[uv].uv for l in f.loops),Vector((0,0)))/len(f.loops)
        col=pixels[int(tc.y*(tex.size[1]-1))%tex.size[1],int(tc.x*(tex.size[0]-1))%tex.size[0],:3]
        is_hair=c.z>.605 and float(max(col))<.30 and (abs(c.x)>.046 or c.y>.032)
        is_skirt=-.05<c.z<.18 and col[2]>col[0]*1.015
    keep=(c.z<-.045)
    if not keep: remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES')
bm.to_mesh(body.data); bm.free()
bpy.context.view_layer.objects.active=body
dec=body.modifiers.new('Garment_LOD0_budget','DECIMATE'); dec.ratio=.60
bpy.ops.object.modifier_apply(modifier=dec.name)
for p in body.data.polygons:p.use_smooth=True

def image_data(name,arr):
    h,w=arr.shape[:2]; im=bpy.data.images.new(name,w,h,alpha=True)
    rgba=np.ones((h,w,4),np.float32);rgba[:,:,:3]=arr
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw=str(ROOT/'textures'/(name+'.png')); im.file_format='PNG'; im.save(); return im
def mat(name,color,rough=.65,image=None,emission=.10,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal
    n.inputs['Specular IOR Level'].default_value=.2;n.inputs['Emission Color'].default_value=(*color,1);n.inputs['Emission Strength'].default_value=emission
    if image:
        t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=image
        m.node_tree.links.new(t.outputs['Color'],n.inputs['Base Color']);m.node_tree.links.new(t.outputs['Color'],n.inputs['Emission Color'])
    return m

# UV-painted face: soft cheek blush and a warmer lower face, without baked lighting.
N=1024; u,v=np.meshgrid(np.linspace(0,1,N),np.linspace(0,1,N))
facecol=np.zeros((N,N,3),np.float32)+[.94,.775,.684]
for cu in [.5-.064,.5+.064]:
    a=np.exp(-(((u-cu)/.037)**2+((v-.45)/.075)**2))* .29
    facecol=facecol*(1-a[:,:,None])+np.array([.90,.34,.38])*a[:,:,None]
facecol+=np.exp(-((v-.64)/.24)**2)[:,:,None]*np.array([.018,.03,.038])
skin=mat('M_Face_Painted',(.94,.775,.684),.82,image_data('T_Face_BaseColor',np.clip(facecol,0,1)),.45)
skinplain=mat('M_Skin_Details',(.70,.49,.38),.82,emission=.45)
dark=mat('M_Lashes',(.021,.012,.024),.88,emission=.25)
mouthmat=mat('M_Mouth',(.30,.12,.12),.9,emission=.16)
white=mat('M_Eye_Sclera',(.94,.895,.86),.48,emission=.3)
hairmats=[]
for k in range(4):
    uu,vv=np.meshgrid(np.linspace(0,1,256),np.linspace(0,1,512))
    c=np.zeros((*uu.shape,3),np.float32)+np.array([.045,.035,.061])*(1+k*.09)
    sheen=np.exp(-((vv-.70-.035*np.sin(uu*pi))/ .09)**2)*(.6+.4*np.cos((uu-.5)*pi))
    fil=(np.cos(uu*pi*28+vv*2)*.5+.5)*.007
    c+=sheen[:,:,None]*np.array([.038,.027,.048])+fil[:,:,None]
    c*= (.78+.22*np.sin(uu*pi))[:,:,None]
    hairmats.append(mat('M_Hair_Ink_'+str(k),(.045,.035,.061),.58,image_data('T_Hair_'+str(k),c),.18))
purple=mat('M_Hairpin_Lavender',(.32,.20,.51),.36,emission=.10,metal=.25)
pinwhite=mat('M_Hairpin_Silver',(.64,.63,.68),.3,emission=.05,metal=.5)
pearl=mat('M_Pearl',(.88,.82,.78),.28,emission=.08)
stocking=mat('M_Stockings',(.023,.025,.029),.89,emission=.10)
leather=mat('M_Loafers',(.060,.035,.027),.52,emission=.10)
cardigan=mat('M_Cardigan_Knit',(.54,.365,.22),.92,emission=.23)
ku,kv=np.meshgrid(np.linspace(0,1,1024),np.linspace(0,1,1024))
stitch=np.sin(ku*2*pi*160+np.abs(((kv*210)%1)-.5)*3)*.007
knit=np.zeros((1024,1024,3),np.float32)+[.76,.635,.475]+stitch[:,:,None]
knitimage=image_data('T_Cardigan_Knit',knit)
kn=cardigan.node_tree.nodes.new('ShaderNodeTexImage');kn.image=knitimage
ks=next(n for n in cardigan.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
cardigan.node_tree.links.new(kn.outputs['Color'],ks.inputs['Base Color']);cardigan.node_tree.links.new(kn.outputs['Color'],ks.inputs['Emission Color'])
shirt=mat('M_Shirt',(.84,.855,.85),.87,emission=.22)
bowmat=mat('M_Ribbon',(.032,.105,.165),.64,emission=.18)
buttonmat=mat('M_Buttons',(.27,.175,.115),.60,emission=.17)
# Material boundaries are cut geometrically after the final reduction.
for material in [stocking,leather,cardigan,skinplain,shirt,bowmat]:body.data.materials.append(material)
uvdata=body.data.uv_layers.active.data
for p in body.data.polygons:
    c=p.center
    if c.z<-.85:p.material_index=2
    elif c.z<-.18:p.material_index=1
    elif c.z<.015:p.material_index=4
    elif c.z>.14 and abs(c.x)<.625:
        uvp=sum((uvdata[li].uv for li in p.loop_indices),Vector((0,0)))/len(p.loop_indices)
        col=pixels[int(uvp.y*(tex.size[1]-1))%tex.size[1],int(uvp.x*(tex.size[0]-1))%tex.size[0],:3]
        if col[2]>col[0]*1.05:p.material_index=6
        elif min(col)>.42 and max(col)-min(col)<.13:p.material_index=5
        else:p.material_index=3

assets=[body]
def bind(o,bone='mixamorig:Head'):
    g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
    mod=o.modifiers.new('Original_Skeleton','ARMATURE');mod.object=rig
    assets.append(o);return o
def mesh(name,verts,faces,uvs,material,bone='mixamorig:Head'):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(material)
    uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth=True
        for li in p.loop_indices: uv.data[li].uv=uvs[me.loops[li].vertex_index]
    return bind(o,bone) if bone else o
def sphere(name,loc,scale,material,segs=32,rings=20,bone='mixamorig:Head'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return bind(o,bone)
def tube(name,points,radii,material,sides=8,bone='mixamorig:Head'):
    verts=[];uvs=[];faces=[]
    for i,p in enumerate(points):
        p=Vector(p); tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        tangent.normalize();a=tangent.cross(Vector((0,1,0)))
        if a.length<.01:a=tangent.cross(Vector((1,0,0)))
        a.normalize();b=tangent.cross(a).normalized()
        r=radii[i] if isinstance(radii,list) else radii
        for j in range(sides):
            verts.append(p+r*(a*cos(2*pi*j/sides)+b*sin(2*pi*j/sides)));uvs.append((j/sides,i/(len(points)-1)))
    for i in range(len(points)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,uvs,material,bone)
def bez(p,t):return (1-t)**3*Vector(p[0])+3*(1-t)**2*t*Vector(p[1])+3*(1-t)*t*t*Vector(p[2])+t**3*Vector(p[3])

# Smooth anime head surface, jaw and nose built into the surface.
levels=[(.655,.009,.028,-.028),(.667,.034,.045,-.012),(.687,.061,.060,.003),(.710,.080,.067,.008),(.740,.094,.076,.014),(.775,.101,.086,.016),(.812,.102,.091,.018),(.850,.098,.092,.021),(.885,.083,.081,.023),(.913,.057,.058,.025),(.930,.008,.015,.025)]
def headprops(z):
    return [float(np.interp(z,[l[0] for l in levels],[l[j] for l in levels])) for j in range(1,4)]
def face_y(x,z):
    rx,ry,cy=headprops(z); a=max(.0001,1-(x/rx)**2)
    y=cy-ry*a**.24
    y-=.020*exp(-((x/.014)**2+((z-.749)/.016)**2))
    y-=.008*exp(-((x/.012)**2+((z-.777)/.032)**2))
    return y
verts=[];uvs=[];faces=[];nr=46;ns=80
for i in range(nr+1):
    z=.655+(.930-.655)*i/nr;rx,ry,cy=headprops(z)
    for j in range(ns+1):
        a=(j/ns-.5)*2*pi;x=rx*sin(a); y=cy-ry*(abs(cos(a))**.48)*(1 if cos(a)>=0 else -1)
        if cos(a)>0:y=face_y(x,z)
        verts.append((x,y,z));uvs.append((j/ns,i/nr))
for i in range(nr):
    for j in range(ns):
        a=i*(ns+1)+j;faces.append((a,a+1,a+ns+2,a+ns+1))
head=mesh('Face_QuadSurface',verts,faces,uvs,skin)
sphere('Neck_Surface',(0,.008,.647),(.037,.035,.075),skinplain,40,24,'mixamorig:Neck')
for s in [-1,1]:
    sphere('Ear_'+str(s),(s*.098,.003,.767),(.016,.011,.027),skinplain,24,16)

# Almond eye surfaces and separate dark eyelid ribbons.
def eye_edge(s,t,upper=True):
    x=s*(.015+.063*t); z=.787+.004*t+(sin(pi*t)**.82)*(.009 if upper else -.010)
    return x,z
for s in [-1,1]:
    ev=[];eu=[];ef=[];ac=40;rc=10
    # Radial almond patch. Slight convexity keeps the iris in front of the face.
    cx=s*.047;cz=.789
    ev.append((cx,face_y(cx,cz)-.007,cz));eu.append((.5,.5))
    for r in range(1,rc+1):
        for a in range(ac):
            ang=a/ac*2*pi;ex,ez=eye_edge(s,(cos(ang)+1)/2,sin(ang)>=0)
            x=cx+(ex-cx)*r/rc;z=cz+(ez-cz)*r/rc
            ev.append((x,face_y(x,z)-.002-.005*(1-(r/rc)**2),z));eu.append((.5+.5*cos(ang)*r/rc,.5+.5*sin(ang)*r/rc))
    for a in range(ac):ef.append((0,1+a,1+(a+1)%ac))
    for r in range(rc-1):
        for a in range(ac):
            b=1+r*ac+a;c=1+r*ac+(a+1)%ac;ef.append((b,c,c+ac,b+ac))
    mesh('Eye_White_'+str(s),ev,ef,eu,white)
    # Painted red-brown iris with radial fibers and upper shadow.
    uu,vv=np.meshgrid(np.linspace(-1,1,512),np.linspace(-1,1,512));rad=np.sqrt(uu**2+vv**2);ang=np.arctan2(vv,uu)
    a=np.clip((rad-.26)/.65,0,1)
    col=np.zeros((512,512,3),np.float32)+[.32,.080,.075]
    col+=np.clip(-vv,0,1)[:,:,None]*np.array([.22,.08,.055])
    col+=(np.sin(ang*43+rad*19)*.5+.5)[:,:,None]*np.array([.08,.03,.012])*a[:,:,None]
    mask=np.clip((rad-.78)/.18,0,1);col=col*(1-mask[:,:,None])+np.array([.035,.017,.026])*mask[:,:,None]
    pupil=np.exp(-((uu/.29)**4+(vv/.55)**4));col=col*(1-pupil[:,:,None])+np.array([.018,.009,.018])*pupil[:,:,None]
    shadow=np.clip(vv,0,1)*.65;col*=1-shadow[:,:,None]
    irismat=mat('M_Iris_'+str(s),(.4,.13,.09),.42,image_data('T_Iris_'+str(s),col),.45)
    iv=[(cx,face_y(cx,cz)-.009,cz)];iu=[(.5,.5)];ifs=[]
    for j in range(64):
        a=2*pi*j/64;x=cx+.0115*cos(a);z=cz+.0101*sin(a)
        iv.append((x,face_y(x,z)-.009,z));iu.append((.5+.5*cos(a),.5+.5*sin(a)))
    for j in range(64):ifs.append((0,1+j,1+(j+1)%64))
    mesh('Iris_'+str(s),iv,ifs,iu,irismat)
    for upper in [True,False]:
        ps=[];rs=[]
        for j in range(41):
            t=j/40;x,z=eye_edge(s,t,upper);ps.append((x,face_y(x,z)-.0035,z));rs.append((.0021 if upper else .00045)*sin(pi*t)**.4+.00015)
        tube(('UpperLash_' if upper else 'LowerLash_')+str(s),ps,rs,dark,6)
    for i in range(3):
        t=.78+i*.075;x,z=eye_edge(s,t);end=(x+s*(.007-i*.0009),face_y(x,z)-.004,z+.003+i*.0005)
        tube('LashTip',[(x,face_y(x,z)-.004,z),end],[.0017,.00005],dark,5)
    brow=[]
    for j in range(21):
        t=j/20;x=s*(.018+.058*t);z=.816+.003*sin(t*pi)-.004*t;brow.append((x,face_y(x,z)-.0018,z))
    tube('Brow_'+str(s),brow,[.0002+.0012*sin(pi*j/20)**.5 for j in range(21)],dark,6)
    catch=mat('M_EyeLight_'+str(s),(1,.96,.91),.2,emission=.9)
    for dx,dz,r in [(-.003,.004,.0027),(.004,-.005,.0012)]:
        x=cx+dx;z=cz+dz;sphere('Eye_Catchlight',(x,face_y(x,z)-.0105,z),(r,.0005,r),catch,16,10)

ps=[]
for j in range(25):
    x=-.011+.022*j/24;z=.712+.0006*cos(x/.011*pi/2)
    ps.append((x,face_y(x,z)-.0013,z))
tube('Mouth_Line',ps,[.00012+.0005*sin(pi*j/24) for j in range(25)],mouthmat,6)

# Closed, tapered hair ribbons. Each lock has deliberate longitudinal flow.
def lock(name,controls,width,material,steps=24,across=8,depth=.006):
    verts=[];uvs=[];faces=[]
    for layer in range(2):
        for i in range(steps+1):
            t=i/steps;c=bez(controls,t);tan=bez(controls,min(1,t+.01))-bez(controls,max(0,t-.01));tan.normalize()
            outward=Vector((c.x,(c.y-.025),max(0,c.z-.80)*.6)).normalized()
            side=tan.cross(outward).normalized();outward=side.cross(tan).normalized()
            w=width*(.18+.82*sin(pi*(t*.82+.10))**.65)*(1-t**5)+.0003
            for j in range(across+1):
                u=j/across*2-1; bulge=depth*(1-u*u)*(1 if layer==0 else -.28)*sin(pi*(t*.9+.05))
                verts.append(c+side*u*w+outward*bulge);uvs.append((j/across,1-t))
    row=across+1;lay=(steps+1)*row
    for l in range(2):
        for i in range(steps):
            for j in range(across):
                a=l*lay+i*row+j;f=(a,a+1,a+row+1,a+row);faces.append(f if l==0 else f[::-1])
    for i in range(steps):
        for j in [0,across]:
            a=i*row+j;faces.append((a,a+row,a+row+lay,a+lay))
    for j in range(across):
        faces.append((j,j+lay,j+lay+1,j+1));a=steps*row+j;faces.append((a,a+1,a+1+lay,a+lay))
    return mesh(name,verts,faces,uvs,material)

# Back mantle: overlapping locks conceal the scalp while leaving a broken bob outline.
sphere('Hair_Scalp',(0,.025,.832),(.104,.085,.125),hairmats[0],40,24)
vv=[];ff=[];uvs=[];rn=18;an=48
for i in range(rn+1):
    t=i/rn;z=.655+.245*t
    rx=np.interp(t,[0,.25,.65,1],[.080,.117,.129,.079]);ry=np.interp(t,[0,.25,.65,1],[.069,.092,.104,.080])
    for j in range(an+1):
        a=pi/2+pi*j/an;vv.append((rx*sin(a),.022-ry*cos(a),z));uvs.append((j/an,t))
for i in range(rn):
    for j in range(an):
        a=i*(an+1)+j;ff.append((a,a+1,a+an+2,a+an+1))
mesh('Hair_Nape_Underlayer',vv,ff,uvs,hairmats[0])
for i in range(17):
    a=-pi*.05+i/16*pi*1.1
    x=cos(a);y=sin(a)
    root=(.005+x*.012,.023+y*.012,.958)
    p1=(x*.119,.022+y*.112,.965)
    p2=(x*.151,.022+y*.124,.756)
    end=(x*(.119+.010*sin(i*2.7)),.022+y*.105,.672+.033*sin(i*1.9)**2)
    lock('Hair_Back_%02d'%i,[root,p1,p2,end],.025,hairmats[i%4],18,5)

# Side framing and irregular short tips.
for s in [-1,1]:
    for i in range(4):
        lock('Hair_Side_%s_%s'%(s,i),[(s*.011,.002-i*.007,.958),(s*(.123+i*.004),-.027-i*.018,.932),(s*(.151-i*.006),-.048-i*.019,.721),(s*(.091+i*.015),-.053-i*.008,.651+i*.015)],.022-i*.002,hairmats[i%4],20,6)

# Asymmetric fringe: exposed right eye (image left), left eye hidden.
fringes=[
    ([(-.012,-.015,.956),(-.068,-.103,.938),(-.099,-.111,.834),(-.075,-.103,.811)],.031),
    ([(.009,-.022,.955),(-.029,-.107,.936),(-.052,-.119,.867),(-.074,-.114,.838)],.027),
    ([(.024,-.019,.951),(.044,-.111,.927),(.020,-.130,.815),(-.015,-.119,.778)],.038),
    ([(.046,-.005,.942),(.090,-.105,.908),(.063,-.131,.792),(.015,-.123,.752)],.038),
    ([(.067,.003,.929),(.126,-.069,.883),(.108,-.110,.779),(.050,-.111,.742)],.034),
    ([(.087,.014,.910),(.135,-.022,.847),(.140,-.066,.758),(.086,-.090,.718)],.025),
]
for i,(controls,w) in enumerate(fringes):lock('Hair_Fringe_%02d'%i,controls,w,hairmats[i%4],24,7,.007)

# Hair pins sit visibly on the exposed temple.
for i,material in enumerate([purple,pinwhite]):
    tube('Hairpin_'+str(i),[(-.086,-.122-i*.001,.864-i*.013),(-.061,-.132-i*.001,.844-i*.012)],.0021,material,10)

# Original art's pearl bracelet on the character's right wrist.
for j in range(14):
    a=j/14*2*pi
    sphere('Bracelet_Pearl_%02d'%j,(-.615,.018+.024*cos(a),.542+.021*sin(a)),(.006,.006,.006),pearl,12,8,'mixamorig:RightHand')

# Five separate fingers on each hand; hand-level skinning preserves the original rig.
nailmat=mat('M_Nails',(.78,.55,.49),.48,emission=.25)
for sign in [-1,1]:
    cy=-.056 if sign==1 else .018;bone='mixamorig:'+('Left' if sign==1 else 'Right')+'Hand'
    sphere('Hand_Palm_'+str(sign),(sign*.655,cy,.542),(.032,.012,.026),skinplain,28,18,bone)
    for j,(dz,length,radius) in enumerate([(.020,.054,.0058),(.007,.066,.0064),(-.007,.060,.0061),(-.020,.046,.0050)]):
        ps=[];rs=[]
        for k in range(13):
            t=k/12;ps.append((sign*(.677+length*t),cy-.003*sin(pi*t),.542+dz-.003*t*t));rs.append(radius*(1-.26*t))
        tube('Finger_%s_%s'%(sign,j),ps,rs,skinplain,8,bone)
        sphere('Fingertip_%s_%s'%(sign,j),ps[-1],(radius*.8,radius*.74,radius*.74),skinplain,12,8,bone)
        sphere('Fingernail_%s_%s'%(sign,j),(sign*(.677+length-.009),cy-.006,.542+dz-.003),(.007,.00065,.0033),nailmat,12,8,bone)
    ps=[(sign*.640,cy,.526),(sign*.651,cy-.002,.510),(sign*.668,cy-.004,.498),(sign*.682,cy-.005,.496)]
    tube('Thumb_'+str(sign),ps,[.009,.008,.007,.0055],skinplain,10,bone)
    sphere('ThumbTip_'+str(sign),ps[-1],(.006,.0055,.0055),skinplain,12,8,bone)

# New pleated skirt: clean continuous UVs and a woven plaid texture.
def transfer_weights(o):
    o.vertex_groups.clear()
    for v in o.data.vertices:
        _,idx,_=source_tree.find(v.co)
        for name,w in source_weights[idx]:
            g=o.vertex_groups.get(name) or o.vertex_groups.new(name=name);g.add([v.index],w,'REPLACE')
def torso_weights(o):
    o.vertex_groups.clear()
    names=['mixamorig:Hips','mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2']
    gs=[o.vertex_groups.new(name=n) for n in names]
    for v in o.data.vertices:
        z=(o.matrix_world@v.co).z
        knots=[.12,.28,.42,.56]
        if z<=knots[0]:gs[0].add([v.index],1,'REPLACE')
        elif z>=knots[-1]:gs[-1].add([v.index],1,'REPLACE')
        else:
            for i in range(3):
                if knots[i]<=z<=knots[i+1]:
                    t=(z-knots[i])/(knots[i+1]-knots[i]);gs[i].add([v.index],1-t,'REPLACE');gs[i+1].add([v.index],t,'REPLACE');break

# Cardigan: tailored open front, gently gathered waist, separate sleeve tubes.
verts=[];uvs=[];faces=[];rows=44;seg=88
torso_levels=[(.100,.149,.093),(.135,.151,.096),(.22,.141,.096),(.31,.124,.080),(.40,.122,.079),(.48,.136,.079),(.54,.150,.073),(.59,.137,.057),(.618,.060,.041)]
for i in range(rows+1):
    t=i/rows;z=.10+.518*t
    rx=np.interp(z,[v[0] for v in torso_levels],[v[1] for v in torso_levels]);ry=np.interp(z,[v[0] for v in torso_levels],[v[2] for v in torso_levels])
    opening=.002+max(0,z-.387)*.205+max(0,.17-z)*.17
    gap=math.asin(min(.90,opening/rx))
    for j in range(seg+1):
        a=gap+(2*pi-2*gap)*j/seg
        fold=.0028*sin(a*9+z*24)*sin(pi*t)**2+.0017*sin(a*17-z*30)*sin(pi*t)
        x=(rx+fold)*sin(a);y=.010-(ry+fold)*cos(a)
        verts.append((x,y,z));uvs.append((j/seg,t))
for i in range(rows):
    for j in range(seg):
        a=i*(seg+1)+j;faces.append((a,a+1,a+seg+2,a+seg+1))
card=mesh('Cardigan_Tailored',verts,faces,uvs,cardigan,'mixamorig:Spine');torso_weights(card)
# Narrow placket follows the two open front edges.
for side in [0,seg]:
    ps=[verts[i*(seg+1)+side] for i in range(rows+1)]
    edge=tube('Cardigan_Placket',ps,.0032,cardigan,6,'mixamorig:Spine');torso_weights(edge)

vv=[];ff=[];uvs=[];bands=6;bs=128
for i in range(bands+1):
    t=i/bands;z=.099+.031*t;gap=math.asin((.002+max(0,.17-z)*.17)/.152)
    for j in range(bs+1):
        a=gap+(2*pi-2*gap)*j/bs;ridge=.00065*cos(a*96)
        vv.append(((.151+ridge)*sin(a),.010-(.096+ridge)*cos(a),z));uvs.append((j/bs,t))
for i in range(bands):
    for j in range(bs):
        a=i*(bs+1)+j;ff.append((a,a+1,a+bs+2,a+bs+1))
hem=mesh('Cardigan_Ribbed_Hem',vv,ff,uvs,cardigan,'mixamorig:Spine');torso_weights(hem)

for sign in [-1,1]:
    vv=[];uvs=[];ff=[];lengths=34;around=32
    for i in range(lengths+1):
        t=i/lengths;x=sign*(.072+.537*t)
        cy=(-.015-.042*t) if sign==1 else (.001+.017*t)
        cz=.569-.026*t
        cap=min(1,t/.18);cap=cap*cap*(3-2*cap)
        radius=.015+.039*cap+.004*sin(pi*t)-.022*t**9
        for j in range(around+1):
            a=j/around*2*pi
            folds=.0038*sin(t*35+cos(a)*2)*sin(pi*t)**.8+.0016*cos(a*7+t*8)
            y=cy+(radius+folds)*cos(a);z=cz+(radius+folds)*sin(a)
            vv.append((x,y,z));uvs.append((j/around,t))
    for i in range(lengths):
        for j in range(around):
            a=i*(around+1)+j;ff.append((a,a+1,a+around+2,a+around+1))
    sleeve=mesh('Cardigan_Sleeve_'+str(sign),vv,ff,uvs,cardigan,'mixamorig:Spine2')
    sleeve.vertex_groups.clear()
    side='Left' if sign==1 else 'Right'
    sg=[sleeve.vertex_groups.new(name=n) for n in ['mixamorig:Spine2','mixamorig:'+side+'Arm','mixamorig:'+side+'ForeArm']]
    for v in sleeve.data.vertices:
        x=abs(v.co.x)
        if x<.21:
            t=max(0,min(1,(x-.125)/.085));sg[0].add([v.index],1-t,'REPLACE');sg[1].add([v.index],t,'REPLACE')
        else:
            t=max(0,min(1,(x-.33)/.09));sg[1].add([v.index],1-t,'REPLACE');sg[2].add([v.index],t,'REPLACE')
    # Ribbed cuff, denser angular rhythm than the body fabric.
    vv=[];uvs=[];ff=[]
    for i in range(5):
        t=i/4;x=sign*(.590+.040*t);cy=-.056 if sign==1 else .018
        for j in range(65):
            a=j/64*2*pi;r=.0305+.0007*cos(a*32)
            vv.append((x,cy+r*cos(a),.543+r*sin(a)));uvs.append((j/64,t))
    for i in range(4):
        for j in range(64):
            a=i*65+j;ff.append((a,a+1,a+66,a+65))
    cuff=mesh('Cardigan_Cuff_'+str(sign),vv,ff,uvs,cardigan,'mixamorig:Spine2');transfer_weights(cuff)

# Shirt bib behind the V opening. Neck and collar remain separate editable pieces.
shirtbib=mesh('Shirt_Bib',[(-.054,-.046,.615),(.054,-.046,.615),(.001,-.065,.387),(-.001,-.065,.387)],[(0,1,2,3)],[(0,1),(1,1),(1,0),(0,0)],shirt,'mixamorig:Spine2')
# Rounded patch pockets on the cardigan, with stitched rim and shallow volume.
for s in [-1,1]:
    vv=[];uvs=[];ff=[];nx=16;ny=14
    for i in range(ny+1):
        t=i/ny;z=.150+.115*t
        for j in range(nx+1):
            u=j/nx; x=s*(.057+.068*u)
            rx=np.interp(z,[v[0] for v in torso_levels],[v[1] for v in torso_levels]);ry=np.interp(z,[v[0] for v in torso_levels],[v[2] for v in torso_levels])
            y=.010-ry*sqrt(max(.01,1-(x/rx)**2))-.003-.008*sin(pi*u)*sin(pi*t)
            vv.append((x,y,z+.008*(abs(2*u-1)**3)*(1-t)));uvs.append((u,t))
    for i in range(ny):
        for j in range(nx):
            a=i*(nx+1)+j;ff.append((a,a+1,a+nx+2,a+nx+1))
    pocket=mesh('Cardigan_Pocket_'+str(s),vv,ff,uvs,cardigan,'mixamorig:Spine');torso_weights(pocket)
    rim=tube('Pocket_Rib',[vv[ny*(nx+1)+j] for j in range(nx+1)],.003,cardigan,6,'mixamorig:Spine');torso_weights(rim)

# Bow loops with curved folded surfaces and pointed tails.
for s in [-1,1]:
    vv=[];uvs=[];ff=[];nu=16;nv=12
    for i in range(nu+1):
        t=i/nu
        for j in range(nv+1):
            w=j/nv*2-1;x=s*(.007+.047*t)
            z=.550+w*(.008+.025*sin(t*pi/2))+.009*t
            y=-.089-.012*sin(pi*t)-.006*(1-w*w)
            vv.append((x,y,z));uvs.append((t,j/nv))
    for i in range(nu):
        for j in range(nv):
            a=i*(nv+1)+j;ff.append((a,a+1,a+nv+2,a+nv+1))
    mesh('Ribbon_Loop_'+str(s),vv,ff,uvs,bowmat,'mixamorig:Spine2')
    tail=mesh('Ribbon_Tail_'+str(s),[(s*.006,-.093,.548),(s*.029,-.087,.538),(s*.041,-.096,.485),(s*.018,-.102,.495),(s*.005,-.102,.489)],[(0,1,2,3,4)],[(0,1),(1,1),(1,0),(.5,.2),(0,0)],bowmat,'mixamorig:Spine2')
sphere('Ribbon_Knot',(0,-.098,.55),(.010,.009,.013),bowmat,24,16,'mixamorig:Spine2')

uu,vv=np.meshgrid(np.linspace(0,1,2048),np.linspace(0,1,1024))
col=np.zeros((*uu.shape,3),np.float32)+[.033,.049,.081]
su=(uu*16)%1;sv=(vv*2.7)%1
col+=((su>.28)&(su<.53))[:,:,None]*np.array([.035,.036,.038])
col+=((sv>.28)&(sv<.52))[:,:,None]*np.array([.028,.030,.031])
for lo,hi in [(.17,.20),(.60,.625),(.655,.666)]:
    stripes=((su>lo)&(su<hi))|((sv>lo)&(sv<hi))
    col+=stripes[:,:,None]*np.array([.16,.15,.13])
col+=(np.sin(uu*2*pi*700)*np.cos(vv*2*pi*500))[:,:,None]*.002
plaid=mat('M_Skirt_Plaid',(.033,.049,.081),.90,image_data('T_Skirt_Plaid',col),.23)
verts=[];uvs=[];faces=[];rows=14;segments=192
for i in range(rows+1):
    t=i/rows;z=.133-.177*t
    for j in range(segments+1):
        a=j/segments*2*pi
        fold=(.002+.008*t)*(cos(a*16)+.23*cos(a*32))
        x=(.130+.059*t+fold)*sin(a);y=.014-(.075+.053*t+fold)*cos(a)
        verts.append((x,y,z+.0015*t*cos(a*16)));uvs.append((j/segments,1-t))
for i in range(rows):
    for j in range(segments):
        a=i*(segments+1)+j;faces.append((a,a+1,a+segments+2,a+segments+1))
skirt=mesh('Skirt_Pleated',verts,faces,uvs,plaid,'mixamorig:Hips')
# Preserve source skirt/body weighting by sampling the original bind mesh.
skirt.vertex_groups.clear()
for v in skirt.data.vertices:
    _,idx,_=source_tree.find(v.co)
    for name,w in source_weights[idx]:
        g=skirt.vertex_groups.get(name) or skirt.vertex_groups.new(name=name);g.add([v.index],w,'REPLACE')
bpy.context.view_layer.objects.active=skirt
sol=skirt.modifiers.new('Hem_Thickness','SOLIDIFY');sol.thickness=.0012
bpy.ops.object.modifier_apply(modifier=sol.name)

# Clean collar leaves cover the cut upper boundary of the retained source shirt.
for s in [-1,1]:
    verts=[(s*.023,-.031,.641),(s*.049,-.011,.635),(s*.069,-.049,.598),(s*.042,-.089,.559),(s*.012,-.066,.600)]
    collar=mesh('Shirt_Collar_'+str(s),verts,[(0,1,2,3,4)],[(0,1),(1,1),(1,.5),(.5,0),(0,.4)],shirt,'mixamorig:Neck')
    bpy.context.view_layer.objects.active=collar
    sol=collar.modifiers.new('Tailored_Thickness','SOLIDIFY');sol.thickness=.002;bpy.ops.object.modifier_apply(modifier=sol.name)
    bev=collar.modifiers.new('Soft_Seam','BEVEL');bev.width=.001;bev.segments=2;bpy.ops.object.modifier_apply(modifier=bev.name)

# Distinct buttons on the cardigan front; original raised button forms remain beneath.
for i,(z,y) in enumerate([(.40,-.081),(.32,-.093),(.24,-.102),(.165,-.102),(.104,-.105)]):
    rx=np.interp(z,[v[0] for v in torso_levels],[v[1] for v in torso_levels]);ry=np.interp(z,[v[0] for v in torso_levels],[v[2] for v in torso_levels])
    x=.006+max(0,z-.387)*.205+max(0,.17-z)*.17
    y=.010-ry*sqrt(1-(x/rx)**2)-.002
    b=sphere('Cardigan_Button_%02d'%i,(x,y,z),(.0055,.0025,.0065),buttonmat,16,10,'mixamorig:Spine');torso_weights(b)

# Consistent mesh normals and four normalized skeletal influences.
for o in assets:
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for v in o.data.vertices:
        weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-7],key=lambda x:-x[1])
        total=sum(w for g,w in weights[:4])
        for gi,w in weights:
            if (gi,w) not in weights[:4]:o.vertex_groups[gi].remove([v.index])
            else:o.vertex_groups[gi].add([v.index],w/total,'REPLACE')

# Match total budget by adapting only the retained source body.
other=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in assets if o!=body)
target=12000
bodytris=sum(len(p.vertices)-2 for p in body.data.polygons)
if target>1000 and bodytris>target:
    bpy.context.view_layer.objects.active=body
    dec=body.modifiers.new('Final_LOD0_budget','DECIMATE');dec.ratio=target/bodytris;bpy.ops.object.modifier_apply(modifier=dec.name)

# The new surfaces have continuous UVs, so their reduction does not cross atlas islands.
otherbudget=66500-sum(len(p.vertices)-2 for p in body.data.polygons)
ratio=min(1,otherbudget/other)
for o in assets:
    count=sum(len(p.vertices)-2 for p in o.data.polygons)
    if o!=body and count>300 and ratio<1:
        bpy.context.view_layer.objects.active=o
        d=o.modifiers.new('LOD0_Surface_Budget','DECIMATE');d.ratio=ratio;bpy.ops.object.modifier_apply(modifier=d.name)
# Split exact stocking and shoe boundaries after decimation, preventing sawtooth edges.
bm=bmesh.new();bm.from_mesh(body.data)
for z in [-.18,-.85]:
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
for f in bm.faces:
    z=f.calc_center_median().z;f.material_index=2 if z<-.85 else 1 if z<-.18 else 4
bm.to_mesh(body.data);bm.free()
for p in body.data.polygons:p.use_smooth=True
body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))

# Re-limit interpolated weights after final collapse.
for o in assets:
    for v in o.data.vertices:
        allw=sorted([(g.group,g.weight) for g in v.groups],key=lambda t:-t[1])
        keep=allw[:4];total=sum(w for _,w in keep)
        for gi,_ in allw:o.vertex_groups[gi].remove([v.index])
        if total:
            for gi,w in keep:o.vertex_groups[gi].add([v.index],w/total,'REPLACE')

# Export rest pose. Preserve imported bone names and reference transforms.
# Remove unassigned material slots before merging the export copy.
for o in assets:
    used=sorted(set(p.material_index for p in o.data.polygons));mats=[o.data.materials[i] for i in used]
    remap={old:new for new,old in enumerate(used)}
    indices=[remap[p.material_index] for p in o.data.polygons]
    o.data.materials.clear()
    for m in mats:o.data.materials.append(m)
    for p,i in zip(o.data.polygons,indices):p.material_index=i
bpy.ops.object.select_all(action='DESELECT');export_copies=[]
for o in assets:
    d=o.copy();d.data=o.data.copy();bpy.context.collection.objects.link(d);d.select_set(True);export_copies.append(d)
bpy.context.view_layer.objects.active=export_copies[0];bpy.ops.object.join();export_mesh=bpy.context.object;export_mesh.name='SK_Heroine_Rebuild'
rig.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'Heroine_Rebuild.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_armature_deform_only=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
bpy.data.objects.remove(export_mesh,do_unlink=True)

stats={'total_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in assets),'bones':len(rig.data.bones),'parts':[{'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in assets], 'source_reuse':'Lower legs/thighs/shoes geometry and original skeleton retained. Face, eyes, hair, neck, hands, cardigan, shirt, bow, skirt and accessories newly built. Fingers use hand-level weights.'}
(ROOT/'build_stats.json').write_text(json.dumps(stats,indent=2))

# Studio rig, deliberately soft illumination to inspect material colors.
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=40
sc.render.resolution_x=1000;sc.render.resolution_y=1400;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX';sc.world.color=(.18,.18,.18)
def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,color in [('Key',(-3,-4,5),220,4,(1,.89,.80)),('Fill',(3,-2,2),130,4,(.78,.86,1)),('Rim',(1,3,3),260,3,(.84,.88,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.name=name;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.data.color=color;point(l,(0,0,.1))
floor=mat('Studio_Ground',(.16,.19,.23),.9,emission=0)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.955));bpy.context.object.name='Studio_Ground';bpy.context.object.data.materials.append(floor)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Review_Camera';sc.camera=cam;cam.data.type='ORTHO';cam.data.lens=70

# Neutral relaxed preview, export remains rest pose.
for name,angle in [('mixamorig:LeftArm',68),('mixamorig:RightArm',-68)]:
    p=rig.pose.bones[name];p.rotation_mode='QUATERNION'
    axis=(rig.matrix_world@p.bone.matrix_local).to_quaternion().inverted()@Vector((0,1,0))
    p.rotation_quaternion=Quaternion(axis,math.radians(angle))
rig['export_note']='FBX exported in original rest pose. Blend uses relaxed review pose.'
for m in list(bpy.data.materials):
    if m.users==0:bpy.data.materials.remove(m)
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0 and im.users:im.pack()
cam.location=(.65,-4,.30);point(cam,(0,0,.02));cam.data.ortho_scale=2.16
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Heroine_Rebuild.blend'))
for name,loc,target,scale,res in [('portrait',(0,-4,.79),(0,0,.79),.55,(1100,1100)),('front',(0,-5,.03),(0,0,.03),2.16,(1000,1400)),('three_quarter',(3,-4,.13),(0,0,.03),2.16,(1000,1400)),('back',(0,5,.03),(0,0,.03),2.16,(1000,1400)),('side',(5,0,.03),(0,0,.03),2.16,(1000,1400))]:
    if '--quick' in sys.argv:
        if name not in ['portrait','front']:continue
        res=tuple(int(n*.6) for n in res);sc.cycles.samples=16
    cam.location=loc;point(cam,target);cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=res
    sc.render.filepath=str(ROOT/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',json.dumps(stats))
