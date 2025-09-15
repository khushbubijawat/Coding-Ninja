import re
from typing import Tuple
SUMIFS = re.compile(r"=\s*SUMIFS\(", re.IGNORECASE)
#XLOOKUP = re.compile(r"=\s*XLOOKUP\(", re.IGNORECASE)
#XLOOKUP = re.compile(r"=\s*XLOOKUP\s*\(", re.IGNORECASE)
XLOOKUP    = re.compile(r"=\s*XLOOKUP\s*\(", re.IGNORECASE)

#INDEX_MATCH = re.compile(r"=\s*INDEX\([^)]*MATCH\(", re.IGNORECASE)
#INDEX_MATCH = re.compile(r"=\s*INDEX\s*\([^)]*MATCH\s*\(", re.IGNORECASE)
INDEX_MATCH = re.compile(r"=\s*INDEX\s*\([^)]*MATCH\s*\(", re.IGNORECASE)

def evaluate_formula(q:dict, f:str)->Tuple[float,str,bool]:
    f=(f or '').strip(); mx=float(q.get('max_score',5))
    if not f.startswith('='): return 0.0,"Provide a valid Excel formula starting with '='.",False
    ok=False; efficient=True
    if q['id']=='q_sumifs_east_pencil': ok = bool(SUMIFS.search(f))
    if q['id']=='q_lookup_rep_item_price':
        if XLOOKUP.search(f): ok=True
        elif INDEX_MATCH.search(f): ok=True; efficient=False
    if ok: return (mx if efficient else mx-1),"Formula accepted.",True
    return 2.0,"Formula not recognized as correct for this task. Recheck ranges/criteria.",False
