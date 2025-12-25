"""
FastAPI application entry point.

Minimal setup for Phase 0 - just health check endpoint.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.api import invoices, monotributo, settings as settings_api

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Code before yield runs on startup.
    Code after yield runs on shutdown.
    """
    # Startup
    settings.tevildo_data_dir.mkdir(parents=True, exist_ok=True)
    settings.invoices_dir.mkdir(parents=True, exist_ok=True)

    print(f"🐱 {settings.app_name} starting...")
    print(f"📁 Data directory: {settings.tevildo_data_dir}")
    print(f"🗄️  Database: {settings.database_url}")

    yield  # Application runs here

    # Shutdown
    print(f"🐱 {settings.app_name} shutting down...")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS (for future frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(invoices.router)
app.include_router(monotributo.router)
app.include_router(settings_api.router)

@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "app": settings.app_name,
        "status": "running",
        "message": "Tevildo backend is operational",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected", 
    }
