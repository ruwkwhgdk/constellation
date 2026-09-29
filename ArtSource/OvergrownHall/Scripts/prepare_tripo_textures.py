"""Re-encode supplied PBR maps without resizing or painting; run before Blender."""
from PIL import Image
from pathlib import Path
import csv
p=Path(__file__).resolve().parents[1]/'TripoReplacement/v002'
for r in csv.DictReader((p/'jobs.csv').open()):
    folder=p/(r['id']+'_'+r['name'])
    for suffix in ['basecolor','normal','rm']:
        source=next(f for f in (folder/'Original').rglob('*') if f.is_file() and f.stem.lower().endswith('_'+suffix))
        with Image.open(source) as im:im.save(folder/(suffix+'.png'))
print('TRIPO_PBR_MAPS_READY: 57')
