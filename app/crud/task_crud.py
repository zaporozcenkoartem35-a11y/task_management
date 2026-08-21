from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_mod import TaskPriority, TaskStatus, TaskTable
from sqlalchemy import case, func, or_, select, update, delete, insert

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


async def get_overdue_tasks_from_db(date_now: datetime,
                                    session: AsyncSession):
    stmt = (
        select(TaskTable)
        .where(
            TaskTable.deadline < date_now,
            TaskTable.status.not_in([TaskStatus.DONE.value, TaskStatus.CANCELLED.value])
        )
        .order_by(TaskTable.deadline.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_stats_from_db(date_now: datetime,
                             session: AsyncSession):
    
    total_stmt = select(func.count(TaskTable.id))
    total_res = await session.execute(total_stmt)
    total_tasks = total_res.scalar_one()


    status_stmt = select(TaskTable.status, func.count(TaskTable.id)).group_by(TaskTable.status)
    status_res = await session.execute(status_stmt)
    by_status = {status.value: 0 for status in TaskStatus}
    for status_name, count in status_res.all():
        by_status[status_name] = count

    
    priority_stmt = select(TaskTable.priority, func.count(TaskTable.id)).group_by(TaskTable.priority)
    priority_res = await session.execute(priority_stmt)
    by_priority = {priority.value: 0 for priority in TaskPriority}
    for priority_name, count in priority_res.all():
        by_priority[priority_name] = count

    
    overdue_stmt = (
        select(func.count(TaskTable.id))
        .where(
            TaskTable.deadline < date_now,
            TaskTable.status.not_in([TaskStatus.DONE.value, TaskStatus.CANCELLED.value])
        )
    )
    overdue_res = await session.execute(overdue_stmt)
    overdue_tasks = overdue_res.scalar_one()

    
    active_statuses = [TaskStatus.BACKLOG.value, TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value]
    active_stmt = (
        select(func.count(TaskTable.id))
        .where(TaskTable.status.in_(active_statuses))
    )
    active_res = await session.execute(active_stmt)
    active_tasks = active_res.scalar_one()

    
    return {
        "total_tasks": total_tasks,
        "by_status": by_status,
        "by_priority": by_priority,
        "overdue_tasks": overdue_tasks,
        "active_tasks": active_tasks
    }


async def auto_cancel_overdue_tasks_in_db(date_now: datetime,
                                          session: AsyncSession) -> int:
    stmt = (
        update(TaskTable)
        .where(
            TaskTable.deadline < date_now,
            TaskTable.status.not_in([TaskStatus.DONE.value, TaskStatus.CANCELLED.value])
        )
        .values(status=TaskStatus.CANCELLED.value)
    )
    result = await session.execute(stmt)
    try:
        await session.commit()
        return result.rowcount
    except:
        await session.rollback()
        raise


async def bulk_create_tasks_in_db(task_data: list[dict],
                                  session: AsyncSession):
    if not task_data:
        return 0

    stmt = (
        insert(TaskTable)
        .values(task_data)
    )

    result = await session.execute(stmt)

    try:
        await session.commit()
        return result.rowcount
    except:
        await session.rollback()
        raise