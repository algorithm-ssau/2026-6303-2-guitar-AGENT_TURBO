# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered guitar recommendation agent that scrapes the Reverb marketplace (own HTML scraper, no official Reverb API). Two modes: **search** (find guitars on Reverb) and **consultation** (answer guitar-related questions). Communication via WebSocket (primary) and REST API (fallback).

## Commands

### Backend (from project root)

```bash
# Install dependencies
pip install -r requirements.txt

# Run server (port 8000)
uvicorn backend.main:app --reload

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_ranking.py -v

# Run a specific test
pytest tests/test_ranking.py::test_function_name -v
```

### Frontend (from `frontend/`)

```bash
npm install
npm run dev          # Dev server on port 5173
npm run build        # Production build
npm run test         # Vitest (watch mode)
```

### Environment

Copy `.env.example` to `.env` and set `GROQ_API_KEY`. With `USE_MOCK_REVERB=true`, Reverb search uses local mock data instead of hitting the live site (recommended for tests and demo).

## Architecture

### Pipeline (core data flow)

```
User query → detect_mode() → "search" | "consultation"
  Search:       LLM extract_search_params → search_reverb() → rank_results() → results
  Consultation: LLM ask() → text answer
```

Entry point: `backend/agent/service.py:interpret_query()` — orchestrates the full pipeline with status callbacks for WebSocket progress updates.

### Backend (Python + FastAPI)

- `backend/main.py` — app setup, WebSocket `/chat` endpoint, includes REST router
- `backend/agent/` — mode detection (regex-based), LLM client (Groq SDK), parameter extraction from LLM JSON
- `backend/search/` — Reverb HTML scraper integration (with mock fallback for tests/demo), REST router (`/api/chat`), Pydantic models
- `backend/ranking/` — scoring algorithm (budget weight + title/type/pickups/brand matching)
- `backend/utils/` — logger, snake_case↔camelCase serializer

Module convention: each module has `service.py` (logic), `router.py` (endpoints), `models.py` (Pydantic schemas). Modules don't import each other's internals — interaction through explicit function signatures.

### Frontend (React + TypeScript + Vite)

Feature-based structure under `frontend/src/features/`. The `chat` feature contains all chat components, hooks, API calls, and types. Shared code lives in `frontend/src/shared/`.

- `useChat` hook manages WebSocket connection (`ws://localhost:8000/chat`) with auto-reconnect
- Vite proxies `/api` requests to backend at `http://localhost:8000`
- Zod validates all API responses

### WebSocket Message Protocol

Frontend↔Backend messages are JSON with `type` field: `"status"` (progress updates), `"result"` (final response), `"error"`. Results include `mode: "search" | "consultation"`.

## Conventions

- Comments in Russian
- Commit messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Branch naming: `feature/<person>/<feature>`
- All config via environment variables, no hardcoded values
- All API data typed with Pydantic (backend) and Zod (frontend)
- Backend sends camelCase JSON to frontend (converted via `snake_to_camel` utility)
- LLM system prompts loaded from `docs/AGENT_PROMPT.md` and `docs/CONSULTATION_PROMPT.md`
- Docs directory contains API contracts, mode detection rules, ranking algorithm docs, and guitar parameter mappings
