from pathlib import Path
P=Path(__file__).resolve().parent
for file in ['import_unreal.py','materials_unreal.py','preview_unreal.py']:
 p=P/file
 exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
