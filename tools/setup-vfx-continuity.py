from pathlib import Path
root=Path(__file__).resolve().parent
for name in ['generate-combat-hit-reactions.py','polish-combat-vfx-materials.py']:
 exec(compile((root/name).read_text(encoding='utf-8-sig'),str(root/name),'exec'),{'__file__':str(root/name)})
