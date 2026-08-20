# Task Management API

REST API for managing tasks and workflows built with FastAPI, PostgreSQL, and SQLAlchemy (Async).

## Tech Stack

- **FastAPI** (Python 3.13)
- **PostgreSQL 16** + **SQLAlchemy 2.0 (asyncpg)**
- **Alembic** (migrations)
- **Pydantic v2**
- **JWT Auth** (access & refresh tokens, Argon2 password hashing)
- **Docker Compose**
- **Pytest** (pytest-asyncio + HTTPX)

## Quick Start (Docker)

Start the entire application and database with migrations applied automatically:

```bash
docker compose up --build
```

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/health](http://localhost:8000/health)

## Local Setup

1. Start PostgreSQL:
   ```bash
   docker compose up -d db
   ```
2. Apply migrations:
   ```bash
   alembic upgrade head
   ```
3. Run dev server:
   ```bash
   uvicorn main:app --reload
   ```

## Running Tests

```bash
pytest -v
```

## Features

- **Task CRUD:** Full task management with pagination.
- **Search & Filters:** Search by title/description (`ILIKE`), filter by status, priority, assignee, deadline.
- **Custom Sorting:** Ordered by priority (`High` → `Medium` → `Low`) and closest deadline.
- **State Machine:** Enforced status transitions (`Backlog` → `In Progress` → `Review` → `Done` / `Cancelled`) with business validation rules.
- **Comments:** Threaded comments support per task.
- **Analytics:** `/tasks/overdue` and `/tasks/stats` endpoints.
- **Background Worker:** Automated periodic cancellation of overdue tasks.
