
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_mod import UserRole, UserTable



async def get_system_user_id(session: AsyncSession) -> int:
    stmt = (
        select(UserTable.id)
        .where(UserTable.username == "System")
        )
    result = await session.execute(stmt)
    system_id = result.scalar_one_or_none()
    

    if system_id is None:
        system_user = UserTable(
            username="System",
            hashed_password="SYSTEM_BOT_ACCOUNT_NO_LOGIN",
            role=UserRole.ADMIN.value,
            created_at=datetime.now(timezone.utc)
        )
        session.add(system_user)
        await session.flush()
        system_id = system_user.id
        
    return system_id


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