# main.py
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="MCP Summarizer")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # change as needed

class SummarizeRequest(BaseModel):
    text: str
    max_sentences: Optional[int] = 3
    source: Optional[str] = None  # optional metadata (source URL or name)

class SummarizeResponse(BaseModel):
    summary: str
    source: Optional[str] = None

def extractive_short(text: str, max_sentences: int = 3) -> str:
    # simple fallback: split on sentences and return first N non-empty sentences
    import re
    sentences = re.split(r'(?<=[\.\!\?])\s+', text.strip())
    sents = [s for s in sentences if s]
    return " ".join(sents[:max_sentences]) if sents else text[:200] + ("..." if len(text) > 200 else "")

@app.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must be provided in the request body")

    # Prefer OpenAI if API key present, otherwise fallback to simple extractor
    if OPENAI_API_KEY:
        # Using OpenAI HTTP API call (keeps dependency surface minimal)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        system = "You are a concise summarization assistant. Summarize the user's text into a short readable paragraph."
        user_prompt = (
            f"Summarize the following text into {req.max_sentences} sentences (concise, actionable):\n\n"
            f"{text}\n\nProvide only the summary text."
        )
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 400,
            "temperature": 0.2,
            "top_p": 1.0,
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            # extract text – handle typical shape
            content = data["choices"][0]["message"]["content"].strip()
            return SummarizeResponse(summary=content, source=req.source)
        except Exception as e:
            # fallback to extractive approach on failure
            fallback = extractive_short(text, req.max_sentences)
            return SummarizeResponse(summary=fallback, source=req.source)
    else:
        # No API key: simple extractive fallback
        fallback = extractive_short(text, req.max_sentences)
        return SummarizeResponse(summary=fallback, source=req.source)

@app.get("/")
def root():
    return {"message": "MCP Summarizer alive"}
