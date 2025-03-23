import time
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

import uvicorn

from .auth.APIKeys import get_api_key

from .routers import *
from .auth.AuthRouter import AuthRouter

logger=logging.getLogger("uvicorn")

app = FastAPI(
    title="Ave Geofencing",
    description="A smart solution for student attendance",
    version="V1",
)

# @app.exception_handler(UserServiceException)
# async def handle_user_service_error(request, exc: UserServiceException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"error": exc.message},
#         headers={"X-Error-Type": "UserServiceException"},
#     )

# @app.exception_handler(GeofenceServiceException)
# async def hanlde_geofence_service_error(request, exc: GeofenceServiceException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"error": exc.message},
#         headers={"X-Error-Type": "GeofenceServiceException"},
#     )


@app.middleware("http")
async def measure_response_time(request: Request, call_next):
    start_time = time.perf_counter()  # Start timer
    response = await call_next(request)  # Process request
    end_time = time.perf_counter()  # End timer
    duration = (end_time - start_time) * 1000  # Convert to milliseconds
    logger.info(f"Request: {request.method} {request.url} - {duration:.2f} ms")
    return response


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
