import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fubble.api import customers, events, invoices, plans, usage
from fubble.database.connection import init_db
from fubble.config import settings


# Initialize the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Flexible Usage Based Billing API",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(customers.router)
app.include_router(events.router)
app.include_router(invoices.router)
app.include_router(plans.router)
app.include_router(usage.router)


@app.on_event("startup")
async def startup_event():
    """Initialize the database on application startup."""
    init_db()


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "If you're reading this, the server is running!",
    }


if __name__ == "__main__":
    uvicorn.run("fubble.app:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
