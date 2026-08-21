import csv
from datetime import datetime, timezone
import io
import os

from fastapi import UploadFile

from app.core.exceptions import CSVEmptyError, CSVInvalidFormatError, CannotChangeAssigneeInReviewError, CannotCompleteOverdueError, CannotCompleteWithoutAssigneeError, CannotDeleteActiveTaskError, CannotEditCompletedTaskError, IncorrectDeadlineError, InvalidStatusTransitionError, NotCSVError, TaskNotFoundError, TooManyTasksError
from app.crud.com_crud import get_comments_by_task_id_from_db
from app.crud.task_crud import add_task_in_db, auto_cancel_overdue_tasks_in_db, bulk_create_tasks_in_db, change_task_status_in_db, check_assignee_tasks_count_in_db, delete_task_from_db, get_overdue_tasks_from_db, get_stats_from_db, get_task_from_db, get_tasks_from_db, update_task_in_db
from app.crud.user_crud import get_system_user_id
from app.models.task_mod import CommentTable, TaskPriority, TaskStatus, TaskTable
from app.schemas.comment_pydan import CommentCreateModel, CommentResponse
from app.schemas.task_pydan import TaskCreateModel, TaskDBResponse, TaskDetailResponse, TaskFilter, TaskStatsResponse, TaskUpdateModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.com_serv import prepare_to_add_comment
from app.services.quote_serv import fetch_random_quote


ALLOWED_TRANSITIONS = {
    TaskStatus.BACKLOG.value: [TaskStatus.IN_PROGRESS.value, TaskStatus.CANCELLED.value],
    TaskStatus.IN_PROGRESS.value: [TaskStatus.REVIEW.value, TaskStatus.CANCELLED.value],
    TaskStatus.REVIEW.value: [TaskStatus.DONE.value],
    TaskStatus.DONE.value: [],
    TaskStatus.CANCELLED.value: [],
}


async def prepare_to_add_task(task_data: TaskCreateModel,
                              user_id: int,
                              session: AsyncSession):
    if task_data.deadline.tzinfo is None:
        task_data.deadline = task_data.deadline.replace(tzinfo=timezone.utc)

    if task_data.deadline < datetime.now(timezone.utc):
        raise IncorrectDeadlineError

    if task_data.assignee_id:
        assignee_tasks_count = await check_assignee_tasks_count_in_db(assignee_id=task_data.assignee_id,
                                                                      session=session)
        if assignee_tasks_count >= 10:
            raise TooManyTasksError

    cur_task: TaskTable = await add_task_in_db(task=TaskTable(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status.value,
        priority=task_data.priority.value,
        author_id=user_id,
        assignee_id=task_data.assignee_id,
        deadline=task_data.deadline
    ), session=session)

    return TaskDBResponse.model_validate(cur_task)


async def prepare_to_get_tasks(filter_data: TaskFilter,
                               session: AsyncSession):
    tasks_from_db: list[TaskTable] = await get_tasks_from_db(filter_data=filter_data,
                                                             session=session)
    return [TaskDBResponse.model_validate(item) for item in tasks_from_db]


async def prepare_to_change_task_status(task_id: int,
                                        new_status: TaskStatus,
                                        user_id: int,
                                        session: AsyncSession):
    cur_task: TaskDBResponse = await get_task_from_db(task_id=task_id,
                                                      session=session)
    if not cur_task:
        raise TaskNotFoundError

    if new_status.value not in ALLOWED_TRANSITIONS[cur_task.status]:
        raise InvalidStatusTransitionError

    if new_status.value == TaskStatus.DONE.value:
        if not cur_task.assignee_id:
            raise CannotCompleteWithoutAssigneeError
        if cur_task.deadline < datetime.now(timezone.utc):
            raise CannotCompleteOverdueError

    new_cur_task: TaskTable = await change_task_status_in_db(task_id=task_id,
                                                  new_status=new_status,
                                                  session=session)
    if not new_cur_task:
        raise TaskNotFoundError

    if new_status == TaskStatus.DONE:
        try:
            quote_text = await fetch_random_quote()
            system_id: int = await get_system_user_id(session=session)
            await prepare_to_add_comment(
                task_id=new_cur_task.id,
                comment_data=CommentCreateModel(content=quote_text),
                user_id=system_id,
                session=session
            )
        except Exception as e:
            print(f"Failed to add system quote: {e}")

    return TaskDBResponse.model_validate(new_cur_task)


async def prepare_to_change_task(task_id: int,
                                 update_task_data: TaskUpdateModel,
                                 user_id: int,
                                 session: AsyncSession):
    cur_task: TaskDBResponse = await get_task_from_db(task_id=task_id,
                                                          session=session)
    if not cur_task:
        raise TaskNotFoundError

    if cur_task.status in (TaskStatus.DONE.value, TaskStatus.CANCELLED.value):
        raise CannotEditCompletedTaskError

    if update_task_data.deadline is not None:
        if update_task_data.deadline.tzinfo is None:
            update_task_data.deadline = update_task_data.deadline.replace(tzinfo=timezone.utc)
        if update_task_data.deadline < datetime.now(timezone.utc):
            raise IncorrectDeadlineError

    if update_task_data.assignee_id is not None:
        if cur_task.status in (TaskStatus.REVIEW.value, TaskStatus.DONE.value):
            raise CannotChangeAssigneeInReviewError

        if update_task_data.assignee_id != cur_task.assignee_id:
            assignee_tasks_count = await check_assignee_tasks_count_in_db(assignee_id=update_task_data.assignee_id,
                                                                        session=session)
            if assignee_tasks_count >= 10:
                raise TooManyTasksError

    dict_update_task_data = update_task_data.model_dump(exclude_unset=True)

    if 'priority' in dict_update_task_data and dict_update_task_data['priority'] is not None:
        dict_update_task_data['priority'] = dict_update_task_data['priority'].value

    new_task = await update_task_in_db(task_id=task_id,
                                       update_task_data=dict_update_task_data,
                                       session=session)

    return TaskDBResponse.model_validate(new_task)


async def prepare_to_delete_task(task_id: int,
                                 user_id: int,
                                 session: AsyncSession):
    cur_task: TaskDBResponse = await get_task_from_db(task_id=task_id,
                                                      session=session)
    if not cur_task:
        raise TaskNotFoundError

    if cur_task.status in (TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value):
        raise CannotDeleteActiveTaskError

    await delete_task_from_db(task_id=task_id,
                              session=session)


async def prepare_to_get_cur_task(task_id: int,
                                  user_id: int,
                                  session: AsyncSession):
    cur_task = await get_task_from_db(task_id=task_id,
                                      session=session)
    if not cur_task:
        raise TaskNotFoundError

    cur_comments = await get_comments_by_task_id_from_db(task_id=task_id,
                                                         session=session)

    return TaskDetailResponse(
        id=cur_task.id,
        title=cur_task.title,
        description=cur_task.description,
        status=cur_task.status,
        priority=cur_task.priority,
        author_id=cur_task.author_id,
        assignee_id=cur_task.assignee_id,
        deadline=cur_task.deadline,
        created_at=cur_task.created_at,
        updated_at=cur_task.updated_at,
        comments=[CommentResponse.model_validate(c) for c in cur_comments]
    )


async def prepare_to_get_overdue_tasks(date_now: datetime,
                                       session: AsyncSession):
    cur_overdues: list[TaskTable] = await get_overdue_tasks_from_db(date_now=date_now,
                                                                    session=session)

    return [TaskDBResponse.model_validate(item) for item in cur_overdues]


async def prepare_to_get_stats(session: AsyncSession):
    cur_stats: dict = await get_stats_from_db(date_now=datetime.now(timezone.utc),
                                              session=session)

    return TaskStatsResponse.model_validate(cur_stats)


async def prepare_to_auto_cancel_overdue_tasks(session: AsyncSession) -> int:
    result: int = await auto_cancel_overdue_tasks_in_db(date_now=datetime.now(timezone.utc),
                                                 session=session)
    return result


async def prepare_to_bulk_import(file_data: UploadFile,
                                 user_id: int,
                                 session: AsyncSession):
    if not file_data.filename or not file_data.filename.endswith('.csv'):
        raise NotCSVError

    content = await file_data.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise CSVInvalidFormatError
    
    reader = csv.DictReader(io.StringIO(csv_text))
    tasks_data = []

    for row in reader:
        title = row.get("title", "").strip()
        raw_deadline = row.get("deadline", "").strip()
        if not title or not raw_deadline:
            raise CSVInvalidFormatError
        try:
            deadline_dt = datetime.fromisoformat(raw_deadline)
        except (ValueError, TypeError):
            raise CSVInvalidFormatError()
        priority = row.get("priority", TaskPriority.MEDIUM.value).strip()
        if priority not in [p.value for p in TaskPriority]:
            priority = TaskPriority.MEDIUM.value
        tasks_data.append({
            "title": title,
            "description": row.get("description", "").strip() or None,
            "status": TaskStatus.BACKLOG.value,
            "priority": priority,
            "author_id": user_id,
            "assignee_id": None,
            "deadline": deadline_dt
        })

    if not tasks_data:
        raise CSVEmptyError
    
    count_tasks: int = await bulk_create_tasks_in_db(task_data=tasks_data,
                                                    session=session)
    if not count_tasks:
        raise CSVEmptyError

    return count_tasks