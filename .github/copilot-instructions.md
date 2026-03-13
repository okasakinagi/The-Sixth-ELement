# AI Coding Agent Instructions

## Project Overview

The Sixth Element is a questionnaire exchange platform.
Users publish surveys, complete others' surveys, and gain points.

Current core flow:
register/login -> browse task hall -> submit survey response -> points awarded immediately -> publish/cancel/manage surveys.

## Current Tech Stack

- Backend: Django 6.0 + MySQL
- Frontend: Vue 3 + Vite
- Entry point: Main.py
- Django project: module/survey_app/

## Runtime Architecture (Important)

The API is not a single-app design anymore.
It is split across multiple Django apps and mounted under the same /api/v1 prefix.

Main URL mount:

- module/survey_app/urls.py

Mounted app routes:

- core.urls (auth, users, fill entry, legacy endpoints, internal similarity)
- survey_management.urls (survey draft/publish/manage/analytics)
- task_hall.urls (task hall)
- points_record.urls under /api/v1/points/
- personal_homepage.urls
- user_profile_extractor.urls under /api/v1/profile/

## Source of Truth for Business Logic

When code and docs conflict, trust code in this order:

1. survey_management/service
2. surveyfill/service
3. task_hall/service
4. points_record/service
5. core/views.py (contains some legacy compatibility logic)

## Authentication

- Bearer token auth via AuthToken model (not Django session auth).
- Token issued on login/register with expiration.
- Most business endpoints require Authorization: Bearer <token>.

## Data Model Notes

Primary models are in core/models.py.
Relevant points fields:

- AppUser.points: tradeable points
- AppUser.activity_points: activity metric points
- Survey.reward_points: per-response reward amount
- Survey.publish_cost_points: total publish budget spent/locked
- PointsLog: immutable ledger-like points change records

## Points Logic (Current Implementation)

### Publish (survey_management publish endpoint)

Endpoint:

- POST /surveys/{survey_id}/publish

Current required payload behavior:

- reward_points is required and must be numeric >= 0.
- budget_points is required and must be numeric >= 0.
- target is required and must be numeric >= 1.
- budget_points must satisfy: budget_points >= reward_points \* target.

Effects:

- survey.reward_points is explicitly set from payload.
- survey.publish_cost_points is set from budget_points.
- owner points are deducted by budget_points.
- PointsLog is created with negative delta.

### Fill Submit (surveyfill)

Endpoint:

- POST /surveys/{survey_id}/fills

Current behavior:

- submit once per user per survey
- duration_seconds guard is enforced
- reward is awarded immediately on submit (no waiting for review in main flow)
- awarded amount comes from survey.reward_points
- points and activity_points both increase
- PointsLog is written with points_type=fill_reward

### Cancel/Delete Refund (survey_management)

Current refund logic infers boost-like portion from existing fields:

- based on publish_cost_points, reward_points, target, completed
- inferred_speed_boost = max(0, total_paid - reward\*target)
- refund excludes inferred_speed_boost

This inference is compatibility logic because there is no dedicated boost_points field.

## Review Endpoint Status

- Legacy review endpoint still exists: POST /fills/{fill_id}/review
- Main frontend flow does not depend on review for awarding points.
- Do not reintroduce review-gated awarding unless explicitly requested.

## Frontend Reality

Key app:

- frontend/sixth_element

Important view for publish pricing contract:

- src/views/SurveyManagementView.vue

Current publish request sends:

- reward_points
- budget_points (currently reward_points \* target + optional boost entered in UI)
- target
- estimated_minutes
- difficulty

When changing publish contract, update both frontend payload and backend validation together.

## Task Hall / Recommendation

Task hall routes are in task_hall app.
Ranking currently relies on similarity service output and does not have a dedicated persisted boost_points signal.
If recommendation scoring rules change, update:

- task_hall/service/task_hall_service.py
- core/services/similarity_service.py
- core/managers/similarity_manager.py

## Points APIs

There are two points-related surfaces:

1. Legacy core endpoint:

- GET /api/v1/points/logs

2. points_record app endpoints:

- GET /api/v1/points/summary
- GET /api/v1/points/logs
- POST /api/v1/points/update

Be careful with behavior differences when modifying points logs/filtering.

## Development Workflow

Backend:

- python Main.py migrate
- python Main.py runserver

Frontend:

- cd frontend/sixth_element
- npm install
- npm run dev

## Implementation Conventions

- Use function-based views/controllers.
- Keep validation in service/controller layer (current project style).
- Preserve existing response envelope patterns and status codes.
- Write PointsLog when mutating user points in business flows.

## High-Risk Areas (Change Carefully)

1. Publish/fill/refund coupling

- survey_management publish/cancel/delete logic and surveyfill reward logic must remain consistent.

2. Dual/legacy endpoints

- Some core endpoints are compatibility paths; avoid silently switching frontend to them.

3. Points ledger consistency

- If points amount changes, ensure matching PointsLog delta and reason remain coherent.

## Guidance for AI Coding Agents

When asked to change points behavior:

1. inspect survey_management/service/survey_management_service.py
2. inspect surveyfill/service/survey_fill_service.py
3. inspect frontend publish payload in SurveyManagementView.vue
4. inspect points logs consumers (core and points_record)
5. update docs under doc/api accordingly

When asked to change only docs, keep docs aligned with current code behavior, not older design notes.

---

Last Updated: 2026-03-13
Branch Context: fans1
Target Audience: AI coding agents
