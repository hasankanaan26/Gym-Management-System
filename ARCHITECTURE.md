# Architecture overview

A bird's-eye view of how the pieces fit together. Read this once before diving into the code — it'll save you a lot of "where does X live?" hunting.

```
┌─────────────────┐     HTTPS/JSON     ┌──────────────────┐     SQL     ┌──────────────┐
│  React (Vite)   │ ─────────────────► │  FastAPI         │ ──────────► │  Postgres    │
│  localhost:3000 │ ◄───────────────── │  localhost:8000  │ ◄────────── │  localhost:  │
│                 │   JWT in header    │                  │             │  5433 (host) │
└─────────────────┘                    └──────────────────┘             └──────────────┘
        │                                       │
        │  localStorage holds the JWT           │  validates JWT signature with JWT_SECRET
        │  (sent on every request)              │  loads the user row to check role
        ▼                                       ▼
   page components                       routers + services
```

## Request lifecycle (e.g. "member enrolls in a class")

1. **User clicks "Enroll"** in [BrowseClasses.jsx](frontend/src/pages/BrowseClasses.jsx).
2. The page calls `api.enroll(classId)` from [api.js](frontend/src/api.js).
3. That sends `POST /enrollments` to the backend with `Authorization: Bearer <jwt>`.
4. **FastAPI dependency** [`require_member`](backend/app/core/security.py) extracts the JWT, decodes it, loads the user, and rejects non-members with 403.
5. **Router** [`create_enrollment`](backend/app/routers/enrollments.py) hands off to the service layer.
6. **Service** [`enroll_member`](backend/app/services/enrollments.py) checks all the business rules:
   - Class exists? (404 if not)
   - User has an active subscription? (402 if not)
   - Not already enrolled? (409 if so)
   - Class not full? (409 if so)
7. If all good, insert the row, commit, return.
8. The frontend's `await api.enroll(...)` resolves, and the page re-fetches the list.

This same pattern — **route → dependency check → service → DB → response** — repeats throughout the codebase. Once you grok one route, you grok them all.

## Layer responsibilities

| Layer | Lives in | Responsible for |
|-------|----------|-----------------|
| **Routes** | `app/routers/*.py` | HTTP plumbing — extract input via Pydantic, call the right service, return the response. No business logic. |
| **Services** | `app/services/*.py` | Business rules — "can this happen?", "what does this mean?". Pure functions on top of the DB session. |
| **Models** | `app/models/*.py` | Database schema. SQLAlchemy ORM classes mirroring tables. |
| **Schemas** | `app/schemas/*.py` | API contract. Pydantic classes describing request bodies and response shapes. |
| **Core** | `app/core/*.py` | Cross-cutting infra — config, DB session, security. |

The backend is a tiny three-tier app: **HTTP → business logic → data**. Each layer only talks to the one immediately below it.

## Frontend layer responsibilities

| Layer | Lives in | Responsible for |
|-------|----------|-----------------|
| **Pages** | `src/pages/*.jsx` | One file per route. Owns its own state, fetches its own data. |
| **Components** | `src/components/*.jsx` | Reusable UI bits (buttons, layout, badges). |
| **Auth context** | `src/auth.jsx` | Global "who's logged in" state via React Context. |
| **API client** | `src/api.js` | The *only* file that knows fetch URLs. Token injection happens here. |

## Authentication model

We use **stateless JWT auth**:

- On login, the server issues a signed token (`access_token`) carrying `{sub: user_id, role, exp}`.
- The frontend saves it in `localStorage` and sends it on every request as `Authorization: Bearer <token>`.
- The server doesn't track sessions — it re-validates the signature and re-loads the user from the DB on each request.
- Logout = wipe local storage. The token will keep working until it expires (currently 60 minutes).

This is the simplest auth design that works. Real production systems usually add: refresh tokens, token revocation lists, secure HttpOnly cookies, MFA. See [CONTRIBUTING.md](CONTRIBUTING.md#authentication--identity) for upgrade paths.

## Database model

```
users ──┬── subscriptions   (one user → many subscriptions, latest one wins)
        └── enrollments ── classes   (join table; unique on user_id + class_id)
```

Foreign keys all use `ON DELETE CASCADE` so deleting a user automatically removes their subscriptions and enrollments. The ORM has matching `cascade="all, delete-orphan"` for in-app deletes.

## Configuration & secrets

Everything reads from environment variables, with defaults in [`app/core/config.py`](backend/app/core/config.py). The single source of truth for defaults is `.env.example` at the repo root. No secrets in code.

In a production deployment you'd swap env vars for a secrets manager (Vault, AWS Secrets Manager). The `Settings` class is the only place to change.

## What's *intentionally* missing

This is a learning app. Many production-grade pieces are deliberately absent so each one can be added as a focused contribution:

- No tests yet. (`pytest` for the backend, Vitest for the frontend, Playwright for E2E.)
- No real auth provider. (Keycloak.)
- No structured logging. (Seq, OpenTelemetry, Sentry.)
- No background jobs / scheduling. (Celery + Redis.)
- No payments. (Stripe.)
- No CI/CD. (GitHub Actions.)
- No production Docker images. (Multi-stage builds, nginx for the frontend.)
- One race condition. (Capacity check + insert isn't atomic — see [`services/enrollments.py`](backend/app/services/enrollments.py).)
- N+1 queries on `/classes`. (Replace with a `GROUP BY` or window function.)

Each of these is listed in [CONTRIBUTING.md](CONTRIBUTING.md) with a recommended tool and the files it would touch. Pick whatever interests you and ship it end-to-end — that's the point of the repo.
