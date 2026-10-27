
from fastapi import FastAPI

from app.api.transactions import router as transactions_router
from app.core.config import settings

from app.api.analytics import router as analytics_router
from app.api.fraud import router as fraud_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Aegis API",
        "version": settings.app_version,
    }


app.include_router(transactions_router)

app.include_router(analytics_router)

app.include_router(fraud_router)