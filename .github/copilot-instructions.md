# AI Coding Agent Instructions

## Project Overview

**The Sixth Element** is a campus/community questionnaire exchange platform. Users publish surveys and complete others' surveys to earn points. Core workflow: register → browse tasks → fill surveys → earn points → publish surveys → receive responses.

**Tech Stack:**
- Backend: Django 6.0 + MySQL (module/survey_app/)
- Frontend: Vue 3 + Vite (frontend/sixth_element/)
- Key files: module/survey_app/settings.py, core/models.py, core/views.py, core/urls.py

## Architecture & Data Flow

### Backend Structure
- **Entry point:** `Main.py` (Django management wrapper with module/ path injection)
- **Config:** `module/survey_app/settings.py` (MySQL at 127.0.0.1:3306, DB name: sixth_element)
- **Core app:** `core/` contains all models, views, and URL routing
- **Models (core/models.py):** AppUser, Survey, FillRecord, PointsLog, Report
  - AppUser: id (string PK: u_{uuid}), email, nickname, points, credit_score, activity_points, token (auth)
  - Survey: id, owner_fk, title, link, reward_points, deadline, status (active/closed), estimated_minutes
  - FillRecord: id, survey_fk, user_fk, duration_seconds, status (pending/approved/rejected), points_awarded
  - PointsLog: audit trail for point transactions

### API Pattern (core/urls.py → core/views.py)
- Base: `/api/v1/` (routed in module/survey_app/urls.py)
- **Auth:** POST /auth/register, POST /auth/login (return access_token)
- **Auth flow:** Token stored in AppUser.token, extracted via "Bearer {token}" header
- **Survey endpoints:** GET /surveys, POST /surveys/{id}/fills, PATCH /surveys/{id}/close
- **User endpoints:** GET /users/me, PATCH /users/me (user updates)
- **Points:** GET /points/logs (user's transaction history)

### Response Format
All endpoints return JSON:
- Success: `{"key": value}` or JSON model response (from survey_response(), user_response())
- Error: `{"error": "message"}` with HTTP status codes (401=auth, 405=method, 422=validation, etc.)
- Timestamps: ISO 8601 with Z suffix (now_iso() helper in views.py)

### Frontend Structure
- **Vite proxy (vite.config.js):** `/api` → `http://127.0.0.1:8000` for local dev
- **Router (src/router/index.js):** SPA with 6+ routes (task-hall, survey-management, survey-builder, analytics, profile)
- **Views:** Vue components per route (src/views/*.vue)
- **Store pattern:** TBD (likely uses localStorage or Pinia for auth token + user state)

## Developer Workflow

### Backend Development
```bash
# Ensure MySQL: database 'sixth_element', user 'sixth_element', password '123456'

### Frontend Development
```bash
cd frontend/sixth_element
npm install
npm run dev    # Vite dev server on http://localhost:5173, proxies /api to Django
npm run build  # Production build to dist/
npm run lint   # ESLint fix with cache
```

### Adding Models
1. Create model in `core/models.py`
2. Create migration: `python Main.py makemigrations`
3. Apply: `python Main.py migrate`
4. Add response serializer (like survey_response, user_response) in views.py
5. Add URL route in core/urls.py

### Adding API Endpoints
1. Create view function in `core/views.py` with:
   - `@csrf_exempt` decorator (API doesn't use CSRF tokens)
   - `require_auth(request)` for protected endpoints (returns user or error)
   - Input validation via `parse_json(request)`
   - Response via `JsonResponse()` or `error(status, message)`
2. Register in `core/urls.py` with descriptive path

## Code Patterns & Conventions

### Django Views (core/views.py)
- **No class-based views:** Use function-based views (FBV)
- **ID generation:** UUIDs with prefixes (e.g., "u_" for users, survey IDs TBD)
- **Auth token:** Single token per user, regenerated on login, checked via Bearer header
- **Validation:** Minimal, done in view functions (not forms/serializers)
- **No third-party:** No DRF, Celery, or task queues—keep it simple
- **CSRF disabled:** @csrf_exempt on all API routes (stateless token auth)

### Frontend (Vue 3)
- **Setup script:** `<script setup>` syntax (no Options API)
- **Components:** SFC (Single File Component) in .vue files
- **Router:** Vue Router 4.x with component-based routes
- **API calls:** Likely fetch() with Authorization header (Bearer token from localStorage)
- **State:** TBD (check views for localStorage or Pinia patterns)

### JSON API Convention
- `POST /path` → create resource, return new object
- `GET /path` → list (filtered by user context)
- `GET /path/{id}` → detail
- `PATCH /path/{id}` → partial update
- Include owner_id, created_at in responses for audit

## Key Business Rules (Critical for Implementation)

1. **Points economy:** Publishing costs points, filling gains points (configurable per survey)
2. **Credit score:** Starts at 80, affects trust/visibility
3. **Activity points:** Track contribution, non-tradeable
4. **Fill status:** pending → reviewed by owner → approved/rejected → points awarded
5. **Anti-cheat:** Minimum fill duration check (not yet implemented, but expected)
6. **Report system:** User-generated reports on survey/user abuse, status: pending/reviewed

## Testing & Debugging

- **No test suite yet:** Create tests in test files if adding features
- **Debug settings:** DEBUG=1 in env (default in settings.py)
- **Migrations:** Track in core/migrations/, never edit manually
- **Common errors:**
  - "Unauthorized" → missing/invalid Bearer token
  - "email already registered" → check AppUser.objects.filter(email=email)
  - MySQL connection → verify settings.py DB credentials match server

## Files to Know

| File | Purpose |
|------|---------|
| core/models.py | All Django ORM models (7 classes) |
| core/views.py | ~420 lines, all API endpoints |
| core/urls.py | Route definitions (13 paths) |
| module/survey_app/settings.py | Django config, DB, installed apps |
| frontend/sixth_element/src/router/index.js | SPA route definitions |
| Main.py | Entry point (manages sys.path for module/) |

## Integration Points

- **Frontend ↔ Backend:** Vite proxy dev, production likely uses reverse proxy
- **Auth:** Token in Bearer header (stateless, no sessions)
- **Database:** MySQL, single instance, no replicas mentioned
- **External:** Survey links are stored as URLs (third-party forms), not embedded

---

**Last Updated:** 2026-01-15  
**Branch:** fans1  
**Instructions written for:** AI coding agents (Claude/Copilot/etc.)
