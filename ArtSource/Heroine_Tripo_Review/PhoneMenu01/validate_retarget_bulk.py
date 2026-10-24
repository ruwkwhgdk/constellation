"""Use Blender bulk RNA reads with the same float values and lida hash schema."""
import sys,runpy,array
from pathlib import Path
sys.path.insert(0,"C:/Users/User/.codex/skills/lida-avatar-workflow/scripts")
import lida_model_tools as lida
original=lida._coordinates
def coordinates(items):
    values=array.array("f",[0.0])*(len(items)*3)
    items.foreach_get("co",values)
    result=list(zip(values[0::3],values[1::3],values[2::3]))
    if len(items):
        assert result[0]==tuple(float(v) for v in items[0].co)
        assert result[-1]==tuple(float(v) for v in items[-1].co)
    return result
lida._coordinates=coordinates
runpy.run_path(str(Path(__file__).parent/"validate_retarget.py"))
