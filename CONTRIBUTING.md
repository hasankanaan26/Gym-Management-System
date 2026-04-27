# Contributing

Welcome! This project is built as a **learning playground**. The current code is intentionally simple, beginner-friendly, and deliberately leaves out many "production" concerns. That's not laziness — it's an invitation. Each missing piece is an opportunity to learn a real-world software engineering tool by adding it.

If you're looking to grow as an engineer, picking one of the ideas below and shipping it end-to-end will teach you more than any tutorial.

---

## How to contribute

1. **Fork** the repo and create a feature branch (`git checkout -b feature/keycloak-auth`).
2. **Open an issue first** if your change is large — it helps us discuss the approach before you write code.
3. **Keep PRs focused.** One feature, one PR. Smaller is better.
4. **Update docs.** If you add a new service, add it to [docker-compose.yml](docker-compose.yml), [.env.example](.env.example), and the [README](README.md).
5. **Don't break the golden path.** A new dev should still be able to clone the repo and run `docker compose up --build` to get a working app.
6. **Add a short note in your PR description** explaining what you learned. We love that.

We don't enforce strict code style yet — just match the surrounding code. Python: snake_case, type hints, no unused imports. JS/JSX: 2-space indent, no semicolons-vs-semicolons drama, just be consistent within the file.

---

## Idea board

Pick one. Each item links a real-world tool to the part of the codebase it would touch.

### Authentication & Identity

- **Replace bcrypt+JWT with [Keycloak](https://www.keycloak.org/)** — *the* canonical "real auth" upgrade. Run Keycloak in Docker Compose, configure a realm + client, swap [`app/core/security.py`](backend/app/core/security.py) to validate Keycloak-issued JWTs (use the realm's JWKS endpoint), and update the frontend to use the OIDC code flow (e.g. `keycloak-js`). You'll learn OIDC, OAuth 2.0, JWKS, refresh tokens, and SSO.
- **Add a third role: Trainer.** Trainers can edit their own classes but can't add/remove members. Touches [`models/user.py`](backend/app/models/user.py), [`core/security.py`](backend/app/core/security.py), all manager routes.
- **Multi-factor auth.** TOTP via [pyotp](https://github.com/pyauth/pyotp) and a QR code on enrollment.
- **Password reset flow** with one-time tokens and an email step (see "Email" below).

### Secrets & Config

- **[HashiCorp Vault](https://www.vaultproject.io/)** for secrets management. Run Vault in Compose dev mode, store `JWT_SECRET` and DB creds in Vault, fetch them at startup via [hvac](https://github.com/hvac/hvac). Replaces hardcoded `.env` values for production realism.
- **[Doppler](https://www.doppler.com/) or [SOPS](https://github.com/getsops/sops)** as a lighter-weight alternative to Vault.
- **Switch from environment variables to Pydantic Settings** with validation, so missing required vars fail loudly at startup.

### Logging & Observability

- **[Seq](https://datalust.co/seq)** for structured log search. Add [`structlog`](https://www.structlog.org/) on the backend, ship JSON logs to Seq via the [seqlog](https://pypi.org/project/seqlog/) handler, and run Seq as a Compose service. Searchable logs in the browser within an afternoon.
- **OpenTelemetry + [Jaeger](https://www.jaegertracing.io/) or [Tempo](https://grafana.com/oss/tempo/)** for distributed tracing. Instrument FastAPI and SQLAlchemy. See *every* SQL query a request triggers.
- **[Prometheus + Grafana](https://prometheus.io/)** for metrics. Use `prometheus-fastapi-instrumentator` to expose `/metrics`. Build a dashboard with request rate, latency p95, and error rate.
- **[Sentry](https://sentry.io/)** for error tracking. The free tier is enough for learning. One SDK call on the backend, one on the frontend.
- **Audit log table.** Record every manager action (member removed, class deleted) in an `audit_events` table. Show recent activity on the manager dashboard.

### Service Discovery & Configuration

- **[HashiCorp Consul](https://www.consul.io/)** for service registration and dynamic config. Overkill for two services, but wiring it up teaches you what service meshes solve.
- **[Traefik](https://traefik.io/)** as a reverse proxy in front of the frontend and backend. Auto-routing by hostname, free TLS via Let's Encrypt.

### Caching, Queues & Real-time

- **Redis** for response caching on hot endpoints (e.g. `GET /classes` invalidated on class create/update).
- **[Celery](https://docs.celeryq.dev/) + Redis** for background jobs. Move email sending and "expire stale subscriptions" cron into Celery tasks.
- **WebSockets** for live class roster updates — when someone enrolls, the manager's roster page updates instantly. FastAPI has built-in `WebSocket` support.
- **Server-sent events** as a simpler alternative to WebSockets for one-way push.

### Payments & Email

- **[Stripe](https://stripe.com/)** integration to actually charge for subscriptions. Replace the "status flag" with Checkout Sessions and webhook-driven status updates. Learn webhooks the right way (signature verification, idempotency).
- **Transactional email** via [Resend](https://resend.com/), [Postmark](https://postmarkapp.com/), or AWS SES — welcome emails, class reminders, subscription expiry warnings.
- **iCal export.** A `.ics` file per member with their upcoming classes; let them subscribe in Google Calendar.

### Testing

- **[pytest](https://pytest.org/)** for the backend. Start with the business rules in [`services/enrollments.py`](backend/app/services/enrollments.py) — they're pure functions on top of a session, perfect to unit-test. Then add integration tests using FastAPI's `TestClient` and a throwaway sqlite DB.
- **[Vitest](https://vitest.dev/) + React Testing Library** on the frontend. Render a page, click "Enroll", assert the API was called.
- **[Playwright](https://playwright.dev/)** for end-to-end. Spin up the whole stack, click through Manager → create a class → log in as Member → enroll.
- **[Schemathesis](https://schemathesis.readthedocs.io/)** for property-based API testing — generates random valid requests from your OpenAPI schema and looks for crashes.

### CI/CD & DevOps

- **GitHub Actions** workflow: on push, build both Docker images, run backend tests, run frontend tests, run a smoke test against `docker compose up`.
- **Pre-commit hooks** with [pre-commit](https://pre-commit.com/): ruff + black for Python, prettier + eslint for JS.
- **Database migrations in CI.** Run `alembic upgrade head` against an ephemeral Postgres before tests.
- **Multi-stage Dockerfile** for the frontend — build with Node, serve with Nginx. Half the image size.
- **Helm chart** to deploy to a local Kubernetes cluster (kind or minikube). Big jump in scope, but a great portfolio piece.

### Database & Performance

- **N+1 query fixes.** [`routers/classes.py`](backend/app/routers/classes.py) calls `count()` for each class — fix it with a single grouped query and `selectinload`. Use `EXPLAIN ANALYZE` to prove it.
- **[Alembic migrations](backend/alembic/)** for real. Generate the initial migration, remove the `Base.metadata.create_all()` shortcut from [`main.py`](backend/app/main.py).
- **Read replicas.** Configure a separate read-only SQLAlchemy engine and route GET requests to it.
- **Soft deletes.** Add `deleted_at` columns and a global query filter so deletes are recoverable.
- **Audit columns.** `created_by`, `updated_at`, `updated_by` populated automatically via SQLAlchemy events.

### Frontend Improvements

- **[TanStack Query](https://tanstack.com/query)** for server state — caching, refetching, optimistic updates. Replace the manual `useEffect + fetch` pattern.
- **[Zod](https://zod.dev/)** schemas mirroring the Pydantic models, validated on the client.
- **TypeScript** migration. Convert `.jsx` → `.tsx`, generate types from the OpenAPI spec via [openapi-typescript](https://github.com/drwpow/openapi-typescript).
- **Accessibility audit.** Run axe-core, fix what it finds. Add proper aria-labels, keyboard nav, focus management on modals.
- **Dark mode** via Tailwind's `dark:` variant + a system-preference toggle.
- **PWA / offline shell.** Service worker, installable, cached classes list.

### Bigger architecture moves

- **Multi-tenancy.** Multiple gyms, each with their own manager, members, and classes. Add a `tenants` table and a `tenant_id` foreign key to everything else. Touches almost every model, schema, and route.
- **Event-driven.** Publish a `member.enrolled` event to RabbitMQ or Kafka when someone enrolls; have a separate worker send the confirmation email. Real microservices intro.
- **Recurring classes.** Today a class is a single weekly slot. Model it as a template + generated instances per week, so cancellations and roster snapshots are per-instance.
- **Mobile app.** React Native or Expo, hitting the same backend.
- **GraphQL gateway** in front of the REST API. Strawberry on the backend, Apollo on the frontend.

---

## What we'd love to see in your PR

- A short "what I learned" note in the description.
- Updated `README.md` and `.env.example` if you added env vars or services.
- A `docker compose up --build` that still works for someone who hasn't touched anything else.
- Tests if you added a complex feature.
- Screenshots if you changed the UI.

---

## Questions?

Open a [discussion](https://github.com/hasankanaan26/Gym-Management-System/discussions) or an [issue](https://github.com/hasankanaan26/Gym-Management-System/issues). No question is too basic — this repo exists for people learning, and that includes the maintainers.

Happy hacking!
