#!/usr/bin/env python3
"""
MCP Energy Hub - Startup Script
Initializes database and loads initial data for HuggingFace deployment
"""

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup():
    """Initialize the application"""
    from app.db.session import init_db, async_session_maker
    from app.ingestion.eia_collector import EIACollector
    from app.models.database import DataCenterDB
    from sqlalchemy import select, func

    logger.info("🚀 Starting MCP Energy Hub initialization...")

    # Initialize database
    logger.info("📦 Initializing database...")
    await init_db()
    logger.info("✅ Database initialized")

    # Ensure regions exist and load initial data
    logger.info("🌍 Loading grid regions...")
    async with async_session_maker() as session:
        collector = EIACollector(session)
        await collector.ensure_regions_exist()
        logger.info("✅ Grid regions loaded")

        # Try to fetch initial EIA data
        logger.info("⚡ Fetching initial EIA data (this may take a moment)...")
        try:
            count = await collector.run()
            logger.info(f"✅ Loaded {count} grid metrics records")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch EIA data: {e}")
            logger.info("   (Data will be fetched on first API call)")

    # Seed data centers if empty
    async with async_session_maker() as session:
        result = await session.execute(select(func.count()).select_from(DataCenterDB))
        dc_count = result.scalar()
        if dc_count == 0:
            logger.info("🏢 Seeding data centers...")
            from seed_datacenters import DATA_CENTERS
            for dc_data in DATA_CENTERS:
                dc = DataCenterDB(**dc_data)
                session.add(dc)
            await session.commit()
            logger.info(f"✅ Seeded {len(DATA_CENTERS)} data centers")
        else:
            logger.info(f"✅ {dc_count} data centers already in database")

    logger.info("🎉 MCP Energy Hub ready!")
    logger.info("   📊 API Docs: /docs")
    logger.info("   🎨 Gradio UI: /ui")
    logger.info("   🔧 MCP Tools: /mcp/tools")


if __name__ == "__main__":
    asyncio.run(startup())
