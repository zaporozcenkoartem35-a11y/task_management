from datetime import datetime, timezone
import os
from celery.result import AsyncResult
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.celery_app import celery_app
from app.core.exceptions import CSVEmptyError, CSVInvalidFormatError, CannotChangeAssigneeInReviewError, CannotCompleteOverdueError, CannotCompleteWithoutAssigneeError, CannotDeleteActiveTaskError, CannotEditCompletedTaskError, IncorrectDeadlineError, InvalidStatusTransitionError, NotCSVError, TaskNotFoundError, TooManyTasksError
from app.models.task_mod import TaskStatus
from app.schemas.task_pydan import TaskCreateModel, TaskDBResponse, TaskDetailResponse, TaskFilter, TaskStatsResponse, TaskUpdateModel
from app.schemas.user_pydan import UserJWTData
from app.api.deps import allowed_client, get_session
from app.services.task_serv import prepare_to_add_task, prepare_to_bulk_import, prepare_to_change_task, prepare_to_change_task_status, prepare_to_delete_task, prepare_to_get_cur_task, prepare_to_get_overdue_tasks, prepare_to_get_stats, prepare_to_get_tasks
from app.tasks.celery_tasks import export_user_tasks_to_csv_task

router = APIRouter()


@router.post('/tasks', response_model=TaskDBResponse, status_code=status.HTTP_201_CREATED)
async def add_task(task_data: TaskCreateModel,
                   user_data: UserJWTData = Depends(allowed_client),
                   session: AsyncSession = Depends(get_session)):
    try:
        cur_task = await prepare_to_add_task(task_data=task_data,
                                             user_id=user_data.id,
                                             session=session)
    except IncorrectDeadlineError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Deadline cannot be in the past')
    except TooManyTasksError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User has reached the limit of 10 active tasks')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_task


@router.get('/tasks', response_model=list[TaskDBResponse])
async def get_tasks(filter_data: TaskFilter = Depends(),
                    user_data: UserJWTData = Depends(allowed_client),
                    session: AsyncSession = Depends(get_session)):
    try:
        cur_tasks: list[TaskDBResponse] = await prepare_to_get_tasks(filter_data=filter_data,
                                                                     session=session)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_tasks


@router.get('/tasks/overdue', response_model=list[TaskDBResponse])
async def get_overdue_tasks(user_data: UserJWTData = Depends(allowed_client),
                            session: AsyncSession = Depends(get_session)):
    try:
        cur_overdues: list[TaskDBResponse] = await prepare_to_get_overdue_tasks(date_now=datetime.now(timezone.utc),
                                                                                session=session)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_overdues


@router.get('/tasks/stats', response_model=TaskStatsResponse)
async def get_stats(user_data: UserJWTData = Depends(allowed_client),
                    session: AsyncSession = Depends(get_session)):
    try:
        cur_stats: TaskStatsResponse = await prepare_to_get_stats(session=session)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_stats


@router.post('/tasks/bulk-import', status_code=status.HTTP_201_CREATED)
async def add_bulk_import(file_data: UploadFile = File(...),
                          user_data: UserJWTData = Depends(allowed_client),
                          session: AsyncSession = Depends(get_session)):
    try:
        created_count = await prepare_to_bulk_import(file_data=file_data,
                                     user_id=user_data.id,
                                     session=session)
    except NotCSVError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Only .csv files are allowed')
    except CSVInvalidFormatError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid CSV format or missing fields')
    except CSVEmptyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='CSV file contains no valid tasks')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return {
        "status": "success",
        "imported_count": created_count
    }


@router.get('/tasks/{task_id}', response_model=TaskDetailResponse)
async def get_cur_task(task_id: int,
                       user_data: UserJWTData = Depends(allowed_client),
                       session: AsyncSession = Depends(get_session)):
    try:
        cur_task: TaskDetailResponse = await prepare_to_get_cur_task(task_id=task_id,
                                                                     user_id=user_data.id,
                                                                     session=session)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_task


@router.patch('/tasks/{task_id}/status', response_model=TaskDBResponse)
async def change_task_status(task_id: int,
                             new_status: TaskStatus = Body(embed=True),
                             user_data: UserJWTData = Depends(allowed_client),
                             session: AsyncSession = Depends(get_session)):
    try:
        cur_task: TaskDBResponse = await prepare_to_change_task_status(task_id=task_id,
                                                                       new_status=new_status,
                                                                       user_id=user_data.id,
                                                                       session=session)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    except InvalidStatusTransitionError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid status transition')
    except CannotCompleteWithoutAssigneeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot mark task as Done without an assignee')
    except CannotCompleteOverdueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot mark task as Done because deadline has passed')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_task


@router.patch('/tasks/{task_id}', response_model=TaskDBResponse)
async def change_task(task_id: int,
                      update_task_data: TaskUpdateModel,
                      user_data: UserJWTData = Depends(allowed_client),
                      session: AsyncSession = Depends(get_session)):
    try:
        cur_task: TaskDBResponse = await prepare_to_change_task(task_id=task_id,
                                                                update_task_data=update_task_data,
                                                                user_id=user_data.id,
                                                                session=session)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    except CannotEditCompletedTaskError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot edit completed or cancelled task')
    except CannotChangeAssigneeInReviewError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot change assignee for task in Review or Done status')
    except IncorrectDeadlineError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Deadline cannot be in the past')
    except TooManyTasksError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User has reached the limit of 10 active tasks')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_task


@router.delete('/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int,
                      user_data: UserJWTData = Depends(allowed_client),
                      session: AsyncSession = Depends(get_session)):
    try:
        await prepare_to_delete_task(
            task_id=task_id,
            user_id=user_data.id,
            session=session
        )
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    except CannotDeleteActiveTaskError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot delete task in progress or under review')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return {'status': 'success'}


@router.post('/tasks/export', status_code=status.HTTP_202_ACCEPTED)
async def export_tasks(user_data: UserJWTData = Depends(allowed_client)):
    task = export_user_tasks_to_csv_task.delay(user_id=user_data.id)
    return {"task_id": task.id}


@router.get('/tasks/export/{task_id}')
async def get_export_status(task_id: str,
                            user_data: UserJWTData = Depends(allowed_client)):
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state in ["PENDING", "STARTED"]:
        return {
            "task_id": task_id,
            "status": "Processing"
        }
    elif task_result.state == "SUCCESS":
        result_data = task_result.result or {}
        return {
            "task_id": task_id,
            "status": "Done",
            "download_url": result_data.get("download_url")
        }
    else:
        return {
            "task_id": task_id,
            "status": "Failed"
        }


@router.get('/tasks/export/{task_id}/download')
async def download_exported_tasks(task_id: str,
                                  user_data: UserJWTData = Depends(allowed_client)):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state != "SUCCESS":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Export file not found or expired')

    result_data = task_result.result or {}
    file_path = result_data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Export file not found or expired')

    return FileResponse(
        path=file_path,
        filename=f"tasks_export_{task_id}.csv",
        media_type="text/csv"
    )