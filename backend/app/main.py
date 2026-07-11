"""FastAPI app entrypoint + Lambda handler.

Locally: `uvicorn app.main:app --reload`.
In Lambda: the `handler` (Mangum) is the configured entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI(title="Resume/CV Tailor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


handler = Mangum(app)
