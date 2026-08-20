from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_mod import CommentTable


async def add_comment_in_db(comment: CommentTable, session: AsyncSession) -> CommentTable:
    session.add(comment)
    try:
        await session.commit()
        await session.refresh(comment)
        return comment
    except:
        await session.rollback()
        raise


async def get_comments_by_task_id_from_db(task_id: int, session: AsyncSession) -> list[CommentTable]:
    stmt = (
        select(CommentTable)
        .where(CommentTable.task_id == task_id)
        .order_by(CommentTable.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
