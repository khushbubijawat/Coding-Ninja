// export async function apiStart(candidate_email?: string) {
//   const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/start`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ candidate_email }) });
//   return res.json();
// }
// export async function apiAnswer(payload: any) {
//   const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/answer`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
//   return res.json();
// }
// export async function apiReport(interview_id: string) {
//   const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/report/${interview_id}`);
//   return res.json();
// }




// frontend/lib/api.ts
const BASE = (process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000').replace(/\/+$/,'');

async function asJson(res: Response) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    // show helpful error in Next overlay
    throw new Error(`API ${res.url} returned ${res.status} ${res.statusText}. Body:\n${text}`);
  }
}

export async function apiStart(candidate_email?: string) {
  const res = await fetch(`${BASE}/start`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ candidate_email }),
  });
  if (!res.ok) throw new Error(`Failed /start: ${res.status} ${res.statusText}`);
  return asJson(res);
}

export async function apiAnswer(payload: any) {
  const res = await fetch(`${BASE}/answer`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed /answer: ${res.status} ${res.statusText}`);
  return asJson(res);
}

export async function apiReport(interview_id: string) {
  const res = await fetch(`${BASE}/report/${encodeURIComponent(interview_id)}`);
  if (!res.ok) throw new Error(`Failed /report: ${res.status} ${res.statusText}`);
  return asJson(res);
}
