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
from .models import BulletInput, ResumeImportRequest, ResumeImportResponse

router = APIRouter()

_SYSTEM = (
    "You extract resume bullet points from raw resume text. Return every distinct "
    "accomplishment/experience bullet you find. For each, infer the project/company, "
    "the skills/technologies used, a category (one of: backend, frontend, cloud, AI, "
    "other), and any quantified impact metric. "
    "Respond with STRICT JSON only — no preamble, no markdown fences. "
    'Schema: {"bullets":[{"bullet":str,"project":str|null,"skills":[str],'
    '"category":str,"impact_metric":str|null}]}'
)


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
    return ResumeImportResponse(imported=len(created), bullets=created)
