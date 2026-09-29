"""Larger perimeter chips on the maintained slab; central bench support remains."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=(ROOT/'ArtSource/OvergrownHall/Scripts/build_shore_slab.py').read_text()
source=source.replace('TripoReplacement/v012','TripoReplacement/v017').replace('SM_OH_ShoreSlab','SM_OH_BenchShoreFinish')
source=source.replace("[(-.98,-.93,.20),(.96,.98,.19),(-.38,-1.02,.105),(.65,-1.02,.12)]","[(-.98,-.93,.34),(.96,.98,.30),(-.38,-1.02,.26),(.57,-1.04,.29),(.97,-.62,.22),(-.90,.90,.25)]")
exec(compile(source,'bench_shore_finish','exec'))
