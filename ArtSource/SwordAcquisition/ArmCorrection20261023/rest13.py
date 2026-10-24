import bpy,json
from pathlib import Path
P=Path(__file__).parent;data={}
for label,file in [('source',P.parent/'GripRevision20261023/Heroine_Sword_RightUpper06.blend'),('final',P/'Heroine_Sword_ArmCorrection13.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];data[label]={'bones':{b.name:{'parent':b.parent.name if b.parent else None,'matrix':[list(row) for row in b.matrix_local],'deform':b.use_deform} for b in r.data.bones},'object_world':[list(row) for row in r.matrix_world]}
result={'equal':data['source']==data['final'],'bone_count':len(data['source']['bones'])};(P/'rest_skeleton13.json').write_text(json.dumps(result,indent=2));print(result);assert result['equal']
