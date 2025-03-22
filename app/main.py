from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import uvicorn

from .auth.APIKeys import get_api_key

from .routers import *
from .auth.AuthRouter import AuthRouter



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
