# Resume/Application Tracker — Build Spec

**Project:** AI-powered resume bullet matcher for job applications
**Context:** Built for the AWS Builder Center "Weekend Productivity Challenge" (July 10–13, 2026)
**Owner:** Sherif — CS student, University of Lagos, AWS Certified Solutions Architect – Associate

## 1. Problem Statement

I maintain a bank of resume bullets across multiple past projects (ScholarArk, Skurel, AI Fitness Microservice, trackR, TrustLayer, course marketplace, etc.) and I'm actively tailoring resumes for different roles (Amazon SWE intern, Mono backend intern, Digicore Java backend, 8Peaks Cloud intern, Bank of America Global Technology). Right now, tailoring each resume to a job description is manual and slow. This tool takes a job description, matches it against my bullet bank using an LLM, and returns a ranked, tailored suggestion — plus a gap analysis of keywords I'm missing.

## 2. High-Level Architecture

```
┌─────────────┐      ┌───────────────┐      ┌───────────────────┐
│   Frontend   │ ───▶ │  API Gateway   │ ───▶ │  Lambda (FastAPI   │
│ (Vite React  │      │  (REST API)    │      │  via Mangum)       │
│  app on S3)  │ ◀─── │                │ ◀─── │                    │
└─────────────┘      └───────────────┘      └─────────┬──────────┘
                                                          │
                                        ┌─────────────────┼─────────────────┐
                                        ▼                                   ▼
                                ┌───────────────┐                ┌────────────────────┐
                                │   DynamoDB     │                │   Amazon Bedrock    │
                                │ ResumeBullets  │                │   (Nova Lite/Micro)  │
                                │  table         │                │                     │
                                └───────────────┘                └────────────────────┘
```

## 3. Components

### 3.1 Frontend
- Vite + React app, single page, no auth: a textarea to paste a job description, a "Match my resume" button, and a results panel.
- Keep it to one or two components (e.g. `JobDescriptionForm` and `MatchResults`) — no router needed for a single-page tool.
- Plain `fetch` (or `axios`) call to `POST /match` on submit; render the JSON response as a ranked bullet list, a missing-keywords callout, and the suggested order.
- Local state via `useState` is enough — no need for a state management library at this scale.
- `npm run build` produces a static `dist/` folder — deploy that to an S3 bucket configured for static website hosting (same deployment target as the plain-HTML option, just with a build step first).
- Set `VITE_API_BASE_URL` as an env var pointing at the API Gateway invoke URL so the endpoint isn't hardcoded.

### 3.2 API Gateway
REST API with two routes:
- `POST /bullets` — add/update an entry in the bullet bank
- `POST /match` — takes a job description string, returns ranked bullets + gap analysis

Optional: API Gateway built-in API key (`x-api-key` header) for basic access control. Not required for a single-user weekend build, but easy to add and worth mentioning in the writeup.

### 3.3 Lambda (FastAPI + Mangum)
One Lambda function wrapping a FastAPI app via Mangum.

**Endpoints:**
- `add_bullet(bullet, project, skills, category, impact_metric)` → writes to DynamoDB
- `match(job_description)` → reads all bullets from DynamoDB, builds a prompt, calls Bedrock, parses and returns JSON

**Bedrock call:** use `boto3.client("bedrock-runtime").invoke_model(...)` with a Nova model ID (Nova Lite recommended — cheap and sufficient for this task).

**Prompt requirement:** instruct the model to return strict JSON only (no preamble, no markdown fences) so the Lambda can parse it directly without regex cleanup.

**Expected Bedrock response shape:**
```json
{
  "ranked_bullets": [
    {"bullet_id": "b004", "reason": "Directly matches JD's emphasis on distributed systems"},
    {"bullet_id": "b011", "reason": "Matches required CI/CD experience"}
  ],
  "missing_keywords": ["observability", "SLA", "incident response"],
  "suggested_order": ["b004", "b011", "b002"]
}
```

### 3.4 DynamoDB

**Table name:** `ResumeBullets`
**Billing mode:** On-demand (no capacity planning needed, free-tier friendly)

**Schema:**
| Field | Type | Notes |
|---|---|---|
| `bullet_id` | String (PK) | e.g. "b001" |
| `bullet` | String | the actual resume line |
| `project` | String | e.g. "ScholarArk", "TrustLayer", "AI Fitness Microservice" |
| `skills` | List\<String\> | e.g. ["FastAPI", "Redis", "RabbitMQ"] |
| `category` | String | "backend" / "cloud" / "AI" / "frontend" |
| `impact_metric` | String (optional) | e.g. "reduced latency by 30%" |

Seed this table with 15–20 real bullets pulled from existing resumes (Amazon SWE, Mono, Digicore, 8Peaks, Bank of America versions) before building the match logic.

### 3.5 Amazon Bedrock
- Model: Nova Lite (fast, cheap, sufficient for text matching/ranking tasks)
- One prompt per `/match` call combining the JD text and the full bullet list
- Ask for JSON-only output to avoid parsing issues

## 4. Data Flow (single `/match` request)

1. Frontend sends JD text to `POST /match`.
2. Lambda scans DynamoDB for all bullets (table is small, so a full scan is fine — no GSIs needed at this scale).
3. Lambda constructs a prompt: JD + bullet list + instructions to return strict JSON.
4. Lambda calls Bedrock via `invoke_model`.
5. Lambda parses the JSON response and returns it to the frontend.
6. Frontend renders: ranked bullet list, missing keywords, suggested ordering.

## 5. IAM / Permissions

Lambda execution role should be scoped to exactly:
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Scan` on the `ResumeBullets` table ARN
- `bedrock:InvokeModel` on the Nova model ARN

No other permissions needed. Worth calling out least-privilege scoping in the article writeup.

## 6. Suggested Build Order / Timeline

| Step | Task | Est. time |
|---|---|---|
| 1 | Create DynamoDB table, seed 15–20 bullets from real resumes | 30 min |
| 2 | Write FastAPI app locally (`/bullets`, `/match`), test Bedrock calls locally | 2 hrs |
| 3 | Wrap with Mangum, deploy to Lambda, wire up API Gateway | 1.5 hrs |
| 4 | Scaffold Vite React app, build form + results UI, `npm run build` and host `dist/` on S3 | 1–1.5 hrs |
| 5 | End-to-end test, capture screenshots/GIF for article | 30 min |
| 6 | Write 500+ word AWS Builder Center article with architecture diagram | 1.5 hrs |

Total: roughly one solid day, leaving buffer before the Monday July 13, 1:00 PM PT deadline.

## 7. Notes for Claude Code

- Reuse the FastAPI + Mangum pattern already familiar from other projects (Skurel, TrustLayer) — no new framework to learn.
- Skip auth/Keycloak entirely; this is single-user.
- Keep the Bedrock prompt strict about JSON-only output to avoid brittle string parsing.
- Local dev: test the FastAPI app and Bedrock calls locally with `uvicorn` before wrapping in Mangum and deploying.
- Deployment: SAM CLI or plain `aws lambda` CLI both work; pick whichever is fastest to iterate with given the tight weekend timeline.
- Keep scope tight — this is a pass/fail weekend challenge on completeness + functionality + AWS usage, not a polish contest.
- Frontend: scaffold with `npm create vite@latest -- --template react` (or `react-ts` if typed). Two components max, no router, no state library — `useState` and a single `fetch` call are enough.

## 8. AWS Builder Center Article Requirements (for reference)

- Title must include: "Weekend Productivity Challenge: [Name of Your App]"
- Tag: `#productivity`
- Minimum 500 words
- Must cover: Vision & What the App Does / How You Built It / AWS Services Used & Architecture Overview / What You Learned / Link to App or Repo
- Deadline: July 13, 2026, 1:00 PM PT
