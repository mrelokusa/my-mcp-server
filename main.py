# main.py
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="MCP Summarizer")

# Gemini API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCgzU8GQUgi8Crs2qG8EKNEE_tZr_-F4xE")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-pro")  # change if needed

class SummarizeRequest(BaseModel):
    text: str
    max_sentences: Optional[int] = 3
    source: Optional[str] = None  # optional metadata (source URL or name)

class SummarizeResponse(BaseModel):
    summary: str
    source: Optional[str] = None

def extractive_short(text: str, max_sentences: int = 3) -> str:
    """Fallback simple summarizer"""
    import re
    sentences = re.split(r'(?<=[\.\!\?])\s+', text.strip())
    sents = [s for s in sentences if s]
    return " ".join(sents[:max_sentences]) if sents else text[:200] + ("..." if len(text) > 200 else "")

@app.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must be provided in the request body")

    if GEMINI_API_KEY:
        # Gemini API call
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"Summarize the following text into {req.max_sentences} sentences (concise, actionable):\n{text}"}
                    ]
                }
            ]
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            # Gemini returns nested structure; extract first text part
            content = data.get("candidates", [{}])[0].get("content", "").strip()
            if not content:
                # fallback if Gemini returns nothing
                content = extractive_short(text, req.max_sentences)
            return SummarizeResponse(summary=content, source=req.source)
        except Exception:
            # fallback if API fails
            fallback = extractive_short(text, req.max_sentences)
            return SummarizeResponse(summary=fallback, source=req.source)
    else:
        # No API key: fallback
        fallback = extractive_short(text, req.max_sentences)
        return SummarizeResponse(summary=fallback, source=req.source)

@app.get("/")
def root():
    return {"message": "MCP Summarizer alive"}
