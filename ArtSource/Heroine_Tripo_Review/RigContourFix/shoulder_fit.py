import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def fit_point(p):
 q=p.copy();w=smooth((abs(p.x)-.028)/.072)*smooth((p.z-.69)/.080)
 q.x-=(1 if p.x>0 else -1)*.024*w;q.z-=.008*w
 return q
def eye_depth(p):
 ax=abs(p.x)
 anchor=-.052+.017*smooth((ax-.022)/.028)
 w=smooth((p.z-.881)/.006)*(1-smooth((p.z-.906)/.010))*smooth((ax-.010)/.008)*(1-smooth((ax-.049)/.013))
 strength=(.40+.35*smooth((ax-.027)/.020))*w
 return max(0,anchor-p.y)*strength
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=str(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend'))
 ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids'];o=bpy.data.objects['Heroine_DetailFinish2']
 edited=[];patch=set()
 for face in o.data.polygons:
  if o.data.materials[face.material_index].name.startswith('M_EyelidPatch'):patch.update(face.vertices)
 for v in o.data.vertices:
  c=ids[v.index];p=v.co.copy()
  if c in [3,4,32]:
   q=fit_point(p)
   if c==4:
    w=smooth((abs(p.x)-.065)/.060)*(1-smooth((abs(p.x)-.220)/.085))*smooth((p.z-.69)/.055)
    q.z-=(p.z-.785)*.24*w;q.y-=(p.y-.006)*.17*w
   v.co=q
  elif c in [14,21,29] or v.index in patch:
   v.co.y+=eye_depth(p)
  if (v.co-p).length>1e-9:edited.append(v.index)
 for ob in bpy.context.scene.objects:
  if ob.name.startswith(('Sclera_','Iris_Surface_','Lower_Eyelid_')):
   for v in ob.data.vertices:v.co.y+=eye_depth(v.co)
  elif ob.name.startswith('Lower_Lid_Skin_'):
   for v in ob.data.vertices:v.co.y+=eye_depth(v.co)
 bracelet=bpy.data.objects['Heroine_Pearl_Bracelet'];bracelet.location.x+=.024;bracelet.location.z-=.008
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'shoulder_source.blend'))
 (P/'edited_vertices.json').write_text(json.dumps(edited))
