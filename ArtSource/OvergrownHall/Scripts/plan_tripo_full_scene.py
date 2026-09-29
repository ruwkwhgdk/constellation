"""Translate maintained layout markers into Tripo module instances (UE cm)."""
import bpy,json,math,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'TripoReplacement/v002'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Scene/v001/overgrown_hall_layout.blend'))
rows=[];random.seed(925)
def box(o):
    ps=[o.matrix_world@v.co for v in o.data.vertices]
    lo=Vector([min(p[i] for p in ps) for i in range(3)]); hi=Vector([max(p[i] for p in ps) for i in range(3)])
    return (lo+hi)/2,hi-lo,lo.z
def add(id,x,y,z,dims,yaw=0,pitch=0,roll=0,source='layout'):
    rows.append(dict(id=id,position=[-x*100,y*100,z*100],dimensions=list(dims),yaw=-yaw,pitch=pitch,roll=roll,source=source))
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    id=o.name[:2];c,d,z=box(o)
    if id in ['01','03']:
        add(id,c.x,c.y,z,d,source=o.name)
    elif id=='02':
        n=max(1,math.ceil(d.z/3)); h=d.z/n
        for k in range(n):add('02',c.x,c.y,z+k*h,(d.x,d.y,h),source=o.name)
    elif id in ['05','09']:
        side=d.y>d.x;length=max(d.x,d.y);n=max(1,math.ceil(length/(3 if id=='05' else 4)));w=length/n
        for k in range(n):
            offset=-length/2+(k+.5)*w
            add(id,c.x+(0 if side else offset),c.y+(offset if side else 0),z,(w,min(d.x,d.y),d.z),yaw=90 if side else 0,source=o.name)
    elif id=='13' and ('DryIsland' in o.name or 'BenchDryPatch' in o.name):
        add(id,c.x,c.y,z,(d.x,d.y,max(.045,d.z)),source=o.name)
    elif id in ['16','17','18'] and ('Foliage' in o.name or 'PlacedShrub' in o.name):
        if id=='16':dims=(.7,.7,max(.25,min(.6,d.z)))
        elif id=='17':dims=(max(.9,min(2,d.x)),max(.9,min(1.8,d.y)),max(.65,min(1.7,d.z)))
        else:dims=(.65,.18,1.65)
        add(id,c.x,c.y,max(0,z),dims,yaw=random.uniform(-180,180) if id!='18' else (90 if c.x>0 else -90),source=o.name)
    elif id=='26':add(id,c.x,c.y,c.z,(d.x,d.y,.16),roll=math.degrees(o.rotation_euler.y),source=o.name)
# Complete arch assemblies replace all old individual ring segments and jambs.
for x in [-6.35,6.35]:
    for y in [4,8,12,16]:add('04',x,y,.15,(3.7,.4,7.15),yaw=90)
    for y in [2,6,10,14,18]:add('11',x-math.copysign(.7,x),y,8.8,(1.5,.3,.35),pitch=18 if x>0 else -18)
    for y in [3,5]:add('25',x,y,.25,(2,.12,1),yaw=90)
for x0 in [-5.8,-2,2,5.8]:
    x=x0*.84*.78; w=(3.25 if abs(x0)>4 else 3.55)*.84*.78
    add('06',x,19.6,3,(w,.14,4.2))
    add('06',x,19.6,7.7,(w,.14,2))
    add('07',x,19.6,9.7,(w,.14,w/2))
    add('08',x,19.58,3,(.05,.08,4.2))
for y in [6,12,18]:add('10',0,y,10,(12.7,.22,2))
for x in [-6,-3,0,3,6]:
    for y in [3,7,11,15,19]:add('08',x,y,12-abs(x)*2/7.6,(.1,.1,4),roll=90)
add('12',0,19.65,0,(1.7,.5,2.2))
add('14',-1.2,10.2,0,(1.8,.65,.9),yaw=180)
for x in range(-7,8,2):
    for y in range(1,20,2):add('13',x,y,-.15,(2,2,.15))
# Exterior apron uses the same Tripo slab; retain continuous player collision.
for x in range(-28,29,8):
    for y in range(-14,51,8):
        if abs(x)<8 and -1<y<23:continue
        add('13',x,y,-.45,(8,8,.15),source='exterior apron')
for x,y in [(-5,7),(5,9),(-4.8,15),(4,18),(-2.5,18),(5.7,4)]:add('15',x,y,.01,(1.2,1,.45),yaw=random.uniform(-180,180))
assert set(r['id'] for r in rows)==set(['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','25','26'])
(OUT/'placements.json').write_text(json.dumps(rows,indent=2));print('TRIPO_PLACEMENTS',len(rows))
