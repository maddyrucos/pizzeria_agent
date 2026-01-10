from fastapi import FastAPI, Depends
from backend.api.router import api
from backend.agent.router import agent, limiter
from backend.auth.router import router as auth_router

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import db, models

from contextlib import asynccontextmanager
from typing import Annotated

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup database
    
    await db.setup_database()
    yield
    # Shutdown: any cleanup can be done here

app = FastAPI()
app.include_router(api)

app.include_router(agent)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)

    
@app.post("/setup_db")
async def setup_database():
    try:
        async with db.engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)
        return {"status": "Database setup completed successfully."}
    except Exception as e:
        return {"status": "Database setup failed.", "error": str(e)}
    
