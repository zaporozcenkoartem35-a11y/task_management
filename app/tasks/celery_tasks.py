import asyncio
import csv
import os

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.crud.task_crud import get_all_user_tasks_for_export
from app.services.task_serv import prepare_to_auto_cancel_overdue_tasks

celery_engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
celery_session_maker = async_sessionmaker(
    bind=celery_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def generate_tasks_csv_file(user_id: int, task_id: str, session) -> str:
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/export_{user_id}_{task_id}.csv"

    tasks = await get_all_user_tasks_for_export(user_id=user_id, session=session)

    with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id", "title", "description", "status", "priority", "deadline", "created_at"])
        for t in tasks:
            writer.writerow([
                t.id,
                t.title,
                t.description or "",
                t.status,
                t.priority,
                t.deadline.isoformat() if t.deadline else "",
                t.created_at.isoformat() if t.created_at else ""
            ])
    return file_path


@celery_app.task(name="auto_cancel_overdue_tasks_task")
def auto_cancel_overdue_tasks_task():
    async def _run():
        async with celery_session_maker() as session: 
            cancelled_count = await prepare_to_auto_cancel_overdue_tasks(session=session)
            return cancelled_count

    return asyncio.run(_run())


@celery_app.task(name="export_user_tasks_to_csv_task", bind=True)
def export_user_tasks_to_csv_task(self, user_id: int):
    task_id = self.request.id
    async def _run():
        async with celery_session_maker() as session:
            return await generate_tasks_csv_file(user_id, task_id, session)
        
    file_path = asyncio.run(_run())
    
    return {
        "file_path": file_path,
        "download_url": f"/api/v1/tasks/export/{task_id}/download"
    }