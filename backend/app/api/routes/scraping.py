import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.deps import get_db, get_json_store
from app.scraping.config_loader import list_available_sites, load_site_config
from app.scraping.config_models import SiteConfig
from app.scraping.engine import ScrapingEngine
from app.scraping.jobs import scraping_jobs
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/sites")
async def get_sites():
    return list_available_sites()


@router.post("/{site_slug}")
async def start_scraping(site_slug: str, background_tasks: BackgroundTasks):
    try:
        config = load_site_config(site_slug)
    except FileNotFoundError:
        raise HTTPException(404, "Site config not found")

    job_id = str(uuid.uuid4())
    scraping_jobs[job_id] = {
        "status": "running",
        "site": site_slug,
        "progress": 0,
        "total_found": 0,
        "error": None,
        "errors": [],
        "duration_seconds": None,
    }

    background_tasks.add_task(_run_scraping_job, job_id, config)

    return {"job_id": job_id, "status": "started", "site": site_slug}


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    job = scraping_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"job_id": job_id, **job}


async def _run_scraping_job(job_id: str, config: SiteConfig):
    engine = ScrapingEngine()
    json_store = get_json_store()
    db = get_db()

    def on_progress(count: int):
        scraping_jobs[job_id]["progress"] = count

    try:
        data, result = await engine.scrape_site(config, on_progress=on_progress)

        if data.companies:
            json_store.save_scraped_data(data)
            await db.upsert_companies(data)

        job_status = "failed" if result.status == "failed" else "completed"

        scraping_jobs[job_id].update(
            {
                "status": job_status,
                "progress": data.total_companies,
                "total_found": data.total_companies,
                "errors": result.errors,
                "duration_seconds": result.duration_seconds,
                "scrape_status": result.status,
            }
        )
    except Exception as exc:
        logger.error(f"Scraping job {job_id} failed: {exc}")
        scraping_jobs[job_id].update({"status": "failed", "error": str(exc)})
