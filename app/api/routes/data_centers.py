"""
Data Center Endpoints
Data center metadata and energy estimates
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.session import get_db
from app.models.database import DataCenterDB, DataCenterEnergyEstimateDB, GridMetricsDB
from app.models.schemas import (
    DataCenter,
    Coordinates,
    DataCenterEnergyEstimate,
    DataCenterListResponse,
    DataCenterEnergyResponse,
)

router = APIRouter(prefix="/data-centers", tags=["Data Centers"])


@router.get("", response_model=DataCenterListResponse)
async def list_data_centers(
    region_id: Optional[str] = Query(
        None, description="Filter by grid region"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    ai_only: bool = Query(False, description="Only AI-focused data centers"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List data centers with optional filters
    """
    query = select(DataCenterDB)

    if region_id:
        query = query.where(DataCenterDB.region_id == region_id)
    if operator:
        query = query.where(DataCenterDB.operator.ilike(f"%{operator}%"))
    if ai_only:
        query = query.where(DataCenterDB.is_ai_focused == True)

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    data_centers = [
        DataCenter(
            dc_id=dc.dc_id,
            name=dc.name,
            operator=dc.operator,
            region_id=dc.region_id,
            coordinates=Coordinates(lat=dc.latitude, lon=dc.longitude),
            max_capacity_mw=dc.max_capacity_mw,
            avg_pue=dc.avg_pue,
            cooling_type=dc.cooling_type,
            primary_grid_connection=dc.primary_grid_connection,
            renewable_ppa_mw=dc.renewable_ppa_mw,
            commissioned_year=dc.commissioned_year,
            is_ai_focused=dc.is_ai_focused,
        )
        for dc in rows
    ]

    return DataCenterListResponse(
        total_count=total,
        data_centers=data_centers,
    )


@router.get("/{dc_id}", response_model=DataCenter)
async def get_data_center(
    dc_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get data center details by ID
    """
    result = await db.execute(
        select(DataCenterDB).where(DataCenterDB.dc_id == dc_id)
    )
    dc = result.scalar_one_or_none()

    if not dc:
        raise HTTPException(
            status_code=404, detail=f"Data center {dc_id} not found")

    return DataCenter(
        dc_id=dc.dc_id,
        name=dc.name,
        operator=dc.operator,
        region_id=dc.region_id,
        coordinates=Coordinates(lat=dc.latitude, lon=dc.longitude),
        max_capacity_mw=dc.max_capacity_mw,
        avg_pue=dc.avg_pue,
        cooling_type=dc.cooling_type,
        primary_grid_connection=dc.primary_grid_connection,
        renewable_ppa_mw=dc.renewable_ppa_mw,
        commissioned_year=dc.commissioned_year,
        is_ai_focused=dc.is_ai_focused,
    )


@router.post("", response_model=DataCenter)
async def create_data_center(
    data_center: DataCenter,
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update a data center record
    """
    stmt = insert(DataCenterDB).values(
        dc_id=data_center.dc_id,
        name=data_center.name,
        operator=data_center.operator,
        region_id=data_center.region_id,
        latitude=data_center.coordinates.lat,
        longitude=data_center.coordinates.lon,
        max_capacity_mw=data_center.max_capacity_mw,
        avg_pue=data_center.avg_pue,
        cooling_type=data_center.cooling_type,
        primary_grid_connection=data_center.primary_grid_connection,
        renewable_ppa_mw=data_center.renewable_ppa_mw,
        commissioned_year=data_center.commissioned_year,
        is_ai_focused=data_center.is_ai_focused,
    )

    # Upsert
    stmt = stmt.on_conflict_do_update(
        index_elements=["dc_id"],
        set_={
            "name": stmt.excluded.name,
            "operator": stmt.excluded.operator,
            "max_capacity_mw": stmt.excluded.max_capacity_mw,
            "avg_pue": stmt.excluded.avg_pue,
            "cooling_type": stmt.excluded.cooling_type,
            "renewable_ppa_mw": stmt.excluded.renewable_ppa_mw,
            "is_ai_focused": stmt.excluded.is_ai_focused,
        }
    )

    await db.execute(stmt)
    await db.commit()

    return data_center


@router.get("/{dc_id}/energy", response_model=DataCenterEnergyResponse)
async def get_data_center_energy(
    dc_id: str,
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """
    Get energy estimates for a data center

    Returns current estimate and historical data
    """
    # Get data center
    dc_result = await db.execute(
        select(DataCenterDB).where(DataCenterDB.dc_id == dc_id)
    )
    dc = dc_result.scalar_one_or_none()

    if not dc:
        raise HTTPException(
            status_code=404, detail=f"Data center {dc_id} not found")

    # Get energy estimates
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    estimates_result = await db.execute(
        select(DataCenterEnergyEstimateDB)
        .where(DataCenterEnergyEstimateDB.dc_id == dc_id)
        .where(DataCenterEnergyEstimateDB.timestamp_utc >= cutoff)
        .order_by(desc(DataCenterEnergyEstimateDB.timestamp_utc))
    )
    estimates = estimates_result.scalars().all()

    # If no estimates, generate one based on capacity and grid carbon
    if not estimates:
        # Get current grid carbon intensity
        grid_result = await db.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == dc.region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(1)
        )
        grid_metrics = grid_result.scalar_one_or_none()
        carbon_intensity = grid_metrics.carbon_intensity_kg_per_mwh if grid_metrics else 400

        # Estimate based on capacity and typical utilization
        utilization = 0.6  # Assume 60% utilization
        it_load = dc.max_capacity_mw * utilization / dc.avg_pue
        cooling_load = dc.max_capacity_mw * utilization - it_load

        current_estimate = DataCenterEnergyEstimate(
            timestamp_utc=datetime.utcnow(),
            dc_id=dc_id,
            estimated_load_mw=dc.max_capacity_mw * utilization,
            estimated_it_load_mw=it_load,
            estimated_cooling_load_mw=cooling_load,
            pue=dc.avg_pue,
            renewable_usage_pct=min(100, (dc.renewable_ppa_mw / (
                dc.max_capacity_mw * utilization)) * 100) if dc.max_capacity_mw > 0 else 0,
            carbon_intensity_kg_per_mwh=carbon_intensity,
        )
        historical = []
    else:
        latest = estimates[0]
        current_estimate = DataCenterEnergyEstimate(
            timestamp_utc=latest.timestamp_utc,
            dc_id=latest.dc_id,
            estimated_load_mw=latest.estimated_load_mw,
            estimated_it_load_mw=latest.estimated_it_load_mw,
            estimated_cooling_load_mw=latest.estimated_cooling_load_mw,
            pue=latest.pue,
            renewable_usage_pct=latest.renewable_usage_pct,
            carbon_intensity_kg_per_mwh=latest.carbon_intensity_kg_per_mwh,
        )
        historical = [
            DataCenterEnergyEstimate(
                timestamp_utc=e.timestamp_utc,
                dc_id=e.dc_id,
                estimated_load_mw=e.estimated_load_mw,
                estimated_it_load_mw=e.estimated_it_load_mw,
                estimated_cooling_load_mw=e.estimated_cooling_load_mw,
                pue=e.pue,
                renewable_usage_pct=e.renewable_usage_pct,
                carbon_intensity_kg_per_mwh=e.carbon_intensity_kg_per_mwh,
            )
            for e in estimates[1:]
        ]

    return DataCenterEnergyResponse(
        data_center=DataCenter(
            dc_id=dc.dc_id,
            name=dc.name,
            operator=dc.operator,
            region_id=dc.region_id,
            coordinates=Coordinates(lat=dc.latitude, lon=dc.longitude),
            max_capacity_mw=dc.max_capacity_mw,
            avg_pue=dc.avg_pue,
            cooling_type=dc.cooling_type,
            primary_grid_connection=dc.primary_grid_connection,
            renewable_ppa_mw=dc.renewable_ppa_mw,
            commissioned_year=dc.commissioned_year,
            is_ai_focused=dc.is_ai_focused,
        ),
        current_estimate=current_estimate,
        historical=historical if historical else None,
    )


@router.get("/by-region/{region_id}", response_model=List[DataCenter])
async def get_data_centers_by_region(
    region_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all data centers in a specific grid region
    """
    result = await db.execute(
        select(DataCenterDB).where(DataCenterDB.region_id == region_id)
    )
    rows = result.scalars().all()

    return [
        DataCenter(
            dc_id=dc.dc_id,
            name=dc.name,
            operator=dc.operator,
            region_id=dc.region_id,
            coordinates=Coordinates(lat=dc.latitude, lon=dc.longitude),
            max_capacity_mw=dc.max_capacity_mw,
            avg_pue=dc.avg_pue,
            cooling_type=dc.cooling_type,
            primary_grid_connection=dc.primary_grid_connection,
            renewable_ppa_mw=dc.renewable_ppa_mw,
            commissioned_year=dc.commissioned_year,
            is_ai_focused=dc.is_ai_focused,
        )
        for dc in rows
    ]
