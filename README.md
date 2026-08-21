# Task Management API

Production-ready REST API for task management, asynchronous processing, and analytics built with FastAPI, PostgreSQL, and Redis.

## Tech Stack

- **FastAPI** (Python 3.13)
- **PostgreSQL 16** + **SQLAlchemy 2.0 (asyncpg)**
- **Redis 7** (Rate Limiting & Async Job Queue)
- **Alembic** (Database Migrations)
- **Pydantic v2** & **Pydantic-Settings**
- **JWT Auth** (Role-based access, Argon2 password hashing)
- **HTTPX** (Non-blocking external API integrations)
- **Docker Compose**
- **Pytest** (Async test suite)

## Quick Start (Docker)

Start the entire application, PostgreSQL, and Redis with migrations applied automatically:

```bash
docker compose up --build
```

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/health](http://localhost:8000/health)

## Local Setup

1. **Start PostgreSQL and Redis:**
   ```bash
   docker compose up -d db redis
   ```
2. **Apply migrations:**
   ```bash
   alembic upgrade head
   ```
3. **Run dev server:**
   ```bash
   uvicorn main:app --reload
   ```

## Running Tests

```bash
pytest -v
```

## Core Features (Round 1 & Round 2)

- **Task Lifecycle & State Machine:** Strict status transitions (`Backlog` → `In Progress` → `Review` → `Done` / `Cancelled`) with validation rules.
- **Performance Logging Middleware:** Real-time request duration tracking. Logs warning to `app.log` for requests exceeding 500ms.
- **Bulk CSV Import:** High-performance batch creation of tasks from CSV using SQLAlchemy Core Bulk Insert (`POST /api/v1/tasks/bulk-import`).
- **Redis Rate Limiter:** Protects comment submissions (`POST /api/v1/tasks/{id}/comments`) with atomic Redis counters (max 5 comments/min → `429 Too Many Requests`).
- **ZenQuotes API Integration:** Asynchronous (`httpx.AsyncClient`) fetching of motivational quotes automatically posted by `System` upon task completion.
- **Task Queue & Async CSV Export:** Long-running task export using Redis shared state (`POST /tasks/export` [202 Accepted] → `GET /tasks/export/{task_id}` [Polling status] → `GET /tasks/export/{task_id}/download` [Streamed CSV FileResponse]).
- **Search, Filters & Custom Sorting:** Full-text search (`ILIKE`), composite filters, and priority-deadline ordering.
- **Analytics & Background Automation:** `/tasks/overdue`, `/tasks/stats`, and automated periodic cancellation of overdue tasks.
