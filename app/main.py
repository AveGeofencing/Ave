from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import uvicorn

from .auth.APIKeys import get_api_key

from .routers import *
from .database import sessionmanager, Base
from .auth.AuthRouter import AuthRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    # Startup logic: Create database tables
    async with sessionmanager._engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(
    title="Ave Geofencing",
    description="A smart solution for student attendance",
    version="V1",
    lifespan=lifespan,
)

origins = [
    "http://127.0.0.0:3000",
    "http://localhost:3000",
    "https://ave-main.onrender.com",
    "http://127.0.0.1:3000",
    "https://ave-po7b.onrender.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Just for Development. Would be changed later.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", dependencies=[Depends(get_api_key)])
async def index():
    return "Hello World 1"


app.include_router(GeneralUserRouter)
app.include_router(AuthRouter)
app.include_router(AdminRouter)
app.include_router(StudentRouter)
app.include_router(GeofenceRouter)

if __name__ == "__main__":
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=8000, reload=True)
