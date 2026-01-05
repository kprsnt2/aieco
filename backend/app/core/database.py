"""AIEco - Database Connection"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = None
AsyncSessionLocal = None

async def init_db():
    global engine, AsyncSessionLocal
    engine = create_async_engine(settings.database_url, echo=settings.debug)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def close_db():
    if engine:
        await engine.dispose()

@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except:
        return False
