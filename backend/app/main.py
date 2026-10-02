from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    try:
        from backend.app.services.demo_service import DemoService
        if DemoService.is_demo_mode():
            logger.info("Initializing MAHA-GR in Demo/Offline Mode with representative Maharashtra GRs...")
            DemoService.seed_sample_documents()
    except Exception as e:
        logger.warning(f"Demo initialization notice: {e}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title="MAHA-GR API",
    description=(
        "Multilingual AI-Powered RAG System for Maharashtra Government Resolutions (शासन निर्णय). "
        "Supports query understanding in Marathi, Hindi, and English with strict factual grounding and citations."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
is_wildcard = "*" in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app" if not is_wildcard else None,
    allow_credentials=not is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred in MAHA-GR backend."},
    )


# Mount API v1 router under /api/v1
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to MAHA-GR API: AI for Bharat - Maharashtra Government Resolutions",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=False)

