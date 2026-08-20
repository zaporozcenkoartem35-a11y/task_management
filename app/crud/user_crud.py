
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_mod import UserTable


async def add_user_in_db(user_data: UserTable, session: AsyncSession):
    session.add(user_data)

    try:
        await session.commit()
        await session.refresh(user_data)
        return user_data
    except:
        await session.rollback()
        raise 


async def check_user_in_db(username: str, session: AsyncSession):
    stmt = (
        select(UserTable)
        .where(UserTable.username == username)  
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()