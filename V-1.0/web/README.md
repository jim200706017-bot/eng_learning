# English Secretary Web App

Web-based UI for the English Learning Secretary System. Gmail-style interface with voice interaction.

## Setup

```bash
cd web
pip install -r requirements.txt
```

## Run

```bash
cd web
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

**Note:** Requires Python 3.11+ with `httpx` installed. The app reads your local vocabulary, briefings, and stats files directly.

## Features

- Gmail-style sidebar with agent selection
- Chat with AI secretary agents
- Voice input (browser microphone) + auto speech output
- Real-time vocabulary library viewer
- Today's briefing display
- GitHub sync status

## Architecture

```
Frontend (HTML/CSS/JS)  ←→  FastAPI Backend  ←→  DeepSeek API
                     ↓                        ↓
              Web Speech API           vocabulary/, briefings/, 
              (voice I/O)              sessions/, config/
```
