from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_db
from app.api.routes import ai, companies, scraping
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TechPark Hunter API starting...")
    db = get_db()
    await db.init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")


app = FastAPI(title="TechPark Hunter API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(scraping.router, prefix="/api/scrape", tags=["scraping"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])


@app.get("/")
async def root():
    return {"status": "running", "app": "TechPark Hunter"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
