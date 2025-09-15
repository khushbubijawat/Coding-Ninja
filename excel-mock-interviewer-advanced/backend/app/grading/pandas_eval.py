import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
import pathlib
DATA_DIR = pathlib.Path(__file__).parents[1] / 'questions' / 'datasets'
def _csv(n): return pd.read_csv(DATA_DIR / n)
def evaluate(q:dict, answer_text: Optional[str], answer_table: Optional[List[Dict[str, Any]]])->Tuple[float,str,bool]:
    k=q.get('kind'); key=q.get('eval_key'); mx=float(q.get('max_score',5))
    if k=='value':
        exp=_val(key)
        try: ans=float(str(answer_text).strip())
        except: return 0.0,"Answer must be a numeric value.",False
        return (mx,"Correct numeric result.",True) if abs(ans-exp)<=1e-6 else (2.0,f"Expected {exp}, got {ans}.",False)
    if k=='table':
        exp=_tab(key).copy()
        try: ans=pd.DataFrame(answer_table or [])
        except: return 0.0,"Answer must be a JSON array of objects.",False
        req=['Region','Sales']; miss=[c for c in req if c not in ans.columns]
        if miss: return 1.0,f"Missing columns: {miss}. Expected: {req}.",False
        exp['Sales']=pd.to_numeric(exp['Sales'], errors='coerce').round(2)
        ans['Sales']=pd.to_numeric(ans['Sales'], errors='coerce').round(2)
        exp=exp[req].sort_values(['Sales','Region'], ascending=[False,True]).reset_index(drop=True)
        ans=ans[req].sort_values(['Sales','Region'], ascending=[False,True]).reset_index(drop=True)
        if len(ans)!=len(exp): return 1.5,f"Row count mismatch: expected {len(exp)}, got {len(ans)}.",False
        if exp.equals(ans): return mx,"Correct table.",True
        diff=(exp!=ans).any(axis=1).to_list(); idx=diff.index(True) if True in diff else 0
        return 2.0,f"Table differs near row {idx+1}. Expected {exp.iloc[idx].to_dict()}, got {ans.iloc[idx].to_dict()}.",False
    return 0.0,"Unsupported kind.",False
def _val(key:str):
    if key=='total_units_east_pencil':
        df=_csv('sales.csv'); return float(df[(df.Region=='East')&(df.Item=='Pencil')]['Units'].sum())
    if key=='unitprice_rep_item':
        df=_csv('sales.csv'); r=df[(df.Rep=='Kivell')&(df.Item=='Binder')]
        return float(r['UnitPrice'].iloc[0]) if not r.empty else float('nan')
    return float('nan')
def _tab(key:str):
    if key=='region_total_sales_desc':
        df=_csv('sales.csv'); df['Sales']=df['Units']*df['UnitPrice']
        return df.groupby('Region',as_index=False)['Sales'].sum().sort_values('Sales',ascending=False)
    import pandas as pd; return pd.DataFrame()
