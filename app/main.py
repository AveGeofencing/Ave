import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

import uvicorn
from starlette.responses import JSONResponse

from .routers import auth_router
from .routers import general_user_router
from .routers import geofence_router
from .routers.rekognition import router as rekognition_router

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

@app.middleware("http")
async def measure_response_time(request: Request, call_next):
    start_time = time.perf_counter()  # Start timer
    response = await call_next(request)  # Process request
    end_time = time.perf_counter()  # End timer
    duration = (end_time - start_time) * 1000  # Convert to milliseconds
    logger.info(f"Request: {request.method} {request.url.path} ~ {duration:.2f} ms")
    return response

@app.exception_handler(Exception)
async def custom_exception_handler(_: Request, exc: Exception):
    logger.error(f"{str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred. Check server"},
    )

@app.exception_handler(ValueError)
async def custom_exception_handler(_: Request, exc: Exception):
    logger.error(f"{str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )



origins = [
    "http://localhost:3000",
    "https://ave-frontend-service.onrender.com",
    "http://172.20.10.3:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)



app.include_router(general_user_router)
app.include_router(auth_router)
app.include_router(geofence_router)
app.include_router(rekognition_router)
# app.include_router(admin_router)
# # app.include_router(student_router)

if __name__ == "__main__":
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=8000, reload=True)
