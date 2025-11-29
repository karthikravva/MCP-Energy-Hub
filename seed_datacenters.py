"""
Seed data centers into the database
"""

import asyncio
from app.db.session import async_session_maker, init_db
from app.models.database import DataCenterDB
from sqlalchemy import select


# Sample data centers based on real facilities
DATA_CENTERS = [
    # ERCOT (Texas)
    {"dc_id": "aws-us-texas-1", "name": "AWS US Texas 1", "operator": "AWS", "region_id": "ERCOT",
        "latitude": 32.78, "longitude": -96.80, "max_capacity_mw": 150, "avg_pue": 1.2, "is_ai_focused": True, "primary_grid_connection": "ERCOT-345kV"},
    {"dc_id": "google-texas-1", "name": "Google Midlothian", "operator": "Google", "region_id": "ERCOT",
        "latitude": 32.48, "longitude": -96.99, "max_capacity_mw": 200, "avg_pue": 1.1, "is_ai_focused": True, "primary_grid_connection": "ERCOT-345kV"},
    {"dc_id": "meta-fort-worth", "name": "Meta Fort Worth", "operator": "Meta", "region_id": "ERCOT",
        "latitude": 32.75, "longitude": -97.33, "max_capacity_mw": 180, "avg_pue": 1.15, "is_ai_focused": True, "primary_grid_connection": "ERCOT-138kV"},
    {"dc_id": "oracle-austin", "name": "Oracle Austin", "operator": "Oracle", "region_id": "ERCOT",
        "latitude": 30.27, "longitude": -97.74, "max_capacity_mw": 80, "avg_pue": 1.3, "is_ai_focused": False, "primary_grid_connection": "ERCOT-138kV"},

    # CAISO (California)
    {"dc_id": "google-the-dalles", "name": "Google The Dalles", "operator": "Google", "region_id": "CAISO",
        "latitude": 45.60, "longitude": -121.18, "max_capacity_mw": 250, "avg_pue": 1.08, "is_ai_focused": True, "primary_grid_connection": "BPA-500kV"},
    {"dc_id": "meta-prineville", "name": "Meta Prineville", "operator": "Meta", "region_id": "CAISO",
        "latitude": 44.30, "longitude": -120.83, "max_capacity_mw": 160, "avg_pue": 1.1, "is_ai_focused": True, "primary_grid_connection": "CAISO-230kV"},
    {"dc_id": "aws-us-west-1", "name": "AWS US West 1", "operator": "AWS", "region_id": "CAISO",
        "latitude": 37.77, "longitude": -122.42, "max_capacity_mw": 120, "avg_pue": 1.25, "is_ai_focused": False, "primary_grid_connection": "CAISO-115kV"},

    # PJM (East Coast)
    {"dc_id": "aws-us-east-1", "name": "AWS US East 1 (Virginia)", "operator": "AWS", "region_id": "PJM",
     "latitude": 39.04, "longitude": -77.49, "max_capacity_mw": 300, "avg_pue": 1.18, "is_ai_focused": True, "primary_grid_connection": "Dominion-500kV"},
    {"dc_id": "microsoft-virginia", "name": "Microsoft Virginia", "operator": "Microsoft", "region_id": "PJM",
        "latitude": 38.95, "longitude": -77.45, "max_capacity_mw": 250, "avg_pue": 1.12, "is_ai_focused": True, "primary_grid_connection": "Dominion-230kV"},
    {"dc_id": "google-virginia", "name": "Google Virginia", "operator": "Google", "region_id": "PJM",
        "latitude": 39.10, "longitude": -77.55, "max_capacity_mw": 200, "avg_pue": 1.1, "is_ai_focused": True, "primary_grid_connection": "Dominion-230kV"},
    {"dc_id": "meta-virginia", "name": "Meta Virginia", "operator": "Meta", "region_id": "PJM",
        "latitude": 39.00, "longitude": -77.50, "max_capacity_mw": 180, "avg_pue": 1.15, "is_ai_focused": True, "primary_grid_connection": "Dominion-138kV"},
    {"dc_id": "oracle-ashburn", "name": "Oracle Ashburn", "operator": "Oracle", "region_id": "PJM",
        "latitude": 39.04, "longitude": -77.47, "max_capacity_mw": 100, "avg_pue": 1.28, "is_ai_focused": False, "primary_grid_connection": "Dominion-138kV"},

    # NYISO (New York)
    {"dc_id": "google-new-york", "name": "Google New York", "operator": "Google", "region_id": "NYISO",
        "latitude": 40.71, "longitude": -74.01, "max_capacity_mw": 80, "avg_pue": 1.2, "is_ai_focused": False, "primary_grid_connection": "ConEd-138kV"},
    {"dc_id": "aws-us-east-nyc", "name": "AWS NYC", "operator": "AWS", "region_id": "NYISO",
        "latitude": 40.75, "longitude": -73.99, "max_capacity_mw": 60, "avg_pue": 1.3, "is_ai_focused": False, "primary_grid_connection": "ConEd-138kV"},

    # MISO (Midwest)
    {"dc_id": "google-council-bluffs", "name": "Google Council Bluffs", "operator": "Google", "region_id": "MISO",
        "latitude": 41.26, "longitude": -95.86, "max_capacity_mw": 200, "avg_pue": 1.1, "is_ai_focused": True, "primary_grid_connection": "MISO-345kV"},
    {"dc_id": "meta-altoona", "name": "Meta Altoona", "operator": "Meta", "region_id": "MISO",
        "latitude": 41.64, "longitude": -93.47, "max_capacity_mw": 150, "avg_pue": 1.12, "is_ai_focused": True, "primary_grid_connection": "MISO-161kV"},
    {"dc_id": "microsoft-chicago", "name": "Microsoft Chicago", "operator": "Microsoft", "region_id": "MISO",
        "latitude": 41.88, "longitude": -87.63, "max_capacity_mw": 120, "avg_pue": 1.18, "is_ai_focused": False, "primary_grid_connection": "ComEd-138kV"},

    # SPP (Southwest)
    {"dc_id": "google-oklahoma", "name": "Google Mayes County", "operator": "Google", "region_id": "SPP",
        "latitude": 36.30, "longitude": -95.20, "max_capacity_mw": 180, "avg_pue": 1.09, "is_ai_focused": True, "primary_grid_connection": "SPP-345kV"},

    # ISONE (New England)
    {"dc_id": "aws-boston", "name": "AWS Boston", "operator": "AWS", "region_id": "ISONE", "latitude": 42.36,
        "longitude": -71.06, "max_capacity_mw": 50, "avg_pue": 1.25, "is_ai_focused": False, "primary_grid_connection": "ISONE-115kV"},
]


async def seed():
    """Seed data centers"""
    print(" Seeding data centers...")

    await init_db()

    async with async_session_maker() as session:
        count = 0
        for dc_data in DATA_CENTERS:
            # Check if exists
            existing = await session.execute(
                select(DataCenterDB).where(
                    DataCenterDB.dc_id == dc_data["dc_id"])
            )
            if not existing.scalar_one_or_none():
                dc = DataCenterDB(**dc_data)
                session.add(dc)
                count += 1
                print(
                    f"  ✅ Added: {dc_data['name']} ({dc_data['operator']}) - {dc_data['region_id']}")

        await session.commit()
        print(f"\n🎉 Seeded {count} data centers!")


if __name__ == "__main__":
    asyncio.run(seed())
