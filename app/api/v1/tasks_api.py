from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import CannotChangeAssigneeInReviewError, CannotCompleteOverdueError, CannotCompleteWithoutAssigneeError, CannotDeleteActiveTaskError, CannotEditCompletedTaskError, IncorrectDeadlineError, InvalidStatusTransitionError, TaskNotFoundError, TooManyTasksError
from app.models.task_mod import TaskStatus
from app.schemas.task_pydan import TaskCreateModel, TaskDBResponse, TaskDetailResponse, TaskFilter, TaskUpdateModel
from app.schemas.user_pydan import UserJWTData
from app.api.deps import allowed_client, get_session
from app.services.task_serv import prepare_to_add_task, prepare_to_change_task, prepare_to_change_task_status, prepare_to_delete_task, prepare_to_get_cur_task, prepare_to_get_tasks

router= APIRouter()


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
async def get_tasks(task_filters: TaskFilter = Depends(),
                    user_data: UserJWTData = Depends(allowed_client),
                    session: AsyncSession = Depends(get_session)):
    try:
        cur_tasks: list[TaskDBResponse] = await prepare_to_get_tasks(task_filters=task_filters,
                                                                     user_id=user_data.id,
                                                                     session=session)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_tasks


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