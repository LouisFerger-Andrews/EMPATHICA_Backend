# src/api.py
from fastapi import FastAPI
from pydantic import BaseModel

from src.core.rag_controller import rag_inference  # <-- adjust import to your tree

app = FastAPI(title="EMPATHICA Backend")

class Question(BaseModel):
    prompt: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(q: Question):
    """Run your existing pipeline on a user prompt."""
    answer = rag_inference(q.prompt)
    return {"answer": answer}
