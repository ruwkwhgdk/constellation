import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'NeutralExpression';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'ContourRepair/Delivery/Heroine_ContourRepair.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_ContourRepair'];me=body.data
sc=bpy.context.scene;cam=sc.camera;sc.cycles.samples=24
cam.location=(0,-3,.859);cam.rotation_euler=(Vector((0,0,.859))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.055;sc.render.resolution_x=1000;sc.render.resolution_y=650;sc.render.filepath=str(O/'renders/mouth_before.png');bpy.ops.render.render(write_still=True)
vs=[(v.index,*v.co) for v in me.vertices if abs(v.co.x)<.022 and .845<v.co.z<.875 and v.co.y<-.025]
(O/'mouth_vertices.json').write_text(json.dumps(vs))
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def delta(x,y,z):
 a=abs(x+.00024)
 lateral=smooth((a-.005)/.0045)*(1-smooth((a-.012)/.011))
 vertical=1-smooth((abs(z-.860)-.0045)/.0075)
 front=1-smooth((y+.022)/.012)
 return -.0005*lateral*vertical*front
orig=[v.co.copy() for v in me.vertices];oldnorm=[n.vector.copy() for n in me.corner_normals];changed=[]
for v in me.vertices:
 dz=delta(*v.co)
 if abs(dz)>1e-12:v.co.z+=dz;changed.append(v.index)
normals=[];eps=.00001
for li,l in enumerate(me.loops):
 x,y,z=orig[l.vertex_index];n=oldnorm[li]
 dx=(delta(x+eps,y,z)-delta(x-eps,y,z))/(2*eps);dy=(delta(x,y+eps,z)-delta(x,y-eps,z))/(2*eps);dz=(delta(x,y,z+eps)-delta(x,y,z-eps))/(2*eps)
 normals.append(Vector((n.x-dx*n.z/(1+dz),n.y-dy*n.z/(1+dz),n.z/(1+dz))).normalized())
me.update();me.normals_split_custom_set(normals)
body.name='Heroine_NeutralExpression'
sc.render.filepath=str(O/'renders/mouth_after.png');bpy.ops.render.render(write_still=True)
def render(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1100;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('face',(0,-3,.862),(0,0,.862),.30)
render('angle',(-.9,-3,.878),(0,0,.878),.25)
cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_NeutralExpression.blend'))
(O/'changes.json').write_text(json.dumps({'modified_vertices':len(changed),'max_corner_lowering':.0005,'topology_changed':False,'uv_changed':False,'textures_changed':False,'mouth_width_changed':False},indent=2))
