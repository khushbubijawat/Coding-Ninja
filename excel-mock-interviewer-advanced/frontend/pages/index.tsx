// import { useEffect, useState } from 'react';
// import { apiStart, apiAnswer, apiReport } from '../lib/api';
// type Q = { id: string; prompt: string; kind: string; skill: string; max_score: number; hint?: string };
// export default function Home(){
//   const [interviewId,setInterviewId]=useState<string|null>(null);
//   const [q,setQ]=useState<Q|null>(null);
//   const [log,setLog]=useState<string[]>([]);
//   const [ans,setAns]=useState('');
//   const [done,setDone]=useState(false);
//   const [sum,setSum]=useState<any>(null);
//   useEffect(()=>{(async()=>{const d=await apiStart(); setInterviewId(d.interview_id); setQ(d.question); setLog(l=>[...l,'Agent: Hi! 6 questions in ~12 mins.']);})()},[]);
//   async function submit(wantHint=false){
//     if(!interviewId||!q) return;
//     const p:any={interview_id:interviewId,question_id:q.id,want_hint:wantHint};
//     if(q.kind==='table'){ try{ p.answer_table=JSON.parse(ans);}catch{ alert('For table questions, paste JSON array of objects.'); return; } } else { p.answer_text=ans; }
//     const d=await apiAnswer(p);
//     if(d.hint){ setLog(l=>[...l,`Agent (hint): ${d.hint}`]); return; }
//     setLog(l=>[...l,`You: ${ans}`,`Agent: ${d.feedback} (Score: ${d.score})`]); setAns('');
//     if(d.done){ setDone(true); setSum(d.summary); setQ(null); setLog(l=>[...l,`Agent: Interview complete. Band: ${d.summary.band}.`]); }
//     else { setQ(d.next_question); }
//   }
//   async function downloadReport(){
//     if(!interviewId) return;
//     const json=await apiReport(interviewId);
//     const blob=new Blob([JSON.stringify(json,null,2)],{type:'application/json'});
//     const url=URL.createObjectURL(blob); const a=document.createElement('a');
//     a.href=url; a.download=`report_${interviewId}.json`; a.click(); URL.revokeObjectURL(url);
//   }
//   return (<div style={{maxWidth:820,margin:'40px auto',fontFamily:'Inter,system-ui'}}>
//     <h1>Excel Mock Interviewer (Advanced PoC)</h1>
//     <div style={{border:'1px solid #ddd',borderRadius:8,padding:16,minHeight:300}}>
//       {log.map((t,i)=>(<div key={i} style={{marginBottom:8}}>{t}</div>))}
//       {q&&(<div style={{marginTop:16}}>
//         <div><b>Q ({q.skill}):</b> {q.prompt}</div>
//         <textarea value={ans} onChange={e=>setAns(e.target.value)} rows={5} style={{width:'100%',marginTop:8}} placeholder={q.kind==='table'?'[{"Region":"East","Sales":999.0}]':'Type your answer here'} />
//         <div style={{marginTop:8,display:'flex',gap:8}}>
//           <button onClick={()=>submit(false)}>Submit</button>
//           <button onClick={()=>submit(true)}>Hint</button>
//         </div>
//       </div>)}
//       {done&&sum&&(<div style={{marginTop:16}}>
//         <h3>Summary</h3>
//         <div>Band: <b>{sum.band}</b> ({sum.overall_percent}%)</div>
//         <div>Per-skill: {Object.entries(sum.per_skill).map(([k,v])=>`${k}: ${v}%`).join(' | ')}</div>
//         <div>Strengths: {sum.strengths.join(', ') || '-'}</div>
//         <div>Gaps: {sum.gaps.join(', ') || '-'}</div>
//         <div>Drills: {sum.drills.join('; ') || '-'}</div>
//         <button style={{marginTop:8}} onClick={downloadReport}>Download Report JSON</button>
//       </div>)}
//     </div>
//   </div>);
// }




import { useEffect, useMemo, useState } from 'react';
import { apiStart, apiAnswer, apiReport } from '../lib/api';

type Q = { id: string; prompt: string; kind: 'formula'|'value'|'table'|'text'; skill: string; max_score: number; hint?: string };

export default function Home(){
  const [interviewId,setInterviewId]=useState<string|null>(null);
  const [q,setQ]=useState<Q|null>(null);
  const [log,setLog]=useState<string[]>([]);
  const [ans,setAns]=useState('');
  const [done,setDone]=useState(false);
  const [sum,setSum]=useState<any>(null);

  useEffect(()=>{(async()=>{
    const d=await apiStart();
    setInterviewId(d.interview_id);
    setQ(d.question);
    setLog(l=>[...l,'Agent: Hi! 6 questions in ~12 mins.']);
  })()},[]);

  // --- live input kind detection (mirrors backend detect_kind) ---
  const detectedKind = useMemo<'formula'|'value'|'table'|'text'>(() => {
    if(!q) return 'text';
    if(q.kind==='table'){
      // soft detection: looks like JSON array?
      const t = ans.trim();
      if (t.startsWith('[') && t.endsWith(']')) {
        try { JSON.parse(t); return 'table'; } catch { /* fallthrough */ }
      }
      // if user typed valid JSON we’ll pass; else treat as text
      return 'text';
    }
    const t = ans.trim();
    if (t.startsWith('=')) return 'formula';
    if (t !== '' && !isNaN(Number(t))) return 'value';
    return 'text';
  }, [ans, q]);

  const placeholder = useMemo(() => {
    if(!q) return 'Type your answer here';
    switch(q.kind){
      case 'formula': return '=SUMIFS(D:D,A:A,"East",C:C,"Pencil")';
      case 'value':   return 'e.g., 19.99';
      case 'table':   return '[{"Region":"East","Sales":999.0}]';
      case 'text':    return '2–3 lines (e.g., when to use $ and table refs)';
      default:        return 'Type your answer here';
    }
  }, [q]);

  const canSubmit = !!q && detectedKind === q!.kind;

  async function submit(wantHint=false){
    if(!interviewId||!q) return;

    if (wantHint) {
      // ask for hint regardless of input
      const d = await apiAnswer({ interview_id:interviewId, question_id:q.id, want_hint:true });
      if (d.hint) setLog(l=>[...l,`Agent (hint): ${d.hint}`]);
      return;
    }

    if (!canSubmit) {
      setLog(l=>[...l, `Agent: Expected **${q.kind}**, but you entered **${detectedKind}**. Please adjust before submitting.`]);
      return;
    }

    const p:any={ interview_id:interviewId, question_id:q.id };
    if(q.kind==='table'){
      try {
        p.answer_table = JSON.parse(ans);
      } catch {
        alert('For table questions, paste a valid JSON array of objects, e.g. [{"Region":"East","Sales":999.0}]');
        return;
      }
    } else {
      p.answer_text = ans;
    }

    const d = await apiAnswer(p);

    // server may still enforce type-guard; reflect whatever it says
    if (d.hint){ setLog(l=>[...l,`Agent (hint): ${d.hint}`]); return; }

    setLog(l=>[...l, `You: ${ans}`, `Agent: ${d.feedback} (Score: ${d.score})`]);
    setAns('');

    if (d.done){
      setDone(true);
      setSum(d.summary);
      setQ(null);
      setLog(l=>[...l, `Agent: Interview complete. Band: ${d.summary.band}.`]);
    } else {
      setQ(d.next_question);
    }
  }

  async function downloadReport(){
    if(!interviewId) return;
    const json=await apiReport(interviewId);
    const blob=new Blob([JSON.stringify(json,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url; a.download=`report_${interviewId}.json`; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{maxWidth:820,margin:'40px auto',fontFamily:'Inter,system-ui'}}>
      <h1>Excel Mock Interviewer (Advanced PoC)</h1>

      <div style={{border:'1px solid #ddd',borderRadius:8,padding:16,minHeight:300}}>
        {log.map((t,i)=>(<div key={i} style={{marginBottom:8}} dangerouslySetInnerHTML={{__html:t}} />))}

        {q && (
          <div style={{marginTop:16}}>
            <div><b>Q ({q.skill}):</b> {q.prompt}</div>

            {/* Expected vs Detected */}
            <div style={{opacity:.75, marginTop:6}}>
              Expected: <b>{q.kind}</b>
              {q.kind==='formula' && ' (start with =)'}
              {q.kind==='value'   && ' (number only)'}
              {q.kind==='table'   && ' (JSON array of {Region, Sales})'}
              {q.kind==='text'    && ' (2–3 lines)'}
              <span style={{marginLeft:10, fontStyle:'italic'}}>Detected: {detectedKind}</span>
            </div>

            <textarea
              value={ans}
              onChange={e=>setAns(e.target.value)}
              rows={5}
              style={{width:'100%',marginTop:8}}
              placeholder={placeholder}
            />

            <div style={{marginTop:8,display:'flex',gap:8,alignItems:'center'}}>
              <button onClick={()=>submit(false)} disabled={!canSubmit} title={canSubmit?'':'Answer format does not match expected type'}>
                Submit
              </button>
              <button onClick={()=>submit(true)}>Hint</button>
              {!canSubmit && <span style={{fontSize:12,opacity:.7}}>Format mismatch — adjust your answer.</span>}
            </div>
          </div>
        )}

        {done && sum && (
          <div style={{marginTop:16}}>
            <h3>Summary</h3>
            <div>Band: <b>{sum.band}</b> ({sum.overall_percent}%)</div>
            <div>Per-skill: {Object.entries(sum.per_skill).map(([k,v])=>`${k}: ${v}%`).join(' | ')}</div>
            <div>Strengths: {sum.strengths.join(', ') || '-'}</div>
            <div>Gaps: {sum.gaps.join(', ') || '-'}</div>
            <div>Drills: {sum.drills.join('; ') || '-'}</div>
            <button style={{marginTop:8}} onClick={downloadReport}>Download Report JSON</button>
          </div>
        )}
      </div>
    </div>
  );
}
