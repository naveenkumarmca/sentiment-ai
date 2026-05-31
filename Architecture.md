# Customer Feedback Sentiment Analyzer - Architecture

## 1. Overview
Full-stack web application that processes customer feedback PDFs and returns structured sentiment analysis, key themes, evidence, and recommended actions. Uses async job processing to handle large files without request timeouts.

**Live URLs**  
- Frontend: https://sentiment-ai-steel.vercel.app  
- Backend: https://sentiment-ai-7gso.onrender.com

## 2. System Architecture

| Layer | Technology | Platform | Responsibility |
| --- | --- | --- | --- |
| **Frontend** | React 18, CRA, Axios | Vercel | File upload UI, job polling, results rendering |
| **Backend API** | FastAPI, Uvicorn | Render Web Service | REST endpoints, CORS, job orchestration |
| **Processing** | Python, asyncio | Render Web Service | PDF parsing, LLM calls, result generation |
| **State** | In-memory dict | Render instance | Job status + results. Ephemeral |

### 2.1 Data Flow Steps
1. **Upload**: User selects PDF. React sends `POST /jobs` with `FormData` to Render
2. **Queue**: FastAPI validates file, creates `job_id`, starts background task, returns 202
3. **Poll**: React polls `GET /jobs/{id}` every 2s. Statuses: `queued` -> `processing` -> `completed` or `failed`
4. **Process**: Worker extracts text, chunks if needed, calls LLM, builds result JSON, saves to memory
5. **Fetch**: On `completed`, React calls `GET /jobs/{id}/result` and renders themes, sentiment, actions
6. **Error Path**: If processing fails, status = `failed` with `error` string. React displays error

## 3. Component Breakdown

### 3.1 Frontend: `sentiment-ui/`
- **Framework**: Create React App
- **State**: `useState` for file, jobId, status, result, error
- **API Client**: Axios with base URL from `process.env.REACT_APP_API_URL`
- **Key Components**:
    - File input: accepts `.pdf` only
    - Upload button: disabled until file selected
    - Status display: shows job_id and current status
    - Results panel: renders summary, overall_sentiment, themes, recommended_actions
- **Polling Logic**: `useEffect` with `setInterval` cleared on unmount or status terminal
- **Env Var**: `REACT_APP_API_URL` set in Vercel
- **Build**: `npm run build`. Root directory: `sentiment-ui`

### 3.2 Backend API: `sentiment-ai/`
- **Framework**: FastAPI
- **Endpoints**:
    - `POST /jobs`: Accepts PDF via `UploadFile`. Max 50MB. Returns `{job_id}`, status 202
    - `GET /jobs/{id}`: Returns `{"status": "queued|processing|completed|failed", "error": str|null}`
    - `GET /jobs/{id}/result`: Returns analysis JSON if completed, 404 otherwise
- **Middleware**: `CORSMiddleware` with origins from `CORS_ORIGINS` env var split by comma
- **Async**: `BackgroundTasks` for non-blocking PDF processing
- **Validation**: File extension + size check before queuing
- **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3.3 Processing Pipeline
1. **Validate**: Check `.pdf` extension, size < 50MB. Reject with 400 if invalid
2. **Extract**: `pypdf` or `pdfplumber` -> raw text. Handle scanned PDFs as limitation
3. **Chunk**: Split if text > 12k tokens to fit LLM context window
4. **Analyze**: LLM prompt enforces JSON output with required keys
5. **Evidence**: Map theme claims to line numbers or quote snippets as `evidence_ids`
6. **Store**: Save result in memory dict keyed by `job_id`. TTL not implemented

**Result Schema**
```json
{
  "summary": "string",
  "overall_sentiment": "positive | neutral | negative | mixed",
  "themes": [
    {"name": "string", "evidence_ids": [1, 5, 12]}
  ],
  "recommended_actions": ["string"],
  "limitations": "string | null"
}
```

## 4. Deployment

| Service | Platform | Trigger | Env Vars |
| --- | --- | --- | --- |
| **Frontend** | Vercel | Push to `main` | `REACT_APP_API_URL=https://sentiment-ai-7gso.onrender.com` |
| **Backend** | Render | Push to `main` | `CORS_ORIGINS=https://sentiment-ai-steel.vercel.app`, `OPENAI_API_KEY` |

**Build Settings**  
- **Vercel**: Framework preset: Create React App, Root Directory: `sentiment-ui`, Install: `npm install`, Build: `npm run build`
- **Render**: Environment: Python 3, Build: `pip install -r requirements.txt`, Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Domains**: Vercel auto-provisions SSL. Render provides `.onrender.com` with SSL

## 5. Local Development

**Backend**
```bash
cd sentiment-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export CORS_ORIGINS=http://localhost:3000
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd sentiment-ui
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
npm install
npm start
```

Access frontend at http://localhost:3000

## 6. Security + Ops

- **CORS**: Strict allowlist via env var. Format: https://domain1.com,https://domain2.com. No wildcard in prod
- **Secrets**: API keys stored only in Render/Vercel environment variables. Never committed
- **File Upload**: Server-side validation for type .pdf and size <= 50MB. Rejects early
- **Input Sanitization**: PDF text extracted, not executed. LLM output validated against JSON schema
- **Rate Limiting**: Not implemented. Recommended: Cloudflare rate limit rules for /jobs endpoint
- **Logging**: Python logging to stdout. Captured by Render logs. No PII logged
- **Error Handling**: All endpoints return JSON errors with status codes. Frontend displays err.response.data.detail

## 7. Limitations + Next Steps

| Current Limitation | Impact | Proposed Fix |
| --- | --- | --- |
| In-memory job store | All jobs lost on deploy/restart | Migrate to Redis with TTL or Postgres |
| No auth | Public endpoint, potential abuse/cost | Add Clerk/Auth0 for users + API key auth for programmatic |
| Single worker | ~5 concurrent PDFs before slowdown | Celery + Redis queue + 2-3 worker dynos |
| PDF only | Can't process Word/Excel/text | Add python-docx, openpyxl, .txt parsers |
| No observability | Blind to errors/latency in prod | Add Sentry for errors, Logtail/BetterStack for logs |
| Scanned PDFs | OCR not supported, returns empty text | Add Tesseract OCR or AWS Textract fallback |
| Long feedback | 100 pages may timeout LLM | Map-reduce: summarize chunks then summarize summaries | 

## 8. Key Decisions + Tradeoffs

- **Async jobs vs sync requests**: Chose async with polling to avoid 30s Vercel function timeout and 60s Render request timeout. Tradeoff: More complex frontend polling logic
- **Polling vs WebSockets/SSE**: Polling every 2s is simple and works on free tier. WebSockets need sticky sessions and add infra cost. SSE better for v2
- **Vercel + Render split**: Vercel excels at static React hosting + CI/CD. Render gives persistent Python workers without serverless cold starts. Tradeoff: Cross-origin CORS config needed
- **Create React App vs Next.js**: CRA has zero-config for SPA. Next.js adds complexity with no SEO benefit for this app. Can migrate if SSR needed
- **In-memory vs DB**: In-memory fastest for MVP. No external dependencies. Tradeoff: Not prod-safe. Redis is first upgrade path
- **BackgroundTasks vs Celery**: FastAPI BackgroundTasks runs in same process. Simpler than Celery for MVP. Celery needed for true scale + retries
- **Evidence as line numbers**: Simple to implement and verify. Tradeoff: Line numbers shift if PDF re-flowed. Quote snippets more robust for v2