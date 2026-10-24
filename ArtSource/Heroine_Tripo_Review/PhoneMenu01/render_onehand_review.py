import sys,runpy
from pathlib import Path
sys.argv.append("--no-shadows")
runpy.run_path(str(Path(__file__).parent/"render_free_preview.py"))
