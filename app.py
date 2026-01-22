import logging
import os
import platform
import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import psutil
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Настройка логирования (исправлено)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(name)

# ========== CONFIGURATION ==========
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global start_time
    start_time = time.time()
    logger.info(f"🚀 Starting {SERVICE_NAME} v{SERVICE_VERSION} on {HOST}:{PORT}")
    yield
    logger.info("👋 Shutting down service...")


app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION, lifespan=lifespan)


# --- Вспомогательные функции ---
def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_human = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    return uptime_seconds, uptime_human


# --- Обработчики ошибок (FastAPI style) ---
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


# --- Эндпоинты ---
@app.get("/")
async def get_info(request: Request):
    # Логируем запрос внутри функции, где доступен объект request
    logger.info(f"Request: {request.method} {request.url.path}")

    uptime_seconds, uptime_human = get_uptime()
    return {
        "service": {"name": SERVICE_NAME, "version": SERVICE_VERSION},
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "cpu_count": psutil.cpu_count(),
        },
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.utcnow().isoformat() + "Z",
        },
    }


@app.get("/health")
async def health_check():
    uptime_seconds, _ = get_uptime()
    return {"status": "healthy", "uptime_seconds": uptime_seconds}


if name == "main":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")