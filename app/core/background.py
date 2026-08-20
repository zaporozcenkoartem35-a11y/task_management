import asyncio
from app.db.session import async_session_maker
from app.services.task_serv import prepare_to_auto_cancel_overdue_tasks


async def periodic_overdue_checker():
    while True:
        try:
            async with async_session_maker() as session:
                await prepare_to_auto_cancel_overdue_tasks(session=session)
        except Exception:
            pass

        await asyncio.sleep(60)