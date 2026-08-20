from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import allowed_client, get_session
from app.core.exceptions import TaskNotFoundError
from app.schemas.comment_pydan import CommentCreateModel, CommentResponse
from app.schemas.user_pydan import UserJWTData
from app.services.com_serv import prepare_to_add_comment, prepare_to_get_comments

router = APIRouter()


@router.post('/tasks/{task_id}/comments', response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(task_id: int,
                      comment_data: CommentCreateModel,
                      user_data: UserJWTData = Depends(allowed_client),
                      session: AsyncSession = Depends(get_session)):
    try:
        cur_comment: CommentResponse = await prepare_to_add_comment(task_id=task_id,
                                                                    comment_data=comment_data,
                                                                    user_id=user_data.id,
                                                                    session=session)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return cur_comment


@router.get('/tasks/{task_id}/comments', response_model=list[CommentResponse])
async def get_comments(task_id: int,
                       user_data: UserJWTData = Depends(allowed_client),
                       session: AsyncSession = Depends(get_session)):
    try:
        comments: list[CommentResponse] = await prepare_to_get_comments(task_id=task_id,
                                                                        session=session)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return comments