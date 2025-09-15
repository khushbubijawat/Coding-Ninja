# import uuid, time, json
# from typing import Dict, Any, Optional, List
# from app.questions.bank import get_bank, get_question_by_id
# from app.db import SessionLocal, Interview, Answer
# _STORE: Dict[str, Dict[str, Any]] = {}
# def create_interview(email: Optional[str]=None)->Dict[str,Any]:
#     iid=str(uuid.uuid4()); bank=get_bank()
#     qids=[q['id'] for q in bank['questions']]
#     _STORE[iid]={'id':iid,'candidate_email':email,'created_at':time.time(),'asked':[],'answers':[],'scores':[],'hints':{},'question_ids':qids,'meta':{'difficulty':'E'}}
#     db=SessionLocal(); 
#     try: db.add(Interview(id=iid,candidate_email=email)); db.commit()
#     finally: db.close()
#     return _STORE[iid]
# def get_interview(iid:str)->Optional[Dict[str,Any]]: return _STORE.get(iid)
# def record_hint(iid:str,qid:str):
#     itv=_STORE[iid]; itv['hints'][qid]=itv['hints'].get(qid,0)+1
# def record_answer(iid:str,qid:str,txt,tab,score,fb):
#     itv=_STORE[iid]; itv['answers'].append({'qid':qid,'answer_text':txt,'answer_table':tab}); itv['scores'].append({'qid':qid,'score':score,'feedback':fb})
#     db=SessionLocal()
#     try:
#         db.add(Answer(interview_id=iid,question_id=qid,score=float(score or 0.0),feedback=fb or "",answer_text=txt or "",answer_table_json=json.dumps(tab) if tab else None)); db.commit()
#     finally: db.close()
# def _choose_next(iid:str)->Optional[str]:
#     itv=_STORE[iid]; ids:List[str]=itv['question_ids']; asked=set(itv['asked']); target='M'
#     if len(itv['scores'])>=2 and all(s['score']>=4 for s in itv['scores'][-2:]): target='H'
#     elif itv['scores'] and itv['scores'][-1]['score']<=2: target='E'
#     for qid in ids:
#         if qid in asked: continue
#         q=get_question_by_id(qid); 
#         if q and q.get('difficulty','M')==target: return qid
#     for qid in ids:
#         if qid not in asked: return qid
#     return None
# def next_question(iid:str):
#     itv=_STORE[iid]
#     if len(itv['asked'])>=6: return None
#     qid=_choose_next(iid); 
#     if not qid: return None
#     itv['asked'].append(qid); q=get_question_by_id(qid)
#     return {'id':q['id'],'prompt':q['prompt'],'kind':q['kind'],'skill':q['skill'],'max_score':q['max_score'],'hint':q.get('hint')}






import uuid, time, json
from typing import Dict, Any, Optional, List

from app.questions.bank import get_bank, get_question_by_id
from app.db import SessionLocal, Interview, Answer

# ---- in-memory store ----
_STORE: Dict[str, Dict[str, Any]] = {}

# Penalty per hint (points). Change to 0.25 or 1.0 if you prefer.
HINT_PENALTY = 0.5

# Max questions per interview
MAX_QUESTIONS = 6


def create_interview(email: Optional[str] = None) -> Dict[str, Any]:
    iid = str(uuid.uuid4())
    bank = get_bank()
    qids = [q["id"] for q in bank["questions"]]

    _STORE[iid] = {
        "id": iid,
        "candidate_email": email,
        "created_at": time.time(),
        "asked": [],              # list[str] of question ids asked (order)
        "answers": [],            # list of {qid, answer_text, answer_table}
        "scores": [],             # list of {qid, raw_score, final_score, feedback}
        "hints": {},              # dict[qid] -> count
        "question_ids": qids,     # full bank order for selection
        "meta": {"difficulty": "E"},
    }

    db = SessionLocal()
    try:
        db.add(Interview(id=iid, candidate_email=email))
        db.commit()
    finally:
        db.close()

    return _STORE[iid]


def get_interview(iid: str) -> Optional[Dict[str, Any]]:
    return _STORE.get(iid)


def record_hint(iid: str, qid: str):
    itv = _STORE[iid]
    itv["hints"][qid] = itv["hints"].get(qid, 0) + 1


def record_answer(iid: str, qid: str, txt, tab, score, fb):
    """
    Apply hint penalty and persist final_score (DB stores final_score).
    Keep both raw and final in memory for reporting/adaptivity.
    """
    itv = _STORE[iid]

    # Track the answer text/table
    itv["answers"].append(
        {"qid": qid, "answer_text": txt, "answer_table": tab}
    )

    # Compute hint penalty
    hints_used = itv["hints"].get(qid, 0)
    raw_score = float(score or 0.0)
    penalty = HINT_PENALTY * hints_used
    final_score = max(0.0, raw_score - penalty)

    # Make feedback transparent (optional)
    if hints_used > 0:
        fb = f"{fb} (−{penalty:.1f} for {hints_used} hint{'s' if hints_used!=1 else ''})"

    itv["scores"].append(
        {"qid": qid, "raw_score": raw_score, "final_score": final_score, "feedback": fb}
    )

    # Persist final_score to DB
    db = SessionLocal()
    try:
        db.add(
            Answer(
                interview_id=iid,
                question_id=qid,
                score=final_score,
                feedback=fb or "",
                answer_text=txt or "",
                answer_table_json=json.dumps(tab) if tab else None,
            )
        )
        db.commit()
    finally:
        db.close()


def _choose_next(iid: str) -> Optional[str]:
    """
    Simple adaptive chooser:
    - If last 2 final scores >= 4 -> target 'H'
    - Else if last final score <= 2 -> target 'E'
    - Else default 'M'
    Falls back to first unasked if none match target.
    """
    itv = _STORE[iid]
    ids: List[str] = itv["question_ids"]
    asked = set(itv["asked"])
    target = "M"

    recent = itv["scores"]
    if len(recent) >= 2 and all(s.get("final_score", 0.0) >= 4 for s in recent[-2:]):
        target = "H"
    elif recent and recent[-1].get("final_score", 0.0) <= 2:
        target = "E"

    # try to find next by target difficulty
    for qid in ids:
        if qid in asked:
            continue
        q = get_question_by_id(qid)
        if q and q.get("difficulty", "M") == target:
            return qid

    # fallback: first unasked
    for qid in ids:
        if qid not in asked:
            return qid

    return None


def next_question(iid: str):
    itv = _STORE[iid]
    if len(itv["asked"]) >= MAX_QUESTIONS:
        return None

    qid = _choose_next(iid)
    if not qid:
        return None

    itv["asked"].append(qid)
    q = get_question_by_id(qid)
    return {
        "id": q["id"],
        "prompt": q["prompt"],
        "kind": q["kind"],
        "skill": q["skill"],
        "max_score": q["max_score"],
        "hint": q.get("hint"),
    }
