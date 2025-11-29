"""
Ingestion Control Endpoints
Manual triggers and status for data ingestion
"""

from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.ingestion.eia_collector import EIACollector
from app.ingestion.iso_collector import ERCOTCollector
from app.ingestion.scheduler import ingestion_scheduler

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/trigger/eia")
async def trigger_eia_collection(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger EIA data collection
    """
    async def run_collection():
        collector = EIACollector(db)
        async with collector:
            await collector.ensure_regions_exist()
            return await collector.run()

    background_tasks.add_task(run_collection)

    return {
        "status": "triggered",
        "source": "EIA",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/trigger/iso/{iso_name}")
async def trigger_iso_collection(
    iso_name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger ISO data collection
    """
    iso_collectors = {
        "ERCOT": ERCOTCollector,
    }

    collector_class = iso_collectors.get(iso_name.upper())
    if not collector_class:
        return {
            "status": "error",
            "message": f"Unknown ISO: {iso_name}. Available: {list(iso_collectors.keys())}",
        }

    async def run_collection():
        collector = collector_class(db)
        async with collector:
            return await collector.run()

    background_tasks.add_task(run_collection)

    return {
        "status": "triggered",
        "source": iso_name.upper(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/trigger/all")
async def trigger_all_collection(
    background_tasks: BackgroundTasks,
):
    """
    Trigger all data collectors
    """
    background_tasks.add_task(ingestion_scheduler.run_once)

    return {
        "status": "triggered",
        "sources": ["EIA", "ERCOT"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/status")
async def get_ingestion_status():
    """
    Get current ingestion scheduler status
    """
    return {
        "scheduler_running": ingestion_scheduler.is_running,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/scheduler/start")
async def start_scheduler():
    """
    Start the ingestion scheduler
    """
    ingestion_scheduler.start()
    return {
        "status": "started",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/scheduler/stop")
async def stop_scheduler():
    """
    Stop the ingestion scheduler
    """
    ingestion_scheduler.stop()
    return {
        "status": "stopped",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
