from pathlib import Path
p=Path(__file__).parent
exec(compile((p/'apply.py').read_text(),str(p/'apply.py'),'exec'))
exec(compile((p/'verify_preview.py').read_text(),str(p/'verify_preview.py'),'exec'))
