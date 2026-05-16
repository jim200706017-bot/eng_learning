"""English Secretary Web App — FastAPI backend with LLM + voice support."""

import json
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
VOCAB_DIR = ROOT / "vocabulary"
BRIEFINGS_DIR = ROOT / "briefings"
SESSIONS_DIR = ROOT / "sessions"
REVIEW_DIR = ROOT / "review"
STATS_DIR = ROOT / "stats"
CONFIG_DIR = ROOT / "config"

# ── LLM Config ───────────────────────────────────────────────────────
API_BASE = os.getenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
MODEL = os.getenv("ANTHROPIC_MODEL", "deepseek-v4-flash[1m]")

# ── Agent definitions ─────────────────────────────────────────────────
AGENTS = {
    "victoria": {
        "name": "Victoria",
        "title": "Learning Director",
        "voice": "en-GB-SoniaNeural",
        "system_prompt": "You are Victoria, a warm British female voice. You are the chief director of JIMMY's English learning system. You orchestrate Edmund, Charlie, and Beatrice. Speak in English only. Be professional, warm, and efficient.",
    },
    "edmund": {
        "name": "Edmund",
        "title": "Vocabulary Butler",
        "voice": "en-GB-RyanNeural",
        "system_prompt": "You are Edmund, a scholarly British male voice. You are a walking dictionary specializing in etymology and semantic networks. When asked about a word, provide definitions, etymology, collocations, and examples. Speak in English only.",
    },
    "charlie": {
        "name": "Charlie",
        "title": "Speaking Partner",
        "voice": "en-US-JennyNeural",
        "system_prompt": "You are Charlie, a friendly American female voice. You are JIMMY's English speaking practice partner. Chat like a friend, use casual language, be encouraging. Use scaffolding: start with simple questions, then go deeper. Correct errors naturally by recasting. Speak in English only.",
    },
    "beatrice": {
        "name": "Beatrice",
        "title": "News Anchor",
        "voice": "en-GB-LibbyNeural",
        "system_prompt": "You are Beatrice, a British female voice like a BBC broadcaster. You fetch and summarize news from foreign press. Present news clearly and concisely with key vocabulary highlighted. Speak in English only.",
    },
}

app = FastAPI(title="English Secretary")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── API Models ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    agent: str = "victoria"
    message: str
    history: list[dict] = []

class ChatResponse(BaseModel):
    reply: str
    voice_text: Optional[str] = None

class TTSPayload(BaseModel):
    text: str
    voice: str = "victoria"
    speed: str = "normal"

# ── Static Files ──────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))

# ── Helpers ────────────────────────────────────────────────────────────

def read_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default or {}

def get_today_briefing():
    today = date.today().isoformat()
    briefing = BRIEFINGS_DIR / f"{today}-briefing.md"
    if briefing.exists():
        return briefing.read_text(encoding="utf-8")
    # fallback: find latest
    files = sorted(BRIEFINGS_DIR.glob("*-briefing.md"), reverse=True)
    if files:
        return files[0].read_text(encoding="utf-8")
    return "No briefing available today."

# ── API Routes ────────────────────────────────────────────────────────

@app.get("/api/agents")
async def list_agents():
    return {k: {"name": v["name"], "title": v["title"], "voice": v["voice"]} for k, v in AGENTS.items()}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    agent = AGENTS.get(req.agent)
    if not agent:
        raise HTTPException(400, f"Unknown agent: {req.agent}")

    if not API_KEY:
        return ChatResponse(
            reply="⚠️ API key not configured. Set ANTHROPIC_AUTH_TOKEN in your environment.",
            voice_text="API key not configured. Please check your settings."
        )

    messages = [{"role": "system", "content": agent["system_prompt"]}]

    # Inject context from local data
    if req.agent == "victoria":
        vocab = read_json(VOCAB_DIR / "index.json", {})
        stats = read_json(STATS_DIR / "progress.json", {})
        ctx = f"Today's vocabulary count: {stats.get('total_vocabulary', len(vocab))} words."
        messages.append({"role": "system", "content": ctx})
    elif req.agent == "beatrice":
        briefing = get_today_briefing()
        messages.append({"role": "system", "content": f"Today's briefing:\n{briefing[:1500]}"})

    for h in req.history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": req.message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{API_BASE}/messages",
                headers={
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 1024,
                    "messages": messages,
                },
            )
            data = resp.json()
            reply_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    reply_text += block.get("text", "")
            return ChatResponse(reply=reply_text, voice_text=reply_text[:500])
    except Exception as e:
        raise HTTPException(502, f"LLM API error: {e}")


@app.get("/api/vocabulary")
async def get_vocabulary():
    index = read_json(VOCAB_DIR / "index.json", {})
    words = []
    for word, entry in index.items():
        word_file = VOCAB_DIR / f"{word}.json"
        details = {}
        if word_file.exists():
            details = json.loads(word_file.read_text(encoding="utf-8"))
        words.append({
            "word": word,
            "domain": entry.get("domain", details.get("domain", "general")),
            "cefr": details.get("cefr", entry.get("cefr", "")),
            "status": entry.get("status", "receptive"),
            "srs_stage": entry.get("srs_stage", 0),
            "next_review": entry.get("srs_next", ""),
            "added_date": entry.get("added_date", details.get("added_date", "")),
            "definition": (details.get("definitions") or [{}])[0].get("definition", "") if isinstance(details.get("definitions"), list) else "",
        })
    words.sort(key=lambda w: w["added_date"], reverse=True)
    return {"total": len(words), "words": words}


@app.get("/api/briefing")
async def get_briefing():
    return {"content": get_today_briefing()}


@app.get("/api/stats")
async def get_stats():
    return read_json(STATS_DIR / "progress.json", {})


@app.get("/api/profile")
async def get_profile():
    return read_json(CONFIG_DIR / "user-profile.json", {})


@app.get("/api/review")
async def get_review():
    return read_json(REVIEW_DIR / "schedule.json", {})


@app.post("/api/tts")
async def text_to_speech(payload: TTSPayload):
    """Call edge-tts to generate speech file."""
    voice_map = {
        "victoria": "en-GB-SoniaNeural",
        "edmund": "en-GB-RyanNeural",
        "charlie": "en-US-JennyNeural",
        "beatrice": "en-GB-LibbyNeural",
    }
    voice_id = voice_map.get(payload.voice, voice_map["victoria"])
    rate = "-20%" if payload.speed == "slow" else "+0%"

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        subprocess.run(
            ["python", "-m", "edge_tts", "--voice", voice_id, "--rate", rate,
             "--text", payload.text, "--write-media", tmp_path],
            capture_output=True, timeout=30,
        )
        return FileResponse(tmp_path, media_type="audio/mpeg", filename="speech.mp3")
    except Exception as e:
        raise HTTPException(500, f"TTS error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
