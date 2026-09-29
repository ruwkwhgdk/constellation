import json
from pathlib import Path
p=Path(__file__).resolve().parent
d=json.loads((p/'reference_motion.json').read_text())
for i in range(0,73,6):
 b=d['samples'][i]['bones'];hip=[(b['LeftUpLeg']['head'][k]+b['RightUpLeg']['head'][k])/2 for k in range(3)]
 print(i+1,{n:[round(v-hip[k],3) for k,v in enumerate(b[n]['head'])] for n in ['RightHand','LeftHand','LeftFoot','RightFoot']})
