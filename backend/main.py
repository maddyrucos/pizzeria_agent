from fastapi import FastAPI, Depends
from backend.api.router import api
from backend.agent.router import agent

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import db, models

from contextlib import asynccontextmanager
from typing import Annotated



session_dep = Annotated[AsyncSession, Depends(db.get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup database
    
    await db.setup_database()
    yield
    # Shutdown: any cleanup can be done here

app = FastAPI(lifespan=lifespan)
app.include_router(api)
app.include_router(agent)


    
@app.post("/setup_db")
async def setup_database():
    try:
        async with db.engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)
        return {"status": "Database setup completed successfully."}
    except Exception as e:
        return {"status": "Database setup failed.", "error": str(e)}
    
