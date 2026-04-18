import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

import uvicorn
from .routers import auth_router
from .routers import general_user_router
from .routers import geofence_router
logger=logging.getLogger("uvicorn")

app = FastAPI(
    title="Ave Geofencing",
    description="A smart solution for student attendance",
    version="1.0.1",
    contact={
        "name": "Adedara Adeloro",
        "email": "courageadedara@gmail.com"
    }
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
    logger.info(f"Request: {request.method} {request.url.path} ~ {duration:.2f} ms")
    return response


origins = [
    "http://localhost:3000",
    "https://ave-frontend-service.onrender.com",
    "https://ave-po7b.onrender.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Just for Development. Would be changed later.
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)



app.include_router(general_user_router)
app.include_router(auth_router)
app.include_router(geofence_router)
# app.include_router(admin_router)
# # app.include_router(student_router)

if __name__ == "__main__":
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=8000, reload=True)
