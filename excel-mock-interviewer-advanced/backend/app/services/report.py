from typing import Dict, Any
from collections import defaultdict
from app.questions.bank import get_question_by_id
def generate_report(itv: Dict[str, Any]):
    scores=itv.get('scores',[]); total=0.0; skill_totals=defaultdict(float); skill_max=defaultdict(float)
    for s in scores:
        q=get_question_by_id(s['qid']); 
        if not q: continue
        skill=q.get('skill','general'); total+=s['score']; skill_totals[skill]+=s['score']; skill_max[skill]+=q.get('max_score',5)
    overall_max=sum(skill_max.values()) or 1.0; pct=100.0*total/overall_max
    band='Advanced' if pct>=85 else 'Intermediate' if pct>=65 else 'Beginner'
    strengths=[k for k,v in skill_totals.items() if 100.0*v/(skill_max[k] or 1.0)>=75]
    gaps=[k for k,v in skill_totals.items() if 100.0*v/(skill_max[k] or 1.0)<55]
    drills=[f"Practice more on: {', '.join(gaps)}"] if gaps else []
    return {'total_score':round(total,2),'overall_percent':round(pct,1),'band':band,'per_skill':{k:round(100.0*v/(skill_max[k] or 1.0),1) for k,v in skill_totals.items()},'strengths':strengths,'gaps':gaps,'drills':drills,'answers':itv.get('answers',[]),'scores':scores}
