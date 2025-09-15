AI-powered mock interviewer to assess Excel skills with a structured, interview-style flow.
It asks 6 questions across skills (Aggregation, Lookups, Efficiency, etc.), evaluates answers intelligently, adapts difficulty, and ends with a constructive report.

Built as a hybrid Product/Engineering solution: deterministic grading for formulas/tables, LLM-assisted grading for short text, and robust agentic state management for a realistic interview.

Features

Structured flow: intro → questions (with hints) → summary

Type-guarding: prevents accidental progress on wrong answer types (formula / value / table / text)

Deterministic grading:

Formulas via rule checks (e.g., SUMIFS, INDEX/MATCH, XLOOKUP)

Tables/values via pandas evaluation

LLM-assisted grading (optional): short text answers with rubric

Adaptive difficulty: moves between E/M/H based on recent scores

Hint penalty: default −0.5 per hint, applied to the final score

Report: banding, per-skill %, strengths, gaps, suggested drills

Admin metrics: total answers, avg score, per-skill averages

Front-end UX: shows Expected vs Detected type + disables submit on mismatch



Tech Stack & Rationale

Backend: FastAPI (simple, fast, great DX)

Grading: Rule-based for formula/value/table (deterministic), LLM for short text only

LLM: OpenAI (pluggable via env); if no key → graceful fallback

DB: SQLite in PoC; SQLAlchemy models; easy to swap later

Frontend: Next.js 14 + React 18, simple single-page UI, strong UX for answer types

Hosting:

Backend → Render (Web Service)

Frontend → Vercel/Netlify (or Render Static Site)

⚙️ Environment Variables

Backend (excel-mock-interviewer-advanced/backend/.env)

Never commit secrets. Create locally or on the host.

# Optional: turns LLM grading ON when present
OPENAI_API_KEY=sk-...

# Optional: model for short-text grading
LLM_MODEL=gpt-4o-mini

# DB (defaults to local SQLite if omitted)
DB_URL=sqlite:///./data.db


Frontend (excel-mock-interviewer-advanced/frontend/.env.local)

# Point the UI to your backend
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

 Local Development
1) Backend
cd excel-mock-interviewer-advanced/backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux:       source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
# Health: http://127.0.0.1:8000/health  => {"ok":true,"version":"0.2.0"}
# Docs:   http://127.0.0.1:8000/docs

2) Frontend
cd excel-mock-interviewer-advanced/frontend
npm install
# set NEXT_PUBLIC_API_BASE in .env.local (see above)
npm run dev
# UI: http://localhost:3000

🔌 API Endpoints (Backend)

GET /health → simple health JSON

POST /start → { interview_id, question }

Body: { "candidate_email": "optional@user.com" }

POST /answer → evaluation + next question

Body:

Common: { "interview_id", "question_id" }

For hint: add "want_hint": true

For formula/value/text: add "answer_text": "..."

For table: add "answer_table": [ { ... }, ... ]

Response always includes: score, feedback, done, and either next_question or summary.

GET /report/{interview_id} → final summary (band, per-skill, strengths, gaps, drills)

GET /admin/metrics → admin stats (totals, averages, per-skill)

🧠 Scoring & Adaptivity

Type-Guard: if you submit a wrong type, you don’t advance and get a gentle reminder.

Hints: you can ask for a hint anytime; each hint costs −0.5 from that question’s final score.

Adaptive difficulty: recent scores steer the next question:

last two ≥ 4/5 → target Hard

last one ≤ 2/5 → target Easy

else → Medium

LLM grading (text): used only for short text questions. If OPENAI_API_KEY is absent, a rule-based fallback runs.

Quick Test (Curl)
# Start
curl -s -X POST http://127.0.0.1:8000/start -H "Content-Type: application/json" -d "{}"

# Example answer (formula)
curl -s -X POST http://127.0.0.1:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"interview_id":"<from start>","question_id":"<qid>","answer_text":"=SUMIFS(D:D,A:A,\"East\",C:C,\"Pencil\")"}'

🧑‍💻 Frontend UX Tips

Under each prompt you’ll see: Expected: (formula/value/table/text) and a Detected badge that updates as you type.

Submit is disabled until your input matches the expected format.

Placeholders show valid examples (e.g., a sample formula or table JSON).

 Deployment
Backend (Render)

Root directory: excel-mock-interviewer-advanced/backend

Build command: pip install -r requirements.txt

Start command:

uvicorn app.main:app --host 0.0.0.0 --port $PORT


Env Vars: set OPENAI_API_KEY, LLM_MODEL, and (optionally) DB_URL

Instance: Free is fine for PoC (will sleep on idle)

Frontend (Vercel/Netlify/Render Static Site)

Root directory: excel-mock-interviewer-advanced/frontend

Env: set NEXT_PUBLIC_API_BASE to your backend URL (e.g., https://your-backend.onrender.com)

Build: next build

Start (SSR) or static export (optional):

If you choose static export, set next.config.js accordingly and use next export.

For SSR on Render, create a Node Web Service and run next start -p $PORT.

Keep frontend & backend in separate services. It simplifies environment variables and scaling.

Security

Never commit secrets (.env, API keys).

GitHub may block pushes if it detects keys—rotate & remove from history if this happens.

Use Render/Vercel Environment Variables instead.

📈 Cold-Start → Improve Over Time

Start with a seed bank (this PoC).

Add parametric templates for new variants (change Reps/Items/Regions/Values).

Keep deterministic checks for formulas/tables; expand rubric prompts for text.

Add telemetry (e.g., hardest skills per cohort) to drive new drills.

Sample Transcript (excerpt)
Agent: Hi! 6 questions in ~12 mins.
Q1 (Aggregation): East + Pencil total — Expected: formula
You: =SUMIFS(D:D,A:A,"East",C:C,"Pencil")
Agent: Formula accepted. (Score: 5)

Q2 (Aggregation): Total orders — Expected: value
You: 56
Agent: Correct numeric result. (Score: 5)

...
Agent: Interview complete. Band: Intermediate.
Summary: Aggregation 80% | Lookups 100% | Efficiency 40%
Drills: Practice more on: Efficiency

❓Troubleshooting

Frontend says “Failed to fetch” → check backend URL in NEXT_PUBLIC_API_BASE, backend running/healthy, and CORS.

Git push blocked (large files) → don’t commit .next/, node_modules/, .venv/, data.db (use .gitignore).

Git push blocked (secrets) → remove keys from history, rotate key, push again.

Render start command wrong → use uvicorn app.main:app --host 0.0.0.0 --port $PORT.

License

MIT — use, modify, and build on it.
Please keep attribution if you publish derivatives or demos.

Happy hiring! If you’d like, I can also generate a concise Design Doc (2–3 pages) to attach alongside this repo.
