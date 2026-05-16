# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

English Secretary (英语秘书团) — AI-powered English learning system with 4 agents (Victoria, Edmund, Charlie, Beatrice). User: JIMMY, a freshman law student preparing for CET-4 (2026-06-13), IELTS (2027), general English B2, legal English A2.

## Architecture

```
User ←→ Claude Code (CLI) or Web UI (FastAPI)
               ↓
    4 Agent Skills (english-*.md files)
    Victoria (director) → orchestrates Edmund/Charlie/Beatrice
    Edmund (vocabulary) → 7-dictionary lookup + JSON entries
    Charlie (speaking) → 3-stage scaffolding + error correction
    Beatrice (news) → WebSearch + browser-search news scraping
               ↓
    Local data files (vocabulary/, briefings/, sessions/, review/, stats/)
```

- **Skill files**: `Phase-2-核心Skill文件/english-*.md` — agent definitions in full English
- **MCP servers**: Playwright (browser automation) + edge-tts (TTS) via `.claude/settings.local.json`
- **Web UI**: `web/app.py` (FastAPI) + `web/static/` (Gmail-style frontend with voice I/O)
- **Vocabulary**: `vocabulary/<word>.json` per word + `vocabulary/index.json` as index

## Key Commands

### Claude Code (CLI)
- `/beatrice` — Generate morning news briefing
- `add <word>` — Look up word via Edmund, save to vocabulary
- `/charlie` — Start speaking practice
- `/victoria` — Learning overview + SRS review
- `stats` — View learning statistics
- `review` — View SRS review queue
- `vocab-view` — Regenerate vocabulary library table (runs `vocabulary/vocab-view.py`)

### Web UI
```bash
cd web && python -m uvicorn app:app --host 0.0.0.0 --port 8000
# Then open http://localhost:8000
```

### Data Management
```bash
# Regenerate vocabulary library view
python vocabulary/vocab-view.py
```

## Data Flow

```
Morning: Beatrice briefing → User reads → selects words
  → Edmund lookup (add <word>) → save JSON → update index
  → Charlie speaking practice (uses target words)
  → Victoria SRS review (schedule next review)
```

SRS intervals: 1d → 3d → 7d → 16d → 35d → 90d

## Crontab (scheduled_tasks.json)

| Time | Task |
|------|------|
| 05:03 Mon-Sat | Beatrice news prefetch |
| 08:07 Mon-Sat | Victoria SRS check |
| 22:03 Mon-Sat | Daily learning summary |

## Environment Variables

Set in `C:\Users\HUAWEI\.claude\settings.json`:
- `ANTHROPIC_BASE_URL` — DeepSeek API endpoint
- `ANTHROPIC_AUTH_TOKEN` — API key
- `ANTHROPIC_MODEL` — Model name

## Browser-search Tool Path

`C:\Users\HUAWEI\Desktop\AI工具\.trae\skills\browser-search\browser-search-v3.js`
Used by Beatrice for article content scraping via puppeteer.

## User Profile Summary

- Law student (Civil Law), B2 general / A2 legal / C1 tech English
- Interests: philosophy, politics, psychology, law, AI tech, finance, fitness, sports, music
- Daily vocab goal: 10-12 words
- Study time: 30-60 min/day
- Preferred accent: US (no objection to UK)
