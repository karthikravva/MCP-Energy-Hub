"""
Ingestion Scheduler
Manages periodic data collection jobs
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db.session import async_session_maker
from app.ingestion.eia_collector import EIACollector
from app.ingestion.iso_collector import ERCOTCollector, CAISOCollector, PJMCollector

logger = logging.getLogger(__name__)
settings = get_settings()


class IngestionScheduler:
    """
    Manages scheduled data ingestion jobs
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def run_eia_collection(self):
        """Run EIA data collection"""
        logger.info("Starting scheduled EIA collection")

        async with async_session_maker() as session:
            collector = EIACollector(session)
            async with collector:
                # Ensure regions exist first
                await collector.ensure_regions_exist()
                # Run collection
                result = await collector.run()
                logger.info(f"EIA collection result: {result}")

    async def run_iso_collection(self):
        """Run ISO real-time data collection"""
        logger.info("Starting scheduled ISO collection")

        collectors = [ERCOTCollector]  # Add more as implemented

        for collector_class in collectors:
            async with async_session_maker() as session:
                collector = collector_class(session)
                async with collector:
                    result = await collector.run()
                    logger.info(
                        f"{collector.source_name} collection result: {result}")

    def start(self):
        """Start the scheduler with configured jobs"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # EIA collection - every hour
        self.scheduler.add_job(
            self.run_eia_collection,
            trigger=IntervalTrigger(hours=1),
            id="eia_hourly",
            name="EIA Hourly Collection",
            replace_existing=True,
        )

        # ISO collection - every 5 minutes
        self.scheduler.add_job(
            self.run_iso_collection,
            trigger=IntervalTrigger(
                minutes=settings.ingestion_interval_minutes),
            id="iso_realtime",
            name="ISO Real-time Collection",
            replace_existing=True,
        )

        # Batch jobs - daily at 2 AM
        self.scheduler.add_job(
            self.run_batch_jobs,
            trigger=CronTrigger(hour=settings.batch_ingestion_hour),
            id="batch_daily",
            name="Daily Batch Jobs",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("Ingestion scheduler started")

    async def run_batch_jobs(self):
        """Run daily batch jobs (DOE, LBNL data updates)"""
        logger.info("Starting daily batch jobs")
        # Placeholder for batch data updates
        pass

    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Ingestion scheduler stopped")

    async def run_once(self):
        """Run all collectors once (for testing/manual trigger)"""
        await self.run_eia_collection()
        await self.run_iso_collection()


# Global scheduler instance
ingestion_scheduler = IngestionScheduler()
