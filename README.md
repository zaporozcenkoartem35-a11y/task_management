# Task Management API

Production-ready REST API for task management, asynchronous processing, and analytics built with FastAPI, PostgreSQL, Redis, and Celery.

## Tech Stack

- **FastAPI** (Python 3.13)
- **PostgreSQL 16** + **SQLAlchemy 2.0 (asyncpg)**
- **Redis 7** (Message Broker & Result Backend)
- **Celery 5 & Celery Beat** (Distributed Task Queue & Periodic Job Scheduler)
- **Alembic** (Database Migrations)
- **Pydantic v2** & **Pydantic-Settings**
- **JWT Auth** (Role-based access, Argon2 password hashing)
- **HTTPX** (Non-blocking external API integrations)
- **Docker Compose**
- **Pytest** (Async test suite)

## Quick Start (Docker)

Start the entire stack (FastAPI app, PostgreSQL, Redis, Celery Worker, Celery Beat) with automatic database migrations:

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
3. **Run Celery Worker and Beat:**
   ```bash
   celery -A app.core.celery_app.celery_app worker --loglevel=info
   celery -A app.core.celery_app.celery_app beat --loglevel=info
   ```
4. **Run dev server:**
   ```bash
   uvicorn main:app --reload
   ```

## Running Tests

```bash
pytest -v
```

## Core Features

- **Task Lifecycle & State Machine:** Strict status transitions (`Backlog` → `In Progress` → `Review` → `Done` / `Cancelled`) with validation rules.
- **Celery Distributed Task Queue:** Asynchronous CSV export offloaded to Celery workers via Redis broker (`POST /tasks/export` [202 Accepted] → `GET /tasks/export/{task_id}` [Polling status] → `GET /tasks/export/{task_id}/download` [Streamed CSV FileResponse]).
- **Celery Beat Periodic Scheduler:** Automated periodic job executing every minute to detect and cancel overdue tasks without web-server blocking loops.
- **Performance Logging Middleware:** Real-time request duration tracking. Logs warning to `app.log` for requests exceeding 500ms.
- **Bulk CSV Import:** High-performance batch creation of tasks from CSV using SQLAlchemy Core Bulk Insert (`POST /api/v1/tasks/bulk-import`).
- **Redis Rate Limiter:** Protects comment submissions (`POST /api/v1/tasks/{id}/comments`) with atomic Redis counters (max 5 comments/min → `429 Too Many Requests`).
- **ZenQuotes API Integration:** Asynchronous (`httpx.AsyncClient`) fetching of motivational quotes automatically posted by `System` upon task completion.
- **Search, Filters & Custom Sorting:** Full-text search (`ILIKE`), composite filters, and priority-deadline ordering.
- **Analytics:** `/tasks/overdue` and `/tasks/stats` endpoints.
