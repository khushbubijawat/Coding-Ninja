# import os
# from typing import Tuple
# def evaluate_text_with_rubric(q:dict, ans:str)->Tuple[float,str,bool]:
#     mx=float(q.get('max_score',5)); text=(ans or '').lower()
#     hits=sum(1 for kw in ['absolute','$','anchor','table','structured reference','named range'] if kw in text)
#     score=min(mx,1.0+hits); return score,"Rule-based scoring (no OpenAI key).",score>=mx*0.6




import os, json
from typing import Tuple

def evaluate_text_with_rubric(question: dict, answer_text: str) -> Tuple[float, str, bool]:
    """
    Uses OpenAI if OPENAI_API_KEY is set; otherwise falls back to rule-based scoring.
    Returns: (score: float, feedback: str, is_pass: bool)
    """
    max_score = float(question.get("max_score", 5))
    key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # If no key -> fallback
    if not key:
        return _fallback_rule_based(answer_text, max_score, "no OpenAI key")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)

        payload = {
            "rubric": question.get("rubric", []),
            "answer": answer_text,
            "return_format": {
                "score": "0-5 (number)",
                "reasons": "list of 1-3 short bullets",
                "tags": "list of short labels"
            }
        }

        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},   # force JSON
            messages=[
                {"role": "system", "content": "You are a strict Excel evaluator. Return ONLY valid JSON."},
                {"role": "user", "content": json.dumps(payload)}
            ],
        )

        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)

        # Parse + clamp score
        score = float(data.get("score", 0))
        score = max(0.0, min(score, max_score))
        ok = score >= max_score * 0.6
        return score, "LLM-graded.", ok

    except Exception as e:
        # Any API/JSON issue -> safe fallback
        return _fallback_rule_based(answer_text, max_score, f"LLM error: {e}")

def _fallback_rule_based(text: str, max_score: float, note: str = None):
    t = (text or "").lower()
    hits = sum(1 for kw in ["absolute", "$", "anchor", "table", "structured reference", "named range"] if kw in t)
    score = min(max_score, 1.0 + hits)
    fb = "Rule-based scoring" + (f" ({note})" if note else " (no OpenAI key).")
    return score, fb, score >= max_score * 0.6
