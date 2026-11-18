import logging
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .routers import auth_router, general_user_router, geofence_router
from .routers.rekognition import router as rekognition_router
from .settings import APP_SETTINGS

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Ave Geofencing",
    description="A smart solution for student attendance",
    version="1.0.1",
    contact={"name": "Adedara Adeloro", "email": "courageadedara@gmail.com"},
)


@app.middleware("http")
async def measure_response_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start_time) * 1000
    logger.info("Request: %s %s ~ %.2f ms", request.method, request.url.path, duration)
    return response


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    logger.error("Value error: %s", exc)
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred. Check server"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=APP_SETTINGS.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "ave-api", "version": app.version}


app.include_router(general_user_router)
app.include_router(auth_router)
app.include_router(geofence_router)
app.include_router(rekognition_router)

if __name__ == "__main__":
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=8000, reload=True)
