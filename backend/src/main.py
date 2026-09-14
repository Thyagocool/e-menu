import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from src.config import get_settings
from src.infra.database import SessionLocal
from src.infra.errors import DomainError
from src.modules.cart.routes import router as cart_router
from src.modules.category.routes import router as category_router
from src.modules.product.routes import router as product_router
from src.modules.public.routes import router as public_router
from src.modules.restaurant.routes import router as restaurant_router
from src.modules.upload.routes import router as upload_router
from src.modules.whatsapp.routes import router as whatsapp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(restaurant_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(upload_router)
app.include_router(public_router)
app.include_router(whatsapp_router)
app.include_router(cart_router)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health() -> dict:
    db_status = "up"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health check must not 500
        logger.exception("Health check DB failure")
        db_status = "down"
    return {"status": "ok" if db_status == "up" else "degraded", "database": db_status}