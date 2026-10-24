"""Reject severe per-half-frame arm jumps. Visual anatomy remains a separate gate."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text());errors=[]
for n,row in d['max_half_frame_world_degrees'].items():
 if row['value']>15:errors.append(f"{n}: {row['value']:.2f} degrees at frame {row['frame']}")
for n,row in d['max_half_frame_position_mm'].items():
 if row['value']>35:errors.append(f"{n}: {row['value']:.2f} mm at frame {row['frame']}")
result={'passed':not errors,'errors':errors,'scope':'gross motion discontinuity guard only; not anatomical acceptance'}
p.with_name(p.stem+'-gate.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));sys.exit(bool(errors))
