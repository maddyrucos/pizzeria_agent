

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.database import models

load_dotenv()

engine = create_async_engine(
    "postgresql+asyncpg://app:app_password_change_me@localhost:5432/appdb",
    echo=True,
)

new_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    async with new_session() as session:
        yield session
        
        
async def setup_database():
    async with engine.begin() as conn:
        # Импортируем модели здесь, чтобы зарегистрировать их с метаданными
        await conn.run_sync(models.Base.metadata.drop)
        await conn.run_sync(models.Base.metadata.create_all)