import json, pathlib
def _load():
    here = pathlib.Path(__file__).parent
    with open(here/'bank.json','r',encoding='utf-8') as f:
        return json.load(f)
_BANK=_load()
_ID={q['id']:q for q in _BANK['questions']}
def get_bank(): return _BANK
def get_question_by_id(qid:str): return _ID.get(qid)
