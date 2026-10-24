import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
P=Path(__file__).parent;O=P/'Delivery';O.mkdir(exist_ok=True)
source=P/'Heroine_Sword_ArmCorrection03.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy']
Q=Path('C:/Users/User/Documents/Constellation_ArtWorkspace/ArtSource/Heroine_Rebuild/GamePilot/Revision01');ref=json.loads((Q/'motion_delivery_dump.json').read_text())['reference'];fit=np.array(json.loads((Q/'geometry_info.json').read_text())['fit']);ar=np.eye(4);ar[:3]=fit.T;A=Matrix(ar.tolist());Ai=A.inverted()
def unpack(v):
 q=v['q'];m=Quaternion((q[3],*q[:3])).to_matrix().to_4x4()
 for i in range(3):
  for j in range(3):m[i][j]*=v['s'][j]
 m.translation=Vector(v['t']);return m
def pack(m):
 t,q,z=m.decompose();return {'t':list(t),'q':[q.x,q.y,q.z,q.w],'s':list(z)}
rest={b.name:b.matrix_local.copy() for b in r.data.bones};clips={};s.frame_set(1)
pelvis=A@r.pose.bones['pelvis'].matrix@rest['pelvis'].inverted()@Ai@unpack(ref['pelvis'])
shift=pelvis.translation-Vector(ref['pelvis']['t']);shift.z=0
ranges={'Approach':(1,100),'BraceLoop':(100,172),'ExtractRecover':(244,355),'ReleaseLeft':(415,457),'Raise':(457,523),'RaisedHoldLoop':(523,595),'Lower':(667,739)}
for name,(start,end) in ranges.items():
 rows=[];sword=[]
 for f in range(start,end+1):
  s.frame_set(f);row={b.name:A@b.matrix@rest[b.name].inverted()@Ai@unpack(ref[b.name]) for b in r.pose.bones}
  for n in row:
   if n!='root':row[n].translation-=shift
  rows.append({n:pack(m) for n,m in row.items()})
  # Reflected Blender->Unreal basis: conjugate orientation; translate separately.
  sm=A@r.matrix_world.inverted()@sw.matrix_world@Ai;sm.translation=A@(r.matrix_world.inverted()@sw.matrix_world.translation)-shift
  sword.append(pack(sm))
 clips[name]={'fps':30,'rows':rows,'sword':sword,'duration':(end-start)/30,'loop':name.endswith('Loop')}
(O/'motion.json').write_text(json.dumps({'parents':{b.name:b.parent.name if b.parent else None for b in r.data.bones},'clips':clips,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'alignment_shift':list(shift)}))
print('SWORD_CLIPS_EXPORTED',flush=True)

(O/'sword_tracks.json').write_text(json.dumps({'fps':30,'space':'Unreal component space, centimetres; pivot at guard centre; proxy blade points local -Z','source':str(source),'clips':{n:{k:v for k,v in c.items() if k!='rows'} for n,c in clips.items()}},indent=2))


