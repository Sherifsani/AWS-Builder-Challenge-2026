# Weekend Productivity Challenge: Résumé Bench

**Tag:** `#productivity`

**Live app:** http://resume-tailor-887862869466.s3-website-us-east-1.amazonaws.com

---

## Vision & what the app does

I'm a CS student at the University of Lagos, and every job season I hit the same wall: I keep one growing bank of resume bullets across a dozen projects, and tailoring that bank to each role — an Amazon SWE internship, a backend role, a cloud internship — is slow, manual, and easy to get wrong. You paste your bullets, guess which ones matter for this job, and hope you didn't miss the keywords their ATS is scanning for.

**Résumé Bench** turns that guesswork into a workflow. You keep one bank of bullets. You paste a job description. It ranks your bullets by relevance to that job, shows you exactly which keywords from the description are *missing* from your resume, and generates a tailored, one-page CV you can preview and download as a PDF — or export as LaTeX to compile in Overleaf. The whole loop takes seconds instead of an evening.

The core idea I kept coming back to: **tailoring a resume is a diff** between what you've done and what the job asks for. So the app's signature feature is a keyword-gap readout rendered like a code diff — `- observability`, `- incident response`, `- SLA` — the terms you need to add before you hit submit.

![The Résumé Bench dashboard: profile and live stats on the left, your bullet bank on the right.](docs/screenshots/01-dashboard.png)

## How I built it

The app is single-user-friendly but multi-user by design, with JWT auth so each account only ever sees its own bullets. There are three stages in the UI, and they map directly to how I actually work:

1. **Your material** — add bullets by hand, or upload an existing resume (PDF or DOCX). On upload, the app extracts your bullets *and* your education, volunteering, and certifications, so nothing gets dropped.
2. **Tailor to a job** — paste a job description, get a ranked list of your most relevant bullets plus the keyword gap.
3. **Generate CV** — produce a tailored one-page CV, preview the PDF in-browser, and download it or grab the LaTeX source.

![Match results: your bullets ranked against a real job description, each with a reason.](docs/screenshots/02-match-ranked.png)

![The signature feature — the keyword gap rendered as a diff of terms missing from your bullets.](docs/screenshots/03-keyword-gap.png)

![The tailored CV rendered as a real PDF in the browser — no LaTeX toolchain required.](docs/screenshots/04-cv-preview.png)

One decision I'm happy with: **LaTeX never comes from the language model.** The model only ever returns structured content (plain strings); a single module turns that content into a compile-safe `.tex` document, escaping every user string so a stray `&` or `%` can't break the compile. And factual sections — education, certifications, volunteering — are injected **verbatim** from storage, never rephrased or summarized by the model, so they can't silently disappear from your CV. For people who don't want to touch LaTeX at all, the app also renders a real vector PDF directly in the browser.

## AWS services used & architecture overview

```
React (S3 static site) → API Gateway → Lambda (FastAPI via Mangum)
                                               │
                                   ┌───────────┴───────────┐
                                   ▼                       ▼
                             DynamoDB                Amazon Bedrock
                        (Users + ResumeBullets)      (Nova Lite)
```

- **Amazon S3** — hosts the built React app as a static website.
- **Amazon API Gateway** — the REST front door for the API.
- **AWS Lambda** — a single FastAPI app wrapped with Mangum. One function serves auth, bullets, resume import, matching, and CV generation.
- **Amazon DynamoDB** — two on-demand tables: `Users` and `ResumeBullets` (partitioned by `user_id` so a user's data is naturally isolated).
- **Amazon Bedrock (Nova Lite)** — powers resume parsing, bullet-to-JD matching, and CV content generation. Nova Lite is fast, cheap, and more than capable for structured text tasks.
- **AWS SAM + CloudFormation** — the whole stack is one template, deployed with a single script. The Lambda's IAM role is scoped to exactly what it needs: specific DynamoDB actions on the two table ARNs, `bedrock:InvokeModel` on the Nova model, and read access to one SSM SecureString (the JWT signing secret) — nothing more.

The entire architecture is serverless and pay-per-use, so it costs effectively nothing when idle, and a full weekend of testing came to a few cents — dominated by Bedrock calls at roughly a tenth of a cent each.

## What I learned

- **Prompt for structure, render deterministically.** Asking the model for strict JSON — and keeping all the formatting (LaTeX, PDF) in code — made the output far more reliable than letting the model emit documents directly.
- **Least privilege is easier when you start with it.** Writing the IAM policy as I added each capability kept the role tight instead of a wildcard I'd have to walk back later.
- **Serverless removes a whole class of worry.** No servers to keep warm, no idle bill, no scaling config — I could focus on the product and let SAM handle the infrastructure.
- **Model access is a toggle, not a cost.** My first Bedrock call failed until I enabled Nova Lite in the console — a good reminder that "it's deployed" and "it's authorized" are different things.

Building Résumé Bench in a weekend turned a chore I dreaded into something I'll actually keep using — and it gave me a genuinely fun excuse to wire FastAPI, DynamoDB, and Bedrock together behind a clean serverless front door.
