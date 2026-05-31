# Customer Feedback Sentiment Analyzer - Architecture

## 1. Overview
Full-stack web application that processes customer feedback PDFs and returns structured sentiment analysis, key themes, evidence, and recommended actions. Uses async job processing to handle large files without request timeouts.

**Live URLs**  
- Frontend: https://sentiment-ai-steel.vercel.app  
- Backend: https://sentiment-ai-7gso.onrender.com

## 2. System Architecture

```mermaid
graph TD
    User[User Browser] -->|HTTPS| Vercel[Vercel CDN]
    Vercel --> React[React SPA<br/>sentiment-ui]
    React -->|POST /jobs<br/>multipart/form-data| API[FastAPI<br/>Render Web Service]
    API -->|202 Accepted<br/>job_id| React
    API -->|Background Task| Worker[PDF Parser + LLM]
    Worker --> Store[(In-Memory<br/>Job Store)]
    React -->|Poll GET /jobs/{id}<br/>every 2s| API
    API -->|Read status| Store
    Store -->|status: completed| API
    React -->|GET /jobs/{id}/result| API
    API -->|JSON result| React
    User -->|View Results| React

    subgraph "Vercel"
        Vercel
        React
    end

    subgraph "Render"
        API
        Worker
        Store
    end

    style User fill:#e1f5ff
    style React fill:#61dafb
    style API fill:#009688
    style Worker fill:#ff9800

LayerTechnologyPlatformResponsibilityFrontendReact 18, CRA, AxiosVercelFile upload UI, job polling, results renderingBackend APIFastAPI, UvicornRender Web ServiceREST endpoints, CORS, job orchestrationProcessingPython, asyncioRender Web ServicePDF parsing, LLM calls, result generationStateIn-memory dictRender instanceJob status + results. Ephemeral2.1 Data Flow Steps
Upload: User selects PDF. React sends POST /jobs with FormData to RenderQueue: FastAPI validates file, creates job_id, starts background task, returns 202Poll: React polls GET /jobs/{id} every 2s. Statuses: queued -> processing -> completed|failedProcess: Worker extracts text, chunks if needed, calls LLM, builds result JSON, saves to memoryFetch: On completed, React calls GET /jobs/{id}/result and renders themes, sentiment, actionsError Path: If processing fails, status = failed with error string. React displays error3. Component Breakdown
3.1 Frontend: sentiment-ui/
Framework: Create React AppState: useState for file, jobId, status, result, errorAPI Client: Axios with base URL from process.env.REACT_APP_API_URLKey Components:File input: accepts .pdf onlyUpload button: disabled until file selectedStatus display: shows job_id and current statusResults panel: renders summary, overall_sentiment, themes[], recommended_actions[]Polling Logic: useEffect with setInterval cleared on unmount or status terminalEnv Var: REACT_APP_API_URL set in VercelBuild: npm run build. Root directory: sentiment-ui3.2 Backend API: sentiment-ai/
Framework: FastAPIEndpoints:POST /jobs: Accepts PDF via UploadFile. Max 50MB. Returns {job_id}, status 202GET /jobs/{id}: Returns {"status": "queued|processing|completed|failed", "error": str|null}GET /jobs/{id}/result: Returns analysis JSON if completed, 404 otherwiseMiddleware: CORSMiddleware with origins from CORS_ORIGINS env var split by commaAsync: BackgroundTasks for non-blocking PDF processingValidation: File extension + size check before queuingStart: uvicorn main:app --host 0.0.0.0 --port $PORT3.3 Processing Pipeline
Validate: Check .pdf extension, size < 50MB. Reject with 400 if invalidExtract: pypdf or pdfplumber -> raw text. Handle scanned PDFs as limitationChunk: Split if text > 12k tokens to fit LLM context windowAnalyze: LLM prompt enforces JSON output with required keysEvidence: Map theme claims to line numbers or quote snippets as evidence_idsStore: Save result in memory dict keyed by job_id. TTL not implementedResult Schemajson{
  "summary": "string",
  "overall_sentiment": "positive | neutral | negative | mixed",
  "themes": [
    {"name": "string", "evidence_ids": [1, 5, 12]}
  ],
  "recommended_actions": ["string"],
  "limitations": "string | null"
}4. DeploymentServicePlatformTriggerEnv VarsFrontendVercelPush to mainREACT_APP_API_URL=https://sentiment-ai-7gso.onrender.comBackendRenderPush to mainCORS_ORIGINS=https://sentiment-ai-steel.vercel.app, OPENAI_API_KEYBuild Settings  Vercel: Framework preset: Create React App, Root Directory: sentiment-ui, Install: npm install, Build: npm run buildRender: Environment: Python 3, Build: pip install -r requirements.txt, Start: uvicorn main:app --host 0.0.0.0 --port $PORTDomains: Vercel auto-provisions SSL. Render provides .onrender.com with SSL5. Local Development
Backendbashcd sentiment-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export CORS_ORIGINS=http://localhost:3000
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload --port 8000Frontendbashcd sentiment-ui
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
npm install
npm startAccess frontend at http://localhost:30006. Security + Ops
CORS: Strict allowlist via env var. Format: https://domain1.com,https://domain2.com. No wildcard in prodSecrets: API keys stored only in Render/Vercel environment variables. Never committedFile Upload: Server-side validation for type .pdf and size <= 50MB. Rejects earlyInput Sanitization: PDF text extracted, not executed. LLM output validated against JSON schemaRate Limiting: Not implemented. Recommended: Cloudflare rate limit rules for /jobs endpointLogging: Python logging to stdout. Captured by Render logs. No PII loggedError Handling: All endpoints return JSON errors with status codes. Frontend displays err.response.data.detail7. Limitations + Next StepsCurrent LimitationImpactProposed FixIn-memory job storeAll jobs lost on deploy/restartMigrate to Redis with TTL or PostgresNo authPublic endpoint, potential abuse/costAdd Clerk/Auth0 for users + API key auth for programmaticSingle worker∼5 concurrent PDFs before slowdownCelery + Redis queue + 2-3 worker dynosPDF onlyCan't process Word/Excel/textAdd python-docx, openpyxl, .txt parsersNo observabilityBlind to errors/latency in prodAdd Sentry for errors, Logtail/BetterStack for logsScanned PDFsOCR not supported, returns empty textAdd Tesseract OCR or AWS Textract fallbackLong feedback100 pages may timeout LLMMap-reduce: summarize chunks then summarize summaries8. Key Decisions + Tradeoffs
Async jobs vs sync requests: Chose async with polling to avoid 30s Vercel function timeout and 60s Render request timeout. Tradeoff: More complex frontend polling logicPolling vs WebSockets/SSE: Polling every 2s is simple and works on free tier. WebSockets need sticky sessions and add infra cost. SSE better for v2Vercel + Render split: Vercel excels at static React hosting + CI/CD. Render gives persistent Python workers without serverless cold starts. Tradeoff: Cross-origin CORS config neededCreate React App vs Next.js: CRA has zero-config for SPA. Next.js adds complexity with no SEO benefit for this app. Can migrate if SSR neededIn-memory vs DB: In-memory fastest for MVP. No external dependencies. Tradeoff: Not prod-safe. Redis is first upgrade pathBackgroundTasks vs Celery: FastAPI BackgroundTasks runs in same process. Simpler than Celery for MVP. Celery needed for true scale + retriesEvidence as line numbers: Simple to implement and verify. Tradeoff: Line numbers shift if PDF re-flowed. Quote snippets more robust for v2Last updated: 2026-05-31Maintainer: Naveenkumar T