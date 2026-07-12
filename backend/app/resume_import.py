"""/resume/import — parse an uploaded resume into structured bullets.

Flow: base64 file -> extract raw text (pypdf / python-docx) -> Bedrock structures
the text into bullets -> store under the caller's user_id.
"""
import base64
import io

from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from .bedrock import invoke_json
from .bullets import store_bullets
from .db import users_table
from .models import BulletInput, ResumeImportRequest, ResumeImportResponse

router = APIRouter()

_SYSTEM = (
    "You parse raw resume text into structured JSON. Extract THREE things:\n"
    "1. bullets: every distinct accomplishment/experience bullet. For each, infer "
    "the project/company, skills/technologies used, a category (one of: backend, "
    "frontend, cloud, AI, other), and any quantified impact metric.\n"
    "2. education: every school/degree entry (institution, credential, date, location).\n"
    "3. sections: any OTHER resume section that is not work experience or education — "
    "e.g. Volunteering, Certifications, Awards, Leadership, Publications. Each has a "
    "title and a list of verbatim item strings. Do NOT put work experience here.\n"
    "Copy education and section text faithfully — do not summarise or invent. "
    "Respond with STRICT JSON only — no preamble, no markdown fences. "
    'Schema: {"bullets":[{"bullet":str,"project":str|null,"skills":[str],'
    '"category":str,"impact_metric":str|null}],'
    '"education":[{"institution":str,"credential":str,"date":str|null,"location":str|null}],'
    '"sections":[{"title":str,"items":[str]}]}'
)


def _clean_education(raw) -> list:
    out = []
    for e in raw or []:
        if not isinstance(e, dict):
            continue
        if e.get("institution") or e.get("credential"):
            out.append(
                {
                    "institution": e.get("institution"),
                    "credential": e.get("credential"),
                    "date": e.get("date"),
                    "location": e.get("location"),
                }
            )
    return out


def _clean_sections(raw) -> list:
    out = []
    for s in raw or []:
        if not isinstance(s, dict):
            continue
        items = [i for i in (s.get("items") or []) if i]
        if s.get("title") and items:
            out.append({"title": s["title"], "items": items})
    return out


def _extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        import docx

        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs)
    raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported")


@router.post("/resume/import", response_model=ResumeImportResponse)
def import_resume(req: ResumeImportRequest, user: dict = Depends(get_current_user)):
    try:
        data = base64.b64decode(req.content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="content_base64 is not valid base64")

    text = _extract_text(req.filename, data).strip()
    if not text:
        raise HTTPException(
            status_code=422, detail="Could not extract any text from the file"
        )

    result = invoke_json(_SYSTEM, f"RESUME TEXT:\n{text}", max_tokens=4000)
    raw_bullets = result.get("bullets", [])
    if not raw_bullets:
        raise HTTPException(status_code=422, detail="No bullets found in the resume")

    inputs = [
        BulletInput(
            bullet=b["bullet"],
            project=b.get("project"),
            skills=b.get("skills", []) or [],
            category=b.get("category"),
            impact_metric=b.get("impact_metric"),
        )
        for b in raw_bullets
        if b.get("bullet")
    ]
    created = store_bullets(user["user_id"], inputs, source="import")

    # Persist education + extra sections on the user record so the CV generator can
    # emit them verbatim (they must never be dropped or rephrased by the LLM).
    education = _clean_education(result.get("education"))
    sections = _clean_sections(result.get("sections"))
    if education or sections:
        users_table().update_item(
            Key={"email": user["email"]},
            UpdateExpression="SET education = :e, sections = :s",
            ExpressionAttributeValues={":e": education, ":s": sections},
        )

    return ResumeImportResponse(imported=len(created), bullets=created)
