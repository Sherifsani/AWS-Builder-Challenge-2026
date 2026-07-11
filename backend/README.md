# Resume/CV Tailor — Backend

Multi-user resume bullet matcher. FastAPI + Mangum on Lambda, DynamoDB, Amazon
Bedrock (Nova Lite). See `../spec.md` for the original brief.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/signup` | – | Create user, returns JWT |
| POST | `/auth/login` | – | Returns JWT |
| GET/PUT | `/me` | ✔ | Read/update profile |
| POST/GET | `/bullets` | ✔ | Add / list bullets |
| PUT/DELETE | `/bullets/{id}` | ✔ | Update / delete a bullet |
| POST | `/resume/import` | ✔ | Base64 PDF/DOCX → structured bullets |
| POST | `/match` | ✔ | Rank bullets vs. a job description |
| POST | `/generate-cv` | ✔ | Tailored one-page CV as LaTeX (`.tex`) source |
| GET | `/health` | – | Health check |

Auth is a Bearer JWT (`Authorization: Bearer <token>`), scoped so each user only
ever sees their own bullets (`user_id` partition key).

## Local development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                 # dev secret + local DynamoDB endpoint

# DynamoDB Local
docker run -d --name ddb-local -p 8000:8000 amazon/dynamodb-local
python -m scripts.create_tables

uvicorn app.main:app --reload --port 8080
```

Verify without AWS creds (Bedrock mocked):

```bash
python -m pytest scripts/verify_bedrock_paths.py -q -s
```

`/match` and `/resume/import` make live Bedrock calls — those need AWS credentials
and a region where Nova Lite is available (e.g. `us-east-1`).

## Deploy (AWS SAM)

Prereqs: SAM CLI, AWS credentials, a region with Nova Lite (e.g. `us-east-1`).

1. Create the JWT signing secret in SSM (CloudFormation can't create SecureString):

   ```bash
   aws ssm put-parameter --name /resume-tailor/jwt-secret \
     --type SecureString --value "$(openssl rand -hex 32)" --region us-east-1
   ```

2. Enable Bedrock model access for **Amazon Nova Lite** in the target region
   (Bedrock console → Model access).

3. Build & deploy:

   ```bash
   sam build
   sam deploy --guided --region us-east-1
   ```

   `sam build` packages `requirements.txt` (prod deps only — `uvicorn`/`pytest`
   live in `requirements-dev.txt`). Keep `.venv/` out of the build (it's
   `.gitignore`d); if present it only bloats the artifact.

4. Note the `ApiBaseUrl` output — that's the frontend's `VITE_API_BASE_URL`.

### Template parameters
- `BedrockModelId` (default `amazon.nova-lite-v1:0`)
- `JwtSecretParam` (default `/resume-tailor/jwt-secret`)
- `JwtExpireMinutes` (default `1440`)

### IAM (least privilege)
The function role grants only:
- DynamoDB `GetItem/PutItem/UpdateItem/DeleteItem/Query/BatchWriteItem` on the two
  table ARNs
- `bedrock:InvokeModel` on the Nova model (+ inference-profile ARNs)
- `ssm:GetParameter` on the one JWT-secret parameter
