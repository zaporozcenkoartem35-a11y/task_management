# Interview Copilot

AI-assisted technical interview copilot backend.

## Quick Start

1. Start Postgres database:
   ```bash
   docker compose up -d
   ```

2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

3. Run FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
