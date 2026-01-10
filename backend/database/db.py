

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.database import models

from settings import Settings

settings = Settings()

engine_path = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}" \
                .format(
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT,
                    db=settings.POSTGRES_DB
                )

engine = create_async_engine(
    engine_path,
    echo=True,
)

new_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with new_session() as session:
        yield session
        
        
async def setup_database():
    async with engine.begin() as conn:
        # Импортируем модели здесь, чтобы зарегистрировать их с метаданными
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)