# Gym Management App

A simple, beginner-friendly gym management application.

Two kinds of users:

- **Gym Manager** — manages members and classes, views enrollments.
- **Gym Goer (Member)** — subscribes, browses classes, enrolls/cancels.

Built with **FastAPI + SQLAlchemy + Postgres** on the backend and **React (Vite) + Tailwind** on the frontend. Everything runs via Docker Compose.

## Features

**Manager**
- Log in
- Add / remove members
- Create, edit, delete classes (with `?force=true` for classes that have enrollments)
- See roster per class
- See all members and their subscription status

**Member**
- Sign up and log in
- Subscribe to a plan (monthly / quarterly / yearly) — status flag only, no payments
- Browse classes, enroll, cancel
- See their own upcoming classes

## Running the app

Copy the example env file (optional — defaults work out of the box):

```bash
cp .env.example .env
```

Start everything:

```bash
docker compose up --build
```

Seed the database (in a second terminal, after services are up):

```bash
docker compose exec backend python -m app.seed
```

Open:

- Frontend — http://localhost:3000
- Swagger — http://localhost:8000/docs

## Seeded login

After seeding:

- **Manager** — `manager@gymapp.com` / `manager123`
- **Members** — `alice@gymapp.com`, `bob@gymapp.com`, … / `member123`

The seeder creates 1 manager, 15 members (mix of active/expired subs), 8 classes across the week, and ~25 sample enrollments. Running it twice is safe — it wipes and repopulates.

## Environment variables

See [.env.example](./.env.example). All have sensible defaults for local use.

| Variable             | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `POSTGRES_USER`      | Postgres username                         |
| `POSTGRES_PASSWORD`  | Postgres password                         |
| `POSTGRES_DB`        | Postgres database name                    |
| `JWT_SECRET`         | Secret used to sign JWTs                  |
| `JWT_EXPIRE_MINUTES` | Token lifetime                            |
| `CORS_ORIGINS`       | Comma-separated origins allowed by CORS   |
| `VITE_API_URL`       | Frontend's base URL for API calls         |

## API endpoints

Full interactive docs at `/docs`. Summary:

```
POST   /auth/register          public       create a member account
POST   /auth/login             public       email+password -> JWT
GET    /auth/me                any          current user

GET    /classes                any          list all classes
POST   /classes                manager      create class
PATCH  /classes/{id}           manager      update class
DELETE /classes/{id}?force=    manager      delete (force if enrolled)
GET    /classes/{id}/roster    manager      who's enrolled in this class

POST   /enrollments            member       enroll in a class
DELETE /enrollments/{id}       member       cancel own enrollment
GET    /enrollments/me         member       my upcoming classes

GET    /members                manager      list all members + sub status
POST   /members                manager      add a member
DELETE /members/{id}           manager      remove a member

POST   /subscriptions          member       pick a plan -> active status
GET    /subscriptions/me       member       my current/latest subscription
```

### Business rules enforced

- A member without an active subscription cannot enroll — returns **402**.
- A full class rejects new enrollments — returns **409**.
- Duplicate enrollment — returns **409**.
- Canceling someone else's enrollment — returns **403**.
- Deleting a class with enrollments — returns **409** unless `?force=true`.

## Tech stack

- **Backend** — FastAPI, SQLAlchemy 2.0, Alembic, passlib (bcrypt), python-jose (JWT), Pydantic v2
- **Frontend** — React 18, React Router, Vite, Tailwind CSS
- **Database** — Postgres 16
- **Containerization** — Docker Compose (three services: `db`, `backend`, `frontend`)

## Project layout

```
gym-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/        # config, db, security
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routers/     # auth, members, classes, enrollments, subscriptions
│   │   ├── services/    # business logic
│   │   └── seed.py
│   ├── alembic/
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api.js       # one place for all fetch calls
│   │   ├── auth.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Non-goals

- No payment processing — "subscribed" is just a flag.
- No email, notifications, or real-time updates.
- No tests yet.
- Two hardcoded roles. (Future: swap to Keycloak.)

## Development notes

- Tables are auto-created at app startup via `Base.metadata.create_all()` so the app runs out of the box. For real schema changes, generate Alembic migrations (see [backend/alembic/README.md](./backend/alembic/README.md)).
- The frontend mounts `./frontend` as a volume, so edits hot-reload via Vite.
- The backend mounts `./backend` too — uvicorn runs without `--reload` by default; restart the container to pick up changes, or add `--reload` in the Compose command during development.
