from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import TaskNotFoundError
from app.crud.com_crud import add_comment_in_db, get_comments_by_task_id_from_db
from app.crud.task_crud import get_task_from_db
from app.models.task_mod import CommentTable
from app.schemas.comment_pydan import CommentCreateModel, CommentResponse


async def prepare_to_add_comment(task_id: int,
                                  comment_data: CommentCreateModel,
                                  user_id: int,
                                  session: AsyncSession):
    cur_task = await get_task_from_db(task_id=task_id,
                                      session=session)
    if not cur_task:
        raise TaskNotFoundError

    cur_comment = await add_comment_in_db(comment=CommentTable(task_id=task_id,
                                                               author_id=user_id,
                                                               content=comment_data.content),
                                          session=session)

    return CommentResponse.model_validate(cur_comment)


async def prepare_to_get_comments(task_id: int,
                                   session: AsyncSession):
    cur_task = await get_task_from_db(task_id=task_id,
                                      session=session)
    if not cur_task:
        raise TaskNotFoundError

    comments = await get_comments_by_task_id_from_db(task_id=task_id,
                                                     session=session)

    return [CommentResponse.model_validate(item) for item in comments]