"""Exercise /match and /resume/import code paths with Bedrock mocked out.

Runs in-process against the same DynamoDB Local, so no AWS creds are needed. This
verifies request parsing, DynamoDB reads/writes, and response shaping — everything
except the live model call, which is stubbed to return the strict-JSON we expect.
"""
import base64
import io
import uuid

from fastapi.testclient import TestClient

import app.bedrock as bedrock
import app.cv as cv_mod
import app.match as match_mod
import app.resume_import as resume_mod
from app.latex_template import render_cv, tex_escape
from app.main import app

client = TestClient(app)


def _signup(label):
    email = f"{label}-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/auth/signup", json={"email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _make_docx_bytes(text):
    import docx

    d = docx.Document()
    for line in text.splitlines():
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_resume_import(monkeypatch):
    hdr = _signup("import-user")

    def fake_invoke(system, user, max_tokens=2000):
        assert "RESUME TEXT" in user
        return {
            "bullets": [
                {
                    "bullet": "Built a RabbitMQ pipeline",
                    "project": "AI Fitness Microservice",
                    "skills": ["RabbitMQ", "Python"],
                    "category": "backend",
                    "impact_metric": "cut latency 30%",
                },
                {
                    "bullet": "Set up CI/CD on AWS",
                    "project": "TrustLayer",
                    "skills": ["AWS", "GitHub Actions"],
                    "category": "cloud",
                    "impact_metric": None,
                },
            ]
        }

    monkeypatch.setattr(resume_mod, "invoke_json", fake_invoke)

    docx_bytes = _make_docx_bytes("Built a RabbitMQ pipeline\nSet up CI/CD on AWS")
    r = client.post(
        "/resume/import",
        headers=hdr,
        json={
            "filename": "resume.docx",
            "content_base64": base64.b64encode(docx_bytes).decode(),
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["imported"] == 2, body
    assert all(b["source"] == "import" for b in body["bullets"])
    print("resume_import OK:", body["imported"], "bullets stored")

    # bullets are now queryable for this user
    lst = client.get("/bullets", headers=hdr)
    assert len(lst.json()) == 2
    print("bullets list after import OK")


def test_match(monkeypatch):
    hdr = _signup("match-user")
    # add a bullet so match has data
    client.post(
        "/bullets",
        headers=hdr,
        json={"bullet": "Built distributed systems", "skills": ["Go"], "category": "backend"},
    )

    def fake_invoke(system, user, max_tokens=2000):
        assert "JOB DESCRIPTION" in user and "BULLET BANK" in user
        return {
            "ranked_bullets": [{"bullet_id": "b1", "reason": "matches distributed systems"}],
            "missing_keywords": ["observability", "SLA"],
            "suggested_order": ["b1"],
        }

    monkeypatch.setattr(match_mod, "invoke_json", fake_invoke)

    r = client.post("/match", headers=hdr, json={"job_description": "We need distributed systems + SLA"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["missing_keywords"] == ["observability", "SLA"]
    print("match OK:", body)


def test_match_no_bullets():
    hdr = _signup("empty-user")
    r = client.post("/match", headers=hdr, json={"job_description": "anything"})
    assert r.status_code == 400, r.text
    print("match-no-bullets returns 400 as expected")


def test_latex_escape():
    # Every LaTeX special must be neutralised; backslash handled first.
    out = tex_escape("C++ & 50% off #1 a_b {x} $y ~ ^ \\cmd")
    for danger in ["& ", "50%", "#1", "a_b", "{x}", "$y"]:
        assert danger not in out or "\\" in out
    assert r"\&" in out and r"\%" in out and r"\_" in out and r"\{" in out
    assert r"\textbackslash{}" in out
    print("latex escape OK")


def test_render_cv_structure():
    tex = render_cv(
        {
            "name": "Ada & Co",
            "headline": "Backend Eng",
            "contact": "ada@x.com",
            "summary": "Ships reliable services.",
            "experience": [
                {"project": "Skurel", "bullets": ["Cut latency 30%", "Scaled to 1k rps"]}
            ],
            "skills": ["FastAPI", "AWS"],
        }
    )
    assert tex.startswith("\\documentclass")
    assert "\\begin{document}" in tex and "\\end{document}" in tex
    assert "Ada \\& Co" in tex  # escaped in header
    assert "Cut latency 30\\%" in tex  # escaped in a bullet
    assert "\\section{Experience}" in tex and "\\section{Skills}" in tex
    print("render_cv structure OK")


def test_generate_cv_route(monkeypatch):
    hdr = _signup("cv-user")
    client.post(
        "/bullets",
        headers=hdr,
        json={"bullet": "Built RabbitMQ pipeline", "project": "Fitness", "skills": ["Python"], "category": "backend"},
    )

    def fake_invoke(system, user, max_tokens=2000):
        assert "JOB DESCRIPTION" in user and "BULLET BANK" in user
        return {
            "name": "Test User",
            "headline": "Backend",
            "contact": "t@x.com",
            "summary": "Backend engineer.",
            "experience": [{"project": "Fitness", "bullets": ["Built RabbitMQ pipeline"]}],
            "skills": ["Python", "RabbitMQ"],
        }

    monkeypatch.setattr(cv_mod, "invoke_json", fake_invoke)

    r = client.post("/generate-cv", headers=hdr, json={"job_description": "Need a Python backend eng"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["filename"] == "tailored-cv.tex"
    assert body["tex"].startswith("\\documentclass")
    assert "Built RabbitMQ pipeline" in body["tex"]
    print("generate-cv route OK; tex length:", len(body["tex"]))


def test_generate_cv_no_bullets():
    hdr = _signup("cv-empty")
    r = client.post("/generate-cv", headers=hdr, json={"job_description": "anything"})
    assert r.status_code == 400, r.text
    print("generate-cv no-bullets returns 400 as expected")
