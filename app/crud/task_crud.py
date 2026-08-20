from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_mod import TaskPriority, TaskStatus, TaskTable
from sqlalchemy import case, func, or_, select, update, delete

from app.schemas.task_pydan import TaskFilter, TaskSortBy

async def add_task_in_db(task: TaskTable, session: AsyncSession) -> TaskTable:
    session.add(task)

    try:
        await session.commit()
        await session.refresh(task)
        return task
    except:
        await session.rollback()
        raise
    

async def check_assignee_tasks_count_in_db(assignee_id: int, session: AsyncSession):
    active_statuses = [
        TaskStatus.BACKLOG.value, 
        TaskStatus.IN_PROGRESS.value, 
        TaskStatus.REVIEW.value
    ]
    
    stmt = (
        select(func.count(TaskTable.id))
        .where(TaskTable.assignee_id == assignee_id,
               TaskTable.status.in_(active_statuses))
    )

    result = await session.execute(stmt)

    return result.scalar_one() < 10


async def get_tasks_from_db(task_filters: TaskFilter,
                               user_id: int,
                               session: AsyncSession):
    stmt = (
        select(TaskTable)
    )

    if task_filters.search:
        search_pattern = f"%{task_filters.search}%"
        stmt = stmt.where(
            or_(
                TaskTable.title.ilike(search_pattern),
                TaskTable.description.ilike(search_pattern)
            )
        )

    if task_filters.status:
        stmt = stmt.where(TaskTable.status == task_filters.status.value)
    if task_filters.priority:
        stmt = stmt.where(TaskTable.priority == task_filters.priority.value)
    if task_filters.assignee_id:
        stmt = stmt.where(TaskTable.assignee_id == task_filters.assignee_id)
    if task_filters.deadline:
        stmt = stmt.where(TaskTable.deadline <= task_filters.deadline)

    priority_order = case(
    {
        TaskPriority.HIGH.value: 1,
        TaskPriority.MEDIUM.value: 2,
        TaskPriority.LOW.value: 3
    },
    value=TaskTable.priority,
    else_=4
    )
    if task_filters.sort_by == TaskSortBy.PRIORITY:
        stmt = stmt.order_by(priority_order.asc(), TaskTable.deadline.asc())
    elif task_filters.sort_by == TaskSortBy.DEADLINE:
        stmt = stmt.order_by(TaskTable.deadline.asc())
    elif task_filters.sort_by == TaskSortBy.CREATED_AT:
        stmt = stmt.order_by(TaskTable.created_at.desc())

    offset = (task_filters.page - 1) * task_filters.limit
    stmt = stmt.offset(offset).limit(task_filters.limit)

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_task_from_db(task_id: int, session: AsyncSession):
    stmt = (
        select(TaskTable)
        .where(TaskTable.id == task_id)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def change_task_status_in_db(task_id: int,
                                   new_status: TaskStatus,
                                   session: AsyncSession):
    stmt = (
        update(TaskTable)
        .where(TaskTable.id == task_id)
        .values(status=new_status)
    ).returning(TaskTable)

    result = await session.execute(stmt)
    try:
        await session.commit()
        return result.scalar_one_or_none()
    except:
        await session.rollback()
        raise 


async def update_task_in_db(task_id: int,
                            update_data: dict,
                            session: AsyncSession) -> TaskTable:
    stmt = (
        update(TaskTable)
        .where(TaskTable.id == task_id)
        .values(**update_data)
    ).returning(TaskTable)

    result = await session.execute(stmt)
    try:
        await session.commit()
        return result.scalar_one_or_none()
    except:
        await session.rollback()
        raise 


async def delete_task_from_db(task_id: int, session: AsyncSession) -> None:
    stmt = (
        delete(TaskTable).where(TaskTable.id == task_id)
        )
    
    result = await session.execute(stmt)
    try:
        await session.commit()
        return result.rowcount > 0
    except:
        await session.rollback()
        raise
    